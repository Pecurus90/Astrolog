"""I mosaici scritti: pannelli e mosaici li scrive `group` una volta per posa, la risposta chi
risponde, e nessuno li ricalcola (Marco, 23/9/2026). La regola di prodotto sta nel contratto
(`docs/domini/mosaico.md`), il confronto fra due campi in `mosaic_geometry`.

Vincoli non ovvi:

* **Un pannello si misura sulla posa che l'ha aperto**: senza un'ancora ferma una catena di passi
  sotto soglia camminerebbe per il cielo. Dentro una corsa le pose si piazzano in ordine di ripresa.
* **Si confronta coi pannelli del corredo in una fascia di declinazione**, mai con l'archivio:
  due campi si toccano solo se i centri distano meno della somma dei raggi.
* **La chiave del mosaico e' l'impronta di una delle sue pose, scelta quando nasce** e poi
  ferma, anche quando il mosaico cresce o ne assorbe un altro; mai la chiave di un altro mosaico
  vivo. Non porta il corredo. Una posa che cambia camera resta nel suo pannello se il mosaico ha
  una risposta -- il pannello prende il corredo nuovo quando tutte le sue pose ce l'hanno -- e se
  non ce l'ha si ripiazza fra i pannelli del corredo nuovo: non c'e' niente da perdere, e cosi'
  entra nel mosaico che quel corredo ha gia' li'.
* **Una posa senza cielo non sta in un pannello** (`typeless_answer.detach` la stacca), e un
  pannello rimasto vuoto si toglie: altrimenti legherebbe ancora i vicini.
* **Un pannello che lega dei mosaici entra nel piu' vecchio con una risposta** -- o nel piu'
  vecchio, se nessuno ne ha -- e quello si prende gli altri senza risposta: due risposte
  dell'utente non si fondono mai in silenzio.
"""

import json

from . import declarations as decl
from . import mosaic_describe as descrizione
from . import mosaic_proposals as proposte
from . import mosaic_weight as peso
from . import object_answer as risposta
from .identify_geometry import frame_radius_deg, frame_shape
from .mosaic_geometry import PARTIAL, overlap, same_pointing

_SKY = ("ra_deg", "dec_deg", "width_deg", "height_deg", "rotation_deg")

# Le pose da piazzare, col loro cielo, in ordine di ripresa. Le copie non sono un'altra posa.
_POSES = f"""
SELECT f.id, f.frame_hash, f.rig_id, f.panel_id, {", ".join("w." + c for c in _SKY)}
FROM frames f JOIN frame_wcs w ON w.frame_id = f.id
WHERE f.id IN (SELECT value FROM json_each(?)) AND f.copy_of IS NULL
ORDER BY f.date_obs IS NULL, f.date_obs, f.id
"""  # noqa: S608 - frammenti costanti

_BAND = f"""
SELECT id, mosaic_id, {", ".join(_SKY)} FROM panels
WHERE rig_id IS ? AND dec_deg BETWEEN ? AND ?
ORDER BY id
"""  # noqa: S608 - frammenti costanti


def place(conn, frame_ids):
    """Mette ogni posa nel suo pannello, e ogni pannello nuovo nel suo mosaico. Una posa che ne
    ha gia' uno ci resta, salvo che abbia cambiato corredo in un mosaico senza risposta."""
    widest, pannelli = {}, set()
    for pose in map(dict, conn.execute(_POSES, (json.dumps(list(frame_ids)),)).fetchall()):
        if pose["panel_id"] is not None:
            pannelli.add(pose["panel_id"])  # anche quello che lascia: il suo mosaico si ripesa
            if _stays(conn, pose):
                continue
        if frame_shape(pose) is None or frame_radius_deg(pose) is None:
            continue  # senza cielo, o senza le misure del campo, non si sa cosa inquadra
        band = _band(conn, pose, widest)
        panel = next((p for p in band if same_pointing(p, pose)), None)
        panel_id = panel["id"] if panel else _open(conn, pose, band, widest)
        conn.execute("UPDATE frames SET panel_id = ? WHERE id = ?", (panel_id, pose["id"]))
        pannelli.add(panel_id)
    settle(conn, _mosaics_of(conn, pannelli))


def settle(conn, mosaic_ids):
    """I mosaici in cui delle pose sono arrivate o da cui se ne sono andate: i pannelli vuoti
    tolti, e quei mosaici ripesati, col loro centro, il loro nome e le chiavi sulle pose. Solo
    quelli: gli altri non sono cambiati, e ripesarli tutti costerebbe l'archivio a ogni corsa."""
    _sweep(conn)
    vivi = [
        r[0]
        for r in conn.execute(
            "SELECT id FROM mosaics WHERE id IN (SELECT value FROM json_each(?))",
            (json.dumps(sorted(mosaic_ids)),),
        )
    ]
    peso.weigh(conn, vivi)
    for mosaic_id in vivi:
        descrizione.describe(conn, mosaic_id)
        _write_key(conn, mosaic_id)
    conn.execute(
        "UPDATE frames SET mosaic_key = NULL WHERE mosaic_key IS NOT NULL AND mosaic_key NOT IN"  # noqa: S608
        f" (SELECT m.key FROM mosaics m JOIN ({proposte.LIVE}) r ON r.mosaic_id = m.id)"
    )


def _mosaics_of(conn, panel_ids):
    """I mosaici di quei pannelli: si chiede prima di togliere quelli rimasti vuoti."""
    return {
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT mosaic_id FROM panels WHERE id IN (SELECT value FROM json_each(?))"
            " AND mosaic_id IS NOT NULL",
            (json.dumps(sorted(panel_ids)),),
        )
    }


def leave(conn, frame_ids):
    """Stacca quelle pose dal loro pannello e dal loro mosaico: hanno perso il cielo, o sono
    passate a un corredo in cui si ripiazzano. Torna i mosaici che lasciano, da ripesare
    (`settle`): dopo lo stacco non lo dice piu' niente."""
    lista = json.dumps(list(frame_ids))
    lasciati = _mosaics_of(
        conn,
        [r[0] for r in conn.execute(
            "SELECT panel_id FROM frames WHERE id IN (SELECT value FROM json_each(?))"
            " AND panel_id IS NOT NULL", (lista,),
        )],
    )  # fmt: skip
    conn.execute(
        "UPDATE frames SET panel_id = NULL, mosaic_key = NULL"
        " WHERE id IN (SELECT value FROM json_each(?))",
        (lista,),
    )
    return lasciati


def _stays(conn, pose):
    """Se la posa resta nel suo pannello: si', se il corredo e' lo stesso o se il suo mosaico ha
    una risposta -- e il pannello prende il corredo nuovo quando tutte le sue pose ce l'hanno.
    Altrimenti si stacca."""
    row = conn.execute(
        "SELECT p.rig_id, m.key FROM panels p LEFT JOIN mosaics m ON m.id = p.mosaic_id"
        " WHERE p.id = ?",
        (pose["panel_id"],),
    ).fetchone()
    if row["rig_id"] == pose["rig_id"]:
        return True
    if row["key"] is not None and answer_of(conn, row["key"]) is not None:
        conn.execute(
            "UPDATE panels SET rig_id = ? WHERE id = ? AND NOT EXISTS"
            " (SELECT 1 FROM frames f WHERE f.panel_id = ? AND f.rig_id IS NOT ?)",
            (pose["rig_id"], pose["panel_id"], pose["panel_id"], pose["rig_id"]),
        )
        return True
    leave(conn, [pose["id"]])
    return False


def _sweep(conn):
    """I pannelli rimasti senza pose e i mosaici rimasti senza pannelli, tolti."""
    conn.execute(
        "DELETE FROM panels WHERE NOT EXISTS (SELECT 1 FROM frames f WHERE f.panel_id = panels.id)"
    )
    conn.execute(
        "DELETE FROM mosaics WHERE NOT EXISTS"
        " (SELECT 1 FROM panels p WHERE p.mosaic_id = mosaics.id)"
    )


def write_answer(conn, key, value, now=None):
    """La risposta su un mosaico -- `decl.MOSAIC_NO` o il suo bersaglio -- scritta una volta, e
    la chiave del si' sulle sue pose. Un mosaico che non c'e', o che e' rimasto un pannello solo,
    e' una pagina vecchia, e si dice: una risposta verso il nulla resterebbe li' senza che
    nessuno la veda."""
    row = conn.execute(
        f"SELECT m.id FROM mosaics m JOIN ({proposte.LIVE}) r ON r.mosaic_id = m.id"  # noqa: S608
        " WHERE m.key = ?",
        (key,),
    ).fetchone()
    if row is None:
        raise LookupError(f"mosaico {key}")
    decl.write_declaration(conn, decl.MOSAIC, key, decl.MOSAIC_FIELD, value, now)
    _write_key(conn, row["id"])


def answer_of(conn, key):
    """Il valore scritto su quel mosaico, o `None` se nessuno ha risposto."""
    return decl.declared(conn, decl.MOSAIC, key, decl.MOSAIC_FIELD)


def _band(conn, pose, widest):
    """I pannelli del corredo della posa che potrebbero toccarla: i centri piu' vicini della
    somma dei raggi, in declinazione. L'ascensione retta la guarda la geometria. Il raggio piu'
    largo del corredo si chiede una volta per corsa (`widest`), non una per posa."""
    rig = pose["rig_id"]
    if rig not in widest:
        (widest[rig],) = conn.execute(
            "SELECT COALESCE(MAX(radius_deg), 0) FROM panels WHERE rig_id IS ?", (rig,)
        ).fetchone()
    reach = widest[rig] + (frame_radius_deg(pose) or 0.0)
    righe = conn.execute(_BAND, (pose["rig_id"], pose["dec_deg"] - reach, pose["dec_deg"] + reach))
    return [dict(r) for r in righe]


def _open(conn, pose, band, widest):
    """Un pannello nuovo col cielo di questa posa, e il mosaico dei pannelli che tocca."""
    radius = frame_radius_deg(pose) or 0.0
    widest[pose["rig_id"]] = max(widest.get(pose["rig_id"], 0.0), radius)
    panel_id = conn.execute(
        f"INSERT INTO panels(rig_id, {', '.join(_SKY)}, radius_deg) VALUES(?, ?, ?, ?, ?, ?, ?)",  # noqa: S608
        (pose["rig_id"], *(pose[c] for c in _SKY), radius),
    ).lastrowid
    touching = [p for p in band if overlap(p, pose) == PARTIAL]
    if touching:
        _join(conn, panel_id, pose["frame_hash"], touching)
    return panel_id


def _join(conn, panel_id, frame_hash, touching):
    """Il pannello nuovo e quelli che tocca in un mosaico: quello che c'e' gia', o uno nuovo."""
    ids = sorted({p["mosaic_id"] for p in touching if p["mosaic_id"] is not None})
    keys = dict(
        conn.execute(
            "SELECT id, key FROM mosaics WHERE id IN (SELECT value FROM json_each(?))",
            (json.dumps(ids),),
        ).fetchall()
    )
    answered = [i for i in ids if answer_of(conn, keys[i]) is not None]
    if ids:
        target = answered[0] if answered else ids[0]
        merged = [i for i in ids if i != target and i not in answered]
    else:
        # la stessa chiave torna se le stesse pose rifanno lo stesso mosaico: la sua risposta c'e'
        target = conn.execute(
            "INSERT INTO mosaics(key, ra_deg, dec_deg, proposed) VALUES(?, 0, 0, '')"
            " ON CONFLICT(key) DO UPDATE SET key = excluded.key RETURNING id",
            (_new_key(conn, touching, frame_hash),),
        ).fetchone()[0]
        merged = []
    for i in merged:
        conn.execute("UPDATE panels SET mosaic_id = ? WHERE mosaic_id = ?", (target, i))
        conn.execute("DELETE FROM mosaics WHERE id = ?", (i,))
    free = [p["id"] for p in touching if p["mosaic_id"] is None] + [panel_id]
    conn.executemany("UPDATE panels SET mosaic_id = ? WHERE id = ?", [(target, i) for i in free])


def _new_key(conn, panels, frame_hash):
    """La chiave di un mosaico nuovo: l'impronta della posa piu' vecchia di quei pannelli -- una
    senza data dopo tutte -- che non sia gia' la chiave di un mosaico vivo. Una posa che ha
    cambiato corredo porta con se' la chiave del mosaico da cui e' uscita, e riusarla lo
    riunirebbe a questo attraverso due corredi."""
    for (candidate,) in conn.execute(
        "SELECT frame_hash FROM frames WHERE panel_id IN (SELECT value FROM json_each(?))"
        " ORDER BY date_obs IS NULL, date_obs, id",
        (json.dumps([p["id"] for p in panels]),),
    ):
        if not _alive(conn, candidate):
            return candidate
    return frame_hash


def _alive(conn, key):
    """Se c'e' un mosaico con quella chiave e con almeno un pannello."""
    return (
        conn.execute(
            "SELECT 1 FROM mosaics m JOIN panels p ON p.mosaic_id = m.id WHERE m.key = ? LIMIT 1",
            (key,),
        ).fetchone()
        is not None
    )


def _write_key(conn, mosaic_id):
    """Sulle pose del mosaico la sua chiave se e' un si', niente se e' un no o una domanda; e
    niente su quelle dei pannelli che non contano (`mosaic_weight`): restano col loro oggetto."""
    (key,) = conn.execute("SELECT key FROM mosaics WHERE id = ?", (mosaic_id,)).fetchone()
    confirmed = key if risposta.mosaic_word(answer_of(conn, key)) == decl.MOSAIC_YES else None
    conn.execute(
        "UPDATE frames SET mosaic_key = CASE WHEN p.counts_in_mosaic = 1 THEN ? END"
        " FROM panels p WHERE frames.panel_id = p.id AND p.mosaic_id = ?",
        (confirmed, mosaic_id),
    )
