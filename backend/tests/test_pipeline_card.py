"""Scheda del file, mattone 4: tipo da IMAGETYP, solo vocabolario di N.I.N.A. e ASIAIR (ADR 0031).
Archivio di prova: N.I.N.A. LIGHT/FLAT/DARK/BIAS, ASIAIR Light/Dark/Flat/Bias."""

import math
import re
from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path

import pytest

from astrolog.pipeline.card import Card, FrameType, frame_type, read_card
from astrolog.pipeline.scanner import Program, read_cards

CORPUS = Path(__file__).with_name("header")
NINA, ASIAIR = Program.NINA, Program.ASIAIR


def _values(name: str, tmp_path: Path) -> dict:
    """Real header as a file: only the header is read, so no pixels."""
    lines = (CORPUS / name).read_text(encoding="utf-8").splitlines()
    head = "".join(line.ljust(80)[:80] for line in lines if line.strip() and line[0] != "#")
    head += "END".ljust(80)
    path = tmp_path / "h.fits"
    path.write_bytes((head + " " * (-len(head) % 2880)).encode("latin-1"))
    values = read_cards(path)
    assert values is not None
    return values


@pytest.mark.parametrize(
    ("name", "program"),
    [("nina.txt", NINA), ("asiair.txt", ASIAIR), ("asiair_am3.txt", ASIAIR)],
)
def test_the_real_lights_are_lights(name, program, tmp_path):
    assert frame_type(program, _values(name, tmp_path)) is FrameType.LIGHT


@pytest.mark.parametrize(
    ("program", "written", "kind"),
    [
        (NINA, "LIGHT", FrameType.LIGHT),
        (NINA, "DARK", FrameType.DARK),
        (NINA, "FLAT", FrameType.FLAT),
        (NINA, "BIAS", FrameType.BIAS),
        (NINA, "DARKFLAT", FrameType.DARK),  # N.I.N.A. 3.0 RELEASE_NOTES: "really just DARKs"
        (ASIAIR, "Light", FrameType.LIGHT),
        (ASIAIR, "Dark", FrameType.DARK),
        (ASIAIR, "Flat", FrameType.FLAT),
        (ASIAIR, "Bias", FrameType.BIAS),
        (ASIAIR, " light ", FrameType.LIGHT),
    ],
)
def test_the_written_type_is_read_without_case_or_blanks(program, written, kind):
    assert frame_type(program, {"IMAGETYP": written}) is kind


@pytest.mark.parametrize("written", ["Master Dark", "Light Frame", "science", "", 3, None])
def test_any_other_word_or_no_word_is_unknown(written):
    values = {} if written is None else {"IMAGETYP": written}
    assert frame_type(NINA, values) is FrameType.UNKNOWN


def test_a_nina_snapshot_is_written_light_with_its_default_name():
    """CFitsioFITS.cs: SNAPSHOT scritto LIGHT; nome predefinito 'Snapshot'. Archivio: 7 file."""
    assert frame_type(NINA, {"IMAGETYP": "LIGHT", "OBJECT": "snapshot"}) is FrameType.SNAPSHOT
    assert frame_type(ASIAIR, {"IMAGETYP": "Light", "OBJECT": "Snapshot"}) is FrameType.LIGHT


@pytest.mark.parametrize("name", ["darkflat", "Dark", "FLAT", "bias"])
def test_a_light_named_as_a_calibration_is_unknown_to_ask(name):
    """IMAGETYP e OBJECT in contrasto: si chiede. Archivio: 56 LIGHT 'darkflat'."""
    assert frame_type(NINA, {"IMAGETYP": "LIGHT", "OBJECT": name}) is FrameType.UNKNOWN


def test_a_real_object_with_a_calibration_word_stays_light():
    for name in ("Dark Nebula", "LDN 1235", "Flaming Star", "Light"):
        assert frame_type(NINA, {"IMAGETYP": "LIGHT", "OBJECT": name}) is FrameType.LIGHT


def test_flat_wizard_darks_stay_darks():
    """Archivio: 610 DARK con OBJECT 'FlatWizard'."""
    assert frame_type(NINA, {"IMAGETYP": "DARK", "OBJECT": "FlatWizard"}) is FrameType.DARK


@pytest.mark.parametrize(
    ("written", "start"),
    [
        ("2025-06-29T21:11:33.412", datetime(2025, 6, 29, 21, 11, 33, 412000, UTC)),  # N.I.N.A.
        ("2025-06-29T21:11:33.4123456", datetime(2025, 6, 29, 21, 11, 33, 412345, UTC)),  # 3.2
        ("2024-05-17T19:55:39.147017", datetime(2024, 5, 17, 19, 55, 39, 147017, UTC)),  # ASIAIR
        ("2024-05-17T19:55:39", datetime(2024, 5, 17, 19, 55, 39, tzinfo=UTC)),
    ],
)
def test_the_start_is_date_obs_in_utc(written, start):
    """DATE-OBS = inizio posa, UTC (FITS 4.0; ASIAIR: nome file = fine posa locale)."""
    assert read_card(NINA, {"DATE-OBS": written}).start_utc == start


@pytest.mark.parametrize(
    "written",
    [
        "2025-06-29",  # no time: never midnight
        "2025-06-29T21",
        "2025-W26-1T10:00:00",
        "20250629T210304",
        "2025-06-29 21:03:04",
        "2025-06-29T21:03:04Z",
        "2025-06-29T21:03:04+02:00",
        "2025-02-30T21:03:04",
        "",
        59760.5,
    ],
)
def test_a_start_not_written_as_both_programs_do_is_unknown(written):
    assert read_card(NINA, {"DATE-OBS": written}).start_utc is None


def test_no_date_obs_is_unknown_even_with_mjd_or_date_avg():
    """Nessun file ha MJD-OBS o DATE-AVG senza DATE-OBS: niente riserve (ADR 0031)."""
    values = {"MJD-OBS": 60855.88, "DATE-AVG": "2025-06-29T21:12:34.298"}
    assert read_card(NINA, values).start_utc is None


@pytest.mark.parametrize(
    ("written", "seconds"),
    [(300.0, 300.0), (300, 300.0), (0.006, 0.006), (0, 0.0), (-1.0, None), (True, None),
     ("300", None), (None, None)],
)  # fmt: skip
def test_the_exposure_is_exptime_in_seconds(written, seconds):
    values = {} if written is None else {"EXPTIME": written}
    assert read_card(NINA, {**values, "EXPOSURE": 120.0}).exposure_s == seconds


def _cards_table() -> str:
    schema = Path(__file__).parents[1].joinpath("astrolog", "schema.sql").read_text("utf-8")
    table = schema[schema.index("CREATE TABLE pipeline_cards") :]
    return table[: table.index(") STRICT;")]


def test_the_schema_check_lists_every_frame_type():
    listed = re.search(r"frame_type IN \(([^)]*)\)", _cards_table())
    assert listed is not None
    assert set(re.findall(r"'(\w+)'", listed.group(1))) == {t.value for t in FrameType}


def test_the_table_columns_are_the_card_fields():
    """INSERT nasce dai campi di Card: stessi nomi, stesso ordine."""
    columns = re.findall(r"^  (\w+) ", _cards_table(), re.MULTILINE)
    assert columns == ["file_id", *(f.name for f in fields(Card))]


@pytest.mark.parametrize(
    ("name", "program", "expected"),
    [
        ("nina.txt", NINA, {
            "camera": "ATR2600M(USB2.0)", "width": 6224, "height": 4168, "bin_x": 1, "bin_y": 1,
            "pixel_um": 3.76, "bayer": False, "gain": 100, "iso": None, "offset": 400,
            "ccd_temp_c": -4.9, "set_temp_c": -5.0,
        }),
        ("asiair.txt", ASIAIR, {  # Canon via ASIAIR: ISO, no gain/offset/setpoint
            "camera": "Canon EOS 700D", "width": 5208, "height": 3476, "bin_x": 1, "bin_y": 1,
            "pixel_um": 4.29, "bayer": True, "gain": None, "iso": 800, "offset": None,
            "ccd_temp_c": 13.0, "set_temp_c": None,
        }),
        ("asiair_asi2600.txt", ASIAIR, {
            "camera": "ZWO ASI2600MC Duo", "width": 6248, "height": 4176, "bin_x": 1, "bin_y": 1,
            "pixel_um": 3.76, "bayer": True, "gain": 100, "iso": None, "offset": 50,
            "ccd_temp_c": -9.8, "set_temp_c": -10.0,
        }),
    ],
)  # fmt: skip
def test_the_real_cameras_are_read(name, program, expected, tmp_path):
    card = read_card(program, _values(name, tmp_path))
    assert {k: getattr(card, k) for k in expected} == expected


@pytest.mark.parametrize(
    ("written", "clean"),
    [
        (3.75999999046326, 3.76),  # ASIAIR: float32 of 3.76 at 15 digits
        (-10.1000003814697, -10.1),  # N.I.N.A. driver float32
        (3.76, 3.76),  # true double: untouched
        (-4.9, -4.9),
        (3.7612345678, 3.7612345678),  # not a float32: untouched
    ],
)
def test_float32_tail_is_cut_only_when_the_number_is_a_float32(written, clean):
    assert read_card(ASIAIR, {"XPIXSZ": abs(written)}).pixel_um == abs(clean)
    assert read_card(ASIAIR, {"CCD-TEMP": written}).ccd_temp_c == clean


def test_the_pixel_stays_as_written_with_its_binning():
    """XPIXSZ gia' col binning: SBIG, N.I.N.A. CFitsioFITS.cs, ASIAIR "with binning"."""
    card = read_card(NINA, {"XPIXSZ": 7.52, "XBINNING": 2, "YBINNING": 2})
    assert (card.pixel_um, card.bin_x, card.bin_y) == (7.52, 2, 2)


def test_a_compressed_frame_has_its_size_in_znaxis():
    """FITS 4.0 sez. 10: primario vuoto, dimensioni del frame in ZNAXISn."""
    card = read_card(NINA, {"NAXIS": 0, "ZNAXIS": 2, "ZNAXIS1": 6224, "ZNAXIS2": 4168})
    assert (card.width, card.height) == (6224, 4168)


@pytest.mark.parametrize(
    ("program", "values", "bayer"),
    [
        (NINA, {"BAYERPAT": "RGGB"}, True),
        (ASIAIR, {"BAYERPAT": "RGGB"}, True),
        (NINA, {}, False),  # CFitsioFITS.cs: written unless mono or pattern None
        (ASIAIR, {}, None),  # no ASIAIR mono file: not known
        (NINA, {"BAYERPAT": ""}, None),
        (NINA, {"BAYERPAT": 1}, None),
    ],
)
def test_the_mosaic_is_known_only_where_the_program_says(program, values, bayer):
    assert read_card(program, values).bayer is bayer


@pytest.mark.parametrize(
    ("key", "field", "bad"),
    [
        ("NAXIS1", "width", [0, -1, True, 6224.0, "6224"]),
        ("XBINNING", "bin_x", [0, True, 1.0]),
        ("XPIXSZ", "pixel_um", [0, -3.76, True, "3.76"]),
        ("GAIN", "gain", [-1, True, 100.5, "100"]),
        ("OFFSET", "offset", [-1, True, "50"]),
        ("ISO", "iso", ["0", "8OO", "", " ", "800.0", "８００", True, 0]),
        ("CCD-TEMP", "ccd_temp_c", [True, "-10"]),
        ("SET-TEMP", "set_temp_c", [False, "-10"]),
        ("INSTRUME", "camera", ["", "   ", 3]),
    ],
)
def test_a_value_not_written_as_its_kind_is_unknown(key, field, bad):
    for value in bad:
        assert getattr(read_card(NINA, {key: value}), field) is None, value


@pytest.mark.parametrize("key", ["GAIN", "OFFSET", "ISO", "NAXIS1", "XBINNING"])
def test_an_integer_past_sqlite_is_unknown_not_a_failed_scan(key):
    """SQLite INTEGER: 64 bit. Oltre, OverflowError e scansione intera annullata."""
    assert getattr(read_card(NINA, {key: 2**63}), _FIELD[key]) is None
    assert getattr(read_card(NINA, {key: 2**63 - 1}), _FIELD[key]) == 2**63 - 1


_FIELD = {"GAIN": "gain", "OFFSET": "offset", "ISO": "iso", "NAXIS1": "width", "XBINNING": "bin_x"}


def test_iso_written_as_number_or_digits_is_read():
    assert read_card(ASIAIR, {"ISO": " 1600 "}).iso == 1600
    assert read_card(ASIAIR, {"ISO": 800}).iso == 800


def test_an_infinite_exposure_is_unknown():
    assert read_card(NINA, {"EXPTIME": math.inf}).exposure_s is None
