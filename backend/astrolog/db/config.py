"""User preferences and factory defaults over closed keys. The type belongs to the key, not to the
look of the value: a user named "2024" stays text."""

import sqlite3
from dataclasses import dataclass
from typing import Any, NamedTuple

from ..clock import now_iso
from ..levels import MoonRule
from ..twilight import RISESET_DEG


class Key(NamedTuple):
    kind: type
    factory: str | int | None
    # where the factory value comes from: a public convention or a product choice
    source: str


KEYS: dict[str, Key] = {
    "user_name": Key(str, None, "lo dice l'utente nel wizard"),
    "language": Key(str, "it", "la lingua in cui l'app si costruisce; l'inglese e' la seconda"),
    "onboarding_done_at": Key(str, None, "il timbro del primo avvio: un fatto, non un'euristica"),
    "astap_path": Key(
        str,
        None,
        "dove sta il solver, quando l'app non lo trova da sola. Lo dichiara l'utente nel primo"
        " avvio o nelle Impostazioni, e vince sulla ricerca automatica: e' la via d'uscita"
        " quando quella sbaglia (una copia vecchia, un nome diverso)",
    ),
    "sky_service_key": Key(
        str,
        None,
        "la chiave personale del servizio che stima il cielo: gratuita, chiesta con una email"
        " all'autore. Senza, la luminosita' si misura o si sceglie: l'app funziona uguale",
    ),
    "meteoblue_key": Key(
        str,
        None,
        "la chiave personale di Meteoblue, per il seeing ora per ora: gratuita, chiesta sul loro"
        " sito. Senza, il seeing non c'e': il resto del meteo funziona uguale",
    ),
    "weather_model": Key(
        str,
        "best_match",
        "il modello della previsione: di fabbrica quello che Open-Meteo sceglie per il posto",
    ),
    "moon_good_pct": Key(
        int,
        25,  # [C ING Technical Note 127: dark time lit fraction under 0.25]
        "banda larga buona con la Luna sotto questa percentuale, come il buio dell'osservatorio"
        " ING (illuminata sotto lo 0,25)",
    ),
    "moon_limit_pct": Key(
        int,
        65,  # [C ING Technical Note 127: grey time to 0.65, then bright]
        "banda larga al limite fino a questa percentuale, poi solo banda stretta: il grigio di"
        " ING (fino allo 0,65)",
    ),
    "moon_above_deg": Key(
        int,
        0,  # [C USNO RST_defs: rise and set at -0.833 degrees]
        "la Luna conta da questa altezza: 0 e' quando sorge (ADR 0034); -5 la rete TESS, che"
        " sotto non la sente; 5 e 10 nessuna convenzione",
    ),
}


@dataclass(frozen=True, slots=True)
class Preferences:
    """One field per key of `KEYS`, in its order: the settings page lists them so. The two without
    `None` have a factory value, and a stored NULL falls back to it."""

    user_name: str | None
    language: str
    onboarding_done_at: str | None
    astap_path: str | None
    sky_service_key: str | None
    meteoblue_key: str | None
    weather_model: str
    moon_good_pct: int
    moon_limit_pct: int
    moon_above_deg: int


# A weather model outside this list would give an empty page with no reason.
WEATHER_MODELS = ("best_match", "ecmwf_ifs025", "icon_seamless", "gfs_seamless")
# [C Bara et al. 2021, arXiv 2104.10616: TESS, under -5 degrees the Moon is not felt]
MOON_FLOORS = (-5, 0, 5, 10)
CHOICES: dict[str, tuple[str, ...] | tuple[int, ...]] = {
    "weather_model": WEATHER_MODELS,
    "moon_above_deg": MOON_FLOORS,
}
# A number outside its range would make every night good, or none. [T] percent
RANGES = {"moon_good_pct": (0, 100), "moon_limit_pct": (0, 100)}
# The Moon's rule, read together: a change rewrites what it judged (`moon_rule`).
MOON_KEYS = frozenset({"moon_good_pct", "moon_limit_pct", "moon_above_deg"})


def moon_rule_holds(prefs: Preferences) -> bool:
    """Marginal never under good, or a night would be marginal and good at once."""
    return prefs.moon_limit_pct >= prefs.moon_good_pct


def moon_rule(prefs: Preferences) -> MoonRule:
    """Altitude 0 is the rise, where refraction and radius already lift the Moon: -0.833."""
    floor = RISESET_DEG if prefs.moon_above_deg == 0 else float(prefs.moon_above_deg)
    return MoonRule(prefs.moon_good_pct, prefs.moon_limit_pct, floor)


class OutOfRangeError(ValueError):
    """The right type, outside `RANGES`: the screen can say the range, not "wrong type"."""


# Service keys leave the app only as a `hint`, never whole.
SECRETS = frozenset({"sky_service_key", "meteoblue_key"})
# Written only after a check against the account, by their own route, not by the generic write.
TRIED_ELSEWHERE = frozenset({"meteoblue_key"})


def hint(value: str | None) -> str | None:
    """The last four characters: enough to answer "is it the one I entered?"."""
    if not value:
        return None
    # a key of four characters or fewer would be shown whole: only say that there is one
    return "..." + value[-4:] if len(value) > 4 else "..."


def defaults() -> dict[str, Any]:
    return {k: key.factory for k, key in KEYS.items()}


def read(conn: sqlite3.Connection) -> Preferences:
    """Every key: the saved value in the key's type, or the factory one."""
    values = defaults()
    for row in conn.execute("SELECT key, value FROM config"):
        key = row["key"]
        if key in KEYS and row["value"] is not None:
            values[key] = KEYS[key].kind(row["value"])
    return Preferences(**values)


def write(conn: sqlite3.Connection, key: str, value: object) -> None:
    """`KeyError` for an unknown key, `ValueError` for a value of the wrong type: rejected here,
    where the API can answer 422, not on read."""
    if key not in KEYS:
        raise KeyError(f"chiave di configurazione sconosciuta: {key}")
    kind = KEYS[key].kind
    if value is not None and (isinstance(value, bool) or not isinstance(value, kind)):
        raise ValueError(f"{key} vuole {kind.__name__}, non {value!r}")
    if value is not None and key in CHOICES and value not in CHOICES[key]:
        raise ValueError(f"{key} vuole uno di {CHOICES[key]}, non {value!r}")
    if isinstance(value, int) and key in RANGES and not RANGES[key][0] <= value <= RANGES[key][1]:
        raise OutOfRangeError(key)
    conn.execute(
        "INSERT INTO config(key, value, updated_at) VALUES(?, ?, ?)"
        " ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
        (key, None if value is None else str(value), now_iso()),
    )
