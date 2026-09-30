"""La forma delle risposte e delle richieste del **luogo da cui si osserva e del primo
avvio**: il sito, le preferenze che il wizard scrive, e cio' che manca per fare le notti.

Vale la convenzione di `models.py`: "non so" e' un campo con codice, mai un null muto; i nomi
vengono dal glossario. Un file per dominio: la spina, Da confermare, il sito.

Vincolo non ovvio: `bortle` esce ma non entra mai nel database -- e' derivato dalla
luminosita' e viaggia sempre accanto a lei. In creazione e' invece una scorciatoia d'ingresso
(chi il cielo lo sceglie invece di misurarlo) che si converte subito in una luminosita'.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

from ..units import SQM_MAX, SQM_MIN
from .models_page import Page

# Come si sa la luminosita' del cielo di un luogo, in ordine di fiducia.
SkySource = Literal["measured", "service", "scale"]

# Come si sa l'altitudine: scritta da chi c'e' stato, o chiesta al servizio. Serve per la
# stessa ragione di `sky_source`: spostando il luogo si rifa' solo cio' che veniva dalle
# coordinate, e cio' che l'utente ha scritto resta sua parola.
ElevationSource = Literal["declared", "service"]

# Cosa manca all'app per fare il suo mestiere: un elenco chiuso di motivi, non frasi.
Missing = Literal["no_active_site", "no_solver", "no_star_database"]

# Da quale canale arriva l'eseguibile del riconoscitore. Chiuso come `Missing`, e per la stessa
# ragione: si mostra a schermo, e una parola nuova ci arriverebbe non tradotta.
SolverSource = Literal["declared", "env", "path", "known_place"]

# Cosa di un luogo non si e' potuto sapere, e percio' e' vuoto. La pagina scrive "non
# fornita" e sa perche': un null da solo non distingue "non lo so" da "non l'ho chiesto".
Unknown = Literal["site_no_timezone", "site_no_elevation", "site_no_sky"]


class SiteOut(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    elevation_m: float | None  # None = non fornita: lo zero e' il livello del mare, ed e' vero
    elevation_source: ElevationSource | None
    timezone: str | None  # None dove le coordinate non cadono in nessun fuso (mare aperto)
    sky_sqm: float | None
    sky_source: SkySource | None
    bortle: int | None  # DERIVATO: non e' una colonna, e non compare mai senza la misura
    is_default: bool
    nights: int  # quante notti lo tengono: chi cancella lo sa prima di provarci
    unknown: list[Unknown]  # i campi vuoti, col loro motivo


class SiteList(Page[SiteOut]):
    pass


class SiteCreate(BaseModel):
    name: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    # Se non lo dai, l'app lo chiede al servizio; se lo dai, vince il tuo.
    elevation_m: float | None = None
    sky_sqm: float | None = Field(None, ge=SQM_MIN, le=SQM_MAX)
    bortle: int | None = Field(None, ge=1, le=9)
    is_default: bool = False


class SiteEdit(BaseModel):
    """Cio' che si cambia di un luogo. Un campo assente resta com'e'; le coordinate cambiate
    rifanno il fuso, perche' un fuso vecchio su coordinate nuove e' un errore silenzioso."""

    name: str | None = Field(None, min_length=1)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    elevation_m: float | None = None
    sky_sqm: float | None = Field(None, ge=SQM_MIN, le=SQM_MAX)
    bortle: int | None = Field(None, ge=1, le=9)


class SiteDeleted(BaseModel):
    site_id: int
    deleted: bool


class PlaceOut(BaseModel):
    """Un posto trovato per nome. Non e' un luogo dell'archivio: e' un candidato, e diventa un
    luogo solo quando l'utente lo crea."""

    name: str
    latitude: float
    longitude: float


class PlaceList(BaseModel):
    """La ricerca e' un GESTO, non un elenco dell'archivio: niente pagine, al piu' una
    manciata di candidati che il servizio ha proposto."""

    items: list[PlaceOut]


class SettingsOut(BaseModel):
    values: dict[str, str | None]
    wizard_done: bool  # il timbro c'e': un fatto scritto, non "sembra vuoto"
    missing: list[Missing]


class SolverOut(BaseModel):
    """Dove l'app prende il riconoscitore, e **da cosa** l'ha dedotto.

    Il canale accompagna sempre il percorso perche' "trovato" da solo non si puo' smentire: la
    ricerca automatica sbaglia proprio quando trova qualcosa -- un ASTAP vecchio rimasto nel
    PATH, o quello di un altro utente in un posto noto -- e chi guarda deve poter dire "no, non
    quello" senza indovinare quale dei quattro canali ha risposto."""

    path: str | None  # None = non trovato: il canale e' None insieme a lui, mai da solo
    source: SolverSource | None
    # Cio' che l'utente ha scritto, **anche quando non porta a niente**: senza, un percorso
    # sbagliato sparirebbe dalla schermata e non ci sarebbe niente da correggere.
    declared: str | None
    # I cataloghi stellari trovati accanto al programma, per nome (`d80`, `v50`). Vuoto **con** un
    # percorso vuol dire che ASTAP parte e non riconosce niente; vuoto **senza** percorso vuol dire
    # soltanto che ASTAP non c'e'.
    databases: list[str]


class SettingsPatch(BaseModel):
    """Una scrittura o passa intera o non passa: meta' preferenze scritte sarebbe peggio.

    I valori entrano come sono: il tipo di ogni chiave lo giudica `db/config.py`, che e' dove
    l'elenco chiuso vive. Dichiararlo anche qui vorrebbe dire scriverlo due volte."""

    values: dict[str, Any]
