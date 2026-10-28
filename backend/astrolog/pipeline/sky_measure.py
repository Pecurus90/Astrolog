"""Measures of a shot on the sky (ADR 0022 points 5 and 7, docs/domini/misure.md): its pixel
measures with the solution, the site and the time. Written by the stage, never by a reader."""

import datetime as dt
import sqlite3
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ..db.transaction import transaction
from .airmass import airmass_of, apparent_altitude, at_zenith
from .altitude import true_altitudes
from .footprint import position_angle
from .scan import busy

# Measured shots without a row, or with one before their solution came. Site and time from the
# card of the file measured: a copy's card may say other.
PENDING = (
    "SELECT m.frame_id, m.hfd_px, m.fwhm_px, m.angle_deg, m.gradient_angle_deg,"
    " c.start_utc, c.exposure_s, c.site_lat_deg, c.site_lon_deg,"
    " c.pointing_ra_deg, c.pointing_dec_deg, s.ra_deg, s.dec_deg, s.scale_arcsec_px,"
    " s.cd1_1, s.cd1_2, s.cd2_1, s.cd2_2"
    " FROM pipeline_measures AS m JOIN pipeline_files AS f ON f.id = m.file_id"
    " JOIN pipeline_cards AS c ON c.file_id = m.file_id"
    " LEFT JOIN pipeline_solutions AS s ON s.frame_id = m.frame_id AND s.outcome = 'solved'"
    " LEFT JOIN pipeline_sky AS k ON k.frame_id = m.frame_id"
    " WHERE f.root_id = :root AND m.outcome <> 'unreadable'"
    " AND (k.frame_id IS NULL OR (k.solved = 0 AND s.frame_id IS NOT NULL))"
    " ORDER BY m.frame_id"
)

UPSERT = (
    "INSERT INTO pipeline_sky (frame_id, solved, mid_utc, altitude_deg, airmass, hfd_arcsec,"
    " fwhm_arcsec, hfd_zenith_arcsec, fwhm_zenith_arcsec, angle_pa_deg, angle_axis,"
    " gradient_pa_deg, computed_at)"
    " VALUES (:frame_id, :solved, :mid_utc, :altitude_deg, :airmass, :hfd_arcsec, :fwhm_arcsec,"
    " :hfd_zenith_arcsec, :fwhm_zenith_arcsec, :angle_pa_deg, :angle_axis, :gradient_pa_deg,"
    " :computed_at)"
    " ON CONFLICT (frame_id) DO UPDATE SET solved = excluded.solved, mid_utc = excluded.mid_utc,"
    " altitude_deg = excluded.altitude_deg, airmass = excluded.airmass,"
    " hfd_arcsec = excluded.hfd_arcsec, fwhm_arcsec = excluded.fwhm_arcsec,"
    " hfd_zenith_arcsec = excluded.hfd_zenith_arcsec,"
    " fwhm_zenith_arcsec = excluded.fwhm_zenith_arcsec, angle_pa_deg = excluded.angle_pa_deg,"
    " angle_axis = excluded.angle_axis, gradient_pa_deg = excluded.gradient_pa_deg,"
    " computed_at = excluded.computed_at"
)

# Nearer to East-West than to North-South: along RA. [T] the two axes split at half a right angle
AXIS_SPLIT_DEG = 45.0


@dataclass
class SkyResult:
    written: int = 0


def sky_root(
    conn: sqlite3.Connection, root_id: int, now: str, *, stop: threading.Event | None = None
) -> SkyResult:
    """No pixels read: the root's altitudes in one erfa call, then one write."""
    with busy(root_id):
        rows = conn.execute(PENDING, {"root": root_id}).fetchall()
        if stop is not None and stop.is_set():
            return SkyResult()
        values = [_on_sky(row, now) for row in rows]
        _with_altitudes(rows, values)
        with transaction(conn, immediate=True):
            conn.executemany(UPSERT, values)
        return SkyResult(written=len(values))


def mid_exposure(start_utc: str | None, exposure_s: float | None) -> str | None:
    """Start plus half the exposure; exposure unknown: the start."""
    if start_utc is None:
        return None
    start = dt.datetime.fromisoformat(start_utc)
    return (start + dt.timedelta(seconds=(exposure_s or 0.0) / 2)).isoformat(
        timespec="microseconds"
    )


def sky_axis(position_deg: float) -> str:
    """'ra' along East-West, 'dec' along North-South: the nearer one."""
    return "ra" if abs(position_deg % 180.0 - 90.0) < AXIS_SPLIT_DEG else "dec"


def _on_sky(row: sqlite3.Row, now: str) -> dict[str, object]:
    """All but the altitude: what the solution alone gives."""
    scale = row["scale_arcsec_px"]
    cd = (row["cd1_1"], row["cd1_2"], row["cd2_1"], row["cd2_2"])
    axis = _turned(cd, row["angle_deg"])
    angle = None if axis is None else axis % 180.0
    return {
        "frame_id": row["frame_id"], "solved": int(row["ra_deg"] is not None),
        "mid_utc": mid_exposure(row["start_utc"], row["exposure_s"]),
        "hfd_arcsec": _arcsec(row["hfd_px"], scale), "fwhm_arcsec": _arcsec(row["fwhm_px"], scale),
        "angle_pa_deg": angle, "angle_axis": None if angle is None else sky_axis(angle),
        "gradient_pa_deg": _turned(cd, row["gradient_angle_deg"]),
        "altitude_deg": None, "airmass": None, "computed_at": now,
    }  # fmt: skip


def _arcsec(px: float | None, scale: float | None) -> float | None:
    return None if px is None or scale is None else px * scale


def _turned(cd: tuple[float | None, ...], angle_deg: float | None) -> float | None:
    """A pixel angle on the sky; no matrix or no angle: None."""
    if angle_deg is None or None in cd:
        return None
    return position_angle(cd, angle_deg)  # type: ignore[arg-type]


def apparent_altitudes(rows: Sequence[Mapping[str, Any]]) -> list[float | None]:
    """Centre solved, else the card's pointing; the card's site; mid exposure; one erfa call.
    None: one of them unknown. The comparison tool calls it too, on a card."""
    placed = [
        (i, sky, (row["site_lat_deg"], row["site_lon_deg"]), mid)
        for i, row in enumerate(rows)
        if (sky := _centre(row)) is not None and row["site_lat_deg"] is not None
        and (mid := mid_exposure(row["start_utc"], row["exposure_s"])) is not None
    ]  # fmt: skip
    instants = [dt.datetime.fromisoformat(mid) for *_, mid in placed]
    found = true_altitudes([p[1] for p in placed], instants, [p[2] for p in placed])
    altitudes: list[float | None] = [None] * len(rows)
    for (i, *_), true in zip(placed, found, strict=True):
        altitudes[i] = apparent_altitude(true)
    return altitudes


def _with_altitudes(rows: list[sqlite3.Row], values: list[dict[str, object]]) -> None:
    """Altitude, air mass, zenith values."""
    for value, altitude in zip(values, apparent_altitudes([dict(r) for r in rows]), strict=True):
        airmass = None if altitude is None else airmass_of(altitude)
        value |= {"altitude_deg": altitude, "airmass": airmass}
        value["hfd_zenith_arcsec"] = at_zenith(value["hfd_arcsec"], airmass)  # type: ignore[arg-type]
        value["fwhm_zenith_arcsec"] = at_zenith(value["fwhm_arcsec"], airmass)  # type: ignore[arg-type]


def _centre(row: Mapping[str, Any]) -> tuple[float, float] | None:
    if row["ra_deg"] is not None:
        return row["ra_deg"], row["dec_deg"]
    if row["pointing_ra_deg"] is not None:
        return row["pointing_ra_deg"], row["pointing_dec_deg"]
    return None
