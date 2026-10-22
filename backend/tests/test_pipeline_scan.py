"""Mattoni 3 e 3b: frame per impronta (stessa impronta = doppione, spostato = stesso frame),
header di ogni file letto accanto al frame."""

import json
import os
import shutil
import sqlite3
from collections.abc import Callable
from pathlib import Path

import pytest

from astrolog.db.connect import connect
from astrolog.pipeline import scan
from astrolog.pipeline.changes import add_root
from astrolog.pipeline.scan import ScanRunningError, scan_root
from astrolog.pipeline.scanner import Extracted, Skip, Skipped
from conftest import LATER, NOW, nina_light

ScanFile = Callable[[Path, int | None], Extracted | Skipped]


def _stopping_scan(real: ScanFile, at: int = 1) -> ScanFile:
    """Fake `scan_file`: stops scan with KeyboardInterrupt at call number `at`."""
    calls: list[Path] = []

    def stops(path: Path, size: int | None = None) -> Extracted | Skipped:
        calls.append(path)
        if len(calls) == at:
            raise KeyboardInterrupt
        return real(path, size)

    return stops


def _files(conn):
    return {
        row["rel_path"]: row["frame_id"]
        for row in conn.execute(
            "SELECT rel_path, frame_id FROM pipeline_files WHERE state = 'present'"
        )
    }


def test_each_file_read_points_to_its_frame(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 1)
    nina_light(tmp_path / "b.fits", 2)
    result = scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    files = _files(conn)
    assert files["a.fits"] != files["b.fits"]
    assert result.frames == 2 and result.duplicates == {}


def test_a_copy_in_another_folder_is_one_frame(conn, tmp_path):
    """Stessa posa in due cartelle: un frame, due file, e la ricevuta lo dice."""
    nina_light(tmp_path / "2024-11-03" / "m33.fits", 7)
    shutil.copy(tmp_path / "2024-11-03" / "m33.fits", tmp_path / "2024-11-04_m33.fits")
    result = scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    files = _files(conn)
    assert files["2024-11-03/m33.fits"] == files["2024-11-04_m33.fits"]
    assert result.frames == 1
    assert list(result.duplicates.values()) == [["2024-11-03/m33.fits", "2024-11-04_m33.fits"]]


def test_a_moved_file_is_the_same_frame(conn, tmp_path):
    nina_light(tmp_path / "da_ordinare" / "posa.fits", 3)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    frame = _files(conn)["da_ordinare/posa.fits"]
    (tmp_path / "M42").mkdir()
    (tmp_path / "da_ordinare" / "posa.fits").rename(tmp_path / "M42" / "posa.fits")
    result = scan_root(conn, root, LATER)
    assert result.moved == [("da_ordinare/posa.fits", "M42/posa.fits")]
    assert _files(conn) == {"M42/posa.fits": frame}


def test_a_folder_renamed_while_its_files_are_read_is_still_a_move(conn, tmp_path, monkeypatch):
    """Sparito fra elenco e lettura: non illeggibile, altrove. Prima: perdeva il frame."""
    path = nina_light(tmp_path / "night" / "a.fits", 3)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    _touch_later(path)
    real = scan.scan_file

    def renamed_first(p, size=None):
        if (tmp_path / "night").exists():
            (tmp_path / "night").rename(tmp_path / "night2")
        return real(p, size)

    monkeypatch.setattr(scan, "scan_file", renamed_first)
    assert scan_root(conn, root, LATER).changes.unlooked == ["night/a.fits"]  # said
    monkeypatch.setattr(scan, "scan_file", real)
    later = scan_root(conn, root, "2026-10-24T20:00:00+00:00")
    assert later.moved == [("night/a.fits", "night2/a.fits")]


@pytest.mark.skipif(os.name != "nt", reason="Win32 strips a trailing dot: Windows only")
def test_a_folder_ending_with_a_dot_is_read_as_itself(conn, tmp_path):
    """'night.' fatta da Mac o Linux su NTFS/exFAT: Win32 la apriva come 'night'."""
    dotted = "\\\\?\\" + str(tmp_path / "night.")
    os.makedirs(dotted)
    nina_light(Path(dotted + "\\a.fits"), 1)
    nina_light(tmp_path / "night" / "b.fits", 2)
    result = scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    assert result.changes.new == ["night./a.fits", "night/b.fits"]
    assert result.frames == 2


def test_a_move_plus_a_copy_is_one_move_and_one_duplicate(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 4)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    shutil.copy(tmp_path / "a.fits", tmp_path / "c.fits")
    (tmp_path / "a.fits").rename(tmp_path / "b.fits")
    result = scan_root(conn, root, LATER)
    assert result.moved == [("a.fits", "b.fits")]
    assert list(result.duplicates.values()) == [["b.fits", "c.fits"]]


def test_the_move_is_the_file_that_kept_size_and_date_not_the_first_by_name(conn, tmp_path):
    """Spostato in z/, copiato in b.fits: lo spostato tiene la data. Prima: scelto per nome."""
    nina_light(tmp_path / "a.fits", 4)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    shutil.copy(tmp_path / "a.fits", tmp_path / "b.fits")
    _touch_later(tmp_path / "b.fits")
    (tmp_path / "z").mkdir()
    (tmp_path / "a.fits").rename(tmp_path / "z" / "a.fits")
    assert scan_root(conn, root, LATER).moved == [("a.fits", "z/a.fits")]


def test_a_kept_move_wins_even_when_an_earlier_name_has_none(conn, tmp_path):
    """a e b doppioni; a cancellato, b spostato in c, c copiato in d: b -> c, non b -> d."""
    nina_light(tmp_path / "a.fits", 4)
    shutil.copy(tmp_path / "a.fits", tmp_path / "b.fits")
    _touch_later(tmp_path / "b.fits")
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "a.fits").unlink()
    (tmp_path / "b.fits").rename(tmp_path / "c.fits")
    shutil.copy(tmp_path / "c.fits", tmp_path / "d.fits")
    _touch_later(tmp_path / "d.fits")
    _touch_later(tmp_path / "d.fits")
    assert scan_root(conn, root, LATER).moved == [("a.fits", "d.fits"), ("b.fits", "c.fits")]


def test_a_file_not_read_has_no_frame(conn, tmp_path):
    (tmp_path / "altro.fits").write_bytes(b"SIMPLE  =                    T".ljust(2880))
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    assert _files(conn) == {"altro.fits": None}


def test_an_interrupted_scan_reads_its_files_next_time(conn, tmp_path, monkeypatch):
    """Scansione fermata a meta': la prossima legge cio' che manca, nessuna posa persa."""
    nina_light(tmp_path / "a.fits", 1)
    nina_light(tmp_path / "b.fits", 2)
    root = add_root(conn, tmp_path, NOW)
    real = scan.scan_file
    monkeypatch.setattr(scan, "scan_file", _stopping_scan(real, at=2))
    with pytest.raises(KeyboardInterrupt):
        scan_root(conn, root, NOW)
    monkeypatch.setattr(scan, "scan_file", real)
    assert scan_root(conn, root, LATER).frames == 2


def test_a_file_changed_then_a_stopped_scan_is_read_next_time(conn, tmp_path, monkeypatch):
    """Cambiato, poi scansione fermata prima di leggerlo: la prossima lo vede ancora cambiato."""
    a = nina_light(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    nina_light(a, 1, ("OBJECT  = 'M 42'",))
    _touch_later(a)
    real = scan.scan_file
    monkeypatch.setattr(scan, "scan_file", _stopping_scan(real))
    with pytest.raises(KeyboardInterrupt):
        scan_root(conn, root, LATER)
    monkeypatch.setattr(scan, "scan_file", real)
    assert scan_root(conn, root, LATER).changes.changed == ["a.fits"]
    header = conn.execute("SELECT header FROM pipeline_headers").fetchone()["header"]
    assert json.loads(header)["OBJECT"] == "M 42"


def test_another_connection_writes_while_files_are_read(conn, db_path, tmp_path, monkeypatch):
    """Lettura lenta (NAS) fuori transazione: risposta a un filtro non aspetta la scansione."""
    nina_light(tmp_path / "a.fits", 1)
    nina_light(tmp_path / "b.fits", 2)
    root = add_root(conn, tmp_path, NOW)
    real = scan.scan_file
    wrote: list[bool] = []

    def other_writes(path, size=None):
        other = sqlite3.connect(db_path, timeout=0)
        other.execute(
            "INSERT INTO pipeline_filter_answers (written_key, standard) VALUES (?, 'ha')",
            (path.name,),
        )
        other.commit()
        other.close()
        wrote.append(True)
        return real(path, size)

    monkeypatch.setattr(scan, "scan_file", other_writes)
    scan_root(conn, root, NOW)
    assert wrote == [True, True]


def test_an_interrupted_scan_keeps_what_it_read(conn, tmp_path, monkeypatch):
    """Lotti salvati restano; il prossimo giro legge solo cio' che mancava."""
    for seed in range(3):
        nina_light(tmp_path / f"{seed}.fits", seed)
    root = add_root(conn, tmp_path, NOW)
    monkeypatch.setattr(scan, "BATCH", 1)
    real = scan.scan_file
    monkeypatch.setattr(scan, "scan_file", _stopping_scan(real, at=2))
    with pytest.raises(KeyboardInterrupt):
        scan_root(conn, root, NOW)
    assert _cards(conn) == {"0.fits": "light"}
    monkeypatch.setattr(scan, "scan_file", real)
    again = scan_root(conn, root, LATER)
    assert again.changes.to_read == ["1.fits", "2.fits"]
    assert again.frames == 3


def test_a_move_interrupted_mid_scan_is_still_found_next_time(conn, tmp_path, monkeypatch):
    """Sparito si scrive a fine scansione: interrotta, il giro dopo rivede lo spostamento."""
    nina_light(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "a.fits").rename(tmp_path / "b.fits")
    real = scan.scan_file
    monkeypatch.setattr(scan, "scan_file", _stopping_scan(real))
    with pytest.raises(KeyboardInterrupt):
        scan_root(conn, root, LATER)
    monkeypatch.setattr(scan, "scan_file", real)
    assert scan_root(conn, root, "2026-10-24T20:00:00+00:00").moved == [("a.fits", "b.fits")]
    finished = conn.execute("SELECT finished FROM pipeline_scans ORDER BY id").fetchall()
    assert [r["finished"] for r in finished] == [1, 0, 1]


def test_a_move_already_saved_when_the_scan_stopped_is_found_next_time(conn, tmp_path, monkeypatch):
    """Lotto con lo spostato salvato, fermata dopo: il giro dopo abbina ancora."""
    nina_light(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "a.fits").rename(tmp_path / "b.fits")
    nina_light(tmp_path / "c.fits", 2)
    monkeypatch.setattr(scan, "BATCH", 1)
    real = scan.scan_file
    monkeypatch.setattr(scan, "scan_file", _stopping_scan(real, at=2))
    with pytest.raises(KeyboardInterrupt):
        scan_root(conn, root, LATER)
    monkeypatch.setattr(scan, "scan_file", real)
    assert scan_root(conn, root, "2026-10-24T20:00:00+00:00").moved == [("a.fits", "b.fits")]


def test_a_move_survives_a_stopped_scan_then_a_silent_root(conn, tmp_path, monkeypatch):
    """Fermata, poi NAS spento (scansione finita senza giudizio): lo spostamento si trova."""
    nas = tmp_path / "nas"
    nina_light(nas / "a.fits", 1)
    root = add_root(conn, nas, NOW)
    scan_root(conn, root, NOW)
    (nas / "a.fits").rename(nas / "b.fits")
    nina_light(nas / "c.fits", 2)
    monkeypatch.setattr(scan, "BATCH", 1)
    real = scan.scan_file
    monkeypatch.setattr(scan, "scan_file", _stopping_scan(real, at=2))
    with pytest.raises(KeyboardInterrupt):
        scan_root(conn, root, LATER)
    monkeypatch.setattr(scan, "scan_file", real)
    nas.rename(tmp_path / "off")
    assert not scan_root(conn, root, "2026-10-24T20:00:00+00:00").changes.reachable
    (tmp_path / "off").rename(nas)
    assert scan_root(conn, root, "2026-10-25T20:00:00+00:00").moved == [("a.fits", "b.fits")]


def test_a_file_changed_in_place_is_not_a_move(conn, tmp_path):
    """Riletto allo stesso posto: nessuno spostamento, anche se un'altra copia sparisce."""
    nina_light(tmp_path / "a.fits", 1)
    nina_light(tmp_path / "b.fits", 1)  # copy of same frame
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "a.fits").unlink()
    nina_light(tmp_path / "b.fits", 1, ("OBJECT  = 'M 42'",))
    _touch_later(tmp_path / "b.fits")
    assert scan_root(conn, root, LATER).moved == []


def test_a_second_scan_of_the_same_root_is_refused_and_loses_nothing(
    conn, db_path, tmp_path, monkeypatch
):
    """Seconda scansione della stessa radice mentre la prima gira: rifiutata, niente sparito."""
    for seed in range(3):
        nina_light(tmp_path / f"{seed}.fits", seed)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    _touch_later(tmp_path / "0.fits")
    other = connect(db_path)
    refused: list[bool] = []
    tried: list[bool] = []
    real = scan.scan_file

    def second_scan_meanwhile(path, size=None):
        if not tried:
            tried.append(True)
            try:
                scan_root(other, root, "2026-10-23T21:00:00+00:00")
            except ScanRunningError:
                refused.append(True)
        return real(path, size)

    monkeypatch.setattr(scan, "scan_file", second_scan_meanwhile)
    try:
        result = scan_root(conn, root, LATER)
    finally:
        other.close()
    assert refused == [True]
    assert conn.execute("SELECT COUNT(*) FROM pipeline_scans").fetchone()[0] == 2  # none for it
    assert result.changes.gone == []
    assert (
        conn.execute("SELECT COUNT(*) FROM pipeline_files WHERE state = 'gone'").fetchone()[0] == 0
    )


def test_two_roots_scan_side_by_side(conn, db_path, tmp_path, monkeypatch):
    nina_light(tmp_path / "a" / "1.fits", 1)
    nina_light(tmp_path / "b" / "2.fits", 2)
    first, second = add_root(conn, tmp_path / "a", NOW), add_root(conn, tmp_path / "b", NOW)
    other = connect(db_path)
    real = scan.scan_file
    inner: list[int] = []

    def other_root_meanwhile(path, size=None):
        if not inner:
            inner.append(0)
            inner[0] = scan_root(other, second, NOW).frames
        return real(path, size)

    monkeypatch.setattr(scan, "scan_file", other_root_meanwhile)
    try:
        assert scan_root(conn, first, NOW).frames == 1
    finally:
        other.close()
    assert inner == [1]


def test_moves_are_written_with_the_scan_that_found_them(conn, tmp_path):
    """Spostati scritti, non solo in memoria: la schermata li legge, mai li ricalcola."""
    nina_light(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "night").mkdir()
    (tmp_path / "a.fits").rename(tmp_path / "night" / "a.fits")
    result = scan_root(conn, root, LATER)
    rows = conn.execute("SELECT scan_id, was_path, now_path FROM pipeline_moves").fetchall()
    assert [tuple(r) for r in rows] == [(result.changes.scan_id, "a.fits", "night/a.fits")]
    assert result.moved == [("a.fits", "night/a.fits")]


def test_a_move_is_never_lost_if_the_process_dies_closing_the_scan(conn, tmp_path, monkeypatch):
    """Morto fra 'sparito' e 'spostato': stessa transazione, il giro dopo rifa' tutto."""
    nina_light(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "a.fits").rename(tmp_path / "b.fits")
    real = scan._moved

    def dies(*_args):
        raise KeyboardInterrupt

    monkeypatch.setattr(scan, "_moved", dies)
    with pytest.raises(KeyboardInterrupt):
        scan_root(conn, root, LATER)
    monkeypatch.setattr(scan, "_moved", real)
    assert scan_root(conn, root, "2026-10-24T20:00:00+00:00").moved == [("a.fits", "b.fits")]


def test_pairing_moves_finds_files_by_frame_through_an_index(conn):
    """Cartella alta rinominata = archivio intero spostato: senza indice 8.000 file 8 s."""
    plan = " ".join(
        row["detail"] for row in conn.execute(f"EXPLAIN QUERY PLAN {scan.MOVED}", (1, 1))
    )
    assert "pipeline_files_frame" in plan


def test_an_unchanged_archive_is_not_read_again(conn, tmp_path, monkeypatch):
    nina_light(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)

    def forbidden(_path):
        raise AssertionError("a file was opened")

    monkeypatch.setattr(scan, "scan_file", forbidden)
    result = scan_root(conn, root, LATER)
    assert result.frames == 1


def _headers(conn) -> dict[str, tuple[str, dict]]:
    """rel_path -> (program, header) of every file with stored header, present or gone. Checks
    invariant on the way: file has frame iff it has header."""
    rows = conn.execute(
        "SELECT f.rel_path, f.frame_id, h.program, h.header FROM pipeline_files AS f"
        " LEFT JOIN pipeline_headers AS h ON h.file_id = f.id"
    ).fetchall()
    for row in rows:
        assert (row["frame_id"] is None) == (row["header"] is None), row["rel_path"]
    return {
        row["rel_path"]: (row["program"], json.loads(row["header"]))
        for row in rows
        if row["header"] is not None
    }


def _touch_later(path: Path) -> None:
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 10**9))


def test_the_header_is_stored_as_written_with_its_types(conn, tmp_path):
    nina_light(
        tmp_path / "a.fits",
        1,
        ("GAIN    =                  100", "EXPOSURE=                300.0"),
    )
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    program, header = _headers(conn)["a.fits"]
    assert program == "N.I.N.A."
    assert header["SIMPLE"] is True
    assert header["GAIN"] == 100 and isinstance(header["GAIN"], int)
    assert header["EXPOSURE"] == 300.0 and isinstance(header["EXPOSURE"], float)
    assert header["IMAGETYP"] == "LIGHT"


def test_two_copies_of_a_frame_keep_each_its_own_header(conn, tmp_path):
    """Stessa posa, header riscritto in una copia: un frame, due header, nessuno perso."""
    nina_light(tmp_path / "a.fits", 5)
    nina_light(tmp_path / "b.fits", 5, ("OBJECT  = 'M 33'",))
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    files, headers = _files(conn), _headers(conn)
    assert files["a.fits"] == files["b.fits"]
    assert "OBJECT" not in headers["a.fits"][1]
    assert headers["b.fits"][1]["OBJECT"] == "M 33"


def test_a_file_read_again_replaces_its_header(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    nina_light(tmp_path / "a.fits", 1, ("OBJECT  = 'M 42'",))
    _touch_later(tmp_path / "a.fits")
    scan_root(conn, root, LATER)
    assert _headers(conn)["a.fits"][1]["OBJECT"] == "M 42"


def test_a_file_with_new_pixels_has_a_new_frame_and_header(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    before = _files(conn)["a.fits"]
    nina_light(tmp_path / "a.fits", 2, ("OBJECT  = 'M 42'",))
    _touch_later(tmp_path / "a.fits")
    scan_root(conn, root, LATER)
    assert _files(conn)["a.fits"] != before
    assert _headers(conn)["a.fits"][1]["OBJECT"] == "M 42"


def test_a_gone_file_keeps_its_header(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "a.fits").unlink()
    scan_root(conn, root, LATER)
    assert _headers(conn)["a.fits"][1]["IMAGETYP"] == "LIGHT"


def test_a_file_back_is_no_longer_gone(conn, tmp_path):
    """Tornato: non dice piu' quando era sparito; lo schema rifiuta la riga che lo dice."""
    nina_light(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "a.fits").rename(tmp_path / "away.fit")
    scan_root(conn, root, LATER)
    (tmp_path / "away.fit").rename(tmp_path / "a.fits")
    scan_root(conn, root, LATER)
    row = conn.execute("SELECT state, gone_scan_id FROM pipeline_files WHERE rel_path = 'a.fits'")
    assert tuple(row.fetchone()) == ("present", None)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE pipeline_files SET gone_scan_id = seen_scan_id")


def test_a_file_rewritten_by_another_program_loses_frame_and_header(conn, tmp_path):
    """Riscritto da un editor sopra l'originale: oggi non e' posa, header vecchio non resta."""
    nina_light(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    nina_light(tmp_path / "a.fits", 1, ("PROGRAM = 'Editor 1.9.3'",))
    _touch_later(tmp_path / "a.fits")
    scan_root(conn, root, LATER)
    assert _files(conn) == {"a.fits": None}
    assert _headers(conn) == {}


@pytest.mark.parametrize(
    ("pixels", "extra"), [(2, ()), (1, ("PROGRAM = 'Editor 1.9.3'",))], ids=["pixels", "rewritten"]
)
def test_a_frame_no_file_points_to_any_more_is_gone(conn, tmp_path, pixels, extra):
    """Posa lasciata da ogni file, presente o sparito: non resta come fantasma. Copia e
    sparito tengono la loro."""
    nina_light(tmp_path / "a.fits", 1)
    nina_light(tmp_path / "copy" / "a.fits", 3)
    nina_light(tmp_path / "b.fits", 3)
    nina_light(tmp_path / "gone.fits", 4)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "gone.fits").unlink()
    nina_light(tmp_path / "a.fits", pixels, extra)
    nina_light(tmp_path / "b.fits", 5)
    _touch_later(tmp_path / "a.fits")
    _touch_later(tmp_path / "b.fits")
    scan_root(conn, root, LATER)
    frames = {row["id"] for row in conn.execute("SELECT id FROM pipeline_frames")}
    used = conn.execute("SELECT frame_id FROM pipeline_files WHERE frame_id IS NOT NULL")
    assert frames == {row["frame_id"] for row in used}
    assert len(frames) == (4 if pixels == 2 else 3)
    gone = conn.execute("SELECT frame_id FROM pipeline_files WHERE rel_path = 'gone.fits'")
    assert gone.fetchone()["frame_id"] in frames


def test_an_unreachable_folder_leaves_every_header(conn, tmp_path):
    archive = tmp_path / "nas"
    nina_light(archive / "a.fits", 1)
    root = add_root(conn, archive, NOW)
    scan_root(conn, root, NOW)
    archive.rename(tmp_path / "spento")
    scan_root(conn, root, LATER)
    assert _headers(conn)["a.fits"][1]["IMAGETYP"] == "LIGHT"


def test_a_skipped_file_has_no_header(conn, tmp_path):
    (tmp_path / "altro.fits").write_bytes(b"SIMPLE  =                    T".ljust(2880))
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    assert _headers(conn) == {}


def _cards(conn) -> dict[str, str]:
    """rel_path -> frame type; checks a file has a card if and only if it has a header."""
    rows = conn.execute(
        "SELECT f.rel_path, h.file_id AS h, c.frame_type FROM pipeline_files AS f"
        " LEFT JOIN pipeline_headers AS h ON h.file_id = f.id"
        " LEFT JOIN pipeline_cards AS c ON c.file_id = f.id"
    ).fetchall()
    for row in rows:
        assert (row["h"] is None) == (row["frame_type"] is None), row["rel_path"]
    return {r["rel_path"]: r["frame_type"] for r in rows if r["frame_type"] is not None}


def test_each_file_read_gets_its_card(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 1)
    nina_light(tmp_path / "b.fits", 2, ("OBJECT  = 'Snapshot'",))
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    assert _cards(conn) == {"a.fits": "light", "b.fits": "snapshot"}


def test_a_file_read_again_gets_a_new_card_and_a_skipped_one_none(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 1)
    nina_light(tmp_path / "b.fits", 2)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    nina_light(tmp_path / "a.fits", 1, ("OBJECT  = 'darkflat'",))
    nina_light(tmp_path / "b.fits", 2, ("PROGRAM = 'Editor 1.9.3'",))
    _touch_later(tmp_path / "a.fits")
    _touch_later(tmp_path / "b.fits")
    scan_root(conn, root, LATER)
    assert _cards(conn) == {"a.fits": "unknown"}


@pytest.mark.parametrize("reason", [Skip.UNREADABLE, Skip.INCOMPLETE])
def test_a_file_that_failed_to_read_is_read_again_next_scan(conn, tmp_path, monkeypatch, reason):
    """Bloccato dal NAS o copia in corso: motivo passeggero, mai perso per sempre."""
    path = nina_light(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    _touch_later(path)
    real = scan.scan_file
    monkeypatch.setattr(scan, "scan_file", lambda p, size=None: Skipped(p, reason))
    scan_root(conn, root, LATER)
    assert _cards(conn) == {}
    monkeypatch.setattr(scan, "scan_file", real)
    again = scan_root(conn, root, "2026-10-24T20:00:00+00:00")
    assert again.changes.to_read == ["a.fits"]
    assert _cards(conn) == {"a.fits": "light"}


def test_a_broken_header_is_not_opened_again_until_the_file_changes(conn, tmp_path):
    """BITPIX 17: header finito e sbagliato, rotto per sempre. Prima riaperto a ogni scansione."""
    path = nina_light(tmp_path / "a.fits", 1, ("BITPIX  =                   17",))
    raw = path.read_bytes().replace(b"BITPIX  =                   16", b"COMMENT".ljust(30), 1)
    path.write_bytes(raw)
    root = add_root(conn, tmp_path, NOW)
    first = scan_root(conn, root, NOW)
    assert [s.reason for s in first.skipped] == ["broken"]
    assert scan_root(conn, root, LATER).changes.to_read == []


def test_a_scan_says_what_the_walk_left_out(conn, tmp_path):
    """Cestini e file solo nel cloud: fuori, ma detti, mai persi in silenzio."""
    nina_light(tmp_path / "a.fits", 1)
    nina_light(tmp_path / ".Trashes" / "deleted.fits", 2)
    (tmp_path / "night").mkdir()
    (tmp_path / "night" / ".M42.fits.icloud").write_bytes(b"SIMPLE  = T")
    result = scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    assert result.changes.hidden == [".Trashes"]
    assert result.changes.online_only == ["night/M42.fits"]


def test_the_receipt_keeps_rereads_skips_and_what_was_left_out(conn, tmp_path, monkeypatch):
    """Ricevuta: riletti a parte dai cambiati, saltati contati, fuori coi percorsi."""
    path = nina_light(tmp_path / "a.fits", 1)
    nina_light(tmp_path / "b.fits", 2, ("PROGRAM = 'Editor 1.9.3'",))
    nina_light(tmp_path / ".Trashes" / "deleted.fits", 3)
    root = add_root(conn, tmp_path, NOW)
    real = scan.scan_file
    monkeypatch.setattr(
        scan,
        "scan_file",
        lambda p, size=None: Skipped(p, Skip.UNREADABLE) if p == path else real(p, size),
    )
    first = scan_root(conn, root, NOW)
    monkeypatch.setattr(scan, "scan_file", real)
    second = scan_root(conn, root, LATER)
    assert (first.changes.new, second.changes.reread, second.changes.changed) == (
        ["a.fits", "b.fits"],
        ["a.fits"],
        [],
    )
    rows = conn.execute(
        "SELECT new, changed, reread, unchanged, skipped, left_out FROM pipeline_scans ORDER BY id"
    ).fetchall()
    left_out = {"hidden": [".Trashes"], "online_only": [], "unreachable": [], "unlooked": []}
    assert [tuple(r)[:4] for r in rows] == [(2, 0, 0, 0), (0, 0, 1, 1)]
    assert [json.loads(r["skipped"]) for r in rows] == [{"unreadable": 1, "rewritten": 1}, {}]
    assert [json.loads(r["left_out"]) for r in rows] == [left_out, left_out]


def test_a_copy_still_running_is_incomplete_by_its_size_not_its_date(conn, tmp_path):
    """Dimensione, non la data: una copia a meta' resta incompleta e si rilegge."""
    path = nina_light(tmp_path / "a.fits", 1)
    path.write_bytes(path.read_bytes()[:3000])  # header whole, pixels cut
    result = scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    assert [s.reason for s in result.skipped] == ["incomplete"]


def test_the_receipt_counts_the_gone(conn, tmp_path):
    a = nina_light(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    a.unlink()
    scan_root(conn, root, LATER)
    gone = conn.execute("SELECT gone FROM pipeline_scans ORDER BY id DESC").fetchone()[0]
    assert gone == 1


def test_the_receipt_counts_the_keys_no_program_list_knows(conn, tmp_path):
    """Chiave che N.I.N.A. non scrive (dell'utente, o nuova): si dice, quanti file la portano."""
    nina_light(tmp_path / "a.fits", 1, ("MYNOTE  = 'x'",))
    nina_light(tmp_path / "b.fits", 2, ("MYNOTE  = 'y'",))
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    row = conn.execute("SELECT unknown_keys FROM pipeline_scans").fetchone()
    assert json.loads(row["unknown_keys"]) == {"MYNOTE": 2}


def test_a_file_skipped_for_its_content_is_not_read_again(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 1, ("PROGRAM = 'Editor 1.9.3'",))
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    assert scan_root(conn, root, LATER).changes.to_read == []


def _conditions(conn) -> dict[str, float]:
    rows = conn.execute(
        "SELECT f.rel_path, c.humidity_pct FROM pipeline_conditions AS c"
        " JOIN pipeline_files AS f ON f.id = c.file_id"
    ).fetchall()
    return {r["rel_path"]: r["humidity_pct"] for r in rows}


def test_conditions_live_only_where_written_and_follow_the_file(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 1, ("HUMIDITY=                 39.0",))
    nina_light(tmp_path / "b.fits", 2, ("HUMIDITY=                 45.0",))
    nina_light(tmp_path / "c.fits", 3)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    assert _conditions(conn) == {"a.fits": 39.0, "b.fits": 45.0}
    nina_light(tmp_path / "a.fits", 1)  # read again without weather
    nina_light(
        tmp_path / "b.fits", 2, ("HUMIDITY=                 45.0", "PROGRAM = 'Editor 1.9.3'")
    )
    _touch_later(tmp_path / "a.fits")
    _touch_later(tmp_path / "b.fits")
    scan_root(conn, root, LATER)
    assert _conditions(conn) == {}


def test_the_card_stores_start_and_exposure_in_one_form(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 1, ("DATE-OBS= '2025-06-29T21:11:33.412'", "EXPTIME =  120.0"))
    nina_light(tmp_path / "b.fits", 2)
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    rows = {
        r["rel_path"]: (r["start_utc"], r["exposure_s"])
        for r in conn.execute(
            "SELECT f.rel_path, c.start_utc, c.exposure_s FROM pipeline_cards AS c"
            " JOIN pipeline_files AS f ON f.id = c.file_id"
        )
    }
    assert rows == {"a.fits": ("2025-06-29T21:11:33.412000+00:00", 120.0), "b.fits": (None, None)}


def test_a_gone_file_keeps_its_card(conn, tmp_path):
    nina_light(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "a.fits").unlink()
    scan_root(conn, root, LATER)
    assert _cards(conn) == {"a.fits": "light"}
