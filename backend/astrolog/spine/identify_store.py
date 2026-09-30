"""Le domande al database dello stadio `identify`, tutte qui e tutte statiche.

Vincolo non ovvio: nessuna decisione vive in questo file. Chi legge `identify.py` deve poter
capire cosa succede senza aprire questo, e chi legge questo deve trovare solo SQL.

Due posti dove questo file "sa" qualcosa, e sono dichiarati. `wcs` torna un **dizionario**: la
geometria legge il cielo con `.get()` -- lati e rotazione possono mancare a soluzione buona --
e una riga di `sqlite3.Row` non ha `.get()`; passarla tal quale solleva alla prima istruzione.
E `add_name` non scrive un nome che e' gia' di un altro oggetto: e' la regola "un nome, un
oggetto" che l'indice unico impone, e sta qui perche' il chiamante dovrebbe altrimenti fare la
stessa domanda al database una riga prima. Torna se **alla fine l'oggetto ha quel nome** -- che
non e' "ha scritto": un nome gia' suo torna `True` senza scrivere niente, ed e' il caso
normalissimo del nome grezzo uguale alla sigla che il catalogo gli ha appena dato.
"""

from ..db import idlist


def frame(conn, frame_id):
    """La posa: qui serve solo il nome che l'header portava."""
    return conn.execute("SELECT id, object_raw FROM frames WHERE id = ?", (frame_id,)).fetchone()


def wcs(conn, frame_id):
    """Il cielo misurato come dizionario, o `{}` se la posa non e' stata risolta."""
    row = conn.execute(
        "SELECT ra_deg, dec_deg, scale_arcsec_px, rotation_deg, width_deg, height_deg"
        " FROM frame_wcs WHERE frame_id = ?",
        (frame_id,),
    ).fetchone()
    return dict(row) if row else {}


def object_by_slug(conn, slug):
    row = conn.execute("SELECT * FROM objects WHERE catalog_slug = ?", (slug,)).fetchone()
    return dict(row) if row else None


def object_by_name(conn, name):
    row = conn.execute(
        "SELECT o.* FROM objects o JOIN object_names n ON n.object_id = o.id WHERE n.name = ?",
        (name,),
    ).fetchone()
    return dict(row) if row else None


def name_owner(conn, name):
    """Di chi e' gia' questo nome, se di qualcuno. Un nome, un oggetto."""
    row = conn.execute("SELECT object_id FROM object_names WHERE name = ?", (name,)).fetchone()
    return row[0] if row else None


def create_object(conn, *, slug, method, confidence, now):
    return conn.execute(
        "INSERT INTO objects(catalog_slug, identity_method, identity_confidence,"
        " identified_at, created_at) VALUES(?, ?, ?, ?, ?)",
        (slug, method, confidence, now, now),
    ).lastrowid


def set_identity(conn, object_id, *, method, confidence, now):
    conn.execute(
        "UPDATE objects SET identity_method = ?, identity_confidence = ?, identified_at = ?"
        " WHERE id = ?",
        (method, confidence, now, object_id),
    )


def add_name(conn, object_id, name, *, origin, is_primary=0):
    """Il nome all'oggetto. Torna `True` se alla fine l'oggetto ce l'ha.

    Torna `False` in un caso solo: il nome e' **di un altro** oggetto. Non e' un guasto, e' la
    regola "un nome, un oggetto" che si applica -- succede davvero, perche' nel catalogo 110
    voci si spartiscono 42 nomi comuni, e perche' due oggetti diversi possono avere lo stesso
    nome grezzo nell'header.

    Che il nome sia gia' di QUESTO oggetto e' invece la norma e non si conta: il nome grezzo
    dell'header e' spessissimo la sigla che il catalogo gli ha appena dato."""
    padrone = name_owner(conn, name)
    if padrone is not None:
        return padrone == object_id
    conn.execute(
        "INSERT INTO object_names(object_id, name, origin, is_primary) VALUES(?, ?, ?, ?)",
        (object_id, name, origin, is_primary),
    )
    return True


def set_frame_object(conn, frame_id, object_id):
    conn.execute("UPDATE frames SET object_id = ? WHERE id = ?", (object_id, frame_id))


def set_empty_cone(conn, frame_id, empty):
    conn.execute("UPDATE frames SET empty_cone = ? WHERE id = ?", (empty, frame_id))


def detach(conn, frame_ids):
    """Stacca l'oggetto dalle pose che questo stadio sta per rifare: e' un derivato, e chi lo
    rimette in coda ha detto che quello vecchio non vale piu'."""
    if not frame_ids:
        return
    with idlist.holding(conn, frame_ids) as listed:
        conn.execute(f"UPDATE frames SET object_id = NULL WHERE id IN {listed}")  # noqa: S608


def drop_empty_objects(conn):
    """Toglie gli oggetti a cui non e' rimasta nessuna posa. `object_names` e le `sessions`
    li seguono per CASCADE -- perche' anche le sessioni, e perche' non si perde niente, sta
    accanto al vincolo in `schema.sql`. Torna quanti ne ha tolti.

    **Anche quelli `user`**: l'utente non crea oggetti, crea correzioni, e gli oggetti li fa
    `identify` quando una posa ci va -- quindi uno a zero pose e' sempre un residuo. Non si
    perde niente, perche' l'oggetto e' un derivato e la parola dell'utente vive in
    `declarations`."""
    return conn.execute(
        "DELETE FROM objects"
        " WHERE id NOT IN (SELECT object_id FROM frames WHERE object_id IS NOT NULL)"
    ).rowcount
