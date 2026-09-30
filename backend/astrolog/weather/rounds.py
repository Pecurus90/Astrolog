"""Un giro del meteo: la previsione dei modelli, poi il cielo in quota. Lo fanno il giro in
sottofondo e il pulsante, e l'esito che torna e' quello della previsione.

Vincolo non ovvio: **senza un sito da chiedere non si chiede niente a nessuno**: senza sito di casa,
o senza il suo fuso, le fonti del cielo non si interrogano nemmeno.
"""

from . import forecast, sky


def refresh(conn, site, *, fetch=None, now=None):
    esito = forecast.refresh(conn, site, fetch=fetch, now=now)
    if esito not in (forecast.NO_SITE, forecast.NO_TIMEZONE):
        sky.refresh(conn, site, fetch=fetch, now=now)
    return esito
