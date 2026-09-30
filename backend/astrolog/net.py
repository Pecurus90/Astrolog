"""La rete verso i servizi esterni: una richiesta che si presenta, e due modi di sbagliare -- il
servizio che rifiuta la richiesta, e il servizio che non risponde.

Vincolo non ovvio: chi chiama riceve la chiamata come argomento (`fetch`), cosi' i test passano un
finto e la suite non esce mai di casa. Un servizio che tace torna `None` e lo dice al log: per chi
lo usa e' "non lo so", mai un errore in faccia. Lo usano il luogo (`place`) e il meteo (`weather`).
"""

import json
import logging
import urllib.error
import urllib.request

log = logging.getLogger(__name__)

# Chi chiama deve dirsi: la policy dei servizi lo pretende, e senza blocca.
USER_AGENT = "AstroLog/0.1 (https://github.com/Pecurus90/Astrolog)"
TIMEOUT_S = 15

REFUSED = "refused"
UNREACHABLE = "unreachable"
# Cio' che un servizio dice quando la richiesta non vale: la chiave (400, 401, 403) o i crediti
# finiti (429). Il resto -- un 500, un 503 -- e' il servizio giu', e non dice niente della chiave.
_RIFIUTI = frozenset({400, 401, 403, 429})


def service_of(url):
    """Il servizio, senza la sua richiesta: cio' che si puo' scrivere in un log. La query puo'
    portare la chiave personale dell'utente, e il log e' il file che si allega a una
    segnalazione."""
    return url.split("?", 1)[0]


def fetch(url):
    """L'unico posto che tocca la rete davvero. Chi lo sostituisce nei test passa `fetch`."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310 - solo https, e gli URL sono costanti di chi chiama
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:  # noqa: S310 - idem
        body = r.read().decode("utf-8", "replace")
    try:
        return json.loads(body)
    except ValueError:
        return body  # qualche servizio risponde un numero e basta, non JSON


def ask_why(fetch_, url):
    """Come `ask`, ma dice anche perche' non ha risposto: `(risposta, None)`, o `(None, "refused")`
    quando il servizio rifiuta la richiesta (una chiave che non vale), o `(None, "unreachable")`.
    Del rifiuto si scrive solo il codice: il testo lo scrive il servizio, e puo' ripetere la
    richiesta con la chiave dentro."""
    try:
        return fetch_(url), None
    except urllib.error.HTTPError as err:
        rifiuto = err.code in _RIFIUTI
        log.info(
            "rete: il servizio rifiuta" if rifiuto else "rete: servizio non raggiungibile",
            extra={"service": service_of(url), "code": err.code},
        )
        return None, REFUSED if rifiuto else UNREACHABLE
    except Exception as err:  # noqa: BLE001 - qualunque guasto della rete e' "non lo so"
        # Il motivo del socket (un nome che non si risolve, un certificato che non vale) e' la
        # diagnosi che serve, e non porta la richiesta: quella, con la chiave dentro, no.
        motivo = err.reason if isinstance(err, urllib.error.URLError) else err
        log.info(
            "rete: servizio non raggiungibile",
            extra={
                "service": service_of(url),
                "error": type(err).__name__,
                "reason": f"{type(motivo).__name__}: {motivo}"
                if isinstance(err, urllib.error.URLError)
                else type(motivo).__name__,
            },
        )
        return None, UNREACHABLE


def ask(fetch_, url):
    """Chiede, e se qualcosa va storto lo dice al log e torna None."""
    return ask_why(fetch_, url)[0]
