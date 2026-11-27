"""What changed in chosen folder since last scan, no file opened: path, size, date.
Folder not answering: no verdict on its files (ADR 0030, brick 2)."""

import json
import os
import sqlite3
from dataclasses import dataclass, field

from ..db.inserted import inserted_id
from ..db.transaction import transaction
from .roots import above, identity, is_text
from .scanner import Skip
from .values import SQLITE_MAX, SQLITE_MIN
from .walk import Walk, long_path, walk_dir

# Skip reasons that pass (file locked, copy running): read again every scan.
PASSING = frozenset({Skip.UNREADABLE, Skip.INCOMPLETE, Skip.FAULT})
LEFT_OUT_KEPT = 100  # [P ADR 0038] paths per list in each receipt


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
    unreachable: list[str] = field(default_factory=list)  # subfolders not answering, dangling links
    unlooked: list[str] = field(default_factory=list)  # no stat, name not text, gone before read
    hidden: list[str] = field(default_factory=list)  # trash, service, hidden files: out, said
    online_only: list[str] = field(default_factory=list)  # cloud placeholders: never downloaded
    not_fits: dict[str, int] = field(default_factory=dict)  # other files, by extension
    # files to read -> (size, mtime_ns) seen now; written only with their read
    stat: dict[str, tuple[int, int]] = field(default_factory=dict)

    @property
    def to_read(self) -> list[str]:
        return sorted(self.new + self.changed + self.reread)


def _rel(path: str, root: str) -> str:
    """Walk builds every path from root: cut it. relpath (abspath) strips a trailing dot."""
    return path[len(root) :].lstrip(os.sep).replace(os.sep, "/")


def _under(rel: str, folders: list[str]) -> bool:
    return any(rel == f or rel.startswith(f + "/") for f in folders)


def _on_disk(found: list[str], root: str) -> tuple[dict[str, tuple[int, int]], set[str]]:
    """rel path -> (size, mtime_ns), plus files not looked at (passing NAS error, rights, gone
    since walk, name not text: DB stores UTF-8): not judged, and said."""
    seen: dict[str, tuple[int, int]] = {}
    unlooked: set[str] = set()
    for path in found:
        if not is_text(path):
            unlooked.add(_rel(path, root))
            continue
        try:  # not DirEntry.stat: NTFS listing stays stale when file changed via another hard link
            st = os.stat(long_path(path))
        except OSError:
            unlooked.add(_rel(path, root))
            continue
        seen[_rel(path, root)] = (st.st_size, _held(st.st_mtime_ns))
    return seen, unlooked


def _ms(mtime_ns: int) -> int:
    """Date compared to the millisecond (spina.md:40): a remounted NAS truncates the rest.
    Toward zero like SQLite integer division in scan.MOVED, before 1970 too."""
    whole = abs(mtime_ns) // 1_000_000
    return whole if mtime_ns >= 0 else -whole


def _held(mtime_ns: int) -> int:
    """Date past SQLite INTEGER (NTFS 1601, year 2300): pinned to edge; file still read."""
    return max(SQLITE_MIN, min(mtime_ns, SQLITE_MAX))


def record_changes(conn: sqlite3.Connection, root_id: int, now: str) -> Changes:
    """Compares folder with last reads; writes verdicts and receipt. Walk outside transaction:
    slow disk never holds lock."""
    row = conn.execute(
        "SELECT path, device FROM pipeline_roots WHERE id = ?", (root_id,)
    ).fetchone()
    root = row["path"]
    walk = walk_dir(root)
    root_failed = any(os.path.normcase(u) == os.path.normcase(root) for u in walk.unreachable)
    changes = Changes(
        reachable=not (root_failed or _emptied(conn, root_id, root, walk)),
        root_id=root_id,
        root=root,
    )
    # other disk under root (same letter, remount): judged anyway, said in receipt; owner's
    # choice: wrong disk shows frames gone, back with right disk, never silent for good
    ident = identity(root)
    other_volume = ident is not None and row["device"] is not None and ident[0] != row["device"]
    # added while silent (NAS off): disk known only now
    first_seen = ident is not None and row["device"] is None
    heights = above(root) if other_volume or first_seen else {}  # held by new disk too
    disk: dict[str, tuple[int, int]] = {}
    unlooked: set[str] = set()
    if changes.reachable:
        changes.unreachable = sorted(_rel(u, root) for u in walk.unreachable)
        disk, unlooked = _on_disk(walk.found, root)
        changes.unlooked = sorted(unlooked)
        changes.hidden = sorted(_rel(p, root) for p in walk.hidden)
        changes.online_only = sorted(_rel(p, root) for p in walk.online_only)
        changes.not_fits = dict(walk.not_fits.most_common(LEFT_OUT_KEPT))
    with transaction(conn):
        changes.scan_id = inserted_id(
            conn.execute(
                "INSERT INTO pipeline_scans"
                " (root_id, scanned_at, reachable, volume_changed, new, changed, reread, unchanged,"
                " gone, skipped, unknown_keys, unknown_more, left_out, left_out_more, not_fits,"
                " finished) VALUES (?, ?, ?, ?, 0, 0, 0, 0, 0, '{}', '{}', 0, ?, ?, ?, 0)",
                (
                    root_id,
                    now,
                    int(changes.reachable),
                    int(changes.reachable and other_volume),
                    *(_left_out(changes) if changes.reachable else (None, None)),
                    json.dumps(changes.not_fits) if changes.reachable else None,
                ),
            )
        )
        if changes.reachable:
            if ident is not None and (other_volume or first_seen):  # root lives on this volume
                conn.execute(
                    "UPDATE pipeline_roots SET device = ?, inode = ?, ancestors = ? WHERE id = ?",
                    (*ident, json.dumps(list(heights)), root_id),
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
    if walk.found or walk.online_only or walk.hidden or walk.unreachable:
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
        if (before["size"], _ms(before["mtime_ns"])) != (stat[0], _ms(stat[1])):
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
