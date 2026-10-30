"""The measure comparison reads the reference programs right and says the gaps as ratios.
No program runs here: their launch is faked with the output measured on a real frame."""

import json
import os
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from confronto_misure import (
    NAMES,
    Analysis,
    Astap,
    Ours,
    Row,
    analysis_script,
    astap_from_code,
    card_altitude,
    debayered_name,
    group_of,
    main,
    ratios,
    read_analysis,
    read_groups,
    stage_clock,
    stars,
    times,
)

ASTAP_CODE = 332000523  # HFD_MEDIAN=3,3 and STARS=523 on stdout, two decimals in the code


def _row_of(**values):
    """A measurements row in NAMES order; what is not given is 0, as the program stores it."""
    return [values.get(name, 0) for name in NAMES]


# One real frame (ATR2600M, 30/10/2026): what Image Analysis answered, the columns the bench uses.
REAL = _row_of(Path="C:/copie/08.fits", Stars=5023, FWHMpx=2.1918546, Eccentricity=0.4523,
               Median=0.0037842374, Noise=0.00032331119, PSFSNR=0.58449784, Altitude=52.5,
               Airmass=1.26, Flags=0x2, FWHMTilt=0.0, FWHMCurvature=0.031)  # fmt: skip


def _result(rows, times_=(), error=None):
    found = {"names": list(NAMES), "rows": rows, "times": [list(t) for t in times_]}
    return json.dumps(found | ({"error": error} if error else {}))


def test_the_astap_exit_code_carries_hfd_and_stars():
    """Stdout prints the decimal comma of the locale and one decimal: the code has two."""
    assert astap_from_code(ASTAP_CODE) == Astap(hfd_px=3.32, stars=523)
    assert astap_from_code(407000069) == Astap(hfd_px=4.07, stars=69)


@pytest.mark.parametrize("code", [0, 1, -1])
def test_an_astap_failure_is_no_measure(code):
    assert astap_from_code(code) is None


def test_every_column_of_the_measurements_table_is_read_by_name():
    """57 columns (ImageAnalysis doc, Table 6); median and noise stay on [0,1] as it stores them."""
    assert len(NAMES) == 57 and NAMES[3] == "Path" and NAMES[-1] == "Offset"
    found = read_analysis(_result([REAL]))["08.fits"]
    assert found.values["Stars"] == 5023
    assert found.values["FWHMpx"] == pytest.approx(2.19185, abs=1e-5)
    assert found.values["Median"] == pytest.approx(0.0037842374)
    assert found.values["Airmass"] == 1.26
    assert "Path" not in found.values


def test_an_undefined_value_is_none_and_a_flagged_zero_is_a_value():
    """Undefined stored as 0; the Flags bit mask says which can be a true 0 (Table 7)."""
    values = read_analysis(_result([REAL]))["08.fits"].values
    assert values["FWHMTilt"] == 0.0, "bit 0x2 set: a defined zero"
    assert values["ElongationAngle"] is None, "bit 0x1 unset"
    assert values["Trails"] is None, "bit 0x8 unset"
    assert values["MoonIllumination"] is None
    assert values["Gain"] is None


def test_the_seconds_of_each_frame_come_back_by_label():
    text = _result([REAL], [("C:/copie/08.fits", "estese", 3.3), ("C:/copie/08.fits", "base", 2.2)])
    assert read_analysis(text)["08.fits"].seconds == {"estese": 3.3, "base": 2.2}


def test_a_script_error_is_said_not_swallowed():
    with pytest.raises(ValueError, match=r"no column Foo"):
        read_analysis(_result([], error="Error: no column Foo"))


def test_the_script_names_every_frame_with_forward_slashes():
    """The script engine reads a backslash as an escape: C:\\new would hold a newline."""
    frames = [PureWindowsPath(r"C:\copie\new.fits"), PureWindowsPath(r"C:\copie\b.fits")]
    colour = [PureWindowsPath(r"C:\copie\canon.fits")]
    work, out = PureWindowsPath(r"C:\out"), PureWindowsPath(r"C:\out\ia.json")
    script = analysis_script(frames, colour, work, out, timed=True)
    assert '"C:/copie/new.fits"' in script and '"C:/copie/b.fits"' in script
    assert '"C:/copie/canon.fits"' in script and '"C:/out"' in script
    assert '"C:/out/ia.json"' in script
    assert "\\" not in script.split("function")[0]


def test_the_script_reads_the_columns_by_their_constants():
    """Never a literal index: the doc says the order may change."""
    script = analysis_script([], [], PurePosixPath("/w"), PurePosixPath("/w/o.json"), timed=False)
    assert 'ImageAnalysis["measurements_measurement" + n]' in script
    assert json.dumps(list(NAMES)) in script


def test_colour_frames_are_debayered_with_vng_before_they_are_measured():
    """As WBPP: Debayer, pattern from the header, VNG; the RGB copy is what gets measured."""
    script = analysis_script([], [PurePosixPath("/c/canon.fits")], PurePosixPath("/w"),
                             PurePosixPath("/w/o.json"), timed=False)  # fmt: skip
    assert script.index("new Debayer") < script.index("new ImageAnalysis")
    assert "Debayer.VNG" in script and "Debayer.Auto" in script
    assert 'D.outputPostfix = "_d"' in script
    assert "PixelMath" not in script, "no intensity copy: the program takes the RGB itself"
    assert debayered_name(PurePosixPath("/c/canon.fits")) == "canon_d.xisf"


def test_the_measure_run_has_the_extended_measures_and_no_cache():
    script = analysis_script([], [], PurePosixPath("/w"), PurePosixPath("/w/o.json"), timed=False)
    assert "analyse(files, true, true)" in script
    assert "P.fileCache = false" in script


def test_each_frame_is_timed_alone_with_and_without_the_extended_measures():
    """One frame at a time, no file threads: the seconds of a frame, as ours are."""
    untimed = analysis_script([], [], PurePosixPath("/w"), PurePosixPath("/w/o.json"), timed=False)
    timed = analysis_script([], [], PurePosixPath("/w"), PurePosixPath("/w/o.json"), timed=True)
    assert "let timed = false;" in untimed and "let timed = true;" in timed
    assert 'clock(f, "estese", () => analyse([f], true, false))' in timed
    assert 'clock(f, "base", () => analyse([f], false, false))' in timed


def test_our_altitude_comes_from_the_card_as_the_sky_stage_does():
    """M13 da Montebelluna poco dopo il transito: alto; senza sito, niente altezza."""
    cards = {"SWCREATE": "N.I.N.A. 3.2.0.9001 (x64)", "IMAGETYP": "LIGHT",
             "DATE-OBS": "2025-06-29T21:30:00.000", "EXPTIME": 300.0, "SITELAT": 45.494,
             "SITELONG": 11.5218, "RA": 241.2548, "DEC": 17.7166}  # fmt: skip
    altitude = card_altitude(cards)
    assert altitude is not None and 60 < altitude < 75
    assert card_altitude({k: v for k, v in cards.items() if not k.startswith("SITE")}) is None


def test_groups_go_by_the_longest_name_prefix():
    groups = read_groups("A M31_Andromeda\nB M3\n\nB NGC_7023\n")
    assert group_of("M31_Andromeda_Poseidon_0.fits", groups) == "A"
    assert group_of("M33_Triangulum_0.fits", groups) == "B"
    assert group_of("IC_405_0.fits", groups) == "-"
    assert group_of("x.fits", {}) == "-"


def _analysis(**values):
    return Analysis(values=values)


def _row(name, color, ours, astap=None, analysis=None):
    return Row(name, color, "A", ours, astap, analysis)


def test_ratios_split_group_and_kind():
    rows = [
        _row("a", False, Ours(1000, 2.0, 100, 10), Astap(2.5, 100),
             _analysis(Stars=2000, Noise=9 / 65535)),
        _row("b", False, Ours(3000, 3.0, 200, 30), Astap(3.0, 300),
             _analysis(Stars=3000, Noise=30 / 65535)),
        _row("c", True, Ours(500, 4.0, 50, 5), Astap(5.0, 50), _analysis(Noise=10 / 65535)),
        Row("d", False, "B", Ours(500, 4.0, 50, 5), None, _analysis(Stars=250)),
    ]  # fmt: skip
    table = ratios(rows)
    assert table["stelle / ASTAP"]["mono A"] == (2, 10.0, 10.0, 10.0)
    assert table["stelle / ASTAP"]["colori A"] == (1, 10.0, 10.0, 10.0)
    assert table["HFD / ASTAP HFD"]["mono A"] == pytest.approx((2, 0.8, 0.9, 1.0))
    assert table["stelle / Image Analysis"]["mono B"] == (1, 2.0, 2.0, 2.0)
    assert table["rumore / Image Analysis"]["colori A"] == pytest.approx((1, 0.5, 0.5, 0.5))


def test_every_common_measure_is_set_beside_image_analysis():
    ours = Ours(1000, 2.0, 100, 10, fwhm_px=2.2, eccentricity=0.45, psf_snr=0.6,
                altitude_deg=51.0)  # fmt: skip
    theirs = _analysis(FWHMpx=2.0, Eccentricity=0.5, Median=110 / 65535, PSFSNR=0.5,
                       Altitude=50.0, Airmass=1.3)  # fmt: skip
    table = ratios([_row("a", False, ours, analysis=theirs)])
    assert table["FWHM / Image Analysis"]["mono A"] == pytest.approx((1, 1.1, 1.1, 1.1))
    assert table["eccentricita' / Image Analysis"]["mono A"] == pytest.approx((1, 0.9, 0.9, 0.9))
    assert table["PSF SNR / Image Analysis"]["mono A"] == pytest.approx((1, 1.2, 1.2, 1.2))
    assert table["altezza / Image Analysis"]["mono A"] == pytest.approx((1, 1.02, 1.02, 1.02))
    assert table["fondo / mediana Image Analysis"]["mono A"][2] == pytest.approx(100 / 110)
    airmass = table["massa d'aria / Image Analysis"]["mono A"][2]
    assert 1.28 / 1.3 < airmass < 1.0, "ours at 51 degrees, a bit under its 1.3 at 50"


def test_a_missing_program_or_undefined_value_leaves_its_ratio_out():
    rows = [_row("a", False, Ours(1000, 2.0, 100.0, 10.0), None, _analysis(PSFSNR=None))]
    table = ratios(rows)
    assert table["HFD / ASTAP HFD"] == {}
    assert table["PSF SNR / Image Analysis"] == {}


def _frame(colour: bool) -> np.ndarray:
    rng = np.random.default_rng(1)
    data = rng.normal(1000, 10, (256, 256))
    yy, xx = np.mgrid[:256, :256]
    for y, x in rng.uniform(20, 236, (60, 2)):
        data += 3000 * np.exp(-((yy - y) ** 2 + (xx - x) ** 2) / (2 * 1.5**2))
    return data if not colour else data * np.tile([[1.0, 0.8], [0.8, 0.6]], (128, 128))


def test_the_stage_clock_times_what_measure_frame_calls_and_puts_it_back():
    names = {name: getattr(stars, name) for name in ("median3x3", "shape_of", "detect", "sep")}
    seconds: dict[str, float] = {}
    with stage_clock(seconds):
        stars.measure_frame(_frame(False), saturation=65535, pattern=None)
    expected = {"fondo sep", "mediana 3x3", "forma", "stelle e flusso PSF", "rumore MRS"}
    assert expected <= set(seconds)
    assert "debayer VNG" not in seconds and "rumore per piano colore" not in seconds
    assert all(getattr(stars, name) is fn for name, fn in names.items())


def test_a_stage_inside_another_counts_once():
    """_mosaic_noise calls mrs_noise per plane: that time is the plane noise's, not twice."""
    seconds: dict[str, float] = {}
    with stage_clock(seconds):
        stars.measure_frame(_frame(True), saturation=65535, pattern="RGGB")
    assert {"debayer VNG", "rumore per piano colore", "rumore MRS"} <= set(seconds)
    alone: dict[str, float] = {}
    with stage_clock(alone):
        stars.mrs_noise(_frame(False))
    assert set(alone) == {"rumore MRS"}


def test_the_times_are_medians_per_kind_of_seconds_a_frame():
    rows = [
        _row("a", False, Ours(1, 1.0, 1, 1, seconds={"mediana 3x3": 0.5, "totale": 2.0}), None,
             Analysis({}, {"base": 2.0, "estese": 3.0})),
        _row("b", False, Ours(1, 1.0, 1, 1, seconds={"mediana 3x3": 0.7, "totale": 4.0}), None,
             Analysis({}, {"base": 2.4, "estese": 3.6})),
        _row("c", True, Ours(1, 1.0, 1, 1, seconds={"totale": 9.0}), None,
             Analysis({}, {"debayer": 4.0, "base": 1.0, "estese": 2.0})),
    ]  # fmt: skip
    table = times(rows)
    assert table["mono"]["AstroLog mediana 3x3"] == pytest.approx(0.6)
    assert table["mono"]["AstroLog totale"] == pytest.approx(3.0)
    assert table["mono"]["Image Analysis estese"] == pytest.approx(3.3)
    assert table["colori"]["Image Analysis debayer"] == 4.0
    assert table["colori"]["Image Analysis estese + debayer"] == 6.0


def test_main_measures_every_frame_and_prints_the_tables(tmp_path, capsys):
    folder = tmp_path / "copie"
    folder.mkdir()
    for name in ("08.fits", "09.fit"):
        (folder / name).write_bytes(b"")
    (folder / "nota.txt").write_text("non un frame")
    (tmp_path / "gruppi.txt").write_text("A 08\nB 09\n")
    launched = []

    def run(cmd, timeout_s):
        launched.append(cmd)
        if "-analyse" in cmd:
            return ASTAP_CODE, "HFD_MEDIAN=3,3\nSTARS=523\n"
        script = Path(next(a for a in cmd if a.startswith("-r="))[3:])
        text = script.read_text(encoding="utf-8")
        mono, colour = (line for line in text.split("\n")[1:3])
        assert "08.fits" in mono and "09.fit" not in mono and "09.fit" in colour
        deb = f"{script.parent.as_posix()}/09_d.xisf"
        rows = [_row_of(Path=(folder / "08.fits").as_posix(), Stars=5000, FWHMpx=2.0),
                _row_of(Path=deb, Stars=4000, FWHMpx=2.5, Eccentricity=0.45)]  # fmt: skip
        script.with_suffix(".json").write_text(_result(rows, [(deb, "debayer", 4.0)]))
        return 0, ""

    def measure(path):
        ours = Ours(3000, 2.9, 244.0, 22.9, 2.6, 0.42, seconds={"totale": 5.0})
        return ours, path.name == "09.fit"

    out = tmp_path / "banco.json"
    code = main([str(folder), "--astap", "astap_cli", "--reference", "PI",
                 "--groups", str(tmp_path / "gruppi.txt"), "--out", str(out)],
                run=run, measure=measure)  # fmt: skip
    assert code == 0
    printed = capsys.readouterr().out
    assert "08.fits" in printed and "09.fit" in printed and "nota.txt" not in printed
    assert sum("-analyse" in c for c in launched) == 2, "ASTAP once a frame"
    assert sum(any(a.startswith("-r=") for a in c) for c in launched) == 1, "one batch"
    assert "| 09.fit | colori | B | 3000 | 4000 | 2.60 | 2.50 | 0.42 | 0.45 |" in printed
    assert "- stelle / Image Analysis, mono A: n=1" in printed
    assert "Image Analysis debayer" in printed and "AstroLog totale" in printed
    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved[1]["analysis"]["values"]["Stars"] == 4000


def test_main_without_frames_says_so(tmp_path, capsys):
    assert main([str(tmp_path)], run=lambda c, t: (0, ""), measure=lambda p: None) == 1
    assert "nessun frame" in capsys.readouterr().out
