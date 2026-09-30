"""La corsa di uno stadio che lavora posa per posa, scritta una volta: la guardia della posa, lo
scheletro della corsa e la ricevuta che worker e pagina leggono.

Vincolo non ovvio: una posa rotta si segna `failed` e la corsa continua, un guasto fuori da una
posa la ferma; e cio' che le pose lavorate hanno spostato si riscrive in ogni caso, anche a corsa
fermata o rotta. La transazione di una posa sta in `db/transaction.py`; l'ordine degli stadi, in
`spine/run.py`.
"""

import logging
from contextlib import contextmanager

from .stages import set_status

log = logging.getLogger(__name__)


def frame_safely(conn, stage, frame_id, work, counts, errors):  # noqa: PLR0913
    """Cio' che torna `work()`, o None se la posa si e' rotta: allora e' segnata `failed` col suo
    perche', contata in `counts["errors"]` e messa in `errors`."""
    try:
        return work()
    except Exception as err:  # noqa: BLE001 - il guasto e' della posa, non della corsa
        set_status(conn, frame_id, stage, "failed", reason="internal_error")
        log.exception("%s: posa non lavorata", stage, extra={"frame_id": frame_id})
        counts["errors"] += 1
        errors.append({"frame_id": frame_id, "reason": f"{type(err).__name__}: {err}"})
        return None


@contextmanager
def watched(stage, counts, at_end, **start):
    """Il corpo di una corsa: `at_end()` gira comunque -- finita, fermata dall'utente o rotta.
    `start` va nella riga di log d'inizio; lo stato che la corsa scrive in cio' che riceve va in
    quella di fine."""
    log.info("%s: inizio", stage, extra=start)
    outcome = {"status": "ok"}
    try:
        yield outcome
    except GeneratorExit:
        log.info("%s: fermato", stage, extra={**counts})
        raise
    except Exception:
        log.exception("%s: errore di sistema", stage, extra={**counts})
        raise
    finally:
        at_end()
    log.info("%s: fine", stage, extra={**outcome, **counts})


def receipt(status, reason, counts, errors, **extra):
    """L'ultimo evento di una corsa: il worker si ferma al primo `done` che vede."""
    return {
        "done": True,
        "status": status,
        "reason": reason,
        **counts,
        "errors_detail": list(errors),
        **extra,
    }
