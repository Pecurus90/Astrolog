"""Stage measure: each light shot of a root measured once from one of its files (ADR 0022,
docs/domini/misure.md). N.I.N.A. lights with synthetic stars of known HFD."""

import threading
from pathlib import Path

import numpy as np
import pytest

from astrolog.pipeline.measure import measure_root
from astrolog.pipeline.roots import add_root
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
    # A Gaussian read by the Moffat 4 of Image Analysis: 5% narrow (misure.md, Forma)
    assert row["fwhm_px"] == pytest.approx(0.95 * 2.3548 * 2.5, rel=0.03)
    assert row["psf_residual"] > 0 and row["fwhm_sigma_px"] >= 0
    assert row["eccentricity"] < 0.15
    assert row["angle_deg"] is None
    assert (row["ceiling_adu"], row["saturated"]) == (65535.0, 0)
    assert row["psf_snr"] > 0
    assert row["psf_count"] == 60 and row["psf_flux_adu"] > row["psf_mean_flux_adu"] > 0
    assert row["gradient_noise"] < 1 and row["row_banding"] < 0.05
    assert row["fwhm_tilt"] < 0.05 and row["fwhm_curvature"] is not None
    assert (row["tilt_level"], row["sampling_class"]) == ("go", "over")  # FWHM 5.6 px
    assert row["hfd_tilt_pct"] < 5 and abs(row["off_axis_px"]) < 0.1
    areas = [row[f"hfd_corner_{i}_px"] for i in (1, 2, 3, 4)] + [row["hfd_centre_px"]]
    assert all(c == pytest.approx(row["hfd_px"], rel=0.05) for c in areas)
    assert 0 <= row["elongation_coherence"] <= 1
    assert result.measured == 1
    again = measure_root(conn, root, "2026-01-01T00:00:00+00:00")
    assert again.measured == 0
    assert _measures(conn)[0]["measured_at"] == LATER


def test_the_pixel_statistics_are_written_the_pedestal_off_and_the_sky_rate_per_second(
    conn, tmp_path
):
    """ImageAnalysis par. 2.1.2: Median less PEDESTAL, SkyRate = Median / EXPTIME. software-ok"""
    _light(tmp_path / "nas" / "a.fits", _field("gauss", 2.5), "EXPTIME =                120.0",
           "PEDESTAL=                  100")  # fmt: skip
    _light(tmp_path / "nas" / "b.fits", _field("gauss", 2.5, seed=4))
    measure_root(conn, _scanned(conn, tmp_path / "nas"), LATER)
    timed, untimed = _measures(conn)
    assert timed["median_adu"] == pytest.approx(900, abs=2)
    assert timed["sky_rate_adu_s"] == pytest.approx(timed["median_adu"] / 120.0)
    assert untimed["median_adu"] == pytest.approx(1000, abs=2) and untimed["sky_rate_adu_s"] is None
    assert timed["sigma_adu"] == pytest.approx(10, rel=0.05)
    # 16-bit steps at sigma 10: bins of 0.625 ADU, some empty; under the 2.047 of continuous noise
    assert 1.0 < timed["entropy_bits"] < 2.1 and 0.5 < timed["noise_ratio"] <= 1
    assert timed["snr"] > 0 and timed["psf_signal_weight"] > 0
    assert timed["mstar_adu"] == pytest.approx(0.6745 * 10, rel=0.1)
    assert timed["nstar_adu"] == pytest.approx(10, rel=0.1)


def test_the_trails_are_written(conn, tmp_path):
    """A diagonal line 8 noise high across one frame: one trail; the other none."""
    crossed = _field("gauss", 2.5)
    rows, cols = np.indices(crossed.shape)
    crossed += 80.0 * np.exp(-((rows - cols) ** 2) / 4.0)
    _light(tmp_path / "nas" / "a.fits", crossed, "EXPTIME =                120.0")
    _light(tmp_path / "nas" / "b.fits", _field("gauss", 2.5, seed=4))
    measure_root(conn, _scanned(conn, tmp_path / "nas"), LATER)
    timed, untimed = _measures(conn)
    assert (timed["trails"], untimed["trails"]) == (1, 0)


def test_the_brightness_ladder_is_written(conn, tmp_path):
    """60 stars: the window from rank 1, none from 51 (misure.md Trasparenza). A hot pixel tops
    the frame: else 60 equal stars all reach 3/4 of the highest and count saturated."""
    data = _field("gauss", 2.5)
    data[3, 3] = 65535.0
    _light(tmp_path / "nas" / "a.fits", data)
    measure_root(conn, _scanned(conn, tmp_path / "nas"), LATER)
    (row,) = _measures(conn)
    assert 3 < row["ladder_1_dex"] < 7  # log10 ADU of stars of 1e3 to 1e7 ADU
    assert row["ladder_51_dex"] is None and row["ladder_6401_dex"] is None


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


def test_the_file_measured_is_the_one_whose_card_stands_for_the_shot(conn, tmp_path):
    """La copia arrivata dopo viene prima per nome, si misura l'originale. Prima: la
    prima per percorso, e il cielo prendeva sito e ora dalla sua scheda."""
    original = _light(tmp_path / "nas" / "b.fits", _field())
    root = _scanned(conn, tmp_path / "nas")
    (tmp_path / "nas" / "a-backup.fits").write_bytes(original.read_bytes())
    settle(tmp_path / "nas" / "a-backup.fits")
    scan_root(conn, root, LATER)
    measure_root(conn, root, LATER)
    (row,) = _measures(conn)
    read = conn.execute("SELECT rel_path FROM pipeline_files WHERE id = ?", (row["file_id"],))
    assert read.fetchone()[0] == "b.fits"


def _card_in_b_copy_in_a(conn, tmp_path: Path) -> tuple[Path, int, int]:
    """The shot's card file in root B (file 1), its copy in root A (file 2): original, B, A."""
    original = _light(tmp_path / "b" / "x.fits", _field())
    root_b = _scanned(conn, tmp_path / "b")
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "x.fits").write_bytes(original.read_bytes())
    settle(tmp_path / "a" / "x.fits")
    return original, root_b, _scanned(conn, tmp_path / "a")


def test_a_copy_in_another_root_waits_for_the_card_of_its_shot(conn, tmp_path):
    """Scheda in B, copia in A misurata per prima: si misura la scheda. Prima: la copia, e
    il cielo prendeva sito e ora dalla sua scheda (Issue #108)."""
    _, root_b, root_a = _card_in_b_copy_in_a(conn, tmp_path)
    measure_root(conn, root_a, LATER)
    measure_root(conn, root_b, LATER)
    (row,) = _measures(conn)
    read = conn.execute("SELECT root_id FROM pipeline_files WHERE id = ?", (row["file_id"],))
    assert read.fetchone()[0] == root_b


def test_a_copy_measured_while_its_card_was_skipped_gives_way_to_the_card(conn, tmp_path):
    """Scheda tagliata a meta': la copia misura la posa, la scheda tornata intera la rimisura."""
    original, root_b, root_a = _card_in_b_copy_in_a(conn, tmp_path)
    kept = original.read_bytes()
    original.write_bytes(kept[:5000])
    settle(original, 300)
    scan_root(conn, root_b, LATER)
    measure_root(conn, root_a, LATER)
    copy = _measures(conn)[0]["file_id"]
    original.write_bytes(kept)
    settle(original, 200)
    scan_root(conn, root_b, LATER)
    measure_root(conn, root_b, LATER)
    (row,) = _measures(conn)
    assert (copy, row["file_id"], row["outcome"]) == (2, 1, "measured")


def test_a_copy_measures_the_shot_while_the_card_root_does_not_answer(conn, tmp_path):
    """Cartella della scheda spenta: la copia misura la posa, la scheda tornata la rimisura.
    Prima della correzione la posa restava illeggibile finche' la cartella non tornava."""
    _, root_b, root_a = _card_in_b_copy_in_a(conn, tmp_path)
    (tmp_path / "b").rename(tmp_path / "off")
    scan_root(conn, root_b, LATER)
    for _ in range(2):
        measure_root(conn, root_b, LATER)
        measure_root(conn, root_a, LATER)
    assert [(r["file_id"], r["outcome"]) for r in _measures(conn)] == [(2, "measured")]
    (tmp_path / "off").rename(tmp_path / "b")
    measure_root(conn, root_b, LATER)
    assert [(r["file_id"], r["outcome"]) for r in _measures(conn)] == [(1, "measured")]


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
