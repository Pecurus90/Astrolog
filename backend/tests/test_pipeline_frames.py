"""Mattone 3 della pipeline nuova, seconda meta': il frame e i suoi file. Un frame per impronta;
due file con la stessa impronta sono un doppione, non due pose; un file spostato resta lo stesso
frame."""

import shutil
from pathlib import Path

import pytest

from astrolog.pipeline.changes import add_root
from astrolog.pipeline.frames import scan_root

NOW = "2026-10-22T20:00:00+00:00"
LATER = "2026-10-23T20:00:00+00:00"
CORPUS = Path(__file__).with_name("header")


def _nina(path: Path, seed: int) -> Path:
    """A small N.I.N.A. light with its own pixels: `seed` makes it a different frame."""
    lines = [
        "SIMPLE  =                    T",
        "BITPIX  =                   16",
        "NAXIS   =                    2",
        "NAXIS1  =                   16",
        "NAXIS2  =                   16",
        "IMAGETYP= 'LIGHT'",
        "SWCREATE= 'N.I.N.A. 3.2.0.9001 (x64)'",
        "END",
    ]
    head = "".join(line.ljust(80) for line in lines)
    head += " " * (-len(head) % 2880)
    data = bytes((seed + i) % 256 for i in range(512))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(head.encode("ascii") + data + b"\0" * (2880 - 512))
    return path


def _files(conn):
    return {
        row["rel_path"]: row["frame_id"]
        for row in conn.execute(
            "SELECT rel_path, frame_id FROM pipeline_files WHERE state = 'present'"
        )
    }


def test_each_file_read_points_to_its_frame(conn, tmp_path):
    _nina(tmp_path / "a.fits", 1)
    _nina(tmp_path / "b.fits", 2)
    result = scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    files = _files(conn)
    assert files["a.fits"] != files["b.fits"]
    assert result.frames == 2 and result.duplicates == {}


def test_a_copy_in_another_folder_is_one_frame(conn, tmp_path):
    """La stessa posa in due cartelle: un frame, con i suoi due file, e la ricevuta lo dice."""
    _nina(tmp_path / "2024-11-03" / "m33.fits", 7)
    shutil.copy(tmp_path / "2024-11-03" / "m33.fits", tmp_path / "2024-11-04_m33.fits")
    result = scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    files = _files(conn)
    assert files["2024-11-03/m33.fits"] == files["2024-11-04_m33.fits"]
    assert result.frames == 1
    assert list(result.duplicates.values()) == [["2024-11-03/m33.fits", "2024-11-04_m33.fits"]]


def test_a_moved_file_is_the_same_frame(conn, tmp_path):
    _nina(tmp_path / "da_ordinare" / "posa.fits", 3)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    frame = _files(conn)["da_ordinare/posa.fits"]
    (tmp_path / "M42").mkdir()
    (tmp_path / "da_ordinare" / "posa.fits").rename(tmp_path / "M42" / "posa.fits")
    result = scan_root(conn, root, LATER)
    assert result.moved == [("da_ordinare/posa.fits", "M42/posa.fits")]
    assert _files(conn) == {"M42/posa.fits": frame}


def test_a_move_plus_a_copy_is_one_move_and_one_duplicate(conn, tmp_path):
    _nina(tmp_path / "a.fits", 4)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    shutil.copy(tmp_path / "a.fits", tmp_path / "c.fits")
    (tmp_path / "a.fits").rename(tmp_path / "b.fits")
    result = scan_root(conn, root, LATER)
    assert result.moved == [("a.fits", "b.fits")]
    assert list(result.duplicates.values()) == [["b.fits", "c.fits"]]


def test_a_file_not_read_has_no_frame(conn, tmp_path):
    (tmp_path / "altro.fits").write_bytes(b"SIMPLE  =                    T".ljust(2880))
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    assert _files(conn) == {"altro.fits": None}


def test_an_interrupted_scan_reads_its_files_next_time(conn, tmp_path, monkeypatch):
    """Una scansione fermata a meta' non salva nulla: la prossima rilegge, nessuna posa persa."""
    _nina(tmp_path / "a.fits", 1)
    _nina(tmp_path / "b.fits", 2)
    root = add_root(conn, tmp_path, NOW)
    import astrolog.pipeline.frames as frames

    real = frames.scan_file
    calls: list[Path] = []

    def stops_at_second(path):
        calls.append(path)
        if len(calls) == 2:
            raise KeyboardInterrupt
        return real(path)

    monkeypatch.setattr(frames, "scan_file", stops_at_second)
    with pytest.raises(KeyboardInterrupt):
        scan_root(conn, root, NOW)
    monkeypatch.setattr(frames, "scan_file", real)
    assert scan_root(conn, root, LATER).frames == 2


def test_an_unchanged_archive_is_not_read_again(conn, tmp_path, monkeypatch):
    _nina(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    import astrolog.pipeline.frames as frames

    def forbidden(_path):
        raise AssertionError("a file was opened")

    monkeypatch.setattr(frames, "scan_file", forbidden)
    result = scan_root(conn, root, LATER)
    assert result.frames == 1
