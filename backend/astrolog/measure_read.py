"""A frame's measures as the pipeline's stages wrote them, each with its value or why it has none
(measure_list.py). Reads only, its tables by SQL as `api/sites.py`: no pipeline import."""

import sqlite3
from dataclasses import dataclass

from .measure_list import MEASURES, Entry, Silent, Table
from .sqm_shots import SQM_SHOTS

# One row: the frame's card and filter, whether sky brightness is for it. SQM_SHOTS a constant.
_ADMITTED = (
    "SELECT 1 FROM pipeline_measures AS m JOIN pipeline_cards AS c ON c.file_id = m.file_id"  # noqa: S608
    " LEFT JOIN pipeline_filter_spellings AS p ON p.written = c.filter"
    f" WHERE m.frame_id = ? AND {SQM_SHOTS}"
)
# A measure row with no pixels read; too_few_stars keeps what it has, the rest silent with it.
_STAGE_SILENT = {
    "unreadable": Silent.UNREADABLE, "not_supported": Silent.NOT_SUPPORTED,
    "fz_unsupported": Silent.FZ_UNSUPPORTED,
}  # fmt: skip
_ROW_SILENT = {**_STAGE_SILENT, "too_few_stars": Silent.TOO_FEW_STARS}
_SQM_SILENT = {
    "calibration_failed": Silent.CALIBRATION_FAILED, "no_altitude": Silent.NO_ALTITUDE,
    "unreadable": Silent.UNREADABLE,
}  # fmt: skip
# Sky columns turned from a pixel one (sky_measure.py): NULL there, the pixel one's reason.
_FROM_PX = {
    "hfd_arcsec": "hfd_px", "hfd_zenith_arcsec": "hfd_px", "fwhm_arcsec": "fwhm_px",
    "fwhm_zenith_arcsec": "fwhm_px", "off_axis_arcsec": "off_axis_px",
    "angle_pa_deg": "angle_deg", "gradient_pa_deg": "gradient_angle_deg",
}  # fmt: skip
_BY_KEY = {e.key: e for e in MEASURES}


@dataclass(frozen=True)
class Value:
    entry: Entry
    value: float | None
    silent: Silent | None  # None with a value


@dataclass(frozen=True)
class FrameMeasures:
    frame_id: int
    measure_outcome: str | None  # None: not measured yet
    solved: bool | None  # None: sky not written yet
    sqm_outcome: str | None  # None: no row
    shape: str | None
    tilt_level: str | None
    sampling_class: str | None
    angle_axis: str | None
    values: list[Value]


def frame_measures(conn: sqlite3.Connection, frame_id: int) -> FrameMeasures | None:
    """None: no such frame."""
    if conn.execute("SELECT 1 FROM pipeline_frames WHERE id = ?", (frame_id,)).fetchone() is None:
        return None
    rows = _rows(conn, frame_id)
    m, k, q = rows[Table.MEASURES], rows[Table.SKY], rows[Table.SQM]
    whole = {
        Table.MEASURES: _measure_silent(m),
        Table.SKY: _sky_silent(m, k),
        Table.SQM: _sqm_silent(conn, frame_id, m, k, q),
    }
    values = [_value(e, rows[e.table], whole[e.table], m) for e in MEASURES]
    return FrameMeasures(
        frame_id=frame_id,
        measure_outcome=None if m is None else m["outcome"],
        solved=None if k is None else bool(k["solved"]),
        sqm_outcome=None if q is None else q["outcome"],
        shape=None if m is None else m["shape"],
        tilt_level=None if m is None else m["tilt_level"],
        sampling_class=None if m is None else m["sampling_class"],
        angle_axis=None if k is None else k["angle_axis"],
        values=values,
    )


def sqm_silent(conn: sqlite3.Connection, frame_id: int) -> Silent | None:
    """Why the frame has no sky brightness, as its measures say it; None with a value."""
    rows = _rows(conn, frame_id)
    m, k, q = rows[Table.MEASURES], rows[Table.SKY], rows[Table.SQM]
    return _value(_BY_KEY["sqm"], q, _sqm_silent(conn, frame_id, m, k, q), m).silent


def _rows(conn: sqlite3.Connection, frame_id: int) -> dict[Table, sqlite3.Row | None]:
    return {
        table: conn.execute(f"SELECT * FROM {table} WHERE frame_id = ?", (frame_id,)).fetchone()  # noqa: S608 - our names
        for table in Table
    }


def _measure_silent(m: sqlite3.Row | None) -> Silent | None:
    if m is None:
        return Silent.NOT_MEASURED_YET
    return _STAGE_SILENT.get(m["outcome"])


def _sky_silent(m: sqlite3.Row | None, k: sqlite3.Row | None) -> Silent | None:
    """Sky written from the cards too when no pixels were read (sky_measure.PENDING)."""
    if k is not None:
        return None
    if m is None or m["outcome"] == "unreadable":
        return _measure_silent(m)
    return Silent.SKY_PENDING


def _sqm_silent(
    conn: sqlite3.Connection,
    frame_id: int,
    m: sqlite3.Row | None,
    k: sqlite3.Row | None,
    q: sqlite3.Row | None,
) -> Silent | None:
    """The whole row's reason; None when it is measured."""
    if q is not None:
        return _SQM_SILENT.get(q["outcome"])
    if (stage := _measure_silent(m)) is not None:
        return stage
    if k is None:
        return Silent.SKY_PENDING
    if not k["solved"]:
        return Silent.NOT_SOLVED
    if conn.execute(_ADMITTED, (frame_id,)).fetchone() is None:
        return Silent.SQM_NOT_THIS_FILTER
    return Silent.SQM_PENDING


def _value(
    entry: Entry, row: sqlite3.Row | None, whole: Silent | None, m: sqlite3.Row | None
) -> Value:
    if whole is not None or row is None:
        return Value(entry, None, whole or Silent.NOT_MEASURED_YET)
    value = row[entry.key]
    if value is not None:
        return Value(entry, float(value), None)
    return Value(entry, None, _why(entry, row, m))


def _why(entry: Entry, row: sqlite3.Row, m: sqlite3.Row | None) -> Silent | None:
    if entry.table is Table.MEASURES and (stage := _ROW_SILENT.get(row["outcome"])) is not None:
        return stage
    if (px := _FROM_PX.get(entry.key)) is not None and m is not None and m[px] is None:
        return _why(_BY_KEY[px], m, m)
    if entry.solved_only and not row["solved"]:
        return Silent.NOT_SOLVED
    altitude = row["altitude_deg"] if entry.on_airmass else None
    if altitude is not None and altitude < 0:
        return Silent.BELOW_HORIZON
    if entry.key == "sqm" and row["colour"] and row["bias_adu"] is None:
        return Silent.NEEDS_CAMERA_BIAS
    return entry.why
