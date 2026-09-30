"""Il tempo nella grafia del DB: l'istante corrente e la notte a cui un istante appartiene. Una
casa sola, usata da spina, worker e rotte: due grafie sarebbero due ordini -- e la data della
notte, nel progetto di prima, viveva in due case che si contraddicevano.

Vincolo non ovvio: `DATE-OBS` e' UTC, come dice lo standard FITS (accordo IAU-FWG sulle date,
<https://fits.gsfc.nasa.gov/year2000.html>, 4.4) -- l'app non lo corregge con `DATE-LOC`
(Marco, 23/9/2026).
"""

import zoneinfo
from datetime import UTC, datetime, time, timedelta


def iso_z(instant):
    """Un istante con fuso nella grafia del DB: UTC, al millesimo, con la Z."""
    return instant.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def now_iso():
    return iso_z(datetime.now(UTC))


def parse_iso(instant_iso):
    """L'istante ISO come `datetime`, col fuso se lo porta, o `None` se non e' una data."""
    if not instant_iso:
        return None
    try:
        return datetime.fromisoformat(str(instant_iso).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def elapsed_s(started_iso, ended_iso):
    """Quanto e' durata una cosa che ha un inizio e una fine, in **secondi**, o `None`.

    Il database tiene i due istanti e non la differenza: calcolarla a schermo andrebbe contro la
    regola che il backend manda cio' che lo schermo mostra. Secondi e non minuti perche' una
    lettura di prova dura tre secondi, e zero minuti direbbe che non e' successo niente.

    `None` vuol dire **non lo so**, mai zero: una corsa ancora aperta non ha una fine, e una fine
    prima dell'inizio -- un orologio spostato a meta' corsa -- darebbe un numero negativo, che a
    schermo e' peggio di un vuoto."""
    inizio, fine = parse_iso(started_iso), parse_iso(ended_iso)
    if inizio is None or fine is None:
        return None
    secondi = (fine - inizio).total_seconds()
    return secondi if secondi >= 0 else None


# La notte della posa, in SQL, per chi la vuole dentro una `GROUP BY`: la colonna che `scan` scrive
# con `night_date` nel fuso del posto (`spine/scan.py`, `night_of`). La importano le
# domande per notte, e un test la tiene incollata a `night_date` (`test_foundations.py`).
NIGHT_SQL = "f.local_night"


def night_date(instant_iso, tz_name=None):
    """La notte a cui appartiene un istante: da mezzogiorno a mezzogiorno **nel fuso dato**,
    come `YYYY-MM-DD`. `None` se la data non si legge o il fuso non esiste.

    Il fuso e' quello del sito, e conta davvero: lo stesso istante cade in due notti diverse a
    Roma e in Arizona. Senza fuso si legge in UTC, l'unico fuso che il file sa."""
    quando = _in_zone(instant_iso, tz_name)
    # La sottrazione su un istante con fuso lavora sull'orologio da parete, che e' cio' che
    # serve: mezzogiorno locale, non mezzogiorno UTC spostato.
    return None if quando is None else (quando - timedelta(hours=12)).date().isoformat()


def night_instant(date_obs, mtime):
    """L'istante da cui viene la notte di un frame: il suo `DATE-OBS`, o senza l'istante in cui il
    file e' stato scritto (Marco, 27/9/2026)."""
    return date_obs or datetime.fromtimestamp(mtime, UTC).isoformat()


def local_iso(instant_iso, tz_name=None):
    """Un istante come si legge nel fuso dato, ISO col suo scarto (`2026-03-14T20:30:00+09:00`); in
    UTC senza fuso. `None` se l'istante non si legge o il fuso non esiste. La pagina lo taglia e
    basta (`oraDelSito`): il fuso lo sceglie chi scrive."""
    quando = _in_zone(instant_iso, tz_name or "UTC")
    return None if quando is None else quando.isoformat(timespec="seconds")


def _in_zone(instant_iso, tz_name):
    """L'istante nel fuso dato, o com'e' scritto se il fuso non c'e' (senza scarto e' UTC:
    `DATE-OBS` senza fuso e' UTC per standard). `None` se non si legge o il fuso non esiste."""
    quando = parse_iso(instant_iso)
    if quando is None:
        return None
    if quando.tzinfo is None:
        quando = quando.replace(tzinfo=UTC)
    if not tz_name:
        return quando
    try:
        return quando.astimezone(zoneinfo.ZoneInfo(tz_name))
    except (zoneinfo.ZoneInfoNotFoundError, ValueError):
        return None


def midnight_of(night_date_str, tz_name):
    """La **mezzanotte** di una notte, come istante con fuso: il mezzo della sua finestra.

    E' l'inversa di `night_date` -- `night_date(midnight_of(d, tz), tz)` torna `d`, e un test lo
    tiene -- e cade il **giorno dopo** quello che da' il nome alla notte: la notte del 18 va dalle
    12 del 18 alle 12 del 19. Serve a chi chiede al cielo com'era quella notte: la Luna cambia
    mentre passa, e un istante va scelto. **Non** e' il mezzo esatto della finestra, che nella
    notte del cambio d'ora cade mezz'ora prima o dopo: e' la mezzanotte, che si spiega in una
    parola e non dipende da quanto dura quella notte.

    `None` se la data non si legge o il fuso non si riconosce: senza fuso l'istante sarebbe
    quello di Greenwich, cioe' il cielo di un altro posto."""
    if not tz_name:
        return None
    try:
        giorno = datetime.strptime(night_date_str, "%Y-%m-%d").date()  # noqa: DTZ007 - una data, non un istante
        fuso = zoneinfo.ZoneInfo(tz_name)
    except (TypeError, ValueError, zoneinfo.ZoneInfoNotFoundError):
        return None
    # Dove il cambio d'ora cade a mezzanotte (Santiago, L'Avana) quell'ora locale non esiste:
    # `zoneinfo` non solleva e risolve con lo scarto di prima, che e' un istante di quella notte --
    # ed e' cio' che serve.
    return datetime.combine(giorno + timedelta(days=1), time(0), tzinfo=fuso)


# Da che ora si guarda una notte: mezzogiorno del suo giorno, nel fuso del sito.
_ORA_DI_INIZIO = 12


def night_window(night_date_str, tz_name):
    """(quando comincia la notte, quante ore **vere** dura): da mezzogiorno a mezzogiorno nel fuso
    del sito, e in UTC senza fuso.

    I due mezzogiorni si costruiscono e la durata si misura fra loro: la notte del cambio d'ora
    dura 23 ore in primavera e 25 in autunno. **La differenza si prende in UTC**: sottrarre due
    istanti con un fuso vero da' la differenza sull'orologio a muro, 24 ore tonde anche la notte
    in cui le lancette saltano."""
    fuso = zoneinfo.ZoneInfo(tz_name) if tz_name else UTC
    giorno = datetime.strptime(night_date_str, "%Y-%m-%d").date()  # noqa: DTZ007 - una data, non un istante
    comincia = datetime.combine(giorno, time(_ORA_DI_INIZIO), tzinfo=fuso)
    finisce = datetime.combine(giorno + timedelta(days=1), time(_ORA_DI_INIZIO), tzinfo=fuso)
    quante = (finisce.astimezone(UTC) - comincia.astimezone(UTC)).total_seconds() / 3600
    return comincia, quante
