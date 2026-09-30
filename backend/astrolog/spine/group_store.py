"""Le domande al database dello stadio `group`, tutte qui e tutte statiche.

Vincolo non ovvio: notti e sessioni sono un **derivato**, come gli oggetti. Chi le scrive le
cerca prima e le crea poi, e chi rifa' il lavoro stacca le pose e spazza cio' che resta vuoto:
una sessione a zero pose sarebbe una riga che dice "0 pose" sulla pagina Notti, e una notte
senza sessioni non e' una notte. La parola dell'utente non vive qui -- vive in `declarations`.
"""

from ..db import idlist


def frame(conn, frame_id):
    """Cio' che serve a raggruppare una posa: quando, cosa, con che corredo, e da dove dice
    l'header di essere stata ripresa."""
    return conn.execute(
        "SELECT id, date_obs, object_id, rig_id, site_lat, site_lon, header_json"
        " FROM frames WHERE id = ?",
        (frame_id,),
    ).fetchone()


_SITE = "SELECT id, name, latitude, longitude, timezone, sky_sqm FROM sites"


def home_site(conn):
    """Il luogo di casa: e' lui a dare il fuso alle notti. `None` se non ce n'e' uno."""
    return conn.execute(_SITE + " WHERE is_default = 1").fetchone()


def sites(conn):
    """Tutti i luoghi dichiarati: una posa ripresa vicino a uno di loro ci va senza chiedere."""
    return conn.execute(_SITE).fetchall()


def night(conn, site_id, night_date):
    """La notte di quel luogo in quella data, se c'e' gia'."""
    return conn.execute(
        "SELECT id FROM nights WHERE site_id = ? AND night_date = ?", (site_id, night_date)
    ).fetchone()


def site_by_name(conn, name):
    """Un sito per NOME: e' la chiave su cui viaggia la risposta dell'utente, perche' gli id si
    riusano. `None` se quel sito non c'e' piu' o si chiama in un altro modo."""
    return conn.execute(_SITE + " WHERE name = ?", (name,)).fetchone()


def create_night(conn, site_id, night_date, now, *, declared=False):
    """Una notte nuova. `detected` quando e' l'app ad attribuirla al luogo di casa, `declared`
    quando il sito viene da una risposta dell'utente: e' la differenza che decide chi puo'
    spostarla dopo (nessuno, nel secondo caso)."""
    return conn.execute(
        "INSERT INTO nights(site_id, night_date, site_source, created_at) VALUES(?, ?, ?, ?)",
        (site_id, night_date, "declared" if declared else "detected", now),
    ).lastrowid


def session(conn, night_id, object_id, rig_id):
    """La sessione di quella terna, se c'e' gia'. Il corredo vuoto si confronta come tale:
    e' la stessa forma della chiave nello schema, o due pose senza corredo non si
    ritroverebbero nella stessa sessione."""
    return conn.execute(
        "SELECT id FROM sessions WHERE night_id = ? AND object_id = ?"
        " AND COALESCE(rig_id, -1) = COALESCE(?, -1)",
        (night_id, object_id, rig_id),
    ).fetchone()


def create_session(conn, night_id, object_id, rig_id):
    return conn.execute(
        "INSERT INTO sessions(night_id, object_id, rig_id) VALUES(?, ?, ?)",
        (night_id, object_id, rig_id),
    ).lastrowid


def set_frame_group(conn, frame_id, night_id, session_id):
    """Dove finisce la posa: la sua notte e la sua sessione."""
    conn.execute(
        "UPDATE frames SET night_id = ?, session_id = ? WHERE id = ?",
        (night_id, session_id, frame_id),
    )


def detach(conn, frame_ids):
    """Stacca notte e sessione dalle pose che questo stadio sta per rifare: sono un derivato, e
    chi le ha rimesse in coda ha detto che quelli vecchi non valgono piu'."""
    if not frame_ids:
        return
    with idlist.holding(conn, frame_ids) as listed:
        conn.execute(
            f"UPDATE frames SET night_id = NULL, session_id = NULL"  # noqa: S608
            f" WHERE id IN {listed}"
        )


def drop_empty_sessions(conn):
    """Le sessioni rimaste senza pose. Torna quante ne ha tolte."""
    return conn.execute(
        "DELETE FROM sessions"
        " WHERE id NOT IN (SELECT session_id FROM frames WHERE session_id IS NOT NULL)"
    ).rowcount


def drop_empty_nights(conn):
    """Le notti rimaste senza sessioni. Si chiama DOPO la spazzata delle sessioni, o una notte
    appena svuotata resterebbe in piedi per un giro.

    **Mai una notte dichiarata dall'utente**: quella e' una sua risposta ("queste pose sono di
    questo luogo") e puo' restare vuota per un giro senza essere un residuo -- basta che le sue
    pose aspettino un altro stadio. Toglierla vorrebbe dire cancellare una risposta in
    silenzio, che e' la cosa che questo progetto non fa mai."""
    return conn.execute(
        "DELETE FROM nights"
        " WHERE site_source != 'declared'"
        " AND id NOT IN (SELECT night_id FROM sessions)"
        " AND id NOT IN (SELECT night_id FROM frames WHERE night_id IS NOT NULL)"
    ).rowcount
