"""Le preferenze dell'utente e i valori di fabbrica: chiavi CHIUSE, con tipo e fonte.

Vincolo non ovvio: il tipo e' della chiave, non dell'aspetto del valore (un nome utente
"2024" resta testo). Ogni valore di fabbrica dice da dove viene: una convenzione pubblica
dove c'e', altrimenti una scelta di prodotto dichiarata, che l'utente cambia in Impostazioni.
"""

from ..clock import now_iso

# chiave -> (tipo, valore di fabbrica, da dove viene)
KEYS = {
    "user_name": (str, None, "lo dice l'utente nel wizard"),
    "language": (str, "it", "la lingua in cui l'app si costruisce; l'inglese e' la seconda"),
    "onboarding_done_at": (str, None, "il timbro del primo avvio: un fatto, non un'euristica"),
    "astap_path": (
        str,
        None,
        "dove sta il solver, quando l'app non lo trova da sola. Lo dichiara l'utente nel primo"
        " avvio o nelle Impostazioni, e vince sulla ricerca automatica: e' la via d'uscita"
        " quando quella sbaglia (una copia vecchia, un nome diverso)",
    ),
    "sky_service_key": (
        str,
        None,
        "la chiave personale del servizio che stima il cielo: gratuita, chiesta con una email"
        " all'autore. Senza, la luminosita' si misura o si sceglie: l'app funziona uguale",
    ),
    "meteoblue_key": (
        str,
        None,
        "la chiave personale di Meteoblue, per il seeing ora per ora: gratuita, chiesta sul loro"
        " sito. Senza, il seeing viene da 7Timer, a fasce: l'app funziona uguale",
    ),
    "weather_model": (
        str,
        "best_match",
        "il modello della previsione: di fabbrica quello che Open-Meteo sceglie per il posto",
    ),
}

# Le chiavi che accettano solo certi valori. I modelli meteo sono quelli che la previsione chiede
# al servizio (`weather/openmeteo.py` li prende da qui): un nome fuori elenco darebbe una pagina
# vuota senza un perche'.
CHOICES = {"weather_model": ("best_match", "ecmwf_ifs025", "icon_seamless", "gfs_seamless")}


# Le chiavi dei servizi: fuori da qui escono solo come suggerimento (`hint`), mai intere.
SECRETS = frozenset({"sky_service_key", "meteoblue_key"})
# Quelle che si scrivono solo dopo averle provate sul conto: le scrive la loro rotta
# (`api/weather_key.py`), non la scrittura generica delle preferenze.
TRIED_ELSEWHERE = frozenset({"meteoblue_key"})


def hint(value):
    """Come si mostra una chiave senza mostrarla: le ultime quattro cifre. Basta a rispondere alla
    sola domanda che serve -- e' quella che ho messo io?"""
    if not value:
        return None
    # una chiave di quattro caratteri o meno sarebbe mostrata intera: si dice solo che c'e'
    return "..." + value[-4:] if len(value) > 4 else "..."


def defaults():
    return {k: v for k, (_t, v, _why) in KEYS.items()}


def read(conn):
    """Tutte le chiavi: il valore salvato (nel tipo della chiave), o quello di fabbrica."""
    values = defaults()
    for row in conn.execute("SELECT key, value FROM config"):
        key = row["key"]
        if key in KEYS and row["value"] is not None:
            values[key] = KEYS[key][0](row["value"])
    return values


def write(conn, key, value):
    """Scrive una chiave nota; `KeyError` per una chiave fuori dall'elenco, `ValueError` per
    un valore che non e' del tipo della chiave: si respinge qui, dove si puo' rispondere
    422, non in lettura."""
    if key not in KEYS:
        raise KeyError(f"chiave di configurazione sconosciuta: {key}")
    kind = KEYS[key][0]
    if value is not None and (isinstance(value, bool) or not isinstance(value, kind)):
        raise ValueError(f"{key} vuole {kind.__name__}, non {value!r}")
    if value is not None and key in CHOICES and value not in CHOICES[key]:
        raise ValueError(f"{key} vuole uno di {CHOICES[key]}, non {value!r}")
    conn.execute(
        "INSERT INTO config(key, value, updated_at) VALUES(?, ?, ?)"
        " ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
        (key, None if value is None else str(value), now_iso()),
    )
