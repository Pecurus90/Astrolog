"""A frame's folder: the one holding the file, not the registered root, from its first present
position in a live folder. Root and subfolder travel in the row: re-splitting a key goes wrong."""

import sqlite3
from collections.abc import Callable, Mapping
from typing import Any

_FIRST_POSITION = """
  SELECT p2.id FROM positions p2 JOIN folders d2 ON d2.id = p2.folder_id
  WHERE p2.frame_id = f.id AND p2.status = 'present' AND d2.retired_at IS NULL
  ORDER BY p2.id LIMIT 1
"""

# `rtrim` strips from the right every character that is NOT a slash, i.e. the file name, leaving
# `night/M51/`; a file in the root has no slash and leaves it empty.
_SUB = "rtrim(p.rel_path, replace(p.rel_path, '/', ''))"
COLUMNS = f"d.root_path AS root, {_SUB} AS sub"
JOIN = f"JOIN positions p ON p.id = ({_FIRST_POSITION}) JOIN folders d ON d.id = p.folder_id"

# `folder_key` in SQL, for comparing inside a query; the two must say the same thing.
_ROOT_KEY = r"rtrim(replace(d.root_path, '\', '/'), '/')"
_DENTRO = f"trim({_SUB}, '/')"
KEY = f"{_ROOT_KEY} || CASE WHEN {_DENTRO} = '' THEN '' ELSE '/' || {_DENTRO} END"
# For a query that already has `frames f`.
KEY_OF_FRAME = (
    f"SELECT {KEY} FROM positions p"  # noqa: S608 - constants
    f" JOIN folders d ON d.id = p.folder_id WHERE p.id = ({_FIRST_POSITION})"
)

# Searched from the folder, by index on its positions: starting from the frames would rebuild the
# folder of every frame in the archive at each answer.
_IN_FOLDER = (
    "SELECT f.id, f.image_type FROM folders d"  # noqa: S608 - constants of this file
    " CROSS JOIN positions p ON p.folder_id = d.id"
    " CROSS JOIN frames f ON f.id = p.frame_id"
    f" WHERE d.root_path = ? AND p.rel_path >= ? AND p.rel_path < ? AND {_SUB} = ?"
    f" AND p.id = ({_FIRST_POSITION})"
)
# `night/` runs to `night0`, `0` being the character right after the slash. Under the root, an
# empty BLOB, which SQLite sorts after every text.
_AFTER_EVERY_PATH = b""

# Anything carrying a folder's `root` and `sub`: a query row or a page row.
type FolderRow = sqlite3.Row | Mapping[str, Any]


def folder_key(root_path: str, sub: str = "") -> str:
    """Also what is shown. Always forward slashes: Windows accepts them, and the system separator
    would make two machines disagree."""
    root = root_path.replace("\\", "/").rstrip("/")
    dentro = sub.strip("/")
    return f"{root}/{dentro}" if dentro else root


def key_of_path(root_path: str, rel_path: str) -> str:
    """Without the DB, for the scan that decides before writing the frame."""
    dritto = rel_path.replace("\\", "/")
    return folder_key(root_path, dritto.rsplit("/", 1)[0] if "/" in dritto else "")


def frames_in(conn: sqlite3.Connection, row: FolderRow) -> list[sqlite3.Row]:
    """Copies included, with the file type: the answerer picks which to requeue."""
    sub = row["sub"]
    end = sub[:-1] + "0" if sub else _AFTER_EVERY_PATH
    return conn.execute(_IN_FOLDER, (row["root"], sub, end, sub)).fetchall()


def group_of(groups: dict[str, dict[str, Any]], row: FolderRow, **fields: Any) -> dict[str, Any]:
    """Created with `fields` the first time; root and subfolder stay in the group."""
    key = folder_key(row["root"], row["sub"])
    return groups.setdefault(key, {"key": key, "root": row["root"], "sub": row["sub"], **fields})


def counted(
    conn: sqlite3.Connection,
    query: str,
    *,
    skip: Callable[[sqlite3.Row], bool] | None = None,
) -> list[dict[str, Any]]:
    """Largest first. A folder left at zero asks nothing: only copies are there, and a question on
    zero frames makes no sense."""
    groups: dict[str, dict[str, Any]] = {}
    for row in conn.execute(query):
        if skip and skip(row):
            continue
        group_of(groups, row, frames=0)["frames"] += row["n"] or 0
    return sorted(
        (g for g in groups.values() if g["frames"]), key=lambda g: (-g["frames"], g["key"])
    )
