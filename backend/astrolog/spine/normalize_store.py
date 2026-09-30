"""Le scritture di `normalize`: le specifiche di una camera, le focali in attesa e il legame col
frame. Query statiche, nessuna decisione: chi decide e' `normalize.py`. Far **nascere** un pezzo o
un filtro e' di `gear_create`, trovare o creare un corredo per impronta di `rigs`: servono anche a
chi scrive a mano, e lo store di uno stadio e' solo suo.
"""

from ..db import idlist
from . import counts


def frame(conn, frame_id):
    return conn.execute("SELECT * FROM frames WHERE id = ?", (frame_id,)).fetchone()


def none_filter_id(conn):
    """La riga "nessun filtro", una sola nell'archivio, o None. Si cerca per `is_none` e non per
    nome: l'utente puo' averla rinominata."""
    row = conn.execute("SELECT id FROM filters WHERE is_none = 1").fetchone()
    return None if row is None else row["id"]


# Per ogni camera, i file che la usano raggruppati per cio' che dicono: poche righe, non una per
# posa. Ogni camera c'e', anche senza pose (`n` a zero), perche' possa dimenticare cio' che le
# pose dicevano. Le copie riscritte non votano, perche' non sono un'altra posa.
_CAMERA_VOTES = """
SELECT i.id AS camera_id, i.name AS camera, f.pixel_size_um, f.binning,
       f.bayer_pattern IS NOT NULL AS color, COUNT(f.id) AS n
FROM instruments i
LEFT JOIN rigs r ON r.camera_id = i.id
LEFT JOIN frames f ON f.rig_id = r.id AND f.copy_of IS NULL AND f.id NOT IN {listed}
WHERE i.kind = 'camera'
GROUP BY i.id, f.pixel_size_um, f.binning, color
"""


def camera_votes(conn, leaving_out=()):
    """Le righe del voto; `leaving_out` sono le pose che non votano col corredo che hanno adesso."""
    with idlist.holding(conn, leaving_out) as listed:
        return conn.execute(_CAMERA_VOTES.format(listed=listed)).fetchall()


def camera_colours(conn):
    """`{id della camera: (nome, colore votato)}`, prima che un voto nuovo lo riscriva."""
    rows = conn.execute("SELECT id, name, camera_type FROM instruments WHERE kind = 'camera'")
    return {r["id"]: (r["name"], r["camera_type"]) for r in rows}


def set_camera_specs(conn, camera_id, camera_type, pixel_size_um):
    conn.execute(
        "UPDATE instruments SET camera_type = ?, pixel_size_um = ?"
        " WHERE id = ? AND (camera_type IS NOT ? OR pixel_size_um IS NOT ?)",
        (camera_type, pixel_size_um, camera_id, camera_type, pixel_size_um),
    )


# Le nidiate delle pose date: tutti i frame che dicono di essere lo stesso scatto di una di loro
# (stessa data, stessa camera, stessa esposizione). Chi non ne dice uno dei tre non ha nidiata:
# su un dato assente non si afferma niente, e `NULL = NULL` legherebbe pose vere fra loro.
_BROODS = """
SELECT f.id, f.date_obs, f.instrument_raw, f.exposure_s, f.software_raw, f.header_json, f.copy_of
FROM frames f JOIN (
    SELECT DISTINCT date_obs, instrument_raw, exposure_s FROM frames WHERE id IN {listed}
    AND date_obs IS NOT NULL AND instrument_raw IS NOT NULL AND exposure_s IS NOT NULL
) k ON f.date_obs = k.date_obs AND f.instrument_raw = k.instrument_raw
   AND f.exposure_s = k.exposure_s
ORDER BY f.date_obs, f.instrument_raw, f.exposure_s
"""


def broods(conn, frame_ids):
    """Le righe una alla volta, non un elenco: chi le legge tiene di ognuna solo cio' che gli
    serve, e gli header di tutta la coda non stanno in memoria insieme. L'elenco resta preso
    finche' la lettura non finisce (`db/idlist.py`, la rientranza)."""
    with idlist.holding(conn, frame_ids) as listed:
        yield from conn.execute(_BROODS.format(listed=listed))


def pending_focals(conn, frame_ids):
    """Le focali grezze dei frame in coda: servono tutte insieme per raggrupparle prima di
    scrivere, cosi' l'ordine dei file non cambia i corredi."""
    with idlist.holding(conn, frame_ids) as listed:
        return [
            r[0]
            for r in conn.execute(
                f"SELECT DISTINCT focal_mm_raw FROM frames WHERE id IN {listed}"  # noqa: S608
            )
        ]


def set_normalized(conn, frame_id, *, filter_id, rig_id, software, copy_of, rewrite_mark, on_frame):  # noqa: PLR0913
    """`on_frame` sono gli strumenti che la posa nomina addosso a se', per genere: le colonne si
    chiamano come il genere piu' `_id`, e chi non c'e' arriva `None`. I generi li elenca
    `counts.CARRIED`, che e' la casa sola."""
    colonne = "".join(f", {k}_id = ?" for k in counts.CARRIED)
    conn.execute(
        "UPDATE frames SET filter_id = ?, rig_id = ?, software = ?, copy_of = ?,"  # noqa: S608 - generi nostri, mai valori dell'utente
        f" rewrite_mark = ?{colonne} WHERE id = ?",
        (
            filter_id,
            rig_id,
            software,
            copy_of,
            rewrite_mark,
            *(on_frame[k] for k in counts.CARRIED),
            frame_id,
        ),
    )
