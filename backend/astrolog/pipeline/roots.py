"""Roots the user chose: one row each, for old and new pipeline (step 40.3). Retired, never deleted:
frames and receipts stay. Writes in caller's transaction; `add_root` opens its own."""

import json
import os
import sqlite3
from dataclasses import dataclass

from ..db.inserted import inserted_id
from ..db.transaction import transaction
from .walk import absolute as walk_absolute
from .walk import long_path, plain, real_key


class RootOverlapError(ValueError):
    """Folder inside (`inside`) or around an active root: files would count twice."""

    def __init__(self, other: str, other_id: int, *, inside: bool) -> None:
        super().__init__(f"{'inside' if inside else 'around'} {other}")
        self.other = other
        self.other_id = other_id
        self.inside = inside


class RootTakenError(ValueError):
    """Path is already another root's (written or real key): two rows, one folder."""

    def __init__(self, other_id: int) -> None:
        super().__init__(f"root {other_id}")
        self.other_id = other_id


@dataclass(frozen=True)
class Root:
    id: int
    path: str


@dataclass(frozen=True)
class _Place:
    """Path as stored, its keys and what the disk says of it (None: not answering)."""

    path: str
    written: str
    real: str
    identity: tuple[str, str] | None
    ancestors: dict[str, str]


def normalized(path: str | os.PathLike[str]) -> str:
    """Absolute, normalised; NotADirectoryError: relative, name not text, or a file. A folder not
    answering passes (NAS switched off): registering is permissive."""
    written_path = plain(_unquoted(os.fspath(path)))
    if not os.path.isabs(written_path):  # empty or relative: would be app's working folder
        raise NotADirectoryError(written_path)
    absolute = os.path.normpath(walk_absolute(written_path))
    # name not text (PEP 383): DB stores UTF-8, its files could never be read either
    if not is_text(absolute) or os.path.isfile(long_path(absolute)):
        raise NotADirectoryError(absolute)
    return absolute


def _place(path: str | os.PathLike[str]) -> _Place:
    absolute = normalized(path)
    written, real = _keys(absolute)
    return _Place(absolute, written, real, identity(absolute), above(absolute))


def add_root(conn: sqlite3.Connection, path: str | os.PathLike[str], now: str) -> int:
    """`register` in its own transaction."""
    place = _place(path)
    with transaction(conn):
        return _register(conn, place, now, None)


def register(
    conn: sqlite3.Connection, path: str | os.PathLike[str], now: str, name: str | None = None
) -> int:
    """Same folder another way, retired too: its id. Overlap with an active root on disk or as
    written, not around it: RootOverlapError. Around roots as written: takes them (`absorb`)."""
    return _register(conn, _place(path), now, name)


def _register(conn: sqlite3.Connection, place: _Place, now: str, name: str | None) -> int:
    held = {
        r["id"] for r in conn.execute("SELECT id, written_key FROM pipeline_roots")
        if _inside(r["written_key"], place.written)
    }  # fmt: skip
    same = _same_root(conn, place, held)
    if same is not None:
        return same
    root_id = inserted_id(
        conn.execute(
            "INSERT INTO pipeline_roots (path, written_key, real_key, device, inode, ancestors,"
            " name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (place.path, place.written, place.real, *(place.identity or (None, None)),
             json.dumps(list(place.ancestors)), name, now),
        )
    )  # fmt: skip
    absorb(conn, root_id, now)
    return root_id


def absorb(conn: sqlite3.Connection, outer_id: int, now: str) -> None:
    """Roots inside, retired too, give files, receipts, moves (prefixed) and retire; a retired one
    around gives back files under it. New root or one coming back: same rule (step 38)."""
    outer = conn.execute(
        "SELECT path, written_key FROM pipeline_roots WHERE id = ?", (outer_id,)
    ).fetchone()
    for row in conn.execute("SELECT * FROM pipeline_roots WHERE id != ?", (outer_id,)).fetchall():
        if _inside(row["written_key"], outer["written_key"]):
            _take_over(conn, outer_id, row["id"], _prefix(row["path"], outer["path"]), now)
        elif row["retired_at"] is not None and _inside(outer["written_key"], row["written_key"]):
            _give_back(conn, row["id"], outer_id, _prefix(outer["path"], row["path"]))


def _take_over(conn: sqlite3.Connection, outer: int, inner: int, prefix: str, now: str) -> None:
    """Same rows, paths prefixed. IGNORE: a file both held present is the outer's already, the
    inner's copy stays with it as history."""
    conn.execute(
        "UPDATE OR IGNORE pipeline_files SET root_id = ?, rel_path = ? || rel_path"
        " WHERE root_id = ?",
        (outer, prefix, inner),
    )
    conn.execute(
        "UPDATE pipeline_moves SET was_path = :p || was_path, now_path = :p || now_path"
        " WHERE scan_id IN (SELECT id FROM pipeline_scans WHERE root_id = :inner)",
        {"p": prefix, "inner": inner},
    )
    conn.execute("UPDATE pipeline_scans SET root_id = ? WHERE root_id = ?", (outer, inner))
    conn.execute(
        "UPDATE pipeline_roots SET retired_at = ? WHERE id = ? AND retired_at IS NULL",
        (now, inner),
    )


def _give_back(conn: sqlite3.Connection, around: int, root: int, prefix: str) -> None:
    """Files of retired `around` under `root` pass to it, prefix cut. IGNORE: one it holds stays."""
    conn.execute(
        "UPDATE OR IGNORE pipeline_files SET root_id = :root, rel_path = substr(rel_path, :cut)"
        " WHERE root_id = :around AND substr(rel_path, 1, :n) = :prefix",
        {"root": root, "cut": len(prefix) + 1, "around": around, "n": len(prefix),
         "prefix": prefix},
    )  # fmt: skip


def move(conn: sqlite3.Connection, root_id: int, path: str | os.PathLike[str]) -> None:
    """Same id, new place: files are relative, they follow. Path another root's: RootTakenError."""
    place = _place(path)
    for row in conn.execute(
        "SELECT id FROM pipeline_roots WHERE id != ? AND (written_key = ? OR real_key = ?)",
        (root_id, place.written, place.real),
    ):
        raise RootTakenError(int(row["id"]))
    conn.execute(
        "UPDATE pipeline_roots SET path = ?, written_key = ?, real_key = ?, device = ?, inode = ?,"
        " ancestors = ? WHERE id = ?",
        (place.path, place.written, place.real, *(place.identity or (None, None)),
         json.dumps(list(place.ancestors)), root_id),
    )  # fmt: skip


def retire(conn: sqlite3.Connection, root_id: int, at: str | None) -> None:
    """`at` None: back in use."""
    conn.execute("UPDATE pipeline_roots SET retired_at = ? WHERE id = ?", (at, root_id))


@dataclass(frozen=True)
class Declared:
    """What a backup brings back of a root (ADR 0017)."""

    path: str
    name: str | None
    retired_at: str | None
    sample: str  # JSON pairs (rel path, fingerprint)


def restore(conn: sqlite3.Connection, declared: Declared, now: str) -> int | None:
    """By path, even if not here; another system's (`D:/Astro` on NAS) as written, keys from text.
    One database's rows: no overlap asked. Name not text: None, left out."""
    name, retired_at, sample = declared.name, declared.retired_at, declared.sample
    if not is_text(declared.path):
        return None
    try:  # normalised only when it is here: `/volume1/photo` on Windows is not `C:\volume1`
        if not os.path.isdir(long_path(declared.path)):
            raise NotADirectoryError(declared.path)
        place = _place(declared.path)
    except NotADirectoryError:
        key = os.path.normcase(declared.path)
        place = _Place(declared.path, key, key, None, {})
    row = conn.execute(
        "SELECT id FROM pipeline_roots WHERE written_key = ? OR real_key = ?",
        (place.written, place.real),
    ).fetchone()
    if row is None:
        return inserted_id(
            conn.execute(
                "INSERT INTO pipeline_roots (path, written_key, real_key, device, inode, ancestors,"
                " name, retired_at, sample_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (place.path, place.written, place.real, *(place.identity or (None, None)),
                 json.dumps(list(place.ancestors)), name, retired_at, sample, now),
            )
        )  # fmt: skip
    conn.execute(
        "UPDATE pipeline_roots SET name = ?, retired_at = ?, sample_json = ? WHERE id = ?",
        (name, retired_at, sample, row["id"]),
    )
    return int(row["id"])


def held(conn: sqlite3.Connection, path: str) -> list[Root]:
    """Active roots `path` would hold, as written: adding it takes them."""
    written = _keys(normalized(path))[0]
    return [Root(r["id"], r["path"]) for r in _active(conn) if _inside(r["written_key"], written)]


def holder(conn: sqlite3.Connection, path: str) -> Root | None:
    """Active root `path` is inside, as written: its files are read already."""
    written = _keys(normalized(path))[0]
    return next(
        (Root(r["id"], r["path"]) for r in _active(conn) if _inside(written, r["written_key"])),
        None,
    )


def _active(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, path, written_key FROM pipeline_roots WHERE retired_at IS NULL ORDER BY id"
    ).fetchall()


def _ignores_case(path: str) -> bool:
    """Asks the disk: same folder under swapped case (macOS APFS default, Windows). Path not
    there yet: its nearest folder that is."""
    while not os.path.lexists(path) and os.path.dirname(path) != path:
        path = os.path.dirname(path)
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


def identity(path: str) -> tuple[str, str] | None:
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


def _unquoted(path: str) -> str:
    """Windows 'Copy as path' wraps it in quotes: one pair off, only when path as written
    is not there (Linux name may hold quotes)."""
    quoted = len(path) > 1 and path[0] == path[-1] == '"'
    return path[1:-1] if quoted and not os.path.exists(long_path(path)) else path


def above(absolute: str) -> dict[str, str]:
    """Letter mapped below a share (or link): what holds it shows only on the real path."""
    return _ancestors(absolute) | _ancestors(plain(os.path.realpath(long_path(absolute))))


def _ancestors(path: str) -> dict[str, str]:
    """'device:inode' -> folder, for every folder holding path: share and letter agree there."""
    found: dict[str, str] = {}
    current = path
    while (parent := os.path.dirname(current)) != current:
        current = parent
        if (ident := identity(current)) is not None:
            found[":".join(ident)] = current
    return found


def _same_root(conn: sqlite3.Connection, place: _Place, held: set[int]) -> int | None:
    """Id of root that is this folder, retired too; an active one inside or around it (text or
    disk), not `held`: RootOverlapError. Disk id survives rename: match while path still is it."""
    mine_id = ":".join(place.identity) if place.identity is not None else None
    rows = conn.execute("SELECT * FROM pipeline_roots ORDER BY retired_at IS NULL, id").fetchall()
    for row in rows:  # retired first: same folder wins over an overlap
        theirs_id = f"{row['device']}:{row['inode']}" if row["device"] is not None else None
        if place.written == row["written_key"] or place.real == row["real_key"]:
            return int(row["id"])
        if mine_id is not None and mine_id == theirs_id and _still(row["path"], place.path):
            return int(row["id"])
    for row in rows:
        if row["id"] in held or row["retired_at"] is not None:
            continue
        _refuse_overlap(row, place, mine_id)
    return None


def _refuse_overlap(row: sqlite3.Row, place: _Place, mine_id: str | None) -> None:
    theirs_id = f"{row['device']}:{row['inode']}" if row["device"] is not None else None
    for mine, theirs in ((place.written, row["written_key"]), (place.real, row["real_key"])):
        if _inside(mine, theirs) or _inside(theirs, mine):
            raise RootOverlapError(row["path"], row["id"], inside=_inside(mine, theirs))
    if theirs_id in place.ancestors and _still(row["path"], place.ancestors[theirs_id]):
        raise RootOverlapError(row["path"], row["id"], inside=True)
    if mine_id is not None and mine_id in json.loads(row["ancestors"]):
        raise RootOverlapError(row["path"], row["id"], inside=False)


def _prefix(inner: str, outer: str) -> str:
    """Bars at the joint off: a path kept as written may end with one (backup of another system)."""
    return inner[len(outer) :].replace(os.sep, "/").strip("/") + "/"


def is_text(path: str) -> bool:
    """Linux name in another encoding comes as lone surrogates (Python, PEP 383)."""
    try:
        path.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True
