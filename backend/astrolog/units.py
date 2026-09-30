"""Le unita' e i numeri, una casa sola: la scala dal corredo, il raggio di un oggetto in gradi,
la coda che una float32 si porta dietro.

Vincolo non ovvio: si converte a monte, una volta; chi mostra o media riceve gia' il numero
confrontabile. Nessuna dipendenza: solo aritmetica.
"""

import math
from collections import Counter

# Quante cifre una float32 puo' davvero affermare: `4.29` riletta in doppia precisione
# diventa `4.28999996185303`, e quella coda non e' misura, e' formato.
F32_SIGNIFICANT_DIGITS = 7

# Arcosecondi in un radiante, diviso mille: la conversione micron -> millimetri e' dentro.
ARCSEC_PER_RAD_PER_1000 = 206.265


def strip_float32_noise(value, *, digits=F32_SIGNIFICANT_DIGITS):
    """Il valore senza la coda della sua rappresentazione; `None` resta `None`.

    Non e' un arrotondamento di comodo: taglia dove la float32 smette di dire qualcosa. Per
    accorciare un numero che ha davvero troppe cifre decide il chiamante, con `round`."""
    if value is None:
        return None
    return float(f"%.{digits}g" % value)


def most_frequent(weights):
    """Il valore col peso piu' alto in `{valore: peso}`, o `None` se non ce n'e' o se due
    pesano uguale: fra due valori con gli stessi file non si sceglie a caso."""
    top = Counter(weights).most_common(2)
    if not top or (len(top) == 2 and top[0][1] == top[1][1]):
        return None
    return top[0][0]


def physical_pixel_um(pixel_um, binning):
    """Il pixel fisico del sensore, o `None` se manca un dato. `XPIXSZ` per convenzione include
    il binning (la convenzione e le sue fonti stanno nel contratto, `docs/domini/spina.md`),
    quindi si divide. Il quoziente si ripulisce come una float32: 11,28 / 3 non e'
    3,7599999999999997."""
    if pixel_um is None or not binning:
        return None
    return strip_float32_noise(pixel_um / binning)


def hundredths(value):
    """Un numero come lo schermo lo legge, a due decimali; `None` resta `None`. Oltre il
    secondo decimale la pagina mostrerebbe cifre che nessuno legge come una misura."""
    return None if value is None else round(value, 2)


def median(values):
    """Il valore di mezzo, o `None` se non ce n'e' nessuno. **Mediana e non media**: da tre misure
    in su una storta -- una posa risolta male su un campo povero di stelle -- sposterebbe la media e
    non la mediana; con due, la mediana e' la loro media."""
    ordered = sorted(v for v in values if v is not None)
    if not ordered:
        return None
    half = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[half]
    return (ordered[half - 1] + ordered[half]) / 2


def pixel_um_from_scale(scale_arcsec_px, focal_mm, binning):
    """Il pixel fisico del sensore dalla scala misurata, la focale e il binning: l'inversa di
    `scale_arcsec_px`, diviso il binning perche' la scala misurata e' quella dei pixel uniti.
    `None` se manca un dato: un binning che non si sa non vale 1."""
    if not scale_arcsec_px or not focal_mm or not binning:
        return None
    return scale_arcsec_px * focal_mm / ARCSEC_PER_RAD_PER_1000 / binning


def scale_arcsec_px(pixel_um, focal_mm):
    """Arcosecondi per pixel dalle specifiche del corredo, `None` se manca un dato.

    E' la scala DERIVATA: non conosce il binning ne' l'ottica reale. Quella misurata dal
    solver vince sempre; questa e' la risposta finche' una misura non c'e'."""
    if not pixel_um or not focal_mm or pixel_um <= 0 or focal_mm <= 0:
        return None
    return pixel_um / focal_mm * ARCSEC_PER_RAD_PER_1000


# Un gruppo di focali ha uno spread <= 5 % (max/min <= 1.05): assorbe il tremolio
# dell'header senza incatenare configurazioni ottiche diverse.
FOCAL_TOLERANCE = 0.05


def known_focal(value):
    """La focale se e' una misura, altrimenti `None`: `True` in JSON e' un intero, e una focale
    zero o negativa non e' una focale -- focale ignota, mai inventata."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        return None
    return float(value)


def same_focal(known, focal_mm):
    """Se due focali sono la stessa: entro il +-5 % di quella gia' vista. Ignota da una parte sola
    non e' la stessa; ignota tutte e due, si'."""
    if known is None or focal_mm is None:
        return known is None and focal_mm is None
    return abs(known - focal_mm) <= FOCAL_TOLERANCE * abs(known)


def focal_buckets(focals, tol=FOCAL_TOLERANCE):
    """Mappa `{focale -> focale rappresentativa del gruppo}` raggruppando le focali entro il
    +-5 %. Portata da old/ coi suoi otto test.

    E' DETERMINISTICA e non dipende dall'ordine: si ordinano i valori distinti, si apre un
    gruppo ancorato al piu' piccolo e vi entra ogni valore fino ad `ancora * (1 + tol)`.
    L'ancoraggio al minimo e' il vincolo non ovvio: senza, 560 -> 570 -> 580 -> ... si
    incatenerebbero fino a unire due ottiche diverse. Rappresentante = mediana dei distinti.
    `None` e i valori non positivi restano fuori: focale ignota, mai inventata."""
    distinct = sorted({f for f in map(known_focal, focals) if f is not None})
    mapping = {}
    i = 0
    while i < len(distinct):
        anchor = distinct[i]
        j = i + 1
        while j < len(distinct) and distinct[j] <= anchor * (1 + tol):
            j += 1
        cluster = distinct[i:j]
        representative = cluster[len(cluster) // 2]
        for value in cluster:
            mapping[value] = representative
        i = j
    return mapping


# --- il cielo -----------------------------------------------------------------------------
# Il fondo naturale del cielo notturno: 174 microcandele per metro quadro. Anche in un posto
# senza una lampadina il cielo non e' nero (aria che brilla, luce zodiacale, stelle deboli),
# e senza sommarlo un luogo perfetto darebbe una luminosita' infinita.
NATURAL_SKY_CD_M2 = 174e-6
# La costante che lega candele per metro quadro e magnitudini per arcosecondo quadrato.
CD_M2_PER_MAG0 = 1.08e5

# I confini della scala di Bortle in magnitudini per arcosecondo quadrato. ATTENZIONE: sono
# una CONSUETUDINE, non una norma. Bortle scrisse una scala descrittiva ("si vede la Via
# Lattea", "si vedono le ombre") e non le diede confini numerici, e in giro ne circolano DUE
# famiglie che su uno stesso cielo differiscono fino a due classi. Qui si usa quella dei siti
# di astrofotografia (Wikipedia, AstroBackyard, Telescope Live), perche' e' il numero con cui
# l'utente confrontera' il nostro; l'altra famiglia, piu' severa al buio, viene dal mondo
# degli strumenti SQM. Per la stessa ragione il numero non si memorizza mai e a schermo
# compare accanto alla misura, che invece e' un fatto -- tranne nei due posti dove la misura
# non c'e' o non ci sta: il primo avvio, dove si sceglie, e il piede della barra, dove sono
# 227px e la classe e' un promemoria di dov'e' puntata l'app.
# Due confini sono i piu' deboli, e sono dichiarati: le fonti fondono la 8 e la 9 sotto 18,00
# (qui si separano a 17,00, dove le descrizioni mettono il centro citta') e la 9 non ha un
# fondo (BORTLE_BOTTOM), che serve solo a chi la classe la SCEGLIE invece di misurarla.
BORTLE_FLOORS = ((1, 21.76), (2, 21.60), (3, 21.30), (4, 20.40), (5, 19.10), (6, 18.50),
                 (7, 18.00), (8, 17.00))  # fmt: skip
# La 1 e' aperta in alto e la 9 in basso: due estremi di comodo per il verso inverso.
BORTLE_TOP, BORTLE_BOTTOM = 22.00, 16.00


def sqm_from_brightness(artificial_mcd_m2):
    """Da luce artificiale (millicandele per metro quadro, com'e' data dai servizi) a
    magnitudini per arcosecondo quadrato: si somma il fondo naturale, poi si converte.
    `None` per un dato assente o negativo, che non e' una luminosita'."""
    if artificial_mcd_m2 is None or artificial_mcd_m2 < 0:
        return None
    total = artificial_mcd_m2 / 1000.0 + NATURAL_SKY_CD_M2
    return hundredths(-2.5 * math.log10(total / CD_M2_PER_MAG0))


# I confini di cio' che e' un cielo: sotto sta un piazzale illuminato, sopra non esiste un
# posto sulla Terra. Un servizio che risponde fuori da qui ha risposto un guasto, non un
# cielo. Lo `schema.sql` ripete gli stessi numeri in un CHECK: e' la guardia del database,
# che vale anche per chi scrive nel DB senza passare di qui.
SQM_MIN, SQM_MAX = 10.0, 23.0


def believable_sqm(sqm):
    """La luminosita' se e' un cielo possibile, altrimenti `None`: una stima assurda non si
    salva e non si mostra, si tratta come una risposta che non c'e' stata."""
    if sqm is None or not (SQM_MIN <= sqm <= SQM_MAX):
        return None
    return sqm


def bortle_of(sqm):
    """La classe di cielo, da 1 (il piu' scuro) a 9. `None` resta `None`: non si indovina."""
    if sqm is None:
        return None
    for classe, floor in BORTLE_FLOORS:
        if sqm >= floor:
            return classe
    return 9


def sqm_of_bortle(classe):
    """Il verso opposto, per chi il cielo lo sceglie dall'elenco invece di misurarlo: il
    centro della classe, cosi' rileggendolo si ritrova la stessa classe."""
    floors = dict(BORTLE_FLOORS)
    low = floors.get(classe, BORTLE_BOTTOM)
    high = floors.get(classe - 1, BORTLE_TOP)
    return hundredths((low + high) / 2)


def field_deg(pixels, scale_arcsec_px_):
    """Il lato del campo in gradi, da quanti pixel ha il sensore e da quanto vale un pixel.
    `None` se manca un dato: il campo ignoto non si inventa, e chi lo passa al solver preferisce
    che cerchi da se' piuttosto che cercare il campo sbagliato."""
    if not pixels or not scale_arcsec_px_ or pixels <= 0 or scale_arcsec_px_ <= 0:
        return None
    return pixels * scale_arcsec_px_ / 3600.0


def radius_deg(size_major_arcmin):
    """Il raggio di un oggetto in gradi, dalla sua dimensione maggiore in primi d'arco. Senza
    dimensione e' zero: l'oggetto e' un punto."""
    return size_major_arcmin / 120.0 if size_major_arcmin else 0.0


def separation_deg_from_cosine(cos_sep):
    """Quanto distano due direzioni del cielo, dal coseno dell'angolo fra loro.

    Il taglio a [-1, 1] non e' prudenza: due versori paralleli danno un prodotto scalare come
    `1.0000000000000002`, e `acos` di quello solleva. Sta qui e non nei due chiamanti perche'
    e' una formula sola -- chi cerca per cono arriva al coseno con un prodotto scalare che ha
    gia' pronto, chi confronta due candidati parte dalle coordinate."""
    return math.degrees(math.acos(min(1.0, max(-1.0, cos_sep))))


def angular_separation_deg(ra1_deg, dec1_deg, ra2_deg, dec2_deg):
    """Quanto distano due punti del cielo, in gradi.

    Passa dai versori invece che dalla formula sferica con le differenze di ascensione retta:
    cosi' il salto a 0/360 gradi non e' un caso da ricordarsi, e due punti a 0,5 e 359,5
    distano un grado invece di trecentocinquantanove."""
    ra1, dec1, ra2, dec2 = map(math.radians, (ra1_deg, dec1_deg, ra2_deg, dec2_deg))
    cos_sep = math.sin(dec1) * math.sin(dec2) + math.cos(dec1) * math.cos(dec2) * math.cos(
        ra1 - ra2
    )
    return separation_deg_from_cosine(cos_sep)
