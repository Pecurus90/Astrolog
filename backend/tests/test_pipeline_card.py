"""Scheda del file, mattone 4: tipo da IMAGETYP, solo vocabolario di N.I.N.A. e ASIAIR (ADR 0031).
Archivio di prova: N.I.N.A. LIGHT/FLAT/DARK/BIAS, ASIAIR Light/Dark/Flat/Bias."""

import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from astrolog.pipeline.card import FrameType, frame_type, read_card
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


def test_the_schema_check_lists_every_frame_type():
    schema = Path(__file__).parents[1].joinpath("astrolog", "schema.sql").read_text("utf-8")
    table = schema[schema.index("CREATE TABLE pipeline_cards") :]
    listed = re.search(r"frame_type IN \(([^)]*)\)", table)
    assert listed is not None
    assert set(re.findall(r"'(\w+)'", listed.group(1))) == {t.value for t in FrameType}
