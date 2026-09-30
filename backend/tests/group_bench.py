"""Il banco dello stadio `group`: un luogo di casa, e come si mette una posa gia' identificata.

Lo usano i test dello stadio e quelli della sezione dei luoghi di Da confermare, che guardano lo
stesso archivio da due parti: uno cosa finisce nel database, l'altro la domanda che l'app fa
quando non sa da dove hai ripreso.
"""

import json

from astrolog.clock import now_iso
from astrolog.spine import group
from astrolog.spine.scan import night_of
from astrolog.spine.stages import mark_pending, set_status

# Due fusi lontani, perche' lo stesso istante cade in due notti diverse: e' cio' che il
# progetto di prima sbagliava calcolando la notte in UTC.
ROMA = ("Casa", 45.5455, 11.5354, "Europe/Rome")
ARIZONA = ("Deserto", 33.45, -111.98, "America/Phoenix")
# Un posto vero a 12 km da casa.
VICINO = (45.6, 11.667)


def prepara(conn):
    """Due oggetti e due corredi gia' in casa: `group` viene dopo di loro. E' una funzione e non
    una fixture perche' la fixture la dichiara ogni file di test in tre righe -- importarla
    farebbe litigare il nome col parametro dei test, e con `archivio` di `conftest`, che e'
    un'altra cosa."""
    conn.execute(
        "INSERT INTO objects(id, catalog_slug, identity_method, identity_confidence, created_at)"
        " VALUES(1, 'm-31', 'coord_confirmed', 'certain', ?)",
        (now_iso(),),
    )
    conn.execute(
        "INSERT INTO objects(id, catalog_slug, identity_method, identity_confidence, created_at)"
        " VALUES(2, 'm-45', 'coord_confirmed', 'certain', ?)",
        (now_iso(),),
    )
    conn.execute(
        "INSERT INTO rigs(id, focal_mm, detected, created_at) VALUES(1, 700, 1, ?)", (now_iso(),)
    )
    conn.execute(
        "INSERT INTO rigs(id, focal_mm, detected, created_at) VALUES(2, 400, 1, ?)", (now_iso(),)
    )
    return conn


def luogo(conn, sito=ROMA, *, casa=True):
    """Un luogo dichiarato; torna il suo id."""
    nome, lat, lon, tz = sito
    return conn.execute(
        "INSERT INTO sites(name, latitude, longitude, timezone, is_default, created_at)"
        " VALUES(?, ?, ?, ?, ?, ?)",
        (nome, lat, lon, tz, int(casa), now_iso()),
    ).lastrowid


def attrezzo(conn, kind, nome, **campi):
    """Uno strumento gia' in casa, come lo scriverebbe la spina leggendo un header. I campi della
    scheda si passano per nome: sono colonne di questo banco, mai valori dell'utente."""
    colonne = "".join(f", {c}" for c in campi)
    segni = ", ?" * len(campi)
    sql = (  # noqa: S608 - nomi di colonna di questo banco, mai valori dell'utente
        f"INSERT INTO instruments(kind, name, detected, created_at{colonne})"
        f" VALUES(?, ?, 1, ?{segni})"
    )
    return conn.execute(sql, (kind, nome, now_iso(), *campi.values())).lastrowid


def filtro(conn, nome, banda="ha"):
    """Un filtro posseduto; torna il suo id. Serve a chi guarda le ore per filtro."""
    return conn.execute(
        "INSERT INTO filters(name, passband, created_at) VALUES(?, ?, ?)",
        (nome, banda, now_iso()),
    ).lastrowid


def posa(
    conn,
    *,
    quando,
    oggetto=1,
    corredo=1,
    coord=None,
    hash_=None,
    identify="done",
    ora_locale=None,
    filtro_id=None,
    esposizione=None,
    copia_di=None,
):
    """Una posa gia' passata dagli stadi a monte, pronta per `group`.

    `ora_locale` scrive `DATE-LOC` nell'header salvato, accanto al `DATE-OBS`: serve a provare
    che l'app non lo usa per correggere l'ora. `esposizione`, `filtro_id` e `copia_di` servono a
    chi conta ore e filtri."""
    header = json.dumps([["DATE-OBS", quando], ["DATE-LOC", ora_locale]]) if ora_locale else "[]"
    lat, lon = coord or (None, None)
    # la notte della posa come la scrive `scan` quando la posa entra, con la sua stessa regola; una
    # posa senza data qui non ha un file da cui prenderla, e resta senza notte invece di inventarla
    campi = {"date_obs": quando, "site_lat": lat, "site_lon": lon}
    notte, fuso, istante = night_of(conn, campi, 0) if quando else (None, None, None)
    frame_id = conn.execute(
        "INSERT INTO frames(frame_hash, image_type, date_obs, local_night, local_tz, night_instant,"
        " object_id, rig_id, site_lat, site_lon, header_json, filter_id, exposure_s, copy_of,"
        " created_at) VALUES(?, 'light', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            hash_ or f"h{quando}{oggetto}{corredo}{coord}{filtro_id}{esposizione}{copia_di}",
            quando,
            notte,
            fuso,
            istante,
            oggetto,
            corredo,
            *(coord or (None, None)),
            header,
            filtro_id,
            esposizione,
            copia_di,
            now_iso(),
        ),
    ).lastrowid
    mark_pending(conn, frame_id)
    for stadio in ("solve", "normalize"):
        set_status(conn, frame_id, stadio, "done")
    set_status(conn, frame_id, "identify", identify, reason=None if identify == "done" else "x")
    return frame_id


def corri(conn):
    """Lo stadio intero; torna la ricevuta."""
    return list(group.group_frames(conn))[-1]


def notte_di(conn, frame_id):
    return conn.execute(
        "SELECT n.* FROM nights n JOIN frames f ON f.night_id = n.id WHERE f.id = ?", (frame_id,)
    ).fetchone()


def sessione_di(conn, frame_id):
    return conn.execute(
        "SELECT s.* FROM sessions s JOIN frames f ON f.session_id = s.id WHERE f.id = ?",
        (frame_id,),
    ).fetchone()


def stato(conn, frame_id):
    r = conn.execute(
        "SELECT status, reason FROM frame_stages WHERE frame_id = ? AND stage = 'group'",
        (frame_id,),
    ).fetchone()
    return r["status"], r["reason"]
