"""L'unico scrittore lungo: stadi in ordine, uno alla volta; Stop cooperativo a transazione
chiusa; niente avvio da solo; un lavoro alla volta; i timbri; il rilascio comunque vada."""

import threading
import time

import pytest

from astrolog.worker.states import (
    COMPLETED,
    COMPLETED_WITH_ERRORS,
    ERROR,
    IDLE,
    NOT_RUN,
    RUNNING,
    STOPPED,
    Stage,
)
from astrolog.worker.worker import Worker, WorkerBusyError
from conftest import wait_until


def fake_stage(name, items, log, gate=None):
    def factory():
        def gen():
            for i in range(1, items + 1):
                log.append(f"{name}:{i}")
                if gate is not None:
                    gate.wait(2.0)
                yield {"current": i, "total": items, "processed": i}
            yield {"done": True, "total": items, "processed": items, "errors_detail": []}

        return gen()

    return Stage(name, factory)


def test_a_stage_that_aborted_is_not_reported_as_completed():
    """Uno stadio che si e' FERMATO da solo non e' "completato", e il suo motivo deve arrivare
    a chi legge lo stato.

    Senza questo, il solver che si ferma perche' ASTAP non ha il suo catalogo stellare diceva
    `current 1 / total 1`, stato "completato", zero risolte e **nessun motivo** -- su un
    archivio da cinquemila pose. Cioe' la corsa dichiarava di aver fatto tutto."""

    def factory():
        def gen():
            yield {"current": 1, "total": 1, "processed": 0}
            yield {
                "done": True,
                "status": "aborted",
                "reason": "no_star_database",
                "total": 1,
                "processed": 0,
                "errors_detail": [],
            }

        return gen()

    w = Worker()
    w.start([Stage("solve", factory)])
    w.join(5.0)
    stadio = w.snapshot()["stages"][0]
    assert (stadio["state"], stadio["reason"]) == (ERROR, "no_star_database")


def test_worker_events_stages_run_in_order_one_at_a_time():
    log = []
    w = Worker()
    w.start([fake_stage("scan", 3, log), fake_stage("solve", 2, log)])
    w.join(5.0)
    assert log == ["scan:1", "scan:2", "scan:3", "solve:1", "solve:2"]
    snap = w.snapshot()
    assert snap["state"] == COMPLETED
    assert [s["name"] for s in snap["stages"]] == ["scan", "solve"]
    assert all(s["state"] == COMPLETED for s in snap["stages"])
    assert snap["stages"][0]["tally"] == {"processed": 3}
    assert snap["stages"][0]["total"] == 3


def test_the_state_says_there_were_errors_without_carrying_them():
    """Lo stato del worker lo chiede la pagina della scansione ogni pochi secondi: dice che uno
    stadio e' finito con dei file non letti, ma non ne porta l'elenco, che puo' contarne migliaia.
    I file non letti si leggono a pagine dalla ricevuta scritta (`api/scan.py`)."""

    def factory():
        def gen():
            yield {"current": 1, "total": 1, "processed": 0}
            rotto = [{"file": "a.fits", "reason": "header_unreadable"}]
            yield {"done": True, "total": 1, "processed": 0, "errors_detail": rotto}

        return gen()

    w = Worker()
    w.start([Stage("scan", factory)])
    w.join(5.0)
    stadio = w.snapshot()["stages"][0]
    assert stadio["state"] == COMPLETED_WITH_ERRORS
    assert "errors_detail" not in stadio


def test_worker_stop_cooperative():
    log = []
    w = Worker()
    gate = threading.Event()

    def stopper():
        def gen():
            log.append("scan:1")
            yield {"current": 1, "total": 2, "processed": 1}
            w.stop()
            log.append("scan:2")
            yield {"current": 2, "total": 2, "processed": 2}
            yield {"done": True, "total": 2, "processed": 2, "errors_detail": []}

        return gen()

    w.start([Stage("scan", stopper), fake_stage("solve", 2, log, gate)])
    w.join(5.0)
    snap = w.snapshot()
    assert snap["state"] == STOPPED
    assert "solve:1" not in log  # fermare ferma, non trasforma
    assert snap["stages"][0]["state"] == STOPPED and snap["stages"][1]["state"] == NOT_RUN
    assert log == ["scan:1", "scan:2"]  # si ferma al confine dopo l'elemento in corso


def test_worker_no_autostart_and_stop_when_idle_is_a_noop():
    w = Worker()
    assert w.snapshot()["state"] == IDLE and not w.is_running()
    w.stop()
    assert w.snapshot()["state"] == IDLE
    log = []
    w.start([fake_stage("a", 2, log)])
    w.join(3.0)
    assert w.snapshot()["state"] == COMPLETED and len(log) == 2


def test_worker_one_job_at_a_time():
    log = []
    gate = threading.Event()
    w = Worker()
    w.start([fake_stage("scan", 2, log, gate)])
    assert wait_until(lambda: w.snapshot()["state"] == RUNNING)
    with pytest.raises(WorkerBusyError):
        w.start([fake_stage("altro", 1, log)])
    gate.set()
    w.join(5.0)
    assert "altro:1" not in log


def test_worker_on_finish_runs_once_even_if_the_stage_explodes():
    released = []
    w = Worker()

    def boom():
        def gen():
            yield {"current": 1, "total": 2}
            raise RuntimeError("boom")

        return gen()

    w.start([Stage("esplode", boom, on_finish=lambda: released.append("esplode")),
             Stage("mai", lambda: iter(()), on_finish=lambda: released.append("mai"))])  # fmt: skip
    w.join(5.0)
    assert released == ["esplode", "mai"] and w.snapshot()["state"] == ERROR


def test_worker_stamps_and_reset():
    w = Worker()
    assert w.snapshot()["started_at"] is None and w.snapshot()["ended_at"] is None
    w.start([Stage("noop", lambda: iter([{"done": True}]))])
    w.join(3.0)
    snap = w.snapshot()
    assert snap["started_at"] <= snap["ended_at"] and snap["ended_at"].endswith("Z")
    time.sleep(0.01)
    snap = w.reset()
    assert snap["state"] == IDLE and snap["started_at"] is None
