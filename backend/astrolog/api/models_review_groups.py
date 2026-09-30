"""I **gruppi di pose su cui l'app chiede**: la forma di ogni domanda di Da confermare.

Vincolo non ovvio: si chiede per **gruppo, mai per posa** -- per cartella, per coordinate, per
camera, per notte, per regione di cielo -- e ogni gruppo porta la chiave
stabile con cui si risponde, mai un numero di riga. Un gruppo gia' risposto resta in pagina, perche'
si deve poter cambiare idea: e' `answer` a dire se e' ancora una domanda.

L'inventario di cio' che l'utente possiede, e la pagina intera, stanno in `models_review.py`; le
risposte in `models_review_apply.py`.
"""

from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel

# Una distanza esce dall'API come lo schermo la mostra: un decimale, cioe' cento metri. Quindici
# decimali non sono una misura, sono la rappresentazione di una float. Si arrotonda **qui**, una
# volta sola per tutti i campi che la mandano, e non in `place.distance_km`: quella serve anche a
# decidere se due coordinate sono lo stesso posto (`spine.group.SAME_PLACE_KM`), e arrotondarla
# li' sposterebbe la soglia invece di cambiare come si legge un numero.
DistanceKm = Annotated[float, AfterValidator(lambda km: round(km, 1))]


class Subject(BaseModel):
    """Un oggetto che il cielo ha trovato nelle pose di un gruppo, e in quante."""

    name: str
    frames: int


class Subjects(BaseModel):
    """Cosa hai ripreso in quel gruppo, per ricordarlo senza andare a memoria: gli oggetti, il piu'
    ripreso in cima, e le pose dei due vuoti -- che non sono lo stesso: `not_yet` e' il cielo che
    non ci ha ancora guardato (o non ci e' riuscito), `not_found` il cielo che ha guardato senza
    trovare niente. Si legge
    accanto alla domanda e non la cambia: la chiave del gruppo resta quella."""

    found: list[Subject]
    not_found: int
    not_yet: int


class UnnamedAnswer(BaseModel):
    """Cosa l'utente ha detto di un gruppo di pose senza nome e senza cielo: un oggetto di
    catalogo (`value` e' lo slug), un nome scritto, oppure "non e' un oggetto" (`value` vuoto).
    `name` e' come l'oggetto si mostra: il nome della voce, o quello scritto."""

    kind: Literal["catalog", "name", "none"]
    value: str | None
    name: str | None


class UnnamedGroup(BaseModel):
    """Le pose che l'header non nomina e di cui il cielo non dice niente, raggruppate per **notte,
    camera, telescopio e puntamento** (Marco, 24/9/2026), mai per file ne' per cartella. Il gruppo
    si mostra con quei valori; il puntamento e' quello della posa che l'ha aperto. Un gruppo
    risposto resta in pagina con `answer`, perche' si deve poter cambiare idea."""

    key: str  # la chiave del gruppo: si risponde con lei, e non si riapre
    night: str | None  # la notte, YYYY-MM-DD; vuota per chi non dice quando
    camera: str | None  # `INSTRUME` com'e' scritto nel file
    telescope: str | None  # `TELESCOP` com'e' scritto nel file
    ra_deg: float | None  # dove puntava la montatura, dall'header
    dec_deg: float | None
    frames: int
    answer: UnnamedAnswer | None
    # la prima e l'ultima posa, ISO nel fuso della notte: due oggetti senza puntamento nella stessa
    # notte sono un gruppo solo, e le ore dicono a chi risponde se sono due. Contano le pose con
    # `DATE-OBS`: nulle se nessuna lo dice
    first_frame: str | None
    last_frame: str | None


class SiteCandidate(BaseModel):
    """Un luogo gia' dichiarato, con quanto dista da quelle coordinate: e' cio' che si clicca
    per rispondere. Si ricalcola alla lettura, non si salva."""

    id: int
    name: str
    distance_km: DistanceKm


class UnclearCoordinates(BaseModel):
    """Le pose che l'app ha fermato perche' le coordinate dell'header dicono un altro posto,
    raggruppate per **coordinate**: si chiede per gruppo, mai per posa. Le notti sono quelle
    coinvolte, calcolate nel fuso di quelle coordinate. `site` e' la risposta gia' data, se
    c'e': un gruppo risposto resta in pagina perche' un clic sbagliato si deve poter cambiare."""

    key: str  # le coordinate arrotondate: e' la chiave con cui si risponde
    latitude: float
    longitude: float
    distance_km: DistanceKm | None  # da casa; None senza un luogo di casa (mai uno zero finto)
    frames: int
    nights: list[str]
    site: str | None
    candidates: list[SiteCandidate]
    subjects: Subjects


# Cosa l'utente dice del FILTRO di una camera le cui pose non lo dicono: le parole di
# `spine.unfiltered`, e un test le tiene incollate. Il sensore lo dice la scheda (`CameraType`).
UnfilteredAnswer = Literal["color", "no_filter", "filter"]


class UnfilteredCamera(BaseModel):
    """Le pose che non dicono il filtro, raggruppate per **camera**: senza `BAYERPAT` una mono e
    una camera a colori non si distinguono, e si chiede una volta sola. Una camera che la scheda o
    i file dicono a colori non c'e': le sue pose sono OSC. `answer` e' la risposta gia' data: un
    gruppo risposto resta in pagina perche' si deve poter cambiare idea."""

    key: str  # il nome della camera: e' la chiave con cui si risponde
    frames: int
    answer: Literal["no_filter", "filter"] | None  # "a colori" la toglie dalla pagina
    filter_id: int | None  # con "uno dei tuoi", quale; vuoto se quel filtro non c'e' piu'
    subjects: Subjects


# Le due risposte su una cartella di frame che non dicono CHE FILE SONO: le parole di
# `spine.typeless.ANSWERS`, e un test le tiene incollate. Non c'e' un "non so": non saperlo e'
# gia' lo stato di partenza, e una terza risposta non toglierebbe quei frame da nessuna parte.
TypelessAnswer = Literal["light", "calibration"]


class TypelessFolder(BaseModel):
    """I frame che non dicono che file sono, raggruppati per **cartella**: chi riprende tiene dark
    e flat in cartelle loro, quindi una risposta chiude una cartella intera. Ci sono solo le
    cartelle dove il cielo non sa dire -- risolto e' una foto, senza stelle una calibrazione --, e
    finche' non si risponde quei frame restano fermi prima dell'oggetto: non diventano ore, e non
    compaiono fra i frame senza nome -- li' la domanda e' "cosa hai ripreso", e rispondere con un
    oggetto trasformerebbe una calibrazione in ore. Un gruppo risposto resta in pagina perche' si
    deve poter cambiare idea. Cio' che il cielo ha trovato qui non c'e', e non e' una
    dimenticanza: su quei frame il cielo non ha saputo dire, e mostrare "nessun oggetto"
    sembrerebbe una risposta."""

    key: str  # il percorso della cartella: e' la chiave con cui si risponde
    frames: int
    answer: TypelessAnswer | None


class GroupRig(BaseModel):
    """Il corredo che l'utente ha detto per un gruppo: i **nomi** dei pezzi, mai i numeri di
    riga. `optics` vuoto vuol dire che non l'ha detta, non che non c'era."""

    optics: str | None
    camera: str
    focal_mm: float | None


class OpticslessRig(BaseModel):
    """Le pose i cui file non nominano l'ottica (l'ASIAIR ci scrive la montatura, altri non la
    scrivono affatto), una domanda per **camera e focale**: "quale ottica era?". La risposta vale
    anche per le pose che arriveranno; una domanda risposta resta in pagina per cambiare idea."""

    key: str  # la chiave della camera a quella focale: si risponde con lei
    camera: str
    focal_mm: float | None
    frames: int
    integration_s: float
    untimed: int
    answer: str | None  # il nome dell'ottica gia' detta
    subjects: Subjects


class RiglessGroup(BaseModel):
    """Le pose che non dicono con che camera sono state riprese, raggruppate per **notte e valori
    dell'header** (Marco, 23/9/2026): si chiede per gruppo, mai per posa, e mai per cartella. Il
    gruppo si mostra con la notte -- vuota per le pose senza data -- e i valori che lo fanno. Ci
    cadono anche le pose che portano il telescopio ma non la camera (l'ASIAIR scrive la montatura in
    `TELESCOP`). `optics` e `focal_mm` sono cio' che le pose dicono gia', quando dicono una cosa
    sola; `focal_suggested` la focale nativa dell'ottica in scheda, da proporre dove le pose non la
    portano. Un gruppo risposto resta in pagina perche' si deve poter cambiare idea."""

    key: str  # la chiave del gruppo: si risponde con lei, e non si riapre
    night: str | None  # la notte, YYYY-MM-DD; vuota per chi non dice quando
    telescope: str | None  # `TELESCOP` com'e' scritto nel file: e' nella chiave, e va a video
    width_px: int | None
    height_px: int | None
    pixel_um: float | None
    frames: int
    optics: str | None
    focal_mm: float | None
    focal_suggested: float | None
    answer: GroupRig | None
    subjects: Subjects


# Le due risposte su un mosaico proposto: le parole di `spine.declarations.MOSAIC_ANSWERS`, e un
# test le tiene
# incollate. Un no e' una risposta come un si': senza, l'unico modo di far tacere una proposta
# sbagliata sarebbe accettarla.
MosaicAnswer = Literal["yes", "no"]


class MosaicCandidate(BaseModel):
    """Una regione ripresa a **pannelli affiancati**, come la pagina la propone: quanti pannelli,
    quante pose e quali soggetti tocca -- spesso piu' d'uno, perche' ogni pannello inquadra una
    parte diversa del complesso e l'app li identifica come oggetti diversi.

    Si risponde con la **chiave** del mosaico, che non cambia quando cambia la camera. Un gruppo
    risposto resta in pagina: si deve poter cambiare idea."""

    key: str  # cio' con cui si risponde
    ra_deg: float  # il centro del mosaico: a schermo dice quale, se due hanno lo stesso nome
    dec_deg: float
    object: str  # i soggetti che tocca, coi loro nomi, in ordine alfabetico
    panels: int
    frames: int
    integration_s: float  # la somma del tempo dei pannelli; a schermo si legge in ore
    untimed: int  # quante di quelle pose non dicono il tempo: non valgono zero, si contano qui
    answer: MosaicAnswer | None
    answer_name: str | None  # di cosa e' il mosaico, come l'ha detto l'utente; solo col si'
    names: list[str]  # i soggetti di `object`, uno per voce, e la proposta: i suggerimenti
    proposed: str  # la voce del catalogo al centro: il campo arriva compilato con lei
