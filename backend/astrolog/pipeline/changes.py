"""What changed in chosen folder since last scan, no file opened: path, size, date.
Folder not answering: no verdict on its files (ADR 0030, brick 2)."""

import os
import sqlite3
from dataclasses import dataclass, field

from ..db.inserted import inserted_id
from ..db.transaction import transaction
from .walk import long_path, walk_dir


@dataclass
class Changes:
    """Paths relative to root, with `/`, each list sorted."""

    reachable: bool
    scan_id: int = 0  # receipt this scan wrote
    new: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    gone: list[str] = field(default_factory=list)
    unreachable: list[str] = field(default_factory=list)  # subfolders not answering
    unlooked: list[str] = field(default_factory=list)  # size and date unreadable

    @property
    def to_read(self) -> list[str]:
        return sorted(self.new + self.changed)


def add_root(conn: sqlite3.Connection, path: str | os.PathLike[str], now: str) -> int:
    with transaction(conn):
        conn.execute(
            "INSERT OR IGNORE INTO pipeline_roots (path, created_at) VALUES (?, ?)",
            (str(path), now),
        )
        row = conn.execute("SELECT id FROM pipeline_roots WHERE path = ?", (str(path),)).fetchone()
    return int(row["id"])


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
        try:
            st = os.stat(long_path(path))
        except OSError:
            unlooked.add(_rel(path, root))
            continue
        seen[_rel(path, root)] = (st.st_size, st.st_mtime_ns)
    return seen, unlooked


def sync(conn: sqlite3.Connection, root_id: int, now: str) -> Changes:
    """Compares folder with what last scans saw; writes result and its receipt."""
    with transaction(conn):
        return record_changes(conn, root_id, now)


def record_changes(conn: sqlite3.Connection, root_id: int, now: str) -> Changes:
    """`sync` inside caller's transaction: what it reads of files commits with it."""
    root = conn.execute("SELECT path FROM pipeline_roots WHERE id = ?", (root_id,)).fetchone()[
        "path"
    ]
    walk = walk_dir(root)
    root_failed = any(os.path.normcase(u) == os.path.normcase(root) for u in walk.unreadable)
    changes = Changes(reachable=not root_failed)
    disk: dict[str, tuple[int, int]] = {}
    unlooked: set[str] = set()
    if changes.reachable:
        changes.unreachable = sorted(_rel(u, root) for u in walk.unreadable)
        disk, unlooked = _on_disk(walk.found, root)
        changes.unlooked = sorted(unlooked)
    scan_id = inserted_id(
        conn.execute(
            "INSERT INTO pipeline_scans"
            " (root_id, scanned_at, reachable, new, changed, unchanged, gone)"
            " VALUES (?, ?, ?, 0, 0, 0, 0)",
            (root_id, now, int(changes.reachable)),
        )
    )
    if changes.reachable:
        _judge(conn, root_id, scan_id, disk, changes)
        not_judged = unlooked | {_rel(p, root) for p in walk.online_only}
        _mark_gone(conn, root_id, scan_id, not_judged, changes)
        conn.execute(
            "UPDATE pipeline_scans SET new = ?, changed = ?, unchanged = ?, gone = ?"
            " WHERE id = ?",
            (len(changes.new), len(changes.changed), len(changes.unchanged),
             len(changes.gone), scan_id),
        )  # fmt: skip
    changes.scan_id = scan_id
    for items in (changes.new, changes.changed, changes.unchanged, changes.gone):
        items.sort()
    return changes


def _judge(
    conn: sqlite3.Connection,
    root_id: int,
    scan_id: int,
    disk: dict[str, tuple[int, int]],
    changes: Changes,
) -> None:
    known = {
        row["rel_path"]: row
        for row in conn.execute(
            "SELECT rel_path, size, mtime_ns, state FROM pipeline_files WHERE root_id = ?",
            (root_id,),
        )
    }
    for rel, (size, mtime_ns) in disk.items():
        before = known.get(rel)
        if before is None or before["state"] == "gone":
            changes.new.append(rel)
        elif (before["size"], before["mtime_ns"]) != (size, mtime_ns):
            changes.changed.append(rel)
        else:
            changes.unchanged.append(rel)
        conn.execute(
            "INSERT INTO pipeline_files (root_id, rel_path, size, mtime_ns, state, seen_scan_id)"
            " VALUES (?, ?, ?, ?, 'present', ?)"
            " ON CONFLICT (root_id, rel_path) DO UPDATE SET size = excluded.size,"
            " mtime_ns = excluded.mtime_ns, state = 'present',"
            " seen_scan_id = excluded.seen_scan_id",
            (root_id, rel, size, mtime_ns, scan_id),
        )


def _mark_gone(
    conn: sqlite3.Connection, root_id: int, scan_id: int, not_judged: set[str], changes: Changes
) -> None:
    """Present before, not seen now. File only in cloud (OneDrive, iCloud) or not looked at:
    stays as was."""
    missing = conn.execute(
        "SELECT rel_path FROM pipeline_files WHERE root_id = ? AND state = 'present'"
        " AND seen_scan_id != ?",
        (root_id, scan_id),
    ).fetchall()
    for (rel,) in missing:
        if rel in not_judged or _under(rel, changes.unreachable):
            continue
        changes.gone.append(rel)
        conn.execute(
            "UPDATE pipeline_files SET state = 'gone', seen_scan_id = ?"
            " WHERE root_id = ? AND rel_path = ?",
            (scan_id, root_id, rel),
        )
