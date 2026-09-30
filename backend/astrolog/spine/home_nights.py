"""La notte delle pose che non dicono dove sono state fatte **segue il fuso di casa**, e le risposte
per gruppo che portano quella notte nella chiave la seguono.

Vincoli non ovvi:

* **Si riscrive solo chi non ha un fuso dalle coordinate dell'header**, con la regola della
  scansione (`place.timezone_of_frame`): dove le coordinate danno un fuso vale quello, e casa non
  c'entra. Si confronta col
  fuso scritto sulla posa, quindi chiamarla due volte non cambia niente.
* **Il gruppo della camera e' fatto solo di chi non la dice** (`rigless`): una posa con la camera
  nell'header che cambia notte non porta ne' toglie risposte a nessuno.
* **Nelle chiavi la notte e' una data**: la notte UTC del 14 e quella locale del 14 sono la stessa
  chiave, e si sposta solo chi cambia data. Una notte si puo' dividere in due (la risposta va su
  tutte e due le parti) e due notti diventare una: una risposta sola -- o la stessa su tutte e due
  -- va sul gruppo unito, anche sulle pose che non l'avevano; due risposte diverse cadono e la
  domanda torna aperta, perche' scegliere vorrebbe dire inventarne una.
* **Una risposta rimasta senza pose si toglie**: varrebbe per pose diverse che arrivassero domani
  con la stessa data e gli stessi valori.
"""

import json

from ..clock import NIGHT_SQL, night_date
from ..place import timezone_of_frame
from . import declarations as decl
from . import rigless, unnamed
from .night_rig import asks_camera
from .scan_store import home_timezone
from .stages import invalidate

# I posti delle pose che non stanno nel fuso di casa: si chiede il fuso una volta per posto.
_PLACES = "SELECT DISTINCT site_lat, site_lon FROM frames WHERE local_tz IS NOT ?"
_OF_PLACE = """
SELECT f.id, f.local_night, f.night_instant, f.unnamed_key, f.instrument_raw, f.telescope_raw,
  f.naxis1, f.naxis2, f.pixel_size_um
FROM frames f WHERE f.local_tz IS NOT ? AND f.site_lat IS ? AND f.site_lon IS ?
"""
_REWRITE = "UPDATE frames SET local_night = ?, local_tz = ? WHERE id = ?"
_OF_NIGHTS = f"""
SELECT f.id, {NIGHT_SQL} AS night, f.unnamed_key, f.instrument_raw, f.telescope_raw, f.naxis1,
  f.naxis2, f.pixel_size_um
FROM frames f WHERE {NIGHT_SQL} IN (SELECT value FROM json_each(?))
"""  # noqa: S608 - frammento costante


def follow_home(conn):
    """Porta nel fuso di casa di adesso -- o in UTC, senza casa -- la notte delle pose che non
    hanno un fuso dalle coordinate dell'header, sposta le risposte per gruppo che la portano nella
    chiave, e rimette in coda da `normalize` le pose delle notti toccate. La chiama chi cambia casa
    o il suo fuso (`api/sites.py`)."""
    casa = home_timezone(conn)
    moved, riscritte = [], []
    for lat, lon in conn.execute(_PLACES, (casa,)).fetchall():
        if timezone_of_frame(lat, lon, casa) != casa:
            continue  # il fuso viene dalle coordinate
        for r in conn.execute(_OF_PLACE, (casa, lat, lon)).fetchall():
            notte = night_date(r["night_instant"], casa)
            riscritte.append((notte, casa, r["id"]))
            if notte != r["local_night"]:
                moved.append((r, notte))
    conn.executemany(_REWRITE, riscritte)
    if not moved:
        return
    notti = json.dumps(
        sorted({n for _, n in moved} | {r["local_night"] for r, _ in moved}, key=str)
    )
    spostati = {r["id"] for r, _ in moved}
    fermi = [r for r in conn.execute(_OF_NIGHTS, (notti,)) if r["id"] not in spostati]
    rig_fermi = {
        rigless.key_of_row(r, r["night"]) for r in fermi if asks_camera(r["instrument_raw"])
    }
    _carry(conn, decl.GROUP_RIG, _rigless_moves(moved), rig_fermi)
    oggetto_fermi = {r["unnamed_key"] for r in fermi}
    _carry(conn, decl.GROUP_OBJECT, _unnamed_moves(conn, moved), oggetto_fermi)
    invalidate(conn, [r["id"] for r in conn.execute(_OF_NIGHTS, (notti,))], "normalize")


def _rigless_moves(moved):
    """`{chiave nuova: chiavi vecchie}` delle domande sulla camera: la chiave si ricompone dalla
    notte, quindi si sposta da sola, e con lei deve andare la risposta."""
    verso = {}
    for r, notte in moved:
        if asks_camera(r["instrument_raw"]):
            vecchia = rigless.key_of_row(r, r["local_night"])
            verso.setdefault(rigless.key_of_row(r, notte), set()).add(vecchia)
    return verso


def _unnamed_moves(conn, moved):
    """`{chiave nuova: chiavi vecchie}` dei frame senza nome: la chiave e' scritta sulla posa, e si
    risceglie col puntamento nella notte nuova (`unnamed.assign`), dove puo' finire in un gruppo
    che c'era gia'."""
    toccati = sorted(((r["id"], r["unnamed_key"]) for r, _ in moved if r["unnamed_key"]))
    conn.executemany(
        "UPDATE frames SET unnamed_key = NULL WHERE id = ?", [(i,) for i, _ in toccati]
    )
    verso = {}
    for frame_id, vecchia in toccati:
        verso.setdefault(unnamed.assign(conn, frame_id), set()).add(vecchia)
    return verso


def _carry(conn, field, verso, fermi):
    """Porta le risposte `field` dalle chiavi vecchie alle nuove. `fermi` sono le chiavi che le
    pose rimaste al loro posto portano ancora: la risposta di una di quelle vale anche per chi
    arriva. Tutto si legge prima di scrivere, perche' la chiave vecchia di un gruppo puo' essere
    la nuova di un altro."""
    tutte = set(verso).union(*verso.values())
    prima = {k: decl.declared(conn, decl.FRAME_GROUP, k, field) for k in tutte}
    for nuova, vecchie in verso.items():
        fonti = vecchie | ({nuova} if nuova in fermi else set())
        dette = {prima[k] for k in fonti} - {None}
        if len(dette) == 1:
            decl.write_declaration(conn, decl.FRAME_GROUP, nuova, field, dette.pop())
        else:
            decl.forget(conn, decl.FRAME_GROUP, nuova, field)
    for vecchia in tutte - set(verso) - fermi:
        decl.forget(conn, decl.FRAME_GROUP, vecchia, field)
