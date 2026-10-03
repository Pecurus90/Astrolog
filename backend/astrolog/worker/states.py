"""Worker states, which are also the per-stage states (one vocabulary), and the stage contract."""

import logging
from collections.abc import Callable, Mapping
from typing import Any

from ..spine.stage_run import Factory

log = logging.getLogger(__name__)

IDLE = "idle"
RUNNING = "running"
STOPPED = "stopped"
COMPLETED = "completed"
COMPLETED_WITH_ERRORS = "completed_with_errors"
ERROR = "error"
NOT_RUN = "not_run"

TERMINAL_STATES = frozenset({COMPLETED, COMPLETED_WITH_ERRORS, ERROR, STOPPED})

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


def blank_record(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "state": NOT_RUN,
        "current": None,
        "total": None,
        "tally": {},
        "last_event": None,
    }
