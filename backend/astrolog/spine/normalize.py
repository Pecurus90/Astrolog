"""Lo stadio `normalize`: dai grezzi dell'header ai filtri, agli strumenti e ai corredi
dell'utente. Traduce, non interpreta.

Vincolo non ovvio: l'ordine e' sempre regola imparata -> vocabolario -> resta grezzo. Oltre
il vocabolario non si indovina: cio' che resta grezzo e' un gruppo per la pagina Da
confermare, mai una scelta presa al posto dell'utente. Il dichiarato non si tocca mai, e un
frame che esplode diventa `failed` col suo perche' senza fermare gli altri.
"""

import logging
from functools import cache, partial
from typing import NamedTuple

from ..clock import now_iso
from ..db.transaction import transaction
from ..units import focal_buckets
from ..vocab.filters import (
    NO_FILTER,
    NO_FILTER_NAME,
    UNKNOWN,
    is_broadband_word,
    normalize_filter,
    passband_of,
)
from ..vocab.header_value import normalize_header_value
from ..vocab.software import normalize_software
from . import (
    camera_sky,
    camera_specs,
    copies,
    declarations,
    gear_usage,
    rewrite,
    rigless,
    typeless_folders,
    unfiltered,
)
from . import night_rig as della_notte
from . import normalize_store as store
from . import rigs as corredi
from .gear_create import create_filter, filter_id_by_name
from .normalize_rig import instruments_on_frame, mount_for_frame, rig_for_frame
from .stage_run import frame_safely, receipt, watched
from .stages import invalidate, ready, set_status

log = logging.getLogger(__name__)

COUNTS = ("normalized", "filters", "instruments", "rigs", "copies", "to_review", "errors")


def normalize_frames(conn):
    """Normalizza i frame che aspettano questo stadio; un evento per frame, poi la ricevuta."""
    counts = dict.fromkeys(COUNTS, 0)
    errors, seen, context = [], 0, None

    def at_end():
        # le pose lavorate sono scritte e uscite dalla coda: nessuna corsa le rivotera'
        if seen:  # una volta per corsa, e solo se qualche posa si e' mossa: contare costa
            _at_round_end(conn, context.colours if context else None)
            gear_usage.write(conn)

    with watched("normalize", counts, at_end):
        frame_ids, context = _before_the_round(conn)
        for frame_id in frame_ids:
            work = partial(_one_frame, conn, frame_id, context, counts)
            counts["to_review"] += bool(
                frame_safely(conn, "normalize", frame_id, work, counts, errors)
            )
            seen += 1
            yield {"current": seen, "total": len(frame_ids), **counts}
    yield receipt("ok", None, counts, errors, total=seen)


class _Round(NamedTuple):
    """Cio' che il giro sa prima di scrivere: le focali raggruppate, la camera di ogni posa col suo
    perche' (`_camera_of`), l'originale di ogni copia e il marchio di ogni file (`copies.decide`)
    e il colore delle camere (`camera_specs.ahead`)."""

    buckets: dict
    cameras: dict
    copy_of: dict
    marks: dict
    colours: dict


def _before_the_round(conn):
    """Le pose del giro e cio' che serve loro, deciso una volta per tutte: `(pose, _Round)`.

    Chi una di queste decisioni cambia, fra le pose gia' fatte, entra in questo stesso giro: il
    giro e' uno, e nessuna posa si rifa' a fine corsa perche' un'altra l'ha spostata."""
    frame_ids = ready(conn, "normalize")
    if not frame_ids:
        return [], None
    # Una posa che dice la camera puo' cambiare quella che la sua notte da' alle pose che non la
    # dicono.
    vicine = set(della_notte.in_nights_of(conn, frame_ids)) - set(frame_ids)
    if vicine:
        invalidate(conn, vicine, "normalize")
    frame_ids = ready(conn, "normalize")
    copy_of, marks, redo = copies.decide(store.broods(conn, frame_ids), frame_ids)
    if redo:
        invalidate(conn, redo, "normalize")
    frame_ids = ready(conn, "normalize")
    nights = cache(lambda: della_notte.night_rigs(conn))
    cameras, voting = {}, []
    for i in frame_ids:
        # una riga alla volta: della posa restano la camera e il suo voto, non l'header
        frame = store.frame(conn, i)
        cameras[i] = _camera_of(conn, frame, nights)
        if cameras[i][0] and copy_of.get(i, frame["copy_of"]) is None:
            voting.append((cameras[i][0], frame["bayer_pattern"] is not None))
    colours = camera_specs.ahead(conn, frame_ids, voting)
    # le pose senza matrice di una camera che cambia colore: la loro camera e il loro voto restano
    # quelli, cambia solo il filtro che sceglieranno
    for i in ready(conn, "normalize"):
        if i not in cameras:
            cameras[i] = _camera_of(conn, store.frame(conn, i), nights)
            frame_ids.append(i)
    # Le focali si raggruppano PRIMA di scrivere, tutte insieme: cosi' 559, 560 e 561 danno lo
    # stesso corredo qualunque sia l'ordine dei file sul disco.
    buckets = focal_buckets(store.pending_focals(conn, frame_ids))
    return frame_ids, _Round(buckets, cameras, copy_of, marks, colours)


def _camera_of(conn, frame, nights):
    """`(nome della camera, risposta sul gruppo, corredo della notte)` di una posa. Dove l'header
    non la dice, la dice la risposta sul gruppo e poi la notte: se la vedesse solo il corredo,
    quelle pose avrebbero un filtro che nessuno puo' piu' chiedere loro."""
    camera = declarations.instrument_name(conn, "camera", frame["instrument_raw"])
    detto = notte = None
    if camera is None:
        detto = rigless.rig_of_frame(conn, frame)
        if detto is None:
            notte = della_notte.rig_of_night(conn, frame, nights())
    return (detto or notte or {}).get("camera", camera), detto, notte


def _at_round_end(conn, colours):
    """A fine corsa: voto dei file, pixel dal cielo e corredi vuoti, che una posa sposta, e le
    cartelle della domanda sul tipo, dove una copia trovata non conta piu'."""
    camera_specs.from_files(conn, colours)
    camera_sky.write(conn)
    corredi.drop_empty(conn)
    typeless_folders.write(conn)


def _one_frame(conn, frame_id, context, counts):
    """Un frame, in una transazione: cio' che e' fatto e' fatto anche se ci si ferma dopo. Torna
    se resta da rivedere."""
    frame = store.frame(conn, frame_id)
    camera, detto, notte = context.cameras[frame_id]
    now = now_iso()
    with transaction(conn):
        # Il software si risolve PRIMA del corredo, non dopo: e' lui a dire come va letto
        # `TELESCOP`, e leggerlo dopo vorrebbe dire averci gia' costruito sopra un'ottica.
        software = normalize_software(frame["software_raw"])
        filter_id, filter_known = _filter_for(conn, frame, counts, now, camera, context.colours)
        rig_id = rig_for_frame(
            conn, frame, context.buckets, counts, now, camera, detto, software, notte
        )
        addosso = instruments_on_frame(conn, frame, counts, now)
        addosso["mount"] = mount_for_frame(conn, frame, rig_id, software, counts, now)
        copy_of = context.copy_of.get(frame_id, frame["copy_of"])
        counts["copies"] += 1 if copy_of is not None else 0
        was = (frame["filter_id"], frame["rig_id"], frame["software"], frame["copy_of"])
        if (filter_id, rig_id, software, copy_of) != was:
            # Filtro, corredo, software e "e' una copia" cambiano le risposte di chi viene
            # dopo: si passa sempre da qui, mai da un UPDATE a mano sugli stadi a valle.
            invalidate(conn, [frame["id"]], "normalize", now=now)
        store.set_normalized(
            conn,
            frame["id"],
            filter_id=filter_id,
            rig_id=rig_id,
            on_frame=addosso,
            software=software,
            copy_of=copy_of,
            rewrite_mark=context.marks[frame_id]
            if frame_id in context.marks
            else rewrite.mark_of(frame),
        )
        set_status(conn, frame["id"], "normalize", "done", now=now)
        counts["normalized"] += 1
        return not filter_known or rig_id is None


def _filter_for(conn, frame, counts, now, camera, colours):  # noqa: PLR0913
    """(id del filtro, si sa cos'e'?): regola imparata (non su una camera a colori per una parola
    che il vocabolario sa banda larga) -> vocabolario -> no.

    Un filtro con banda sconosciuta ESISTE (la pagina lo chiede, con le sue pose) ma non e'
    "saputo": e' una domanda finche' non gli si risponde. `camera` e' il nome della camera di
    questa posa -- dall'header, dalla risposta sul suo gruppo o dalla sua notte -- perche' senza di
    lei non c'e' niente da chiedere sul suo filtro."""
    # A essere a colori e' la CAMERA, non la posa: il programma che non scrive `BAYERPAT` non fa
    # una posa mono in mezzo alle altre.
    bayer = bool(frame["bayer_pattern"])
    colour = bayer or unfiltered.is_colour(conn, camera, colours)
    key = normalize_header_value(frame["filter_raw"])
    name = declarations.alias_target(conn, "filter", key) if key else None
    if name is not None:
        filter_id = filter_id_by_name(conn, name)
        # una risposta su una parola che il vocabolario non conosce (`Filtro1`) resta dell'utente
        larga = colour and is_broadband_word(frame["filter_raw"])
        if filter_id is not None and not larga:
            return filter_id, True
        if filter_id is None:
            # La risposta dell'utente punta a un filtro che non c'e' piu': si dice e si torna al
            # vocabolario. Perderla in silenzio sarebbe peggio di ignorare la regola. Non si
            # crea, come si fa per gli strumenti: di un filtro non si saprebbe la banda.
            log.warning(
                "normalize: regola verso un filtro sparito",
                extra={"filter": name, "frame_id": frame["id"]},
            )

    if unfiltered.says_no_filter(frame["filter_raw"]):
        # Senza matrice di Bayer una mono e una camera a colori non si distinguono, e un
        # `FILTER=none` puo' voler dire "nessun vetro" o "ruota in posizione neutra": non si
        # assume niente, lo dice l'utente per la camera (`spine/unfiltered.py`).
        # La risposta parla di una mono: su un frame con la matrice, o su una camera a colori, e'
        # OSC qualunque cosa dica.
        detto, filtro = unfiltered.said(conn, camera)
        if not colour:
            # una mono senza risposta resta da chiedere
            if detto == unfiltered.NO_FILTER_ANSWER:
                return _no_filter(conn, frame, now)
            if filtro:
                return _answered_filter(conn, frame, filtro, now)
            return None, False
    canonical = normalize_filter(frame["filter_raw"], bayer=colour)
    # La regola imparata vale anche sul nome che il vocabolario da', dopo il colore: rinominato
    # `Lum`, una posa che scrive `L` diventa `Lum` e poi il nome nuovo, o il filtro rinascerebbe;
    # su una camera a colori `L` resta OSC.
    tenuto = declarations.alias_target(conn, "filter", normalize_header_value(canonical or ""))
    if tenuto and (filter_id := filter_id_by_name(conn, tenuto)) is not None:
        return filter_id, True
    band = passband_of(canonical)
    filter_id = filter_id_by_name(conn, canonical)
    if filter_id is None:
        filter_id = create_filter(conn, canonical, band, now)
        counts["filters"] += 1
    return filter_id, band != UNKNOWN


def _answered_filter(conn, frame, name, now):
    """Il filtro che la risposta sulla camera ha detto. Un nome che non c'e' piu' si dice, e la
    posa resta da rivedere: come per una regola verso un filtro."""
    filter_id = filter_id_by_name(conn, name)
    if filter_id is None:
        log.warning(
            "normalize: la camera dice un filtro sparito",
            extra={"filter": name, "frame_id": frame["id"]},
        )
        return None, False
    return filter_id, True


def _no_filter(conn, frame, now):
    """La riga "nessun filtro", creata la prima volta che una risposta la chiede. Se non c'e' e il
    suo nome e' gia' di un altro filtro (l'utente ha spento `is_none`, o ha chiamato cosi' un filtro
    vero) non si indovina quale sia: si dice, e la posa resta da rivedere."""
    filter_id = store.none_filter_id(conn)
    if filter_id is not None:
        return filter_id, True
    if filter_id_by_name(conn, NO_FILTER_NAME) is not None:
        log.warning("normalize: nessun filtro, nome preso", extra={"frame_id": frame["id"]})
        return None, False
    filter_id = create_filter(conn, NO_FILTER_NAME, NO_FILTER, now, is_none=True)
    return filter_id, True
