"""A shot's files, for the stages that read one per shot (solve, measure): the plain file before
its fpack copy, which fewer readers open."""

import sqlite3


def is_fz(name: str) -> bool:
    return name.lower().endswith(".fz")


def first_per_shot(rows: list[sqlite3.Row]) -> list[sqlite3.Row]:
    """The query's order kept: a shot's plain file before its copies."""
    seen: set[int] = set()
    first = []
    for row in rows:
        if row["frame_id"] not in seen:
            seen.add(row["frame_id"])
            first.append(row)
    return first
