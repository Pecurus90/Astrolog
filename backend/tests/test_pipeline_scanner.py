"""Lo scanner della pipeline nuova: trova i FITS, legge l'header e ne estrae le chiavi che
scrivono N.I.N.A. e ASIAIR, e nient'altro. Gli header sono quelli veri di `tests/header/`."""

import math
import os
import re
import sys
from pathlib import Path

import pytest

from astrolog.pipeline.scanner import Extracted, Program, Skip, Skipped, scan, scan_file

CORPUS = Path(__file__).with_name("header")


def _fits(path: Path, lines: list[str], end: bool = True) -> Path:
    """A FITS file from `KEY = value / comment` lines, with the zero pixels its header announces
    (a file shorter than that is incomplete)."""
    cards = [line.ljust(80)[:80] for line in lines]
    if end:
        cards.append("END".ljust(80))
    raw = "".join(cards)
    raw += " " * (-len(raw) % 2880)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw.encode("latin-1") + b"\0" * _span(lines))
    return path


def _span(lines: list[str]) -> int:
    keys = {
        line[:8].strip(): line[10:].split("/")[0].strip() for line in lines if line[8:10] == "= "
    }
    try:
        axes = [int(keys[f"NAXIS{n}"]) for n in range(1, int(keys["NAXIS"]) + 1)]
        size = abs(int(keys["BITPIX"])) // 8 * math.prod(axes) if axes else 0
    except (KeyError, ValueError):
        return 0
    return size + (-size % 2880)


def _link(target: Path, link: Path) -> None:
    """A folder link: a junction on Windows (no privilege needed), a symlink elsewhere."""
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        link.symlink_to(target, target_is_directory=True)


def _corpus(name: str) -> list[str]:
    """A real header, with the image shrunk to 16x16 so the test file stays small."""
    return [
        re.sub(r"^(NAXIS[12]  =)\s*\d+", lambda m: m.group(1) + "16".rjust(21), line)
        for line in (CORPUS / name).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def test_the_scan_reads_through_a_linked_folder_once(tmp_path):
    real = tmp_path / "real"
    _fits(real / "a.fits", _corpus("nina.txt"))
    root = tmp_path / "root"
    root.mkdir()
    _link(real, root / "acquisitions")
    _link(root, real / "loop")
    results = list(scan(root))
    assert [(r.path.name, type(r).__name__) for r in results] == [("a.fits", "Extracted")]


def test_a_file_beyond_260_characters_is_read(tmp_path):
    from astrolog.pipeline.walk import long_path

    deep = str(tmp_path)
    while len(deep) < 300:
        deep = os.path.join(deep, "Nebulosa della Testa di Cavallo - IC 434 - sessione lunga")
    os.makedirs(long_path(deep), exist_ok=True)
    lines = _corpus("nina.txt")
    cards = "".join(line.ljust(80)[:80] for line in lines) + "END".ljust(80)
    with open(long_path(os.path.join(deep, "frame.fits")), "wb") as fh:
        fh.write((cards + " " * (-len(cards) % 2880)).encode("latin-1") + b"\0" * _span(lines))
    results = list(scan(tmp_path))
    assert [type(r).__name__ for r in results] == ["Extracted"]


def test_what_the_walk_leaves_out_is_skipped_with_its_reason(tmp_path):
    _fits(tmp_path / "ok.fits", _corpus("nina.txt"))
    _fits(tmp_path / ".Trashes" / "deleted.fits", _corpus("nina.txt"))
    _fits(tmp_path / ".M42.fits.icloud", ["SIMPLE  = T"])
    skipped = {(r.path.name, r.reason) for r in scan(tmp_path) if isinstance(r, Skipped)}
    assert skipped == {(".Trashes", Skip.HIDDEN), ("M42.fits", Skip.ONLINE_ONLY)}


def test_nina_file_gives_every_nina_key_it_carries(tmp_path):
    lines = _corpus("nina.txt")
    got = scan_file(_fits(tmp_path / "n.fits", lines))
    assert isinstance(got, Extracted)
    assert got.program is Program.NINA
    assert got.values["IMAGETYP"] == "LIGHT"
    assert got.values["SWCREATE"].startswith("N.I.N.A.")
    carried = {line[:8].strip() for line in lines if line[8:10] == "= "}
    assert set(got.values) == carried


@pytest.mark.parametrize("name", ["asiair.txt", "asiair_am3.txt", "asiair_asi2600.txt"])
def test_asiair_file_gives_every_asiair_key_it_carries(tmp_path, name):
    lines = _corpus(name)
    got = scan_file(_fits(tmp_path / "a.fit", lines))
    assert isinstance(got, Extracted)
    assert got.program is Program.ASIAIR
    carried = {line[:8].strip() for line in lines if line[8:10] == "= "}
    assert set(got.values) == carried


def test_string_values_lose_quotes_and_padding(tmp_path):
    got = scan_file(_fits(tmp_path / "a.fit", _corpus("asiair_asi2600.txt")))
    assert isinstance(got, Extracted)
    assert got.values["IMAGETYP"] == "Light"
    assert got.values["CREATOR"] == "ZWO ASIAIR Plus"


def test_keys_outside_the_known_list_are_kept_and_reported(tmp_path):
    lines = [*_corpus("nina.txt"), "STRKEYWD= 'Example'", "HISTORY  some step", "ISO     = 800"]
    got = scan_file(_fits(tmp_path / "n.fits", lines))
    assert isinstance(got, Extracted)
    assert got.values["STRKEYWD"] == "Example"
    assert got.values["ISO"] == 800
    assert got.unknown == frozenset({"STRKEYWD", "ISO"})
    assert "HISTORY" not in got.values


@pytest.mark.parametrize("name", ["nina.txt", "asiair.txt", "asiair_am3.txt", "asiair_asi2600.txt"])
def test_the_real_headers_have_no_unknown_key(tmp_path, name):
    got = scan_file(_fits(tmp_path / "f.fits", _corpus(name)))
    assert isinstance(got, Extracted)
    assert got.unknown == frozenset()


def test_a_broken_card_keeps_its_text_and_an_empty_one_stays(tmp_path):
    lines = [
        "SIMPLE  =                    T",
        "BITPIX  =                   16",
        "NAXIS   =                    0",
        "SWCREATE= 'N.I.N.A. 3.2.0.9001 (x64)'",
        "GAIN    = abc / x",
        "EXPOSURE= 1.2.3",
        "FILTER  =",
    ]
    got = scan_file(_fits(tmp_path / "odd.fits", lines))
    assert isinstance(got, Extracted)
    assert got.values["GAIN"] == "abc"
    assert got.values["EXPOSURE"] == "1.2.3"
    assert got.values["FILTER"] == ""


_NINA_HEAD = [
    "SIMPLE  =                    T",
    "BITPIX  =                   16",
    "NAXIS   =                    2",
    "NAXIS1  =                    4",
    "NAXIS2  =                    4",
    "SWCREATE= 'N.I.N.A. 3.2.0.9001 (x64)'",
]


def test_a_control_character_in_a_value_does_not_stop_the_scan(tmp_path):
    _fits(tmp_path / "a_bad.fits", [*_NINA_HEAD, "OBJECT  = 'M 31\tAndromeda'"])
    _fits(tmp_path / "b_good.fits", _corpus("nina.txt"))
    results = list(scan(tmp_path))
    assert [r.path.name for r in results] == ["a_bad.fits", "b_good.fits"]
    assert all(isinstance(r, Extracted) for r in results)


def test_a_value_with_a_colon_stays_under_its_own_key(tmp_path):
    got = scan_file(_fits(tmp_path / "sh2.fits", [*_NINA_HEAD, "OBJECT  = 'Sh2: 155'"]))
    assert isinstance(got, Extracted)
    assert got.values["OBJECT"] == "Sh2: 155"


def test_commentary_with_an_equal_sign_is_not_a_key(tmp_path):
    got = scan_file(_fits(tmp_path / "c.fits", [*_NINA_HEAD, "COMMENT = 'x'", "HISTORY = 'y'"]))
    assert isinstance(got, Extracted)
    assert not {"COMMENT", "HISTORY"} & set(got.values)


def test_a_hierarch_key_is_kept_and_reported(tmp_path):
    got = scan_file(_fits(tmp_path / "h.fits", [*_NINA_HEAD, "HIERARCH ESO DET = 5"]))
    assert isinstance(got, Extracted)
    assert got.values["ESO DET"] == 5
    assert "ESO DET" in got.unknown


def test_accented_letters_written_by_nina_are_kept(tmp_path):
    got = scan_file(_fits(tmp_path / "neb.fits", [*_NINA_HEAD, "OBJECT  = 'Nébuleuse'"]))
    assert isinstance(got, Extracted)
    assert got.values["OBJECT"] == "Nébuleuse"


def test_the_checksums_of_the_cfitsio_writer_are_nina_keys(tmp_path):
    lines = [
        *_corpus("nina.txt"),
        "BSCALE  =                  1.0",
        "CHECKSUM= 'ZaFbZYDbZaDbZYDb'",
        "DATASUM = '2384729374'",
    ]
    got = scan_file(_fits(tmp_path / "c.fits", lines))
    assert isinstance(got, Extracted)
    assert got.unknown == frozenset()


def _compressed(path: Path) -> Path:
    """A tile-compressed N.I.N.A. file as cfitsio writes it: empty primary, keys in page 2."""
    import numpy as np
    from astropy.io import fits

    header = fits.Header()
    for line in _corpus("nina.txt"):
        key = line[:8].strip()
        if line[8:10] == "= " and key not in {
            "SIMPLE",
            "BITPIX",
            "NAXIS",
            "NAXIS1",
            "NAXIS2",
            "EXTEND",
            "BZERO",
            "BSCALE",
        }:
            header.append(fits.Card.fromstring(line.ljust(80)))
    data = np.zeros((8, 8), dtype=np.uint16)
    fits.HDUList([fits.PrimaryHDU(), fits.CompImageHDU(data, header)]).writeto(path)
    return path


@pytest.mark.parametrize("name", ["light.fits.fz", "light.fits"])
def test_a_compressed_nina_file_gives_its_keys_from_the_image_page(tmp_path, name):
    got = scan_file(_compressed(tmp_path / name))
    assert isinstance(got, Extracted)
    assert got.program is Program.NINA
    assert got.values["IMAGETYP"] == "LIGHT"
    assert got.unknown == frozenset()


def test_the_table_geometry_of_a_compressed_file_is_not_the_frame(tmp_path):
    got = scan_file(_compressed(tmp_path / "light.fits.fz"))
    assert isinstance(got, Extracted)
    assert "NAXIS1" not in got.values and "NAXIS2" not in got.values
    assert (got.values["ZNAXIS1"], got.values["ZNAXIS2"]) == (8, 8)


def test_a_user_z_key_in_a_compressed_file_is_unknown(tmp_path):
    from astropy.io import fits

    path = _compressed(tmp_path / "light.fits.fz")
    with fits.open(path, mode="update", disable_image_compression=True) as hdul:
        hdul[1].header["ZOOM"] = 2
    got = scan_file(path)
    assert isinstance(got, Extracted)
    assert got.unknown == frozenset({"ZOOM"})


def test_a_z_key_in_an_uncompressed_file_is_unknown(tmp_path):
    got = scan_file(_fits(tmp_path / "z.fits", [*_corpus("nina.txt"), "ZOOM    = 2"]))
    assert isinstance(got, Extracted)
    assert got.unknown == frozenset({"ZOOM"})


def test_a_long_value_split_over_continue_cards_is_read_whole(tmp_path):
    long_name = "A very long target name that does not fit in one card at all"
    lines = [
        "SIMPLE  =                    T",
        "BITPIX  =                   16",
        "NAXIS   =                    0",
        "SWCREATE= 'N.I.N.A. 3.2.0.9001 (x64)'",
        "OBJECT  = 'A very long target name that does not fit in one card&'",
        "CONTINUE  ' at all'",
    ]
    got = scan_file(_fits(tmp_path / "long.fits", lines))
    assert isinstance(got, Extracted)
    assert got.values["OBJECT"] == long_name


def test_a_file_from_another_program_is_skipped_with_its_reason(tmp_path):
    got = scan_file(_fits(tmp_path / "x.fits", ["SIMPLE  = T", "SWCREATE= 'SomethingElse 1.0'"]))
    assert got == Skipped(tmp_path / "x.fits", Skip.NOT_SUPPORTED)


def test_a_file_rewritten_by_another_program_is_skipped(tmp_path):
    lines = [*_corpus("asiair_asi2600.txt"), "PROGRAM = 'Stacker 1.0'", "STACKCNT= 30"]
    got = scan_file(_fits(tmp_path / "stack.fit", lines))
    assert got == Skipped(tmp_path / "stack.fit", Skip.REWRITTEN)


def test_a_rewrite_that_dropped_the_capture_program_is_rewritten(tmp_path):
    lines = [line for line in _corpus("nina.txt") if not line.startswith("SWCREATE")] + [
        "PROGRAM = 'Editor 1.9.3'"
    ]
    got = scan_file(_fits(tmp_path / "saved.fits", lines))
    assert got == Skipped(tmp_path / "saved.fits", Skip.REWRITTEN)


def test_a_header_without_end_is_unreadable(tmp_path):
    got = scan_file(_fits(tmp_path / "t.fits", _corpus("nina.txt"), end=False))
    assert got == Skipped(tmp_path / "t.fits", Skip.UNREADABLE)


def test_a_file_that_cannot_be_opened_is_unreadable(tmp_path):
    missing = tmp_path / "gone.fits"
    assert scan_file(missing) == Skipped(missing, Skip.UNREADABLE)


def test_a_folder_that_cannot_be_opened_is_reported(tmp_path):
    gone = tmp_path / "unplugged"
    assert list(scan(gone)) == [Skipped(gone, Skip.UNREACHABLE)]


def test_scan_walks_and_reads_everything(tmp_path):
    _fits(tmp_path / "n.fits", _corpus("nina.txt"))
    _fits(tmp_path / "sub/a.FIT", _corpus("asiair.txt"))
    _fits(tmp_path / "x.fits", ["SIMPLE  = T"])
    results = sorted(scan(tmp_path), key=lambda r: r.path.name)
    assert [type(r).__name__ for r in results] == ["Extracted", "Extracted", "Skipped"]
    assert os.fspath(results[0].path).endswith("a.FIT")
