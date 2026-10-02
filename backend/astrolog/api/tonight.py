"""Cosa fa il cielo stanotte dal sito di casa: la Luna, e dov'e' il buio.

Vincoli non ovvi:

* **La notte e' quella dell'app**, da mezzogiorno a mezzogiorno nel fuso del sito
  (`astrolog.clock.night_date`), non una giornata di calendario: chi guarda alle due di notte
  sta ancora nella notte di ieri, e vuole la luna di ieri. E la finestra si misura **fra i due
  mezzogiorni veri**, non a ventiquattro ore fisse: la notte del cambio d'ora ne dura 23 o 25.
* **La fase si chiede a meta' notte**, non a mezzogiorno. La Luna cambia il 6% al giorno: chiesta
  all'inizio della finestra, chi guarda la barra alle undici di sera legge il numero di dodici ore
  prima -- misurato, 48% contro 54% sulla stessa notte.
* **Senza sito di casa non c'e' niente da dire**, e si dice: `site` assente e `moon` assente. Una
  luna calcolata su un posto inventato sarebbe un numero che sembra vero. Il sito, quando c'e',
  **viaggia col suo cielo**: il piede della barra scrive il posto e la sua classe in una riga
  sola, e chiederli a due rotte sarebbe un momento in cui la pagina e' a meta'.
* **Il conto costa**, perche' campiona una notte di cielo **due volte**, una per corpo: 140 ms la
  Luna e 53 il Sole, contro i 2 ms di una rotta che legge e basta (misurato il 20/9/2026). I due
  campionamenti non si sommano per distrazione: sono due corpi diversi, e la griglia -- che e'
  gratis -- e' l'unica cosa che si rifa'. La risposta porta la notte a cui si riferisce, cosi' chi
  la mostra sa quando e' scaduta senza richiederla a ogni respiro.
* **Le effemeridi si importano in testa**, non dentro la rotta. Erano pigre "per non far
  aspettare l'avvio", e misurando quella ragione era falsa: l'app ci mette 531 ms e le effemeridi
  ne aggiungono **uno**, perche' astropy entra comunque con la spina. Peggio: il loro import e'
  cio' che disinnesca la rete di astropy, quindi finche' nessuno apriva questa rotta il processo
  girava **col download armato** -- e "offline sempre" era vero per le effemeridi, non per l'app.
"""

import sqlite3
from typing import cast

from fastapi import APIRouter, Depends

from ..clock import midnight_of, night_date, night_window, now_iso
from ..ephemeris import moon, sun
from ..spine.group_store import home_site
from ..units import bortle_of
from . import weather
from .deps import get_db
from .models_tonight import MoonOut, SiteSkyOut, SkyBandOut, SkyPointOut, TonightOut

router = APIRouter(prefix="/api/v1", tags=["stanotte"])


def _iso(istante):
    """Un istante in ISO, o `None` se non c'e'.

    Il nome non e' `_quando`: `ephemeris/moon.py` ha gia' un `_quando`, che fa un'altra cosa
    (porta un istante in `Time` di astropy e **solleva** se non ha fuso). Due significati sotto lo
    stesso nome a due import di distanza sono una trappola per chi legge."""
    return istante.isoformat() if istante else None


def _sito(riga):
    """Il sito come lo scrive il piede della barra: il nome e il cielo che ha.

    La classe di Bortle **non si ricalcola qui**: la conversione da luminosita' a classe vive in
    `astrolog.units` e la usa anche la scheda del luogo. Due conti uguali in due posti sono due
    conti che un giorno diranno cose diverse: le due famiglie di conversione che girano, sullo
    stesso cielo, differiscono fino a due classi."""
    return SiteSkyOut(name=riga["name"], sky_sqm=riga["sky_sqm"], bortle=bortle_of(riga["sky_sqm"]))


def _fascia(fascia):
    """Una fascia del cielo come la legge chi disegna: i due istanti scritti, e quale cielo e'."""
    return SkyBandOut(
        starts_at=fascia["starts_at"].isoformat(),
        ends_at=fascia["ends_at"].isoformat(),
        kind=fascia["kind"],
    )


def _sky_point(punto):
    """Un punto del cielo come lo legge chi disegna: l'istante scritto, l'altezza com'e'."""
    return SkyPointOut(at=punto["at"].isoformat(), altitude_deg=punto["altitude_deg"])


@router.get("/tonight", response_model=TonightOut)
def tonight(conn: sqlite3.Connection = Depends(get_db)):
    """Che luna fa stanotte dal sito di casa."""
    riga = home_site(conn)
    if riga is None:
        return TonightOut(night=None, site=None, moon=None)
    sito = dict(riga)

    notte = night_date(now_iso(), sito["timezone"])
    # La fase si chiede alla **mezzanotte** di quella notte, e l'istante lo compone `clock`: e' lo
    # stesso che usa la pagina Notti, o due schermi dello stesso archivio chiederebbero la stessa
    # notte a due momenti diversi.
    mezzanotte = midnight_of(notte, sito["timezone"]) if notte else None
    if mezzanotte is None:
        # Due casi in una riga sola, e tutti e due veri: un fuso salvato che il sistema non
        # conosce piu' (il database dei fusi cambia), e un sito **senza** fuso -- coordinate in
        # mare aperto, o `tzdata` vecchio sul NAS. Si esce di qui, perche' un attimo dopo il conto
        # solleverebbe e la rotta diventerebbe un 500; e non si ripiega su Greenwich, che darebbe
        # la luna giusta di un altro posto senza che nessuno se ne accorga. Il sito, senza la sua
        # notte e senza la sua luna, si legge lo stesso.
        return TonightOut(night=None, site=_sito(sito), moon=None)
    # A midnight exists only for a night.
    comincia, quante_ore = night_window(cast("str", notte), sito["timezone"])

    fase = moon.phase(mezzanotte)
    cielo = moon.night_track(comincia, sito["latitude"], sito["longitude"], hours=quante_ore)
    return TonightOut(
        night=notte,
        site=_sito(sito),
        weather=weather.brief_of(conn, sito["id"], notte),
        sky_bands=[
            _fascia(f)
            for f in sun.night_bands(
                comincia, sito["latitude"], sito["longitude"], hours=quante_ore
            )
        ],
        moon=MoonOut(
            phase_key=fase["phase_key"],
            illumination_pct=fase["illumination_pct"],
            rise=_iso(cielo["rise"]),
            set=_iso(cielo["set"]),
            highest=_sky_point(cielo["highest"]),
            track=[_sky_point(p) for p in cielo["track"]],
            ceiling_deg=moon.sky_ceiling(sito["latitude"]),
            lit_side=moon.lit_side(fase["phase_key"], sito["latitude"]),
        ),
    )
