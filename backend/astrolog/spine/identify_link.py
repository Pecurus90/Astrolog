"""L'oggetto dell'archivio a cui una decisione si aggancia: quello che c'e', o uno nuovo.

Qui si scrive cosa diventa una posa identificata -- la riga in `objects`, i suoi nomi, la sua
fiducia -- mentre la sequenza che ci arriva sta in `identify.py` e il criterio in
`identify_decide.py`.

Vincoli non ovvi:

* **Il nome grezzo dell'header entra in `object_names`** anche quando l'oggetto viene dal cielo
  e quel nome non ha deciso niente: e' cio' che l'utente ha scritto. L'unica eccezione e' un nome
  che e' **gia' di un altro oggetto** -- un nome, un oggetto -- e allora si scrive nel log: cade,
  ma non in silenzio.
* **`name_taken` conta i NOMI, non le pose**: ogni nome che non e' entrato perche' era di un
  altro oggetto, di catalogo o grezzo. Una posa sola puo' valerne tre.
* **Un oggetto ha sempre un modo di chiamarsi, ma non sempre in `object_names`.** Il primario si
  assegna al primo nome **libero** e non al primo in lista: i nomi che il catalogo gli darebbe
  possono essere gia' di altri (110 voci si spartiscono 42 nomi comuni -- `HCG 92` e `NGC 7318`
  sono due dei cinque "Stephan's Quintet"), e un oggetto nato quando il catalogo non era caricato
  puo' essersi preso una sigla. Se non ce n'e' nessuno libero l'oggetto nasce **senza nomi
  propri**, e va bene solo perche' ha `catalog_slug`, cioe' il catalogo sa come si chiama. Un
  oggetto **fuori** catalogo questo problema non ce l'ha mai: se il suo nome fosse di qualcuno,
  `hang` si aggancerebbe a quell'oggetto invece di crearne uno.
* **La parola dell'utente non si tocca mai**, ed e' la sola regola che questo stadio ha il
  potere di violare in silenzio. Ma se e' la posa NUOVA a portarla si scrive sempre: la scala
  delle fiducie non conosce `user`, e passare di li' voleva dire che rispondendo su un oggetto
  gia' in archivio il lucchetto non si scriveva mai, l'oggetto restava `low`, e la pagina lo
  rimetteva in cima all'utente che aveva appena risposto.
"""

import logging

from ..catalog import lookup
from . import identify_decide as rule
from . import identify_store as store

log = logging.getLogger(__name__)


def entry_for(conn, slug, hit, cands):
    """La voce di catalogo che la decisione ha scelto, fra quelle gia' in mano: serve per i nomi
    dell'oggetto, e chiederla di nuovo al database sarebbe una terza interrogazione per posa."""
    if slug is None:
        return None
    if hit and hit["slug"] == slug:
        return hit
    fra_i_candidati = next((c for c in cands if c["slug"] == slug), None)
    # Una voce che non e' ne' il nome ne' un candidato c'e' solo quando l'utente l'ha dichiarata:
    # il cielo diceva un'altra cosa, quindi va chiesta al catalogo per nome proprio.
    return fra_i_candidati or lookup.by_slug(conn, slug)


def hang(conn, decision, raw, entry, now, counts):  # noqa: PLR0913
    """L'oggetto di questa decisione: quello che c'e' gia', o uno nuovo. Torna `(id, lucchettato)`,
    dove il lucchetto e' la parola dell'utente -- ed e' cio' che dice se la pagina fara' ancora
    una domanda su questo oggetto."""
    slug = decision["slug"]
    if slug:
        existing = store.object_by_slug(conn, slug)
    else:
        existing = store.object_by_name(conn, decision["name"])
    lucchettato = decision["method"] == "user" or (
        existing is not None and existing["identity_method"] == "user"
    )

    if existing is None:
        object_id = store.create_object(
            conn,
            slug=slug,
            method=decision["method"],
            confidence=decision["confidence"],
            now=now,
        )
        counts["name_taken"] += _name_it(conn, object_id, decision, entry)
        counts["new_objects"] += 1
    else:
        object_id = existing["id"]
        _restate(conn, existing, decision, now)

    if raw and not store.add_name(conn, object_id, raw, origin="raw"):
        counts["name_taken"] += 1
        log.info("identify: nome gia' di un altro oggetto", extra={"nome": raw, "obj": object_id})
    return object_id, lucchettato


def _name_it(conn, object_id, decision, entry):
    """I nomi di un oggetto appena nato, col primo che riesce a entrare come primario. Torna
    quanti ne sono stati rifiutati perche' gia' di un altro oggetto.

    Le altre sigle del catalogo non si copiano: le sa il catalogo, e ricopiarle qui sarebbe lo
    stesso fatto in due case. Il primario si assegna al primo nome LIBERO e non al primo in
    lista, perche' un nome puo' essere gia' di un altro oggetto: due voci di catalogo possono
    portare lo stesso nome comune, e un oggetto nato quando il catalogo non era caricato si e'
    preso una sigla che adesso servirebbe qui."""
    if entry is None:
        # Un nome che viene da una correzione e' parola dell'utente, non un'etichetta trovata
        # in un header: si conserva con la sua provenienza, e l'export lo porta via con se'.
        origine = "user" if decision["method"] == "user" else "raw"
        candidati = [(decision["name"], origine)]
    else:
        candidati = [(entry["name"], "catalog")]
        if entry.get("common_name"):
            candidati.append((entry["common_name"], "catalog"))

    primario, rifiutati = True, 0
    for nome, origine in candidati:
        if store.add_name(conn, object_id, nome, origin=origine, is_primary=int(primario)):
            primario = False
        else:
            rifiutati += 1
    if primario:
        # Regge solo perche' l'oggetto ha `catalog_slug`: il catalogo sa come si chiama. Un
        # oggetto fuori catalogo non arriva mai qui senza il suo nome.
        log.warning("identify: oggetto senza nomi propri", extra={"obj": object_id})
    return rifiutati


def _restate(conn, existing, decision, now):
    """La fiducia dell'oggetto quando un'altra posa lo aggancia.

    Due regole, e vanno in quest'ordine. La parola dell'utente non si tocca mai -- e' quella che
    questo stadio ha il potere di violare in silenzio. Ma se e' la posa NUOVA a portarla, si
    scrive sempre: la scala delle fiducie non conosce `user`, e passare di li' voleva dire che
    rispondendo su un oggetto **gia' in archivio** il lucchetto non si scriveva mai, l'oggetto
    restava `low`, e la pagina lo rimetteva in cima -- all'utente che aveva appena risposto."""
    if existing["identity_method"] == "user":
        return
    if decision["method"] == "user":
        store.set_identity(conn, existing["id"], method="user", confidence="user", now=now)
        return
    kept = rule.confidence_after(existing["identity_confidence"], decision["confidence"])
    if kept == existing["identity_confidence"]:
        return
    store.set_identity(conn, existing["id"], method=decision["method"], confidence=kept, now=now)
