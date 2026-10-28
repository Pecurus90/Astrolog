"""Il lettore dei cataloghi .1476 di ASTAP: formato, zone, finestra; su file costruiti qui, e sul
D80 vero solo dove e' installato."""

import math
from pathlib import Path

import numpy as np
import pytest

from astrolog.pipeline.star_catalogue import (
    RING_CELLS,
    area_of,
    catalogue_in,
    decode,
    find_areas,
    window,
)

ASTAP = Path(r"C:\Program Files\astap")


def _file(records: list[list[int]], size: int = 5, version: int = 1) -> bytes:
    head = bytearray(b" " * 110)
    head[108], head[109] = version, size
    return bytes(head) + b"".join(bytes(r + [0] * (size - len(r))) for r in records)


def _header(dec9: int, mag10: int) -> list[int]:
    return [0xFF, 0xFF, 0xFF, dec9 + 128, mag10 + 16]


def test_the_documented_star_decodes_to_sirius():
    """Esempio della documentazione HNSKY: RA 6h45m09s, Dec -16 42' 58", magnitudine -1,4."""
    buf = _file([_header(-24, -14), [0xC3, 0x06, 0x48, 0xD7, 0x39]])
    stars = decode(buf)
    assert stars.ra_deg[0] / 15 == pytest.approx(6.75247662, abs=1e-7)
    assert stars.dec_deg[0] == pytest.approx(-16.7161401, abs=1e-6)
    assert stars.mag.tolist() == [-1.4]


def test_a_header_record_sets_magnitude_and_high_byte_for_the_stars_after_it():
    buf = _file([_header(-24, -14), [1, 0, 0, 0, 0], _header(0, 100), [0, 0, 0, 0x10, 0]])
    stars = decode(buf)
    assert stars.mag.tolist() == [-1.4, 10.0]
    assert stars.dec_deg[1] == pytest.approx(16 * 90 / (128 * 65536 - 1))


def test_six_byte_records_read_like_five():
    """Il sesto byte e' il colore (v50, versione 2): per lo SQM non serve, si salta."""
    five = decode(_file([_header(0, 50), [9, 9, 9, 9, 9]]))
    six = decode(_file([_header(0, 50), [9, 9, 9, 9, 9, 200]], size=6, version=2))
    assert six.ra_deg.tolist() == five.ra_deg.tolist()
    assert six.dec_deg.tolist() == five.dec_deg.tolist()


def test_another_record_size_is_refused():
    with pytest.raises(ValueError, match="record"):
        decode(_file([_header(0, 50)], size=7))


def test_the_sky_has_1476_areas_in_36_rings():
    assert sum(RING_CELLS) == 1476 and len(RING_CELLS) == 36


@pytest.mark.parametrize(
    ("ra", "dec", "name"),
    [(0.0, -89.0, "0101"), (10.0, 89.0, "3601"), (359.99, 0.1, "1969"),
     (0.01, -0.1, "1801"), (101.29, -16.72, "1519"), (0.0, -87.0, "0201"),
     (359.0, 87.0, "3503")],
)  # fmt: skip
def test_a_position_falls_in_its_area(ra, dec, name):
    assert area_of(ra, dec).name == name


def test_area_numbers_count_from_the_south_pole():
    assert area_of(0.0, -89.0).number == 1
    assert area_of(200.0, 89.0).number == 1476
    assert area_of(0.0, -87.0).number == 2


def test_a_small_field_inside_one_area_needs_only_it():
    centre = area_of(101.29, -16.72)
    found = find_areas(101.29, -16.72, 0.5)
    assert [a.name for a, _ in found] == [centre.name]
    assert found[0][1] == pytest.approx(1.0)


def test_a_field_on_the_corner_of_four_areas_shares_its_quota():
    """Un campo sul confine prende da ogni zona la parte di campo che ci cade (find_areas)."""
    edge_ra = 360.0 / RING_CELLS[18]  # due anelli di 69 celle si toccano all'equatore
    found = find_areas(edge_ra, 0.0, 1.0)
    assert [a.name for a, _ in found] == ["1902", "1901", "1802", "1801"]
    assert [f for _, f in found] == pytest.approx([0.25] * 4, abs=1e-3)


def test_the_field_is_cropped_to_one_area_side():
    """Oltre 5,142857 gradi si taglia: una zona oltre la vicina non verrebbe letta."""
    assert len(find_areas(101.29, -16.72, 40.0)) <= 4


def test_the_window_keeps_the_square_around_the_centre():
    """La finestra di readdatabase1476: |dRA| cos(Dec0) e |dDec| sotto meta' campo."""
    ra_raw = [round(r / 360 * (2**24 - 1)) for r in (100.0, 100.4, 101.0)]
    dec_low = round(0.1 / 90 * (128 * 65536 - 1))
    records = [_header(0, 80)]
    for r in ra_raw:
        records.append([r & 0xFF, r >> 8 & 0xFF, r >> 16, dec_low & 0xFF, dec_low >> 8 & 0xFF])
    stars = decode(_file(records))
    kept = window(stars, 100.0, 0.0, 1.0)
    assert kept.ra_deg.tolist() == pytest.approx([100.0, 100.4], abs=1e-4)


def test_the_catalogue_is_the_first_gaia_bp_one_in_astaps_order(tmp_path):
    for name in ("d20_0101.1476", "d50_0101.1476", "v50_0101.1476"):
        (tmp_path / name).write_bytes(b"")
    assert catalogue_in(tmp_path) == "d50"
    assert catalogue_in(tmp_path / "missing") is None


def test_v50_alone_is_not_used(tmp_path):
    """V50 porta magnitudini Johnson V, non Gaia BP: lo zero point sarebbe un altro."""
    (tmp_path / "v50_0101.1476").write_bytes(b"")
    assert catalogue_in(tmp_path) is None


@pytest.mark.skipif(not (ASTAP / "d80_0101.1476").exists(), reason="D80 non installato")
def test_the_real_d80_reads_bright_to_faint():
    from astrolog.pipeline.star_catalogue import read_area

    stars = read_area(ASTAP, "d80", area_of(241.26, 17.74))
    assert len(stars.ra_deg) > 10000
    assert np.all(np.diff(stars.mag) >= 0)
    assert math.isfinite(float(stars.dec_deg.max()))
