"""Scheda del file, mattone 4: tipo da IMAGETYP, solo vocabolario di N.I.N.A. e ASIAIR (ADR 0031).
Archivio di prova: N.I.N.A. LIGHT/FLAT/DARK/BIAS, ASIAIR Light/Dark/Flat/Bias."""

import math
import re
import warnings
from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS

from astrolog.pipeline.card import Card, FrameType, PointingSource, frame_type, read_card
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
    columns = re.findall(r"^  ([a-z_\d]+) ", _cards_table(), re.MULTILINE)
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
        ("TELESCOP", "optics", ["", "   ", 3]),
        ("XPIXSZ", "pixel_um", [-0.0]),
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


@pytest.mark.parametrize(
    ("name", "program", "optics", "focal"),
    [
        ("nina.txt", NINA, "Askar 103Apo", 560.0),
        ("asiair.txt", ASIAIR, None, 560.0),  # ASIAIR TELESCOP: the mount
        ("asiair_asi2600.txt", ASIAIR, None, 1004.0),
        ("asiair_am3.txt", ASIAIR, None, 335.0),
    ],
)
def test_the_real_optics_are_read(name, program, optics, focal, tmp_path):
    card = read_card(program, _values(name, tmp_path))
    assert (card.optics, card.focal_mm) == (optics, focal)


def test_asiair_telescop_is_the_mount_never_the_optics():
    for mount in ("EQMod Mount", "ZWO AM3 ", "Askar 103Apo"):
        assert read_card(ASIAIR, {"TELESCOP": mount}).optics is None
    assert read_card(NINA, {"TELESCOP": " Askar 103Apo "}).optics == "Askar 103Apo"


@pytest.mark.parametrize("bad", [0, -0.0, -560.0, True, "560", math.inf])
def test_a_focal_not_a_positive_number_is_unknown(bad):
    assert read_card(NINA, {"FOCALLEN": bad}).focal_mm is None


def test_a_float32_focal_loses_its_tail():
    assert read_card(NINA, {"FOCALLEN": 335.299987792969}).focal_mm == 335.3


def _sky(ra: object, dec: object) -> Any:  # astropy stubs: units, arrays
    return SkyCoord(ra, dec, unit="deg")


@pytest.mark.parametrize("name", ["asiair.txt", "asiair_asi2600.txt", "asiair_am3.txt"])
def test_an_asiair_solve_gives_the_centre_of_its_image(name, tmp_path):
    """Centro = pixel centrale dell'immagine risolta (IMAGEW/H), non CRPIX: astropy con SIP
    come riferimento."""
    values = _values(name, tmp_path)
    card = read_card(ASIAIR, values)
    header = fits.Header()
    for key, value in values.items():
        if key.startswith(("CTYPE", "CRVAL", "CRPIX", "CD", "A_", "B_", "AP_", "BP_")):
            header[key] = value
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ra, dec = WCS(header).all_pix2world(
            (values["IMAGEW"] - 1) / 2, (values["IMAGEH"] - 1) / 2, 0
        )
    assert card.pointing_source is PointingSource.SOLVE
    centre = _sky(card.pointing_ra_deg, card.pointing_dec_deg)
    assert float(centre.separation(_sky(float(ra), float(dec))).arcsec) < 30  # SIP left out: a hint


@pytest.mark.parametrize("name", ["asiair.txt", "asiair_asi2600.txt", "asiair_am3.txt"])
def test_the_asiair_mount_is_of_date_and_lands_on_its_solve_once_precessed(name, tmp_path):
    """RA/DEC ASIAIR in JNow: archivio, 1,2' dal solve precessato contro 17,7' letto J2000."""
    values = _values(name, tmp_path)
    solved = read_card(ASIAIR, values)
    no_solve = {k: v for k, v in values.items() if not k.startswith("CTYPE")}
    mount = read_card(ASIAIR, no_solve)
    assert mount.pointing_source is PointingSource.MOUNT
    centre = _sky(solved.pointing_ra_deg, solved.pointing_dec_deg)
    landed = float(centre.separation(_sky(mount.pointing_ra_deg, mount.pointing_dec_deg)).arcmin)
    as_written = float(centre.separation(_sky(values["RA"], values["DEC"])).arcmin)
    assert landed < as_written
    assert landed < 5


def test_an_asiair_mount_without_date_is_unknown():
    card = read_card(ASIAIR, {"RA": 210.0, "DEC": 54.0})
    assert card.pointing_source is None


def test_a_nina_mount_is_j2000_as_written(tmp_path):
    values = _values("nina.txt", tmp_path)
    card = read_card(NINA, values)
    assert card.pointing_source is PointingSource.MOUNT
    assert (card.pointing_ra_deg, card.pointing_dec_deg) == (values["RA"], values["DEC"])


@pytest.mark.parametrize(
    ("ra", "dec", "expected"),
    [
        ("16 05 00", "+17 43 24", (241.25, 17.723333)),
        ("05 35 17.3", "-05 23 28", (83.822083, -5.391111)),
        ("00 10 00", "-00 30 00", (2.5, -0.5)),  # sign of -00
        ("05 59 59.99", "+89 59 59", (89.999958, 89.999722)),  # 59: still valid
    ],
)
def test_without_mount_the_nina_target_is_read(ra, dec, expected):
    card = read_card(NINA, {"OBJCTRA": ra, "OBJCTDEC": dec})
    assert card.pointing_source is PointingSource.TARGET
    assert (card.pointing_ra_deg, card.pointing_dec_deg) == pytest.approx(expected, abs=1e-6)


@pytest.mark.parametrize(
    ("ra", "dec"), [("05 75 00", "+10 00 00"), ("05 00 60", "+10 00 00"), ("05 00 00", "+10 60 00")]
)
def test_a_target_with_minutes_or_seconds_past_59_is_unknown(ra, dec):
    assert read_card(NINA, {"OBJCTRA": ra, "OBJCTDEC": dec}).pointing_source is None


def test_the_target_placeholder_is_unknown():
    for dec in ("00 00 00", "+00 00 00"):
        assert read_card(NINA, {"OBJCTRA": "00 00 00", "OBJCTDEC": dec}).pointing_source is None


@pytest.mark.parametrize(
    "values",
    [
        {"RA": 400.0, "DEC": 10.0},
        {"RA": 10.0, "DEC": 95.0},
        {"RA": True, "DEC": 10.0},
        {"RA": 10.0},
    ],
)
def test_a_mount_out_of_range_falls_to_the_target(values):
    card = read_card(NINA, {**values, "OBJCTRA": "16 05 00", "OBJCTDEC": "+17 43 24"})
    assert card.pointing_source is PointingSource.TARGET


def test_a_mount_at_360_is_0():
    assert read_card(NINA, {"RA": 360.0, "DEC": 10.0}).pointing_ra_deg == 0.0


@pytest.mark.parametrize(
    "broken",
    [{"CD1_1": 0.0, "CD1_2": 0.0}, {"CTYPE1": "RA---SIN"}, {"IMAGEW": 0}, {"CRVAL2": "x"}],
)
def test_a_broken_solve_falls_to_the_mount(broken, tmp_path):
    values = {**_values("asiair_asi2600.txt", tmp_path), **broken}
    assert read_card(ASIAIR, values).pointing_source is PointingSource.MOUNT


def test_calibration_frames_keep_where_the_mount_was():
    card = read_card(NINA, {"IMAGETYP": "DARK", "RA": 10.0, "DEC": 20.0})
    assert card.pointing_source is PointingSource.MOUNT


@pytest.mark.parametrize(
    ("written", "name"),
    [
        (" vdB 152 ", "vdB 152"),
        ("IC 405 Pannello 2", "IC 405 Pannello 2"),  # mosaic panel: grouped by sky, part 2
        ("Targets", "Targets"),  # near a placeholder: exact match only
        ("", None),
        ("   ", None),
        (3, None),
    ],
)
def test_the_object_is_the_name_as_written(written, name):
    assert read_card(NINA, {"OBJECT": written}).object_name == name


@pytest.mark.parametrize("placeholder", ["Target", "target ", "FlatWizard", "Snapshot"])
def test_a_nina_placeholder_is_no_object(placeholder):
    """SimpleSequenceVM.cs 'Target', FlatWizardVM.cs, AnchorableSnapshotVM.cs: nomi di N.I.N.A."""
    assert read_card(NINA, {"OBJECT": placeholder}).object_name is None
    assert read_card(ASIAIR, {"OBJECT": placeholder}).object_name == placeholder.strip()


def test_a_calibration_keeps_its_object():
    """Flat di sequenza porta nome del bersaglio: serve ad abbinarlo."""
    assert read_card(NINA, {"IMAGETYP": "FLAT", "OBJECT": "IC 405"}).object_name == "IC 405"
    assert read_card(NINA, {"IMAGETYP": "FLAT", "OBJECT": "FlatWizard"}).object_name is None


@pytest.mark.parametrize(
    ("lat", "lon", "site"),
    [
        (45.494, 11.5218, (45.494, 11.5218)),  # archive, N.I.N.A.
        (45.6, 11.6666666666667, (45.6, 11.6666666666667)),  # true double: kept
        (46.0497, 11.3165, (46.0497, 11.3165)),  # archive, ASIAIR
        (0.0, 11.5, (0.0, 11.5)),  # equator: real
        (45.0, 0.0, (45.0, 0.0)),  # Greenwich: real
        (45.0, 180.0, (45.0, -180.0)),  # same meridian as -180
        (0.0, 0.0, (None, None)),  # N.I.N.A. factory profile (AstrometrySettings.cs)
        (90.1, 11.0, (None, None)),
        (45.0, 181.0, (None, None)),
        (45.0, 359.0, (None, None)),
        ("45.494", 11.5, (None, None)),
        (True, 11.5, (None, None)),
        (45.0, None, (None, None)),
    ],
)
def test_the_site_is_where_the_program_says_east_positive(lat, lon, site):
    values = {k: v for k, v in (("SITELAT", lat), ("SITELONG", lon)) if v is not None}
    for program in (NINA, ASIAIR):
        card = read_card(program, values)
        assert (card.site_lat_deg, card.site_lon_deg) == site


@pytest.mark.parametrize(
    ("local", "minutes"),
    [
        ("2025-06-29T23:11:33.412", 120),  # archive: summer
        ("2025-06-29T22:11:33.412", 60),  # archive: winter
        ("2025-06-30T02:56:33.412", 345),  # Nepal +5:45
        ("2025-06-29T21:11:33.412", 0),
        ("2025-06-29T09:11:33.412", -720),
        ("2025-06-29T22:12:33.412", None),  # not a zone: not the same instant
        ("2025-06-30T12:11:33.412", None),  # +15 h: no zone
        ("2025-06-29T08:11:33.412", None),  # -13 h
        ("2025-06-29", None),
        ("2025-06-29T23:11:33+02:00", None),
    ],
)
def test_the_clock_offset_is_local_minus_utc(local, minutes):
    """DATE-LOC = ora del PC (CFitsioFITS.cs ToLocalTime): fuso del PC, non del sito."""
    values = {"DATE-OBS": "2025-06-29T21:11:33.412", "DATE-LOC": local}
    assert read_card(NINA, values).clock_offset_min == minutes


def test_no_utc_start_no_clock_offset():
    assert read_card(NINA, {"DATE-LOC": "2025-06-29T23:11:33.412"}).clock_offset_min is None


def test_iso_written_as_number_or_digits_is_read():
    assert read_card(ASIAIR, {"ISO": " 1600 "}).iso == 1600
    assert read_card(ASIAIR, {"ISO": 800}).iso == 800


def test_an_infinite_exposure_is_unknown():
    assert read_card(NINA, {"EXPTIME": math.inf}).exposure_s is None
