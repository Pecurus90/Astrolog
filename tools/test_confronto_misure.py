"""The measure comparison reads the reference programs right and says the gaps as ratios.
No program runs here: their launch is faked with the output measured on a real frame."""

import os
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from confronto_misure import (
    Astap,
    Ours,
    Row,
    Subframe,
    astap_from_code,
    card_altitude,
    colour_subframe,
    debayered_name,
    intensity_name,
    main,
    ratios,
    read_subframes,
    subframe_script,
)

# One real frame (ATR2600M, 26/10/2026): what each program answered.
SUBFRAME_CSV = (
    "path,fwhm_px,eccentricity,median,noise,stars,psf_snr,altitude_deg\n"
    "C:/copie/08.fits,2.1918546436391044,0.4523,0.003784237429499626,0.0003233111870382953,5023,"
    "0.5844978444396778,52.5\n"
)
_HEADER = "path,fwhm_px,eccentricity,median,noise,stars,psf_snr,altitude_deg\n"
ASTAP_CODE = 332000523  # HFD_MEDIAN=3,3 and STARS=523 on stdout, two decimals in the code


def test_the_astap_exit_code_carries_hfd_and_stars():
    """Stdout prints the decimal comma of the locale and one decimal: the code has two."""
    assert astap_from_code(ASTAP_CODE) == Astap(hfd_px=3.32, stars=523)
    assert astap_from_code(407000069) == Astap(hfd_px=4.07, stars=69)


@pytest.mark.parametrize("code", [0, 1, -1])
def test_an_astap_failure_is_no_measure(code):
    assert astap_from_code(code) is None


def test_the_subframe_values_come_back_in_adu():
    """The table holds median and noise on [0,1] of a 16-bit range: 0.00378 is 248 ADU."""
    found = read_subframes(SUBFRAME_CSV)
    sub = found["08.fits"]
    assert sub.fwhm_px == pytest.approx(2.1919, abs=1e-4)
    assert sub.eccentricity == pytest.approx(0.4523)
    assert sub.median_adu == pytest.approx(248.0, abs=0.01)
    assert sub.noise_adu == pytest.approx(21.19, abs=0.01)
    assert sub.stars == 5023
    assert sub.psf_snr == pytest.approx(0.5845, abs=1e-4)  # unitless: no scaling
    assert sub.altitude_deg == 52.5


def test_an_altitude_the_program_left_empty_is_none():
    assert (
        read_subframes(_HEADER + "C:/a.fits,2,0.4,0.004,0.0003,10,0.5,\n")["a.fits"].altitude_deg
        is None
    )


def test_the_script_reads_the_psf_snr_and_altitude_columns():
    """Column 28 is PSF SNR: c3 F^2 / (c4 sigma^2) of columns 21 and 12 within 3% (misure.md);
    20 the altitude."""
    script = subframe_script([], [], PurePosixPath("/w"), PurePosixPath("/w/o.csv"))
    assert "m[28], m[20]" in script


def test_our_altitude_comes_from_the_card_as_the_sky_stage_does():
    """M13 da Montebelluna poco dopo il transito: alto; senza sito, niente altezza."""
    cards = {"SWCREATE": "N.I.N.A. 3.2.0.9001 (x64)", "IMAGETYP": "LIGHT",
             "DATE-OBS": "2025-06-29T21:30:00.000", "EXPTIME": 300.0, "SITELAT": 45.494,
             "SITELONG": 11.5218, "RA": 241.2548, "DEC": 17.7166}  # fmt: skip
    altitude = card_altitude(cards)
    assert altitude is not None and 60 < altitude < 75
    assert card_altitude({k: v for k, v in cards.items() if not k.startswith("SITE")}) is None


def test_the_altitude_is_set_beside_the_subframe_selector():
    ours = Ours(1000, 2.0, 100, 10, altitude_deg=51.0)
    table = ratios([_row("a", False, ours, None, Subframe(2.0, 110, 9, 2000, altitude_deg=50.0))])
    assert table["altezza / SubframeSelector"]["mono"] == pytest.approx((1.02, 1.02, 1.02))


def test_psf_snr_is_set_beside_the_subframe_selector():
    ours = Ours(1000, 2.0, 100, 10, psf_snr=0.6)
    sub = Subframe(2.0, 110, 9, 2000, psf_snr=0.5)
    table = ratios([_row("a", False, ours, None, sub)])
    assert table["PSF SNR / SubframeSelector"]["mono"] == pytest.approx((1.2, 1.2, 1.2))


def test_a_script_error_is_said_not_swallowed():
    with pytest.raises(ValueError, match=r"Error: routine\(\)"):
        read_subframes(_HEADER + "error,Error: routine()\n")


def test_the_script_names_every_frame_with_forward_slashes(tmp_path):
    """The script engine reads a backslash as an escape: C:\\new would hold a newline."""
    frames = [PureWindowsPath(r"C:\copie\new.fits"), PureWindowsPath(r"C:\copie\b.fits")]
    colour = [PureWindowsPath(r"C:\copie\canon.fits")]
    work, out = PureWindowsPath(r"C:\out"), PureWindowsPath(r"C:\out\ss.csv")
    script = subframe_script(frames, colour, work, out)
    assert '"C:/copie/new.fits"' in script and '"C:/copie/b.fits"' in script
    assert '"C:/copie/canon.fits"' in script and '"C:/out"' in script
    assert '"C:/out/ss.csv"' in script
    assert "\\" not in script.split("var lines")[0]


def test_colour_frames_are_debayered_with_vng_before_they_are_measured():
    """As WBPP: Debayer, pattern from the header, VNG; the copy is what gets measured."""
    script = subframe_script([], [PurePosixPath("/c/canon.fits")], PurePosixPath("/w"),
                             PurePosixPath("/w/ss.csv"))  # fmt: skip
    debayer = script.index("new Debayer")
    assert debayer < script.index("new SubframeSelector")
    assert "Debayer.prototype.VNG" in script and "Debayer.prototype.Auto" in script
    assert 'D.outputPostfix = "_d"' in script and '"_d"' in script
    assert debayered_name(PurePosixPath("/c/canon.fits")) == "canon_d.xisf"


def test_colour_frames_give_their_intensity_too_and_its_psf_snr_is_compared():
    """HSI (min + max) / 2 of the debayered copy, the plane measure_frame works on; the PSF SNR
    of the colour row is the intensity's (Marco, 28/10/2026)."""
    script = subframe_script([], [PurePosixPath("/c/canon.fits")], PurePosixPath("/w"),
                             PurePosixPath("/w/ss.csv"))  # fmt: skip
    assert "(max($T[0],$T[1],$T[2])+min($T[0],$T[1],$T[2]))/2" in script
    assert script.index("new PixelMath") < script.index("new SubframeSelector")
    assert intensity_name(PurePosixPath("/c/canon.fits")) == "canon_d_i.xisf"
    rgb = Subframe(2.0, 100, 9, 400, psf_snr=0.03)
    assert colour_subframe(rgb, Subframe(2.0, 100, 8, 500, psf_snr=0.9)).psf_snr == 0.9
    assert colour_subframe(rgb, None).psf_snr is None
    assert colour_subframe(None, rgb) is None


def _row(name, color, ours, astap, sub):
    return Row(name, color, ours, astap, sub)


def test_ratios_split_mono_and_color():
    rows = [
        _row("a", False, Ours(1000, 2.0, 100, 10), Astap(2.5, 100), Subframe(1.5, 110, 9, 2000)),
        _row("b", False, Ours(3000, 3.0, 200, 30), Astap(3.0, 300), Subframe(2.0, 190, 30, 3000)),
        _row("c", True, Ours(500, 4.0, 50, 5), Astap(5.0, 50), Subframe(3.0, 50, 10, 400)),
    ]
    table = ratios(rows)
    stars = table["stelle / ASTAP"]
    assert stars["mono"] == (10.0, 10.0, 10.0)
    assert stars["colori"] == (10.0, 10.0, 10.0)
    hfd = table["HFD / ASTAP HFD"]["mono"]
    assert hfd == pytest.approx((0.8, 0.9, 1.0))
    noise = table["rumore / SubframeSelector"]["colori"]
    assert noise == pytest.approx((0.5, 0.5, 0.5))


def test_fwhm_and_eccentricity_are_set_beside_the_subframe_selector():
    ours = Ours(1000, 2.0, 100, 10, fwhm_px=2.2, eccentricity=0.45)
    table = ratios([_row("a", False, ours, None, Subframe(2.0, 110, 9, 2000, eccentricity=0.5))])
    assert table["FWHM / SubframeSelector FWHM"]["mono"] == pytest.approx((1.1, 1.1, 1.1))
    assert table["eccentricita' / SubframeSelector"]["mono"] == pytest.approx((0.9, 0.9, 0.9))


def test_a_missing_program_leaves_its_ratios_out():
    rows = [_row("a", False, Ours(1000, 2.0, 100.0, 10.0), None, None)]
    table = ratios(rows)
    assert table["HFD / ASTAP HFD"] == {}
    assert table["fondo / SubframeSelector"] == {}


def test_main_measures_every_frame_and_prints_the_table(tmp_path, capsys):
    folder = tmp_path / "copie"
    folder.mkdir()
    for name in ("08.fits", "09.fit"):
        (folder / name).write_bytes(b"")
    (folder / "nota.txt").write_text("non un frame")
    launched = []

    def run(cmd, timeout_s):
        launched.append(cmd)
        if "-analyse" in cmd:
            return ASTAP_CODE, "HFD_MEDIAN=3,3\nSTARS=523\n"
        out = next(a for a in cmd if a.startswith("-r="))[3:]
        csv = Path(out).with_suffix(".csv")
        script = Path(out).read_text(encoding="utf-8")
        mono, colour = (script.split("\n")[i] for i in (0, 1))
        assert "08.fits" in mono and "09.fit" not in mono and "09.fit" in colour
        csv.write_text(
            _HEADER + f"{(folder / '08.fits').as_posix()},2.0,0.40,0.0038,0.0003,5000,0.5,40\n"
            f"{csv.parent.as_posix()}/09_d.xisf,2.5,0.45,0.0040,0.0004,4000,0.4,41\n"
        )
        return 0, ""

    def measure(path):
        return Ours(3000, 2.9, 244.0, 22.9, 2.6, 0.42), path.name == "09.fit"

    code = main(
        [str(folder), "--astap", "astap_cli", "--subframe", "PixInsight"],  # software-ok
        run=run,
        measure=measure,
    )
    assert code == 0
    printed = capsys.readouterr().out
    assert "08.fits" in printed and "09.fit" in printed and "nota.txt" not in printed
    assert sum("-analyse" in c for c in launched) == 2, "ASTAP once a frame"
    assert sum(any(a.startswith("-r=") for a in c) for c in launched) == 1, "one batch"
    assert "stelle / ASTAP" in printed
    row = "| 09.fit | colori | 3000 | 2.90 | 2.60 | 0.42 | 244.0 | 22.9 | 523 | 3.32 | 4000 | 2.50 "
    row += "| 0.45 |"
    assert row in printed


def test_main_without_frames_says_so(tmp_path, capsys):
    assert main([str(tmp_path)], run=lambda c, t: (0, ""), measure=lambda p: None) == 1
    assert "nessun frame" in capsys.readouterr().out
