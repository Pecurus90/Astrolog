"""La forma della pagina di **Da confermare**: le domande che l'app non sa risolvere da sola.

Vale la convenzione di `models.py`: "non so" e' un campo con codice, mai un null muto; i nomi
vengono dal glossario. La pagina ha tre file, uno per mestiere: qui filtri, pezzi e oggetti e
`ReviewOut` che li tiene insieme; i **gruppi di pose su cui l'app chiede** in
`models_review_groups.py`, che e' il file che cresce a ogni domanda nuova; le **risposte** in
`models_review_apply.py`.
"""

from typing import Literal

from pydantic import BaseModel

from .models_page import Page
from .models_review_groups import (
    MosaicCandidate,
    OpticslessRig,
    RiglessGroup,
    TypelessFolder,
    UnclearCoordinates,
    UnfilteredCamera,
    UnnamedGroup,
)

# --- Da confermare: cio' che la scansione ha trovato, e le risposte dell'utente ---------

InstrumentKind = Literal[
    "optics", "camera", "mount", "reducer", "filter_wheel", "guide_scope", "guide_camera",
    "focuser",
]  # fmt: skip
# Le bande che si possono DICHIARARE sono quelle fisiche, mai un'etichetta derivata: un
# filtro non lascia passare "duo". Scritte qui perche' un `Literal` vuole valori costanti, e
# un test verifica che dicano le stesse parole di `vocab.filters.BANDS`.
Band = Literal["L", "R", "G", "B", "HA", "HB", "OIII", "SII"]
# Il colore di una camera: le parole del CHECK dello schema e di `spine.declarations`, tenute
# incollate da un test. La risposta "a colori" sulle pose che non dicono il filtro e' la stessa.
CameraType = Literal["mono", "color"]
# I campi che una scheda puo' chiedere: quali per ogni tipo lo dice `instrument_answer.CARD`, e un
# test tiene questo elenco incollato a quello e ai campi che la risposta accetta.
CardField = Literal[
    "brand", "model", "camera_type", "pixel_size_um", "aperture_mm", "focal_mm", "reducer_factor",
    "weight_kg", "payload_kg", "slots", "notes",
]  # fmt: skip
# Come e' stato identificato un oggetto, e quanto ci si fida. Stessa ragione del `Literal` qui
# sopra: i valori sono costanti, e un test li tiene incollati a `spine.identify_decide` -- che a
# sua volta ha la sua guardia contro il CHECK dello schema.
IdentityMethod = Literal["coord_confirmed", "coord_review", "exact_name", "historic_name", "user"]
IdentityConfidence = Literal["certain", "high", "low", "user"]


class BandOut(BaseModel):
    band: Band
    width_nm: float | None  # facoltativa: un anti inquinamento luminoso non la dichiara


class FilterModelOut(BaseModel):
    """Un filtro IN COMMERCIO, come si legge in tendina quando si dichiara un filtro nuovo.

    Non e' un filtro dell'archivio: e' una voce del vocabolario che l'app si porta dentro. Gli
    **alias** restano fuori -- servono a riconoscere una grafia nell'header, e a schermo sarebbero
    rumore. Quando si sceglie da qui, `catalog_id` ricorda quale voce era."""

    id: str
    brand: str
    name: str
    passband: str


class FilterModelList(BaseModel):
    items: list[FilterModelOut]


class FilterCandidate(BaseModel):
    """Uno dei tuoi filtri, fra cui si sceglie una risposta: uno con la banda nota."""

    id: int
    name: str
    passband: str


class FilterOut(BaseModel):
    id: int
    name: str
    brand: str | None
    model: str | None
    catalog_id: str | None
    passband: str
    is_none: bool
    bands: list[BandOut]
    frames: int


class RigChoice(BaseModel):
    """Uno dei tuoi corredi, fra cui si sceglie con che camera sono state riprese delle pose: solo
    quelli con una camera, perche' uno senza non risponde a quella domanda."""

    id: int
    name: str | None  # quello che gli hai dato tu; senza, la pagina mostra i due pezzi
    optics: str | None
    camera: str
    focal_mm: float | None


class LookalikeOut(BaseModel):
    """Due grafie che hanno tutta l'aria di essere la stessa camera: "sono lo stesso pezzo?". Si'
    unisce `id` dentro `into_id`, no non la propone piu'."""

    id: int
    name: str
    frames: int
    into_id: int
    into_name: str
    into_frames: int


class ObjectCandidate(BaseModel):
    """Una voce che il cielo ha trovato nel campo di questo oggetto: e' cio' che si clicca per
    rispondere. La scrive chi identifica (`spine/object_candidates.py`), e la pagina la legge."""

    slug: str
    name: str
    common_name: str | None
    in_frame: bool | None  # None quando il cielo non porta lati o rotazione: si e' detto cerchio


class ObjectOut(BaseModel):
    """Un oggetto dell'archivio. `name` sono i due passi del contratto gia' fatti dal backend:
    il nome primario, o quello che il catalogo da' allo slug."""

    id: int  # il numero di riga: serve al frontend come chiave di lista, non per rispondere
    key: str  # la chiave stabile con cui si risponde: lo slug di catalogo, o il nome
    name: str | None
    slug: str | None
    method: IdentityMethod | None
    confidence: IdentityConfidence | None
    frames: int
    integration_s: float  # la somma del tempo delle pose; a schermo si legge in ore
    untimed: int  # quante di quelle pose non dicono il tempo: non valgono zero, si contano qui
    confirmed: bool
    candidates: list[ObjectCandidate] = []  # solo su quelli da decidere


class SettledObjects(Page[ObjectOut]):
    """Gli oggetti gia' visti, senza niente da scegliere, a pagine: non sono domande, e crescono
    con l'archivio (Marco, 27/9/2026). Si aprono dalla sezione Oggetti, e da li' si correggono. Un
    dubbio di cui il cielo non sa dire niente sta qui, una volta visto: non c'e' niente da
    cliccare."""


class ReviewSeen(BaseModel):
    """Fin dove la pagina ha guardato gli oggetti: il numero di riga piu' alto che ha davvero
    elencato. L'Applica lo rimanda e conferma solo fino a li'.

    Numeri di riga e non orari, perche' **due righe nate nello stesso istante non si ordinano**
    (la misura e il perche' stanno in `docs/domini/spina.md`, sezione Da confermare).

    Zero vuol dire "non ho visto niente", ed e' anche cio' che vale quando la pagina non elenca
    nessun oggetto: non e' un limite mancante, e' un limite che non lascia passare niente. Chi non
    manda `seen` del tutto sta dicendo un'altra cosa -- "conferma cio' che c'e' adesso" -- e la sua
    casa e' `ReviewApply`."""

    objects: int = 0


class ReviewOut(BaseModel):
    """Tutta la pagina in una risposta: non e' un elenco paginato, sono le domande aperte."""

    lookalikes: list[LookalikeOut]  # due grafie che sembrano la stessa camera
    filters: list[FilterOut]
    rig_choices: list[RigChoice]  # i corredi fra cui si risponde sulle pose senza camera
    objects: list[ObjectOut]  # quelli da decidere e quelli nuovi; i dubbi in cima
    settled_objects: int  # quanti sono gli altri, gia' visti: si leggono a pagine
    unnamed: list[UnnamedGroup]
    unclear: list[UnclearCoordinates]  # i posti su cui l'app chiede: vuoto quando non chiede
    unfiltered: list[UnfilteredCamera]  # le camere le cui pose non dicono il filtro
    filter_choices: list[FilterCandidate]  # i filtri con la banda nota, fra cui si risponde
    rigless: list[RiglessGroup]  # i gruppi di pose che non dicono la camera
    opticsless: list[OpticslessRig]  # le camere a una focale le cui pose non nominano l'ottica
    optics_choices: list[str]  # le ottiche che hai, fra cui si risponde a quella domanda
    typeless: list[TypelessFolder]  # le cartelle i cui frame non dicono che file sono
    mosaics: list[MosaicCandidate]  # le regioni riprese a pannelli affiancati
    to_confirm: int
    seen: ReviewSeen  # fin dove questa pagina ha guardato: l'Applica lo rimanda e conferma solo
    #                   cio' che era elencato, mai cio' che e' arrivato nel frattempo
