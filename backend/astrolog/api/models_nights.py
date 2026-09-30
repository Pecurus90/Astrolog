"""La forma di cio' che la pagina **Notti** mostra: le notti, gia' pronte per lo schermo.

Vincolo non ovvio: qui non c'e' niente da ricalcolare. Le ore sono gia' sommate senza le copie
riscritte, i nomi degli oggetti sono gia' risolti, e i filtri arrivano **in ordine di tempo
dato**, che e' l'ordine con cui la pagina li mostra. Cio' che non c'e' ancora -- la Luna, il
meteo, le misure delle pose -- non ha un campo vuoto qui: nasce col suo pezzo
(`docs/domini/notti.md`).
"""

from typing import Literal

from pydantic import BaseModel, Field

from .models_page import Page
from .models_tonight import PhaseKey
from .models_weather import WeatherSkyOut


class NightObject(BaseModel):
    """Un oggetto ripreso in quella notte."""

    key: str  # la chiave stabile, la stessa dell'Archivio
    name: str | None
    frames: int
    integration_s: float


class FilterUsed(BaseModel):
    """Un filtro con cui hai ripreso qualcosa, col tempo che gli e' stato dato.

    Nasce qui, dove l'hanno chiesto per primo le Notti, e lo riusa l'Archivio: la casa che li
    conta e' una sola (`spine/filters_used.py`), e due forme direbbero due volte lo stesso fatto."""

    name: str  # il nome che gli hai dato tu, o quello che i file portavano
    passband: str  # la banda canonica (`vocab/filters`): e' lei a dare il colore
    frames: int
    integration_s: float


class MoonThatNight(BaseModel):
    """Che luna c'era: la fase e quanto era illuminata. **Calcolata**, non conservata."""

    # Le otto fasi sono **quelle della rotta di stanotte**, non un secondo elenco: e' la stessa
    # Luna, e chi la mostra ha un dizionario solo per i suoi nomi.
    phase_key: PhaseKey
    # Lo stesso vincolo della rotta di stanotte: e' la stessa grandezza, e due forme in OpenAPI
    # per lo stesso fatto sono due contratti da tenere d'accordo.
    illumination_pct: int = Field(ge=0, le=100)


class NightWeather(WeatherSkyOut):
    """Il meteo vero di quella notte, dall'archivio: `ok` col suo cielo; `waiting` finche' non e'
    arrivato (una notte giovane aspetta la rianalisi); `unknown` se il fuso del sito non si
    riconosce."""

    state: Literal["ok", "waiting", "unknown"]


class Night(BaseModel):
    """Una riga: **una notte**, con dentro cosa ci hai fatto."""

    id: int  # con cui chiamarla: il modale che nascera' ha gia' come chiedere questa notte
    night_date: str  # la data della notte, nel fuso del sito; a schermo si legge come data
    site: str  # da dove: due siti nella stessa data sono due notti, e la riga lo deve dire
    site_source: str  # `declared` se l'hai detto tu, `detected` se lo ha ricavato l'app
    frames: int  # quante pose, copie riscritte escluse
    integration_s: float  # la somma del tempo delle pose, in secondi
    untimed: int  # quante non dicono quanto sono durate: non valgono zero
    objects: list[NightObject]
    filters: list[FilterUsed]
    # Nulla quando il fuso del sito non si riconosce: senza fuso non c'e' una mezzanotte, e la
    # riga tace invece di descrivere il cielo di un altro posto.
    moon: MoonThatNight | None
    weather: NightWeather


class ArchiveTotals(BaseModel):
    """Cosa tiene l'archivio intero: non dipende da quante righe si stanno guardando."""

    nights: int
    frames: int
    integration_s: float
    untimed: int


class WaitingPoses(BaseModel):
    """Pose che nessuna notte ha raccolto, raggruppate per **dove si risponde**: una domanda di
    *Da confermare* (`review`), il sito da dichiarare (`site`), o niente (`never`) -- che e' il
    caso di una posa senza data, a cui nessuna risposta puo' rimediare."""

    answer_at: Literal["review", "site", "never"]
    frames: int


class NightList(Page[Night]):
    totals: ArchiveTotals
    waiting: list[WaitingPoses]
    still_reading: int  # quante pose la spina ha ancora da lavorare: lavoro, non una domanda
