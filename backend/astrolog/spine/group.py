"""The `group` stage: frames into nights (`clock.night_date`, site's zone) and sessions (object x
night x rig). Where a frame was shot is asked, never guessed: nobody notices a misplaced night."""

import logging
import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from functools import partial

from ..clock import night_date, now_iso
from ..db.transaction import transaction
from ..place import by_distance, coordinates_key, distance_km
from . import declarations as decl
from . import gear_usage, mosaic
from . import group_store as store
from .stage_run import Event, FrameError, frame_safely, receipt, watched
from .stages import StageName, StageStatus, ready, set_status

log = logging.getLogger(__name__)

COUNTS = ("linked", "nights", "sessions", "waiting", "swept", "errors")

# Below this the header's coordinates and the site's are the same place: two decimals already
# move a coordinate by 1.1 km, and a consumer GPS errs by metres. Beyond it, ask.
SAME_PLACE_KM = 1.0


class GroupReason(StrEnum):
    """Why a frame stays out of a session: a code, never a sentence."""

    NO_ACTIVE_SITE = "no_active_site"  # the same code the settings already show
    SITE_NO_TIMEZONE = "site_no_timezone"  # and the same the site uses for a missing zone
    SITE_UNCLEAR = "site_unclear"
    NO_OBJECT = "no_object"
    NO_DATE = "no_date"


@dataclass(frozen=True, slots=True)
class _Placed:
    """Where a frame goes: the site, its night in the site's zone, whether the user said it."""

    site: sqlite3.Row
    night_date: str
    declared: bool


type Sites = tuple[sqlite3.Row | None, list[sqlite3.Row]]


def group_frames(conn: sqlite3.Connection) -> Iterator[Event]:
    """One event per frame, then the receipt."""
    counts: dict[str, int] = dict.fromkeys(COUNTS, 0)
    errors: list[FrameError] = []
    seen = 0

    def at_end() -> None:
        if seen:  # each piece's nights, only if some frame was worked
            gear_usage.write(conn)

    with watched(StageName.GROUP, counts, at_end):
        frame_ids = ready(conn, StageName.GROUP)
        store.detach(conn, frame_ids)
        # At the start, not the end: sky and rig are already decided, and a run stopped halfway
        # would leave grouped frames, no longer ready, that nobody would place.
        mosaic.place(conn, frame_ids)
        # read once per run: nobody writes sites during a run
        site, all_sites = store.home_site(conn), store.sites(conn)
        total = len(frame_ids)
        for frame_id in frame_ids:
            # one that meanwhile is no longer ready is skipped (`stages.ready`)
            if ready(conn, StageName.GROUP, frame_id=frame_id):
                work = partial(_one_frame, conn, frame_id, (site, all_sites), counts)
                frame_safely(conn, StageName.GROUP, frame_id, work, counts, errors)
            seen += 1
            yield {"current": seen, "total": total, **counts}
        counts["swept"] = _sweep(conn)
    yield receipt("ok", None, counts, errors, total=seen)


def _sweep(conn: sqlite3.Connection) -> int:
    """At the end, unlike `identify` which frees unique names: here sweeping first would delete a
    night and recreate it with a new id. Sessions first, or an emptied night stays a whole run."""
    dropped = store.drop_empty_sessions(conn)
    dropped += store.drop_empty_nights(conn)
    if dropped:
        log.info("group: sessioni e notti rimaste vuote, tolte", extra={"quante": dropped})
    return dropped


def _one_frame(
    conn: sqlite3.Connection, frame_id: int, known: Sites, counts: dict[str, int]
) -> None:
    frame = store.frame(conn, frame_id)
    now = now_iso()
    where = _where(conn, frame, known)
    with transaction(conn):
        if isinstance(where, GroupReason):
            set_status(conn, frame_id, StageName.GROUP, StageStatus.SKIPPED, reason=where, now=now)
            counts["waiting"] += 1
        else:
            night_id = _night(conn, where, now, counts)
            session_id = _session(conn, night_id, frame["object_id"], frame["rig_id"], counts)
            store.set_frame_group(conn, frame_id, night_id, session_id)
            set_status(conn, frame_id, StageName.GROUP, StageStatus.DONE, now=now)
            counts["linked"] += 1


def _where(conn: sqlite3.Connection, frame: sqlite3.Row, known: Sites) -> _Placed | GroupReason:
    """What the frame lacks before what the app lacks, or the user fixes the wrong thing. The
    user's answer for those coordinates beats a nearer site declared later."""
    home, all_sites = known
    if frame["object_id"] is None:
        return GroupReason.NO_OBJECT
    # without a zone, so "unreadable date" stays apart from "the site's zone does not exist"
    if night_date(frame["date_obs"]) is None:
        return GroupReason.NO_DATE
    lat, lon = frame["site_lat"], frame["site_lon"]
    away_km = None if home is None else distance_km(lat, lon, home["latitude"], home["longitude"])
    if home is not None and (away_km is None or away_km <= SAME_PLACE_KM):
        return _with_timezone(home, frame, answered=False)
    if None in (lat, lon):
        return GroupReason.NO_ACTIVE_SITE
    said_site = decl.site_for_coordinates(conn, coordinates_key(lat, lon))
    if said_site:
        site = store.site_by_name(conn, said_site)
        if site is None:
            # The declared site was deleted or renamed: ask again rather than fall back on home.
            return GroupReason.SITE_UNCLEAR
        return _with_timezone(site, frame, answered=True)
    near = [s for km, s in by_distance(lat, lon, all_sites) if km <= SAME_PLACE_KM]
    if near:
        return _with_timezone(near[0], frame, answered=False)
    return GroupReason.SITE_UNCLEAR if home is not None else GroupReason.NO_ACTIVE_SITE


def _with_timezone(
    site: sqlite3.Row, frame: sqlite3.Row, *, answered: bool
) -> _Placed | GroupReason:
    date = night_date(frame["date_obs"], site["timezone"]) if site["timezone"] else None
    if date is None:
        return GroupReason.SITE_NO_TIMEZONE
    return _Placed(site, date, answered)


def _night(conn: sqlite3.Connection, placed: _Placed, now: str, counts: dict[str, int]) -> int:
    """`declared` when the site came from the user's answer, even "I was home": such a night is
    moved by nobody, neither a home move nor the sweep."""
    site_id = placed.site["id"]
    row = store.night(conn, site_id, placed.night_date)
    if row is not None:
        return row["id"]
    counts["nights"] += 1
    return store.create_night(conn, site_id, placed.night_date, now, declared=placed.declared)


def _session(
    conn: sqlite3.Connection,
    night_id: int,
    object_id: int,
    rig_id: int | None,
    counts: dict[str, int],
) -> int:
    row = store.session(conn, night_id, object_id, rig_id)
    if row is not None:
        return row["id"]
    counts["sessions"] += 1
    return store.create_session(conn, night_id, object_id, rig_id)
