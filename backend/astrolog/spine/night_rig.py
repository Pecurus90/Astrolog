"""Il **corredo della notte**: cio' che le pose di una notte dicono dell'attrezzatura, per la posa
che non lo dice.

Una posa senza camera prende quella della sua notte, se gli header ne dicono una sola (Marco,
23/9/2026); e se non dice l'ottica, prende quella della notte quando la notte ne dice una sola a
una focale sola, con la focale se la posa non la dice -- senza, nasceva un corredo senza ottica
accanto a quello delle pose complete. Una focale sua diversa non prende l'ottica. Lo usano
`normalize` (`normalize_rig.rig_for_frame`) e la domanda sulla camera (`spine/rigless.py`), che un
gruppo risolto dalla notte non lo chiede.

Vincolo non ovvio: **si legge dal grezzo**, software compreso: le pose della notte possono non
essere ancora normalizzate quando la si chiede, e la colonna normalizzata sarebbe vuota.
"""

import json

from ..clock import NIGHT_SQL
from ..units import known_focal, same_focal
from ..vocab.header_value import normalize_header_value
from ..vocab.software import normalize_software, telescope_is_mount
from . import declarations as decl


def rigs_by_night(listed):
    """Cio' che le pose di una notte dicono dell'attrezzatura: una riga per notte e grezzi, mai per
    posa. Con `listed` solo le notti di un elenco JSON, che si cercano con l'indice."""
    dove = f"{NIGHT_SQL} IN (SELECT value FROM json_each(?))" if listed else "1"  # noqa: S608
    return f"""
SELECT {NIGHT_SQL} AS night, f.instrument_raw, f.telescope_raw, f.software_raw, f.focal_mm_raw
FROM frames f WHERE {NIGHT_SQL} IS NOT NULL AND f.instrument_raw IS NOT NULL AND {dove}
GROUP BY night, f.instrument_raw, f.telescope_raw, f.software_raw, f.focal_mm_raw
"""  # noqa: S608 - frammenti costanti


# La notte della posa in SQL e non con `clock.night_date`: deve essere la stessa chiave del
# raggruppamento, e con il fuso scritto nella data le due lingue non concordano.
NIGHT_OF = f"SELECT {NIGHT_SQL} AS night FROM frames f WHERE f.id = ?"  # noqa: S608

_RAW_OF = "SELECT id, instrument_raw FROM frames WHERE id IN (SELECT value FROM json_each(?))"

# Le pose delle notti di queste pose: la notte puo' aver cambiato la loro camera.
_IN_NIGHTS_OF = f"""
SELECT f.id, f.instrument_raw FROM frames f
WHERE {NIGHT_SQL} IN (
  SELECT {NIGHT_SQL} FROM frames f WHERE f.id IN (SELECT value FROM json_each(?))
)
"""  # noqa: S608 - frammento costante


def asks_camera(instrument_raw):
    """Se quella posa non dice con che camera e' stata ripresa. Si guarda il grezzo con la stessa
    normalizzazione con cui si cerca la regola imparata (`declarations.instrument_name`): un valore
    che si riduce a niente -- soli bianchi, o il solo indice di istanza ASCOM -- non e' un nome."""
    return not normalize_header_value(instrument_raw)


def night_rigs(conn, nights=None):
    """`{notte: corredo}` per le notti in cui gli header dicono una camera sola. Il corredo porta
    l'ottica e la focale solo se la notte ne dice **una**, e "nessuna ottica" dell'ASIAIR e' una
    risposta anch'essa; se no porta la camera sola. Le grafie passano dalla regola imparata.

    `nights` tiene solo quelle notti: il corredo di una notte dipende solo dalle sue pose, e chi ne
    chiede poche non deve leggere l'archivio intero."""
    per_notte, nomi = {}, {}
    if nights is None:
        righe = conn.execute(rigs_by_night(False))
    else:
        righe = conn.execute(rigs_by_night(True), (json.dumps(sorted(nights)),))

    def nome(kind, grafia):  # una grafia si risolve una volta, non una per notte
        if (kind, grafia) not in nomi:
            nomi[kind, grafia] = decl.instrument_name(conn, kind, grafia) if grafia else None
        return nomi[kind, grafia]

    for r in righe:
        if (camera := nome("camera", r["instrument_raw"])) is None:
            continue
        mount = telescope_is_mount(normalize_software(r["software_raw"]))
        ottica = None if mount else nome("optics", r["telescope_raw"])
        visto = (camera, ottica, known_focal(r["focal_mm_raw"]))
        per_notte.setdefault(r["night"], []).append(visto)
    corredi = {notte: _rig_of(viste) for notte, viste in per_notte.items()}
    return {notte: corredo for notte, corredo in corredi.items() if corredo is not None}


def _rig_of(viste):
    """Il corredo di una notte dalle sue terne (camera, ottica, focale), o `None` se le camere sono
    piu' d'una."""
    camere, ottiche = {v[0] for v in viste}, {v[1] for v in viste}
    if len(camere) != 1:
        return None
    focali = [v[2] for v in viste]
    intero = len(ottiche) == 1 and all(same_focal(focali[0], f) for f in focali)
    return {
        "camera": camere.pop(),
        "optics": ottiche.pop() if intero else None,
        "focal_mm": focali[0] if intero else None,
    }


def rig_of_night(conn, frame, rigs):
    """Il corredo della notte di questa posa in `rigs` (`night_rigs`), o `None`."""
    return rigs.get(conn.execute(NIGHT_OF, (frame["id"],)).fetchone()["night"])


def in_nights_of(conn, frame_ids):
    """Le pose senza camera delle notti in cui cade una di queste pose che la camera la dice: il
    corredo della loro notte puo' essere cambiato, e chi normalizza le rimette in coda."""
    dicono = [r["id"] for r in conn.execute(_RAW_OF, (json.dumps(list(frame_ids)),))
              if not asks_camera(r["instrument_raw"])]  # fmt: skip
    if not dicono:
        return []
    rows = conn.execute(_IN_NIGHTS_OF, (json.dumps(dicono),))
    return [r["id"] for r in rows if asks_camera(r["instrument_raw"])]
