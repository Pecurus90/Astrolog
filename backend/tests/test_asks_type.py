"""Chi aspetta una risposta sul tipo e' scritto sulla posa (`frames.asks_type`), e lo scritto e'
cio' che la regola direbbe dopo ogni strada che cambia un suo ingresso.

La regola (`stages.WAITING_RULE`) guarda il tipo del file, la risposta della cartella della sua
prima posizione viva e lo stato del cielo. Chi legge -- il residuo, `ready`, Da confermare, lo
stacco -- legge il segno. Un segno rimasto a 0 su una posa che la regola ferma e' il caso
pericoloso: `identify` la prenderebbe, e un dark diventerebbe ore. Per questo ogni prova di una
strada che cambia un ingresso confronta TUTTE le pose con la regola. Poi le cartelle della domanda,
scritte a fine stadio, e i piani di chi legge.
"""

import re

from astrolog.spine import scan_store, typeless, typeless_answer
from astrolog.spine.normalize import normalize_frames
from astrolog.spine.scan import scan_folder
from astrolog.spine.solve import solve_frames
from astrolog.spine.stages import (
    _WAITING_BY_STAGE,
    WAITING_RULE,
    invalidate,
    mark_pending,
    set_status,
)
from conftest import add_folder, sky_solved, write_fits
from test_solve import solver


def _posa(conn, folder_id, rel_path, image_type="unknown"):
    """Una posa con la sua posizione e i suoi stadi da fare, come la fa la scansione: prima il
    frame, poi la posizione."""
    frame_id = conn.execute(
        "INSERT INTO frames(frame_hash, image_type, header_json, created_at)"
        " VALUES(?, ?, '[]', 'ora')",
        (f"{folder_id}:{rel_path}", image_type),
    ).lastrowid
    mark_pending(conn, frame_id, "ora")
    scan_store.upsert_position(conn, frame_id, folder_id, rel_path, 1, 1.0, "ora")
    return frame_id


def _scritto(conn, frame_id):
    return conn.execute("SELECT asks_type FROM frames WHERE id = ?", (frame_id,)).fetchone()[0]


def _come_la_regola(conn):
    """Nessuna posa ha un segno diverso da cio' che la regola dice adesso."""
    sql = f"SELECT f.id, f.asks_type, ({WAITING_RULE}) AS regola FROM frames f"  # noqa: S608 - costante
    storte = [(r["id"], r["asks_type"], r["regola"]) for r in conn.execute(sql)]
    assert [s for s in storte if s[1] != s[2]] == []


def test_a_new_frame_without_type_waits_from_the_start(conn):
    """Appena entrata, una posa senza tipo aspetta: il cielo non l'ha ancora guardata. Una che dice
    di essere un light no."""
    radice = add_folder(conn, "D:/Astro")
    muta = _posa(conn, radice, "M51/a.fits")
    detta = _posa(conn, radice, "M51/b.fits", image_type="light")
    assert (_scritto(conn, muta), _scritto(conn, detta)) == (1, 0)
    _come_la_regola(conn)


def test_a_frame_that_enters_a_folder_answered_light_does_not_wait(conn):
    """La risposta vale anche per i file che arrivano dopo: il segno lo riscrive la posizione."""
    radice = add_folder(conn, "D:/Astro")
    typeless.declare(conn, "D:/Astro/M51", typeless.LIGHT)
    posa = _posa(conn, radice, "M51/a.fits")
    assert _scritto(conn, posa) == 0
    _come_la_regola(conn)


def test_the_sky_moves_the_mark_both_ways(conn):
    """Risolta, la posa e' una foto e non aspetta; rimessa in fila dal cielo, torna ad aspettare."""
    radice = add_folder(conn, "D:/Astro")
    posa = _posa(conn, radice, "M51/a.fits")
    sky_solved(conn, posa)
    assert _scritto(conn, posa) == 0
    invalidate(conn, [posa], "solve")
    assert _scritto(conn, posa) == 1
    set_status(conn, posa, "solve", "failed", reason="no_solution")
    assert _scritto(conn, posa) == 1
    _come_la_regola(conn)


def test_an_answer_moves_the_mark_of_every_frame_of_its_folder(conn):
    """Una risposta "calibrazione" ferma anche una posa risolta; "foto del cielo" lascia andare
    anche una che il cielo non sa dire. Le altre cartelle non si muovono."""
    radice = add_folder(conn, "D:/Astro")
    risolta = _posa(conn, radice, "dark/a.fits")
    sky_solved(conn, risolta)
    muta = _posa(conn, radice, "flat/b.fits")
    altrove = _posa(conn, radice, "M51/c.fits")
    typeless.declare(conn, "D:/Astro/dark", typeless.CALIBRATION)
    typeless.declare(conn, "D:/Astro/flat", typeless.LIGHT)
    assert [_scritto(conn, p) for p in (risolta, muta, altrove)] == [1, 0, 1]
    _come_la_regola(conn)


def test_a_frame_whose_folder_changes_takes_the_answer_of_the_new_one(conn):
    """Il file sparito dalla cartella detta "foto" resta solo in una che non ha risposto: torna ad
    aspettare. Ricompare, e torna a non aspettare. La cartella e' quella della prima posizione
    viva."""
    radice = add_folder(conn, "D:/Astro")
    typeless.declare(conn, "D:/Astro/luci", typeless.LIGHT)
    posa = _posa(conn, radice, "luci/a.fits")
    scan_store.upsert_position(conn, posa, radice, "copie/a.fits", 1, 1.0, "ora")
    assert _scritto(conn, posa) == 0
    scan_store.mark_missing(conn, radice, {"copie/a.fits"}, set(), "ora")
    assert _scritto(conn, posa) == 1
    prima = scan_store.position(conn, radice, "luci/a.fits")["id"]
    scan_store.set_position_present(conn, prima, "ora")
    assert _scritto(conn, posa) == 0
    _come_la_regola(conn)


def test_a_position_that_changes_file_moves_both_marks(conn):
    """Lo stesso percorso con un file diverso: la posizione passa all'altro frame, e quello di
    prima, rimasto senza cartella, non ha piu' la risposta che lo lasciava andare."""
    radice = add_folder(conn, "D:/Astro")
    typeless.declare(conn, "D:/Astro/luci", typeless.LIGHT)
    vecchio = _posa(conn, radice, "luci/a.fits")
    nuovo = conn.execute(
        "INSERT INTO frames(frame_hash, image_type, header_json, created_at)"
        " VALUES('nuovo', 'unknown', '[]', 'ora')"
    ).lastrowid
    mark_pending(conn, nuovo, "ora")
    scan_store.upsert_position(conn, nuovo, radice, "luci/a.fits", 2, 2.0, "ora")
    assert (_scritto(conn, vecchio), _scritto(conn, nuovo)) == (1, 0)
    _come_la_regola(conn)


def _muto(path, **header):
    """Un file che non dice `IMAGETYP`, con cio' che serve alla normalizzazione e al cielo."""
    card = {"INSTRUME": "ASI2600MM", "FILTER": "Ha", "EXPTIME": 300.0, "OBJECT": "M 51"}
    return write_fits(path, {**card, "DATE-OBS": "2024-05-17T21:00:00", **header})


def test_the_end_of_the_normalization_writes_the_folders_without_its_copies(conn, tmp_path):
    """La normalizzazione trova le copie, e una copia non si conta: le cartelle le riscrive lei,
    perche' puo' ripartire da sola dopo una risposta senza che il cielo giri dopo di lei."""
    _muto(tmp_path / "lib" / "notte" / "raw.fits", SWCREATE="Un programma qualunque 7")
    _muto(
        tmp_path / "lib" / "notte" / "cal.fits", SWCREATE="Un programma qualunque 7", CALSTAT="BDF"
    )
    list(scan_folder(conn, add_folder(conn, tmp_path / "lib")))
    for (frame_id,) in conn.execute("SELECT id FROM frames").fetchall():  # il cielo non sa dire
        set_status(conn, frame_id, "solve", "failed", reason="no_solution")
    assert typeless.by_folder(conn) == []  # ne' la scansione ne' uno stato la scrivono
    list(normalize_frames(conn))
    assert [g["frames"] for g in typeless.by_folder(conn)] == [1]


def test_the_end_of_the_sky_writes_the_folders_it_cannot_tell(conn, tmp_path):
    """Il cielo decide chi non sa dire: a fine stadio le cartelle si riscrivono, e quella dei file
    che non ha risolto diventa una domanda."""
    for i in range(2):
        _muto(tmp_path / "lib" / "dark" / f"{i}.fits")
    list(scan_folder(conn, add_folder(conn, tmp_path / "lib")))
    assert typeless.by_folder(conn) == []
    list(
        solve_frames(conn, exe="astap", run=solver(esiti={0: None, 1: None}), cache=tmp_path / "c")
    )
    assert [g["frames"] for g in typeless.by_folder(conn)] == [2]


def _piano(conn, query):
    return " ".join(r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + query))


def test_the_readers_start_from_the_frames_that_wait(conn):
    """Il residuo e lo stacco partono dalle pose segnate: un archivio che scrive il tipo non ne ha
    nessuna, e chi non lo scrive paga solo quelle che aspettano davvero -- non tutte quelle senza
    tipo, e non lo stadio `measure`, che ha in fila ogni posa."""
    for query in (_WAITING_BY_STAGE, typeless_answer._WAITING_AND_ATTACHED):
        piano = _piano(conn, query)
        assert re.match(r"(SCAN|SEARCH) f USING (COVERING )?INDEX frames_asks_type\b", piano), piano
        assert "frame_stages_pending" not in piano, piano


def test_the_type_question_reads_the_written_folders(conn):
    """La domanda sul tipo in Da confermare legge la tabella scritta, non le pose."""
    piano = _piano(conn, typeless._WRITTEN)
    assert re.findall(r"(?:SCAN|SEARCH) (\w+)", piano) == ["t", "dc"], piano
