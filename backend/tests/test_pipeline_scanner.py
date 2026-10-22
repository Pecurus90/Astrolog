"""Scanner: trova i FITS, estrae chiavi di N.I.N.A. e ASIAIR, nient'altro. Header veri da
`tests/header/`."""

import math
import os
import re
import time
import warnings
from pathlib import Path
from typing import Any

import pytest

from astrolog.pipeline.changes import add_root
from astrolog.pipeline.scan import scan_root
from astrolog.pipeline.scanner import Extracted, Skip, Skipped, scan_file
from astrolog.pipeline.values import Program
from conftest import HEADER_CORPUS, NOW, folder_link


def _fits(path: Path, lines: list[str], end: bool = True) -> Path:
    """FITS from `KEY = value / comment` lines, with zero pixels its header announces (shorter:
    incomplete)."""
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


def _corpus(name: str) -> list[str]:
    """Real header, image shrunk to 16x16 so test file stays small."""
    return [
        re.sub(r"^(NAXIS[12]  =)\s*\d+", lambda m: m.group(1) + "16".rjust(21), line)
        for line in (HEADER_CORPUS / name).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def test_the_scan_reads_through_a_linked_folder_once(conn, tmp_path):
    real = tmp_path / "real"
    _fits(real / "a.fits", _corpus("nina.txt"))
    root = tmp_path / "root"
    root.mkdir()
    folder_link(real, root / "acquisitions")
    folder_link(root, real / "loop")
    result = scan_root(conn, add_root(conn, root, NOW), NOW)
    assert result.changes.new == ["acquisitions/a.fits"]
    assert (result.frames, result.skipped) == (1, [])


def test_a_file_beyond_260_characters_is_read(conn, tmp_path):
    from astrolog.pipeline.walk import long_path

    deep = str(tmp_path)
    while len(deep) < 300:
        deep = os.path.join(deep, "Nebulosa della Testa di Cavallo - IC 434 - sessione lunga")
    os.makedirs(long_path(deep), exist_ok=True)
    lines = _corpus("nina.txt")
    cards = "".join(line.ljust(80)[:80] for line in lines) + "END".ljust(80)
    with open(long_path(os.path.join(deep, "frame.fits")), "wb") as fh:
        fh.write((cards + " " * (-len(cards) % 2880)).encode("latin-1") + b"\0" * _span(lines))
    result = scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    assert len(result.changes.new) == 1
    assert (result.frames, result.skipped) == (1, [])


def test_nina_file_gives_every_nina_key_it_carries(tmp_path):
    lines = _corpus("nina.txt")
    got = scan_file(_fits(tmp_path / "n.fits", lines))
    assert isinstance(got, Extracted)
    assert got.program is Program.NINA
    assert got.values["IMAGETYP"] == "LIGHT"
    writer = got.values["SWCREATE"]
    assert isinstance(writer, str)
    assert writer.startswith("N.I.N.A.")
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


def test_a_control_character_in_a_value_does_not_stop_the_scan(conn, tmp_path):
    _fits(tmp_path / "a_bad.fits", [*_NINA_HEAD, "OBJECT  = 'M 31\tAndromeda'"])
    _fits(tmp_path / "b_good.fits", _corpus("nina.txt"))
    result = scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    assert result.changes.new == ["a_bad.fits", "b_good.fits"]
    assert (result.frames, result.skipped) == (2, [])


def test_a_value_with_a_colon_stays_under_its_own_key(tmp_path):
    got = scan_file(_fits(tmp_path / "sh2.fits", [*_NINA_HEAD, "OBJECT  = 'Sh2: 155'"]))
    assert isinstance(got, Extracted)
    assert got.values["OBJECT"] == "Sh2: 155"


def test_a_doubled_quote_in_a_string_is_one_quote(tmp_path):
    """FITS 4.0 sez. 4.2.1.1: '' dentro la stringa e' un apice."""
    got = scan_file(_fits(tmp_path / "q.fits", [*_NINA_HEAD, "OBSERVER= 'O''Brien'"]))
    assert isinstance(got, Extracted)
    assert got.values["OBSERVER"] == "O'Brien"


def test_logicals_are_true_and_false_never_their_letter(tmp_path):
    """FITS 4.0 sez. 4.2.2: T e F logici."""
    lines = [*_NINA_HEAD, "FLIPPED =                    F", "ROTATED =                    T"]
    got = scan_file(_fits(tmp_path / "l.fits", lines))
    assert isinstance(got, Extracted)
    assert (got.values["FLIPPED"], got.values["ROTATED"]) == (False, True)
    assert got.values["FLIPPED"] is False


def test_words_python_reads_as_numbers_but_fits_does_not_stay_text(tmp_path):
    """NaN, inf, trattino basso: non numeri FITS (4.0 sec. 4.2.3-4.2.4). Restano testo, header
    resta JSON valido."""
    lines = [*_NINA_HEAD, "CCD-TEMP= NaN", "SET-TEMP= inf", "AIRMASS = Infinity", "GAIN    = 1_000"]
    got = scan_file(_fits(tmp_path / "w.fits", lines))
    assert isinstance(got, Extracted)
    assert [got.values[k] for k in ("CCD-TEMP", "SET-TEMP", "AIRMASS", "GAIN")] == [
        "NaN",
        "inf",
        "Infinity",
        "1_000",
    ]


def test_real_beyond_a_double_stays_text(tmp_path):
    """1E999: reale FITS, non sta in un double. Resta testo, header resta JSON."""
    lines = [*_NINA_HEAD, "CCD-TEMP= 1E999", "SET-TEMP= -1D999"]
    got = scan_file(_fits(tmp_path / "o.fits", lines))
    assert isinstance(got, Extracted)
    assert [got.values["CCD-TEMP"], got.values["SET-TEMP"]] == ["1E999", "-1D999"]


def test_fits_numbers_keep_their_type(tmp_path):
    lines = [*_NINA_HEAD, "GAIN    = 100", "EXPOSURE= 300.", "FOCRATIO= 1.5D1", "CCD-TEMP= -1E-1"]
    got = scan_file(_fits(tmp_path / "n.fits", lines))
    assert isinstance(got, Extracted)
    assert [got.values[k] for k in ("GAIN", "EXPOSURE", "FOCRATIO", "CCD-TEMP")] == [
        100,
        300.0,
        15.0,
        -0.1,
    ]
    assert isinstance(got.values["EXPOSURE"], float)


def test_a_lower_case_d_exponent_stays_text(tmp_path):
    """FITS: esponente E o D maiuscola. e minuscola si leggeva gia', d no."""
    lines = [*_NINA_HEAD, "FOCRATIO= 1.5d3", "CCD-TEMP= 1e3"]
    got = scan_file(_fits(tmp_path / "d.fits", lines))
    assert isinstance(got, Extracted)
    assert [got.values["FOCRATIO"], got.values["CCD-TEMP"]] == ["1.5d3", 1000.0]


def test_commentary_with_an_equal_sign_is_not_a_key(tmp_path):
    got = scan_file(_fits(tmp_path / "c.fits", [*_NINA_HEAD, "COMMENT = 'x'", "HISTORY = 'y'"]))
    assert isinstance(got, Extracted)
    assert not {"COMMENT", "HISTORY"} & set(got.values)


def test_a_hierarch_key_is_kept_and_reported(tmp_path):
    got = scan_file(_fits(tmp_path / "h.fits", [*_NINA_HEAD, "HIERARCH ESO DET = 5"]))
    assert isinstance(got, Extracted)
    assert got.values["ESO DET"] == 5
    assert "ESO DET" in got.unknown


@pytest.mark.parametrize(
    "card",
    ["        = 5", "OB\x01ECT  = 'x'", "ob ject = 'x'", "HIERARCH  = 5", "HIERARCH E\x7fSO = 5"],
)
def test_a_key_outside_the_fits_grammar_is_not_a_key(card, tmp_path):
    """FITS 4.0 sez. 4.1.2.1: A-Z, 0-9, '-', '_', niente spazi dentro. Archivio vero: 16.136 file,
    nessuna chiave fuori."""
    got = scan_file(_fits(tmp_path / "k.fits", [*_NINA_HEAD, card]))
    assert isinstance(got, Extracted)
    assert set(got.values) == {line[:8].strip() for line in _NINA_HEAD}


def test_accented_letters_written_by_nina_are_kept(tmp_path):
    got = scan_file(_fits(tmp_path / "neb.fits", [*_NINA_HEAD, "OBJECT  = 'Nébuleuse'"]))
    assert isinstance(got, Extracted)
    assert got.values["OBJECT"] == "Nébuleuse"


def test_accented_letters_written_in_utf8_are_read_as_written(tmp_path):
    """ASIAIR su Linux: byte UTF-8. Letti latin-1 erano 'NÃ©buleuse'."""
    utf8_bytes_as_latin1 = "Nébuleuse".encode().decode("latin-1")
    lines = [*_corpus("asiair.txt"), f"OBJECT  = '{utf8_bytes_as_latin1}'"]
    got = scan_file(_fits(tmp_path / "a.fit", lines))
    assert isinstance(got, Extracted)
    assert got.values["OBJECT"] == "Nébuleuse"


_BARE = ["SIMPLE  =                    T", "BITPIX  =                   16"]
_NINA_WRITER = "SWCREATE= 'N.I.N.A. 3.2.0.9001 (x64)'"
_BAD_AXES = [
    ["NAXIS1  =                  -16", "NAXIS2  =                   16"],
    ["NAXIS1  =                 16.5", "NAXIS2  =                   16"],
]


@pytest.mark.parametrize("axes", _BAD_AXES)
def test_axes_that_are_not_counts_make_the_file_broken(tmp_path, axes):
    """FITS 4.0 sez. 4.4.1.1: NAXISn intero non negativo; altro non e' un'immagine."""
    lines = [*_BARE, "NAXIS   =                    2", *axes, _NINA_WRITER]
    path = _fits(tmp_path / "a.fits", lines)
    assert scan_file(path) == Skipped(path, Skip.BROKEN)


def test_reading_a_file_says_nothing_on_the_console(tmp_path):
    """Avvisi di astropy su card storte: mai fuori dalla lettura."""
    lines = [*_BARE, "NAXIS   =                    0", _NINA_WRITER, "BADCARD = 'unterminated",
             "DATE-OBS= 2025-06-29T21:11:33"]  # fmt: skip
    path = _fits(tmp_path / "a.fits", lines)
    path.write_bytes(path.read_bytes() + bytes(2880))  # padding astropy warns about
    with warnings.catch_warnings(record=True) as said:
        warnings.simplefilter("always")
        scan_file(path)
    assert said == []


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


def _compressed(path: Path, dtype: str = "uint16") -> Path:
    """Tile-compressed N.I.N.A. file as cfitsio writes it: empty primary, keys in page 2."""
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
    data = np.zeros((8, 8), dtype=dtype)
    fits.HDUList([fits.PrimaryHDU(), fits.CompImageHDU(data, header)]).writeto(path)
    return path


def test_a_compressed_floating_point_file_is_rewritten(tmp_path):
    """Compresso: il tipo dei pixel del frame e' ZBITPIX (FITS 4.0 sez. 10), non BITPIX."""
    path = _compressed(tmp_path / "cal.fits.fz", "float32")
    assert scan_file(path) == Skipped(path, Skip.REWRITTEN)


@pytest.mark.parametrize(
    ("lines", "key", "value"),
    [
        (["MYGAIN  = 12&", "CONTINUE  'z'"], "MYGAIN", "12&"),  # unquoted value: no long string
        (["OBSERVER= 'M&'", "CONTINUE  z"], "OBSERVER", "M&"),  # unquoted CONTINUE: not a part
        (["OBSERVER= 'M&'", "CONTINUE  '42'"], "OBSERVER", "M42"),  # the convention itself
        (["OBSERVER= 'M&'", "CONTINUE  z", "CONTINUE  '42'"], "OBSERVER", "M&"),  # chain ended
    ],
)
def test_continue_joins_quoted_strings_only(tmp_path, lines, key, value):
    """FITS 4.0 sez. 4.2.1.2: stringhe lunghe solo tra apici."""
    got = scan_file(_fits(tmp_path / "a.fits", [*_corpus("nina.txt"), *lines]))
    assert isinstance(got, Extracted)
    assert got.values[key] == value


def test_a_long_continue_chain_is_read_in_linear_time(tmp_path):
    """3.500 CONTINUE (quasi il tetto di 100 blocchi): ogni pezzo una volta, valore esatto."""
    piece = "abcdefghij" * 6
    links = [f"CONTINUE  '{piece}&'"] * 3_500
    lines = [*_corpus("nina.txt"), "NOTE    = 'start&'", *links, "CONTINUE  'end'"]
    path = _fits(tmp_path / "a.fits", lines)
    started = time.perf_counter()
    got = scan_file(path)
    assert time.perf_counter() - started < 2  # linear: well under 1 s
    assert isinstance(got, Extracted)
    assert got.values["NOTE"] == "start" + piece * 3_500 + "end"


def test_continue_is_never_a_key(tmp_path):
    got = scan_file(_fits(tmp_path / "a.fits", [*_corpus("nina.txt"), "CONTINUE= 'x'"]))
    assert isinstance(got, Extracted)
    assert "CONTINUE" not in got.values


def test_a_compressed_frame_with_a_negative_axis_is_broken(tmp_path):
    """Compresso: dimensioni del frame in ZNAXISn (FITS 4.0 sez. 10), stessa regola."""
    path = _compressed(tmp_path / "light.fits.fz")
    raw = path.read_bytes()
    good = b"ZNAXIS1 =                    8"
    assert good in raw
    path.write_bytes(raw.replace(good, b"ZNAXIS1 =                   -8", 1))
    assert scan_file(path) == Skipped(path, Skip.BROKEN)


@pytest.mark.parametrize("cut", ["no_end", "short"])
def test_a_compressed_page_without_its_end_is_broken(tmp_path, cut):
    """Pagina dell'immagine senza END (o copia tagliata li'): rotto come la primaria, non
    di altro programma."""
    path = _compressed(tmp_path / "light.fits.fz")
    raw = path.read_bytes()
    end = b"END" + b" " * 77
    page = raw.index(end) + len(end)
    page += -page % 2880
    if cut == "no_end":
        path.write_bytes(raw[:page] + raw[page:].replace(end, b" " * 80, 1))
    else:
        path.write_bytes(raw[: page + 2880])
    assert scan_file(path) == Skipped(path, Skip.BROKEN)


def test_an_empty_primary_alone_is_not_supported(tmp_path):
    """Sola primaria vuota, nessuna pagina dopo: file di nessun programma, non rotto."""
    path = _fits(tmp_path / "empty.fits", ["SIMPLE  =                    T", "BITPIX  =  8",
                                           "NAXIS   =                    0"])  # fmt: skip
    assert scan_file(path) == Skipped(path, Skip.NOT_SUPPORTED)


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
        page: Any = hdul[1]  # astropy stubs type int index as slice: HDUList
        page.header["ZOOM"] = 2
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


def test_a_stack_count_alone_is_rewritten(tmp_path):
    """STACKCNT senza PROGRAM: lo scrive chi impila, mai N.I.N.A. ne' ASIAIR."""
    lines = [*_corpus("nina.txt"), "STACKCNT= 30"]
    got = scan_file(_fits(tmp_path / "stack.fits", lines))
    assert got == Skipped(tmp_path / "stack.fits", Skip.REWRITTEN)


def test_a_rewrite_that_dropped_the_capture_program_is_rewritten(tmp_path):
    lines = [line for line in _corpus("nina.txt") if not line.startswith("SWCREATE")] + [
        "PROGRAM = 'Editor 1.9.3'"
    ]
    got = scan_file(_fits(tmp_path / "saved.fits", lines))
    assert got == Skipped(tmp_path / "saved.fits", Skip.REWRITTEN)


@pytest.mark.parametrize("bitpix", [-32, -64])
def test_a_floating_point_file_is_rewritten_even_with_the_capture_header(tmp_path, bitpix):
    """N.I.N.A. salva interi (BaseImageData.SaveFits), ASIAIR 16 bit (archivio: tutti i grezzi):
    a virgola mobile e' elaborato altrove. Prima: stessa posa del grezzo."""
    lines = [line.replace("16", str(bitpix)) if line.startswith("BITPIX") else line
             for line in _NINA_HEAD]  # fmt: skip
    path = _fits(tmp_path / "cal.fits", lines)
    assert scan_file(path) == Skipped(path, Skip.REWRITTEN)


@pytest.mark.parametrize(("blocks", "broken"), [(100, False), (101, True)])
def test_a_header_past_100_blocks_is_broken(tmp_path, blocks, broken):
    """Tetto deciso col proprietario: 100 blocchi (288 KB); i file veri ne usano 2-4.
    Prima 1000: un header ostile pesava 2,9 MB nel database."""
    filler = ["HISTORY x"] * (blocks * 36 - 1 - len(_NINA_HEAD))
    path = _fits(tmp_path / "long.fits", [*_NINA_HEAD, *filler])
    assert (scan_file(path) == Skipped(path, Skip.BROKEN)) is broken


def test_a_header_without_end_is_broken(tmp_path):
    got = scan_file(_fits(tmp_path / "t.fits", _corpus("nina.txt"), end=False))
    assert got == Skipped(tmp_path / "t.fits", Skip.BROKEN)


def test_a_file_that_cannot_be_opened_is_unreadable(tmp_path):
    missing = tmp_path / "gone.fits"
    assert scan_file(missing) == Skipped(missing, Skip.UNREADABLE)


def test_a_folder_that_cannot_be_opened_is_reported(conn, tmp_path):
    gone = tmp_path / "unplugged"
    gone.mkdir()
    root_id = add_root(conn, gone, NOW)
    gone.rmdir()
    assert not scan_root(conn, root_id, NOW).changes.reachable
