"""A site is always declared: header coordinates are a hint and create nothing. What coordinates
yield (zone, elevation, sky) is derived on write and saved, so an opening page never waits."""

import json
import sqlite3
from dataclasses import asdict
from typing import Any, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from .. import place
from ..clock import now_iso
from ..db import config
from ..db.inserted import inserted_id
from ..db.transaction import transaction
from ..spine import declarations, home_nights, site_requeue
from ..units import bortle_of
from .deps import get_db
from .models_site import (
    PlaceList,
    PlaceOut,
    SiteCreate,
    SiteDeleted,
    SiteEdit,
    SiteList,
    SiteOut,
    SiteSkyMeasured,
    Unknown,
)
from .scan import sky_follows

router = APIRouter(prefix="/api/v1", tags=["sites"])

_SELECT = (
    "SELECT s.id, s.name, s.latitude, s.longitude, s.coords_source, s.elevation_m, s.timezone,"
    " s.sky_sqm, s.elevation_source, s.sky_source, s.sky_nights, s.is_default,"
    " (SELECT COUNT(*) FROM nights n WHERE n.site_id = s.id) AS nights,"
    " m.nights AS m_nights, m.months AS m_months, m.sqm AS m_sqm, m.first_night AS m_first,"
    " m.last_night AS m_last, m.marks_json AS m_marks, d.bortle AS dismissed"
    " FROM sites s LEFT JOIN site_sky_measures m ON m.site_id = s.id"
    " LEFT JOIN site_sky_dismissed d ON d.site_id = s.id"
)


def _measured(data: dict[str, Any]) -> SiteSkyMeasured:
    """Proposed when the measure is enough, of another class than the site's (none included),
    and not the class the user dismissed."""
    sqm = data.pop("m_sqm")
    bortle = bortle_of(sqm)
    dismissed = data.pop("dismissed")
    return SiteSkyMeasured(
        status="enough" if sqm is not None else "too_few",
        nights=data.pop("m_nights") or 0, months=data.pop("m_months") or 0,
        sqm=sqm, bortle=bortle, first_night=data.pop("m_first"), last_night=data.pop("m_last"),
        propose=bortle is not None
        and bortle != bortle_of(data["sky_sqm"])
        and bortle != dismissed,
        month_marks=json.loads(marks) if (marks := data.pop("m_marks")) else [],
    )  # fmt: skip


def _out(row: sqlite3.Row) -> SiteOut:
    """Bortle is derived here from the brightness and never stored: a convention, not a datum."""
    data = dict(row)
    data["is_default"] = bool(data["is_default"])
    data["measured"] = _measured(data)
    blanks: tuple[tuple[Unknown, object], ...] = (
        ("site_no_timezone", data["timezone"]),
        ("site_no_elevation", data["elevation_m"]),
        ("site_no_sky", data["sky_sqm"]),
    )
    return SiteOut(
        **data,
        bortle=bortle_of(data["sky_sqm"]),
        # zero is a real elevation, not an unknown one
        unknown=[code for code, value in blanks if value is None],
    )


def _row(conn: sqlite3.Connection, site_id: int) -> sqlite3.Row:
    row = conn.execute(_SELECT + " WHERE s.id = ?", (site_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "site_not_found"})
    return row


def _sky_key(conn: sqlite3.Connection) -> str | None:
    """Without the sky service's key nobody is asked: the sky is measured or chosen."""
    return config.read(conn).sky_service_key


def _make_default(conn: sqlite3.Connection, site_id: int) -> None:
    """Taken from the others before it is given, in the caller's transaction: the unique index
    does not tolerate even an instant with two homes."""
    previous = conn.execute("SELECT id FROM sites WHERE is_default = 1").fetchone()
    conn.execute("UPDATE sites SET is_default = 0 WHERE is_default = 1 AND id != ?", (site_id,))
    conn.execute("UPDATE sites SET is_default = 1 WHERE id = ?", (site_id,))
    if previous is not None and previous[0] != site_id:
        site_requeue.adopt_nights(conn, site_id, previous[0])


@router.get("/places", response_model=PlaceList)
def search_places(q: str = Query(min_length=1)) -> PlaceList:
    """The places bearing that name, to fill in the coordinates without typing them by hand.
    It does not touch the database: searching creates nothing, and without network it returns an
    empty list -- the manual way always stays open. No pages: the cap is `place.search`'s."""
    return PlaceList(items=[PlaceOut(**asdict(p)) for p in place.search(q)])


@router.get("/sites", response_model=SiteList)
def list_sites(
    limit: int = Query(100, ge=1, le=1000),  # [T]
    offset: int = Query(0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
) -> SiteList:
    """The sites, the home one first and then by name, each with its number of nights and the
    codes of what is not known about it (`unknown`)."""
    total = conn.execute("SELECT COUNT(*) FROM sites").fetchone()[0]
    rows = conn.execute(
        _SELECT + " ORDER BY s.is_default DESC, s.name COLLATE NOCASE, s.id LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return SiteList(items=[_out(r) for r in rows], total=total, limit=limit, offset=offset)


def _name_taken_or_raise(err: sqlite3.IntegrityError) -> NoReturn:
    """Only the name index is the user's 409; any other broken rule is a fault, and stays one."""
    if "sites.name" in str(err):
        raise HTTPException(status_code=409, detail={"code": "site_name_taken"}) from err
    raise err


# [C RFC 9110 15.3.2: 201 Created]
@router.post("/sites", response_model=SiteOut, status_code=201)
def create_site(
    body: SiteCreate, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> SiteOut:
    """A new site, enriched by what its coordinates can tell, returned as it is now saved.

    The very first site becomes the home one by itself: empty-handed there is nothing to choose,
    and asking would be a question with a single answer.

    409 `site_name_taken` if another site already has that name."""
    timezone = place.timezone_of(body.latitude, body.longitude)
    elevation_m, elevation_source = place.elevation_from(
        body.latitude, body.longitude, declared=body.elevation_m
    )
    sky_sqm, sky_source = place.sky_of(
        body.latitude, body.longitude, sqm=body.sky_sqm, bortle=body.bortle, key=_sky_key(conn)
    )
    try:
        with transaction(conn):
            # inside the transaction: outside, the answer would be an instant old, and there is
            # one home for the whole app
            first = conn.execute("SELECT COUNT(*) FROM sites").fetchone()[0] == 0
            site_id = inserted_id(
                conn.execute(
                    "INSERT INTO sites(name, latitude, longitude, coords_source, elevation_m,"
                    " elevation_source, timezone, sky_sqm, sky_source, is_default, created_at)"
                    " VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)",
                    (
                        body.name,
                        body.latitude,
                        body.longitude,
                        body.coords_source,
                        elevation_m,
                        elevation_source,
                        timezone,
                        sky_sqm,
                        sky_source,
                        now_iso(),
                    ),
                )
            )
            if body.is_default or first:
                _make_default(conn, site_id)
            site_requeue.requeue_waiting(
                conn, near=[(body.latitude, body.longitude)], homeless=body.is_default or first
            )
            home_nights.follow_home(conn)
    except sqlite3.IntegrityError as err:
        _name_taken_or_raise(err)
    sky_follows(request)
    return _out(_row(conn, site_id))


@router.patch("/sites/{site_id}", response_model=SiteOut)
def edit_site(
    site_id: int, body: SiteEdit, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> SiteOut:
    """What is sent wins, even when empty: sending a field empty means deleting it, and a field
    not sent stays as it was. Returns the site as it now is.

    Moving the coordinates always redoes the time zone, and redoes **what came from the
    coordinates**: the elevation and brightness asked of the service are asked again for the new
    place, and if the service is silent they stay empty with their reason. What the user wrote --
    a declared elevation, a measured or chosen sky -- stays their word and nobody touches it. That
    is why the source of each is recorded: a number left attached to new coordinates would be
    indistinguishable from a measurement.

    404 `site_not_found`; 422 `field_required` with the `fields` among `name`, `latitude` and
    `longitude` sent empty; 409 `site_name_taken` if another site already has the new name."""
    old = dict(_row(conn, site_id))
    fields = body.model_dump(exclude_unset=True)
    blanks = [f for f in ("name", "latitude", "longitude") if f in fields and fields[f] is None]
    if blanks:
        raise HTTPException(status_code=422, detail={"code": "field_required", "fields": blanks})

    latitude = fields.get("latitude", old["latitude"])
    longitude = fields.get("longitude", old["longitude"])
    moved = (latitude, longitude) != (old["latitude"], old["longitude"])
    declared = place.CoordsSource.DECLARED
    coords_source = (fields.get("coords_source") or declared) if moved else old["coords_source"]

    timezone = place.timezone_of(latitude, longitude)
    if "elevation_m" in fields:
        # sent empty means deleted, not asked of the service again: otherwise "empty this field"
        # would mean two different things on two neighbouring fields
        written = fields["elevation_m"]
        elevation_m, elevation_source = (
            (written, place.ElevationSource.DECLARED) if written is not None else (None, None)
        )
    elif moved and old["elevation_source"] == place.ElevationSource.SERVICE:
        elevation_m, elevation_source = place.elevation_from(latitude, longitude)
    else:
        elevation_m, elevation_source = old["elevation_m"], old["elevation_source"]

    sky_nights = None
    if "sky_sqm" in fields or "bortle" in fields:
        sky_sqm, sky_source = place.sky_of(
            latitude, longitude, sqm=fields.get("sky_sqm"), bortle=fields.get("bortle")
        )
    elif moved and old["sky_source"] == place.SkySource.SERVICE:
        sky_sqm, sky_source = place.sky_of(latitude, longitude, key=_sky_key(conn))
    elif moved and old["sky_source"] == place.SkySource.FRAMES:
        sky_sqm, sky_source = None, None  # that place's frames; the new place proposes its own
    else:
        sky_sqm, sky_source, sky_nights = old["sky_sqm"], old["sky_source"], old["sky_nights"]
    try:
        with transaction(conn):
            conn.execute(
                "UPDATE sites SET name = ?, latitude = ?, longitude = ?, coords_source = ?,"
                " elevation_m = ?, elevation_source = ?, timezone = ?, sky_sqm = ?,"
                " sky_source = ?, sky_nights = ? WHERE id = ?",
                (
                    fields.get("name", old["name"]),
                    latitude,
                    longitude,
                    coords_source,
                    elevation_m,
                    elevation_source,
                    timezone,
                    sky_sqm,
                    sky_source,
                    sky_nights,
                    site_id,
                ),
            )
            if moved:
                site_requeue.requeue_nights_of(conn, site_id)
                # "Keep" answered that place's measure: the new place proposes its own
                conn.execute("DELETE FROM site_sky_dismissed WHERE site_id = ?", (site_id,))
            new_name = fields.get("name", old["name"])
            if new_name != old["name"]:
                declarations.follow_site_rename(conn, old["name"], new_name)
            site_requeue.requeue_waiting(
                conn,
                near=[(old["latitude"], old["longitude"]), (latitude, longitude)] if moved else [],
                names=[old["name"], new_name] if new_name != old["name"] else [],
            )
            home_nights.follow_home(conn)
    except sqlite3.IntegrityError as err:
        _name_taken_or_raise(err)
    sky_follows(request)
    return _out(_row(conn, site_id))


@router.post("/sites/{site_id}/default", response_model=SiteOut)
def set_default(
    site_id: int, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> SiteOut:
    """ "This is my home site": it decides the time zone of the nights. Returns the site as it now
    is.

    404 `site_not_found`."""
    row = _row(conn, site_id)
    with transaction(conn):
        no_home = conn.execute("SELECT 1 FROM sites WHERE is_default = 1").fetchone() is None
        _make_default(conn, site_id)
        site_requeue.requeue_waiting(
            conn, near=[(row["latitude"], row["longitude"])], homeless=no_home
        )
        home_nights.follow_home(conn)
    sky_follows(request)
    return _out(_row(conn, site_id))


@router.delete("/sites/{site_id}", response_model=SiteDeleted)
def delete_site(
    site_id: int, request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> SiteDeleted:
    """A site that has nights is not lost by mistake: the app refuses and says how many. If it was
    the home one, the app does not elect another by itself: it asks.

    404 `site_not_found`; 409 `site_has_nights` with the number of `nights`."""
    nights = _row(conn, site_id)["nights"]
    if nights:
        raise HTTPException(status_code=409, detail={"code": "site_has_nights", "nights": nights})
    with transaction(conn):
        conn.execute("DELETE FROM sites WHERE id = ?", (site_id,))
        site_requeue.requeue_waiting(conn)
        home_nights.follow_home(conn)
    sky_follows(request)
    return SiteDeleted(site_id=site_id, deleted=True)


def _enough_or_raise(row: sqlite3.Row) -> None:
    if row["m_sqm"] is None:
        raise HTTPException(status_code=409, detail={"code": "site_sky_not_measured"})


@router.post("/sites/{site_id}/sky/use", response_model=SiteOut)
def use_measured_sky(site_id: int, conn: sqlite3.Connection = Depends(get_db)) -> SiteOut:
    """Use Bortle b: the sky measured on the frames becomes the site's, with its nights. Returns
    the site as it now is.

    404 `site_not_found`; 409 `site_sky_not_measured` while the frames are too few."""
    row = _row(conn, site_id)
    _enough_or_raise(row)
    with transaction(conn):
        conn.execute(
            "UPDATE sites SET sky_sqm = ?, sky_source = ?, sky_nights = ? WHERE id = ?",
            (row["m_sqm"], place.SkySource.FRAMES, row["m_nights"], site_id),
        )
    return _out(_row(conn, site_id))


@router.post("/sites/{site_id}/sky/dismiss", response_model=SiteOut)
def dismiss_measured_sky(site_id: int, conn: sqlite3.Connection = Depends(get_db)) -> SiteOut:
    """Keep Bortle b0: the site stays as it is, and the measure is proposed again only when its
    class changes. Returns the site as it now is.

    404 `site_not_found`; 409 `site_sky_not_measured` while the frames are too few."""
    row = _row(conn, site_id)
    _enough_or_raise(row)
    with transaction(conn):
        conn.execute(
            "INSERT OR REPLACE INTO site_sky_dismissed (site_id, bortle) VALUES (?, ?)",
            (site_id, bortle_of(row["m_sqm"])),
        )
    return _out(_row(conn, site_id))
