"""Il log strutturato (una riga JSON per evento), i percorsi dei dati, lo stato per frame
per stadio."""

import json
import logging

import pytest

from astrolog.db import paths
from astrolog.log import setup_logging
from astrolog.spine import group, identify, normalize, scan, solve
from astrolog.spine.stages import (
    SETTLED,
    STAGES,
    count_pending,
    mark_pending,
    ready,
    set_status,
)


def test_log_writes_one_json_line_per_event_with_extras(tmp_path):
    handler = setup_logging(tmp_path)
    try:
        logging.getLogger("astrolog.prova").warning("ciao", extra={"run_id": "abc", "n": 3})
        handler.flush()
    finally:
        logging.getLogger().removeHandler(handler)
        handler.close()
    lines = (tmp_path / "astrolog.log").read_text(encoding="utf-8").strip().splitlines()
    row = json.loads(lines[-1])
    assert row["msg"] == "ciao" and row["level"] == "WARNING" and row["logger"] == "astrolog.prova"
    assert row["run_id"] == "abc" and row["n"] == 3 and row["t"].endswith("+00:00")


def test_data_dir_honours_the_env_override_and_creates_the_tree(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTROLOG_DATA_DIR", str(tmp_path / "dati"))
    assert paths.data_dir() == tmp_path / "dati"
    assert paths.db_path() == tmp_path / "dati" / "astrolog.db"
    assert paths.cache_dir().is_dir() and paths.log_dir().is_dir()
    monkeypatch.delenv("ASTROLOG_DATA_ROOT", raising=False)
    assert paths.data_root() is None
    monkeypatch.setenv("ASTROLOG_DATA_ROOT", str(tmp_path))
    assert paths.data_root() == str(tmp_path.resolve())


def test_data_dir_default_is_per_user(monkeypatch):
    monkeypatch.delenv("ASTROLOG_DATA_DIR", raising=False)
    assert paths.data_dir().name == "AstroLog"


def test_stages_status_and_pending(conn):
    conn.execute(
        "INSERT INTO frames(frame_hash, image_type, header_json, created_at)"
        " VALUES('h1', 'light', '[]', 'now')"
    )
    mark_pending(conn, 1)
    assert ready(conn, "solve") == [1]
    set_status(conn, 1, "solve", "failed", reason="no_stars")
    assert count_pending(conn, "solve") == 0 and ready(conn, "solve", limit=5) == []
    row = conn.execute("SELECT status, reason FROM frame_stages WHERE stage = 'solve'").fetchone()
    assert (row["status"], row["reason"]) == ("failed", "no_stars")
    assert all(count_pending(conn, s) == 1 for s in STAGES if s != "solve")
    with pytest.raises(ValueError):
        set_status(conn, 1, "solve", "boh")


def _una_posa(conn):
    conn.execute(
        "INSERT INTO frames(frame_hash, image_type, header_json, created_at)"
        " VALUES('h1', 'light', '[]', 'now')"
    )
    mark_pending(conn, 1)
    return 1


def test_identify_runs_on_a_frame_the_solver_gave_up_on(conn):
    """Le due situazioni "niente cielo" del contratto esistono solo grazie a questa riga.

    Una posa non risolta resta `failed` per sempre, e finche' `ready` pretendeva `done` da ogni
    dipendenza `identify` non la vedeva mai: due delle otto situazioni non potevano accadere."""
    frame = _una_posa(conn)
    set_status(conn, frame, "normalize", "done")
    set_status(conn, frame, "solve", "failed", reason="no_solution")
    assert ready(conn, "identify") == [frame]


def test_identify_waits_for_a_frame_still_queued_at_the_solver(conn):
    """`failed` e' definitivo, `pending` no. Agganciare dal nome una posa che fra un minuto
    avra' il suo cielo sarebbe una risposta data in fretta -- ed e' esattamente cio' che
    succede quando ASTAP non e' ancora installato, che e' il primo avvio di chiunque."""
    frame = _una_posa(conn)
    set_status(conn, frame, "normalize", "done")
    assert ready(conn, "identify") == []


def test_the_exceptions_are_two_and_declared(conn):
    """Le eccezioni al "a monte dev'essere `done`" sono **due**, e nessuno stadio ne eredita
    una per sbaglio. Sono opposte, e vanno lette insieme:

    * `identify` parte su una posa che il solver ha **rinunciato** a risolvere, perche' da li'
      l'oggetto si aggancia dal nome -- senza, due delle otto situazioni non esisterebbero;
    * `group` vede anche una posa che `identify` ha **saltato**, non per raggrupparla (un
      oggetto che non c'e' non fa una sessione) ma per **fermarla col suo perche'**: se non
      arrivasse mai, resterebbe `pending` per sempre, e il residuo dello stadio non
      scenderebbe a zero -- il difetto che rende il pulsante Avvia una promessa a vuoto.

    `failed` invece non passa in nessuno dei due casi: e' un guasto, non una risposta."""
    assert set(SETTLED) == {("identify", "solve"), ("group", "identify")}
    frame = _una_posa(conn)
    set_status(conn, frame, "normalize", "done")
    set_status(conn, frame, "identify", "failed", reason="internal_error")
    assert ready(conn, "group") == []

    set_status(conn, frame, "identify", "skipped", reason="no_name_no_sky")
    assert ready(conn, "group") == [frame], "la posa saltata non arriva mai a fermarsi"


# Gli stadi che non esistono ancora. Non e' un elenco di comodo: e' cio' che fa diventare rossa
# la guardia qui sotto il giorno che uno nasce, invece di lasciarla passare su quattro voci
# scritte a mano che nessuno pensera' ad aggiornare.
STADI_CHE_DEVONO_NASCERE = ("measure",)


def test_no_stage_counter_collides_with_a_reserved_log_field():
    """Ogni stadio versa i suoi contatori nel log con `extra={**counts}`, e `logging` SOLLEVA se
    una chiave e' un campo suo. Non e' un difetto di log: la corsa intera si ferma, e si scopre
    solo mandando quello stadio fino in fondo -- il contatore `created` di `identify` ha fatto
    esattamente questo."""
    moduli = {"normalize": normalize, "solve": solve, "identify": identify, "group": group}
    assert set(moduli) | set(STADI_CHE_DEVONO_NASCERE) == set(STAGES)
    moduli["scan"] = scan  # non e' uno stadio del grafo per frame, ma versa i suoi contatori

    riservati = set(logging.LogRecord("n", 0, "p", 0, "m", None, None).__dict__) | {"message"}
    for stadio, modulo in moduli.items():
        assert not set(modulo.COUNTS) & riservati, stadio
