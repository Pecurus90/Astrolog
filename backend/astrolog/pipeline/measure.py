"""Light shots of a root measured from their pixels (ADR 0022, docs/domini/misure.md): one row
per shot, from one present file, written once; never redone by a reader."""

import sqlite3
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from ..db.transaction import transaction
from ..measure_list import STARTS
from .debayer import pattern_of
from .inspection import sampling_class
from .pixels import Pixels, Unmeasurable, Why, read_pixels
from .scan import busy
from .shape import Shape
from .shots import first_per_shot
from .stars import Measured, measure_frame
from .values import as_number

# Light shots without a row, or whose last file was unreadable; plain file before its copy.
PENDING = (
    "SELECT f.id AS file_id, f.frame_id, f.rel_path, c.bayer, c.exposure_s,"
    " h.header ->> '$.BAYERPAT' AS BAYERPAT, h.header ->> '$.XBAYROFF' AS XBAYROFF,"
    " h.header ->> '$.YBAYROFF' AS YBAYROFF, h.header ->> '$.PEDESTAL' AS PEDESTAL"
    " FROM pipeline_files AS f JOIN pipeline_cards AS c ON c.file_id = f.id"
    " JOIN pipeline_headers AS h ON h.file_id = f.id"
    " WHERE f.root_id = :root AND f.state = 'present' AND f.skip_reason IS NULL"
    " AND c.frame_type = 'light'"
    " AND NOT EXISTS (SELECT 1 FROM pipeline_measures AS m"
    "   WHERE m.frame_id = f.frame_id AND m.outcome <> 'unreadable')"
    " ORDER BY f.frame_id, lower(f.rel_path) LIKE '%.fz', f.rel_path"
)

_NUMBERS = (  # TooFewStars: no hfd_px
    "stars", "kept", "hfd_px", "background_adu", "noise_adu", "ceiling_adu", "saturated",
    "psf_snr", "psf_flux_adu", "psf_mean_flux_adu", "psf_count", "psf_signal_weight",
    "gradient_noise", "gradient_angle_deg", "row_banding", "column_banding", "trails", "fwhm_tilt",
    "fwhm_curvature", "elongation_angle_deg", "elongation_coherence", "median_adu", "sigma_adu",
    "entropy_bits", "noise_ratio", "snr", "mstar_adu", "nstar_adu",
)  # fmt: skip
_SHAPE = (
    "shape", "shape_stars", "fwhm_px", "eccentricity", "angle_deg", "fwhm_sigma_px",
    "eccentricity_sigma", "psf_residual", "psf_residual_sigma",
)  # fmt: skip
_LADDER = {start: f"ladder_{start}_dex" for start in STARTS}
_CORNERS = ("hfd_corner_1_px", "hfd_corner_2_px", "hfd_corner_3_px", "hfd_corner_4_px")
_INSPECTION = ("hfd_tilt_pct", "tilt_level", "off_axis_px", *_CORNERS, "hfd_centre_px")  # Measured
_WRITTEN = ("file_id", "outcome", *_NUMBERS, *_SHAPE, "sampling_class", *_INSPECTION,
            *_LADDER.values(), "sky_rate_adu_s", "duration_s", "measured_at")  # fmt: skip
# Only an unreadable row is written over: the others stay (misure.md).
UPSERT = (
    f"INSERT INTO pipeline_measures (frame_id, {', '.join(_WRITTEN)})"  # noqa: S608 - our names
    f" VALUES (:frame_id, {', '.join(f':{c}' for c in _WRITTEN)})"
    f" ON CONFLICT (frame_id) DO UPDATE SET {', '.join(f'{c} = excluded.{c}' for c in _WRITTEN)}"
    " WHERE pipeline_measures.outcome = 'unreadable'"
)


@dataclass
class MeasureResult:
    measured: int = 0
    not_measured: Counter[str] = field(default_factory=Counter)  # outcome -> shots


def measure_root(
    conn: sqlite3.Connection, root_id: int, now: str, *, stop: threading.Event | None = None
) -> MeasureResult:
    """One frame at a time, a write each; a stop ends between two frames."""
    with busy(root_id):
        root = conn.execute("SELECT path FROM pipeline_roots WHERE id = ?", (root_id,)).fetchone()
        rows = first_per_shot(conn.execute(PENDING, {"root": root_id}).fetchall())
        result = MeasureResult()
        for row in rows:
            if stop is not None and stop.is_set():
                break
            outcome = _measure(conn, Path(root["path"], row["rel_path"]), row, now)
            if outcome == "measured":
                result.measured += 1
            else:
                result.not_measured[outcome] += 1
        return result


def _measure(conn: sqlite3.Connection, path: Path, row: sqlite3.Row, now: str) -> str:
    start = time.perf_counter()
    values: dict[str, object] = {key: None for key in _WRITTEN}
    pattern = pattern_of(dict(row))
    read = Unmeasurable(Why.NOT_SUPPORTED)  # a matrix not R G B (CYGM): no debayer for it
    if pattern is not None or not row["bayer"]:
        read = read_pixels(path)
    if isinstance(read, Pixels):
        pedestal = as_number(row["PEDESTAL"]) or 0.0  # ImageAnalysis eq. 8: none written, none off
        found = measure_frame(read.data, saturation=read.saturation, pattern=pattern,
                              pedestal=pedestal)  # fmt: skip
        outcome = "measured" if isinstance(found, Measured) else "too_few_stars"
        values |= {key: getattr(found, key, None) for key in _NUMBERS}
        values |= {column: found.ladder.get(start) for start, column in _LADDER.items()}
        if row["exposure_s"]:  # SkyRate: Median per second of exposure (ImageAnalysis par. 2.1.2)
            values["sky_rate_adu_s"] = found.median_adu / row["exposure_s"]
        if found.shape is not None:
            values |= _shape_values(found.shape)
        if isinstance(found, Measured):
            seen = found.inspection
            corners = seen.corners_px or (None,) * len(_CORNERS)
            values |= dict(zip(_INSPECTION, (seen.tilt_pct, seen.tilt_level, seen.off_axis_px,
                                             *corners, seen.centre_px), strict=True))  # fmt: skip
    else:
        outcome = read.why.value
    values |= {
        "frame_id": row["frame_id"], "file_id": row["file_id"], "outcome": outcome,
        "duration_s": time.perf_counter() - start, "measured_at": now,
    }  # fmt: skip
    with transaction(conn):
        conn.execute(UPSERT, values)
    return outcome


def _shape_values(shape: Shape) -> dict[str, object]:
    return {
        "shape": shape.kind.value, "shape_stars": shape.stars, "fwhm_px": shape.fwhm_px,
        "eccentricity": shape.eccentricity, "angle_deg": shape.angle_deg,
        "psf_residual": shape.psf_residual, "sampling_class": sampling_class(shape.fwhm_px),
        "fwhm_sigma_px": spread.fwhm_px if (spread := shape.spread) else None,
        "eccentricity_sigma": spread.eccentricity if spread else None,
        "psf_residual_sigma": spread.psf_residual if spread else None,
    }  # fmt: skip
