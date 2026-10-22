"""Mattoni 3 e 3b: frame per impronta (stessa impronta = doppione, spostato = stesso frame),
header di ogni file letto accanto al frame."""

import json
import os
import shutil
import sqlite3
from pathlib import Path

import pytest

from astrolog.db.connect import connect
from astrolog.pipeline import scan
from astrolog.pipeline.changes import add_root
from astrolog.pipeline.scan import ScanRunningError, scan_root
from astrolog.pipeline.scanner import Skip, Skipped

NOW = "2026-10-22T20:00:00+00:00"
LATER = "2026-10-23T20:00:00+00:00"
CORPUS = Path(__file__).with_name("header")


def _nina(path: Path, seed: int, extra: tuple[str, ...] = ()) -> Path:
    """Small N.I.N.A. light with own pixels: `seed` makes different frame, `extra` cards
    different header on same frame."""
    lines = [
        "SIMPLE  =                    T",
        "BITPIX  =                   16",
        "NAXIS   =                    2",
        "NAXIS1  =                   16",
        "NAXIS2  =                   16",
        "IMAGETYP= 'LIGHT'",
        "SWCREATE= 'N.I.N.A. 3.2.0.9001 (x64)'",
        *extra,
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
    """Stessa posa in due cartelle: un frame, due file, e la ricevuta lo dice."""
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
    """Scansione fermata a meta' non salva nulla: la prossima rilegge, nessuna posa persa."""
    _nina(tmp_path / "a.fits", 1)
    _nina(tmp_path / "b.fits", 2)
    root = add_root(conn, tmp_path, NOW)
    import astrolog.pipeline.scan as scan

    real = scan.scan_file
    calls: list[Path] = []

    def stops_at_second(path):
        calls.append(path)
        if len(calls) == 2:
            raise KeyboardInterrupt
        return real(path)

    monkeypatch.setattr(scan, "scan_file", stops_at_second)
    with pytest.raises(KeyboardInterrupt):
        scan_root(conn, root, NOW)
    monkeypatch.setattr(scan, "scan_file", real)
    assert scan_root(conn, root, LATER).frames == 2


def test_another_connection_writes_while_files_are_read(conn, db_path, tmp_path, monkeypatch):
    """Lettura lenta (NAS) fuori transazione: risposta a un filtro non aspetta la scansione."""
    _nina(tmp_path / "a.fits", 1)
    _nina(tmp_path / "b.fits", 2)
    root = add_root(conn, tmp_path, NOW)
    real = scan.scan_file
    wrote: list[bool] = []

    def other_writes(path):
        other = sqlite3.connect(db_path, timeout=0)
        other.execute(
            "INSERT INTO pipeline_filter_answers (written_key, standard) VALUES (?, 'ha')",
            (path.name,),
        )
        other.commit()
        other.close()
        wrote.append(True)
        return real(path)

    monkeypatch.setattr(scan, "scan_file", other_writes)
    scan_root(conn, root, NOW)
    assert wrote == [True, True]


def test_an_interrupted_scan_keeps_what_it_read(conn, tmp_path, monkeypatch):
    """Lotti salvati restano; il prossimo giro legge solo cio' che mancava."""
    for seed in range(3):
        _nina(tmp_path / f"{seed}.fits", seed)
    root = add_root(conn, tmp_path, NOW)
    monkeypatch.setattr(scan, "BATCH", 1)
    real = scan.scan_file
    calls: list[str] = []

    def stops_at_second(path):
        calls.append(path.name)
        if len(calls) == 2:
            raise KeyboardInterrupt
        return real(path)

    monkeypatch.setattr(scan, "scan_file", stops_at_second)
    with pytest.raises(KeyboardInterrupt):
        scan_root(conn, root, NOW)
    assert _cards(conn) == {"0.fits": "light"}
    monkeypatch.setattr(scan, "scan_file", real)
    again = scan_root(conn, root, LATER)
    assert again.changes.to_read == ["1.fits", "2.fits"]
    assert again.frames == 3


def test_a_move_interrupted_mid_scan_is_still_found_next_time(conn, tmp_path, monkeypatch):
    """Sparito si scrive a fine scansione: interrotta, il giro dopo rivede lo spostamento."""
    _nina(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "a.fits").rename(tmp_path / "b.fits")

    def stops(path):
        raise KeyboardInterrupt

    real = scan.scan_file
    monkeypatch.setattr(scan, "scan_file", stops)
    with pytest.raises(KeyboardInterrupt):
        scan_root(conn, root, LATER)
    monkeypatch.setattr(scan, "scan_file", real)
    assert scan_root(conn, root, "2026-10-24T20:00:00+00:00").moved == [("a.fits", "b.fits")]
    finished = conn.execute("SELECT finished FROM pipeline_scans ORDER BY id").fetchall()
    assert [r["finished"] for r in finished] == [1, 0, 1]


def test_a_move_already_saved_when_the_scan_stopped_is_found_next_time(conn, tmp_path, monkeypatch):
    """Lotto con lo spostato salvato, fermata dopo: il giro dopo abbina ancora."""
    _nina(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "a.fits").rename(tmp_path / "b.fits")
    _nina(tmp_path / "c.fits", 2)
    monkeypatch.setattr(scan, "BATCH", 1)
    real = scan.scan_file
    calls: list[str] = []

    def stops_at_second(path):
        calls.append(path.name)
        if len(calls) == 2:
            raise KeyboardInterrupt
        return real(path)

    monkeypatch.setattr(scan, "scan_file", stops_at_second)
    with pytest.raises(KeyboardInterrupt):
        scan_root(conn, root, LATER)
    monkeypatch.setattr(scan, "scan_file", real)
    assert scan_root(conn, root, "2026-10-24T20:00:00+00:00").moved == [("a.fits", "b.fits")]


def test_a_move_survives_a_stopped_scan_then_a_silent_root(conn, tmp_path, monkeypatch):
    """Fermata, poi NAS spento (scansione finita senza giudizio): lo spostamento si trova."""
    nas = tmp_path / "nas"
    _nina(nas / "a.fits", 1)
    root = add_root(conn, nas, NOW)
    scan_root(conn, root, NOW)
    (nas / "a.fits").rename(nas / "b.fits")
    _nina(nas / "c.fits", 2)
    monkeypatch.setattr(scan, "BATCH", 1)
    real = scan.scan_file
    calls: list[str] = []

    def stops_at_second(path):
        calls.append(path.name)
        if len(calls) == 2:
            raise KeyboardInterrupt
        return real(path)

    monkeypatch.setattr(scan, "scan_file", stops_at_second)
    with pytest.raises(KeyboardInterrupt):
        scan_root(conn, root, LATER)
    monkeypatch.setattr(scan, "scan_file", real)
    nas.rename(tmp_path / "off")
    assert not scan_root(conn, root, "2026-10-24T20:00:00+00:00").changes.reachable
    (tmp_path / "off").rename(nas)
    assert scan_root(conn, root, "2026-10-25T20:00:00+00:00").moved == [("a.fits", "b.fits")]


def test_a_file_changed_in_place_is_not_a_move(conn, tmp_path):
    """Riletto allo stesso posto: nessuno spostamento, anche se un'altra copia sparisce."""
    _nina(tmp_path / "a.fits", 1)
    _nina(tmp_path / "b.fits", 1)  # copy of same frame
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "a.fits").unlink()
    _nina(tmp_path / "b.fits", 1, ("OBJECT  = 'M 42'",))
    _touch_later(tmp_path / "b.fits")
    assert scan_root(conn, root, LATER).moved == []


def test_a_second_scan_of_the_same_root_is_refused_and_loses_nothing(
    conn, db_path, tmp_path, monkeypatch
):
    """Seconda scansione della stessa radice mentre la prima gira: rifiutata, niente sparito."""
    for seed in range(3):
        _nina(tmp_path / f"{seed}.fits", seed)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    _touch_later(tmp_path / "0.fits")
    other = connect(db_path)
    refused: list[bool] = []
    tried: list[bool] = []
    real = scan.scan_file

    def second_scan_meanwhile(path):
        if not tried:
            tried.append(True)
            try:
                scan_root(other, root, "2026-10-23T21:00:00+00:00")
            except ScanRunningError:
                refused.append(True)
        return real(path)

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
    _nina(tmp_path / "a" / "1.fits", 1)
    _nina(tmp_path / "b" / "2.fits", 2)
    first, second = add_root(conn, tmp_path / "a", NOW), add_root(conn, tmp_path / "b", NOW)
    other = connect(db_path)
    real = scan.scan_file
    inner: list[int] = []

    def other_root_meanwhile(path):
        if not inner:
            inner.append(0)
            inner[0] = scan_root(other, second, NOW).frames
        return real(path)

    monkeypatch.setattr(scan, "scan_file", other_root_meanwhile)
    try:
        assert scan_root(conn, first, NOW).frames == 1
    finally:
        other.close()
    assert inner == [1]


def test_an_unchanged_archive_is_not_read_again(conn, tmp_path, monkeypatch):
    _nina(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    import astrolog.pipeline.scan as scan

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
    _nina(
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
    _nina(tmp_path / "a.fits", 5)
    _nina(tmp_path / "b.fits", 5, ("OBJECT  = 'M 33'",))
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    files, headers = _files(conn), _headers(conn)
    assert files["a.fits"] == files["b.fits"]
    assert "OBJECT" not in headers["a.fits"][1]
    assert headers["b.fits"][1]["OBJECT"] == "M 33"


def test_a_file_read_again_replaces_its_header(conn, tmp_path):
    _nina(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    _nina(tmp_path / "a.fits", 1, ("OBJECT  = 'M 42'",))
    _touch_later(tmp_path / "a.fits")
    scan_root(conn, root, LATER)
    assert _headers(conn)["a.fits"][1]["OBJECT"] == "M 42"


def test_a_file_with_new_pixels_has_a_new_frame_and_header(conn, tmp_path):
    _nina(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    before = _files(conn)["a.fits"]
    _nina(tmp_path / "a.fits", 2, ("OBJECT  = 'M 42'",))
    _touch_later(tmp_path / "a.fits")
    scan_root(conn, root, LATER)
    assert _files(conn)["a.fits"] != before
    assert _headers(conn)["a.fits"][1]["OBJECT"] == "M 42"


def test_a_gone_file_keeps_its_header(conn, tmp_path):
    _nina(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "a.fits").unlink()
    scan_root(conn, root, LATER)
    assert _headers(conn)["a.fits"][1]["IMAGETYP"] == "LIGHT"


def test_a_file_rewritten_by_another_program_loses_frame_and_header(conn, tmp_path):
    """Riscritto da un editor sopra l'originale: oggi non e' posa, header vecchio non resta."""
    _nina(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    _nina(tmp_path / "a.fits", 1, ("PROGRAM = 'Editor 1.9.3'",))
    _touch_later(tmp_path / "a.fits")
    scan_root(conn, root, LATER)
    assert _files(conn) == {"a.fits": None}
    assert _headers(conn) == {}


def test_an_unreachable_folder_leaves_every_header(conn, tmp_path):
    archive = tmp_path / "nas"
    _nina(archive / "a.fits", 1)
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
    _nina(tmp_path / "a.fits", 1)
    _nina(tmp_path / "b.fits", 2, ("OBJECT  = 'Snapshot'",))
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    assert _cards(conn) == {"a.fits": "light", "b.fits": "snapshot"}


def test_a_file_read_again_gets_a_new_card_and_a_skipped_one_none(conn, tmp_path):
    _nina(tmp_path / "a.fits", 1)
    _nina(tmp_path / "b.fits", 2)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    _nina(tmp_path / "a.fits", 1, ("OBJECT  = 'darkflat'",))
    _nina(tmp_path / "b.fits", 2, ("PROGRAM = 'Editor 1.9.3'",))
    _touch_later(tmp_path / "a.fits")
    _touch_later(tmp_path / "b.fits")
    scan_root(conn, root, LATER)
    assert _cards(conn) == {"a.fits": "unknown"}


@pytest.mark.parametrize("reason", [Skip.UNREADABLE, Skip.INCOMPLETE])
def test_a_file_that_failed_to_read_is_read_again_next_scan(conn, tmp_path, monkeypatch, reason):
    """Bloccato dal NAS o copia in corso: motivo passeggero, mai perso per sempre."""
    path = _nina(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    _touch_later(path)
    real = scan.scan_file
    monkeypatch.setattr(scan, "scan_file", lambda p: Skipped(p, reason))
    scan_root(conn, root, LATER)
    assert _cards(conn) == {}
    monkeypatch.setattr(scan, "scan_file", real)
    again = scan_root(conn, root, "2026-10-24T20:00:00+00:00")
    assert again.changes.to_read == ["a.fits"]
    assert _cards(conn) == {"a.fits": "light"}


def test_a_scan_says_what_the_walk_left_out(conn, tmp_path):
    """Cestini e file solo nel cloud: fuori, ma detti, mai persi in silenzio."""
    _nina(tmp_path / "a.fits", 1)
    _nina(tmp_path / ".Trashes" / "deleted.fits", 2)
    (tmp_path / "night").mkdir()
    (tmp_path / "night" / ".M42.fits.icloud").write_bytes(b"SIMPLE  = T")
    result = scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    assert result.changes.hidden == [".Trashes"]
    assert result.changes.online_only == ["night/M42.fits"]


def test_the_receipt_keeps_rereads_skips_and_what_was_left_out(conn, tmp_path, monkeypatch):
    """Ricevuta: riletti a parte dai cambiati, saltati contati, fuori coi percorsi."""
    path = _nina(tmp_path / "a.fits", 1)
    _nina(tmp_path / "b.fits", 2, ("PROGRAM = 'Editor 1.9.3'",))
    _nina(tmp_path / ".Trashes" / "deleted.fits", 3)
    root = add_root(conn, tmp_path, NOW)
    real = scan.scan_file
    monkeypatch.setattr(
        scan, "scan_file", lambda p: Skipped(p, Skip.UNREADABLE) if p == path else real(p)
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
    assert [tuple(r)[:5] for r in rows] == [(2, 0, 0, 0, 2), (0, 0, 1, 1, 0)]
    assert [json.loads(r["left_out"]) for r in rows] == [left_out, left_out]


def test_a_file_skipped_for_its_content_is_not_read_again(conn, tmp_path):
    _nina(tmp_path / "a.fits", 1, ("PROGRAM = 'Editor 1.9.3'",))
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
    _nina(tmp_path / "a.fits", 1, ("HUMIDITY=                 39.0",))
    _nina(tmp_path / "b.fits", 2, ("HUMIDITY=                 45.0",))
    _nina(tmp_path / "c.fits", 3)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    assert _conditions(conn) == {"a.fits": 39.0, "b.fits": 45.0}
    _nina(tmp_path / "a.fits", 1)  # read again without weather
    _nina(tmp_path / "b.fits", 2, ("HUMIDITY=                 45.0", "PROGRAM = 'Editor 1.9.3'"))
    _touch_later(tmp_path / "a.fits")
    _touch_later(tmp_path / "b.fits")
    scan_root(conn, root, LATER)
    assert _conditions(conn) == {}


def test_the_card_stores_start_and_exposure_in_one_form(conn, tmp_path):
    _nina(tmp_path / "a.fits", 1, ("DATE-OBS= '2025-06-29T21:11:33.412'", "EXPTIME =  120.0"))
    _nina(tmp_path / "b.fits", 2)
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    rows = {
        r["rel_path"]: (r["start_utc"], r["exposure_s"])
        for r in conn.execute(
            "SELECT f.rel_path, c.start_utc, c.exposure_s FROM pipeline_cards AS c"
            " JOIN pipeline_files AS f ON f.id = c.file_id"
        )
    }
    assert rows == {"a.fits": ("2025-06-29T21:11:33.412000+00:00", 120.0), "b.fits": (None, None)}


def test_the_schema_refuses_a_start_in_another_form(conn, tmp_path):
    _nina(tmp_path / "a.fits", 1)
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    for bad in ("2025-06-29T21:11:33.412+00:00", "2025-06-29T21:11:33.412000"):
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE pipeline_cards SET start_utc = ?", (bad,))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE pipeline_cards SET exposure_s = -1.0")


def test_a_gone_file_keeps_its_card(conn, tmp_path):
    _nina(tmp_path / "a.fits", 1)
    root = add_root(conn, tmp_path, NOW)
    scan_root(conn, root, NOW)
    (tmp_path / "a.fits").unlink()
    scan_root(conn, root, LATER)
    assert _cards(conn) == {"a.fits": "light"}


def test_the_schema_refuses_a_header_that_is_not_a_json_object(conn, tmp_path):
    _nina(tmp_path / "a.fits", 1)
    scan_root(conn, add_root(conn, tmp_path, NOW), NOW)
    for bad in ("[1, 2]", '{"CCD-TEMP": NaN}'):
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE pipeline_headers SET header = ?", (bad,))
