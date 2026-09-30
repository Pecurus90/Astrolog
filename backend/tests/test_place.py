"""Cosa si puo' sapere di un luogo dalle sue coordinate: il fuso (offline), l'altitudine e la
luminosita' del cielo (dalla rete), e la ricerca del posto per nome.

Vincolo di questi test: **non toccano internet**. Ogni chiamata esterna si passa come
argomento, e qui si passa un finto. Un test che chiamasse un servizio vero fallirebbe il
giorno che il servizio cambia, e non girerebbe su un portatile senza rete.
"""

import re
from pathlib import Path

import pytest

from astrolog import net, place
from conftest import SCARICANO, SuiteInRete


def test_no_test_downloads_unless_it_fakes_the_network():
    """Il recinto della suite (`conftest.py`) ferma lo scaricamento di `place` in ogni file di test,
    prima ancora di cercare il nome del servizio: una prova che chiamasse un servizio vero cade,
    invece di dipendere dalla rete di chi la fa girare."""
    with pytest.raises(SuiteInRete, match="ha chiamato la rete"):
        place._fetch("https://nominatim.openstreetmap.org/search?q=x")


def test_a_download_the_app_would_swallow_still_fails_the_test():
    """Anche uno scaricamento che salta ogni `_fetch` sostituito, e arriva al socket, cade: non si
    perde dentro il `try` largo con cui l'app dice "servizio non raggiungibile". L'indirizzo e'
    uno di documentazione (RFC 5737): nessun nome da risolvere, nessun servizio vero."""
    with pytest.raises(SuiteInRete, match="ha aperto la rete"):
        net.ask_why(net.fetch, "https://203.0.113.1/v1/forecast")


def test_every_module_that_downloads_is_fenced():
    """Il recinto conosce i moduli che scaricano per nome (`conftest.SCARICANO`): l'elenco si
    ricava dai sorgenti, non dal recinto, cosi' un modulo nuovo che scarica non resta fuori."""
    radice = Path(place.__file__).parent
    dai_sorgenti = {
        ".".join(p.relative_to(radice.parent).with_suffix("").parts)
        for p in radice.rglob("*.py")
        if re.search(r"^_fetch = net\.fetch$", p.read_text(encoding="utf-8"), re.MULTILINE)
    }
    assert dai_sorgenti == {m.__name__ for m in SCARICANO}


def fake(payload):
    """Un servizio finto che risponde sempre la stessa cosa, e ricorda cosa gli e' stato chiesto."""
    chiamate = []

    def fetch(url):
        chiamate.append(url)
        if isinstance(payload, Exception):
            raise payload
        return payload

    fetch.calls = chiamate
    return fetch


# --- il fuso: offline, dai confini veri --------------------------------------------------


def test_site_timezone_offline():
    """Il fuso viene dai confini politici, non dalla longitudine: due luoghi vicini possono
    stare in due fusi, e un meridiano darebbe la risposta sbagliata."""
    assert place.timezone_of(45.87, 11.51) == "Europe/Rome"
    assert place.timezone_of(40.71, -74.01) == "America/New_York"
    assert place.timezone_of(-54.80, -68.30) == "America/Argentina/Ushuaia"
    # un fuso di comodo in mezzo all'oceano e' comunque un nome valido
    assert place.timezone_of(30.0, -40.0) == "Etc/GMT+3"
    assert place.timezone_of(None, 11.0) is None and place.timezone_of(45.0, None) is None


@pytest.mark.parametrize(
    "name, ok",
    [
        ("Europe/Rome", True),
        ("America/Argentina/Ushuaia", True),
        ("Etc/GMT+1", True),
        ("UTC", True),
        ("CET", True),
        ("Europe/Roma", False),  # il nome italiano non esiste
        ("Europe", False),  # una cartella del database dei fusi, non un fuso
        ("Rome", False),
        ("Europe/rome", False),  # le maiuscole contano
        ("", False),
        (None, False),
    ],
)
def test_a_timezone_name_is_valid_only_if_it_is_in_the_official_list(name, ok):
    """Si valida per APPARTENENZA all'elenco, non provando ad aprire il nome: "Europe" e
    "Europe/Roma" sono sbagliati in due modi diversi e sollevano eccezioni diverse."""
    assert place.valid_timezone(name) is ok


# --- l'altitudine: dalla rete, o niente --------------------------------------------------


def test_site_elevation_or_nothing():
    """L'altitudine si chiede al servizio; se non risponde resta VUOTA. Zero non e' "non lo
    so": zero e' il livello del mare, ed e' un'altitudine vera."""
    assert place.elevation_of(45.46, 9.19, fetch=fake({"elevation": [147.0]})) == 147.0
    assert place.elevation_of(44.0, 8.9, fetch=fake({"elevation": [0.0]})) == 0.0

    for risposta in (
        {},
        {"elevation": []},
        {"elevation": [None]},
        {"elevation": ["non un numero"]},
        {"altro": 1},
        [],
    ):
        assert place.elevation_of(45.0, 9.0, fetch=fake(risposta)) is None, risposta
    assert place.elevation_of(45.0, 9.0, fetch=fake(TimeoutError("rete assente"))) is None
    assert place.elevation_of(None, 9.0, fetch=fake({"elevation": [1.0]})) is None


def test_the_elevation_request_carries_the_coordinates():
    fetch = fake({"elevation": [12.0]})
    place.elevation_of(45.5, 9.25, fetch=fetch)
    assert "latitude=45.5" in fetch.calls[0] and "longitude=9.25" in fetch.calls[0]


# --- il cielo: dalla rete, con la chiave, o niente ---------------------------------------


def test_the_sky_service_needs_a_key_and_never_invents():
    """Senza chiave non si chiede niente a nessuno; con la chiave, una risposta che non si
    capisce vale come nessuna risposta."""
    assert place.sky_sqm_of(45.87, 11.51, key=None, fetch=fake("1.5")) is None
    assert place.sky_sqm_of(45.87, 11.51, key="", fetch=fake("1.5")) is None

    # il servizio da' la luce artificiale in millicandele: qui diventa una misura del cielo
    misura = place.sky_sqm_of(45.87, 11.51, key="k", fetch=fake("1.0"))
    assert misura == pytest.approx(19.91, abs=0.01)
    assert place.sky_sqm_of(45.87, 11.51, key="k", fetch=fake("0")) == pytest.approx(
        21.98, abs=0.01
    )

    for risposta in ("", "non un numero", None, {"boh": 1}, "-3"):
        assert place.sky_sqm_of(45.87, 11.51, key="k", fetch=fake(risposta)) is None, risposta
    assert place.sky_sqm_of(45.87, 11.51, key="k", fetch=fake(OSError("giu'"))) is None


def test_the_sky_request_carries_the_key_and_the_world_atlas_layer():
    fetch = fake("0.5")
    place.sky_sqm_of(45.87, 11.51, key="segreto", fetch=fetch)
    url = fetch.calls[0]
    assert "wa_2015" in url and "qt=point" in url and "segreto" in url
    # il servizio vuole longitudine e latitudine IN QUEST'ORDINE, nello stesso parametro:
    # scambiarle non darebbe un errore, darebbe il cielo di un altro punto del mondo
    assert "qd=11.51%2C45.87" in url


# --- la ricerca del posto ----------------------------------------------------------------


def test_searching_a_place_gives_name_and_coordinates():
    risposta = [
        {
            "display_name": "Asiago, Vicenza, Veneto, 36012, Italia",
            "lat": "45.9133",
            "lon": "11.5025",
        },
        {"display_name": "Asiago, Alberta, Canada", "lat": "53.5", "lon": "-113.5"},
    ]
    trovati = place.search("Asiago", fetch=fake(risposta))
    assert [p["name"] for p in trovati] == [
        "Asiago, Vicenza, Veneto, 36012, Italia",
        "Asiago, Alberta, Canada",
    ]
    assert trovati[0]["latitude"] == pytest.approx(45.9133)
    assert trovati[0]["longitude"] == pytest.approx(11.5025)


def test_searching_survives_a_service_that_answers_badly():
    """Rete assente, risposta storta, coordinate illeggibili: si torna un elenco vuoto, mai
    un risultato inventato e mai un errore che arriva all'utente."""
    for risposta in ([], {}, "boh", [{"display_name": "x"}], [{"lat": "a", "lon": "b"}]):
        assert place.search("x", fetch=fake(risposta)) == [], risposta
    assert place.search("x", fetch=fake(TimeoutError())) == []
    assert place.search("", fetch=fake([{"display_name": "x", "lat": "1", "lon": "2"}])) == []


def test_the_search_says_who_is_asking(monkeypatch):
    """La policy del servizio pretende che chi chiama si identifichi: senza, blocca. Si prova
    sulla richiesta VERA che parte, non sulla costante: e' `_fetch` che la compone, ed e'
    li' che l'intestazione si potrebbe perdere."""
    visti = {}

    class Risposta:
        def read(self):
            return b"[]"

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    def finta_urlopen(req, timeout=None):
        visti["agent"] = req.get_header("User-agent")
        visti["timeout"] = timeout
        return Risposta()

    monkeypatch.setattr(place, "_fetch", net.fetch)  # lo scaricamento vero, la rete finta
    monkeypatch.setattr(place.urllib.request, "urlopen", finta_urlopen)
    place.search("Asiago")

    assert visti["agent"] == net.USER_AGENT
    assert visti["agent"].startswith("AstroLog/") and "http" in visti["agent"]
    assert visti["timeout"] == net.TIMEOUT_S  # una rete lenta non blocca una pagina per sempre


def test_a_service_that_answers_a_bare_number_is_understood(monkeypatch):
    """Il servizio del cielo non risponde JSON: risponde un numero e basta. Chi legge deve
    tornare il corpo com'e' invece di rompersi sul JSON che non c'e'."""

    class Risposta:
        def read(self):
            return b"0.5"

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    monkeypatch.setattr(place, "_fetch", net.fetch)  # lo scaricamento vero, la rete finta
    monkeypatch.setattr(place.urllib.request, "urlopen", lambda req, timeout=None: Risposta())
    assert place.sky_sqm_of(45.87, 11.51, key="k") == pytest.approx(20.51, abs=0.02)


def test_a_service_that_answers_a_page_instead_of_a_number_is_not_a_sky(monkeypatch):
    """Quando un servizio va giu' risponde spesso una pagina di errore, non JSON e non un
    numero: si legge come testo e vale come nessuna risposta, non come un guasto in faccia."""

    class Pagina:
        def read(self):
            return b"<html><body>503 Service Unavailable</body></html>"

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    monkeypatch.setattr(place, "_fetch", net.fetch)  # lo scaricamento vero, la rete finta
    monkeypatch.setattr(place.urllib.request, "urlopen", lambda req, timeout=None: Pagina())
    assert place.sky_sqm_of(45.87, 11.51, key="k") is None


def test_the_search_waits_its_turn_between_two_calls(monkeypatch):
    """Una richiesta al secondo: e' una condizione d'uso del servizio, e vale per chiunque
    chiami. La prima non aspetta nessuno; la seconda aspetta il tempo che manca."""
    monkeypatch.setattr(place, "SEARCH_MIN_INTERVAL_S", 1.0)
    monkeypatch.setattr(place, "_last_search", 0.0)
    orologio = iter([10.0, 10.0, 10.3, 11.0])
    attese = []

    place.search("uno", fetch=fake([]), now=lambda: next(orologio), sleep=attese.append)
    assert attese == []

    place.search("due", fetch=fake([]), now=lambda: next(orologio), sleep=attese.append)
    assert attese == [pytest.approx(0.7)]


def test_coordinates_key_is_the_same_place_at_the_same_kilometre():
    """La chiave di un posto: due decimali, cioe' circa un chilometro -- la stessa scala della
    tolleranza con cui `group` decide se due coordinate sono lo stesso posto.

    Due punti a poche centinaia di metri possono cadere ai due lati di un confine e diventare
    due chiavi: e' dichiarato, e costa una risposta in piu', non una posa persa. Lo zero
    negativo si normalizza, o lo stesso punto avrebbe due chiavi."""
    assert place.coordinates_key(45.6, 11.667) == "45.60,11.67"
    assert place.coordinates_key(45.601, 11.6671) == place.coordinates_key(45.6, 11.667)
    assert place.coordinates_key(-0.001, -0.0) == "0.00,0.00"
    assert place.coordinates_key(None, 11.0) is None and place.coordinates_key(45.0, None) is None
    # l'antimeridiano da' due chiavi allo stesso punto: due domande invece di una, mai una perdita
    assert place.coordinates_key(45, 179.999) != place.coordinates_key(45, -179.999)


def test_the_log_says_why_the_network_failed_without_the_request(caplog):
    """Sul NAS la diagnosi e' proprio questa: un nome che non si risolve, un certificato che non
    vale. Si scrive il motivo del socket, che non porta la richiesta (e la chiave dentro)."""
    import urllib.error

    caplog.set_level("INFO")

    def giu(url):
        raise urllib.error.URLError(OSError(11001, "getaddrinfo failed"))

    assert net.ask(giu, "https://esempio.test/x?key=segreta99") is None
    (riga,) = caplog.records
    assert "getaddrinfo failed" in riga.__dict__["reason"]
    assert "segreta99" not in str(riga.__dict__)
