"""What changed in chosen folder since last scan, no file opened: path, size, date.
Folder not answering: no verdict on its files (ADR 0030, brick 2)."""

import json
import os
import sqlite3
from dataclasses import dataclass, field

from ..db.inserted import inserted_id
from ..db.transaction import transaction
from .scanner import Skip
from .walk import Walk, long_path, real_key, walk_dir

# Skip reasons that pass (file locked, copy running): read again every scan.
_PASSING = frozenset({Skip.UNREADABLE, Skip.INCOMPLETE})


@dataclass
class Changes:
    """Paths relative to root, with `/`, each list sorted."""

    reachable: bool
    scan_id: int = 0  # receipt this scan wrote
    root_id: int = 0
    root: str = ""  # its path, as stored
    new: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    reread: list[str] = field(default_factory=list)  # same on disk, last read failed
    unchanged: list[str] = field(default_factory=list)
    gone: list[str] = field(default_factory=list)
    unreachable: list[str] = field(default_factory=list)  # subfolders not answering
    unlooked: list[str] = field(default_factory=list)  # size and date unreadable
    hidden: list[str] = field(default_factory=list)  # trash, service folders: left out, said
    online_only: list[str] = field(default_factory=list)  # cloud placeholders: never downloaded
    # files to read -> (size, mtime_ns) seen now; written only with their read
    stat: dict[str, tuple[int, int]] = field(default_factory=dict)

    @property
    def to_read(self) -> list[str]:
        return sorted(self.new + self.changed + self.reread)


class RootOverlapError(ValueError):
    """Folder inside (`inside`) or around a root already added: files would count twice."""

    def __init__(self, other: str, *, inside: bool) -> None:
        super().__init__(f"{'inside' if inside else 'around'} {other}")
        self.other = other
        self.inside = inside


def _ignores_case(path: str) -> bool:
    """Asks the disk: same folder under swapped case (macOS APFS default, Windows)."""
    swapped = path.swapcase()
    try:
        return swapped != path and os.path.samefile(path, swapped)
    except OSError:
        return False


def _keys(path: str) -> tuple[str, str]:
    """(as written, real) comparison keys; computed once, on this path only."""
    written, real = os.path.normcase(path), real_key(path)
    if _ignores_case(path):
        written, real = written.casefold(), real.casefold()
    return written, real


def _inside(child: str, parent: str) -> bool:
    """On key text. Parent ending in bar (drive root, share written with one): no bar added.
    Another drive never inside."""
    return child.startswith(parent if parent.endswith(os.sep) else parent + os.sep)


def add_root(conn: sqlite3.Connection, path: str | os.PathLike[str], now: str) -> int:
    """Existing folder only. Same folder written another way: same root; inside or around one
    (written or real key): RootOverlapError. Other roots' disks never touched: keys stored."""
    absolute = os.path.normpath(os.path.abspath(path))
    if not os.path.isdir(long_path(absolute)):
        raise NotADirectoryError(absolute)
    written, real = _keys(absolute)
    with transaction(conn, immediate=True):
        for row in conn.execute("SELECT id, path, written_key, real_key FROM pipeline_roots"):
            if written == row["written_key"] or real == row["real_key"]:
                return int(row["id"])
            for mine, theirs in ((written, row["written_key"]), (real, row["real_key"])):
                if _inside(mine, theirs) or _inside(theirs, mine):
                    raise RootOverlapError(row["path"], inside=_inside(mine, theirs))
        return inserted_id(
            conn.execute(
                "INSERT INTO pipeline_roots (path, written_key, real_key, created_at)"
                " VALUES (?, ?, ?, ?)",
                (absolute, written, real, now),
            )
        )


def _rel(path: str, root: str) -> str:
    return os.path.relpath(path, root).replace(os.sep, "/")


def _under(rel: str, folders: list[str]) -> bool:
    return any(rel == f or rel.startswith(f + "/") for f in folders)


def _on_disk(found: list[str], root: str) -> tuple[dict[str, tuple[int, int]], set[str]]:
    """rel path -> (size, mtime_ns), plus files stat could not see (passing NAS error, rights,
    gone since walk): not judged."""
    seen: dict[str, tuple[int, int]] = {}
    unlooked: set[str] = set()
    for path in found:
        try:  # not DirEntry.stat: NTFS listing stays stale when file changed via another hard link
            st = os.stat(long_path(path))
        except OSError:
            unlooked.add(_rel(path, root))
            continue
        seen[_rel(path, root)] = (st.st_size, st.st_mtime_ns)
    return seen, unlooked


def record_changes(conn: sqlite3.Connection, root_id: int, now: str) -> Changes:
    """Compares folder with last reads; writes verdicts and receipt. Walk outside transaction:
    slow disk never holds lock."""
    root = conn.execute("SELECT path FROM pipeline_roots WHERE id = ?", (root_id,)).fetchone()[
        "path"
    ]
    walk = walk_dir(root)
    root_failed = any(os.path.normcase(u) == os.path.normcase(root) for u in walk.unreadable)
    changes = Changes(
        reachable=not (root_failed or _emptied(conn, root_id, root, walk)),
        root_id=root_id,
        root=root,
    )
    disk: dict[str, tuple[int, int]] = {}
    unlooked: set[str] = set()
    if changes.reachable:
        changes.unreachable = sorted(_rel(u, root) for u in walk.unreadable)
        disk, unlooked = _on_disk(walk.found, root)
        changes.unlooked = sorted(unlooked)
        changes.hidden = sorted(_rel(p, root) for p in walk.hidden)
        changes.online_only = sorted(_rel(p, root) for p in walk.online_only)
    with transaction(conn, immediate=True):
        changes.scan_id = inserted_id(
            conn.execute(
                "INSERT INTO pipeline_scans"
                " (root_id, scanned_at, reachable, new, changed, reread, unchanged, gone, skipped,"
                " finished) VALUES (?, ?, ?, 0, 0, 0, 0, 0, 0, 0)",
                (root_id, now, int(changes.reachable)),
            )
        )
        if changes.reachable:
            _judge(conn, root_id, disk, changes)
            _write_counts(conn, changes)
    for items in (changes.new, changes.changed, changes.reread, changes.unchanged, changes.gone):
        items.sort()
    return changes


def finish_scan(conn: sqlite3.Connection, changes: Changes) -> None:
    """After last read, caller's transaction: gone marked only now, so a stopped scan
    leaves gone and new for next one to pair (moved)."""
    if changes.reachable:
        _mark_gone(conn, changes.root_id, set(changes.unlooked) | set(changes.online_only), changes)
        changes.gone.sort()
        _write_counts(conn, changes)
    conn.execute("UPDATE pipeline_scans SET finished = 1 WHERE id = ?", (changes.scan_id,))


def _write_counts(conn: sqlite3.Connection, changes: Changes) -> None:
    conn.execute(
        "UPDATE pipeline_scans SET new = ?, changed = ?, reread = ?, unchanged = ?, gone = ?,"
        " left_out = ? WHERE id = ?",
        (len(changes.new), len(changes.changed), len(changes.reread),
         len(changes.unchanged), len(changes.gone), _left_out(changes), changes.scan_id),
    )  # fmt: skip


def _emptied(conn: sqlite3.Connection, root_id: int, root: str, walk: Walk) -> bool:
    """Opens with no entry at all, though files were there: unmounted NAS (Docker mount point
    stays, empty). Counts as silent root, never as every file gone."""
    if walk.found or walk.online_only or walk.hidden or walk.unreadable:
        return False
    had = conn.execute(
        "SELECT 1 FROM pipeline_files WHERE root_id = ? AND state = 'present' LIMIT 1", (root_id,)
    ).fetchone()
    if had is None:
        return False
    try:  # notes, night folders, other files: mounted, only FITS removed
        with os.scandir(long_path(root)) as entries:
            return next(entries, None) is None
    except OSError:
        return True


def _left_out(changes: Changes) -> str:
    return json.dumps(
        {
            "hidden": changes.hidden,
            "online_only": changes.online_only,
            "unreachable": changes.unreachable,
            "unlooked": changes.unlooked,
        }
    )


def _judge(
    conn: sqlite3.Connection,
    root_id: int,
    disk: dict[str, tuple[int, int]],
    changes: Changes,
) -> None:
    known = {
        row["rel_path"]: row
        for row in conn.execute(
            "SELECT rel_path, size, mtime_ns, state, skip_reason FROM pipeline_files"
            " WHERE root_id = ?",
            (root_id,),
        )
    }
    for rel, stat in disk.items():
        before = known.get(rel)
        if before is None or before["state"] == "gone":
            changes.new.append(rel)
            changes.stat[rel] = stat  # row written with its read
            continue
        if (before["size"], before["mtime_ns"]) != stat:
            changes.changed.append(rel)
            changes.stat[rel] = stat
        elif before["skip_reason"] in _PASSING:  # read failed last time: never lost
            changes.reread.append(rel)
            changes.stat[rel] = stat
        else:
            changes.unchanged.append(rel)
        conn.execute(  # old size and date stay until read: interrupted, read again
            "UPDATE pipeline_files SET seen_scan_id = ? WHERE root_id = ? AND rel_path = ?",
            (changes.scan_id, root_id, rel),
        )


def _mark_gone(
    conn: sqlite3.Connection, root_id: int, not_judged: set[str], changes: Changes
) -> None:
    """Present before, not seen now. Only in cloud, not looked at, under folder not answering or
    hidden since: stays as was. Bin holds files under new path: those gone."""
    missing = conn.execute(
        "SELECT rel_path FROM pipeline_files WHERE root_id = ? AND state = 'present'"
        " AND seen_scan_id != ?",
        (root_id, changes.scan_id),
    ).fetchall()
    for (rel,) in missing:
        if rel in not_judged or _under(rel, changes.unreachable + changes.hidden):
            continue
        changes.gone.append(rel)
        conn.execute(
            "UPDATE pipeline_files SET state = 'gone', gone_scan_id = ?"
            " WHERE root_id = ? AND rel_path = ?",
            (changes.scan_id, root_id, rel),
        )
