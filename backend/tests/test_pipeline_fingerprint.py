"""Impronta frame, portata da `fits/header_read.py`: inizio e lunghezza pixel, impronta uguale
alla vecchia. In piu': file incompleto (la vecchia lo prende come frame)."""

import numpy as np
import pytest
from astropy.io import fits

from astrolog.fits.header_read import frame_fingerprint, read_frame
from astrolog.pipeline import fingerprint
from astrolog.pipeline.fingerprint import data_block, frame_identity
from astrolog.pipeline.scanner import Extracted, Skip, Skipped, read_cards, scan_file

pytestmark = pytest.mark.filterwarnings("ignore::astropy.utils.exceptions.AstropyUserWarning")


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


def _image(path, shape, dtype, cards=0, **keys):
    header = fits.Header()
    header["SWCREATE"] = "N.I.N.A. 3.2.0.9001 (x64)"
    for key, value in keys.items():
        header[key] = value
    for i in range(cards):  # header lungo, oltre il primo blocco da 2880 byte
        header[f"NOTA{i:04d}"] = "x" * 40
    data = np.arange(int(np.prod(shape)), dtype=dtype).reshape(shape)
    fits.PrimaryHDU(data=data, header=header).writeto(path)
    return path


def _compressed(path, shape=(40, 60)):
    header = fits.Header()
    header["SWCREATE"] = "N.I.N.A. 3.2.0.9001 (x64)"
    data = (np.arange(int(np.prod(shape))) % 997).astype(np.uint16).reshape(shape)
    fits.HDUList([fits.PrimaryHDU(), fits.CompImageHDU(data, header)]).writeto(path)
    return path


def _bench(tmp_path):
    """Forme che N.I.N.A. e ASIAIR scrivono: pagina con pixel, o compressa."""
    return {
        "int16": _image(tmp_path / "a.fits", (3, 4), np.int16),
        "uint16_large": _image(tmp_path / "b.fits", (300, 300), np.uint16),
        "float32": _image(tmp_path / "c.fits", (8, 8), np.float32),
        "odd": _image(tmp_path / "d.fits", (7, 13), np.uint8),
        "long_header": _image(tmp_path / "e.fits", (3, 4), np.int16, cards=80),
        "short_keys": _image(tmp_path / "f.fits", (3, 4), np.int16, RA=10.5, ENDTIME="21:00"),
        "compressed": _compressed(tmp_path / "g.fits.fz"),
    }


def test_the_data_block_is_the_one_astropy_finds(tmp_path):
    for name, path in _bench(tmp_path).items():
        assert data_block(path) == _astropy(str(path)), name


def test_a_plain_file_does_not_need_astropy(tmp_path, monkeypatch):
    """Caso comune letto dai blocchi: senza strada veloce, scansione paga astropy su ogni file
    nuovo."""
    bench = _bench(tmp_path)
    expected = {n: _astropy(str(p)) for n, p in bench.items() if n != "compressed"}

    def forbidden(*_args, **_kwargs):
        raise AssertionError("fits.open chiamato su un file semplice")

    monkeypatch.setattr(fingerprint.fits, "open", forbidden)
    for name, block in expected.items():
        assert data_block(bench[name]) == block, name


def test_the_identity_is_today_s_fingerprint(tmp_path):
    """Porto fedele: su ogni forma, impronta nuova = quella del codice di oggi."""
    for name, path in _bench(tmp_path).items():
        header, block = read_frame(str(path))
        cards = read_cards(path)
        assert cards is not None, name
        assert frame_identity(path, cards).fingerprint == frame_fingerprint(
            str(path), header, block
        ), name


def test_two_shapes_with_the_same_bytes_are_two_frames(tmp_path):
    """Dimensioni nell'impronta: 40x60 e 60x40 tutti a zero hanno stessi byte."""
    seen = set()
    for rows, cols in ((40, 60), (60, 40)):
        path = tmp_path / f"z{rows}x{cols}.fits"
        header = fits.Header()
        header["SWCREATE"] = "N.I.N.A. 3.2.0.9001 (x64)"
        fits.PrimaryHDU(data=np.zeros((rows, cols), np.int16), header=header).writeto(path)
        seen.add(frame_identity(path, read_cards(path)).fingerprint)
    assert len(seen) == 2


def test_two_exposures_with_the_same_pixels_are_two_frames(tmp_path):
    """Cappuccio chiuso o centro saturo: pixel uguali, inizio diverso, due pose. La copia, stesso
    inizio, resta una posa sola."""
    seen = []
    for name, start in (("a", "2025-06-29T21:11:33.412"), ("b", "2025-06-29T21:16:40.105"),
                        ("copy", "2025-06-29T21:11:33.412")):  # fmt: skip
        path = _image(tmp_path / f"{name}.fits", (300, 300), np.uint16, **{"DATE-OBS": start})
        seen.append(frame_identity(path, read_cards(path)).fingerprint)
    assert seen[0] != seen[1]
    assert seen[0] == seen[2]


def test_a_file_without_pixels_is_told_apart_by_its_cards(tmp_path):
    """Senza blocco dati, impronta di oggi prende le schede: due header diversi, due frame."""
    seen = set()
    for name in ("M31", "M42"):
        path = tmp_path / f"{name}.fits"
        header = fits.Header()
        header["SWCREATE"] = "N.I.N.A. 3.2.0.9001 (x64)"
        header["OBJECT"] = name
        fits.PrimaryHDU(header=header).writeto(path)
        today, block = read_frame(str(path))
        got = frame_identity(path, read_cards(path)).fingerprint
        assert got == frame_fingerprint(str(path), today, block), name
        seen.add(got)
    assert len(seen) == 2


def test_a_file_shorter_than_its_header_says_is_incomplete(tmp_path):
    """Copia interrotta: header si', pixel no. Saltato; finita la copia, file cambia dimensione e
    scansione dopo lo rilegge."""
    path = _image(tmp_path / "copia.fits", (300, 300), np.uint16)
    path.write_bytes(path.read_bytes()[:10000])
    assert scan_file(path) == Skipped(path, Skip.INCOMPLETE)


def test_a_whole_file_carries_its_fingerprint(tmp_path):
    path = _image(tmp_path / "intera.fits", (300, 300), np.uint16)
    got = scan_file(path)
    assert isinstance(got, Extracted)
    header, block = read_frame(str(path))
    assert got.fingerprint == frame_fingerprint(str(path), header, block)


def test_a_compressed_file_is_complete_and_has_its_fingerprint(tmp_path):
    path = _compressed(tmp_path / "light.fits.fz", (100, 100))
    got = scan_file(path)
    assert isinstance(got, Extracted)
    header, block = read_frame(str(path))
    assert got.fingerprint == frame_fingerprint(str(path), header, block)
