"""Lo stadio `solve` senza ASTAP: il primo avvio di chiunque.

Le pose restano da fare, la cache risponde lo stesso, e niente si prepara per un lancio che non ci
sara'. Il resto dello stadio, e il finto ASTAP che i test lanciano, stanno in `test_solve.py`.
"""

import test_solve
from astrolog.db.connect import connect
from astrolog.spine import solve, stages
from astrolog.spine.solve import solve_frames
from test_solve import corri, solver, stato

archivio_letto = test_solve.archivio_letto  # la stessa fixture, non una copia


def test_without_astap_the_frames_wait_instead_of_burning(db_path, archivio_letto, tmp_path):
    """Al primo avvio il solver puo' non esserci ancora: le pose restano DA FARE, non fallite.

    Segnarle fallite sarebbe un vicolo cieco -- nessuno le rimetterebbe in coda, e chi installa
    ASTAP il giorno dopo troverebbe un archivio senza cielo e un pulsante che dice "niente da
    fare"."""
    conn = connect(db_path)
    ricevuta = list(solve_frames(conn, exe=None, cache=tmp_path / "cache"))[-1]
    assert ricevuta["waiting"] == 5 and ricevuta["status"] == "ok"
    assert set(stato(conn).values()) == {"pending"}
    assert stages.count_pending(conn, "solve") == 5

    # e quando ASTAP arriva, si risolvono davvero
    assert corri(conn, solver(), cache=tmp_path / "cache")["solved"] == 5
    conn.close()


def test_without_astap_nothing_is_prepared_for_a_launch_that_will_not_happen(
    db_path, archivio_letto, tmp_path, monkeypatch
):
    """Senza il solver ogni corsa ripassa le pose in attesa per chiedere alla cache, e basta: il
    cielo di una sorella da suggerire e la pulizia dei file di esito servono a un lancio che non
    ci sara', e costavano piu' della cache stessa a ogni Avvia e a ogni giro del NAS."""
    conn = connect(db_path)
    chiesti = []
    # il suggerimento si chiede a `_hint_for`: le pose di prova hanno le coordinate nell'header,
    # quindi la sorella non si cercherebbe comunque
    monkeypatch.setattr(solve, "_hint_for", lambda *a: chiesti.append("suggerimento"))
    monkeypatch.setattr(solve, "_forget", lambda *a: chiesti.append("pulizia"))
    assert list(solve_frames(conn, exe=None, cache=tmp_path / "cache"))[-1]["waiting"] == 5
    assert chiesti == []
    conn.close()


def test_without_astap_the_cache_still_answers(db_path, archivio_letto, tmp_path):
    """Il ripasso senza solver c'e' per la cache: dopo un azzeramento del database le pose gia'
    risolte ritrovano il loro cielo da li', anche se ASTAP non c'e'."""
    conn = connect(db_path)
    cache = tmp_path / "cache"
    corri(conn, solver(), cache=cache)
    stages.invalidate(conn, [r[0] for r in conn.execute("SELECT id FROM frames")], "solve")
    assert list(solve_frames(conn, exe=None, cache=cache))[-1]["cached"] == 5
    conn.close()


def test_a_crooked_result_from_yesterday_is_thrown_away_before_astap_runs(
    db_path, archivio_letto, tmp_path
):
    """Un esito rimasto storto si butta prima di lanciare ASTAP: se ASTAP fallisse senza scrivere,
    l'app rileggerebbe quello di ieri -- e uno che dice "manca il catalogo stellare" fermerebbe la
    corsa intera. Finche' non parte nessun lancio, invece, resta dov'e', innocuo: la cache lo legge
    e lo scarta."""
    conn = connect(db_path)
    cache = tmp_path / "cache"
    (cache / "solve").mkdir(parents=True)
    frame_hash = conn.execute("SELECT frame_hash FROM frames ORDER BY id LIMIT 1").fetchone()[0]
    storto = cache / "solve" / f"{frame_hash}.ini"
    storto.write_text("PLTSOLVD=F\nERROR=No star database found.\n", encoding="utf-8")
    list(solve_frames(conn, exe=None, cache=cache))
    assert storto.exists()
    ricevuta = corri(conn, solver(esiti=dict.fromkeys(range(5))), cache=cache)  # non scrive
    assert (ricevuta["status"], ricevuta["unsolved"]) == ("ok", 5)
    conn.close()
