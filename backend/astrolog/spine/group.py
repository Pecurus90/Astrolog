"""The `group` stage: frames into nights (noon to noon in the site's zone) and sessions (object x
night x rig). Where a frame was shot is asked, never guessed: nobody notices a misplaced night."""

import logging
import sqlite3
from collections.abc import Iterator
from functools import partial

from ..clock import night_date, now_iso
from ..db.transaction import transaction
from ..place import by_distance, coordinates_key, distance_km
from . import declarations as decl
from . import gear_usage, mosaic
from . import group_store as store
from .stage_run import Event, FrameError, frame_safely, receipt, watched
from .stages import ready, set_status

log = logging.getLogger(__name__)

COUNTS = ("linked", "nights", "sessions", "waiting", "swept", "errors")

# Below this the header's coordinates and the site's are the same place: two decimals already
# move a coordinate by 1.1 km, and a consumer GPS errs by metres. Beyond it, ask.
SAME_PLACE_KM = 1.0

# Why a frame stays out of a session: a code, never a sentence.
NO_ACTIVE_SITE = "no_active_site"  # the same code the settings already show
SITE_NO_TIMEZONE = "site_no_timezone"  # and the same the site uses for a missing zone
SITE_UNCLEAR = "site_unclear"
NO_OBJECT = "no_object"
NO_DATE = "no_date"

# (site row, whether the user said it, reason it stays out)
type Where = tuple[sqlite3.Row | None, bool | None, str | None]
type Sites = tuple[sqlite3.Row | None, list[sqlite3.Row]]


def group_frames(conn: sqlite3.Connection) -> Iterator[Event]:
    """One event per frame, then the receipt."""
    counts: dict[str, int] = dict.fromkeys(COUNTS, 0)
    errors: list[FrameError] = []
    seen = 0

    def at_end() -> None:
        if seen:  # each piece's nights, only if some frame was worked
            gear_usage.write(conn)

    with watched("group", counts, at_end):
        frame_ids = ready(conn, "group")
        store.detach(conn, frame_ids)
        # At the start, not the end: sky and rig are already decided, and a run stopped halfway
        # would leave grouped frames, no longer ready, that nobody would place.
        mosaic.place(conn, frame_ids)
        # read once per run: nobody writes sites during a run
        site, luoghi = store.home_site(conn), store.sites(conn)
        total = len(frame_ids)
        for frame_id in frame_ids:
            # one that meanwhile is no longer ready is skipped (`stages.ready`)
            if ready(conn, "group", frame_id=frame_id):
                work = partial(_one_frame, conn, frame_id, (site, luoghi), counts)
                frame_safely(conn, "group", frame_id, work, counts, errors)
            seen += 1
            yield {"current": seen, "total": total, **counts}
        counts["swept"] = _sweep(conn)
    yield receipt("ok", None, counts, errors, total=seen)


def _sweep(conn: sqlite3.Connection) -> int:
    """At the end, unlike `identify` which frees unique names: here sweeping first would delete a
    night and recreate it with a new id. Sessions first, or an emptied night stays a whole run."""
    tolte = store.drop_empty_sessions(conn)
    tolte += store.drop_empty_nights(conn)
    if tolte:
        log.info("group: sessioni e notti rimaste vuote, tolte", extra={"quante": tolte})
    return tolte


def _one_frame(
    conn: sqlite3.Connection, frame_id: int, dove: Sites, counts: dict[str, int]
) -> None:
    frame = store.frame(conn, frame_id)
    now = now_iso()
    site, risposta, fuori = _where(conn, frame, dove)
    with transaction(conn):
        # `site` is there exactly when there is no reason to stop: both are checked so the pair
        # holds for the reader and the type checker.
        if fuori or site is None:
            set_status(conn, frame_id, "group", "skipped", reason=fuori, now=now)
            counts["waiting"] += 1
        else:
            data = night_date(frame["date_obs"], site["timezone"])
            night_id = _night(conn, site, data, now, counts, declared=bool(risposta))
            session_id = _session(conn, night_id, frame["object_id"], frame["rig_id"], counts)
            store.set_frame_group(conn, frame_id, night_id, session_id)
            set_status(conn, frame_id, "group", "done", now=now)
            counts["linked"] += 1


def _where(conn: sqlite3.Connection, frame: sqlite3.Row, dove: Sites) -> Where:
    """What the frame lacks before what the app lacks, or the user fixes the wrong thing. The
    user's answer for those coordinates beats a nearer site declared later."""
    home, luoghi = dove
    if frame["object_id"] is None:
        return _stop(NO_OBJECT)
    # without a zone, so "unreadable date" stays apart from "the site's zone does not exist"
    if night_date(frame["date_obs"]) is None:
        return _stop(NO_DATE)
    lat, lon = frame["site_lat"], frame["site_lon"]
    lontano = None if home is None else distance_km(lat, lon, home["latitude"], home["longitude"])
    if home is not None and (lontano is None or lontano <= SAME_PLACE_KM):
        return _with_timezone(home, frame, risposta=False)
    if None in (lat, lon):
        return _stop(NO_ACTIVE_SITE)
    detto = decl.site_for_coordinates(conn, coordinates_key(lat, lon))
    if detto:
        site = store.site_by_name(conn, detto)
        if site is None:
            # The declared site was deleted or renamed: ask again rather than fall back on home.
            return _stop(SITE_UNCLEAR)
        return _with_timezone(site, frame, risposta=True)
    vicini = [s for km, s in by_distance(lat, lon, luoghi) if km <= SAME_PLACE_KM]
    if vicini:
        return _with_timezone(vicini[0], frame, risposta=False)
    return _stop(SITE_UNCLEAR if home is not None else NO_ACTIVE_SITE)


def _stop(reason: str) -> Where:
    return None, None, reason


def _with_timezone(site: sqlite3.Row, frame: sqlite3.Row, *, risposta: bool) -> Where:
    if not site["timezone"] or night_date(frame["date_obs"], site["timezone"]) is None:
        return _stop(SITE_NO_TIMEZONE)
    return site, risposta, None


def _night(  # noqa: PLR0913
    conn: sqlite3.Connection,
    site: sqlite3.Row,
    night_date_str: str | None,
    now: str,
    counts: dict[str, int],
    *,
    declared: bool,
) -> int:
    """`declared` when the site came from the user's answer, even "I was home": such a night is
    moved by nobody, neither a home move nor the sweep."""
    riga = store.night(conn, site["id"], night_date_str)
    if riga is not None:
        return riga["id"]
    counts["nights"] += 1
    return store.create_night(conn, site["id"], night_date_str, now, declared=declared)


def _session(
    conn: sqlite3.Connection,
    night_id: int,
    object_id: int,
    rig_id: int | None,
    counts: dict[str, int],
) -> int:
    riga = store.session(conn, night_id, object_id, rig_id)
    if riga is not None:
        return riga["id"]
    counts["sessions"] += 1
    return store.create_session(conn, night_id, object_id, rig_id)
