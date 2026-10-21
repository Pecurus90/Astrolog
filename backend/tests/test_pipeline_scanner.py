"""Lo scanner della pipeline nuova: trova i FITS, legge l'header e ne estrae le chiavi che
scrivono N.I.N.A. e ASIAIR, e nient'altro. Gli header sono quelli veri di `tests/header/`."""

import os
import sys
from pathlib import Path

import pytest

from astrolog.pipeline.scanner import Extracted, Program, Skip, Skipped, find_fits, scan, scan_file

CORPUS = Path(__file__).with_name("header")


def _fits(path: Path, lines: list[str], end: bool = True) -> Path:
    """A header-only FITS file from `KEY = value / comment` lines."""
    cards = [line.ljust(80)[:80] for line in lines]
    if end:
        cards.append("END".ljust(80))
    raw = "".join(cards)
    raw += " " * (-len(raw) % 2880)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw.encode("ascii"))
    return path


def _link(target: Path, link: Path) -> None:
    """A folder link: a junction on Windows (no privilege needed), a symlink elsewhere."""
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        link.symlink_to(target, target_is_directory=True)


def _corpus(name: str) -> list[str]:
    return [
        line
        for line in (CORPUS / name).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def test_finds_every_fits_extension_in_any_case_and_nothing_else(tmp_path):
    for name in ("a.fits", "b.FIT", "c/d.fts", "c/e.Fits", "f.xisf", "g.jpg", "h.fits.txt"):
        _fits(tmp_path / name, ["SIMPLE  = T"])
    found = sorted(p.relative_to(tmp_path).as_posix() for p in find_fits(tmp_path))
    assert found == ["a.fits", "b.FIT", "c/d.fts", "c/e.Fits"]


def test_follows_a_linked_folder_and_sees_each_folder_once(tmp_path):
    real = tmp_path / "real"
    _fits(real / "a.fits", ["SIMPLE  = T"])
    root = tmp_path / "root"
    root.mkdir()
    _link(real, root / "acquisitions")
    _link(root, real / "loop")
    found = list(find_fits(root))
    assert [p.name for p in found] == ["a.fits"]


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


def test_a_header_without_end_is_unreadable(tmp_path):
    got = scan_file(_fits(tmp_path / "t.fits", _corpus("nina.txt"), end=False))
    assert got == Skipped(tmp_path / "t.fits", Skip.UNREADABLE)


def test_a_file_that_cannot_be_opened_is_unreadable(tmp_path):
    missing = tmp_path / "gone.fits"
    assert scan_file(missing) == Skipped(missing, Skip.UNREADABLE)


def test_a_folder_that_cannot_be_opened_is_reported(tmp_path):
    gone = tmp_path / "unplugged"
    assert list(scan(gone)) == [Skipped(gone, Skip.FOLDER_UNREADABLE)]


def test_scan_walks_and_reads_everything(tmp_path):
    _fits(tmp_path / "n.fits", _corpus("nina.txt"))
    _fits(tmp_path / "sub/a.FIT", _corpus("asiair.txt"))
    _fits(tmp_path / "x.fits", ["SIMPLE  = T"])
    results = sorted(scan(tmp_path), key=lambda r: r.path.name)
    assert [type(r).__name__ for r in results] == ["Extracted", "Extracted", "Skipped"]
    assert os.fspath(results[0].path).endswith("a.FIT")
