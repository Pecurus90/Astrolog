"""Lo stadio `identify`: dire cosa e' stato fotografato, e scriverlo.

Incrocia due fonti che possono contraddirsi -- il nome scritto nell'header e il cielo misurato
dal solver -- nelle otto situazioni del contratto, e da ognuna esce un oggetto dell'archivio.
Il criterio sta in `identify_decide`, la geometria in `identify_geometry`, il punteggio in
`identify_score`, l'aggancio all'oggetto in `identify_link`, l'SQL in `identify_store`: qui c'e'
solo la sequenza.

Vincoli non ovvi:

* **Il cono si chiede piu' largo del campo.** Un oggetto grande col centro lontano contiene il
  puntamento pur stando fuori dall'inquadratura, e su una focale lunga sarebbe proprio il
  soggetto a cadere fuori dalla ricerca. Poi il rettangolo dice, per ognuno, se e' davvero nella
  foto: e' un'informazione, non un filtro -- chi scarta e' `overlaps_frame`, e sbaglia apposta
  per difetto.
* **Un oggetto con la risposta dell'utente non si tocca**, mai, per nessun motivo. E' la sola
  regola che questo stadio ha il potere di violare in silenzio, e sarebbe la peggiore.
* **La grafia dell'header resta la grafia dell'header** per tutta la posa: una regola imparata
  cambia il nome che DECIDE, non cio' che l'utente ha scritto -- che e' quello che finisce fra i
  nomi dell'oggetto. Confonderli faceva sparire dall'archivio l'etichetta dell'utente.
* **La parola dell'utente arriva per due strade, e non si sovrappongono mai.** La *regola*
  imparata ("quando l'header dice X, e' Y") vale **solo dove il cielo non c'e'**: li' il nome e'
  l'unica fonte. Dove il cielo c'e' decide lui, e a spostare l'oggetto e' la *correzione*, che e'
  agganciata a cio' che l'app ha dedotto guardando il cielo -- e si segue a catena, per chi si
  corregge. Farle convivere sulla stessa posa e' costato due giri: una stringa di testo che
  batteva una misura, e poi un nome corretto in conflitto col cielo originale.
* **Una correzione chiude la domanda**, anche dove il cielo era in dubbio: e' agganciata alla
  chiave che la pagina mostrava, quindi e' la risposta a *quella* domanda. Lasciare li' il dubbio
  voleva dire richiedere all'infinito cio' su cui l'utente aveva appena cliccato. E una richiesta
  si conta solo se la pagina la fara' davvero -- su un oggetto lucchettato non la fa.
"""

import logging
from functools import partial

from ..catalog import lookup
from ..clock import now_iso
from ..db.transaction import transaction
from ..vocab.header_value import normalize_header_value
from ..vocab.object_label import clean_object_name
from . import declarations as decl
from . import gear_usage, object_candidates, unnamed
from . import identify_decide as rule
from . import identify_geometry as geometry
from . import identify_link as link
from . import identify_score as score
from . import identify_store as store
from . import object_answer as risposta
from .stage_run import frame_safely, receipt, watched
from .stages import ready, set_status

log = logging.getLogger(__name__)

COUNTS = ("linked", "new_objects", "review", "waiting", "name_taken", "swept", "errors")

# Quanti candidati **mostrare**: in un campo affollato sono decine, e oltre i primi nessuno
# guarda. Non e' il tetto di chi decide: la regola della sigla dell'header la cerca fra tutti i
# candidati, e fermarsi ai primi la rimetterebbe a chiedere.
CANDIDATES_LIMIT = 6


def candidates(conn, wcs, limit: int | None = CANDIDATES_LIMIT):
    """Le voci di catalogo in gara per questa posa, dalla piu' probabile.

    Ognuna e' la voce come la da' il catalogo, piu' `score` (quanto e' probabile che sia il
    soggetto) e `in_frame` (se e' davvero nell'inquadratura o solo li' accanto). Con
    `limit=None` le da' **tutte**: e' cio' che serve a chi decide. Lista vuota se
    la posa non ha cielo misurato, o se il catalogo non e' caricato: nessuna delle due e' un
    guasto -- l'app senza catalogo cataloga, cerca e conta le ore lo stesso."""
    if wcs.get("ra_deg") is None or wcs.get("dec_deg") is None:
        return []

    fov = geometry.frame_radius_deg(wcs)
    found = lookup.in_cone(conn, wcs["ra_deg"], wcs["dec_deg"], geometry.search_radius_deg(fov))

    running = []
    for entry in found:
        size = entry.get("size_major_arcmin")
        if not geometry.overlaps_frame(entry["sep_deg"], size, fov):
            continue  # nella foto non c'e' proprio
        running.append(
            {
                **entry,
                "score": score.score_candidate(entry, fov),
                "in_frame": geometry.in_frame(wcs, entry["ra_deg"], entry["dec_deg"], size),
            }
        )
    running.sort(key=lambda c: c["score"], reverse=True)
    return running[:limit]


def identify_frames(conn):
    """Aggancia il suo oggetto a ogni posa che aspetta questo stadio; un evento per posa, poi
    la ricevuta."""
    counts = dict.fromkeys(COUNTS, 0)
    errors, seen, frame_ids = [], 0, []

    def at_end():
        if frame_ids:  # anche prima della prima posa: stacco e spazzata sono gia' fatti
            _at_round_end(conn)

    with watched("identify", counts, at_end):
        frame_ids = ready(conn, "identify")
        # Prima si stacca cio' che si rifa', poi si toglie cio' che resta senza pose: cosi' i nomi
        # dell'oggetto vecchio sono LIBERI per quelli nuovi, e il CASCADE non si porta via la
        # grafia che l'utente aveva scritto nell'header.
        store.detach(conn, frame_ids)
        counts["swept"] = _sweep(conn)
        total = len(frame_ids)
        for frame_id in frame_ids:
            # chi nel frattempo non e' piu' pronto si salta (`stages.ready`)
            if ready(conn, "identify", frame_id=frame_id):
                work = partial(_one_frame, conn, frame_id, counts)
                frame_safely(conn, "identify", frame_id, work, counts, errors)
            seen += 1
            yield {"current": seen, "total": total, **counts}
    yield receipt("ok", None, counts, errors, total=seen)


def _at_round_end(conn):
    """Gli oggetti di ogni pezzo e i candidati degli oggetti in dubbio: cio' che il nome sposta."""
    gear_usage.write(conn)
    object_candidates.write(conn)


def _sweep(conn):
    """Gli oggetti a cui non e' rimasta nessuna posa, tolti all'inizio della corsa.

    Non e' pulizia di comodo: quando una dichiarazione sposta le pose altrove, quello che resta
    indietro comparirebbe nella pagina come "NGC 7023 -- 0 pose" -- misurato sulle 41 pose vere
    dell'Iris -- e **terrebbe in ostaggio i suoi nomi**, costringendo l'oggetto vero a nascere
    senza nomi propri. Un oggetto e' cio' che e' stato fotografato.

    **All'inizio** della corsa, subito dopo aver staccato le pose da rifare: e' il solo momento
    in cui i nomi che libera servono ancora, perche' e' in questa stessa passata che si
    riassegnano. Farlo alla fine voleva dire perderli.

    Anche sugli oggetti `user`: l'utente non crea oggetti, crea correzioni, quindi uno a zero
    pose e' sempre un residuo -- e finche' restava si teneva i suoi nomi, cosi' che correggendo
    due volte l'oggetto giusto ripiegava sul nome comune. La sua parola non si perde: vive in
    `declarations` e questa passata non la tocca."""
    tolti = store.drop_empty_objects(conn)
    if tolti:
        log.info("identify: oggetti rimasti senza pose, tolti", extra={"quanti": tolti})
    return tolti


def _one_frame(conn, frame_id, counts):
    """Una posa, in una transazione: cio' che e' fatto e' fatto anche se ci si ferma dopo."""
    frame = store.frame(conn, frame_id)
    raw = clean_object_name(frame["object_raw"])
    sky = store.wcs(conn, frame_id)
    # L'elenco intero, non i sei della pagina: perche', sta con la regola in `identify_decide`.
    cands = candidates(conn, sky, limit=None)
    fov = geometry.frame_radius_deg(sky) if sky else None
    # `raw` resta la grafia dell'header, che `identify_link.hang` mette fra i nomi dell'oggetto; a
    # decidere e' il nome DOPO le regole, che puo' essere un altro.
    named, hit, da_regola = _named_by_rule(conn, raw, con_cielo=bool(cands))
    # Senza nome e senza candidati resta l'oggetto del suo gruppo (`spine/unnamed.py`): come per
    # la regola sui nomi, dove il cielo ha dei candidati decide lui.
    detto = None if raw or cands else unnamed.named_by_group(conn, unnamed.assign(conn, frame_id))
    if detto and detto != unnamed.NONE:
        (named, hit), da_regola = detto, True
    decision = rule.decide(raw_name=named, hit=hit, cands=cands, fov_radius_deg=fov)
    if da_regola:
        # Una regola e' la parola dell'utente, e qui il cielo non c'e' per contraddirla:
        # `user`/`user`, cosi' nessuna posa successiva puo' abbassarla e la pagina non la
        # richiede. Vale anche su un bersaglio fuori catalogo: `free_name_only` chiede perche'
        # un nome libero puo' essere un segnaposto, ma questo l'ha scelto l'utente.
        decision = {**decision, "method": "user", "confidence": "user", "review": False}
    decision = _as_the_user_said(conn, decision)

    now = now_iso()
    with transaction(conn):
        store.set_empty_cone(conn, frame_id, int(not cands) if sky else None)
        if decision["branch"] == "nothing":
            # Non e' un guasto: e' l'unica cosa che l'app non puo' dedurre da sola, oppure
            # l'utente ha detto che non e' un oggetto. `skipped` e non `pending`, o il residuo
            # dello stadio non arriverebbe mai a zero e il pulsante Avvia partirebbe a vuoto a
            # ogni clic. Aspetta una risposta solo la prima.
            motivo = rule.NOT_AN_OBJECT if detto == unnamed.NONE else rule.NO_NAME_NO_SKY
            set_status(conn, frame_id, "identify", "skipped", reason=motivo, now=now)
            counts["waiting"] += motivo == rule.NO_NAME_NO_SKY
        else:
            entry = link.entry_for(conn, decision["slug"], hit, cands)
            object_id, lucchettato = link.hang(conn, decision, raw, entry, now, counts)
            store.set_frame_object(conn, frame_id, object_id)
            set_status(conn, frame_id, "identify", "done", now=now)
            counts["linked"] += 1
            # La richiesta si conta solo se la pagina la fara' davvero: su un oggetto lucchettato
            # dall'utente il dubbio di questa posa non arriva a schermo (la pagina guarda
            # `objects.identity_confidence`, e li' c'e' `user`), e contarlo darebbe una ricevuta
            # che dice "3 da rivedere" mentre lo schermo ne mostra zero.
            if decision["review"] and not lucchettato:
                counts["review"] += 1


def _named_by_rule(conn, raw, *, con_cielo):
    """Il nome di questa posa dopo le regole imparate, con la voce di catalogo che gli
    corrisponde e se una regola c'e' stata: `(nome, voce, da_regola)`.

    **La regola vale solo dove il cielo non c'e'**, ed e' il punto che ha richiesto due
    correzioni. Per un filtro o uno strumento la grafia dell'header e' l'unica fonte, e li' una
    regola e' tutto cio' che c'e'. Per un oggetto no: c'e' una misura, ed e' migliore. Applicata
    con il cielo davanti, la regola faceva danni in tutte e due le direzioni -- prima batteva la
    misura e lucchettava (una posa di M 83 finiva su M 31 senza nessuna domanda), poi, spostata
    sul nome, metteva in conflitto il nome corretto col cielo originale e **l'app richiedeva su
    tutte le pose a cui l'utente aveva appena risposto** (misurato: 41 richieste sull'Iris).

    Dove il cielo c'e', la strada giusta e' l'altra: si decide guardando il cielo, e la
    **correzione** sposta l'oggetto che ne esce -- che e' agganciata a cio' che l'app ha dedotto,
    non a una stringa di testo.

    Il bersaglio di una regola e' uno slug di catalogo **oppure** un nome pulito -- lo schema lo
    dichiara cosi' -- e a distinguerli e' il catalogo: se quella voce esiste e' uno slug."""
    if not raw:
        return raw, None, False
    target = None if con_cielo else decl.alias_target(conn, "object", normalize_header_value(raw))
    if target:
        named, entry = risposta.catalog_target(conn, target) or (target, None)
        return named, entry, True
    return raw, lookup.by_designation(conn, raw), False


def _as_the_user_said(conn, decision):
    """La decisione dopo la **correzione** dell'utente sull'oggetto trovato, seguita a catena:
    `m-31` manda a `m-45`, e se poi l'utente si corregge, `m-45` manda a `m-101`. Fermarsi al
    primo passo rendeva impossibile correggere un clic sbagliato -- la seconda cosa piu'
    probabile su quella pagina -- e lo faceva **in silenzio**. Si tiene conto di dove si e' gia'
    passati, cosi' un anello che si chiude si ferma esattamente come si fermava un passo solo.

    Un bersaglio che non esiste si **ignora**, e si resta su cio' che il cielo dice: la parola
    dell'utente ha il potere di spostare delle pose, mai di farle sparire."""
    found = decision["slug"] or decision["name"]
    visti = set()
    while found:
        visti.add(found)
        target = risposta.correction_of(conn, found)
        # L'anello si guarda PRIMA di applicare il passo: applicarlo e accorgersene dopo
        # riporterebbe la posa esattamente da dove era partita.
        if target is None or target[1] in visti:
            break
        # E il bersaglio entra fra i visti ANCHE se il passo non riesce (un bersaglio che non
        # esiste lascia la decisione com'era): senza, quel passo si riproverebbe per sempre.
        visti.add(target[1])
        decision = _towards(conn, decision, target[1], kind=target[0])
        found = decision["slug"] or decision["name"]
    return decision


def _towards(conn, decision, value, kind):
    """La decisione portata su `value`, che e' uno slug di catalogo o un nome libero."""
    entry = lookup.by_slug(conn, value)
    if kind == "catalog" and entry is None:
        log.warning(
            "identify: la parola dell'utente punta a uno slug che non c'e'", extra={"a": value}
        )
        return decision
    # Cio' che nasce da una parola dell'utente E' dichiarato: `user` / `user`, che e' anche il
    # lucchetto perche' nessuna posa successiva possa abbassarne la fiducia -- e la domanda e'
    # chiusa. Vale **anche** dove il cielo era in dubbio, che e' il caso per cui la pagina
    # esiste: la correzione e' agganciata alla chiave che la pagina mostrava, quindi e' la
    # risposta a quella domanda. Lasciare li' il dubbio voleva dire richiedere all'infinito cio'
    # a cui l'utente aveva appena cliccato.
    detto = {"method": "user", "confidence": "user", "review": False}
    if entry is not None:
        return {**decision, **detto, "slug": value, "name": None}
    return {**decision, **detto, "slug": None, "name": value}
