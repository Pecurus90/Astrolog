"""Header raw values to filters, instruments and rigs: learned rule, then vocabulary, then raw. What
stays raw is a question for the user, never a guess."""

import logging
import sqlite3
from collections.abc import Callable, Iterator
from functools import cache, partial
from typing import Any, NamedTuple, cast

from ..clock import now_iso
from ..db.transaction import transaction
from ..units import focal_buckets
from ..vocab.filters import (
    NO_FILTER_NAME,
    Passband,
    is_broadband_word,
    normalize_filter,
    passband_of,
)
from ..vocab.header_value import normalize_header_value
from ..vocab.software import normalize_software
from . import (
    camera_sky,
    camera_specs,
    copies,
    declarations,
    gear_usage,
    night_rig,
    rewrite,
    rigs,
    signature,
    typeless_folders,
    unfiltered,
)
from . import normalize_store as store
from .gear_create import create_filter, filter_id_by_name
from .normalize_rig import Given, Writing, instruments_on_frame, mount_for_frame, rig_for_frame
from .stage_run import Event, FrameError, frame_safely, receipt, watched
from .stages import StageName, StageStatus, invalidate, ready, set_status

log = logging.getLogger(__name__)

COUNTS = ("normalized", "filters", "instruments", "rigs", "copies", "to_review", "errors")

# camera name -> its voted colour
Colours = dict[str, str | None]


def normalize_frames(conn: sqlite3.Connection) -> Iterator[Event]:
    counts: dict[str, int] = dict.fromkeys(COUNTS, 0)
    errors: list[FrameError] = []
    seen = 0
    context: _Round | None = None

    def at_end() -> None:
        # once per run and only if a frame moved: the votes and counts are costly
        if seen:
            _at_round_end(conn, context.colours if context else None)
            gear_usage.write(conn)

    with watched(StageName.NORMALIZE, counts, at_end):
        frame_ids, context = _before_the_round(conn)
        for frame_id in frame_ids:
            work = partial(_one_frame, conn, frame_id, context, counts)
            counts["to_review"] += bool(
                frame_safely(conn, StageName.NORMALIZE, frame_id, work, counts, errors)
            )
            seen += 1
            yield {"current": seen, "total": len(frame_ids), **counts}
    yield receipt("ok", None, counts, errors, total=seen)


class _Round(NamedTuple):
    """Decided once before writing, so no frame is redone at the end because another moved it."""

    buckets: dict[float, float]
    cameras: dict[int, Given]
    copy_of: dict[int, int | None]
    marks: dict[int, rewrite.RewriteMark | None]
    colours: Colours


def _before_the_round(conn: sqlite3.Connection) -> tuple[list[int], _Round]:
    """Frames whose answers these decisions change join this same round."""
    frame_ids = ready(conn, StageName.NORMALIZE)
    if not frame_ids:
        return [], _Round({}, {}, {}, {}, {})
    # a frame that names the camera can change the one its night gives to frames that do not
    neighbours = set(night_rig.in_nights_of(conn, frame_ids)) - set(frame_ids)
    if neighbours:
        invalidate(conn, neighbours, StageName.NORMALIZE)
    frame_ids = ready(conn, StageName.NORMALIZE)
    copy_of, marks, redo = copies.decide(store.broods(conn, frame_ids), frame_ids)
    if redo:
        invalidate(conn, redo, StageName.NORMALIZE)
    frame_ids = ready(conn, StageName.NORMALIZE)
    nights = cache(lambda: night_rig.night_rigs(conn))
    answers = signature.answers(conn)
    cameras: dict[int, Given] = {}
    voting: list[tuple[str, bool]] = []
    for i in frame_ids:
        # one row at a time: only the camera and its vote stay, not the header
        frame = store.frame(conn, i)
        cameras[i] = _camera_of(conn, frame, nights, answers)
        camera = cameras[i].camera
        if camera and copy_of.get(i, frame["copy_of"]) is None:
            voting.append((camera, frame["bayer_pattern"] is not None))
    colours = camera_specs.ahead(conn, frame_ids, voting)
    # frames without a matrix of a camera that changed colour: only their filter changes
    for i in ready(conn, StageName.NORMALIZE):
        if i not in cameras:
            cameras[i] = _camera_of(conn, store.frame(conn, i), nights, answers)
            frame_ids.append(i)
    # all focals bucketed before writing, so 559, 560 and 561 give one rig in any file order
    buckets = focal_buckets(store.pending_focals(conn, frame_ids))
    return frame_ids, _Round(buckets, cameras, copy_of, marks, colours)


def _camera_of(
    conn: sqlite3.Connection,
    frame: sqlite3.Row,
    nights: Callable[[], Any],
    answers: signature.Answers,
) -> Given:
    """Where the header is silent the signature's answer, then the night, name the camera: from the
    rig alone those frames would get a filter nobody could ask them about."""
    camera = declarations.instrument_name(conn, "camera", frame["instrument_raw"])
    found = signature.answer_for(answers, signature.parts_of(frame))
    answered = found[1] if found else None
    night = None
    if camera is None and (answered is None or answered.camera is None):
        night = night_rig.rig_of_night(conn, frame, nights())
    camera = camera or (answered.camera if answered else None) or (night or {}).get("camera")
    return Given(camera, answered, night)


def _at_round_end(conn: sqlite3.Connection, colours: Colours | None) -> None:
    """What the frames moved: camera votes, sky pixels, empty rigs, folders asking for a type."""
    camera_specs.from_files(conn, colours)
    camera_sky.write(conn)
    rigs.drop_empty(conn)
    typeless_folders.write(conn)


def _one_frame(
    conn: sqlite3.Connection, frame_id: int, context: _Round, counts: dict[str, int]
) -> bool:
    """One frame, one transaction, so what is done stays done. True if it is left to review."""
    frame = store.frame(conn, frame_id)
    given = context.cameras[frame_id]
    now = now_iso()
    writing = Writing(counts, now, context.buckets)
    with transaction(conn):
        # software first: it says how `TELESCOP` is read, before any optics is built on it
        software = normalize_software(frame["software_raw"])
        filter_id, filter_known = _filter_for(conn, frame, writing, given, context.colours)
        rig_id = rig_for_frame(conn, frame, writing, given, software)
        carried = instruments_on_frame(conn, frame, counts, now)
        carried["mount"] = mount_for_frame(conn, frame, rig_id, software, counts, now)
        copy_of = context.copy_of.get(frame_id, frame["copy_of"])
        counts["copies"] += 1 if copy_of is not None else 0
        was = (frame["filter_id"], frame["rig_id"], frame["software"], frame["copy_of"])
        if (filter_id, rig_id, software, copy_of) != was:
            # these change the answers downstream: always through here, never a hand UPDATE
            invalidate(conn, [frame["id"]], StageName.NORMALIZE, now=now)
        mark = context.marks[frame_id] if frame_id in context.marks else rewrite.mark_of(frame)
        written = store.Normalized(filter_id, rig_id, software, copy_of, mark, carried)
        store.set_normalized(conn, frame["id"], written)
        set_status(conn, frame["id"], StageName.NORMALIZE, StageStatus.DONE, now=now)
        counts["normalized"] += 1
        return not filter_known or rig_id is None


def _filter_for(
    conn: sqlite3.Connection,
    frame: sqlite3.Row,
    writing: Writing,
    given: Given,
    colours: Colours,
) -> tuple[int | None, bool]:
    """(filter id, is it known?). A filter with an unknown band exists but is not known: it stays a
    question until answered."""
    counts, now, answered = writing.counts, writing.now, given.answer
    # colour belongs to the camera, not the frame: a program that omits `BAYERPAT` is not mono
    bayer = bool(frame["bayer_pattern"])
    colour = bayer or unfiltered.is_colour(conn, given.camera, colours)
    key = normalize_header_value(frame["filter_raw"])
    name = declarations.alias_target(conn, "filter", key) if key else None
    if name is not None:
        filter_id = filter_id_by_name(conn, name)
        # an answer on a word the vocabulary does not know (`Filtro1`) stays the user's
        broadband = colour and is_broadband_word(frame["filter_raw"])
        if filter_id is not None and not broadband:
            return filter_id, True
        if filter_id is None:
            # the rule points to a vanished filter: warn and fall back, since losing it silently is
            # worse; not recreated like an instrument, its band would be unknown
            log.warning(
                "normalize: regola verso un filtro sparito",
                extra={"filter": name, "frame_id": frame["id"]},
            )

    # without a Bayer matrix mono and colour look alike, and `none` may be an empty wheel slot: the
    # signature's answer says it. It speaks of a mono; on colour it is OSC anyway.
    if not colour and unfiltered.says_no_filter(frame["filter_raw"]):
        if answered is not None and answered.filter == signature.NO_FILTER:
            return _no_filter(conn, frame, now)
        if answered is not None and answered.filter_name:
            return _answered_filter(conn, frame, answered.filter_name, now)
        return None, False
    canonical = normalize_filter(frame["filter_raw"], bayer=colour)
    # the learned rule also applies to the vocabulary's name, or a renamed filter would be reborn
    kept = declarations.alias_target(conn, "filter", normalize_header_value(canonical or ""))
    if kept and (filter_id := filter_id_by_name(conn, kept)) is not None:
        return filter_id, True
    band = passband_of(canonical)
    # a silent filter returned above, and with a colour matrix it is at least OSC
    named = cast(str, canonical)
    filter_id = filter_id_by_name(conn, named)
    if filter_id is None:
        filter_id = create_filter(conn, named, band, now)
        counts["filters"] += 1
    return filter_id, band != Passband.UNKNOWN


def _answered_filter(
    conn: sqlite3.Connection, frame: sqlite3.Row, name: str, now: str
) -> tuple[int | None, bool]:
    filter_id = filter_id_by_name(conn, name)
    if filter_id is None:
        log.warning(
            "normalize: la risposta dice un filtro sparito",
            extra={"filter": name, "frame_id": frame["id"]},
        )
        return None, False
    return filter_id, True


def _no_filter(conn: sqlite3.Connection, frame: sqlite3.Row, now: str) -> tuple[int | None, bool]:
    """The "no filter" row, created when an answer first needs it; if its name already belongs to
    another filter, which one is meant is not guessed and the frame stays to review."""
    filter_id = store.none_filter_id(conn)
    if filter_id is not None:
        return filter_id, True
    if filter_id_by_name(conn, NO_FILTER_NAME) is not None:
        log.warning("normalize: nessun filtro, nome preso", extra={"frame_id": frame["id"]})
        return None, False
    filter_id = create_filter(conn, NO_FILTER_NAME, Passband.NO_FILTER, now, is_none=True)
    return filter_id, True
