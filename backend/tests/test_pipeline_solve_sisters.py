"""Mattone solve, ASTAP 7: a una posa che non sa dove guarda o quanto e' largo il campo li presta
una sorella gia' risolta, dello stesso oggetto per l'indizio e dello stesso setup per il campo."""

import pytest

from conftest import nina_light
from test_pipeline_solve import _SKY, FakeAstap, _option, _scanned, _solutions, _solve

_M13 = ("OBJECT  = 'M 13'", "INSTRUME= 'ATR2600M'")


def _sisters(conn, tmp_path, second: tuple[str, ...], run: FakeAstap) -> list[dict]:
    """A solved with its own pointing and field; b with the cards given, first in the folder."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1, (*_M13, *_SKY))
    nina_light(nas / "_b.fits", 2, second)
    _solve(conn, _scanned(conn, nas), run, tmp_path)
    return _solutions(conn)


def test_a_shot_without_a_pointing_starts_from_its_solved_sister(conn, tmp_path):
    """Il centro MISURATO della sorella dello stesso oggetto, non quello scritto nel suo header:
    la sorella con l'indizio si risolve prima, anche se viene dopo nella cartella."""
    run = FakeAstap("solved.ini")
    rows = _sisters(conn, tmp_path, (*_M13, *_SKY[:2]), run)
    assert "-ra" in run.commands[0] and "-ra" in run.commands[1]
    measured_ra, measured_dec = 241.25198643662179, 17.726894038989336  # tests/astap/solved.ini
    assert float(_option(run.commands[1], "-ra")) == pytest.approx(measured_ra / 15, abs=1e-5)
    assert float(_option(run.commands[1], "-spd")) == pytest.approx(measured_dec + 90, abs=1e-4)
    hints = {r["file_id"]: r["hint_from"] for r in rows}
    assert sorted(hints.values()) == ["card", "sister"]


@pytest.mark.parametrize(
    "second",
    [("INSTRUME= 'ATR2600M'", *_SKY[:2]), ("OBJECT  = 'M 92'", "INSTRUME= 'ATR2600M'", *_SKY[:2])],
    ids=["no object", "other object"],
)
def test_a_pointing_is_inherited_only_from_the_same_object(conn, tmp_path, second):
    """Due pose senza OBJECT non sono sorelle: un indizio sbagliato costa piu' della cieca."""
    run = FakeAstap("solved.ini")
    rows = _sisters(conn, tmp_path, second, run)
    assert "-ra" not in run.commands[1]
    assert sorted(str(r["hint_from"]) for r in rows) == ["None", "card"]


def test_a_shot_without_a_field_takes_the_scale_of_a_solved_shot_of_the_same_setup(conn, tmp_path):
    """Camera, binning e ottica uguali: la scala misurata della sorella per la propria altezza."""
    run = FakeAstap("solved.ini")
    rows = _sisters(conn, tmp_path, (*_M13, *_SKY[2:]), run)
    scale = next(r["scale_arcsec_px"] for r in rows if r["field_from"] == "card")
    assert float(_option(run.commands[1], "-fov")) == pytest.approx(16 * scale / 3600, abs=1e-3)
    assert sorted(r["field_from"] for r in rows) == ["card", "sister"]


@pytest.mark.parametrize(
    "setup",
    [("INSTRUME= 'ASI2600MC'",), ("INSTRUME= 'ATR2600M'", "XBINNING=                    2"),
     ("INSTRUME= 'ATR2600M'", "TELESCOP= 'Esprit 100'")],
    ids=["other camera", "other binning", "other optics"],
)  # fmt: skip
def test_a_field_is_inherited_only_from_the_same_setup(conn, tmp_path, setup):
    run = FakeAstap("solved.ini")
    rows = _sisters(conn, tmp_path, ("OBJECT  = 'M 13'", *setup, *_SKY[2:]), run)
    assert _option(run.commands[1], "-fov") == "0"
    assert sorted(str(r["field_from"]) for r in rows) == ["None", "card"]
