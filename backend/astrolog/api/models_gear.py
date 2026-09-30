"""La forma di cio' che la pagina **Attrezzatura** mostra, e di cio' che le si dice.

Vincolo non ovvio: **cio' che non si sa e' `None`, e non zero**. Le ore di una montatura sono
nulle perche' nessun file la lega a una posa, e la scala di un corredo che non ha ancora ripreso
non esiste: chi mostra la riga dice **perche'** manca, e un numero al loro posto sarebbe un dato
falso che nessuno potrebbe smentire (`docs/domini/attrezzatura.md`).
"""

from typing import Literal

from pydantic import BaseModel, Field

from .models_review import BandOut, CameraType, CardField, InstrumentKind
from .models_review_apply import BandIn


class InstrumentCardIn(BaseModel):
    """La scheda di un pezzo come la si scrive: i campi, e basta. La usano il pezzo che nasce e
    quello che si corregge, perche' il giorno che un campo cambia forma non cambi in un gesto e
    nell'altro no. **Il nome no**: correggendo e' un campo come gli altri e si puo' non mandarlo,
    creando e' cio' che fa esistere il pezzo -- quindi lo dichiara chi lo chiede, con la sua forma.

    Le **misure** valgono solo positive: uno zero non e' una misura, e' un vuoto scritto male, e
    una volta in scheda chi ne deriva lo scarta in silenzio -- una focale 0 fa sparire la scala.
    E' la stessa regola che `RiglessGroupEdit.focal_mm` impone alla risposta sulla camera:
    "ignota, mai inventata" o vale in tutte le case, o non e' una regola."""

    brand: str | None = None
    model: str | None = None
    camera_type: CameraType | None = None
    pixel_size_um: float | None = Field(None, gt=0)
    aperture_mm: float | None = Field(None, gt=0)
    focal_mm: float | None = Field(None, gt=0)
    reducer_factor: float | None = Field(None, gt=0)
    weight_kg: float | None = Field(None, gt=0)
    payload_kg: float | None = Field(None, gt=0)
    slots: int | None = Field(None, gt=0)  # un conto: zero non e' "non lo so", e' nessuna ruota
    backfocus_mm: float | None = Field(None, gt=0)
    notes: str | None = None


class InstrumentCorrection(InstrumentCardIn):
    """La scheda di un pezzo che c'e' gia', o l'unione con un altro (`merge_into`, "e' lo stesso
    pezzo di", e allora il resto non conta). Mandare il nome e' rinominare; non mandarlo lascia
    quello che c'e'. Quale pezzo sia lo dice l'indirizzo."""

    name: str | None = Field(None, min_length=1)
    merge_into: int | None = None


class RigNaming(BaseModel):
    """Il nome che dai a un corredo: e' cosi' che si dichiara."""

    name: str = Field(min_length=1)


class FilterNew(BaseModel):
    """Un filtro che scrivi tu: il nome, e la banda che lascia passare -- e' cio' che sblocca le
    pose. Marca e modello se vuoi."""

    name: str = Field(min_length=1)
    bands: list[BandIn] = Field(min_length=1)
    brand: str | None = None
    model: str | None = None


class RigNew(BaseModel):
    """Un corredo che scrivi tu: ottica e camera fra i tuoi pezzi, e la focale -- senza, i file
    che la dicono farebbero nascere un secondo corredo."""

    optics_id: int
    camera_id: int
    focal_mm: float = Field(gt=0)


class RigMount(BaseModel):
    """La montatura con cui usi un corredo, fra quelle che possiedi; `None` torna a quella che
    dicono i file."""

    mount_id: int | None


class GearObject(BaseModel):
    """Un oggetto ripreso con quel pezzo, e quanto ci ha pesato."""

    key: str
    name: str | None
    frames: int
    integration_s: float


class InstrumentOnPage(BaseModel):
    """Un pezzo dell'attrezzatura: la sua scheda -- i campi vuoti sono quelli che l'header non sa
    dire e che compila l'utente -- piu' quanto e' servito e cosa ci hai ripreso."""

    id: int
    kind: InstrumentKind
    name: str
    brand: str | None
    model: str | None
    camera_type: CameraType | None
    pixel_size_um: float | None
    # ricavato dal cielo quando i file non lo dicono: in un campo suo, perche' chi lo mostra dica
    # che e' ricavato e non lo confonda con quello dei file o dell'utente
    pixel_from_sky_um: float | None
    aperture_mm: float | None
    focal_mm: float | None
    reducer_factor: float | None
    weight_kg: float | None
    payload_kg: float | None
    slots: int | None
    backfocus_mm: float | None
    notes: str | None
    detected: bool  # rilevato dai file, o dichiarato da te
    mergeable_into: list[int]  # i pezzi in cui si puo' unire: solo quelli che la spina accetta
    # Nulli dove il legame con le pose non esiste: un genere che in **questo archivio** nessuna
    # posa nomina non ha zero ore, ha ore che l'app non sa -- e chi mostra la riga lo dice. Chi
    # lo decide e' `spine/inventory.py`, non questa forma.
    frames: int | None
    integration_s: float | None
    untimed: int | None
    nights: int | None
    objects: list[GearObject]
    # Falso per un pezzo nato a meta' giro, che chi conta non ha ancora contato: "non ancora
    # contato" non e' "non si puo' sapere", e la pagina li dice diversi.
    counted: bool
    # Perche' un pezzo contato non ha ore da mostrare: i file non nominano quel genere, o e' una
    # montatura che nessun corredo porta ancora. `None` quando le ore ci sono.
    no_hours: Literal["files_silent", "no_rig"] | None


class RigOnPage(BaseModel):
    """Un corredo: com'e' fatto, quanto e' servito, e **quanto cielo inquadra davvero**."""

    id: int
    name: str | None  # il nome che gli hai dato, se gliene hai dato uno
    # la montatura che gli hai dato tu; dove taci, le pose prendono quella che il file nomina
    mount_id: int | None
    optics: str | None
    camera: str | None
    focal_mm: float | None
    # nulli finche' non e' contato (`counted`): un corredo nato a meta' giro
    frames: int | None
    integration_s: float | None
    untimed: int | None
    nights: int | None
    objects: list[GearObject]
    counted: bool
    # Misurati sulle pose risolte, mediana: nulli finche' il riconoscitore non ne ha risolta
    # nessuna. Si chiamano come nello schema (`frame_wcs`), che e' da dove vengono.
    scale_arcsec_px: float | None
    width_deg: float | None
    height_deg: float | None


class FilterOnPage(BaseModel):
    """Un filtro posseduto, con la banda che lascia passare."""

    id: int
    name: str
    brand: str | None
    model: str | None
    bands: list[BandOut]
    frames: int | None  # nulli finche' non e' contato (`counted`)
    integration_s: float | None
    untimed: int | None
    nights: int | None
    objects: list[GearObject]
    counted: bool
    mergeable_into: list[int]  # i filtri in cui si puo' unire: solo quelli che la spina accetta


class GearList(BaseModel):
    instruments: list[InstrumentOnPage]
    rigs: list[RigOnPage]
    filters: list[FilterOnPage]
    # Quali campi chiede la scheda di ogni genere, nell'ordine in cui si leggono. Arriva **per
    # genere e non per pezzo** perche' serve anche a scriverne uno di un genere che non possiedi
    # ancora: li' non c'e' nessun pezzo da cui copiarli. Li decide il backend, e la pagina non ne
    # tiene un secondo elenco.
    cards: dict[InstrumentKind, list[CardField]]


class InstrumentNew(InstrumentCardIn):
    """Un pezzo che scrivi tu. Genere e nome sono cio' che lo fa esistere -- un pezzo e' il suo
    nome dentro il suo genere -- e la scheda arriva con lui: creare e poi correggere sarebbero due
    gesti per una cosa sola, e fra i due il pezzo esisterebbe a meta'."""

    kind: InstrumentKind
    name: str = Field(min_length=1)  # qui e' obbligatorio: senza nome il pezzo non e' nessuno


class GearWritten(BaseModel):
    """Cos'e' successo scrivendo. `requeued` non e' zero quando la risposta cambia il senso di
    qualche posa -- il colore di una camera lo fa -- e allora il lavoro riparte da solo."""

    id: int
    requeued: int
    run_started: bool
