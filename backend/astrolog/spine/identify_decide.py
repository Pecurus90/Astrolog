"""Le otto situazioni del contratto: dato cio' che dice il nome dell'header e cio' che dice il
cielo misurato, cosa si aggancia, con che metodo e che fiducia, e se si chiede conferma.

Puro: niente database, niente catalogo. Chi chiama ha gia' fatto le due domande (la sigla al
catalogo, il cono al cielo) e qui si decide soltanto.

Vincoli non ovvi:

* **La sigla dell'header scioglie l'ambiguita' ovunque stia fra i candidati**, non solo quando
  e' il migliore: i candidati sono gia' cio' che si sovrappone all'inquadratura, quindi trovarla
  li' vuol dire che il cielo la conferma, e quale pezzo dello stesso complesso vinca il
  punteggio non e' una domanda da girare all'utente. E' la definizione della spina -- *"se
  l'header dice un nome che sta nel campo, quello vince"* (Marco, 2026-09-12). Si chiede quando
  fra i candidati quella sigla **non c'e'**.
* **Si guarda l'elenco intero, non i sei che la pagina mostra.** Il tetto di `identify.py` serve
  a mostrare i candidati; qui taglierebbe la regola. Su un campo di Orione di 3x2 gradi i
  candidati veri sono venti e `NGC 1977` e' il settimo: con la lista tagliata, una posa che lo
  dice nell'header tornerebbe a chiedere.
* **Un nome libero non crea mai un oggetto quando il cielo c'e'**: li' il cielo e' la misura e
  il nome e' un'etichetta. Lo crea solo dove non c'e' altro, e con fiducia bassa: `Snapshot`
  puo' essere il nome di un oggetto quanto il segnaposto di un programma.
* **Ogni decisione porta il suo `branch`**, un nome e non una frase. In `old/` il motivo era
  prosa, e il banco finiva per distinguere i rami leggendola: provava il motivo, non la
  decisione (`old/backend/astrolog/catalogs/identify.py:110-113`).
* **Un oggetto mobile sopprime il cielo**, e si guarda per primo. Una cometa era li' quella
  notte e non ci sara' la prossima: il cono restituirebbe l'oggetto fisso che le stava dietro,
  con tutto il punteggio del caso. Il lessico che la riconosce sta in `vocab.moving`, e sbaglia
  apposta per difetto -- dichiarare mobile un oggetto fisso lo toglierebbe da ogni coda.
* **`user` non si scrive qui.** E' la risposta dell'utente, arriva da Da confermare, e non si
  sovrascrive mai.
"""

from .. import units
from ..vocab.moving import is_moving_designation
from . import identify_score as score

# I due vocabolari chiusi di `objects`. Stanno anche nel CHECK dello schema, e un test li tiene
# incollati: due elenchi che possono divergere in silenzio non sono un vocabolario.
IDENTITY_METHODS = ("coord_confirmed", "coord_review", "exact_name", "historic_name", "user")
IDENTITY_CONFIDENCES = ("certain", "high", "low", "user")

BRANCHES = (
    "moving",
    "name_and_sky_agree",
    "sky_disagrees",
    "sky_only",
    "sky_ambiguous",
    "name_only",
    "free_name_only",
    "nothing",
)

# Il codice con cui si chiude lo stadio di una posa senza nome e senza cielo: non e' un guasto,
# e' l'unica cosa che l'app non puo' dedurre da sola.
NO_NAME_NO_SKY = "no_name_no_sky"
# E quello di una posa della stessa specie di cui l'utente ha detto "non e' un oggetto": uno scatto
# di prova, una messa a fuoco (`spine/unnamed.py`). La domanda e' chiusa, e nessun oggetto nasce.
NOT_AN_OBJECT = "not_an_object"


# Quanto vale una fiducia, dalla migliore. `user` non c'e' dentro: la risposta dell'utente non
# si confronta con niente, si rispetta.
_RANK = {"certain": 0, "high": 1, "low": 2}

# La sola fiducia che e' una DOMANDA. `high` non lo e': "identificato dal solo nome" e' un modo
# di sapere, non un dubbio da girare all'utente.
DOUBT = "low"


def confidence_after(current, new):
    """La fiducia dell'oggetto dopo che una posa nuova l'ha agganciato.

    **`low` e' assorbente**: un oggetto su cui una posa ha lasciato un dubbio resta da confermare
    finche' l'utente non risponde, invece di vedere il dubbio cancellato dalla posa successiva.
    Chiedere una volta di piu' costa un clic; agganciare in silenzio il bersaglio sbagliato costa
    le ore di una stagione.

    **Fra le altre vince la migliore**, che e' la descrizione vera di come l'oggetto e' stato
    identificato. Tenere sempre la piu' dubbiosa sembrava prudente e mentiva: sulle 41 pose vere
    dell'Iris, l'unica che il solver non ha risolto faceva scrivere `exact_name` / `high` a un
    oggetto che il cielo aveva confermato quaranta volte. Non cambiava cosa l'app chiede -- solo
    `low` e' una domanda -- ma raccontava la cosa sbagliata.

    `user` non entra mai nel confronto: chi chiama controlla il lucchetto prima."""
    if current is None:
        return new
    if DOUBT in (current, new):
        return DOUBT
    return min((current, new), key=lambda c: _RANK.get(c, len(_RANK)))


def _decision(branch, *, slug=None, name=None, method=None, confidence=None, review=False):  # noqa: PLR0913
    return {
        "branch": branch,
        "slug": slug,
        "name": name,
        "method": method,
        "confidence": confidence,
        "review": review,
    }


def decide(*, raw_name, hit, cands, fov_radius_deg):
    """Quale oggetto e' questa posa.

    `raw_name` e' il nome dell'header gia' ripulito (puo' essere vuoto); `hit` e' la voce di
    catalogo che porta quella sigla (con `slug` e `is_primary`) o `None` se la sigla non esiste
    o non e' una sigla; `cands` sono i candidati del cielo, dal migliore, o vuoti se la posa
    non ha cielo misurato."""
    name = (raw_name or "").strip()

    if is_moving_designation(name):
        # Una cometa non sta due notti nello stesso punto: il cono direbbe l'oggetto fisso che
        # c'era dietro, e lo direbbe **sicuro di se'**. Qui il cielo non si consulta proprio.
        return _decision("moving", name=name, method="exact_name", confidence="high")
    if cands:
        return _from_the_sky(hit, cands, fov_radius_deg)
    if hit:
        method = "exact_name" if hit["is_primary"] else "historic_name"
        return _decision("name_only", slug=hit["slug"], method=method, confidence="high")
    if name:
        return _decision(
            "free_name_only", name=name, method="exact_name", confidence="low", review=True
        )
    return _decision("nothing")


def _from_the_sky(hit, cands, fov_radius_deg):
    named = next((c for c in cands if c["slug"] == hit["slug"]), None) if hit else None
    if named:
        return _decision(
            "name_and_sky_agree",
            slug=named["slug"],
            method="coord_confirmed",
            confidence="certain",
        )
    if hit:
        # Il nome resta agganciato come ipotesi: e' cio' che l'utente ha scritto, e vale piu'
        # del nostro punteggio finche' non risponde. Chi mostra la domanda ha i candidati per
        # dire cosa c'e' invece a quelle coordinate.
        return _decision(
            "sky_disagrees", slug=hit["slug"], method="coord_review", confidence="low", review=True
        )

    best = cands[0]
    second = cands[1] if len(cands) > 1 else None
    if second and score.is_ambiguous(
        best, second, separation_deg=_between(best, second), fov_radius_deg=fov_radius_deg
    ):
        return _decision(
            "sky_ambiguous",
            slug=best["slug"],
            method="coord_review",
            confidence="low",
            review=True,
        )
    return _decision("sky_only", slug=best["slug"], method="coord_confirmed", confidence="certain")


def _between(first, second):
    """Quanto distano i due candidati fra loro.

    Si misura sulle coordinate, non sulla differenza dei loro scarti dal centro: due oggetti a
    mezzo grado dal centro in direzioni opposte distano un grado e quella sottrazione direbbe
    zero. Sbagliare per difetto qui e' il verso pericoloso -- "sono vicini" diventa "uno
    contiene l'altro", cioe' si aggancia in silenzio invece di chiedere."""
    return units.angular_separation_deg(
        first["ra_deg"], first["dec_deg"], second["ra_deg"], second["dec_deg"]
    )
