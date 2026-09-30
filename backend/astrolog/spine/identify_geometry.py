"""La geometria del campo: quanto cielo chiedere al catalogo, e cosa c'e' davvero nella foto.

Puro: niente database, niente decisioni sull'identita'. Chi decide e' `identify`.

Vincoli non ovvi:

* **Due raggi, e dicono due cose diverse.** `frame_radius_deg` e' la mezza diagonale, cioe'
  quanto e' grande la foto: serve a misurare la centratura. `search_radius_deg` e' quanto
  cielo si chiede al catalogo, e non puo' essere lo stesso -- un oggetto **grande col centro
  lontano** contiene il puntamento pur stando fuori dalla mezza diagonale, e su un campo
  stretto (focale lunga) sarebbe proprio il soggetto a cadere fuori dalla ricerca.
* **Il rettangolo dice, non scarta.** Il cerchio circoscritto copre **1,7 volte** l'area del
  rettangolo (sensore 3:2): sapere che un oggetto e' nel cono ma fuori dall'inquadratura e'
  cio' che l'utente vuole leggere ("M 31 e' nella foto, NGC 206 e' li' accanto"). Chi filtra
  e' `overlaps_frame`, e sbaglia apposta per difetto.
* **La rotazione conta.** Lo stesso oggetto e' dentro o fuori a seconda di come era orientata
  la camera. Dove `frame_wcs` non ce l'ha -- lo schema dice che puo' mancare a soluzione
  buona -- si ricade sul cerchio, e `frame_shape` lo dichiara.
* **Un oggetto piu' grande del campo ha il centro fuori** e riempie la foto: e' il pannello di
  un mosaico. Per questo ogni prova di contenimento somma il raggio dell'oggetto.
"""

import math

from ..units import radius_deg

# Il raggio minimo di ricerca: e' il tetto del metro del punteggio (`identify_score`), cosi'
# nessuna voce che potrebbe **contenere** il puntamento resta fuori dal cono. Portato da
# `old/backend/astrolog/catalogs/propose.py:60-62`.
MIN_SEARCH_RADIUS_DEG = 3.0


def search_radius_deg(frame_radius_deg):
    """Quanto cielo chiedere al catalogo. **Non** la mezza diagonale: su un campo stretto un
    oggetto grande col centro lontano -- che e' il soggetto -- cadrebbe fuori dalla ricerca e
    non tornerebbe mai piu'. Il cono e' largo almeno quanto il metro del punteggio."""
    if frame_radius_deg is None:
        return MIN_SEARCH_RADIUS_DEG
    return max(frame_radius_deg, MIN_SEARCH_RADIUS_DEG)


def frame_radius_deg(wcs):
    """Quanto e' grande la foto: la mezza diagonale dei lati misurati, o `None` se il campo non
    si sa. E' il metro della centratura, non della ricerca.

    Si legge il rettangolo gia' in gradi e non lo si ricalcola dai pixel del sensore: la
    derivazione da `naxis1`/`naxis2` ha gia' una casa, `solve`, che la scrive in `frame_wcs`."""
    width, height = wcs.get("width_deg"), wcs.get("height_deg")
    if not width or not height:
        return None
    return math.hypot(width, height) / 2.0


def tangent_offset_deg(center_ra_deg, center_dec_deg, ra_deg, dec_deg):
    """Lo scarto `(est, nord)` in gradi sul piano tangente al centro del campo, o `None` se il
    punto sta nell'emisfero opposto (li' il piano tangente non arriva).

    Lo scarto tondo non basta a dire se un oggetto e' nell'inquadratura: serve **da che parte**.

    E' la proiezione gnomonica vera, la stessa che usa il solver (`CTYPE = ...-TAN`), non
    l'approssimazione "differenza per il coseno della declinazione": quella e' esatta solo se i
    due punti stanno sullo stesso parallelo, e vicino al polo sballa. Due punti a declinazione
    89,26 e mezzo giro di ascensione retta stanno ai lati del polo, a **1,48 gradi** l'uno
    dall'altro; l'approssimazione ne dichiarava **2,32**, il 57% in piu', e un oggetto dentro
    l'inquadratura finiva dichiarato fuori."""
    ra0, dec0 = math.radians(center_ra_deg), math.radians(center_dec_deg)
    ra1, dec1 = math.radians(ra_deg), math.radians(dec_deg)
    d_ra = ra1 - ra0
    cos_c = math.sin(dec0) * math.sin(dec1) + math.cos(dec0) * math.cos(dec1) * math.cos(d_ra)
    if cos_c <= 0:
        return None  # dall'altra parte del cielo: il piano tangente non ci arriva
    east = math.cos(dec1) * math.sin(d_ra) / cos_c
    north = (
        math.cos(dec0) * math.sin(dec1) - math.sin(dec0) * math.cos(dec1) * math.cos(d_ra)
    ) / cos_c
    return math.degrees(east), math.degrees(north)


def frame_shape(wcs):
    """`"rectangle"` se il campo si sa per intero, `"circle"` se mancano lati o rotazione,
    `None` se non c'e' cielo. E' cio' che permette di **dire** con cosa si e' deciso."""
    if wcs.get("ra_deg") is None or wcs.get("dec_deg") is None:
        return None
    whole = wcs.get("width_deg") and wcs.get("height_deg") and wcs.get("rotation_deg") is not None
    return "rectangle" if whole else "circle"


def in_frame(wcs, ra_deg, dec_deg, size_major_arcmin=None):
    """L'oggetto e' **nell'inquadratura**? `True`/`False`, o `None` se non c'e' cielo.

    Col rettangolo si ruota lo scarto negli assi del sensore e si confronta coi mezzi lati;
    senza, si ricade sul cerchio circoscritto. In tutti e due i casi si somma il raggio
    dell'oggetto: un oggetto piu' grande del campo ha il centro fuori e la foto piena."""
    shape = frame_shape(wcs)
    if shape is None:
        return None
    offset = tangent_offset_deg(wcs["ra_deg"], wcs["dec_deg"], ra_deg, dec_deg)
    if offset is None:
        return False  # dall'altra parte del cielo: nella foto non c'e' di sicuro
    east, north = offset
    radius = radius_deg(size_major_arcmin)
    if shape == "circle":
        circle = frame_radius_deg(wcs)
        return True if circle is None else math.hypot(east, north) <= circle + radius
    # negli assi del sensore: si gira lo scarto all'indietro della rotazione del campo
    t = math.radians(wcs["rotation_deg"])
    x = east * math.cos(t) + north * math.sin(t)
    y = -east * math.sin(t) + north * math.cos(t)
    return abs(x) <= wcs["width_deg"] / 2.0 + radius and abs(y) <= wcs["height_deg"] / 2.0 + radius


def reach_deg(fov_radius_deg, size_major_arcmin):
    """Fin dove un oggetto tocca il campo: il raggio del campo piu' il suo. E' il metro di chi
    chiede "sta nella foto?", qui e nel punteggio (`identify_score.centering_term`)."""
    return fov_radius_deg + radius_deg(size_major_arcmin)


def overlaps_frame(separation_deg, size_major_arcmin, fov_radius_deg):
    """Il candidato tocca il campo? E' il filtro che decide chi resta in gara, e **sbaglia
    apposta per difetto**: portato da `old/backend/astrolog/catalogs/propose.py:196-221`.

    Le tre guardie sono tutte necessarie, e le prime due dicono la stessa cosa: non si scarta
    un candidato per un dato che manca a **noi**. Il filtro deve poter dire "non si sovrappone",
    mai "non lo so". La terza -- l'oggetto piu' grande del campo -- e' gia' coperta dal
    `+ raggio`, verificata sui quattro pannelli veri di IC 405."""
    if fov_radius_deg is None or size_major_arcmin is None:
        return True
    return separation_deg <= reach_deg(fov_radius_deg, size_major_arcmin)
