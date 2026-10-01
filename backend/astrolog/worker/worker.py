"""State is volatile by choice: after a stop the next run resumes from what the DB lacks."""

import logging
import threading
from collections.abc import Mapping, Sequence
from typing import Any

from ..clock import now_iso
from .states import (
    COMPLETED,
    COMPLETED_WITH_ERRORS,
    ERROR,
    IDLE,
    RUNNING,
    STOPPED,
    Stage,
    blank_record,
    tally_of,
)

log = logging.getLogger(__name__)


class WorkerBusyError(RuntimeError):
    """A job is already running: the caller is told, rather than queued invisibly."""


class Worker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._state = IDLE
        self._stage: str | None = None
        self._stages: list[dict[str, Any]] = []
        self._error: str | None = None
        self._stop_flag = False
        self._started_at: str | None = None
        self._ended_at: str | None = None

    def start(self, stages: Sequence[Stage]) -> dict[str, Any]:
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

    def stop(self) -> dict[str, Any]:
        """Picked up at the next boundary between items."""
        with self._lock:
            self._stop_flag = True
            return self._snapshot_locked()

    def reset(self) -> dict[str, Any]:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                raise RuntimeError("reset con un lavoro in corso")
            self.__init__()  # noqa: PLC2801 - back to a fresh state, lock included
            return self._snapshot_locked()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return self._snapshot_locked()

    def is_running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def stage_record(self, name: str) -> dict[str, Any] | None:
        """A copy: the live record changes under the lock, the caller reads it outside."""
        with self._lock:
            rec = self._record(name)
            return None if rec is None else dict(rec, tally=dict(rec["tally"]))

    def join(self, timeout: float | None = None) -> None:
        t = self._thread
        if t is not None:
            t.join(timeout)

    def _snapshot_locked(self) -> dict[str, Any]:
        snap: dict[str, Any] = {
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

    def _record(self, name: str) -> dict[str, Any] | None:
        for r in self._stages:
            if r["name"] == name:
                return r
        return None

    def _set_stage_state(self, name: str, state: str) -> None:
        with self._lock:
            rec = self._record(name)
            if rec is not None:
                rec["state"] = state

    def _stop_requested(self) -> bool:
        with self._lock:
            return self._stop_flag

    def _apply_progress(self, name: str, event: Mapping[str, Any]) -> None:
        with self._lock:
            rec = self._record(name)
            if rec is not None:
                rec["current"] = event.get("current")
                rec["total"] = event.get("total")
                rec["tally"] = tally_of(event)
                rec["last_event"] = event

    def _finish_stage(self, name: str, event: Mapping[str, Any]) -> None:
        with self._lock:
            rec = self._record(name)
            if rec is None:
                return
            rec["tally"] = tally_of(event)
            rec["total"] = event.get("total")
            rec["current"] = event.get("total")
            rec["reason"] = event.get("reason")
            # A stage that stopped itself is not "completed": current is set to total, so the
            # receipt would read done with nothing processed.
            if event.get("status") == "aborted":
                rec["state"] = ERROR
            else:
                # The state only flags that errors exist: the page polls it often and pages the
                # unread files from the written receipt (`api/scan.py`).
                rec["state"] = COMPLETED_WITH_ERRORS if event.get("errors_detail") else COMPLETED

    def _run_stage(self, stage: Stage) -> bool:
        """False when stopped. The generator is closed, then released, and only then is the
        terminal state published."""
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

    def _run(self, stages: list[Stage]) -> None:
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

    def _finish(self, state: str, error: str | None = None) -> None:
        with self._lock:
            self._state = state
            self._stage = None
            self._ended_at = now_iso()
            if error is not None:
                self._error = error

    def _finish_from_stages(self) -> None:
        with self._lock:
            worst = COMPLETED
            for rec in self._stages:
                if rec["state"] == COMPLETED_WITH_ERRORS:
                    worst = COMPLETED_WITH_ERRORS
            self._state = worst
            self._stage = None
            self._ended_at = now_iso()
