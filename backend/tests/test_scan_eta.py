"""Mentre la prima scansione legge l'archivio la Dashboard dice quanto manca e che e' la prima
(tavola dashboard-stati-lettura v37). I due fatti escono scritti da `/pipeline/status`.

Il tempo che manca si stima dal ritmo finora (Marco, 15/10/2026): i file che restano diviso il ritmo
dei file gia' letti. Nel primo minuto tace: il ritmo dei primi file non e' ancora quello vero."""

from datetime import UTC, datetime, timedelta

from astrolog.api.pipeline import _remaining, is_first_scan, remaining_s
from astrolog.clock import iso_z
from astrolog.spine.scan_store import start_run


def test_what_is_left_goes_at_the_pace_so_far():
    # 1.240 file in 3 minuti: ne restano 7.070, al ritmo di prima
    assert remaining_s(current=1240, total=8310, elapsed_s=180) == round(180 * 7070 / 1240)


def test_in_the_first_minute_the_pace_is_not_known_yet():
    assert remaining_s(current=300, total=8310, elapsed_s=59) is None


def test_nothing_read_yet_or_all_read_says_nothing():
    assert remaining_s(current=0, total=8310, elapsed_s=600) is None
    assert remaining_s(current=8310, total=8310, elapsed_s=600) is None


def test_the_pace_starts_with_the_folder_being_read_not_with_the_gesture():
    """Le ricevute di un gesto si aprono tutte insieme: dalla seconda cartella in poi il tempo
    contato dalla ricevuta comprenderebbe le cartelle lette prima. Si conta da quando la lettura
    di questa cartella e' cominciata, e nel suo primo minuto si tace."""
    dieci_secondi_fa = iso_z(datetime.now(UTC) - timedelta(seconds=10))
    assert _remaining({"current": 100, "total": 1000, "since": dieci_secondi_fa}) is None
    due_minuti_fa = iso_z(datetime.now(UTC) - timedelta(seconds=120))
    stimato = _remaining({"current": 100, "total": 1000, "since": due_minuti_fa})
    assert stimato is not None and 1070 <= stimato <= 1090


def _folder(conn, dove: str) -> int:
    return conn.execute(
        "INSERT INTO folders(root_path, created_at) VALUES(?, 'ora')", (dove,)
    ).lastrowid


def test_the_first_reading_is_the_one_with_no_reading_ended_before(conn):
    """La prima scansione: nessuna cartella aveva mai finito una lettura prima di questo gesto. Le
    letture del gesto in corso non contano, finite o no."""
    cartella = _folder(conn, "D:/Astro")
    adesso = start_run(conn, cartella, "ora")
    assert is_first_scan(conn, [adesso])

    conn.execute("UPDATE scan_runs SET ended_at = 'dopo', status = 'ok' WHERE id = ?", (adesso,))
    assert is_first_scan(conn, [adesso])

    # la stessa cartella riletta, dopo una lettura finita: non e' piu' la prima
    poi = start_run(conn, cartella, "dopo ancora")
    assert not is_first_scan(conn, [poi])


def test_resuming_after_one_of_two_folders_was_read_is_still_the_first(conn):
    """Due cartelle: A finita, B fermata. Riprendi apre ricevute nuove per tutte e due: B non e'
    mai stata letta fino in fondo, quindi la lettura e' ancora la prima."""
    a, b = _folder(conn, "D:/A"), _folder(conn, "E:/B")
    a1, b1 = start_run(conn, a, "ora"), start_run(conn, b, "ora")
    conn.execute("UPDATE scan_runs SET ended_at = 'dopo', status = 'ok' WHERE id = ?", (a1,))
    conn.execute("UPDATE scan_runs SET ended_at = 'dopo', status = 'stopped' WHERE id = ?", (b1,))
    a2, b2 = start_run(conn, a, "poi"), start_run(conn, b, "poi")
    assert is_first_scan(conn, [a2, b2])


def test_a_stopped_first_reading_is_still_the_first_when_it_resumes(conn):
    """Ferma e poi Riprendi: la prima lettura fermata non e' finita, e quella che riparte con una
    ricevuta nuova e' ancora la prima."""
    fermata = start_run(conn, _folder(conn, "D:/Astro"), "ora")
    conn.execute(
        "UPDATE scan_runs SET ended_at = 'dopo', status = 'stopped' WHERE id = ?", (fermata,)
    )
    ripresa = start_run(conn, _folder(conn, "E:/Altro"), "dopo ancora")
    assert is_first_scan(conn, [ripresa])
