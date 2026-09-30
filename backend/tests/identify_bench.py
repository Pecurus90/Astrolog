"""Il banco dello stadio `identify`: un DB col catalogo vero, e come si mette una posa.

Lo usano i due file di test dello stadio -- quello che guarda cosa finisce nel database e
quello che guarda la parola dell'utente. Sta qui e non in `conftest.py` perche' e' roba di un
dominio solo; li' ci sono la fixture del catalogo (`db_path_col_catalogo`) e il recinto.
"""

from astrolog.spine import identify
from astrolog.spine.stages import mark_pending, set_status

# Le coordinate vere dei bersagli su cui si prova: un cielo inventato proverebbe l'aritmetica.
M31 = (10.684792, 41.269056)
M45 = (56.869167, 24.105278)
M83 = (204.253958, -29.865417)
# Il puntamento di un campo affollato vero: quanti candidati porti dipende da quanto lo si apre
# (`campo`), e serve ai test che si giocano sul tetto di `identify.CANDIDATES_LIMIT`.
ORIONE = (83.818667, -5.389667)

# Un istante di sera, per i test che fanno arrivare le pose fino a `group`: a Roma sono le
# 00:00 del 18, cioe' la notte del 17. Una sola, cosi' le pose che lo chiedono finiscono
# nella stessa notte e la spazzata si gioca dove deve.
NOTTE = "2024-05-17T22:00:00Z"


def posa(conn, *, obj=None, cielo=None, solve="done", hash_="h", quando=None, campo=(1.5, 1.0)):
    """Una posa pronta per lo stadio: il nome che l'header portava, e il cielo se il solver
    l'ha risolta. Con `quando` (`DATE-OBS` in UTC) la posa arriva anche a `group`, che senza
    data la lascia fuori: serve ai test della spazzata, che si gioca fra i due stadi.

    `campo` e' quanto e' larga la foto in gradi: piu' e' larga, piu' candidati porta: serve ai
    test che si giocano su quanti ne arrivano alla decisione."""
    frame_id = conn.execute(
        "INSERT INTO frames(frame_hash, image_type, object_raw, date_obs, header_json,"
        " created_at) VALUES(?, 'light', ?, ?, '[]', 'now')",
        (f"{hash_}{obj}{cielo}", obj, quando),
    ).lastrowid
    mark_pending(conn, frame_id)
    set_status(conn, frame_id, "normalize", "done")
    set_status(conn, frame_id, "solve", solve, reason=None if solve == "done" else "no_solution")
    if cielo:
        conn.execute(
            "INSERT INTO frame_wcs(frame_id, ra_deg, dec_deg, scale_arcsec_px, width_deg,"
            " height_deg, rotation_deg, solved_at) VALUES(?, ?, ?, 2.0, ?, ?, 0.0, 'now')",
            (frame_id, *cielo, *campo),
        )
    return frame_id


def occupante(conn, object_id, nomi):
    """Un oggetto che tiene gia' quei nomi, **con una posa attaccata**: senza, la spazzata di
    inizio corsa se lo porterebbe via -- ed e' proprio cio' che deve fare."""
    conn.execute(
        "INSERT INTO objects(id, identity_method, identity_confidence, created_at)"
        " VALUES(?, 'exact_name', 'low', 'now')",
        (object_id,),
    )
    for i, nome in enumerate(nomi):
        conn.execute(
            "INSERT INTO object_names(object_id, name, origin, is_primary) VALUES(?, ?, 'raw', ?)",
            (object_id, nome, int(i == 0)),
        )
    frame_id = conn.execute(
        "INSERT INTO frames(frame_hash, image_type, header_json, created_at)"
        " VALUES(?, 'light', '[]', 'now')",
        (f"occupante{object_id}",),
    ).lastrowid
    conn.execute("UPDATE frames SET object_id = ? WHERE id = ?", (object_id, frame_id))


def corri(conn):
    """Lo stadio intero; torna la ricevuta."""
    return list(identify.identify_frames(conn))[-1]


def oggetto_di(conn, frame_id):
    return conn.execute(
        "SELECT o.* FROM objects o JOIN frames f ON f.object_id = o.id WHERE f.id = ?",
        (frame_id,),
    ).fetchone()


def nomi_di(conn, object_id):
    return {
        r["name"]: (r["origin"], r["is_primary"])
        for r in conn.execute("SELECT * FROM object_names WHERE object_id = ?", (object_id,))
    }
