"""The SQM comparison reads what astap.exe -sqm writes and sets ours beside it. No program runs
here: its launch is faked with the .wcs it wrote on a real frame."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from confronto_sqm import Ours, main, read_cards

# A real frame (ATR2600M, filter L), astap.exe -r 30 -sqm 400: the cards that count.
WCS = "".join(
    card.ljust(80)
    for card in (
        "CRVAL1  =  2.412547635082E+002 / RA (J2000) of the reference pixel [deg]",
        "CRVAL2  =  1.771659574468E+001 / DEC (J2000) of the reference pixel [deg]",
        "CRPIX1  =  3.112500000000E+003 / X of reference pixel",
        "CRPIX2  =  2.084500000000E+003 / Y of reference pixel",
        "CD1_1   = -2.627739321034E-004 / CD matrix to convert (x,y) to (Ra, Dec)",
        "CD1_2   =  2.794415521458E-004 / CD matrix to convert (x,y) to (Ra, Dec)",
        "CD2_1   = -2.794426636246E-004 / CD matrix to convert (x,y) to (Ra, Dec)",
        "CD2_2   = -2.628591285841E-004 / CD matrix to convert (x,y) to (Ra, Dec)",
        "MZEROR  =  2.726571355354E+001 / BP=-2.5*log(flux_e)+MZEROR using MZEROAPT",
        "SQM     =  19.31               / Sky background [magn/arcsec^2]",
        "END",
    )
)


def test_the_cards_astap_wrote_are_read():
    cards = read_cards(WCS)
    assert cards["SQM"] == 19.31
    assert cards["MZEROR"] == pytest.approx(27.26571355354)
    assert cards["CRPIX1"] == 3112.5


def test_main_sets_ours_beside_astap_on_mono_frames(tmp_path, capsys):
    folder = tmp_path / "copie"
    folder.mkdir()
    for name in ("m01.fits", "c01.fits"):
        (folder / name).write_bytes(b"")
    launched = []

    def run(cmd, timeout_s):
        launched.append(cmd)
        frame = cmd[cmd.index("-f") + 1]
        (folder / frame).with_suffix(".wcs").write_text(WCS, encoding="latin-1")
        return 0, ""

    def measure(frame, wcs, bias, folder):
        assert bias == 400.0
        assert folder.name == "astap", "the catalogue beside the astap.exe given"
        assert wcs is not None and wcs.crpix == (3112.5, 2084.5)
        if frame.name == "c01.fits":
            return Ours(19.5, 25.6, 380, True)
        return Ours(19.315, 27.2657, 1886, False)

    code = main(
        [str(folder), "--astap", "astap/astap.exe", "--cli", "astap_cli.exe", "--bias", "400"],
        run=run,
        measure=measure,
        colour_of=lambda frame: frame.name == "c01.fits",
    )
    assert code == 0
    printed = capsys.readouterr().out
    by_exe = {cmd[0]: cmd for cmd in launched}
    assert by_exe["astap/astap.exe"][-2:] == ["-sqm", "400"]
    assert "-sqm" not in by_exe["astap_cli.exe"], "astap.exe -sqm hangs on a colour frame"
    assert "| m01.fits | mono | 19.31 | 19.315 | +0.005 | 27.2657 | 27.2657 | 1886 |" in printed
    assert "| c01.fits | colori | - | 19.500 | - | - | 25.6000 | 380 |" in printed
    assert "scarto assoluto: mediana 0.005, massimo 0.005 su 1 frame" in printed


def test_a_frame_astap_did_not_solve_is_said(tmp_path, capsys):
    folder = tmp_path / "copie"
    folder.mkdir()
    (folder / "m01.fits").write_bytes(b"")
    code = main(
        [str(folder), "--astap", "astap.exe"],
        run=lambda cmd, timeout_s: (1, ""),
        measure=lambda frame, wcs, bias, folder: None,
    )
    assert code == 0
    assert "| m01.fits | mono | - | - | - | - | - | - |" in capsys.readouterr().out
