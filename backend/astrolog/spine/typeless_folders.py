"""The typeless question's folders, written so the review page reads them instead of composing
every typeless frame's folder at each opening. An answer does not rewrite them: counts stay."""

import sqlite3

from ..astap import NO_STARS
from ..db.replace_table import replace_rows
from ..fits.frame_type import UNKNOWN
from . import frame_folder as folder
from . import typeless

# Starless frames are calibrations, not asked. The `+` before `sv.stage` keeps the query on the
# file-type index: without it, it starts from the stages even where nothing is typeless.
_BY_FOLDER = f"""
SELECT {folder.COLUMNS}, SUM(f.copy_of IS NULL) AS n,
       SUM(sv.status = 'failed' AND IFNULL(sv.reason, '') <> '{NO_STARS}') AS undecided
FROM frames f {folder.JOIN}
JOIN frame_stages sv ON sv.frame_id = f.id AND +sv.stage = 'solve'
WHERE f.image_type = '{UNKNOWN}'
GROUP BY root, sub
"""  # noqa: S608 - constants from frame_folder, astap and frame_type, not a user value

_COLUMNS = ("key", "root", "sub", "frames", "position")


def write(conn: sqlite3.Connection) -> None:
    """A folder where the sky tells every frame and nobody answered asks nothing."""

    def silent(r: sqlite3.Row) -> bool:
        key = folder.folder_key(r["root"], r["sub"])
        return not r["undecided"] and typeless.answer(conn, key) is None

    groups = folder.counted(conn, _BY_FOLDER, skip=silent)
    rows = [(g["key"], g["root"], g["sub"], g["frames"], i) for i, g in enumerate(groups)]
    replace_rows(conn, "typeless_folders", _COLUMNS, rows)
