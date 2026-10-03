"""The run of a frame-by-frame stage, written once: a broken frame fails alone, a fault outside a
frame stops the run, and what the frames moved is rewritten even after a stop or a crash."""

import logging
import sqlite3
from collections.abc import Callable, Generator, Iterable, Iterator, Mapping
from contextlib import contextmanager
from typing import Any

from .stages import set_status

log = logging.getLogger(__name__)

type Event = dict[str, Any]
type Factory = Callable[[], Generator[Event]]
type FrameError = dict[str, int | str]


def frame_safely[T](  # noqa: PLR0913
    conn: sqlite3.Connection,
    stage: str,
    frame_id: int,
    work: Callable[[], T],
    counts: dict[str, int],
    errors: list[FrameError],
) -> T | None:
    """None if the frame broke: it is then marked `failed` with its reason and counted."""
    try:
        return work()
    except Exception as err:  # noqa: BLE001 - the fault is the frame's, not the run's
        set_status(conn, frame_id, stage, "failed", reason="internal_error")
        log.exception("%s: posa non lavorata", stage, extra={"frame_id": frame_id})
        counts["errors"] += 1
        errors.append({"frame_id": frame_id, "reason": f"{type(err).__name__}: {err}"})
        return None


@contextmanager
def watched(
    stage: str, counts: Mapping[str, int], at_end: Callable[[], object], **start: object
) -> Iterator[dict[str, Any]]:
    """`at_end()` runs whether the run ends, is stopped or breaks. The status written into the
    yielded dict goes into the closing log line."""
    log.info("%s: inizio", stage, extra=start)
    outcome: dict[str, Any] = {"status": "ok"}
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


def receipt(
    status: str,
    reason: str | None,
    counts: Mapping[str, int],
    errors: Iterable[Mapping[str, Any]],
    **extra: object,
) -> Event:
    """The worker stops at the first event with `done`."""
    return {
        "done": True,
        "status": status,
        "reason": reason,
        **counts,
        "errors_detail": list(errors),
        **extra,
    }
