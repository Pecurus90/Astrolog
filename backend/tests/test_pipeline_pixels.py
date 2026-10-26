"""Pixels of a frame for measure: uncompressed FITS read by us (no astropy in the new pipeline),
BZERO and BSCALE applied, the saturation ceiling with them. Files written by astropy here."""

from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits

from astrolog.pipeline.pixels import Pixels, Unmeasurable, Why, read_pixels


def _write(path: Path, data: np.ndarray, **cards: object) -> Path:
    header = fits.Header()
    for key, value in cards.items():
        header[key] = value
    fits.PrimaryHDU(data=data, header=header).writeto(path)
    return path


def _read(path: Path) -> Pixels:
    read = read_pixels(path)
    assert isinstance(read, Pixels), read
    return read


def test_unsigned_16_bit_frames_come_back_with_their_bzero(tmp_path: Path) -> None:
    data = np.array([[0, 1, 32767, 32768, 65535] * 5] * 25, dtype=np.uint16)
    read = _read(_write(tmp_path / "a.fits", data))
    assert read.data.dtype == np.float32
    assert np.array_equal(read.data, data.astype(np.float32))
    assert read.saturation == 65535


def test_the_saturation_is_datamax_when_written(tmp_path: Path) -> None:
    data = np.full((25, 25), 100, dtype=np.uint16)
    assert _read(_write(tmp_path / "a.fits", data, DATAMAX=61212)).saturation == 61212


def test_eight_and_thirty_two_bit_frames_and_bscale(tmp_path: Path) -> None:
    small = np.arange(625, dtype=np.uint8).reshape(25, 25)
    read = _read(_write(tmp_path / "b.fits", small))
    assert np.array_equal(read.data, small.astype(np.float32))
    assert read.saturation == 255
    wide = np.arange(625, dtype=np.int32).reshape(25, 25)
    path = _write(tmp_path / "c.fits", wide)
    fits.setval(path, "BSCALE", value=2.0)  # same integers, written as half of what they mean
    assert np.array_equal(_read(path).data, wide.astype(np.float32) * 2)


def test_rows_and_columns_keep_their_place(tmp_path: Path) -> None:
    data = np.zeros((30, 40), dtype=np.uint16)
    data[2, 7] = 500  # NAXIS2 = 30 rows, NAXIS1 = 40 columns
    read = _read(_write(tmp_path / "a.fits", data))
    assert read.data.shape == (30, 40)
    assert read.data[2, 7] == 500


@pytest.mark.parametrize(
    ("shape", "why"),
    [((3, 25, 25), Why.NOT_SUPPORTED), ((19, 400), Why.NOT_SUPPORTED)],
)
def test_cubes_and_slivers_are_not_frames_to_measure(
    tmp_path: Path, shape: tuple[int, ...], why: Why
) -> None:
    path = _write(tmp_path / "a.fits", np.zeros(shape, dtype=np.uint16))
    assert read_pixels(path) == Unmeasurable(why)


def test_a_cut_file_a_missing_one_and_a_compressed_one_say_why(tmp_path: Path) -> None:
    path = _write(tmp_path / "a.fits", np.zeros((100, 100), dtype=np.uint16))
    path.write_bytes(path.read_bytes()[:5000])
    assert read_pixels(path) == Unmeasurable(Why.UNREADABLE)
    assert read_pixels(tmp_path / "gone.fits") == Unmeasurable(Why.UNREADABLE)
    fz = _write(tmp_path / "b.fits.fz", np.zeros((100, 100), dtype=np.uint16))
    assert read_pixels(fz) == Unmeasurable(Why.FZ_UNSUPPORTED)


def test_a_file_that_is_not_fits_is_unreadable(tmp_path: Path) -> None:
    path = tmp_path / "a.fits"
    path.write_bytes(b"not a fits file" * 400)
    assert read_pixels(path) == Unmeasurable(Why.UNREADABLE)
