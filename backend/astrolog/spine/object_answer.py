"""La risposta dell'utente su un OGGETTO: la correzione, la regola che se ne impara, la conferma.

Sta qui e non in `declarations.py` perche' quello e' lo **strato del dichiarato** -- chi scrive e
rilegge una dichiarazione qualunque -- mentre questa e' la risposta di **un dominio**, con le sue
regole: cosa vuol dire correggere un oggetto, quando una grafia diventa una regola, cosa torna in
coda. Le due cose cambiano per ragioni diverse.

Vincolo non ovvio: la correzione **non** tocca `objects` ne' `object_names`. Quelli li riscrive
`identify` quando rifa' il lavoro, cosi' la risposta e' una sola verita' in un posto solo.
"""

import logging

from ..catalog import lookup
from ..clock import now_iso
from ..vocab.object_label import clean_object_name
from . import objects
from .declarations import (
    MOSAIC_NO,
    MOSAIC_YES,
    UnknownTargetError,
    confirm,
    declared,
    learn,
    write_declaration,
)
from .stages import invalidate

log = logging.getLogger(__name__)

# Il campo con cui l'utente dice "cio' che avete trovato, per me e' quest'altro": la CORREZIONE
# di un oggetto (glossario). Un campo solo, e porta il tipo nel valore: la chiave primaria di
# `declarations` e' (tipo, chiave, campo), e due campi distinti lascerebbero scrivere due
# correzioni contraddittorie sullo stesso oggetto.
CORRECTION = "correction"

CATALOG, NAME = "catalog:", "name:"  # il tipo del bersaglio, in testa al valore


def correct_object(conn, found_key, *, slug=None, name=None, now=None):
    """La correzione dell'utente su un oggetto: "cio' che avete trovato come `found_key`, e'
    questo".

    E' una CORREZIONE e non un lucchetto, ed e' la differenza che fa funzionare la cosa: il
    lucchetto `identity_method = 'user'` protegge l'OGGETTO, non la posa, quindi al primo
    ricalcolo `identify` rifarebbe la sua strada dal cielo e riporterebbe le pose dov'erano. La
    dichiarazione invece si legge ogni volta, e sopravvive a un azzeramento del rilevato.

    `found_key` e' cio' che l'app aveva dedotto -- lo slug di catalogo, o il nome grezzo per un
    oggetto che in catalogo non c'e'. Il bersaglio e' uno slug **oppure** un nome libero: chi
    fotografa una cometa o un campo senza voce ha diritto a un oggetto lo stesso."""
    if not found_key or bool(slug) == bool(name):
        raise ValueError("la correzione vuole un bersaglio solo, slug o nome")
    write_declaration(conn, "object", found_key, CORRECTION, target_value(slug, name), now)


def target_value(slug, name):
    """Un bersaglio come si scrive in una dichiarazione: il tipo nel valore, cosi' uno slug e un
    nome che si scrivono uguali restano due cose."""
    return f"{CATALOG}{slug}" if slug else f"{NAME}{name}"


def catalog_target(conn, slug):
    """`(nome, voce)` di uno slug per chi decide, o `None` se il catalogo non ce l'ha. La voce porta
    `is_primary` perche' una regola punta alla VOCE, non a una sua grafia: chi decide lo legge per
    dire `exact_name` invece di `historic_name`."""
    entry = lookup.by_slug(conn, slug)
    return None if entry is None else (entry["name"], {**entry, "is_primary": 1})


def resolved(conn, slug, name):
    """`(slug, nome)` di una risposta, con un nome scritto che il catalogo riconosce come sigla
    portato sulla sua voce: chi scrive `M 81` intende M 81, e un oggetto fuori catalogo che si
    chiama cosi' dividerebbe le sue ore su due voci. Solo senza uno slug: con tutti e due la
    risposta resta com'e', e chi controlla "un bersaglio solo" la rifiuta."""
    hit = lookup.by_designation(conn, name) if name and not slug else None
    return (hit["slug"], None) if hit else (slug, name)


def refuse_unknown_slug(conn, slug):
    """Rifiuta uno slug che il catalogo non ha. Si chiama PRIMA di scrivere: senza, si scriverebbe
    una risposta verso il nulla -- una correzione, una regola, un oggetto confermato -- e l'unico ad
    accorgersene sarebbe lo stadio, molto dopo, in un log che nessuno legge."""
    if slug and lookup.by_slug(conn, slug) is None:
        raise UnknownTargetError(slug)


def read_target(value):
    """Il bersaglio scritto da `target_value`: `("catalog", slug)`, `("name", nome)`, o `None`.

    Il prefisso si **verifica**, non si presume: una riga che non lo porta e' un valore scritto
    da qualcuno che non e' passato di qui, e tagliarla alla cieca darebbe un nome storpiato. E un
    bersaglio vuoto, o di soli spazi, non e' un bersaglio."""
    if not isinstance(value, str):
        return None
    for prefisso, kind in ((CATALOG, "catalog"), (NAME, "name")):
        if value.startswith(prefisso) and value[len(prefisso) :].strip():
            return kind, value[len(prefisso) :]
    log.warning("declarations: bersaglio senza tipo, ignorato", extra={"value": value})
    return None


def mosaic_word(value):
    """La parola di una risposta scritta su un mosaico: `MOSAIC_NO`, `MOSAIC_YES` per un bersaglio,
    o `None` -- nessuna risposta -- per un valore che non e' ne' l'uno ne' l'altro: l'ha scritto
    qualcosa che non e' passato di qui, e darlo per buono spegnerebbe una domanda."""
    if value is None or value == MOSAIC_NO:
        return value
    return None if read_target(value) is None else MOSAIC_YES


def shown_target(conn, value):
    """`(tipo, valore, come si mostra)` di un bersaglio scritto, o `None` se non si legge. Una voce
    di catalogo che non c'e' piu' vale nessun bersaglio: dire il suo slug sarebbe mostrare un nome
    che nessuno ha scritto."""
    letto = read_target(value)
    if letto is None:
        return None
    kind, valore = letto
    if kind == "name":
        return kind, valore, valore
    entry = lookup.by_slug(conn, valore)
    return None if entry is None else (kind, valore, entry["name"])


def correction_of(conn, found_key):
    """Dove l'utente manda cio' che l'app ha trovato come `found_key`: `("catalog", slug)`,
    `("name", nome)`, o `None` se non ha detto niente."""
    value = declared(conn, "object", found_key, CORRECTION)
    return None if value is None else read_target(value)


def declare_object(conn, key, *, slug=None, name=None, now=None):
    """La risposta dell'utente su un oggetto, tutta insieme. Torna le pose da rimettere in coda.

    `key` e' la chiave STABILE letta dalla pagina -- lo slug di catalogo, o il nome dell'oggetto
    -- mai il numero di riga: `identify` cancella gli oggetti rimasti senza pose e li rifa' con
    numeri nuovi, e una risposta agganciata a un numero punterebbe al nulla.

    Fa tre cose, e la seconda e' quella che conta: (1) scrive la **correzione**, che e' cio' che
    sposta le pose al prossimo giro di `identify`; (2) impara la regola sulla grafia dell'header
    -- ma **solo se quella grafia punta a un oggetto solo** in tutto l'archivio, perche' un
    `Snapshot` che sta su due cieli diversi non e' un nome, e' un segnaposto, e una regola su di
    lui tirerebbe pose che guardavano tutt'altro (Marco, 2026-09-09); (3) conferma l'oggetto, che
    da adesso non si richiede piu'.

    Non tocca `objects` ne' `object_names`: quelli li riscrive `identify` quando rifa' il
    lavoro. Cosi' la risposta e' **una sola verita' in un posto solo**, e non due copie che
    possono divergere."""
    now = now or now_iso()
    row = objects.by_key(conn, key)
    if row is None:
        raise LookupError(f"oggetto {key}")
    refuse_unknown_slug(conn, slug)
    slug, name = resolved(conn, slug, name)
    object_id = row["id"]

    correct_object(conn, key, slug=slug, name=name, now=now)
    target = slug or name
    for grafia in _unambiguous_spellings(conn, object_id):
        learn(conn, "object", grafia, target, now=now)
    confirm(conn, "object", target, now)

    frames = objects.frames_of(conn, object_id)
    invalidate(conn, frames, "identify")
    return frames


def _unambiguous_spellings(conn, object_id):
    """Le grafie dell'header di questo oggetto che in tutto l'archivio puntano a lui solo.

    Si confrontano **ripulite dalle parole di tavolozza**, la stessa forma con cui `identify`
    cerca la regola: `Snapshot LRGB` e `Snapshot` sono la stessa grafia, e scriverne una e
    cercarne un'altra vuol dire una regola che non aggancia mai -- proprio sui nomi per cui
    `vocab.object_label` esiste.

    Una grafia che tocca piu' di un oggetto non diventa una regola: e' un segnaposto, e una
    regola su di lui tirerebbe su un oggetto pose che guardavano tutt'altro."""
    tocca = {}
    for grezzo, altro_id in objects.raw_names_with_objects(conn):
        tocca.setdefault(clean_object_name(grezzo), set()).add(altro_id)
    mie = {clean_object_name(g) for g in objects.raw_names_of(conn, object_id)}
    return [g for g in mie if g and len(tocca.get(g, ())) == 1]
