"""The typeless question's folders, written so the review page reads them instead of composing
every typeless frame's folder at each opening. An answer does not rewrite them: counts stay."""

import sqlite3

from ..astap import Reason
from ..db.replace_table import replace_rows
from ..fits.frame_type import FrameType
from . import declarations as decl
from . import frame_folder as folder
from . import typeless

# Starless frames are not asked (`typeless`). The `+` before `sv.stage` keeps the query on the
# file-type index: without it, it starts from the stages even where nothing is typeless.
_BY_FOLDER = f"""
SELECT {folder.COLUMNS}, SUM(f.copy_of IS NULL) AS n,
       SUM(sv.status = 'failed' AND IFNULL(sv.reason, '') <> '{Reason.NO_STARS}') AS undecided
FROM frames f {folder.JOIN}
JOIN frame_stages sv ON sv.frame_id = f.id AND +sv.stage = 'solve'
WHERE f.image_type = '{FrameType.UNKNOWN}'
GROUP BY root, sub
"""  # noqa: S608 - constants from frame_folder, astap and frame_type, not a user value

_COLUMNS = ("key", "root", "sub", "frames", "position")

# Answered folders inside a live registered root, the deepest root first.
_ANSWERED = f"""
SELECT dc.entity_key AS key, d.root_path AS root, d.root_key FROM declarations dc
JOIN folders d ON d.retired_at IS NULL AND (dc.entity_key = d.root_key
  OR substr(dc.entity_key, 1, length(d.root_key) + 1) = d.root_key || '/')
WHERE dc.entity_type = '{decl.EntityType.FOLDER}' AND dc.field = '{decl.FOLDER_TYPE}'
  AND dc.value IN ({", ".join(f"'{a}'" for a in decl.TypeAnswer)})
ORDER BY length(d.root_key) DESC
"""  # noqa: S608 - constants of declarations


def write(conn: sqlite3.Connection) -> None:
    """A folder where the sky tells every frame and nobody answered asks nothing. An answered one
    stays even when its frames left (the scan keeps no calibration): or it could not be undone."""

    def silent(r: sqlite3.Row) -> bool:
        key = folder.folder_key(r["root"], r["sub"])
        return not r["undecided"] and typeless.answer(conn, key) is None

    groups = folder.counted(conn, _BY_FOLDER, skip=silent)
    seen = {g["key"] for g in groups}
    for r in conn.execute(_ANSWERED):
        if r["key"] in seen:
            continue
        seen.add(r["key"])
        inside = r["key"][len(r["root_key"]) + 1 :]
        groups.append({"key": r["key"], "root": r["root"], "sub": inside and inside + "/",
                       "frames": 0})  # fmt: skip
    rows = [(g["key"], g["root"], g["sub"], g["frames"], i) for i, g in enumerate(groups)]
    replace_rows(conn, "typeless_folders", _COLUMNS, rows)
