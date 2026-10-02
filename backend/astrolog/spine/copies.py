"""A frame is a copy only if a twin is more original; on equal evidence both count, since guessing
would merge two real frames shot at the same instant. A copy points to the leader in one step."""

import sqlite3
from collections.abc import Collection, Iterable
from itertools import groupby
from typing import Any

from . import rewrite


def _shot(row: sqlite3.Row) -> tuple[Any, Any, Any]:
    return row["date_obs"], row["instrument_raw"], row["exposure_s"]


def decide(
    rows: Iterable[sqlite3.Row], frame_ids: Collection[int]
) -> tuple[dict[int, int | None], dict[int, str | None], list[int]]:
    """`(copy of, mark, twins to redo)`; `rows` are the broods sorted by shot. Twins already done
    that point elsewhere are redone: a raw can arrive after its copy, which would count twice."""
    in_queue = set(frame_ids)
    copy_of: dict[int, int | None] = dict.fromkeys(frame_ids)
    marks: dict[int, str | None] = {}
    redo: list[int] = []
    for _, brood in groupby(rows, key=_shot):
        seen = []
        for r in brood:
            marks[r["id"]] = mark = rewrite.mark_of(r)
            seen.append((r["id"], rewrite.originality(r, mark), r["copy_of"]))
        best = min(rank for _, rank, _ in seen)
        leader = min(i for i, rank, _ in seen if rank == best)
        for i, rank, was in seen:
            copy_of[i] = None if rank == best else leader
            if i not in in_queue and was != copy_of[i]:
                redo.append(i)
    return copy_of, marks, redo
