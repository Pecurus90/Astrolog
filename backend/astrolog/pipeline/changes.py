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
from .walk import absolute as walk_absolute

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


_LONG = "\\\\?\\"


def _plain(path: str) -> str:
    """Windows `\\\\?\\` form is same path: `\\\\?\\UNC\\srv` is `\\\\srv` (Maximum Path Length)."""
    if path.startswith(_LONG + "UNC\\"):
        return "\\" + path[len(_LONG) + 3 :]
    return path.removeprefix(_LONG)


def _identity(path: str) -> tuple[int, int] | None:
    """Volume and folder id from disk: same in every spelling (letter, share, `\\\\?\\`)."""
    st = os.stat(long_path(path))
    return (st.st_dev, st.st_ino) if st.st_ino else None


def _still(stored: str, path: str) -> bool:
    """Stored root path is still this folder; only asked when ids match. Not answering: no."""
    try:
        return os.path.samefile(long_path(stored), long_path(path))
    except OSError:
        return False


def add_root(conn: sqlite3.Connection, path: str | os.PathLike[str], now: str) -> int:
    """Existing folder only. Same folder written another way: same root; inside or around one
    (written or real key): RootOverlapError. Other roots' disks touched only when ids match."""
    absolute = os.path.normpath(walk_absolute(_plain(os.fspath(path))))
    if not os.path.isdir(long_path(absolute)):
        raise NotADirectoryError(absolute)
    written, real = _keys(absolute)
    identity = _identity(absolute)
    with transaction(conn, immediate=True):
        same = _same_root(conn, written, real, identity)
        if same is not None:
            return same
        return inserted_id(
            conn.execute(
                "INSERT INTO pipeline_roots"
                " (path, written_key, real_key, device, inode, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (absolute, written, real, *(identity or (None, None)), now),
            )
        )


def _same_root(
    conn: sqlite3.Connection, written: str, real: str, identity: tuple[int, int] | None
) -> int | None:
    """Id of root that is this folder; one inside or around it: RootOverlapError."""
    for row in conn.execute("SELECT * FROM pipeline_roots"):
        if written == row["written_key"] or real == row["real_key"]:
            return int(row["id"])
        # renamed or moved folder keeps its id: confirm stored path is still it
        if identity == (row["device"], row["inode"]) and _still(row["path"], written):
            return int(row["id"])
        for mine, theirs in ((written, row["written_key"]), (real, row["real_key"])):
            if _inside(mine, theirs) or _inside(theirs, mine):
                raise RootOverlapError(row["path"], inside=_inside(mine, theirs))
    return None


def _rel(path: str, root: str) -> str:
    """Walk builds every path from root: cut it. relpath (abspath) strips a trailing dot."""
    return path[len(root) :].lstrip(os.sep).replace(os.sep, "/")


def _under(rel: str, folders: list[str]) -> bool:
    return any(rel == f or rel.startswith(f + "/") for f in folders)


def _is_text(path: str) -> bool:
    """Linux name in another encoding comes as lone surrogates (Python, PEP 383)."""
    try:
        path.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _on_disk(found: list[str], root: str) -> tuple[dict[str, tuple[int, int]], set[str]]:
    """rel path -> (size, mtime_ns), plus files not looked at (passing NAS error, rights, gone
    since walk, name not text: DB stores UTF-8): not judged, and said."""
    seen: dict[str, tuple[int, int]] = {}
    unlooked: set[str] = set()
    for path in found:
        if not _is_text(path):
            unlooked.add(_rel(path, root))
            continue
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
    row = conn.execute(
        "SELECT path, device FROM pipeline_roots WHERE id = ?", (root_id,)
    ).fetchone()
    root = row["path"]
    walk = walk_dir(root)
    root_failed = any(os.path.normcase(u) == os.path.normcase(root) for u in walk.unreadable)
    silent = root_failed or _emptied(conn, root_id, root, walk)
    volume = _volume(root)
    other_volume = None not in (volume, row["device"]) and volume != row["device"]
    changes = Changes(
        reachable=not (silent or (other_volume and _stranger(conn, root_id, root, walk))),
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
                " unknown_keys, finished) VALUES (?, ?, ?, 0, 0, 0, 0, 0, '{}', '{}', 0)",
                (root_id, now, int(changes.reachable)),
            )
        )
        if changes.reachable:
            if other_volume:  # its frames are here: archive now lives on this volume
                conn.execute(
                    "UPDATE pipeline_roots SET device = ?, inode = ? WHERE id = ?",
                    (*(_identity(root) or (None, None)), root_id),
                )
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


def _volume(root: str) -> int | None:
    try:
        return os.stat(long_path(root)).st_dev
    except OSError:
        return None


def _stranger(conn: sqlite3.Connection, root_id: int, root: str, walk: Walk) -> bool:
    """Other volume under root (other disk, same letter or mount) holding none of its frames:
    silent, never every file gone. No frames known: nothing to guard, judged."""
    here = {_rel(path, root) for path in walk.found}
    present = [
        row["rel_path"]
        for row in conn.execute(
            "SELECT rel_path FROM pipeline_files WHERE root_id = ? AND state = 'present'",
            (root_id,),
        )
    ]
    return bool(present) and not any(rel in here for rel in present)


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
