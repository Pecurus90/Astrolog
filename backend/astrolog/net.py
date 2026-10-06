"""The network towards outside services. A silent service returns `None` and tells the log: for
the caller it means "unknown", never an error in the user's face."""

import json
import logging
import urllib.error
import urllib.request
from collections.abc import Callable
from enum import StrEnum
from typing import Any

log = logging.getLogger(__name__)

# The network call each caller receives, so tests pass a fake and never leave the machine.
type Fetch = Callable[[str], Any]

# The services' policy demands that the caller name itself, and blocks it otherwise.
USER_AGENT = "AstroLog/0.1 (https://github.com/Pecurus90/Astrolog)"
TIMEOUT_S = 15


class Failure(StrEnum):
    REFUSED = "refused"
    UNREACHABLE = "unreachable"


# What a service answers when the request is not valid: the key, or the credits run out. The rest
# (a 500, a 503) is the service down, and says nothing about the key.
_REFUSALS = frozenset({400, 401, 403, 429})


def service_of(url: str) -> str:
    """The query may carry the user's personal key, and the log is the file attached to a report."""
    return url.split("?", 1)[0]


def fetch(url: str) -> Any:
    # S310: https only, and the URLs are the callers' constants.
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:  # noqa: S310 - same as above
        body = r.read().decode("utf-8", "replace")
    try:
        return json.loads(body)
    except ValueError:
        return body  # some services answer a bare number, not JSON


def ask_why(fetch_: Fetch, url: str) -> tuple[Any, Failure | None]:
    """Of a refusal only the code is logged: the text is the service's, and may repeat the
    request with the key inside."""
    try:
        return fetch_(url), None
    except urllib.error.HTTPError as err:
        refused = err.code in _REFUSALS
        log.info(
            "rete: il servizio rifiuta" if refused else "rete: servizio non raggiungibile",
            extra={"service": service_of(url), "code": err.code},
        )
        return None, Failure.REFUSED if refused else Failure.UNREACHABLE
    except Exception as err:  # noqa: BLE001 - any network failure is "unknown"
        # The socket's reason (an unresolved name, an invalid certificate) is the diagnosis
        # needed, and does not carry the request.
        cause = err.reason if isinstance(err, urllib.error.URLError) else err
        log.info(
            "rete: servizio non raggiungibile",
            extra={
                "service": service_of(url),
                "error": type(err).__name__,
                "reason": f"{type(cause).__name__}: {cause}"
                if isinstance(err, urllib.error.URLError)
                else type(cause).__name__,
            },
        )
        return None, Failure.UNREACHABLE


def ask(fetch_: Fetch, url: str) -> Any:
    return ask_why(fetch_, url)[0]
