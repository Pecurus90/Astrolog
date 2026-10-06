"""State is volatile by choice: after a stop the next run resumes from what the DB lacks. The
worker states are also the per-stage states: one vocabulary."""

import logging
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any

from ..clock import now_iso
from ..spine.stage_run import Factory

log = logging.getLogger(__name__)


class State(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPED = "stopped"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    ERROR = "error"
    NOT_RUN = "not_run"


TERMINAL_STATES = frozenset(
    {State.COMPLETED, State.COMPLETED_WITH_ERRORS, State.ERROR, State.STOPPED}
)

# The position keys of an event; everything else is the tally, carried without knowing its names.
STRUCTURAL_KEYS = frozenset(
    {
        "current",
        "total",
        "done",
        "file",
        "status",
        "reason",
        "errors_detail",
        "skipped_by_reason",
        "unreadable_dirs",
        "hidden_dirs",
        "linked_dirs",
        "run_id",
        "folder_id",
    }
)


class Stage:
    """`factory` gives a fresh generator per run, yielding progress and ending with `{done: True}`;
    `on_finish` runs exactly once, even if the stage never starts: a lock must not be orphaned."""

    __slots__ = ("name", "factory", "on_finish", "_finished")

    def __init__(
        self,
        name: str,
        factory: Factory,
        on_finish: Callable[[], object] | None = None,
    ) -> None:
        self.name = name
        self.factory = factory
        self.on_finish = on_finish
        self._finished = False

    def finish(self) -> None:
        """Idempotent."""
        if self._finished:
            return
        self._finished = True
        if self.on_finish is None:
            return
        try:
            self.on_finish()
        except Exception:
            log.exception("worker: on_finish dello stadio %s fallito", self.name)


def tally_of(event: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in event.items() if k not in STRUCTURAL_KEYS}


@dataclass(frozen=True, slots=True)
class StageRecord:
    """Replaced whole under the lock, never changed in place: a reader outside it holds a copy."""

    name: str
    state: State = State.NOT_RUN
    current: int | None = None
    total: int | None = None
    tally: Mapping[str, Any] = field(default_factory=dict)
    last_event: Mapping[str, Any] | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class Snapshot:
    state: State
    stage: str | None
    started_at: str | None
    ended_at: str | None
    stages: tuple[StageRecord, ...]
    error: str | None = None


class WorkerBusyError(RuntimeError):
    """A job is already running: the caller is told, rather than queued invisibly."""


class Worker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._state = State.IDLE
        self._stage: str | None = None
        self._stages: list[StageRecord] = []
        self._error: str | None = None
        self._stop_flag = False
        self._started_at: str | None = None
        self._ended_at: str | None = None

    def start(self, stages: Sequence[Stage]) -> Snapshot:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                raise WorkerBusyError("un lavoro di sottofondo e' gia' in corso")
            self._state = State.RUNNING
            self._stage = None
            self._stages = [StageRecord(s.name) for s in stages]
            self._error = None
            self._stop_flag = False
            self._started_at = now_iso()
            t = threading.Thread(
                target=self._run, args=(list(stages),), name="astrolog-worker", daemon=True
            )
            self._thread = t
            t.start()
            return self._snapshot_locked()

    def stop(self) -> Snapshot:
        """Picked up at the next boundary between items."""
        with self._lock:
            self._stop_flag = True
            return self._snapshot_locked()

    def reset(self) -> Snapshot:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                raise RuntimeError("reset con un lavoro in corso")
            self.__init__()  # noqa: PLC2801 - back to a fresh state, lock included
            return self._snapshot_locked()

    def snapshot(self) -> Snapshot:
        with self._lock:
            return self._snapshot_locked()

    def is_running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def stage_record(self, name: str) -> StageRecord | None:
        with self._lock:
            return self._record(name)

    def join(self, timeout: float | None = None) -> None:
        t = self._thread
        if t is not None:
            t.join(timeout)

    def _snapshot_locked(self) -> Snapshot:
        return Snapshot(
            state=self._state,
            stage=self._stage,
            started_at=self._started_at,
            ended_at=self._ended_at,
            stages=tuple(self._stages),
            error=self._error,
        )

    def _record(self, name: str) -> StageRecord | None:
        for r in self._stages:
            if r.name == name:
                return r
        return None

    def _update(self, name: str, **changes: Any) -> None:
        """Under the lock, held by the caller."""
        for i, r in enumerate(self._stages):
            if r.name == name:
                self._stages[i] = replace(r, **changes)
                return

    def _set_stage_state(self, name: str, state: State) -> None:
        with self._lock:
            self._update(name, state=state)

    def _stop_requested(self) -> bool:
        with self._lock:
            return self._stop_flag

    def _apply_progress(self, name: str, event: Mapping[str, Any]) -> None:
        with self._lock:
            self._update(
                name,
                current=event.get("current"),
                total=event.get("total"),
                tally=tally_of(event),
                last_event=event,
            )

    def _finish_stage(self, name: str, event: Mapping[str, Any]) -> None:
        # A stage that stopped itself is not "completed": current is set to total, so the
        # receipt would read done with nothing processed.
        if event.get("status") == "aborted":
            state = State.ERROR
        else:
            # The state only flags that errors exist: the page polls it often and pages the
            # unread files from the written receipt (`api/scan.py`).
            state = State.COMPLETED_WITH_ERRORS if event.get("errors_detail") else State.COMPLETED
        with self._lock:
            self._update(
                name,
                tally=tally_of(event),
                total=event.get("total"),
                current=event.get("total"),
                reason=event.get("reason"),
                state=state,
            )

    def _run_stage(self, stage: Stage) -> bool:
        """False when stopped. The generator is closed, then released, and only then is the
        terminal state published."""
        gen = stage.factory()
        done_event, stopped = None, False
        try:
            self._set_stage_state(stage.name, State.RUNNING)
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
            self._set_stage_state(stage.name, State.STOPPED)
            return False
        if done_event is not None:
            self._finish_stage(stage.name, done_event)
        else:
            self._set_stage_state(stage.name, State.COMPLETED)
        return True

    def _run(self, stages: list[Stage]) -> None:
        try:
            for stage in stages:
                if self._stop_requested():
                    self._finish(State.STOPPED)
                    return
                with self._lock:
                    self._stage = stage.name
                if not self._run_stage(stage):
                    self._finish(State.STOPPED)
                    return
            self._finish_from_stages()
        except Exception as err:
            log.exception("worker: errore di sistema, corsa interrotta")
            with self._lock:
                rec = self._record(self._stage) if self._stage else None
                if rec is not None and rec.state == State.RUNNING:
                    self._update(rec.name, state=State.ERROR)
            self._finish(State.ERROR, error=str(err))
        finally:
            for stage in stages:
                stage.finish()

    def _finish(self, state: State, error: str | None = None) -> None:
        with self._lock:
            self._state = state
            self._stage = None
            self._ended_at = now_iso()
            if error is not None:
                self._error = error

    def _finish_from_stages(self) -> None:
        with self._lock:
            worst = State.COMPLETED
            for rec in self._stages:
                if rec.state == State.COMPLETED_WITH_ERRORS:
                    worst = State.COMPLETED_WITH_ERRORS
            self._state = worst
            self._stage = None
            self._ended_at = now_iso()
