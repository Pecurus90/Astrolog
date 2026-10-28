"""Sky brightness of solved shots (ADR 0022 point 8): ASTAP's method, the catalogue beside ASTAP,
the camera's bias at that offset. Written by the stage and by a declared bias, never by a reader."""

import sqlite3
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..db.transaction import transaction
from .pixels import Pixels, read_pixels
from .scan import busy
from .sqm import Wcs, calibrate, scale_arcsec, sky_brightness
from .star_catalogue import catalogue_in

# Shots it is for (ADR 0022 point 8): mono behind L, colour behind no filter or a broad one.
# Readers filter with it too: a filter answered later changes the set.
SQM_SHOTS = (
    "((c.bayer = 1 AND (c.filter IS NULL OR p.standard IN ('l', 'uvir', 'none')"
    "   OR (p.filter_name IS NOT NULL AND NOT EXISTS (SELECT 1 FROM pipeline_filter_bands AS b"
    "   WHERE b.filter_name = p.filter_name AND b.band NOT IN ('l', 'uvir')))))"
    " OR (ifnull(c.bayer, 0) = 0 AND (p.standard = 'l'"
    "   OR (p.filter_name IS NOT NULL AND NOT EXISTS (SELECT 1 FROM pipeline_filter_bands AS b"
    "   WHERE b.filter_name = p.filter_name AND b.band <> 'l')))))"
)

# Shots with their sky row and solution, without a sky brightness yet; card of the measured file.
PENDING = (  # SQM_SHOTS is a constant: nothing from outside in the text
    "SELECT k.frame_id, k.airmass, m.file_id, f.rel_path, c.bayer, c.bin_x, c.camera, c.offset,"  # noqa: S608
    " s.ra_deg, s.dec_deg, s.crpix1, s.crpix2, s.cd1_1, s.cd1_2, s.cd2_1, s.cd2_2"
    " FROM pipeline_sky AS k JOIN pipeline_measures AS m ON m.frame_id = k.frame_id"
    " JOIN pipeline_files AS f ON f.id = m.file_id"
    " JOIN pipeline_cards AS c ON c.file_id = m.file_id"
    " JOIN pipeline_solutions AS s ON s.frame_id = k.frame_id AND s.outcome = 'solved'"
    " LEFT JOIN pipeline_filter_spellings AS p ON p.written = c.filter"
    " WHERE f.root_id = :root AND k.solved = 1 AND s.crpix1 IS NOT NULL"
    " AND NOT EXISTS (SELECT 1 FROM pipeline_sqm AS q WHERE q.frame_id = k.frame_id)"
    f" AND {SQM_SHOTS} ORDER BY k.frame_id"
)

BIAS = "SELECT bias_adu FROM pipeline_camera_bias WHERE camera = ? AND offset IS ?"

INSERT = (
    "INSERT INTO pipeline_sqm (frame_id, file_id, outcome, catalogue, zero_point_mag,"
    " calibration_stars, sky_adu, colour, bias_adu, sqm, duration_s, computed_at)"
    " VALUES (:frame_id, :file_id, :outcome, :catalogue, :zero_point_mag, :calibration_stars,"
    " :sky_adu, :colour, :bias_adu, :sqm, :duration_s, :computed_at)"
)


@dataclass
class SqmResult:
    written: int = 0


def sqm_root(
    conn: sqlite3.Connection, root_id: int, now: str, catalogues: Path | None,
    *, stop: threading.Event | None = None,
) -> SqmResult:  # fmt: skip
    """One shot at a time, a write each. No Gaia BP catalogue in `catalogues`: all wait."""
    code = None if catalogues is None else catalogue_in(catalogues)
    if code is None or catalogues is None:
        return SqmResult()
    with busy(root_id):
        root = conn.execute("SELECT path FROM pipeline_roots WHERE id = ?", (root_id,)).fetchone()
        result = SqmResult()
        for row in conn.execute(PENDING, {"root": root_id}).fetchall():
            if stop is not None and stop.is_set():
                break
            path = Path(root["path"], row["rel_path"])
            try:
                values = _measured(conn, path, row, (catalogues, code))
            except OSError:  # an area file missing: catalogue half installed, the shot waits
                continue
            with transaction(conn, immediate=True):
                conn.execute(INSERT, values | {"computed_at": now})
            result.written += 1
        return result


def declare_bias(
    conn: sqlite3.Connection, camera: str, offset: int | None, bias_adu: float
) -> None:
    """The camera's bias at that offset; its shots' sky brightness written again."""
    with transaction(conn, immediate=True):
        conn.execute(
            "DELETE FROM pipeline_camera_bias WHERE camera = ? AND offset IS ?", (camera, offset)
        )
        conn.execute(
            "INSERT INTO pipeline_camera_bias (camera, offset, bias_adu) VALUES (?, ?, ?)",
            (camera, offset, bias_adu),
        )
        shots = conn.execute(
            "SELECT q.frame_id, q.zero_point_mag, q.sky_adu, q.colour, k.airmass, s.cd1_2, s.cd2_2"
            " FROM pipeline_sqm AS q JOIN pipeline_sky AS k ON k.frame_id = q.frame_id"
            " JOIN pipeline_solutions AS s ON s.frame_id = q.frame_id"
            " JOIN pipeline_cards AS c ON c.file_id = q.file_id"
            " WHERE q.outcome = 'measured' AND c.camera = ? AND c.offset IS ?",
            (camera, offset),
        ).fetchall()
        for shot in shots:
            conn.execute(
                "UPDATE pipeline_sqm SET bias_adu = ?, sqm = ? WHERE frame_id = ?",
                (bias_adu, _brightness(shot, bias_adu), shot["frame_id"]),
            )


def _measured(
    conn: sqlite3.Connection, path: Path, row: sqlite3.Row, catalogue: tuple[Path, str]
) -> dict[str, object]:
    values: dict[str, object] = {
        "frame_id": row["frame_id"], "file_id": None, "outcome": "no_altitude",
        "catalogue": None, "zero_point_mag": None, "calibration_stars": None, "sky_adu": None,
        "colour": None, "bias_adu": None, "sqm": None, "duration_s": None,
    }  # fmt: skip
    if row["airmass"] is None:  # ASTAP: "Negative altitude calculated!"
        return values
    start = time.perf_counter()
    values |= {"file_id": row["file_id"], "outcome": "unreadable"}
    read = read_pixels(path)
    if isinstance(read, Pixels):
        colour = row["bayer"] == 1 and (row["bin_x"] or 1) == 1  # ASTAP: Bayer only unbinned
        found = calibrate(read.data, _wcs(row), catalogue[0], catalogue[1], colour=colour)
        values |= {"outcome": "calibration_failed", "catalogue": catalogue[1]}
        values["colour"] = int(colour)
        if found is not None:
            bias = conn.execute(BIAS, (row["camera"], row["offset"])).fetchone()
            values |= {
                "outcome": "measured", "zero_point_mag": found.zero_point_mag,
                "calibration_stars": found.stars, "sky_adu": found.sky_adu,
                "bias_adu": None if bias is None else bias["bias_adu"],
            }  # fmt: skip
            values["sqm"] = _brightness(dict(row) | values, bias and bias["bias_adu"])
    return values | {"duration_s": time.perf_counter() - start}


def _brightness(shot: Mapping[str, Any], bias_adu: float | None) -> float | None:
    """Colour without bias: none, up to 0.9 mag off; mono without: written, 0.03-0.18 off."""
    if shot["colour"] and bias_adu is None:
        return None
    scale = scale_arcsec(shot["cd1_2"], shot["cd2_2"])
    zero_point, sky, airmass = shot["zero_point_mag"], shot["sky_adu"], shot["airmass"]
    return sky_brightness(zero_point, sky, bias_adu or 0.0, scale, airmass)


def _wcs(row: sqlite3.Row) -> Wcs:
    return Wcs(
        row["ra_deg"], row["dec_deg"], (row["crpix1"], row["crpix2"]),
        (row["cd1_1"], row["cd1_2"], row["cd2_1"], row["cd2_2"]),
    )  # fmt: skip
