"""A night's measures per object and filter, written once; until step 40 each spine frame takes
those of its own file, same folder and path (ADR 0045). SQL on both worlds, imports neither."""

import json
import os
import sqlite3
from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

from .db.replace_table import replace_rows
from .db.transaction import transaction
from .measure_list import MEASURES, Table
from .units import quantile

BINS = 24  # the spread under each tile [D tavola v76, MisureFrame:227]

_ALIAS = {Table.MEASURES: "m", Table.SKY: "k", Table.SQM: "q"}
_KEYS = tuple(e.key for e in MEASURES)
# Every measure of a spine frame `f` through the bridge: the read of a night uses them too.
VALUES = ", ".join(f"{_ALIAS[e.table]}.{e.key}" for e in MEASURES)
JOINS = """
LEFT JOIN night_measure_frames b ON b.frame_id = f.id
LEFT JOIN pipeline_measures m ON m.frame_id = b.pipeline_frame_id
LEFT JOIN pipeline_sky k ON k.frame_id = b.pipeline_frame_id
LEFT JOIN pipeline_sqm q ON q.frame_id = b.pipeline_frame_id"""
NEVER = ("not_supported", "rewritten", "broken")  # read, no frame, never measured

# Per present position, the present pipeline file at the same path (roots paired in Python): its
# frame, or why it will never have one. Unreadable or incomplete is tried again: no row.
_PAIRS = f"""
SELECT po.frame_id, MIN(pf.frame_id) AS pipeline_frame_id,
       MIN(CASE WHEN pf.skip_reason IN {NEVER} THEN pf.skip_reason END) AS never
FROM positions po JOIN pipeline_files pf ON pf.rel_path = po.rel_path AND pf.state = 'present'
WHERE po.status = 'present' AND po.folder_id = ? AND pf.root_id = ?
GROUP BY po.frame_id
HAVING MIN(pf.frame_id) IS NOT NULL OR never IS NOT NULL
"""  # noqa: S608 - our constants

# The frames the Nights page counts (spine/counts.py), with their measures if bridged.
_FRAMES = f"""
SELECT f.night_id, f.object_id, f.filter_id, b.skip_reason, m.outcome,
       c.camera, c.gain, c.exposure_s, {VALUES}
FROM frames f{JOINS}
LEFT JOIN pipeline_cards c ON c.file_id = m.file_id
WHERE f.night_id IS NOT NULL AND f.copy_of IS NULL
"""  # noqa: S608 - our columns

_MEASURE_COLUMNS = (
    "night_id", "object_id", "filter_id", "key", "frames", "measured", "median", "q1", "q3", "bins",
)  # fmt: skip
_GROUP_COLUMNS = ("night_id", "object_id", "filter_id", "frames", "pending", "comparable")

type GroupKey = tuple[int, int | None, int | None]


@dataclass(slots=True)
class _Group:
    frames: int = 0
    pending: int = 0
    setups: set[tuple[object, object, object]] = field(default_factory=set)
    values: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))


def rebuild(conn: sqlite3.Connection) -> None:
    """All of it, in one transaction: whoever changes frames, files or nights calls it at its end
    (pipeline/run.py, spine/group.py, a camera's bias)."""
    with transaction(conn):
        bridge = ("frame_id", "pipeline_frame_id", "skip_reason")
        replace_rows(conn, "night_measure_frames", bridge, _bridge(conn))
        groups: dict[GroupKey, _Group] = defaultdict(_Group)
        for row in conn.execute(_FRAMES):
            for key in _keys_of(row["night_id"], row["object_id"], row["filter_id"]):
                _add(groups[key], row)
        replace_rows(conn, "night_measures", _MEASURE_COLUMNS, _measure_rows(groups))
        replace_rows(conn, "night_measure_groups", _GROUP_COLUMNS, _group_rows(groups))


def _bridge(conn: sqlite3.Connection) -> list[tuple[int, int | None, str | None]]:
    """The spine keeps a folder as the user added it, the pipeline normalised: compared as the
    disk compares them (case, separators, `..`)."""
    roots = {_same(r["path"]): r["id"] for r in conn.execute("SELECT id, path FROM pipeline_roots")}
    pairs: list[tuple[int, int | None, str | None]] = []
    for folder in conn.execute("SELECT id, root_path FROM folders").fetchall():
        root = roots.get(_same(folder["root_path"]))
        if root is not None:
            pairs += [
                (f, p, None if p is not None else why)
                for f, p, why in conn.execute(_PAIRS, (folder["id"], root))
            ]
    return pairs


def _same(path: str) -> str:
    return os.path.normcase(os.path.normpath(path))


def _keys_of(night: int, obj: int | None, flt: int | None) -> Iterator[GroupKey]:
    """The night whole, per object, per filter, per object and filter; NULL: all of them."""
    yield night, None, None
    if obj is not None:
        yield night, obj, None
    if flt is not None:
        yield night, None, flt
    if obj is not None and flt is not None:
        yield night, obj, flt


def _add(group: _Group, row: sqlite3.Row) -> None:
    group.frames += 1
    if row["outcome"] is None:
        group.pending += row["skip_reason"] is None
        return
    if row["outcome"] == "measured":  # a file read badly has no setup to compare
        group.setups.add((row["camera"], row["gain"], row["exposure_s"]))
    for key in _KEYS:
        if (value := row[key]) is not None:
            group.values[key].append(float(value))


def _measure_rows(groups: dict[GroupKey, _Group]) -> Iterator[tuple[object, ...]]:
    for (night, obj, flt), group in groups.items():
        for key in _KEYS:
            values = sorted(group.values.get(key, ()))
            if not values:
                yield night, obj, flt, key, group.frames, 0, None, None, None, None
                continue
            q1, median, q3 = (quantile(values, p) for p in (0.25, 0.5, 0.75))
            bins = _bins(values)
            yield night, obj, flt, key, group.frames, len(values), median, q1, q3, bins


def _bins(ordered: list[float]) -> str | None:
    low, high = ordered[0], ordered[-1]
    if high == low:
        return None
    counts = [0] * BINS
    for value in ordered:
        counts[min(int((value - low) / (high - low) * BINS), BINS - 1)] += 1
    return json.dumps(counts)


def _group_rows(groups: dict[GroupKey, _Group]) -> Iterable[tuple[object, ...]]:
    return [
        (night, obj, flt, g.frames, g.pending, int(len(g.setups) <= 1))
        for (night, obj, flt), g in groups.items()
    ]
