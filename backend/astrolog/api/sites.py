"""I luoghi da cui si osserva: elenco, creazione, modifica, cancellazione, "questo e' quello
di casa" -- piu' la ricerca di un posto per nome, che e' un gesto e non un elenco.

Vincolo non ovvio: il luogo e' sempre DICHIARATO. Le coordinate degli header sono un indizio
e non creano niente. Cio' che si ricava dalle coordinate (fuso, altitudine, luminosita' del
cielo) si ricava alla scrittura e si salva: una pagina che si apre non deve aspettare la rete.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query

from .. import place
from ..clock import now_iso
from ..db import config
from ..db.transaction import transaction
from ..spine import home_nights, site_requeue
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
    Unknown,
)

router = APIRouter(prefix="/api/v1", tags=["luoghi"])

_SELECT = (
    "SELECT s.id, s.name, s.latitude, s.longitude, s.elevation_m, s.timezone, s.sky_sqm,"
    " s.elevation_source, s.sky_source, s.is_default,"
    " (SELECT COUNT(*) FROM nights n WHERE n.site_id = s.id) AS nights"
    " FROM sites s"
)


def _out(row):
    """Un luogo come lo vede la pagina: il Bortle nasce qui, dalla luminosita', e non esiste
    da nessun'altra parte -- e' una consuetudine, non un dato."""
    data = dict(row)
    data["is_default"] = bool(data["is_default"])
    vuoti: tuple[tuple[Unknown, object], ...] = (
        ("site_no_timezone", data["timezone"]),
        ("site_no_elevation", data["elevation_m"]),
        ("site_no_sky", data["sky_sqm"]),
    )
    return SiteOut(
        **data,
        bortle=bortle_of(data["sky_sqm"]),
        # "non lo so" e' un codice, non un null muto: la pagina scrive "non fornita" e sa
        # perche'. Zero e' un'altitudine vera, e non entra qui.
        unknown=[code for code, value in vuoti if value is None],
    )


def _row(conn, site_id):
    row = conn.execute(_SELECT + " WHERE s.id = ?", (site_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "site_not_found"})
    return row


def _sky_key(conn):
    """La chiave personale del servizio che stima il cielo. Senza, non si chiede niente a
    nessuno e l'app funziona uguale: il cielo si misura o si sceglie."""
    return config.read(conn)["sky_service_key"]


def _make_default(conn, site_id):
    """Uno solo e' quello di casa: si toglie a tutti e si da' a lui, dentro la stessa
    transazione -- l'indice unico non tollera nemmeno un istante con due."""
    vecchia = conn.execute("SELECT id FROM sites WHERE is_default = 1").fetchone()
    conn.execute("UPDATE sites SET is_default = 0 WHERE is_default = 1 AND id != ?", (site_id,))
    conn.execute("UPDATE sites SET is_default = 1 WHERE id = ?", (site_id,))
    if vecchia is not None and vecchia[0] != site_id:
        site_requeue.adopt_nights(conn, site_id, vecchia[0])


@router.get("/places", response_model=PlaceList)
def search_places(q: str = Query(min_length=1)):
    """I posti che portano quel nome, per riempire le coordinate senza scriverle a mano.
    Non tocca il database: cercare non crea niente, e senza rete torna un elenco vuoto --
    la strada manuale resta sempre aperta. Senza pagine: il tetto e' quello di `place.search`."""
    return PlaceList(items=[PlaceOut(**p) for p in place.search(q)])


@router.get("/sites", response_model=SiteList)
def list_sites(
    limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), conn=Depends(get_db)
):
    total = conn.execute("SELECT COUNT(*) FROM sites").fetchone()[0]
    rows = conn.execute(
        _SELECT + " ORDER BY s.is_default DESC, s.name LIMIT ? OFFSET ?", (limit, offset)
    ).fetchall()
    return SiteList(items=[_out(r) for r in rows], total=total, limit=limit, offset=offset)


@router.post("/sites", response_model=SiteOut, status_code=201)
def create_site(body: SiteCreate, conn=Depends(get_db)):
    """Un luogo nuovo, arricchito da cio' che le sue coordinate sanno dire.

    Il primo luogo di tutti diventa quello di casa da solo: a mani vuote non c'e' niente da
    scegliere, e chiederlo sarebbe una domanda con una risposta sola."""
    timezone = place.timezone_of(body.latitude, body.longitude)
    elevation_m, elevation_source = place.elevation_from(
        body.latitude, body.longitude, declared=body.elevation_m
    )
    sky_sqm, sky_source = place.sky_of(
        body.latitude, body.longitude, sqm=body.sky_sqm, bortle=body.bortle, key=_sky_key(conn)
    )
    try:
        with transaction(conn):
            # "e' il primo?" si guarda DENTRO la transazione: fuori sarebbe una risposta
            # vecchia di un istante, e il luogo di casa e' uno solo per tutta l'app.
            first = conn.execute("SELECT COUNT(*) FROM sites").fetchone()[0] == 0
            site_id = conn.execute(
                "INSERT INTO sites(name, latitude, longitude, elevation_m,"
                " elevation_source, timezone, sky_sqm, sky_source, is_default, created_at)"
                " VALUES(?, ?, ?, ?, ?, ?, ?, ?, 0, ?)",
                (
                    body.name,
                    body.latitude,
                    body.longitude,
                    elevation_m,
                    elevation_source,
                    timezone,
                    sky_sqm,
                    sky_source,
                    now_iso(),
                ),
            ).lastrowid
            if body.is_default or first:
                _make_default(conn, site_id)
            site_requeue.requeue_waiting(
                conn, near=[(body.latitude, body.longitude)], homeless=body.is_default or first
            )
            home_nights.follow_home(conn)
    except sqlite3.IntegrityError as err:
        raise HTTPException(status_code=409, detail={"code": "site_name_taken"}) from err
    return _out(_row(conn, site_id))


@router.patch("/sites/{site_id}", response_model=SiteOut)
def edit_site(site_id: int, body: SiteEdit, conn=Depends(get_db)):
    """Cio' che si manda vince, anche se e' vuoto: mandare un campo a vuoto vuol dire
    cancellarlo, e un campo non mandato resta com'era.

    Spostare le coordinate rifa' il fuso sempre, e rifa' **cio' che dalle coordinate veniva**:
    l'altitudine e la luminosita' chieste al servizio si richiedono per il posto nuovo, e se il
    servizio tace restano vuote col loro motivo. Cio' che l'utente ha scritto -- un'altitudine
    dichiarata, un cielo misurato o scelto -- resta la sua parola e nessuno la tocca. Per
    questo dell'una e dell'altra si registra la provenienza: un numero rimasto attaccato a
    coordinate nuove sarebbe indistinguibile da una misura."""
    old = dict(_row(conn, site_id))
    fields = body.model_dump(exclude_unset=True)
    vuoti = [f for f in ("name", "latitude", "longitude") if f in fields and fields[f] is None]
    if vuoti:
        raise HTTPException(status_code=422, detail={"code": "field_required", "fields": vuoti})

    latitude = fields.get("latitude", old["latitude"])
    longitude = fields.get("longitude", old["longitude"])
    moved = (latitude, longitude) != (old["latitude"], old["longitude"])

    timezone = place.timezone_of(latitude, longitude)
    if "elevation_m" in fields:
        # mandata a vuoto vuol dire CANCELLATA: non si torna a chiederla al servizio, o il
        # gesto "svuota questo campo" vorrebbe dire due cose diverse su due campi vicini
        scritta = fields["elevation_m"]
        elevation_m, elevation_source = (
            (scritta, "declared") if scritta is not None else (None, None)
        )
    elif moved and old["elevation_source"] == "service":
        elevation_m, elevation_source = place.elevation_from(latitude, longitude)
    else:
        elevation_m, elevation_source = old["elevation_m"], old["elevation_source"]

    if "sky_sqm" in fields or "bortle" in fields:
        sky_sqm, sky_source = place.sky_of(
            latitude, longitude, sqm=fields.get("sky_sqm"), bortle=fields.get("bortle")
        )
    elif moved and old["sky_source"] == "service":
        sky_sqm, sky_source = place.sky_of(latitude, longitude, key=_sky_key(conn))
    else:
        sky_sqm, sky_source = old["sky_sqm"], old["sky_source"]
    try:
        with transaction(conn):
            conn.execute(
                "UPDATE sites SET name = ?, latitude = ?, longitude = ?, elevation_m = ?,"
                " elevation_source = ?, timezone = ?, sky_sqm = ?, sky_source = ?"
                " WHERE id = ?",
                (
                    fields.get("name", old["name"]),
                    latitude,
                    longitude,
                    elevation_m,
                    elevation_source,
                    timezone,
                    sky_sqm,
                    sky_source,
                    site_id,
                ),
            )
            if moved:
                site_requeue.requeue_nights_of(conn, site_id)
            nome = fields.get("name", old["name"])
            site_requeue.requeue_waiting(
                conn,
                near=[(old["latitude"], old["longitude"]), (latitude, longitude)] if moved else [],
                names=[old["name"], nome] if nome != old["name"] else [],
            )
            home_nights.follow_home(conn)
    except sqlite3.IntegrityError as err:
        raise HTTPException(status_code=409, detail={"code": "site_name_taken"}) from err
    return _out(_row(conn, site_id))


@router.post("/sites/{site_id}/default", response_model=SiteOut)
def set_default(site_id: int, conn=Depends(get_db)):
    """ "Questo e' il mio luogo di casa": e' lui che decide il fuso delle notti."""
    row = _row(conn, site_id)
    with transaction(conn):
        senza_casa = conn.execute("SELECT 1 FROM sites WHERE is_default = 1").fetchone() is None
        _make_default(conn, site_id)
        site_requeue.requeue_waiting(
            conn, near=[(row["latitude"], row["longitude"])], homeless=senza_casa
        )
        home_nights.follow_home(conn)
    return _out(_row(conn, site_id))


@router.delete("/sites/{site_id}", response_model=SiteDeleted)
def delete_site(site_id: int, conn=Depends(get_db)):
    """Un luogo che ha delle notti non si perde per sbaglio: l'app si rifiuta e dice quante.
    Se era quello di casa, non ne elegge un altro da sola: lo chiede."""
    nights = _row(conn, site_id)["nights"]
    if nights:
        raise HTTPException(status_code=409, detail={"code": "site_has_nights", "nights": nights})
    with transaction(conn):
        conn.execute("DELETE FROM sites WHERE id = ?", (site_id,))
        site_requeue.requeue_waiting(conn)
        home_nights.follow_home(conn)
    return SiteDeleted(site_id=site_id, deleted=True)
