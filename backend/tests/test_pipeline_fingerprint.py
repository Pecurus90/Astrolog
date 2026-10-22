"""Impronta della posa: dall'header (camera, inizio, dimensioni, posa), pixel solo come ripiego.
Una sola apertura per file, niente astropy; ripiego uguale alla vecchia."""

import builtins
import io
import os

import numpy as np
import pytest
from astropy.io import fits

from astrolog.fits.header_read import frame_fingerprint, read_frame
from astrolog.pipeline.fingerprint import BLOCK, Header, data_length, frame_identity
from astrolog.pipeline.scanner import Extracted, Skip, Skipped, read_header, scan_file

pytestmark = pytest.mark.filterwarnings("ignore::astropy.utils.exceptions.AstropyUserWarning")

_SHOT = {"INSTRUME": "ATR2600M", "DATE-OBS": "2025-06-29T21:11:33.412", "EXPTIME": 300.0}


def _astropy(path):
    """Oracolo: cio' che dice astropy leggendo tutto il file."""
    with fits.open(
        path, output_verify="silently", ignore_missing_end=True, memmap=False, lazy_load_hdus=False
    ) as hdul:
        for i, hdu in enumerate(hdul):
            info = hdul.fileinfo(i)
            if info and (isinstance(hdu, fits.CompImageHDU) or hdu.header.get("NAXIS", 0)):
                return info["datLoc"], info["datSpan"]
    return 0, 0


def _image(path, shape, dtype, cards=0, keys=None, data=None):
    header = fits.Header()
    header["SWCREATE"] = "N.I.N.A. 3.2.0.9001 (x64)"
    for key, value in (keys or {}).items():
        header[key] = value
    for i in range(cards):  # long header, past first 2880-byte block
        header[f"NOTA{i:04d}"] = "x" * 40
    if data is None:
        data = np.arange(int(np.prod(shape)), dtype=dtype).reshape(shape)
    fits.PrimaryHDU(data=data, header=header).writeto(path)
    return path


def _compressed(path, shape=(40, 60), keys=None, data=None):
    header = fits.Header()
    header["SWCREATE"] = "N.I.N.A. 3.2.0.9001 (x64)"
    for key, value in (keys or {}).items():
        header[key] = value
    if data is None:
        data = (np.arange(int(np.prod(shape))) % 997).astype(np.uint16).reshape(shape)
    fits.HDUList([fits.PrimaryHDU(), fits.CompImageHDU(data, header)]).writeto(path)
    return path


_FLOAT = ("float32", "float64")  # data layout only: a capture is never floating (rewritten)


def _bench(tmp_path):
    """Forme FITS di una pagina con pixel o compressa; a virgola mobile solo per la geometria."""
    return {
        "int16": _image(tmp_path / "a.fits", (3, 4), np.int16),
        "uint16_large": _image(tmp_path / "b.fits", (300, 300), np.uint16),
        "float32": _image(tmp_path / "c.fits", (8, 8), np.float32),
        "float64": _image(tmp_path / "h.fits", (5, 9), np.float64),
        "odd": _image(tmp_path / "d.fits", (7, 13), np.uint8),
        "long_header": _image(tmp_path / "e.fits", (3, 4), np.int16, cards=80),
        "short_keys": _image(tmp_path / "f.fits", (3, 4), np.int16, keys={"ENDTIME": "21:00"}),
        "compressed": _compressed(tmp_path / "g.fits.fz"),
        "compressed_odd": _compressed(tmp_path / "i.fits.fz", (37, 101)),
    }


def _fingerprint(path, size=None):
    got = scan_file(path, size)
    assert isinstance(got, Extracted), got
    return got.fingerprint


def test_the_data_block_is_the_one_astropy_finds(tmp_path):
    """FITS 4.0: |BITPIX|/8 * GCOUNT * (PCOUNT + prod NAXISn), a blocchi da 2880."""
    for name, path in _bench(tmp_path).items():
        with open(path, "rb") as fh:
            got = read_header(fh)
        assert got is not None, name
        assert (got.data_start, got.data_length) == _astropy(str(path)), name


def test_no_file_needs_astropy_and_each_is_opened_once(tmp_path, monkeypatch):
    """NAS: ogni apertura e' un giro di rete. Una per file, compressi compresi."""
    bench = _bench(tmp_path)
    opened: list[str] = []
    real_open = builtins.open

    def counted(file, *args, **kwargs):
        opened.append(os.fspath(file))
        return real_open(file, *args, **kwargs)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("astropy or getsize used to read a frame")

    monkeypatch.setattr(fits, "open", forbidden)
    monkeypatch.setattr(os.path, "getsize", forbidden)
    monkeypatch.setattr(builtins, "open", counted)
    for name, path in bench.items():
        if name in _FLOAT:
            continue
        opened.clear()
        assert isinstance(scan_file(path), Extracted), name
        assert len(opened) == 1, name


def test_a_plain_file_and_its_fpack_copy_are_one_frame(tmp_path):
    """Stessa posa, compressa con fpack: le risposte legate alla posa restano."""
    data = (np.arange(64 * 48) % 4093).astype(np.uint16).reshape(48, 64)
    plain = _image(tmp_path / "a.fits", (48, 64), np.uint16, keys=_SHOT, data=data)
    packed = _compressed(tmp_path / "a.fits.fz", keys=_SHOT, data=data)
    assert _fingerprint(plain) == _fingerprint(packed)


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ({"DATE-OBS": "2025-06-29T21:11:33.4"}, {"DATE-OBS": "2025-06-29T21:11:33.400"}),
        ({"EXPTIME": 300}, {"EXPTIME": 300.0}),
        ({"INSTRUME": "ATR2600M"}, {"INSTRUME": " ATR2600M "}),
    ],
)
def test_the_same_shot_written_two_ways_is_one_frame(tmp_path, first, second):
    a = _image(tmp_path / "a.fits", (3, 4), np.int16, keys={**_SHOT, **first})
    b = _image(tmp_path / "b.fits", (3, 4), np.int16, keys={**_SHOT, **second}, data=np.zeros(
        (3, 4), np.int16))  # fmt: skip
    assert _fingerprint(a) == _fingerprint(b)


@pytest.mark.parametrize(
    "other",
    [
        {"DATE-OBS": "2025-06-29T21:11:33.413"},
        {"EXPTIME": 300.5},
        {"INSTRUME": "Poseidon-C PRO"},
    ],
)
def test_another_shot_is_another_frame_even_with_the_same_pixels(tmp_path, other):
    """Cappuccio chiuso o centro saturo: pixel uguali, posa diversa."""
    a = _image(tmp_path / "a.fits", (3, 4), np.int16, keys=_SHOT)
    b = _image(tmp_path / "b.fits", (3, 4), np.int16, keys={**_SHOT, **other})
    assert _fingerprint(a) != _fingerprint(b)


def test_shots_in_the_same_whole_second_are_told_apart_by_their_pixels(tmp_path):
    """Inizio senza frazione: bias e flat brevi cadono nello stesso secondo. Prima: una posa."""
    keys = {**_SHOT, "DATE-OBS": "2025-06-29T21:11:33", "EXPTIME": 0.001}
    a = _image(tmp_path / "a.fits", (3, 4), np.int16, keys=keys)
    b = _image(tmp_path / "b.fits", (3, 4), np.int16, keys=keys, data=np.zeros((3, 4), np.int16))
    c = _image(tmp_path / "c.fits", (3, 4), np.int16, keys=keys)  # copy of a
    assert _fingerprint(a) != _fingerprint(b)
    assert _fingerprint(a) == _fingerprint(c)


def test_without_a_start_the_pixel_fallback_is_today_s_fingerprint(tmp_path):
    """Ripiego (manca l'inizio): impronta = quella del codice vecchio, su ogni forma."""
    for name, path in _bench(tmp_path).items():
        if name in _FLOAT:
            continue
        header, block = read_frame(str(path))
        assert _fingerprint(path) == frame_fingerprint(str(path), header, block), name


def test_two_shapes_with_the_same_bytes_are_two_frames(tmp_path):
    """Dimensioni nell'impronta: 40x60 e 60x40 tutti a zero hanno stessi byte."""
    seen = set()
    for rows, cols in ((40, 60), (60, 40)):
        zeros = np.zeros((rows, cols), np.int16)
        seen.add(_fingerprint(_image(tmp_path / f"z{rows}x{cols}.fits", (rows, cols), np.int16,
                                     data=zeros)))  # fmt: skip
    assert len(seen) == 2


def test_a_file_without_pixels_is_told_apart_by_its_header(tmp_path):
    seen = set()
    for name in ("M31", "M42"):
        path = tmp_path / f"{name}.fits"
        header = fits.Header()
        header["SWCREATE"] = "N.I.N.A. 3.2.0.9001 (x64)"
        header["OBJECT"] = name
        fits.PrimaryHDU(header=header).writeto(path)
        seen.add(_fingerprint(path))
    assert len(seen) == 2


@pytest.mark.parametrize(
    ("bitpix", "width"), [(8, 1), (16, 2), (32, 4), (64, 8), (-32, 4), (-64, 8)]
)
def test_each_bitpix_has_its_bytes_per_pixel(bitpix, width):
    """FITS 4.0 tab. 8: |BITPIX|/8 byte per pixel. Riga di 2880 pixel: blocchi interi."""
    assert data_length({"BITPIX": bitpix, "NAXIS": 2, "NAXIS1": BLOCK, "NAXIS2": 1}) == (
        width * BLOCK
    )


@pytest.mark.parametrize("missing", ["INSTRUME", "EXPTIME", "NAXIS1"])
def test_a_shot_missing_one_part_falls_back_to_its_pixels(missing):
    """Senza camera, durata o larghezza l'inizio non basta: stesso inizio, pixel diversi, due
    pose."""
    shot = {**_SHOT, "BITPIX": 16, "NAXIS": 2, "NAXIS1": BLOCK // 2, "NAXIS2": 1}
    header = Header({k: v for k, v in shot.items() if k != missing}, 0, BLOCK)
    one = frame_identity(header, BLOCK, io.BytesIO(b"\1" * BLOCK))
    two = frame_identity(header, BLOCK, io.BytesIO(bytes(BLOCK)))
    assert one.fingerprint != two.fingerprint


def test_more_axes_than_fits_allows_is_no_data_length():
    """FITS 4.0 sez. 4.4.1.1: NAXIS 0..999. Oltre: niente, e mai una lista enorme."""
    axes = {f"NAXIS{n}": 1 for n in range(1, 1001)}
    assert data_length({"BITPIX": 16, "NAXIS": 1000, **axes}) is None
    assert data_length({"BITPIX": 16, "NAXIS": 10**12}) is None


def test_an_absurd_data_length_makes_the_file_broken_not_the_scan_fail(tmp_path):
    """Assi enormi (2**40 x 2**40): lunghezza oltre ogni file, mai un errore che ferma tutto."""
    lines = [
        "SIMPLE  =                    T", "BITPIX  =                   16",
        "NAXIS   =                    2", f"NAXIS1  = {2**40:>20}", f"NAXIS2  = {2**40:>20}",
        "SWCREATE= 'N.I.N.A. 3.2.0.9001 (x64)'", "END",
    ]  # fmt: skip
    head = "".join(line.ljust(80) for line in lines)
    path = tmp_path / "huge.fits"
    path.write_bytes((head + " " * (-len(head) % 2880)).encode("ascii"))
    assert scan_file(path) == Skipped(path, Skip.BROKEN)


def test_a_file_shorter_than_its_header_says_is_incomplete(tmp_path):
    """Copia interrotta: header si', pixel no. Saltato; finita la copia, file cambia dimensione e
    scansione dopo lo rilegge."""
    path = _image(tmp_path / "copia.fits", (300, 300), np.uint16)
    path.write_bytes(path.read_bytes()[:10000])
    assert scan_file(path) == Skipped(path, Skip.INCOMPLETE)


def test_the_size_seen_by_the_walk_decides_completeness(tmp_path):
    """Dimensione dal walk, nessun accesso in piu': piu' corta dell'annunciata, incompleto."""
    path = _image(tmp_path / "a.fits", (300, 300), np.uint16, keys=_SHOT)
    whole = path.stat().st_size
    assert isinstance(scan_file(path, whole), Extracted)
    assert scan_file(path, whole - 1) == Skipped(path, Skip.INCOMPLETE)
