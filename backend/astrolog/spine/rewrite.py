"""The rewrite mark: that a file was rewritten after the camera, never by whom, and alone it takes
nothing from anyone. It lets `copies.py` pick the original between two twins."""

import sqlite3
from enum import StrEnum

from ..fits.frame_type import program_names, says_calibrated
from ..fits.header_keys import HeaderLike
from ..fits.header_read import header_from_json
from ..vocab.software import normalize_software


class RewriteMark(StrEnum):
    """The words of `frames.rewrite_mark`."""

    CALIBRATED = "calibrated"
    REWRITTEN = "rewritten"


def rewrite_mark(header: HeaderLike) -> RewriteMark | None:
    """`calibrated`, or `rewritten` when two programs vocab tells apart are named and one is a
    writer key: one name alone is the raw of a Voyager or SGP user, who sign exactly there."""
    if says_calibrated(header):
        return RewriteMark.CALIBRATED
    acquirers, writers = program_names(header)
    if not writers:
        return None
    programs = {normalize_software(n) for n in acquirers + writers}
    return RewriteMark.REWRITTEN if len(programs) > 1 else None


def mark_of(row: sqlite3.Row) -> RewriteMark | None:
    return rewrite_mark(header_from_json(row["header_json"]))


# Calibrations applied mean the pixels changed; two programs only that the header was touched,
# which a solver or metadata fixer also does to a raw. Between the two, the calibrated is worked.
MARK_WEIGHT = {None: 0, RewriteMark.REWRITTEN: 1, RewriteMark.CALIBRATED: 2}


def originality(row: sqlite3.Row, mark: RewriteMark | None) -> tuple[int, int]:
    """Lower is more original. The capture software alone is not enough: a processor often keeps
    the acquiring program's key."""
    return (
        MARK_WEIGHT[mark],
        0 if normalize_software(row["software_raw"]) is not None else 1,
    )
