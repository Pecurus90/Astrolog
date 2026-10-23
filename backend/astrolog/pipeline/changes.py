"""What changed in chosen folder since last scan, no file opened: path, size, date.
Folder not answering: no verdict on its files (ADR 0030, brick 2)."""

import json
import os
import sqlite3
from dataclasses import dataclass, field

from ..db.inserted import inserted_id
from ..db.transaction import transaction
from .scanner import Skip
from .walk import Walk, long_path, plain, real_key, walk_dir
from .walk import absolute as walk_absolute

# Skip reasons that pass (file locked, copy running): read again every scan.
PASSING = frozenset({Skip.UNREADABLE, Skip.INCOMPLETE})
LEFT_OUT_KEPT = 100  # no convention, product choice: paths per list in each receipt


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
    unlooked: list[str] = field(default_factory=list)  # no stat, name not text, gone before read
    hidden: list[str] = field(default_factory=list)  # trash, service, hidden files: out, said
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


def _identity(path: str) -> tuple[str, str] | None:
    """Volume and folder id from disk: same in every spelling (letter, share, `\\\\?\\`).
    Digits: Windows volume serial is unsigned 64 bit, past SQLite INTEGER. Silent disk: None."""
    try:
        st = os.stat(long_path(path))
    except OSError:
        return None
    return (str(st.st_dev), str(st.st_ino)) if st.st_ino else None


def _still(stored: str, path: str) -> bool:
    """Stored root path is still this folder; only asked when ids match. Not answering: no."""
    try:
        return os.path.samefile(long_path(stored), long_path(path))
    except OSError:
        return False


def add_root(conn: sqlite3.Connection, path: str | os.PathLike[str], now: str) -> int:
    """Existing folder only. Same folder written another way: same root; inside or around one
    (written or real key): RootOverlapError. Other roots' disks touched only when ids match."""
    written_path = plain(_unquoted(os.fspath(path)))
    if not os.path.isabs(written_path):  # empty or relative: would be app's working folder
        raise NotADirectoryError(written_path)
    absolute = os.path.normpath(walk_absolute(written_path))
    if not os.path.isdir(long_path(absolute)):
        raise NotADirectoryError(absolute)
    written, real = _keys(absolute)
    identity = _identity(absolute)
    ancestors = _above(absolute)
    with transaction(conn, immediate=True):
        same = _same_root(conn, written, real, identity, ancestors)
        if same is not None:
            return same
        return inserted_id(
            conn.execute(
                "INSERT INTO pipeline_roots"
                " (path, written_key, real_key, device, inode, ancestors, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (absolute, written, real, *(identity or (None, None)), json.dumps(list(ancestors)),
                 now),
            )
        )  # fmt: skip


def _unquoted(path: str) -> str:
    """Windows 'Copy as path' wraps it in quotes: one pair off, only when path as written
    is not there (Linux name may hold quotes)."""
    quoted = len(path) > 1 and path[0] == path[-1] == '"'
    return path[1:-1] if quoted and not os.path.exists(long_path(path)) else path


def _above(absolute: str) -> dict[str, str]:
    """Letter mapped below a share (or link): what holds it shows only on the real path."""
    return _ancestors(absolute) | _ancestors(plain(os.path.realpath(long_path(absolute))))


def _ancestors(path: str) -> dict[str, str]:
    """'device:inode' -> folder, for every folder holding path: share and letter agree there."""
    found: dict[str, str] = {}
    current = path
    while (parent := os.path.dirname(current)) != current:
        current = parent
        if (identity := _identity(current)) is not None:
            found[":".join(identity)] = current
    return found


def _same_root(
    conn: sqlite3.Connection,
    written: str,
    real: str,
    identity: tuple[str, str] | None,
    ancestors: dict[str, str],
) -> int | None:
    """Id of root that is this folder; one inside or around it (text or disk): RootOverlapError.
    Disk id survives rename: match only while stored path still is this folder."""
    mine_id = ":".join(identity) if identity is not None else None
    for row in conn.execute("SELECT * FROM pipeline_roots"):
        if written == row["written_key"] or real == row["real_key"]:
            return int(row["id"])
        theirs_id = f"{row['device']}:{row['inode']}" if row["device"] is not None else None
        if mine_id is not None and mine_id == theirs_id and _still(row["path"], written):
            return int(row["id"])
        for mine, theirs in ((written, row["written_key"]), (real, row["real_key"])):
            if _inside(mine, theirs) or _inside(theirs, mine):
                raise RootOverlapError(row["path"], inside=_inside(mine, theirs))
        if theirs_id in ancestors and _still(row["path"], ancestors[theirs_id]):
            raise RootOverlapError(row["path"], inside=True)
        if mine_id is not None and mine_id in json.loads(row["ancestors"]):
            raise RootOverlapError(row["path"], inside=False)
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
        seen[_rel(path, root)] = (st.st_size, _held(st.st_mtime_ns))
    return seen, unlooked


def _held(mtime_ns: int) -> int:
    """Date past SQLite INTEGER (NTFS 1601, year 2300): pinned to edge; file still read."""
    return max(-(2**63), min(mtime_ns, 2**63 - 1))


def record_changes(conn: sqlite3.Connection, root_id: int, now: str) -> Changes:
    """Compares folder with last reads; writes verdicts and receipt. Walk outside transaction:
    slow disk never holds lock."""
    row = conn.execute(
        "SELECT path, device FROM pipeline_roots WHERE id = ?", (root_id,)
    ).fetchone()
    root = row["path"]
    walk = walk_dir(root)
    root_failed = any(os.path.normcase(u) == os.path.normcase(root) for u in walk.unreadable)
    changes = Changes(
        reachable=not (root_failed or _emptied(conn, root_id, root, walk)),
        root_id=root_id,
        root=root,
    )
    # other disk under root (same letter, remount): judged anyway, said in receipt; owner's
    # choice: wrong disk shows frames gone, back with right disk, never silent for good
    identity = _identity(root)
    other_volume = (
        identity is not None and row["device"] is not None and identity[0] != row["device"]
    )
    above = _above(root) if other_volume else {}  # folders above belong to new disk too
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
                " (root_id, scanned_at, reachable, volume_changed, new, changed, reread, unchanged,"
                " gone, skipped, unknown_keys, unknown_more, left_out, left_out_more, finished)"
                " VALUES (?, ?, ?, ?, 0, 0, 0, 0, 0, '{}', '{}', 0, ?, ?, 0)",
                (
                    root_id,
                    now,
                    int(changes.reachable),
                    int(changes.reachable and other_volume),
                    *(_left_out(changes) if changes.reachable else (None, None)),
                ),
            )
        )
        if changes.reachable:
            if other_volume and identity is not None:  # root now lives on this volume
                conn.execute(
                    "UPDATE pipeline_roots SET device = ?, inode = ?, ancestors = ? WHERE id = ?",
                    (*identity, json.dumps(list(above)), root_id),
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
        " left_out = ?, left_out_more = ? WHERE id = ?",
        (len(changes.new), len(changes.changed), len(changes.reread),
         len(changes.unchanged), len(changes.gone), *_left_out(changes), changes.scan_id),
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


def _left_out(changes: Changes) -> tuple[str, str]:
    """First LEFT_OUT_KEPT paths per list, and how many more: receipt stays small."""
    lists = {
        "hidden": changes.hidden,
        "online_only": changes.online_only,
        "unreachable": changes.unreachable,
        "unlooked": changes.unlooked,
    }
    kept = {name: paths[:LEFT_OUT_KEPT] for name, paths in lists.items()}
    more = {name: max(0, len(paths) - LEFT_OUT_KEPT) for name, paths in lists.items()}
    return json.dumps(kept), json.dumps(more)


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
            " WHERE root_id = ? AND state = 'present'",  # gone only: path new again
            (root_id,),
        )
    }
    for rel, stat in disk.items():
        before = known.get(rel)
        if before is None:
            changes.new.append(rel)
            changes.stat[rel] = stat  # row written with its read
            continue
        if (before["size"], before["mtime_ns"]) != stat:
            changes.changed.append(rel)
            changes.stat[rel] = stat
        elif before["skip_reason"] in PASSING:  # read failed last time: never lost
            changes.reread.append(rel)
            changes.stat[rel] = stat
        else:
            changes.unchanged.append(rel)
        conn.execute(  # old size and date stay until read: interrupted, read again
            "UPDATE pipeline_files SET seen_scan_id = ?"
            " WHERE root_id = ? AND rel_path = ? AND state = 'present'",
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
            " WHERE root_id = ? AND rel_path = ? AND state = 'present'",
            (changes.scan_id, root_id, rel),
        )
