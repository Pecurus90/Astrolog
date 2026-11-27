"""La lettura nella catena degli stadi (`spine/run.py`): una cartella o tante in uno stadio solo,
una ricevuta sola alla fine coi conti sommati e il primo guasto, e chi ascolta quando una cartella
comincia. La lettura vera la da' l'app; qui una finta, che dice cosa si aspetta."""

import pytest

from astrolog.spine import run
from astrolog.spine.scan_store import COUNTS
from astrolog.spine.stages import StageName


def _lettura(esiti):
    """Per ogni cartella un evento di avanzamento e la sua ricevuta; una cartella senza esito non
    comincia mai."""

    def leggi(_conn, folder_id, run_id):
        fine = esiti.get(folder_id)
        if fine is None:
            return
        yield {"current": 1, "folder_id": folder_id, "run_id": run_id}
        yield {"done": True, **fine}

    return leggi


def _scansione(passi):
    nome, fabbrica = passi[0]
    assert nome == StageName.SCAN
    return list(fabbrica())


def test_many_folders_end_in_one_receipt_with_the_sums_and_the_first_fault(db_path):
    """Le ricevute delle cartelle diventano una: i conti si sommano (un conto che una cartella non
    dice vale zero), i file non letti si mettono in fila, e l'esito e' il primo guasto -- una
    cartella che muore a meta' non si legge come "fatto"."""
    esiti = {
        1: {"status": "ok", "reason": None, "found": 3, "new": 2,
            "errors_detail": [{"file": "a.fits", "reason": "file_unreadable"}]},
        2: {"status": "aborted", "reason": "root_unreachable", "found": 1},
        3: {"status": "error", "reason": "database_error", "found": 4,
            "errors_detail": [{"file": "b.fits", "reason": "header_unreadable"}]},
    }  # fmt: skip
    cominciate = []
    passi = run.queue_folders(
        db_path, [(1, 11), (2, 12), (3, 13)], _lettura(esiti),
        on_folder=lambda f, r: cominciate.append((f, r)),
    )  # fmt: skip
    eventi = _scansione(passi)
    fine = eventi[-1]
    assert [e["folder_id"] for e in eventi[:-1]] == [1, 2, 3]
    assert cominciate == [(1, 11), (2, 12), (3, 13)]
    assert (fine["status"], fine["reason"]) == ("aborted", "root_unreachable")
    assert {k: fine[k] for k in COUNTS} == dict.fromkeys(COUNTS, 0) | {"found": 8, "new": 2}
    assert [e["file"] for e in fine["errors_detail"]] == ["a.fits", "b.fits"]


def test_a_folder_whose_reading_never_begins_is_not_heard(db_path):
    """Una cartella la cui lettura non comincia nemmeno non si annuncia, e la corsa va avanti."""
    cominciate = []
    esiti = {2: {"status": "ok", "reason": None}}
    passi = run.queue_folders(
        db_path, [(1, 11), (2, 12)], _lettura(esiti),
        on_folder=lambda f, r: cominciate.append((f, r)),
    )  # fmt: skip
    assert _scansione(passi)[-1]["status"] == "ok"
    assert cominciate == [(2, 12)]


def test_no_folder_to_read_is_the_callers_mistake(db_path):
    with pytest.raises(ValueError, match="^nessuna cartella da leggere$"):
        run.queue_folders(db_path, [], _lettura({}))


@pytest.mark.parametrize(
    ("folder_id", "run_id", "con_lettura"),
    [(None, 11, True), (1, None, True), (1, 11, False), (None, None, False)],
)
def test_one_folder_asks_for_everything_its_reading_needs(db_path, folder_id, run_id, con_lettura):
    """Lo stadio della lettura vuole la cartella, la ricevuta e il lavoro: senza uno dei tre si
    rompe qui, non dopo nel thread del worker in silenzio."""
    lettura = run.Reading(_lettura({})) if con_lettura else None
    with pytest.raises(ValueError, match="^scan vuole folder_id, run_id e il lavoro"):
        run.queue(db_path, [StageName.SCAN], folder_id=folder_id, run_id=run_id, scan=lettura)


def test_one_folder_is_heard_when_its_reading_begins(db_path):
    """Una cartella sola: chi ascolta sente quando la lettura comincia."""
    cominciate = []
    esiti = {1: {"status": "ok", "reason": None}}
    lettura = run.Reading(_lettura(esiti), lambda f, r: cominciate.append((f, r)))
    passi = run.queue(db_path, [StageName.SCAN], folder_id=1, run_id=11, scan=lettura)
    assert _scansione(passi)[-1]["done"] is True
    assert cominciate == [(1, 11)]
