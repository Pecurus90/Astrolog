"""Le domande al database dello stadio `solve`, tutte qui e tutte statiche.

Vincolo non ovvio: nessuna decisione vive in questo file. Chi legge `solve.py` deve poter
capire cosa succede senza aprire questo, e chi legge questo deve trovare solo SQL.
"""

from ..db import idlist


def frame(conn, frame_id):
    """Il frame con la sua prima posizione presente sul disco: `root_path` e `rel_path` per
    comporre il percorso. Un frame le cui posizioni sono tutte `missing` torna comunque, col
    percorso a `None`: e' un disco staccato, non un errore."""
    return conn.execute(
        "SELECT f.*,"
        " (SELECT d.root_path FROM positions p JOIN folders d ON d.id = p.folder_id"
        "   WHERE p.frame_id = f.id AND p.status = 'present' ORDER BY p.id LIMIT 1) AS root_path,"
        " (SELECT p.rel_path FROM positions p"
        "   WHERE p.frame_id = f.id AND p.status = 'present' ORDER BY p.id LIMIT 1) AS rel_path"
        " FROM frames f WHERE f.id = ?",
        (frame_id,),
    ).fetchone()


# La chiave con cui il solver mette in fila il primo giro: oggetto, notte della posa (quella che
# `scan` ha scritto) e i due pezzi come li scrive l'header. **Non e' la sessione** del glossario --
# quella e' oggetto x notte x corredo, e la fa `group`: qui si mette in FILA, non si contano ore.
# Per la stessa ragione l'oggetto e' grezzo: `M31` e `M 31` in due gruppi costano una posa risolta
# in piu' e nient'altro. Che la notte sia quella di `clock.night_date` lo tiene
# `test_the_night_in_sql_says_the_same_as_the_one_in_python`.
SOLVE_ORDER_KEY = (
    "COALESCE(object_raw, '') || '|' || COALESCE(local_night, '')"
    " || '|' || COALESCE(telescope_raw, '') || '|' || COALESCE(instrument_raw, '')"
)


def first_per_order_key(conn, frame_ids):
    """Il primo frame di ogni gruppo di `SOLVE_ORDER_KEY`, fra quelli dati. E' il primo giro:
    basta una posa per gruppo per orientare, raggruppare e disegnare il campo."""
    if not frame_ids:
        return []
    with idlist.holding(conn, frame_ids) as listed:
        return [
            r[0]
            for r in conn.execute(
                f"SELECT MIN(id) FROM frames WHERE id IN {listed} GROUP BY {SOLVE_ORDER_KEY}"  # noqa: S608
            )
        ]


def newest_first(conn, frame_ids):
    """I frame dati, dalla posa piu' recente alla piu' vecchia. Chi non ha data va in fondo:
    non si finge che sia di oggi."""
    if not frame_ids:
        return []
    with idlist.holding(conn, frame_ids) as listed:
        return [
            r[0]
            for r in conn.execute(
                f"SELECT id FROM frames WHERE id IN {listed}"  # noqa: S608 - costante nostra
                " ORDER BY date_obs IS NULL, date_obs DESC, id DESC"
            )
        ]


def sister_solution(conn, frame):
    """Il cielo MISURATO di un'altra posa dello STESSO OGGETTO, se c'e'.

    La condizione e' l'oggetto, non la sessione: lo stesso oggetto e' lo stesso pezzo di
    cielo anche a un anno di distanza e con un altro corredo, e l'indizio serve solo a
    restringere la ricerca. La sessione invece non basterebbe: e' una stringa
    unita con `|` e i pezzi mancanti diventano vuoti, quindi due pose senza `OBJECT` riprese
    la stessa notte con lo stesso corredo la condividono pur guardando due punti diversi --
    ereditare li' manderebbe il solver nel posto sbagliato. Percio' serve un oggetto, e con
    un nome."""
    if not frame["object_raw"]:
        return None
    return conn.execute(
        "SELECT w.ra_deg, w.dec_deg FROM frame_wcs w JOIN frames f ON f.id = w.frame_id"
        " WHERE f.object_raw = ? AND f.id != ? LIMIT 1",
        (frame["object_raw"], frame["id"]),
    ).fetchone()


def has_metrics(conn, frame_id):
    return conn.execute("SELECT 1 FROM frame_metrics WHERE frame_id = ?", (frame_id,)).fetchone()


def save_wcs(conn, frame_id, *, ra_deg, dec_deg, scale, rotation, width, height, now):  # noqa: PLR0913
    conn.execute(
        "INSERT INTO frame_wcs(frame_id, ra_deg, dec_deg, scale_arcsec_px, rotation_deg,"
        " width_deg, height_deg, solved_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT(frame_id) DO UPDATE SET ra_deg = excluded.ra_deg,"
        " dec_deg = excluded.dec_deg, scale_arcsec_px = excluded.scale_arcsec_px,"
        " rotation_deg = excluded.rotation_deg, width_deg = excluded.width_deg,"
        " height_deg = excluded.height_deg, solved_at = excluded.solved_at",
        (frame_id, ra_deg, dec_deg, scale, rotation, width, height, now),
    )


def detach(conn, frame_ids):
    """Stacca da quelle pose cio' che questo stadio aveva scritto: il cielo trovato e le stelle
    contate. Sono il risultato di una passata che non vale piu'."""
    if not frame_ids:
        return
    with idlist.holding(conn, frame_ids) as listed:
        conn.execute(f"DELETE FROM frame_wcs WHERE frame_id IN {listed}")  # noqa: S608 - lista di id
        conn.execute(f"DELETE FROM frame_metrics WHERE frame_id IN {listed}")  # noqa: S608


# Il `+` davanti a `stage` spegne l'indice degli stadi in coda: senza, la ricerca partirebbe da ogni
# posa risolta dell'archivio invece che dalla lista, anche quando la lista e' vuota.
LOST_SKY = (
    f"SELECT frame_id FROM frame_stages s WHERE frame_id IN {idlist.IN_LIST}"  # noqa: S608 - costante
    " AND +stage = 'solve' AND status = 'done'"
    " AND NOT EXISTS (SELECT 1 FROM frame_wcs w WHERE w.frame_id = s.frame_id)"
)


def lost_sky(conn, frame_ids):
    """Quali di quelle pose questo stadio ha risolto, ma non hanno piu' il cielo trovato: qualcuno
    l'ha staccato (`detach`), e solo il solver lo rimette."""
    with idlist.holding(conn, frame_ids):
        return [r[0] for r in conn.execute(LOST_SKY)]


def save_metrics(conn, frame_id, *, hfd_px, stars, now):
    """HFD e stelle dalla passata di analisi. Gli altri campi restano vuoti: sono di `measure`,
    e un numero che nessuno ha misurato non si scrive."""
    conn.execute(
        "INSERT INTO frame_metrics(frame_id, hfd_px, stars, source, measured_at)"
        " VALUES(?, ?, ?, 'astap', ?)"
        " ON CONFLICT(frame_id) DO UPDATE SET hfd_px = excluded.hfd_px,"
        " stars = excluded.stars, source = excluded.source, measured_at = excluded.measured_at",
        (frame_id, hfd_px, stars, now),
    )
