"""Gli stati del worker (che sono anche gli stati per stadio: un vocabolario solo) e il
contratto di uno stadio.

Vincolo non ovvio: `factory` restituisce un generatore FRESCO a ogni corsa, che emette dict
di avanzamento e chiude con `{done: True}`; `on_finish` gira esattamente una volta, comunque
vada, anche se lo stadio non parte mai (un lock non puo' restare orfano).
"""

import logging

log = logging.getLogger(__name__)

IDLE = "idle"
RUNNING = "running"
STOPPED = "stopped"
COMPLETED = "completed"
COMPLETED_WITH_ERRORS = "completed_with_errors"
ERROR = "error"
NOT_RUN = "not_run"

TERMINAL_STATES = frozenset({COMPLETED, COMPLETED_WITH_ERRORS, ERROR, STOPPED})

# Le chiavi di posizione di un evento; tutto il resto e' il tally, che il worker trasporta
# senza conoscerne i nomi.
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
    """Uno stadio: nome, fabbrica del generatore, e il gancio `on_finish` per rilasciare."""

    __slots__ = ("name", "factory", "on_finish", "_finished")

    def __init__(self, name, factory, on_finish=None):
        self.name = name
        self.factory = factory
        self.on_finish = on_finish
        self._finished = False

    def finish(self):
        """Idempotente: la seconda chiamata non fa niente."""
        if self._finished:
            return
        self._finished = True
        if self.on_finish is None:
            return
        try:
            self.on_finish()
        except Exception:
            log.exception("worker: on_finish dello stadio %s fallito", self.name)


def tally_of(event):
    return {k: v for k, v in event.items() if k not in STRUCTURAL_KEYS}


def blank_record(name):
    return {
        "name": name,
        "state": NOT_RUN,
        "current": None,
        "total": None,
        "tally": {},
        "last_event": None,
    }
