"""Cosa scrive una risposta di Da confermare, e cosa rimette in coda.

Le rotte e la pagina che si legge stanno in `review.py`; le regole vere -- cosa vuol dire
unire due grafie, dichiarare un filtro, correggere un oggetto -- stanno nella spina
(`spine.declarations`, `spine.gear`). Qui c'e' l'ordine in cui si applicano, e nient'altro.

Vincolo non ovvio: si confermano gli oggetti che la pagina LETTA elencava (il suo `seen`), non cio'
che c'e' in tabella al momento del clic: fra le due cose puo' essersi infilata una scansione, e
quelle voci nessuno le ha ancora viste.
"""

import sqlite3
from contextlib import contextmanager

from fastapi import HTTPException

from ..db.transaction import transaction
from ..spine import coordinates as places
from ..spine import declarations as decl
from ..spine import gear, gear_create, mosaic
from ..spine import object_answer as risposta
from ..spine import objects as obj
from ..spine import rigs as corredi
from ..spine import unfiltered as unfiltered_reader
from ..spine.group import SITE_UNCLEAR
from ..spine.stages import invalidate
from . import instrument_answer as strumento
from . import lookalike
from . import review_page as page
from . import review_write_folders as folders
from .models_review import ReviewSeen

# I vincoli del database tradotti in parole che una pagina puo' mostrare.
_CONSTRAINT_CODES = {
    "filters.name": "name_taken",
    "instruments.kind": "name_taken",
    "filters.is_none": "none_filter_exists",
}


# Il numero di riga piu' grande che SQLite ammette: il limite di chi non manda `seen` e sta
# chiedendo un'altra cosa -- "conferma cio' che c'e' adesso". La pagina il suo `seen` ce l'ha.
_TUTTO = 2**63 - 1
_SENZA_LIMITI = ReviewSeen(objects=_TUTTO)


def confirm_seen(conn, seen, now):
    """Applica vuol dire "ho visto la pagina": si confermano gli oggetti che la pagina elencava. Uno
    arrivato dopo, da una scansione finita nel frattempo, resta nuovo.

    Il confronto e' sul NUMERO DI RIGA e non sull'orario, perche' **due righe nate nello stesso
    istante non si ordinano** (la misura sta in `docs/domini/spina.md`). Il limite e' `<=` perche'
    `seen` porta l'ultima riga che la pagina ha **mostrato**, non la prima che non ha visto.

    **Cio' su cui l'app sta chiedendo qualcosa non si conferma vedendolo** (Marco, 14/9/2026):
    un oggetto in dubbio e' una domanda aperta, e "ho visto la pagina" non e' una risposta a
    "quale oggetto era". L'attrezzatura qui non si conferma: e' dell'Attrezzatura, e un pezzo nuovo
    non e' una domanda (Marco, 25/9/2026)."""
    fino_a = seen or _SENZA_LIMITI
    count = 0
    for row in obj.identities(conn):
        chiave = obj.stable_key(row)
        if chiave and row["id"] <= fino_a.objects and not page.object_still_open(conn, row):
            decl.confirm(conn, "object", chiave, now)
            count += 1
    return count


def apply_answers(conn, body, now):
    """Le risposte, in ordine: prima quelle sui gruppi di pose, poi le unioni (che tolgono righe),
    poi i filtri e gli oggetti. Le risposte sui gruppi vanno prima perche' la pagina manda tutto
    insieme: un'unione nello stesso Applica si porta dietro la risposta, invece di lasciarla
    cercare un nome che non c'e' piu'."""
    changed, requeued = 0, set()
    for edit in body.unfiltered:
        requeued.update(_answer_unfiltered(conn, edit, now))
        changed += 1
    # i corredi fra cui si sceglie non cambiano dentro l'Applica: si leggono una volta
    scelte = {c.id: c for c in page.rig_choices(conn)} if body.rigless else {}
    for edit in body.rigless:
        requeued.update(folders.answer_rigless(conn, edit, now, scelte))
        changed += 1
    for edit in body.opticsless:
        requeued.update(folders.answer_opticsless(conn, edit, now))
        changed += 1
    for edit in body.unnamed:
        requeued.update(folders.answer_unnamed(conn, edit, now))
        changed += 1
    for edit in body.typeless:
        requeued.update(folders.answer_typeless(conn, edit, now))
        changed += 1
    for edit in body.mosaics:
        _answer_mosaic(conn, edit, now)
        changed += 1
    requeued.update(lookalike.answer_all(conn, body.lookalikes, now))
    changed += len(body.lookalikes)
    for edit in body.filters:
        rimesse, scritta = answer_filter(conn, edit.id, edit, now)
        requeued.update(rimesse)
        changed += int(scritta)
    for edit in body.objects:
        requeued.update(
            risposta.declare_object(conn, edit.key, slug=edit.slug, name=edit.name, now=now)
        )
        changed += 1
    for edit in body.unclear:
        requeued.update(_answer_where(conn, edit, now))
        changed += 1
    return changed, requeued


def answer_filter(conn, filter_id, edit, now):
    """La risposta su un filtro, da tutte e due le porte: l'unione, o la scheda con le bande. Torna
    le pose da rimettere in coda e se qualcosa e' stato scritto: una scheda vuota non lo e'."""
    if edit.merge_into is not None:
        return gear.merge_filter(conn, filter_id, edit.merge_into, now), True
    fields = edit.model_dump(exclude_none=True, exclude={"id", "bands", "is_none", "merge_into"})
    bands = [b.model_dump() for b in edit.bands] if edit.bands is not None else None
    is_none = getattr(edit, "is_none", None)
    requeued = gear.declare_filter(conn, filter_id, fields, bands, is_none, now)
    return requeued, bool(fields) or bands is not None or is_none is not None


@contextmanager
def scrivendo(conn):
    """Una scrittura sola: o entra tutta, o non entra niente -- e i rifiuti che il database o le
    regole alzano diventano **parole che la pagina puo' mostrare**, non guasti. Una casa sola per
    l'Applica e per i gesti dell'Attrezzatura."""
    try:
        with transaction(conn):
            yield
    except Exception as err:
        rifiuto = _rifiuto(err)
        if rifiuto is None:
            raise
        raise rifiuto from err


def _rifiuto(err):
    """Il rifiuto come lo legge una pagina, o `None` se l'errore e' un guasto nostro."""
    if isinstance(err, strumento.FieldNotOfKindError):
        return strumento.refused(err)
    if isinstance(err, gear.MergeRefusedError):
        return HTTPException(status_code=422, detail={"code": "merge_refused"})
    if isinstance(err, decl.UnknownTargetError):
        return HTTPException(status_code=422, detail={"code": "unknown_target"})
    if isinstance(err, corredi.NotAMountError):
        return HTTPException(status_code=422, detail={"code": "not_a_mount"})
    if isinstance(err, corredi.WrongKindError):
        return HTTPException(status_code=422, detail={"code": "wrong_kind"})
    if isinstance(err, gear_create.SpellingTakenError):
        return HTTPException(status_code=409, detail={"code": "spelling_taken"})
    if isinstance(err, corredi.RigExistsError):
        return HTTPException(status_code=409, detail={"code": "rig_exists"})
    # Un `KeyError` **e'** un `LookupError`, ma non vuol dire "non l'ho trovato": e' un guasto
    # nostro, e addolcirlo nel 404 direbbe all'utente che il suo pezzo non c'e'.
    if isinstance(err, LookupError) and not isinstance(err, KeyError):
        return HTTPException(status_code=404, detail={"code": "not_found"})
    if isinstance(err, sqlite3.IntegrityError):
        return HTTPException(status_code=409, detail={"code": constraint_code(err)})
    return None


def _answer_unfiltered(conn, edit, now):
    """ "Le pose di questa camera che non dicono il filtro sono...": si scrive la risposta sulla
    camera e si rimettono in coda le sue pose. Torna quelle pose. Una camera o un filtro che non ci
    sono piu' sono una pagina vecchia, e si dice prima di scrivere. Del filtro si scrive il
    **nome**, non l'id: un'unione cancella la riga, e la risposta deve sopravvivere."""
    camera_id = gear.instrument_id(conn, "camera", edit.key)
    if camera_id is None:
        raise LookupError(f"camera {edit.key}")
    nome = None
    if edit.filter_id is not None:
        scelte = {f.id: f.name for f in page.filter_choices(conn)}
        if edit.filter_id not in scelte:
            raise LookupError(f"filtro {edit.filter_id}")
        nome = scelte[edit.filter_id]
    unfiltered_reader.declare(conn, edit.key, edit.answer, nome, now)
    return unfiltered_reader.requeue(conn, camera_id)


def _answer_mosaic(conn, edit, now):
    """ "Questi pannelli sono un mosaico, ed e' IC 405" -- oppure non lo sono. **Nessuna posa torna
    in coda**: il mosaico sulle pose lo scrive la risposta stessa (`spine/mosaic.py`), e
    nessun altro dato dipende da lei. Un nome che il catalogo riconosce come sigla va sulla sua
    voce, come per le cartelle senza nome: chi scrive `IC 405` intende IC 405."""
    value = decl.MOSAIC_NO
    if edit.answer == decl.MOSAIC_YES:
        slug, name = risposta.resolved(conn, None, (edit.name or "").strip())
        value = risposta.target_value(slug, name)
    mosaic.write_answer(conn, edit.key, value, now)


def _answer_where(conn, edit, now):
    """ "Le pose riprese a queste coordinate sono di questo sito": si scrive la risposta e si
    rimettono in coda le pose che riguarda. Torna quelle pose.

    Le due cose che possono non esistere si controllano **prima** di scrivere: delle coordinate
    su cui non c'e' nessuna posa (la pagina era vecchia) e un sito cancellato nel frattempo.
    Scrivere e accorgersene dopo vorrebbe dire una dichiarazione verso il nulla, e l'unico a
    vederla sarebbe lo stadio, molto dopo, in un log.

    Si scrive il **nome** del sito e non il suo id, che si riusa. E le pose che una risposta
    precedente aveva gia' sistemato tornano in coda anche loro: e' cosi' che si cambia idea."""
    frames = places.frames_at(conn, edit.key, SITE_UNCLEAR)
    if not frames:
        raise LookupError(f"coordinate {edit.key}")
    sito = conn.execute("SELECT name FROM sites WHERE id = ?", (edit.site_id,)).fetchone()
    if sito is None:
        raise LookupError(f"sito {edit.site_id}")
    decl.declare_coordinates(conn, edit.key, sito["name"], now)
    invalidate(conn, frames, "group")
    return frames


def constraint_code(err):
    for needle, code in _CONSTRAINT_CODES.items():
        if needle in str(err):
            return code
    return "constraint_violated"
