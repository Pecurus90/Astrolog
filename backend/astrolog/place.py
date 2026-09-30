"""Cosa si puo' sapere di un LUOGO dalle sue coordinate: il fuso orario, l'altitudine sul
livello del mare, la luminosita' del suo cielo, e la ricerca del posto per nome.

Vincolo non ovvio: ogni chiamata esterna si passa come argomento (`fetch`), cosi' i test
usano un finto e la suite non tocca internet. Quando il servizio tace, la risposta e' `None`
o un elenco vuoto: **mai un valore inventato, mai uno zero di ripiego** -- zero e' il livello
del mare, ed e' un'altitudine vera. Il fuso invece non chiede niente a nessuno: lavora sui
confini veri, offline, e quindi funziona anche in un sito buio senza rete.
"""

import math
import threading
import time
import urllib.parse
import zoneinfo

from tzfpy import get_tz

from . import net
from .units import believable_sqm, sqm_from_brightness, sqm_of_bortle

# Un grado di latitudine sono 111,2 km (il meridiano diviso 360): la costante e' quella,
# non una misura del posto.
_KM_PER_DEGREE = 111.2

# I servizi, uno per riga, con cosa danno e a quali condizioni.
# - l'altitudine: modello di terreno Copernicus a 90 m, libero, senza chiave, da citare
# - il cielo: la luminosita' artificiale allo zenit del World Atlas, chiave personale
#   gratuita (500 richieste al giorno), da citare
ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"
SKY_URL = "https://www.lightpollutionmap.info/QueryRaster/"
SEARCH_URL = "https://nominatim.openstreetmap.org/search"

# La policy del servizio di ricerca concede una richiesta al secondo. Il freno sta qui e non
# nella rotta perche' e' una condizione d'uso del servizio, non una scelta dell'interfaccia:
# vale per chiunque chiami, oggi la rotta, domani il campo che cerca mentre si scrive.
SEARCH_MIN_INTERVAL_S = 1.0
_search_lock = threading.Lock()
_last_search = 0.0

_ZONES = None


# `_fetch` resta un nome di questo modulo perche' i test lo sostituiscono qui: la chiamata vera
# sta in `net`, una casa sola per il luogo e per il meteo.
_fetch = net.fetch


def _ask(fetch, url):
    """Chiede, e se qualcosa va storto torna None: un servizio che non risponde non deve mai
    diventare un errore in faccia a chi sta creando un luogo."""
    return net.ask(fetch or _fetch, url)


def valid_timezone(name):
    """Il nome e' un fuso vero? Si guarda se e' NELL'ELENCO, non si prova ad aprirlo:
    "Europe" (una cartella del database dei fusi) e "Europe/Roma" (un nome inventato)
    falliscono con eccezioni diverse, e una guardia che le insegue le sbaglia."""
    global _ZONES  # noqa: PLW0603 - l'elenco si legge una volta sola: e' un file su disco
    if _ZONES is None:
        _ZONES = zoneinfo.available_timezones()
    return bool(name) and name in _ZONES


def distance_km(lat_a, lon_a, lat_b, lon_b):
    """Quanto distano due punti, in chilometri. `None` se una delle due coppie non c'e'.

    E' la formula piana, non quella sferica: serve a decidere se due coordinate sono **lo
    stesso posto** (sotto il chilometro) o un altro, e a quelle distanze la differenza fra le
    due formule e' di metri. Su scala continentale sbaglierebbe, e infatti nessuno la usa
    cosi'."""
    if None in (lat_a, lon_a, lat_b, lon_b):
        return None
    nord = (lat_a - lat_b) * _KM_PER_DEGREE
    est = (lon_a - lon_b) * _KM_PER_DEGREE * math.cos(math.radians((lat_a + lat_b) / 2))
    return math.hypot(nord, est)


def by_distance(latitude, longitude, sites):
    """I luoghi dal piu' vicino a quelle coordinate, ognuno con la sua distanza: `[(km, luogo)]`.
    Chi non ha coordinate resta fuori, perche' non si saprebbe dove metterlo. Si ordina sulla
    distanza VERA: gli arrotondati a schermo farebbero pareggiare due luoghi vicini, e a parita'
    confrontare le righe del database solleverebbe invece di ordinare."""
    misurati = []
    for site in sites:
        km = distance_km(latitude, longitude, site["latitude"], site["longitude"])
        if km is not None:
            misurati.append((km, site))
    return sorted(misurati, key=lambda coppia: coppia[0])


def coordinates_key(latitude, longitude):
    """La chiave stabile di un POSTO, dalle coordinate: `"45.60,11.67"`. `None` se non ci sono.

    Due decimali, cioe' circa un chilometro: e' la stessa scala della tolleranza con cui si
    decide se due coordinate sono lo stesso posto, e sotto quella la differenza e' in come la
    coordinata e' scritta. Puo' capitare che due pose a poche centinaia di metri cadano ai due
    lati di un confine e diventino due domande invece di una: si risponde due volte, non si
    perde niente."""
    if latitude is None or longitude is None:
        return None
    # `+ 0.0` non toglie il meno a uno zero negativo, e "-0.00" sarebbe una chiave diversa da
    # "0.00" per lo stesso punto: si normalizza guardando il numero, non la stringa.
    lat = 0.0 if abs(latitude) < 0.005 else latitude
    lon = 0.0 if abs(longitude) < 0.005 else longitude
    return f"{lat:.2f},{lon:.2f}"


def timezone_of_frame(latitude, longitude, home_tz):
    """Il fuso della notte di un frame: quello delle coordinate dell'header, se ne danno uno, o
    quello di casa (`None`, cioe' UTC, senza casa). La chiedono la scansione, quando il frame entra,
    e chi riscrive la notte quando casa cambia fuso (`spine/home_nights.py`)."""
    return timezone_of(latitude, longitude) or home_tz


def timezone_of(latitude, longitude):
    """Il fuso IANA del luogo, dai confini veri e senza rete. `None` se le coordinate non
    ci sono o non cadono in nessun fuso."""
    if latitude is None or longitude is None:
        return None
    name = get_tz(longitude, latitude)  # la libreria vuole (longitudine, latitudine)
    return name if valid_timezone(name) else None


def elevation_of(latitude, longitude, *, fetch=None):
    """L'altitudine sul livello del mare, in metri, o `None` se non si e' potuta sapere."""
    if latitude is None or longitude is None:
        return None
    query = urllib.parse.urlencode({"latitude": latitude, "longitude": longitude})
    data = _ask(fetch, f"{ELEVATION_URL}?{query}")
    values = data.get("elevation") if isinstance(data, dict) else None
    if not values or values[0] is None:
        return None
    try:
        return float(values[0])
    except (TypeError, ValueError):
        return None


def sky_sqm_of(latitude, longitude, key, *, fetch=None):
    """La luminosita' del cielo del luogo, in magnitudini per arcosecondo quadrato.

    Il servizio da' la luce ARTIFICIALE allo zenit in millicandele per metro quadro: la
    conversione (col fondo naturale sommato) sta in `units`, una casa sola. Senza chiave non
    si chiede niente a nessuno: l'app funziona lo stesso, il cielo si misura o si sceglie."""
    if not key or latitude is None or longitude is None:
        return None
    query = urllib.parse.urlencode(
        {"ql": "wa_2015", "qt": "point", "qd": f"{longitude},{latitude}", "key": key}
    )
    data = _ask(fetch, f"{SKY_URL}?{query}")
    if not isinstance(data, str | int | float):
        return None  # il servizio risponde un numero e basta: qualunque altra cosa e' un guasto
    try:
        artificial = float(data)
    except ValueError:
        return None
    return believable_sqm(sqm_from_brightness(artificial))


def elevation_from(latitude, longitude, *, declared=None, fetch=None):
    """L'altitudine del luogo e **come la si sa**: scritta da chi c'e' stato, o chiesta al
    servizio. `(None, None)` se non si e' saputa: due campi vuoti insieme, mai un'altitudine
    senza la sua provenienza -- senza, un numero vecchio rimasto attaccato a coordinate nuove
    sarebbe indistinguibile da una misura."""
    if declared is not None:
        return declared, "declared"
    asked = elevation_of(latitude, longitude, fetch=fetch)
    return (asked, "service") if asked is not None else (None, None)


def sky_of(latitude, longitude, *, sqm=None, bortle=None, key=None, fetch=None):  # noqa: PLR0913
    """La luminosita' del cielo del luogo e **come la si sa**, dalle tre strade in ordine di
    fiducia: misurata con lo strumento, scelta sulla scala, chiesta al servizio.

    La misura vince perche' e' un fatto; la scala viene prima del servizio perche' chi la
    sceglie sta guardando quel cielo, mentre il servizio guarda una mappa del 2015. Quando
    nessuna strada da' niente si torna `(None, None)`: due campi vuoti insieme, mai un numero
    senza la sua provenienza."""
    if sqm is not None:
        return sqm, "measured"
    if bortle is not None:
        return sqm_of_bortle(bortle), "scale"
    asked = sky_sqm_of(latitude, longitude, key, fetch=fetch)
    return (asked, "service") if asked is not None else (None, None)


def _wait_turn(now, sleep):
    """Aspetta il proprio turno se l'ultima ricerca e' troppo fresca. L'orologio e l'attesa si
    passano da fuori: un test non deve fermarsi un secondo per provare una regola."""
    global _last_search  # noqa: PLW0603 - l'istante dell'ultima chiamata e' uno per processo
    with _search_lock:
        since = now() - _last_search
        if _last_search and since < SEARCH_MIN_INTERVAL_S:
            sleep(SEARCH_MIN_INTERVAL_S - since)
        _last_search = now()


def search(name, *, fetch=None, limit=5, now=time.monotonic, sleep=time.sleep):
    """I posti che portano quel nome, col loro nome per esteso e le coordinate. Elenco vuoto
    se non si trova niente o se il servizio non risponde: la strada manuale resta aperta."""
    if not name or not name.strip():
        return []
    _wait_turn(now, sleep)
    query = urllib.parse.urlencode({"q": name.strip(), "format": "jsonv2", "limit": limit})
    data = _ask(fetch, f"{SEARCH_URL}?{query}")
    if not isinstance(data, list):
        return []
    out = []
    for row in data:
        if not isinstance(row, dict) or not row.get("display_name"):
            continue
        try:
            latitude, longitude = float(row["lat"]), float(row["lon"])
        except (KeyError, TypeError, ValueError):
            continue  # un posto senza coordinate leggibili non e' un posto: si salta
        out.append({"name": row["display_name"], "latitude": latitude, "longitude": longitude})
    return out
