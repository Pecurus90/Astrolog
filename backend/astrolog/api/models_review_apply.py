"""La forma delle **risposte** di Da confermare: cio' che l'Applica accetta, e cosa torna.

Le pagine lette stanno in `models_review.py`. Vale la stessa convenzione: si risponde con la
chiave stabile letta dalla pagina, mai col numero di riga, e i nomi vengono dal glossario.
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models_review import Band, ReviewSeen
from .models_review_groups import MosaicAnswer, TypelessAnswer, UnfilteredAnswer


class BandIn(BaseModel):
    band: Band
    width_nm: float | None = None


class FilterCorrection(BaseModel):
    """La scheda di un filtro, o "e' lo stesso filtro di" (`merge_into`)."""

    name: str | None = Field(None, min_length=1)
    brand: str | None = None
    model: str | None = None
    catalog_id: str | None = None
    bands: list[BandIn] | None = None
    merge_into: int | None = None


class FilterEdit(FilterCorrection):
    id: int
    is_none: bool | None = None


class LookalikeEdit(BaseModel):
    """La risposta a "sono lo stesso pezzo?": si' unisce `id` dentro `into_id`, no dice che sono
    due pezzi e la proposta non torna."""

    id: int
    into_id: int
    same: bool


class ObjectEdit(BaseModel):
    """La risposta su un oggetto: uno slug di catalogo (di solito un candidato cliccato) oppure
    un nome scritto a mano."""

    key: str = Field(min_length=1)  # la chiave stabile letta dalla pagina, mai l'id di riga
    slug: str | None = None
    name: str | None = Field(None, min_length=1)

    @model_validator(mode="after")
    def one_target_only(self):
        """Uno solo dei due, e almeno uno. Sono la stessa domanda, non due: accettarli tutti e
        due vorrebbe dire scegliere noi quale vince, e nessuna delle due scelte e' cio' che
        l'utente ha chiesto. Il controllo sta qui e non nella rotta perche' e' una forma della
        richiesta, e cosi' l'OpenAPI lo dichiara e la risposta e' il 422 di sempre."""
        if bool(self.slug) == bool(self.name):
            raise ValueError("un bersaglio solo: slug oppure name")
        return self


class CoordinatesEdit(BaseModel):
    """La risposta su un posto: "le pose riprese a queste coordinate sono di questo sito".

    Si manda l'id del sito perche' e' quello che la pagina ha in mano dopo un clic; a scriverla
    e' il **nome**, che e' la chiave che sopravvive."""

    key: str = Field(min_length=1)  # le coordinate lette dalla pagina, mai un numero di riga
    site_id: int


class UnfilteredEdit(BaseModel):
    """La risposta su una camera: le sue pose che non dicono il filtro sono di una camera a colori
    (`color`), riprese senza nessun filtro (`no_filter`), o con uno dei tuoi filtri (`filter`, e
    `filter_id` dice quale)."""

    key: str = Field(min_length=1)  # il nome della camera letto dalla pagina
    answer: UnfilteredAnswer
    filter_id: int | None = None

    @model_validator(mode="after")
    def a_filter_says_which(self):
        """Il filtro c'e' con "uno dei tuoi" e solo li': senza, la risposta non direbbe quale, e
        con un'altra risposta sarebbe un secondo bersaglio fra cui scegliere noi."""
        if (self.filter_id is None) == (self.answer == "filter"):
            raise ValueError("filter_id con la risposta filter, e solo con lei")
        return self


class OpticslessEdit(BaseModel):
    """La risposta su una camera a una focale: con che ottica. Si scrive il **nome**: uno che
    l'Attrezzatura non ha fa nascere il pezzo, come un header."""

    key: str = Field(min_length=1)  # la chiave letta dalla pagina
    optics: str = Field(min_length=1, pattern=r"\S")  # un nome di soli spazi non e' un nome


class RiglessGroupEdit(BaseModel):
    """La risposta su un gruppo: con che corredo sono state riprese quelle pose. Un corredo fra
    quelli che l'app conosce (`rig_id`, cio' che la pagina ha in mano dopo un clic) **oppure** i
    pezzi scritti: la camera e la **focale**, piu' l'ottica se serve. A essere scritti sono sempre i
    **nomi**, e i pezzi nascono da quei nomi come nascono da un header."""

    key: str = Field(min_length=1)  # la chiave del gruppo letta dalla pagina
    rig_id: int | None = None
    optics: str | None = Field(None, min_length=1)
    camera: str | None = Field(None, min_length=1)
    focal_mm: float | None = Field(None, gt=0)  # focale ignota, mai inventata: niente zeri

    @model_validator(mode="after")
    def one_way_only(self):
        """Un corredo dall'elenco oppure i pezzi, e almeno uno dei due: accettarli tutti e due
        vorrebbe dire scegliere noi quale vince, e nessuna delle due e' quella dell'utente. Il
        controllo sta qui perche' e' una forma della richiesta, cosi' l'OpenAPI lo dichiara e la
        risposta e' il 422 di sempre."""
        if bool(self.rig_id) == bool(self.camera):
            raise ValueError("un corredo dall'elenco, oppure la camera scritta")
        if self.rig_id and (self.optics or self.focal_mm):
            raise ValueError("un corredo dall'elenco porta i suoi pezzi")
        if self.camera and self.focal_mm is None:
            # Un corredo e' ottica + camera **a una focale**, e una focale ignota non e' la stessa
            # cosa di una focale nota: senza, questo corredo e quello che i file diranno domani
            # sarebbero due gemelli per sempre, con le ore spartite fra i due (misurato).
            raise ValueError("con la camera si scrive anche la focale")
        return self


class TypelessFolderEdit(BaseModel):
    """La risposta su una cartella di frame che non dicono che file sono: una foto del cielo
    (`light`) o un file di calibrazione (`calibration`). Le parole sono due e stanno nel modello,
    cosi' una terza e' un 422 dichiarato nell'OpenAPI e non una risposta da interpretare."""

    key: str = Field(min_length=1)  # il percorso della cartella letto dalla pagina
    kind: TypelessAnswer


class UnnamedEdit(BaseModel):
    """La risposta su un gruppo di pose senza nome e senza cielo: quale oggetto e' -- uno slug di
    catalogo o un nome scritto -- oppure "non e' un oggetto"."""

    key: str = Field(min_length=1)  # la chiave del gruppo letta dalla pagina
    slug: str | None = Field(None, min_length=1)
    name: str | None = Field(None, min_length=1)
    not_an_object: bool = False

    @model_validator(mode="after")
    def one_answer_only(self):
        """Una risposta sola, e almeno una: accettarne due vorrebbe dire scegliere noi chi vince. Un
        nome di soli spazi non e' una risposta: scritto, la regola lo leggerebbe come riga storta e
        l'Applica direbbe "fatto" senza che niente cambi."""
        nome = bool(self.name and self.name.strip())
        if [bool(self.slug), nome, self.not_an_object].count(True) != 1:
            raise ValueError("una risposta sola: slug, name oppure not_an_object")
        return self


class MosaicEdit(BaseModel):
    """La risposta su un mosaico proposto: si', quei pannelli sono un mosaico (`yes`), oppure no.

    Si manda la **chiave** del mosaico letta dalla pagina."""

    key: str = Field(min_length=1)
    answer: MosaicAnswer
    name: str | None = None  # di cosa e' il mosaico: col si' c'e' sempre, col no mai

    @model_validator(mode="after")
    def a_yes_says_what(self):
        """Una domanda sola (Marco, 22/9/2026): il si' dice di cosa, il no non dice niente. Un nome
        di soli spazi non e' un nome: scritto, il mosaico si chiamerebbe con un vuoto."""
        nome = bool(self.name and self.name.strip())
        if nome != (self.answer == "yes") or (self.name is not None and not nome):
            raise ValueError("il si' con il nome del mosaico, il no senza")
        return self


class ReviewApply(BaseModel):
    """Tutte le decisioni insieme: si scrivono in una transazione sola, e cio' che e'
    elencato nella pagina resta confermato anche se non lo si e' toccato.

    **Un campo che non esiste e' un errore, non una svista da ignorare** (`extra="forbid"`): una
    pagina aperta prima di un aggiornamento del server manderebbe il nome vecchio, Pydantic lo
    scarterebbe in silenzio e l'Applica confermerebbe **tutto**, compreso cio' che quella pagina
    non ha mai mostrato. Sul NAS e' lo scenario ordinario -- una scheda lasciata aperta sul
    tablet -- e il danno cade dalla parte che non si rivede. Meglio un 422 che si vede."""

    model_config = ConfigDict(extra="forbid")

    lookalikes: list[LookalikeEdit] = []
    filters: list[FilterEdit] = []
    objects: list[ObjectEdit] = []
    unclear: list[CoordinatesEdit] = []
    unfiltered: list[UnfilteredEdit] = []
    rigless: list[RiglessGroupEdit] = []
    opticsless: list[OpticslessEdit] = []
    unnamed: list[UnnamedEdit] = []
    typeless: list[TypelessFolderEdit] = []
    mosaics: list[MosaicEdit] = []
    # Fin dove la pagina che si sta applicando aveva guardato. Assente vuol dire "conferma cio'
    # che c'e' adesso": la chiede chi non ha letto una pagina, e non e' la via del bottone.
    seen: ReviewSeen | None = None


class ReviewApplied(BaseModel):
    changed: int  # risposte scritte
    confirmed: int  # voci che da adesso non si richiedono piu'
    requeued: int  # pose rimesse in coda perche' la risposta le riguarda
    run_started: bool  # False se il worker era occupato: il lavoro resta in coda
