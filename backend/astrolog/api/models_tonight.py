"""La forma di cio' che l'app dice sul cielo di stanotte.

Vincolo non ovvio: **ogni campo puo' mancare, e mancare vuol dire una cosa precisa**. Senza sito
di casa non c'e' notte e non c'e' luna; una luna che non sorge nelle ventiquattro ore non ha
un'ora. Sono le **tre forme del dato** del design system -- piena, vuota, ignota -- portate in un
modello: chi le mostra scrive una frase, non uno zero.
"""

from typing import Literal

from pydantic import BaseModel, Field

from .models_weather import WeatherBriefOut

# Le otto fasi. Ripetute qui e non importate da `ephemeris`: questo modulo descrive il
# **contratto della rotta**, e un contratto che cambia forma perche' e' cambiato un modulo
# interno sarebbe un contratto che non si puo' leggere. Che i due elenchi coincidano lo prova
# `tests/test_api_tonight.py`.
PhaseKey = Literal[
    "new",
    "waxing_crescent",
    "first_quarter",
    "waxing_gibbous",
    "full",
    "waning_gibbous",
    "last_quarter",
    "waning_crescent",
]


class SkyPointOut(BaseModel):
    """Un istante della notte e quanto era alta la Luna, in gradi sull'orizzonte.

    L'altezza e' **negativa sotto l'orizzonte**, e non si taglia a zero: e' cio' che permette di
    disegnare dove la Luna entra ed esce invece di una curva che si appoggia al bordo.
    """

    at: str
    altitude_deg: float


class MoonOut(BaseModel):
    phase_key: PhaseKey
    illumination_pct: int = Field(ge=0, le=100)
    # Istanti con il loro fuso, in ISO. `None` quando l'attraversamento non c'e' nella notte:
    # sopra il circolo polare capita, e li' un'ora scritta sarebbe inventata.
    rise: str | None
    set: str | None
    # Da che parte si vede il lembo illuminato, **da questo sito**: dipende dalla fase e
    # dall'emisfero, perche' una crescente e' illuminata a destra da noi e a sinistra in
    # Australia. Lo dice il backend, che conosce tutti e due: farlo dedurre a chi disegna
    # vorrebbe dire un conto nel layout, e mezzo mondo con la Luna specchiata.
    lit_side: Literal["left", "right"]
    # Il punto piu' alto della notte. **Non e' mai assente**, nemmeno quando non ci sono orari:
    # una Luna che non sorge sale lo stesso, sotto l'orizzonte, e quanto poco sale e' la risposta.
    highest: SkyPointOut
    # La curva dell'altezza lungo la notte, per chi la disegna. Il primo e l'ultimo punto sono i
    # due estremi della notte: un grafico che chiudesse prima perderebbe l'ultima mezz'ora.
    track: list[SkyPointOut]
    # Quanto in alto la Luna puo' arrivare **da questo sito**, mai di piu': e' il bordo alto del
    # grafico. Dipende dalla latitudine e non dalla notte, quindi la scala non cambia mai nello
    # stesso posto e due notti si confrontano a occhio. Arriva gia' salito al multiplo di quindici
    # perche' e' il numero che va sulla tacca: farlo salire a schermo sarebbe un conto nel layout.
    ceiling_deg: int = Field(gt=0, le=90)


class SiteSkyOut(BaseModel):
    """Da dove si osserva, e che cielo ha: il piede della barra lo scrive in una riga sola.

    **I due campi del cielo vanno insieme, e insieme possono mancare.** La classe non e' una
    colonna del database: nasce dalla luminosita' (`astrolog.units.bortle_of`), quindi senza la
    misura non c'e' classe -- ed e' lo stato di chi ha saltato quella domanda al primo avvio, non
    un guasto. Chi lo mostra scrive "classe non dichiarata", non uno zero.
    """

    name: str
    sky_sqm: float | None
    bortle: int | None


class SkyBandOut(BaseModel):
    """Un pezzo di notte in cui il cielo e' sempre la stessa cosa: da quando a quando, e quale.

    Perche' escano **gia' divise** invece che come otto orari lo dice `docs/domini/effemeridi.md`,
    voce *"Le fasce arrivano gia' divise"*."""

    starts_at: str
    ends_at: str
    kind: Literal["day", "civil", "nautical", "astronomical", "dark"]


class TonightOut(BaseModel):
    """La notte a cui si riferisce (`YYYY-MM-DD` nel fuso del sito), il sito, la Luna e il cielo."""

    night: str | None
    site: SiteSkyOut | None
    moon: MoonOut | None
    # Vuoto quando non c'e' una notte da dividere -- nessun sito, o un fuso che non si risolve --
    # per la stessa ragione per cui li' la Luna e' `None`.
    sky_bands: list[SkyBandOut] = []
    # Il meteo della notte in corso dal modello scelto, come la previsione l'ha scritto; `None`
    # finche' la previsione non e' arrivata.
    weather: WeatherBriefOut | None = None
