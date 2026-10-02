"""Le pose **senza nome e senza cielo**, raggruppate per **notte, camera, telescopio e
puntamento** (Marco, 24/9/2026: "si lavora a frame non cartelle", e due oggetti della stessa notte
si separano col puntamento): il gruppo, la domanda, la risposta e la regola che ne esce. `identify`,
senza un nome e senza il cielo, non ha niente da cui dedurre un oggetto, e legge qui l'oggetto del
gruppo.

Vincoli non ovvi:

* **Il gruppo si sceglie quando la posa arriva e si scrive su di lei** (`frames.unnamed_key`,
  Marco, 25/9/2026; si risceglie solo se casa cambia fuso, `spine/home_nights.py`): chi arriva
  entra nel gruppo della sua notte, camera e telescopio il cui puntamento dista meno di un campo
  inquadrato dal suo, altrimenti ne apre uno. Una griglia fissa avrebbe dei bordi, e il dithering
  a cavallo di un bordo spezzerebbe lo stesso oggetto in due domande. Chi legge legge la chiave, e
  non ricompone niente.
* **Il gruppo si confronta col puntamento di chi l'ha aperto**, che sta nella chiave: confrontarlo
  con ogni posa del gruppo lo farebbe allungare a catena. Senza puntamento, focale o pixel il campo
  non si sa, e la posa va nel gruppo della notte senza puntamento.
* **Il gruppo si riconosce dalla POSA, mai dallo stato dello stadio**: la chiave, e nessun cielo
  misurato a solver concluso. Lo stato di `identify` una rimessa in coda lo azzera; la chiave no,
  anche se a sceglierla e' `identify`: una posa che lui non ha ancora visto non si chiede.
* **Il cielo che non dice niente vale come nessun cielo**: una posa risolta il cui cono non ha
  trovato niente sta nel gruppo (`frames.empty_cone`, che scrive `identify`). Dove il cielo ha dei
  candidati decide lui, e la risposta non la sposta.
* **Si risponde con un oggetto** -- uno slug di catalogo o un nome -- **oppure "non e' un
  oggetto"**, e la risposta vale anche per le pose che arriveranno nello stesso gruppo.
"""

import json
from typing import cast

from ..clock import NIGHT_SQL, local_iso
from ..units import angular_separation_deg, field_deg, scale_arcsec_px
from ..vocab.header_value import normalize_header_value
from . import declarations as decl
from . import frame_folder as folder
from . import object_answer as risposta
from .stages import WAITING_SQL, invalidate

NONE = "none"  # "non e' un oggetto": il valore che si scrive, e il tipo della risposta

_OF_FRAME = f"""
SELECT f.unnamed_key, {NIGHT_SQL} AS night, f.instrument_raw, f.telescope_raw, f.ra_hint_deg,
  f.dec_hint_deg, f.focal_mm_raw, f.pixel_size_um, f.naxis1, f.naxis2
FROM frames f WHERE f.id = ?
"""  # noqa: S608 - frammento costante della spina

# I gruppi gia' aperti in quella notte. `IS` e non `=`, perche' anche "senza data" e' un gruppo.
_GROUPS_OF_NIGHT = """
SELECT DISTINCT unnamed_key FROM frames
WHERE unnamed_key IS NOT NULL AND json_extract(unnamed_key, '$[0]') IS ?
"""

# Le pose di cui il cielo non dice niente, a solver concluso, nelle cartelle vive: senza cielo
# misurato, o col cono vuoto. Le copie non si contano. **Fuori chi aspetta di sapere che file e'**
# (`spine/typeless.py`), con la stessa regola di chi e' pronto: qui la domanda sarebbe un'altra,
# e rispondere con un oggetto trasformerebbe una calibrazione in ore. Il solver concluso e' un
# `EXISTS` e non una giunzione: con la giunzione SQLite parte dagli stadi del cielo, cioe' da ogni
# posa dell'archivio, invece che dalle poche senza nome.
_BY_GROUP = f"""
SELECT f.unnamed_key AS key, MIN(f.instrument_raw) AS instrument_raw,
  MIN(f.telescope_raw) AS telescope_raw, SUM(f.copy_of IS NULL) AS n,
  MIN(f.date_obs) AS first_frame, MAX(f.date_obs) AS last_frame, MIN(f.local_tz) AS tz
FROM frames f {folder.JOIN}
WHERE f.unnamed_key IS NOT NULL AND NOT ({WAITING_SQL}) AND EXISTS (
  SELECT 1 FROM frame_stages so WHERE so.frame_id = f.id AND so.stage = 'solve'
    AND so.status <> 'pending') AND (
  f.empty_cone = 1 OR NOT EXISTS (SELECT 1 FROM frame_wcs w WHERE w.frame_id = f.id))
GROUP BY f.unnamed_key
"""  # noqa: S608 - frammenti costanti della spina

# Le pose vive del gruppo, copie e pose col cielo comprese: chi risponde le rimette in coda, ed e'
# `identify` a rifare la scelta.
_POSES_OF_GROUP = f"SELECT f.id FROM frames f {folder.JOIN} WHERE f.unnamed_key = ?"  # noqa: S608


def _field(r):
    """Il lato corto del campo inquadrato, in gradi, o `None` se manca un dato."""
    lati = [p for p in (r["naxis1"], r["naxis2"]) if p]
    return (
        field_deg(min(lati), scale_arcsec_px(r["pixel_size_um"], r["focal_mm_raw"]))
        if lati
        else None
    )


def assign(conn, frame_id):
    """Il gruppo di questa posa: quello gia' scritto, o quello della sua notte, camera e telescopio
    il cui puntamento dista meno di un campo, il piu' vicino; altrimenti uno nuovo, che si apre col
    puntamento di questa posa. Si scrive sulla posa e la chiave si torna."""
    r = conn.execute(_OF_FRAME, (frame_id,)).fetchone()
    if r["unnamed_key"]:
        return r["unnamed_key"]
    camera = normalize_header_value(r["instrument_raw"]) or None
    telescope = normalize_header_value(r["telescope_raw"]) or None
    ra, dec, campo = r["ra_hint_deg"], r["dec_hint_deg"], _field(r)
    if ra is None or dec is None or campo is None:
        ra = dec = campo = None
    chiave = json.dumps([r["night"], camera, telescope, ra, dec])
    vicini = []
    for (altra,) in conn.execute(_GROUPS_OF_NIGHT, (r["night"],)):
        _, c, t, a_ra, a_dec = json.loads(altra)
        if (c, t) != (camera, telescope) or (a_ra is None) != (campo is None):
            continue
        if campo is None:
            vicini.append((0.0, altra))
        # A field exists only with a pointing.
        elif (
            distanza := angular_separation_deg(cast("float", ra), cast("float", dec), a_ra, a_dec)
        ) < campo:
            vicini.append((distanza, altra))
    if vicini:
        chiave = min(vicini)[1]
    conn.execute("UPDATE frames SET unnamed_key = ? WHERE id = ?", (chiave, frame_id))
    return chiave


def key_of_frame(conn, frame_id):
    """La chiave scritta su questa posa, o `None` se non ne ha."""
    return conn.execute("SELECT unnamed_key FROM frames WHERE id = ?", (frame_id,)).fetchone()[0]


def _written(value):
    """Come la pagina mostra un grezzo dell'header: senza i bianchi, o `None` se non dice niente."""
    return (value or "").strip() or None


def by_group(conn, only=None):
    """I gruppi di pose senza nome e senza cielo, il piu' numeroso in cima: la notte, la camera, il
    telescopio e il puntamento di chi l'ha aperto, con la risposta gia' data; `only` tiene un
    gruppo solo, per chi risponde. Un gruppo con sole copie non chiede niente."""
    out = []
    for r in conn.execute(_BY_GROUP):
        if not r["n"] or (only is not None and r["key"] != only):
            continue
        notte, _, _, ra, dec = json.loads(r["key"])
        out.append({
            "key": r["key"], "night": notte, "camera": _written(r["instrument_raw"]),
            "telescope": _written(r["telescope_raw"]), "ra_deg": ra, "dec_deg": dec,
            "frames": r["n"], "answer": answer(conn, r["key"]),
            # dalla prima all'ultima posa, nel fuso della notte: due oggetti senza puntamento nella
            # stessa notte sono una domanda sola, e le ore dicono se sono una serie o due. Contano
            # le pose che dicono l'ora (quella del file non e' un'ora di ripresa), e il fuso e'
            # quello delle pose che ne hanno uno: senza, l'ora resta in UTC
            "first_frame": local_iso(r["first_frame"], r["tz"]),
            "last_frame": local_iso(r["last_frame"], r["tz"]),
        })  # fmt: skip
    return sorted(out, key=lambda g: (-g["frames"], g["key"]))


def row_of(conn, key):
    """La riga di quel gruppo come la pagina la mostra, o `None` se non c'e' piu'."""
    return next(iter(by_group(conn, only=key)), None)


def declare(conn, key, *, slug=None, name=None, not_an_object=False, now=None):  # noqa: PLR0913
    """La risposta su un gruppo, riscrivibile: si cambia idea rispondendo di nuovo. Uno slug che il
    catalogo non ha si rifiuta prima di scrivere."""
    risposta.refuse_unknown_slug(conn, slug)
    slug, name = risposta.resolved(conn, slug, name)
    value = NONE if not_an_object else risposta.target_value(slug, name)
    decl.write_declaration(conn, decl.FRAME_GROUP, key, decl.GROUP_OBJECT, value, now)
    if not not_an_object:
        # l'oggetto l'ha nominato l'utente: non torna in pagina a chiedere di essere confermato
        decl.confirm(conn, "object", slug or name, now)


def answer(conn, key):
    """La risposta data per quel gruppo -- `{"kind": "catalog" | "name" | "none", "value", "name"}`,
    dove `name` e' come si mostra -- o `None`. Una riga storta vale nessuna risposta, e
    `read_target` la dice nel log. Anche una voce di catalogo che non c'e' piu': le pose restano
    una domanda (`named_by_group`), e il gruppo non puo' dirsi risposto mentre loro aspettano."""
    value = decl.declared(conn, decl.FRAME_GROUP, key, decl.GROUP_OBJECT) if key else None
    if value is None:
        return None
    if value == NONE:
        return {"kind": NONE, "value": None, "name": None}
    detto = risposta.shown_target(conn, value)
    if detto is None:
        return None
    kind, valore, nome = detto
    return {"kind": kind, "value": valore, "name": nome}


def requeue(conn, row):
    """Rimette in coda le pose di quel gruppo e le torna: ci sono anche quelle che una risposta
    precedente aveva gia' sistemato, ed e' cosi' che si cambia idea. Tutte, copie e pose col cielo
    comprese: e' `identify` a rifare la scelta, e dove il cielo ha candidati la rifa' uguale."""
    frames = [r["id"] for r in conn.execute(_POSES_OF_GROUP, (row["key"],))]
    invalidate(conn, frames, "identify")
    return frames


def named_by_group(conn, key):
    """Per `identify`, su una posa senza nome e senza candidati: `(nome, voce di catalogo)` del
    bersaglio detto per il suo gruppo, `NONE` se l'utente ha detto che non e' un oggetto, `None`
    se non ha detto niente -- o se lo slug non c'e' piu' nel catalogo: la parola dell'utente sposta
    delle pose, mai le fa sparire."""
    detto = answer(conn, key)
    if detto is None:
        return None
    if detto["kind"] == NONE:
        return NONE
    if detto["kind"] == "name":
        return detto["value"], None
    return risposta.catalog_target(conn, detto["value"])
