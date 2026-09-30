"""Dove sta un corpo del sistema solare, visto da un posto della Terra.

Sta in un file suo perche' lo chiedono **in due** -- la Luna e il Sole -- e la stessa mezza dozzina
di righe scritta due volte divergerebbe al primo ritocco: e' il conto piu' delicato che abbiamo, e
una delle due copie si accorgerebbe di un difetto e l'altra no.

Vincoli non ovvi:

* **Un istante senza fuso si rifiuta**, non si indovina: letto come UTC, la notte di un sito
  lontano risulterebbe sbagliata di mezza giornata.
* **Si chiede ad astropy in un colpo solo**, per tutta la griglia: una chiamata per campione
  costerebbe centinaia di conversioni di coordinate per una notte sola.
* **La conversione si guarda**: astropy dichiara che puo' non avvenire, e il conto dopo lavorerebbe
  su niente senza accorgersene.
"""

import datetime as dt

from astropy.coordinates import AltAz, EarthLocation, SkyCoord, get_body, get_sun
from astropy.time import Time


def quando(istante):
    """Un istante con fuso, come `Time` di astropy. Senza fuso si rifiuta."""
    if istante.tzinfo is None:
        raise ValueError(
            "un istante senza fuso non si indovina: sarebbe letto come UTC, e la notte di un"
            " sito lontano risulterebbe sbagliata di mezza giornata"
        )
    return Time(istante.astimezone(dt.UTC))


def convertito(corpo, sistema) -> SkyCoord:
    """Un corpo portato in un altro sistema di coordinate.

    Due cose in una riga. **A tempo di esecuzione**: `astropy` dichiara che la conversione puo'
    non avvenire, e il conto dopo lavorerebbe su niente senza accorgersene -- qui si guarda, e se
    succede si dice. **A tempo di tipi**: il valore dichiarato torna `SkyCoord`, cosi' il
    "puo' essere niente" delle sue stub si ferma qui invece di costringere ogni chiamante a
    zittirlo per conto suo (e' lo stesso rumore che `fits/header_coords.py` disarma sul posto)."""
    dentro = corpo.transform_to(sistema)
    if dentro is None:
        raise RuntimeError(f"astropy non ha convertito in {type(sistema).__name__}")
    return dentro


def altezze(corpo, istanti, latitude, longitude):
    """L'altezza di `corpo` sull'orizzonte, in gradi, per ognuno degli istanti dati.

    **Topocentrica**: il posto entra sia nel chiedere dov'e' il corpo sia nel portarlo in
    orizzontali, e per la Luna non e' un dettaglio -- la parallasse vale quasi un grado.

    Senza pressione, quindi **geometrica**: e' la definizione su cui poggiano le soglie dei
    crepuscoli (`ASTRO_DEG` e le sue sorelle). La rifrazione entra dove deve, cioe' dentro
    `RISESET_DEG`, che e' una soglia e non un'altezza."""
    dove = EarthLocation(lat=latitude, lon=longitude)
    momenti = Time([quando(i) for i in istanti])
    # Il Sole ha la sua strada, e non e' un capriccio: `get_body("sun", ...)` costa **125 ms**
    # contro i 38 di `get_sun` sulla stessa griglia, e le due altezze coincidono -- quanto, lo
    # misura `test_the_sun_asked_the_fast_way_agrees_with_the_slow_one` invece di dirlo qui. Per
    # la Luna invece la strada del corpo serve davvero: li' la parallasse vale quasi un grado.
    astro = get_sun(momenti) if corpo == "sun" else get_body(corpo, momenti, dove)
    sopra = convertito(astro, AltAz(obstime=momenti, location=dove))
    gradi = sopra.alt.deg  # pyright: ignore[reportOptionalMemberAccess]
    return [float(a) for a in gradi]  # pyright: ignore[reportArgumentType, reportOptionalIterable]
