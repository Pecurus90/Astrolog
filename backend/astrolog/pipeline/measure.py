"""Light shots of a root measured from their pixels (ADR 0022, docs/domini/misure.md): one row
per shot, from one present file, written once; never redone by a reader."""

import sqlite3
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from ..db.transaction import transaction
from .debayer import pattern_of
from .pixels import Pixels, Unmeasurable, Why, read_pixels
from .scan import busy
from .shape import Shape
from .shots import first_per_shot
from .stars import Measured, measure_frame

# Light shots without a row, or whose last file was unreadable; plain file before its copy.
PENDING = (
    "SELECT f.id AS file_id, f.frame_id, f.rel_path, c.bayer,"
    " h.header ->> '$.BAYERPAT' AS BAYERPAT, h.header ->> '$.XBAYROFF' AS XBAYROFF,"
    " h.header ->> '$.YBAYROFF' AS YBAYROFF"
    " FROM pipeline_files AS f JOIN pipeline_cards AS c ON c.file_id = f.id"
    " JOIN pipeline_headers AS h ON h.file_id = f.id"
    " WHERE f.root_id = :root AND f.state = 'present' AND f.skip_reason IS NULL"
    " AND c.frame_type = 'light'"
    " AND NOT EXISTS (SELECT 1 FROM pipeline_measures AS m"
    "   WHERE m.frame_id = f.frame_id AND m.outcome <> 'unreadable')"
    " ORDER BY f.frame_id, lower(f.rel_path) LIKE '%.fz', f.rel_path"
)

_NUMBERS = (  # TooFewStars: no hfd_px, tilt_pct, curvature_pct
    "stars", "kept", "hfd_px", "background_adu", "noise_adu", "ceiling_adu", "saturated",
    "psf_snr", "gradient_pct", "gradient_angle_deg", "tilt_pct", "curvature_pct",
)  # fmt: skip
_SHAPE = ("shape", "shape_stars", "fwhm_px", "eccentricity", "angle_deg")

UPSERT = (
    "INSERT INTO pipeline_measures (frame_id, file_id, outcome, stars, kept, hfd_px,"
    " background_adu, noise_adu, ceiling_adu, saturated, psf_snr, gradient_pct,"
    " gradient_angle_deg, tilt_pct, curvature_pct, shape, shape_stars, fwhm_px, eccentricity,"
    " angle_deg, duration_s, measured_at)"
    " VALUES (:frame_id, :file_id, :outcome, :stars, :kept, :hfd_px, :background_adu,"
    " :noise_adu, :ceiling_adu, :saturated, :psf_snr, :gradient_pct, :gradient_angle_deg,"
    " :tilt_pct, :curvature_pct, :shape, :shape_stars, :fwhm_px, :eccentricity, :angle_deg,"
    " :duration_s, :measured_at)"
    " ON CONFLICT (frame_id) DO UPDATE SET file_id = excluded.file_id,"
    " outcome = excluded.outcome, stars = excluded.stars, kept = excluded.kept,"
    " hfd_px = excluded.hfd_px, background_adu = excluded.background_adu,"
    " noise_adu = excluded.noise_adu, ceiling_adu = excluded.ceiling_adu,"
    " saturated = excluded.saturated, psf_snr = excluded.psf_snr,"
    " gradient_pct = excluded.gradient_pct, gradient_angle_deg = excluded.gradient_angle_deg,"
    " tilt_pct = excluded.tilt_pct, curvature_pct = excluded.curvature_pct,"
    " shape = excluded.shape, shape_stars = excluded.shape_stars, fwhm_px = excluded.fwhm_px,"
    " eccentricity = excluded.eccentricity, angle_deg = excluded.angle_deg,"
    " duration_s = excluded.duration_s, measured_at = excluded.measured_at"
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
    values: dict[str, object] = {key: None for key in (*_NUMBERS, *_SHAPE)}
    pattern = pattern_of(dict(row))
    read = Unmeasurable(Why.NOT_SUPPORTED)  # a matrix not R G B (CYGM): no debayer for it
    if pattern is not None or not row["bayer"]:
        read = read_pixels(path)
    if isinstance(read, Pixels):
        found = measure_frame(read.data, saturation=read.saturation, pattern=pattern)
        outcome = "measured" if isinstance(found, Measured) else "too_few_stars"
        values |= {key: getattr(found, key, None) for key in _NUMBERS}
        if found.shape is not None:
            values |= _shape_values(found.shape)
    else:
        outcome = read.why.value
    values |= {
        "frame_id": row["frame_id"], "file_id": row["file_id"], "outcome": outcome,
        "duration_s": time.perf_counter() - start, "measured_at": now,
    }  # fmt: skip
    with transaction(conn, immediate=True):
        conn.execute(UPSERT, values)
    return outcome


def _shape_values(shape: Shape) -> dict[str, object]:
    return {
        "shape": shape.kind.value, "shape_stars": shape.stars, "fwhm_px": shape.fwhm_px,
        "eccentricity": shape.eccentricity, "angle_deg": shape.angle_deg,
    }  # fmt: skip
