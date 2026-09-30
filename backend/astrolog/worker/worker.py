"""Il worker: una lista ordinata di stadi in un thread, uno alla volta; Stop cooperativo fra
un elemento e l'altro; snapshot sotto lock; timbri della corsa.

Vincolo non ovvio: lo stato e' volatile per scelta (dopo uno stop si riparte da cio' che
manca nel DB); non riparte mai da solo; un lavoro alla volta -- chi trova il worker
occupato riceve `WorkerBusyError`, non una coda invisibile.
"""

import logging
import threading

from ..clock import now_iso
from .states import (
    COMPLETED,
    COMPLETED_WITH_ERRORS,
    ERROR,
    IDLE,
    RUNNING,
    STOPPED,
    blank_record,
    tally_of,
)

log = logging.getLogger(__name__)


class WorkerBusyError(RuntimeError):
    """Un lavoro e' gia' in corso."""


class Worker:
    def __init__(self):
        self._lock = threading.Lock()
        self._thread = None
        self._state = IDLE
        self._stage = None
        self._stages = []
        self._error = None
        self._stop_flag = False
        self._started_at = None
        self._ended_at = None

    # -- API ------------------------------------------------------------------------

    def start(self, stages):
        """Avvia la corsa; `WorkerBusyError` se una e' gia' in corso. Ritorna lo snapshot."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                raise WorkerBusyError("un lavoro di sottofondo e' gia' in corso")
            self._state = RUNNING
            self._stage = None
            self._stages = [blank_record(s.name) for s in stages]
            self._error = None
            self._stop_flag = False
            self._started_at = now_iso()
            t = threading.Thread(
                target=self._run, args=(list(stages),), name="astrolog-worker", daemon=True
            )
            self._thread = t
            t.start()
            return self._snapshot_locked()

    def stop(self):
        """Chiede lo stop: il ciclo lo raccoglie al prossimo confine fra elementi."""
        with self._lock:
            self._stop_flag = True
            return self._snapshot_locked()

    def reset(self):
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                raise RuntimeError("reset con un lavoro in corso")
            self.__init__()  # noqa: PLC2801 - lo stato torna a nuovo, stesso lock nuovo
            return self._snapshot_locked()

    def snapshot(self):
        with self._lock:
            return self._snapshot_locked()

    def is_running(self):
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def stage_record(self, name):
        """Il record (copia) dello stadio `name` nella corsa corrente, o None."""
        with self._lock:
            rec = self._record(name)
            return None if rec is None else dict(rec, tally=dict(rec["tally"]))

    def join(self, timeout=None):
        t = self._thread
        if t is not None:
            t.join(timeout)

    # -- interno --------------------------------------------------------------------

    def _snapshot_locked(self):
        snap = {
            "state": self._state,
            "stage": self._stage,
            "started_at": self._started_at,
            "ended_at": self._ended_at,
            "stages": [
                {
                    "name": r["name"],
                    "state": r["state"],
                    "current": r["current"],
                    "total": r["total"],
                    "tally": dict(r["tally"]),
                    "reason": r.get("reason"),
                }
                for r in self._stages
            ],
        }
        if self._error is not None:
            snap["error"] = self._error
        return snap

    def _record(self, name):
        for r in self._stages:
            if r["name"] == name:
                return r
        return None

    def _set_stage_state(self, name, state):
        with self._lock:
            rec = self._record(name)
            if rec is not None:
                rec["state"] = state

    def _stop_requested(self):
        with self._lock:
            return self._stop_flag

    def _apply_progress(self, name, event):
        with self._lock:
            rec = self._record(name)
            if rec is not None:
                rec["current"] = event.get("current")
                rec["total"] = event.get("total")
                rec["tally"] = tally_of(event)
                rec["last_event"] = event

    def _finish_stage(self, name, event):
        with self._lock:
            rec = self._record(name)
            if rec is None:
                return
            rec["tally"] = tally_of(event)
            rec["total"] = event.get("total")
            rec["current"] = event.get("total")
            rec["reason"] = event.get("reason")
            # Uno stadio che si e' FERMATO da solo non e' "completato": senza questa riga la
            # ricevuta diceva `current 1 / total 1`, zero risolte e nessun motivo, su un
            # archivio da cinquemila pose. Per la lettura dei file, finita, l'esito che la pagina
            # mostra non e' questo: lo dicono le ricevute di tutte le cartelle (`api/pipeline.py`).
            if event.get("status") == "aborted":
                rec["state"] = ERROR
            else:
                # dei file non letti lo stato dice solo che ci sono: la pagina lo chiede ogni pochi
                # secondi, e i file li legge a pagine dalla ricevuta scritta (`api/scan.py`)
                rec["state"] = COMPLETED_WITH_ERRORS if event.get("errors_detail") else COMPLETED

    def _run_stage(self, stage):
        """Consuma il generatore; False se ci si e' fermati su Stop. Prima si chiude il
        generatore, poi si rilascia, e solo alla fine si pubblica lo stato terminale."""
        gen = stage.factory()
        done_event, stopped = None, False
        try:
            self._set_stage_state(stage.name, RUNNING)
            if self._stop_requested():
                stopped = True
            else:
                for event in gen:
                    if event.get("done"):
                        done_event = event
                        break
                    self._apply_progress(stage.name, event)
                    if self._stop_requested():
                        stopped = True
                        break
        finally:
            gen.close()
            stage.finish()
        if stopped:
            self._set_stage_state(stage.name, STOPPED)
            return False
        if done_event is not None:
            self._finish_stage(stage.name, done_event)
        else:
            self._set_stage_state(stage.name, COMPLETED)
        return True

    def _run(self, stages):
        try:
            for stage in stages:
                if self._stop_requested():
                    self._finish(STOPPED)
                    return
                with self._lock:
                    self._stage = stage.name
                if not self._run_stage(stage):
                    self._finish(STOPPED)
                    return
            self._finish_from_stages()
        except Exception as err:
            log.exception("worker: errore di sistema, corsa interrotta")
            with self._lock:
                rec = self._record(self._stage) if self._stage else None
                if rec is not None and rec["state"] == RUNNING:
                    rec["state"] = ERROR
            self._finish(ERROR, error=str(err))
        finally:
            for stage in stages:
                stage.finish()

    def _finish(self, state, error=None):
        with self._lock:
            self._state = state
            self._stage = None
            self._ended_at = now_iso()
            if error is not None:
                self._error = error

    def _finish_from_stages(self):
        with self._lock:
            worst = COMPLETED
            for rec in self._stages:
                if rec["state"] == COMPLETED_WITH_ERRORS:
                    worst = COMPLETED_WITH_ERRORS
            self._state = worst
            self._stage = None
            self._ended_at = now_iso()
