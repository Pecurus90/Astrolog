"""Stage measure: each light shot of a root measured once from one of its files (ADR 0022,
docs/domini/misure.md). N.I.N.A. lights with synthetic stars of known HFD."""

import threading
from pathlib import Path

import numpy as np
import pytest

from astrolog.pipeline.changes import add_root
from astrolog.pipeline.measure import measure_root
from astrolog.pipeline.scan import scan_root
from conftest import LATER, NOW, fits_bytes, nina_light, settle
from test_pipeline_stars import _field, _true_hfd


def _light(path: Path, data: np.ndarray, *cards: str, imagetyp: str = "LIGHT") -> Path:
    """A N.I.N.A. light whose pixels are `data`, 16 bit unsigned as N.I.N.A. saves them."""
    rows, cols = data.shape
    lines = [
        "SIMPLE  =                    T",
        "BITPIX  =                   16",
        "NAXIS   =                    2",
        f"NAXIS1  = {cols:>20}",
        f"NAXIS2  = {rows:>20}",
        "BZERO   =                32768",
        f"IMAGETYP= '{imagetyp}'",
        "SWCREATE= 'N.I.N.A. 3.2.0.9001 (x64)'",
        *cards,
    ]
    pixels = (np.clip(np.rint(data), 0, 65535).astype(np.int32) - 32768).astype(">i2").tobytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(fits_bytes(lines) + pixels + b"\0" * (-len(pixels) % 2880))
    settle(path)
    return path


def _scanned(conn, nas: Path) -> int:
    root = add_root(conn, nas, NOW)
    scan_root(conn, root, NOW)
    return root


def _measures(conn) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM pipeline_measures ORDER BY frame_id")]


def test_a_light_is_measured_once_and_written(conn, tmp_path):
    _light(tmp_path / "nas" / "a.fits", _field("gauss", 2.5))
    root = _scanned(conn, tmp_path / "nas")
    result = measure_root(conn, root, LATER)
    (row,) = _measures(conn)
    assert row["outcome"] == "measured"
    assert row["stars"] == 60
    assert row["hfd_px"] == pytest.approx(_true_hfd("gauss", 2.5), rel=0.03)
    assert row["background_adu"] == pytest.approx(1000, abs=1)
    assert row["noise_adu"] == pytest.approx(10, rel=0.05)
    assert row["measured_at"] == LATER
    assert (row["shape"], row["shape_stars"]) == ("fitted", 60)
    assert row["fwhm_px"] == pytest.approx(2.3548 * 2.5, rel=0.03)
    assert row["eccentricity"] < 0.15
    assert row["angle_deg"] is None
    assert result.measured == 1
    again = measure_root(conn, root, "2026-01-01T00:00:00+00:00")
    assert again.measured == 0
    assert _measures(conn)[0]["measured_at"] == LATER


def test_only_lights_are_measured(conn, tmp_path):
    for kind in ("DARK", "FLAT", "BIAS"):
        _light(tmp_path / "nas" / f"{kind}.fits", _field(seed=len(kind)), imagetyp=kind)
    measure_root(conn, _scanned(conn, tmp_path / "nas"), LATER)
    assert _measures(conn) == []


def test_a_cloudy_frame_keeps_its_stars_and_says_too_few(conn, tmp_path):
    _light(tmp_path / "nas" / "a.fits", _field(count=2))
    measure_root(conn, _scanned(conn, tmp_path / "nas"), LATER)
    (row,) = _measures(conn)
    assert (row["outcome"], row["stars"], row["hfd_px"]) == ("too_few_stars", 2, None)
    assert (row["shape"], row["fwhm_px"]) == (None, None)  # too few stars, not a shape fault


def test_a_frame_too_small_to_measure_says_so(conn, tmp_path):
    nina_light(tmp_path / "nas" / "a.fits", 1)  # 16 x 16 pixels
    measure_root(conn, _scanned(conn, tmp_path / "nas"), LATER)
    assert [r["outcome"] for r in _measures(conn)] == ["not_supported"]


def test_the_plain_file_is_read_before_its_fpack_copy(conn, tmp_path):
    plain = _light(tmp_path / "nas" / "b.fits", _field())
    copy = tmp_path / "nas" / "a.fits.fz"
    copy.write_bytes(plain.read_bytes())  # same shot: the copy sorts first by name
    settle(copy)
    measure_root(conn, _scanned(conn, tmp_path / "nas"), LATER)
    (row,) = _measures(conn)
    read = conn.execute("SELECT rel_path FROM pipeline_files WHERE id = ?", (row["file_id"],))
    assert (row["outcome"], read.fetchone()[0]) == ("measured", "b.fits")


def test_a_file_unreadable_now_is_tried_again(conn, tmp_path):
    path = _light(tmp_path / "nas" / "a.fits", _field())
    root = _scanned(conn, tmp_path / "nas")
    kept = path.read_bytes()
    path.write_bytes(kept[:5000])  # cut after the scan
    measure_root(conn, root, LATER)
    assert [r["outcome"] for r in _measures(conn)] == ["unreadable"]
    path.write_bytes(kept)
    measure_root(conn, root, LATER)
    assert [r["outcome"] for r in _measures(conn)] == ["measured"]


def test_a_colour_camera_is_measured_after_its_debayer(conn, tmp_path):
    """G R / B G read as RGGB moved one column (XBAYROFF), as the Debayer's Auto reads it."""
    pattern = np.tile(np.array([[1.0, 0.82], [0.83, 1.0]]), (300, 300))
    _light(tmp_path / "nas" / "a.fits", _field("gauss", 1.2) * pattern,
           "BAYERPAT= 'RGGB'", "XBAYROFF=                    1")  # fmt: skip
    measure_root(conn, _scanned(conn, tmp_path / "nas"), LATER)
    (row,) = _measures(conn)
    assert row["outcome"] == "measured"
    assert row["hfd_px"] == pytest.approx(_true_hfd("gauss", 1.2), rel=0.05)


def test_a_colour_matrix_not_rgb_is_not_measured(conn, tmp_path):
    _light(tmp_path / "nas" / "a.fits", _field("gauss", 2.0), "BAYERPAT= 'CYGM'")
    measure_root(conn, _scanned(conn, tmp_path / "nas"), LATER)
    assert [r["outcome"] for r in _measures(conn)] == ["not_supported"]


def test_a_stop_measures_nothing_more(conn, tmp_path):
    for name in ("a", "b"):
        _light(tmp_path / "nas" / f"{name}.fits", _field(seed=ord(name)))
    stop = threading.Event()
    stop.set()
    measure_root(conn, _scanned(conn, tmp_path / "nas"), LATER, stop=stop)
    assert _measures(conn) == []
