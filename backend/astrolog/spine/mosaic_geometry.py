"""Due campi risolti a confronto: si sovrappongono, uno contiene l'altro, o sono lontani.

Puro: niente database, niente decisioni. Chi decide se sono pannelli di un mosaico e' il
contratto (`docs/domini/mosaico.md`), che chiede *"si sovrappongono e nessuno contiene l'altro"*:
qui si risponde soltanto quale delle tre relazioni c'e'.

Sta fuori da `identify_geometry` -- di cui riusa le primitive -- perche' quello ha un mestiere
solo, la geometria al servizio di `identify`. Non e' uno stadio: quando il mosaico ne diventera'
uno, entrera' anche nel contratto di indipendenza in `backend/pyproject.toml`.

Vincoli non ovvi:

* **Si confronta sul piano tangente al primo campo**, con la proiezione vera di
  `identify_geometry.tangent_offset_deg`: due centri alla stessa declinazione hanno comunque uno
  scarto in nord, e vicino al polo l'approssimazione col coseno sbaglia del 57%.
* **La rotazione conta, e da sola cambia la risposta**: lo stesso centro, girato, presenta al
  vicino il lato corto invece del lungo. Il confronto e' fra rettangoli **orientati**, non fra i
  loro riquadri allineati agli assi.
* **Un dato che manca a noi non allontana due campi.** Senza rotazione si ricade sul cerchio
  circoscritto, come fa gia' `identify_geometry`; senza nemmeno i lati non si sa quanto e' grande
  l'inquadratura e si risponde "si sovrappongono". Sbagliare per eccesso costa una proposta
  rifiutata con un clic, escludere costa un pannello perso in silenzio.
* **La risposta e' simmetrica**: "A con B" e "B con A" dicono la stessa cosa, o il risultato
  dipenderebbe da come la corsa scorre le pose.
"""

import math

from .identify_geometry import frame_radius_deg, frame_shape, tangent_offset_deg

DISJOINT, PARTIAL, NESTED = "disjoint", "partial", "nested"

# Quanto possono distare due centri e restare la STESSA inquadratura, in frazione della mezza
# diagonale del campo. **Non** e' un valore in gradi: in gradi sarebbe tarato sull'attrezzatura di
# chi lo sceglie -- su una focale lunga unirebbe due pannelli, su un campo largo spezzerebbe il
# dithering. Fra le due cose c'e' un divario che nessuna taratura fine deve colmare: il dithering
# che N.I.N.A. consiglia (una decina di pixel della camera di ripresa, nel suo esempio 15 secondi
# d'arco) vale l'1,2% della mezza diagonale, mentre il passo del pannello piu' stretto possibile
# -- mezzo campo -- ne vale l'83%. Un quarto sta in mezzo, con un ordine di grandezza di margine
# da una parte e tre volte dall'altra.
SAME_POINTING_FRACTION = 0.25


def overlap(a, b):
    """Che relazione c'e' fra i due campi: `"disjoint"`, `"partial"`, `"nested"`, o `None` se a
    uno dei due manca il cielo.

    `"nested"` vuol dire che uno contiene l'altro -- la stessa ripresa rifatta, o il dithering --
    e **non** e' un mosaico; `"partial"` e' la relazione fra due pannelli affiancati."""
    if frame_shape(a) is None or frame_shape(b) is None:
        return None
    offset = tangent_offset_deg(a["ra_deg"], a["dec_deg"], b["ra_deg"], b["dec_deg"])
    if offset is None:
        return DISJOINT  # dall'altra parte del cielo
    if frame_shape(a) == "circle" or frame_shape(b) == "circle":
        return _between_circles(a, b, offset)
    return _between_rectangles(a, b, offset)


def same_pointing(a, b):
    """Le due pose guardano la **stessa inquadratura**? `True`/`False`, o `None` senza cielo.

    Serve a non spezzare un pannello in due: il dithering sposta la posa di pochi secondi d'arco,
    e il confronto fra rettangoli non lo distingue da due pannelli affiancati -- li' rispondono
    tutti e due "si sovrappongono". Qui si guarda quanto distano i centri, in frazione del campo.

    Senza i lati la frazione non si puo' misurare, e allora non si dichiara la stessa: unire due
    pannelli in silenzio e' il danno peggiore, mentre tenerli distinti li lascia al confronto fra
    campi e alla conferma dell'utente. Fra due campi di misura diversa decide il **piu' piccolo**:
    e' quello a cui lo stesso scarto pesa di piu'."""
    if frame_shape(a) is None or frame_shape(b) is None:
        return None
    offset = tangent_offset_deg(a["ra_deg"], a["dec_deg"], b["ra_deg"], b["dec_deg"])
    if offset is None:
        return False  # dall'altra parte del cielo: non e' lo stesso puntamento di sicuro
    raggi = [r for r in (frame_radius_deg(a), frame_radius_deg(b)) if r]
    if len(raggi) < 2:
        return False
    return math.hypot(*offset) < min(raggi) * SAME_POINTING_FRACTION


def _between_circles(a, b, offset):
    """Col cerchio circoscritto, quando a un campo manca la rotazione. Senza nemmeno i lati il
    raggio non si sa, e allora non si dichiara mai "lontani": si risponde che si sovrappongono."""
    ra, rb = frame_radius_deg(a), frame_radius_deg(b)
    if ra is None or rb is None:
        return PARTIAL
    distance = math.hypot(*offset)
    if distance > ra + rb:
        return DISJOINT
    if distance + min(ra, rb) <= max(ra, rb):
        return NESTED
    return PARTIAL


def _between_rectangles(a, b, offset):
    """Due rettangoli orientati, col teorema degli assi separatori.

    Si lavora negli assi del sensore di A: lo scarto si gira all'indietro della sua rotazione --
    la stessa mossa di `identify_geometry.in_frame` -- e di B resta la rotazione **relativa**.
    Bastano quattro assi, i due di A e i due di B: se su nessuno i due si separano, si toccano."""
    ax, ay = a["width_deg"] / 2.0, a["height_deg"] / 2.0
    bx, by = b["width_deg"] / 2.0, b["height_deg"] / 2.0
    cx, cy = _in_axes(offset, a["rotation_deg"])
    t = math.radians(b["rotation_deg"] - a["rotation_deg"])
    cos_t, sin_t = abs(math.cos(t)), abs(math.sin(t))

    # quanto B sporge lungo gli assi di A, e quanto A sporge lungo quelli di B
    b_su_a = (bx * cos_t + by * sin_t, bx * sin_t + by * cos_t)
    a_su_b = (ax * cos_t + ay * sin_t, ax * sin_t + ay * cos_t)
    # Da questo lato contano solo i moduli, quindi lo scarto non si gira: scriverlo col segno
    # (`-cx, -cy`, il verso da B ad A) lasciava due segni che nessun test puo' distinguere,
    # perche' finiscono tutti dentro un valore assoluto.
    ux, uy = _in_axes((cx, cy), math.degrees(t))

    if abs(cx) > ax + b_su_a[0] or abs(cy) > ay + b_su_a[1]:
        return DISJOINT
    if abs(ux) > bx + a_su_b[0] or abs(uy) > by + a_su_b[1]:
        return DISJOINT
    if abs(cx) + b_su_a[0] <= ax and abs(cy) + b_su_a[1] <= ay:
        return NESTED  # B sta tutto dentro A
    if abs(ux) + a_su_b[0] <= bx and abs(uy) + a_su_b[1] <= by:
        return NESTED
    return PARTIAL


def _in_axes(offset, rotation_deg):
    """Lo scarto `(est, nord)` riscritto negli assi di un campo ruotato di `rotation_deg`."""
    east, north = offset
    t = math.radians(rotation_deg)
    return east * math.cos(t) + north * math.sin(t), -east * math.sin(t) + north * math.cos(t)
