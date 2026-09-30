"""Cosa rimette in coda un cambio dei luoghi dichiarati: le pose ferme che quel cambio puo'
sbloccare, le notti di un luogo spostato, e il trasloco delle notti quando cambia casa.

Vincolo non ovvio: si rimette in coda solo cio' che il cambio puo' cambiare. Il resto tornerebbe
uguale, e rifarlo e' lavoro buttato. Le rotte stanno in `api/sites.py`; le regole in
`docs/domini/sito.md`.
"""

import json

from .. import place
from ..db import idlist
from .declarations import COORDINATES_SITE
from .group import NO_ACTIVE_SITE, SAME_PLACE_KM, SITE_NO_TIMEZONE, SITE_UNCLEAR
from .stages import invalidate


def requeue_waiting(conn, *, near=(), names=(), homeless=False):
    """Le pose ferme perche' il posto non si sapeva ripartono quando un cambio dei luoghi puo'
    dire da solo dov'erano: quelle entro `SAME_PLACE_KM` da un punto toccato (`near`), quelle la
    cui risposta nomina un luogo rinominato (`names`), quelle ferme perche' casa non c'era quando
    nasce (`homeless`), e sempre quelle ferme per un luogo senza fuso -- poche per natura, e un
    luogo spostato o tolto puo' dargliene uno anche senza che le loro coordinate lo dicano. Le
    altre tornerebbero uguali: rifarle e' lavoro buttato."""
    chiavi = {
        r[0]
        for r in conn.execute(
            "SELECT entity_key FROM declarations WHERE entity_type = 'coordinates'"
            " AND field = ? AND value IN (SELECT value FROM json_each(?))",
            (COORDINATES_SITE, json.dumps(list(names))),
        )
    }
    frames = []
    for r in conn.execute(
        "SELECT s.frame_id, s.reason, f.site_lat, f.site_lon FROM frame_stages s"
        " JOIN frames f ON f.id = s.frame_id WHERE s.stage = 'group' AND s.status = 'skipped'"
        " AND s.reason IN (?, ?, ?)",
        (SITE_UNCLEAR, NO_ACTIVE_SITE, SITE_NO_TIMEZONE),
    ):
        vicino = any(
            (km := place.distance_km(r["site_lat"], r["site_lon"], *punto)) is not None
            and km <= SAME_PLACE_KM
            for punto in near
        )
        nominato = place.coordinates_key(r["site_lat"], r["site_lon"]) in chiavi
        senza_fuso = r["reason"] == SITE_NO_TIMEZONE
        if vicino or nominato or senza_fuso or (homeless and r["reason"] == NO_ACTIVE_SITE):
            frames.append(r["frame_id"])
    invalidate(conn, frames, "group")


def requeue_nights_of(conn, site_id):
    """Le pose delle notti che l'app aveva dato a quel luogo tornano in coda: spostato, le loro
    coordinate potrebbero non cadere piu' li'."""
    frames = [
        r[0]
        for r in conn.execute(
            "SELECT f.id FROM frames f JOIN nights n ON n.id = f.night_id"
            " WHERE n.site_id = ? AND n.site_source = 'detected'",
            (site_id,),
        )
    ]
    invalidate(conn, frames, "group")


def adopt_nights(conn, site_id, old_home):
    """Le notti che l'APP aveva attribuito alla casa vecchia seguono la nuova, e le loro pose
    si rifanno: quelle senza coordinate restano sulla casa nuova, quelle con le coordinate della
    casa vecchia ci tornano, perche' ora e' un luogo dichiarato come gli altri. Le notti
    dichiarate, e quelle che l'app ha dato a un altro luogo, restano dove sono.

    Cambiare il luogo di casa vuol dire "da adesso osservo di qui", e cio' che era un'ipotesi
    dell'app si aggiorna con lui. Una notte dichiarata e' invece una risposta, e nessuno gliela
    tocca. Una notte che sul nuovo luogo esisterebbe gia' (stessa data) **resta dov'e'**: due
    notti della stessa data sullo stesso luogo il database non le ammette, e far fallire il
    trasloco per un'attribuzione dubbia sarebbe peggio -- le pose non si perdono comunque, e
    quella notte si sposta a mano."""
    # Una data per volta: due notti `detected` della stessa data su due luoghi diversi che
    # traslocassero insieme si scontrerebbero fra loro, e il trasloco fallirebbe.
    da_spostare = [
        r[0]
        for r in conn.execute(
            "SELECT MIN(id) FROM nights WHERE site_source = 'detected' AND site_id = ?"
            " AND night_date NOT IN (SELECT night_date FROM nights WHERE site_id = ?)"
            " GROUP BY night_date",
            (old_home, site_id),
        )
    ]
    if not da_spostare:
        return
    with idlist.holding(conn, da_spostare) as listed:
        conn.execute(
            f"UPDATE nights SET site_id = ? WHERE id IN {listed}",  # noqa: S608 - costante nostra
            (site_id,),
        )
        # E le loro pose tornano in coda: il fuso del luogo nuovo puo' tagliare le notti in un
        # altro punto, e una data calcolata col fuso di prima non e' piu' vera. A ritagliarle e'
        # `group`, che e' l'unico che sa farlo.
        frames = [
            r[0]
            for r in conn.execute(
                f"SELECT id FROM frames WHERE night_id IN {listed}"  # noqa: S608 - costante nostra
            )
        ]
    invalidate(conn, frames, "group")
