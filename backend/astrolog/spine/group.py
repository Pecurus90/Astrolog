"""Lo stadio `group`: mettere insieme le pose in notti e sessioni.

Una **notte** va da mezzogiorno a mezzogiorno nel fuso del sito; una **sessione** e' oggetto x
notte x corredo, coi filtri dentro. E' la casella che trasforma un mucchio di pose in ore
osservate, ed e' l'unita' in cui l'app conta tutto quello che verra' dopo.

Vincoli non ovvi:

* **Il fuso e' quello del sito, mai quello del computer**, e la notte la calcola
  `clock.night_date` -- la casa di questa regola. La usa anche `scan` per la notte della posa
  (`frames.local_night`), che leggono le domande e il solver prima che il sito si sappia. Senza
  sito le notti di `group` non nascono -- una notte e' data + luogo -- e l'app lo dice.
* **Da dove hai ripreso si chiede, non si indovina.** Le coordinate dell'header sono un
  indizio: entro `SAME_PLACE_KM` da un luogo dichiarato si tace, oltre la notte **non nasce** e
  la posa aspetta col suo codice. Un GPS o una rete possono sbagliare, e una notte attribuita
  al posto sbagliato e' un dato falso che nessuno rilegge (scelta di Marco, 2026-09-09).
* **Ogni posa che resta fuori porta il suo perche'**, e si conta: `skipped` e non `pending`, o
  il residuo dello stadio non arriverebbe mai a zero e il pulsante Avvia partirebbe a vuoto a
  ogni clic. Vale anche per una posa che `identify` ha **saltato**: arriva fin qui apposta, e si
  ferma qui. Non vale per una posa che uno stadio a monte ha segnato `failed`: quella e' un
  guasto, non una risposta, e resta in coda **apposta** perche' si veda -- a raccoglierle sara'
  la Diagnostica, che ha gia' la sua voce in coda.
* **Cio' che resta vuoto si spazza a fine corsa** -- una sessione a zero pose e' una riga che
  dice "0 pose", ed e' la stessa lezione che gli oggetti hanno gia' insegnato. A fine e non
  all'inizio come fa `identify`: il perche' e' in `_sweep`, e non e' un dettaglio.
"""

import logging
from functools import partial

from ..clock import night_date, now_iso
from ..db.transaction import transaction
from ..place import by_distance, coordinates_key, distance_km
from . import declarations as decl
from . import gear_usage, mosaic
from . import group_store as store
from .stage_run import frame_safely, receipt, watched
from .stages import ready, set_status

log = logging.getLogger(__name__)

COUNTS = ("linked", "nights", "sessions", "waiting", "swept", "errors")

# Sotto questa distanza le coordinate dell'header e quelle del luogo sono **lo stesso posto**:
# una coordinata scritta con due decimali si sposta gia' di 1,1 km da sola, e un GPS di
# consumo sbaglia di metri. Oltre, non si indovina: si chiede.
SAME_PLACE_KM = 1.0

# I motivi per cui una posa resta fuori da una sessione. Un codice, mai una frase.
NO_ACTIVE_SITE = "no_active_site"  # lo stesso codice che le impostazioni gia' mostrano
SITE_NO_TIMEZONE = "site_no_timezone"  # e lo stesso che il luogo usa per il fuso mancante
SITE_UNCLEAR = "site_unclear"
NO_OBJECT = "no_object"
NO_DATE = "no_date"


def group_frames(conn):
    """Mette ogni posa che aspetta questo stadio nella sua notte e nella sua sessione; un
    evento per posa, poi la ricevuta."""
    counts: dict[str, int] = dict.fromkeys(COUNTS, 0)
    errors, seen = [], 0

    def at_end():
        if seen:  # le notti di ogni pezzo, solo se qualche posa e' stata lavorata
            gear_usage.write(conn)

    with watched("group", counts, at_end):
        frame_ids = ready(conn, "group")
        store.detach(conn, frame_ids)
        # Le pose nuove entrano nei loro pannelli e mosaici qui, dove si scrive. All'INIZIO e non
        # alla fine: cielo e corredo di queste pose sono gia' decisi, e una corsa fermata a meta'
        # lascerebbe raggruppate -- non piu' pronte -- pose che nessuno piazzerebbe piu'.
        mosaic.place(conn, frame_ids)
        # i luoghi si leggono una volta per corsa: durante la corsa nessuno li scrive
        site, luoghi = store.home_site(conn), store.sites(conn)
        total = len(frame_ids)
        for frame_id in frame_ids:
            # chi nel frattempo non e' piu' pronto si salta (`stages.ready`)
            if ready(conn, "group", frame_id=frame_id):
                work = partial(_one_frame, conn, frame_id, (site, luoghi), counts)
                frame_safely(conn, "group", frame_id, work, counts, errors)
            seen += 1
            yield {"current": seen, "total": total, **counts}
        counts["swept"] = _sweep(conn)
    yield receipt("ok", None, counts, errors, total=seen)


def _sweep(conn):
    """Le sessioni rimaste senza pose e le notti rimaste senza sessioni, tolte a fine corsa.
    Torna quante righe se ne sono andate.

    **A fine corsa e non all'inizio**, al contrario di `identify`: li' la spazzata anticipata
    serve a liberare dei NOMI, che sono unici e che l'oggetto nuovo deve poter prendere. Qui
    non c'e' niente da liberare -- la chiave di una sessione e' la sua terna, e rifare una posa
    la riporta sulla stessa -- quindi spazzare prima vorrebbe dire cancellare una notte per
    ricrearla identica un istante dopo, con un id nuovo sotto i piedi di chi la stava
    guardando. Le notti si spazzano dopo le sessioni, o una notte appena svuotata resterebbe in
    piedi per un giro intero."""
    tolte = store.drop_empty_sessions(conn)
    tolte += store.drop_empty_nights(conn)
    if tolte:
        log.info("group: sessioni e notti rimaste vuote, tolte", extra={"quante": tolte})
    return tolte


def _one_frame(conn, frame_id, dove, counts):
    """Una posa, in una transazione: cio' che e' fatto e' fatto anche se ci si ferma dopo."""
    frame = store.frame(conn, frame_id)
    now = now_iso()
    site, risposta, fuori = _where(conn, frame, *dove)
    with transaction(conn):
        # `site` c'e' se e solo se non c'e' un motivo per fermarsi: si guardano tutti e due,
        # cosi' la coppia e' vera anche per chi legge (e per il controllo dei tipi).
        if fuori or site is None:
            set_status(conn, frame_id, "group", "skipped", reason=fuori, now=now)
            counts["waiting"] += 1
        else:
            data = night_date(frame["date_obs"], site["timezone"])
            night_id = _night(conn, site, data, now, counts, declared=risposta)
            session_id = _session(conn, night_id, frame["object_id"], frame["rig_id"], counts)
            store.set_frame_group(conn, frame_id, night_id, session_id)
            set_status(conn, frame_id, "group", "done", now=now)
            counts["linked"] += 1


def _where(conn, frame, home, luoghi):
    """Da dove e' stata ripresa questa posa: `(riga del sito, se lo ha detto l'utente, codice)`.

    Il secondo valore e' cio' che rende la notte `declared`, e viene da **come** si e' saputo il
    sito, non da quale sito e': rispondere "ero a casa" e' una risposta come le altre, e la
    notte che ne nasce non la deve spostare piu' nessuno.

    L'ordine conta, ed e' questo: prima cio' che manca alla POSA, poi cio' che manca all'app.
    Una posa senza oggetto o senza data resta senza sessione anche con dieci luoghi dichiarati,
    e dirle "manca il luogo" manderebbe l'utente a sistemare la cosa sbagliata.

    La data si prova **senza fuso**: cosi' "non si legge la data" resta distinto da "il fuso del
    luogo non esiste", che sono due guasti da riparare in due posti diversi.

    Quando le coordinate dell'header dicono un altro posto si guarda prima se l'utente ha gia'
    risposto **per quel posto** (`declarations`, chiave = le coordinate arrotondate): la sua
    risposta vale per tutte le notti riprese li', anche quelle che verranno. Poi il luogo
    dichiarato piu' vicino entro `SAME_PLACE_KM`, come per casa. Senza nessuno dei due si
    aspetta: indovinare vorrebbe dire scrivere una notte falsa che nessuno rilegge."""
    if frame["object_id"] is None:
        return _stop(NO_OBJECT)
    if night_date(frame["date_obs"]) is None:
        return _stop(NO_DATE)
    lat, lon = frame["site_lat"], frame["site_lon"]
    lontano = None if home is None else distance_km(lat, lon, home["latitude"], home["longitude"])
    if home is not None and (lontano is None or lontano <= SAME_PLACE_KM):
        return _with_timezone(home, frame, risposta=False)
    if None in (lat, lon):
        return _stop(NO_ACTIVE_SITE)
    # Prima la risposta dell'utente su quel posto, poi la vicinanza: un sito dichiarato dopo,
    # piu' vicino, non scavalca cio' che l'utente ha detto.
    detto = decl.site_for_coordinates(conn, coordinates_key(lat, lon))
    if detto:
        site = store.site_by_name(conn, detto)
        if site is None:
            # Anche quando il sito dichiarato e' stato cancellato o rinominato dopo: la risposta
            # non aggancia piu' niente, e si torna a chiedere invece di ripiegare su casa.
            return _stop(SITE_UNCLEAR)
        return _with_timezone(site, frame, risposta=True)
    vicini = [s for km, s in by_distance(lat, lon, luoghi) if km <= SAME_PLACE_KM]
    if vicini:
        return _with_timezone(vicini[0], frame, risposta=False)
    return _stop(SITE_UNCLEAR if home is not None else NO_ACTIVE_SITE)


def _stop(reason):
    """La posa resta fuori col suo codice: senza luogo non c'e' nemmeno una risposta da dire."""
    return None, None, reason


def _with_timezone(site, frame, *, risposta):
    """Il luogo, se il suo fuso da' una data alla posa; altrimenti il codice che lo dice."""
    if not site["timezone"] or night_date(frame["date_obs"], site["timezone"]) is None:
        return _stop(SITE_NO_TIMEZONE)
    return site, risposta, None


def _night(conn, site, night_date_str, now, counts, *, declared):  # noqa: PLR0913
    """La notte di quella data in quel luogo: quella che c'e', o una nuova.

    `declared` quando il sito viene da una risposta dell'utente -- anche se la risposta e'
    "ero a casa": una notte cosi' non la sposta piu' nessuno, ne' il trasloco di casa ne' la
    spazzata."""
    riga = store.night(conn, site["id"], night_date_str)
    if riga is not None:
        return riga["id"]
    counts["nights"] += 1
    return store.create_night(conn, site["id"], night_date_str, now, declared=declared)


def _session(conn, night_id, object_id, rig_id, counts):
    """La sessione di quella terna: quella che c'e', o una nuova."""
    riga = store.session(conn, night_id, object_id, rig_id)
    if riga is not None:
        return riga["id"]
    counts["sessions"] += 1
    return store.create_session(conn, night_id, object_id, rig_id)
