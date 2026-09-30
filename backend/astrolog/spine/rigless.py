"""Le pose che non dicono con che camera sono state riprese: il corredo della loro notte
(`spine/night_rig.py`), e se la notte non basta la domanda per **gruppo** -- la notte piu' i
valori dell'header che dicono una camera e un'ottica (Marco, 23/9/2026: "si lavora a frame non
cartelle") --, la sua risposta e cosa rimette in coda.

E' la casa comune fra lo stadio che le lascia senza corredo (`normalize`) e la pagina che le chiede.
Ci cadono anche le pose che portano il telescopio ma non la camera -- l'ASIAIR scrive sempre la
montatura in `TELESCOP` -- che finiscono in un corredo mezzo vuoto: la domanda sul filtro passa per
la camera (`spine/unfiltered.py`), quindi senza camera non c'era nemmeno quella.

Vincoli non ovvi:

* **La chiave si compone in un posto solo** (`group_key`), dai GREZZI: notte, `TELESCOP`,
  dimensioni del sensore e pixel. La focale no: varia di poco da un file all'altro, e si propone.
  Una rinomina di pezzi non la tocca, e un file che arriva dopo con gli stessi valori la ritrova.
* **Il gruppo si riconosce dal GREZZO, non dal corredo che la posa ha adesso**: un gruppo a cui si
  e' risposto resta in pagina con la sua risposta, o cambiare idea sarebbe impossibile.
* **La risposta porta i NOMI dei pezzi**, mai i numeri di riga: un'unione cancella la riga
  rilevata, e i pezzi nascono da quei nomi come da un header (`normalize_rig.instrument_named`).
* **Prima della domanda, la notte** (Marco, 23/9/2026): se gli header della stessa notte dicono
  una camera sola, la posa ha quella, e il gruppo non si chiede. Una risposta pero' e' scritta, e
  vince.
"""

import json
import logging

from ..clock import NIGHT_SQL
from ..units import known_focal
from ..vocab.header_value import normalize_header_value
from ..vocab.software import telescope_is_mount
from . import declarations as decl
from . import frame_folder as folder
from . import objects as obj
from .night_rig import NIGHT_OF as _NIGHT_OF
from .night_rig import asks_camera as _asks
from .night_rig import night_rigs
from .stages import invalidate

log = logging.getLogger(__name__)

# I valori dell'header che fanno il gruppo, dopo la notte, nell'ordine della chiave.
_HEADER = "f.telescope_raw, f.naxis1, f.naxis2, f.pixel_size_um"

# Si raggruppa in SQL, mai una riga per posa, e solo fra le pose di una cartella viva che la
# camera non la dicono (`frames.asks_camera`, scritto dalla scansione): una cartella ritirata o un
# file sparito non chiedono niente. La focale e l'oggetto stanno nella riga per la pagina, non
# nella chiave.
_BY_GROUP = f"""
SELECT {NIGHT_SQL} AS night, {_HEADER}, f.focal_mm_raw, f.software,
       {obj.SUBJECT} AS subject, SUM(f.copy_of IS NULL) AS n
FROM frames f {folder.JOIN}
{obj.SUBJECT_JOIN}
WHERE f.asks_camera = 1
GROUP BY night, {_HEADER}, f.focal_mm_raw, f.software, subject
"""  # noqa: S608 - un frammento costante di questo file, non un valore dell'utente

# Le pose vive di una notte con cio' che serve alla loro chiave, copie comprese: chi risponde le
# rimette in coda. `IS` e non `=`, perche' anche "senza data" e' un gruppo.
_POSES_OF_NIGHT = f"""
SELECT f.id, {NIGHT_SQL} AS night, f.instrument_raw, {_HEADER} FROM frames f {folder.JOIN}
WHERE {NIGHT_SQL} IS ?
"""  # noqa: S608 - stesso frammento costante

_NATIVE_FOCAL = "SELECT focal_mm FROM instruments WHERE kind = 'optics' AND name = ?"


def group_key(night, telescope_raw, naxis1, naxis2, pixel_size_um):
    """La chiave del gruppo: un nome, mai da riaprire. `TELESCOP` si normalizza come si cerca una
    regola imparata, cosi' due grafie che differiscono per i bianchi sono lo stesso gruppo."""
    telescope = normalize_header_value(telescope_raw) or None
    return json.dumps([night, telescope, naxis1, naxis2, pixel_size_um])


def key_of_row(r, night):
    """La chiave del gruppo di una riga che porta i valori dell'header, in quella notte: la notte
    va a parte perche' chi la sposta (`spine/home_nights.py`) compone la vecchia e la nuova."""
    return group_key(night, r["telescope_raw"], r["naxis1"], r["naxis2"], r["pixel_size_um"])


def key_of_frame(conn, frame):
    """La chiave del gruppo di questa posa (`frame` porta le colonne di `frames`). Si compone anche
    per una posa che non sta piu' in nessuna cartella viva: la risposta la raggiunge lo stesso, e la
    pagina non la chiede."""
    return key_of_row(frame, conn.execute(_NIGHT_OF, (frame["id"],)).fetchone()["night"])


def _only(valori):
    """L'unica cosa che le pose dicono, o `None` se ne dicono piu' d'una o nessuna: con due focali
    nello stesso gruppo non si sceglie per l'utente, e un vuoto e' "non so"."""
    detti = {v for v in valori if v is not None}
    return detti.pop() if len(detti) == 1 else None


def _native_focal(conn, optics_name):
    """La focale nativa di quell'ottica, dalla sua scheda: e' cio' che la pagina propone quando le
    pose la focale non la dicono. Senza una focale il corredo che nasce dalla risposta resterebbe un
    gemello separato per sempre da quello rilevato (`rigs.rig_for`)."""
    if not optics_name:
        return None
    row = conn.execute(_NATIVE_FOCAL, (optics_name,)).fetchone()
    return None if row is None else row["focal_mm"]


def by_group(conn, only=None):
    """I gruppi di pose che non dicono la camera, il piu' numeroso in cima: la notte e i valori che
    lo fanno (`TELESCOP` in una delle grafie che il gruppo riunisce), quante pose, cio' che le pose
    dicono gia', la focale da proporre e la risposta gia' data. Un gruppo che la notte risolve non
    si chiede, se non ha gia' una risposta.

    `only` tiene un gruppo solo: chi risponde vuole quella riga, e comporre tutta la pagina per
    ognuna delle risposte di un Applica costava **401 query per risposta** (misurato il 12/9/2026 su
    200 gruppi), cioe' il numero di gruppi al quadrato."""
    righe = [(r, key_of_row(r, r["night"])) for r in conn.execute(_BY_GROUP)]
    righe = [(r, k) for r, k in righe if only is None or k == only]
    notti = night_rigs(conn, {r["night"] for r, _ in righe if r["night"]}) if righe else {}
    risposte = {k: answer(conn, k) for k in {k for _, k in righe}}
    gruppi = {}
    for r, chiave in righe:
        if risposte[chiave] is None and r["night"] in notti:
            continue
        scritto = (r["telescope_raw"] or "").strip() or None
        gruppo = gruppi.setdefault(chiave, {
            "key": chiave, "night": r["night"], "telescope": scritto,
            "width_px": r["naxis1"], "height_px": r["naxis2"], "pixel_um": r["pixel_size_um"],
            "frames": 0, "optics": set(), "focal": set(),
        })  # fmt: skip
        gruppo["frames"] += r["n"] or 0
        if r["n"]:  # un oggetto che in quel gruppo ha solo copie non e' un'altra posa
            obj.count_subject(gruppo, r["subject"], r["n"])
        # con l'ASIAIR `TELESCOP` e' la montatura, e lo e' per tutto il gruppo: stessa grafia
        if telescope_is_mount(r["software"]):
            gruppo["mount_named"] = True
        gruppo["optics"].add(decl.instrument_name(conn, "optics", r["telescope_raw"]))
        gruppo["focal"].add(known_focal(r["focal_mm_raw"]))
    out = [_shown(conn, g, risposte[g["key"]]) for g in obj.subjects(conn, gruppi.values())]
    return sorted(out, key=lambda g: (-g["frames"], g["key"]))


def _shown(conn, gruppo, risposta):
    """La riga come la pagina la mostra: cio' che le pose dicono gia' serve a riempire la risposta,
    e la focale nativa dell'ottica si propone solo dove le pose non ne portano una."""
    optics, focal = _only(gruppo.pop("optics")), _only(gruppo.pop("focal"))
    optics = None if gruppo.pop("mount_named", False) else optics
    return {
        **gruppo,
        "optics": optics,
        "focal_mm": focal,
        "focal_suggested": None if focal is not None else _native_focal(conn, optics),
        "answer": risposta,
    }


def row_of(conn, key):
    """La riga di quel gruppo come la pagina la mostra, o `None` se non c'e' piu': e' cosi' che una
    risposta ritrova il gruppo, senza rileggere la chiave a pezzi."""
    return next(iter(by_group(conn, only=key)), None)


def declare(conn, key, optics, camera, focal_mm, now=None):  # noqa: PLR0913
    """La risposta su un gruppo, riscrivibile: si cambia idea rispondendo di nuovo. Si scrivono i
    NOMI di ottica e camera con la focale, mai i numeri di riga: un'unione cancella la riga del
    pezzo, e una risposta scritta sul suo numero non sopravviverebbe a un azzeramento del
    rilevato."""
    dato = {"optics": optics, "camera": camera, "focal_mm": focal_mm}
    decl.write_declaration(conn, decl.FRAME_GROUP, key, decl.GROUP_RIG, json.dumps(dato), now)


def follow_piece(conn, kind, old_name, new_name, now=None):
    """Porta le risposte sui gruppi sul nome nuovo di un'ottica o di una camera, rinominata o unita:
    col nome vecchio, al giro dopo il pezzo rinascerebbe accanto a quello nuovo."""
    for chiave, valore in decl.values_of(conn, decl.FRAME_GROUP, decl.GROUP_RIG):
        dato = _read(valore)
        if dato is not None and dato[kind] == old_name:
            dato[kind] = new_name
            declare(conn, chiave, dato["optics"], dato["camera"], dato["focal_mm"], now)


def _read(value):
    """La risposta salvata, o `None` se la riga non si legge: una riga storta vale **nessuna
    risposta**, e le pose restano dove sono invece di finire su un'ipotesi. La camera e' la sola
    cosa obbligatoria -- e' la domanda -- e senza di lei non c'e' niente da leggere. Una riga che
    non si legge si **dice**: e' una risposta dell'utente che si sta perdendo."""
    if value is None:
        return None  # nessuna risposta non e' una risposta storta: non c'e' niente da dire
    try:
        dato = json.loads(value) if isinstance(value, str) else None
    except ValueError:
        dato = None
    if not isinstance(dato, dict) or not isinstance(dato.get("camera"), str) or not dato["camera"]:
        log.warning("rigless: risposta sul gruppo illeggibile, ignorata")
        return None
    optics = dato.get("optics")
    return {
        "optics": optics if isinstance(optics, str) and optics else None,
        "camera": dato["camera"],
        "focal_mm": known_focal(dato.get("focal_mm")),
    }


def answer(conn, key):
    """La risposta data per quel gruppo, o `None`."""
    return _read(decl.declared(conn, decl.FRAME_GROUP, key, decl.GROUP_RIG) if key else None)


def rig_of_frame(conn, frame):
    """La risposta del gruppo di questa posa, o `None`. Chi normalizza parte dalla posa: la
    dichiarazione si rilegge a ogni giro, ed e' per questo che vale anche per le pose che
    arriveranno con la stessa notte e gli stessi valori."""
    return answer(conn, key_of_frame(conn, frame))


def frames_of(conn, row):
    """Gli id delle pose di quel gruppo, **copie comprese**: un corredo ce l'hanno anche loro, e la
    sessione a cui appartengono lo guarda. A video invece non si contano, come in ogni conteggio."""
    return [
        r["id"] for r in conn.execute(_POSES_OF_NIGHT, (row["night"],))
        if _asks(r["instrument_raw"]) and key_of_row(r, r["night"]) == row["key"]
    ]  # fmt: skip


def requeue(conn, row):
    """Rimette in coda le pose di quel gruppo e le torna. Ci sono anche quelle che una risposta
    precedente aveva gia' sistemato: e' cosi' che si cambia idea."""
    frames = frames_of(conn, row)
    invalidate(conn, frames, "normalize")
    return frames
