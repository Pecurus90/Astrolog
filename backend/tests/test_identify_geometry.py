"""La geometria del campo: quanto cielo chiedere al catalogo, e cosa c'e' davvero nella foto.

E' la meta' di `identify` che puo' sbagliare in silenzio. Un raggio troppo stretto perde il
soggetto e nessuno se ne accorge; un rettangolo storto dice "nell'inquadratura" a cio' che non
c'e'. Qui si prova con numeri a mano, dove il conto si puo' rifare a mente.
"""

import math

import pytest

from astrolog.spine import identify_geometry as geo

# Un campo realistico: 4000x3000 pixel a 1 arcosecondo per pixel. Lati 1,111 x 0,833 gradi,
# diagonale 1,389: mezza diagonale 0,694. I numeri tornano a mano, ed e' il punto.
CAMPO = {"ra_deg": 100.0, "dec_deg": 0.0, "scale_arcsec_px": 1.0,
         "width_deg": 4000 / 3600, "height_deg": 3000 / 3600, "rotation_deg": 0.0}  # fmt: skip


# --- quanto cielo chiedere al catalogo -------------------------------------------------------


def test_the_frame_radius_is_the_half_diagonal_of_the_field():
    """Quanto e' grande la foto: l'unico raggio che copre **gli angoli** del sensore e' la
    mezza diagonale. Prendere la mezza larghezza perderebbe cio' che sta negli angoli -- e
    negli angoli ci finisce il soggetto ogni volta che si inquadra di sbieco."""
    assert geo.frame_radius_deg(CAMPO) == pytest.approx(2500 / 3600, abs=1e-9)
    doppio = {**CAMPO, "width_deg": 8000 / 3600, "height_deg": 6000 / 3600}
    assert geo.frame_radius_deg(doppio) == pytest.approx(5000 / 3600, abs=1e-9)


def test_the_search_asks_for_more_sky_than_the_frame():
    """Su un campo stretto -- focale lunga -- un oggetto grande ha il centro **fuori** dalla
    mezza diagonale e contiene il puntamento lo stesso: sarebbe il soggetto, e cercando solo
    quanto e' larga la foto non tornerebbe mai. Il cono e' largo almeno quanto il metro del
    punteggio; su un campo largo, invece, e' il campo a comandare."""
    stretto = geo.frame_radius_deg({**CAMPO, "width_deg": 1000 / 3600, "height_deg": 700 / 3600})
    assert stretto < 0.2  # 0,17 gradi: una focale lunga
    assert geo.search_radius_deg(stretto) == geo.MIN_SEARCH_RADIUS_DEG
    assert geo.search_radius_deg(5.0) == 5.0
    assert geo.search_radius_deg(None) == geo.MIN_SEARCH_RADIUS_DEG


def test_without_the_sides_no_radius_is_invented():
    """Il rettangolo puo' mancare a soluzione buona -- lo schema lo dice, `frame_wcs` non porta
    i pixel del sensore. Allora non si inventa un raggio da quel che resta: si torna `None`, e
    chi chiama ricade sul cerchio o sul neutro."""
    assert geo.frame_radius_deg({**CAMPO, "width_deg": None, "height_deg": None}) is None
    assert geo.frame_radius_deg({**CAMPO, "width_deg": 1.0, "height_deg": None}) is None
    assert geo.frame_radius_deg({"ra_deg": 100.0, "dec_deg": 0.0}) is None


# --- lo scarto, e da che parte ---------------------------------------------------------------


def test_the_offset_says_how_far_and_in_which_direction():
    """Lo scarto in gradi non basta a dire se un oggetto e' nell'inquadratura: serve **da che
    parte**. Un grado a est e un grado a nord hanno lo stesso scarto e finiscono in due punti
    diversi di un rettangolo."""
    est, nord = geo.tangent_offset_deg(100.0, 0.0, 101.0, 0.0)
    assert (est, nord) == (pytest.approx(1.0, abs=1e-3), pytest.approx(0.0, abs=1e-9))
    est, nord = geo.tangent_offset_deg(100.0, 0.0, 100.0, 1.0)
    assert (est, nord) == (pytest.approx(0.0, abs=1e-9), pytest.approx(1.0, abs=1e-3))


def test_the_offset_shrinks_towards_the_pole():
    """A declinazione alta un grado di ascensione retta e' molto meno di un grado di cielo: a
    60 gradi vale la meta'. Senza questo, ogni campo vicino al polo direbbe che mezza
    costellazione e' nell'inquadratura."""
    est, _ = geo.tangent_offset_deg(100.0, 60.0, 101.0, 60.0)
    assert est == pytest.approx(0.5, abs=1e-3)


def _true_sep_deg(ra0, dec0, ra1, dec1):
    """Lo scarto vero sulla sfera, col prodotto scalare: il metro con cui si giudica lo scarto
    sul piano."""
    a, b, c, d = (math.radians(v) for v in (ra0, dec0, ra1, dec1))
    coseno = math.sin(b) * math.sin(d) + math.cos(b) * math.cos(d) * math.cos(c - a)
    return math.degrees(math.acos(min(1.0, coseno)))


@pytest.mark.parametrize(
    ("ra0", "dec0", "ra1", "dec1", "dove"),
    [
        (10.68, 41.27, 11.68, 41.27, "M 31, declinazione media"),
        (148.9, 69.07, 149.9, 69.07, "M 81, declinazione alta"),
        (12.1, 85.0, 13.1, 85.0, "vicino al polo"),
        (37.9, 89.26, 38.9, 89.26, "la Polare"),
        (37.9, 89.26, 217.9, 89.26, "oltre il polo: l'ascensione retta si ribalta"),
        (0.1, 10.0, 359.9, 10.0, "a cavallo dello zero dell'ascensione retta"),
    ],
)
def test_the_offset_agrees_with_the_true_separation(ra0, dec0, ra1, dec1, dove):
    """Lo scarto sul piano deve valere quello vero sulla sfera. La regola "differenza per il
    coseno della declinazione" e' esatta solo se i due punti stanno sullo stesso parallelo:
    ai lati del polo due punti a 1,48 gradi veri l'uno dall'altro venivano dichiarati a 2,32,
    **il 57% in piu'**, e un oggetto dentro l'inquadratura finiva dichiarato fuori."""
    est, nord = geo.tangent_offset_deg(ra0, dec0, ra1, dec1)
    assert math.hypot(est, nord) == pytest.approx(_true_sep_deg(ra0, dec0, ra1, dec1), rel=1e-3), (
        dove
    )


def test_the_other_half_of_the_sky_has_no_place_on_the_plane():
    """Il piano tangente copre un emisfero: dall'altra parte la proiezione si ribalterebbe e
    darebbe uno scarto piccolo a un oggetto lontanissimo. Li' si torna `None`, e `in_frame`
    risponde `False` -- che e' la verita'."""
    assert geo.tangent_offset_deg(100.0, 0.0, 280.0, 0.0) is None
    assert geo.in_frame(CAMPO, 280.0, 0.0) is False


def test_the_offset_survives_the_zero_of_right_ascension():
    """Due punti a mezzo grado l'uno dall'altro possono avere coordinate 359,8 e 0,2."""
    est, _ = geo.tangent_offset_deg(359.8, 0.0, 0.2, 0.0)
    assert est == pytest.approx(0.4, abs=1e-4)


# --- cosa c'e' davvero nella foto ------------------------------------------------------------


def test_inside_the_circle_is_not_the_same_as_inside_the_picture():
    """E' la ragione per cui il rettangolo esiste. Il cerchio circoscritto copre **1,7 volte**
    l'area del rettangolo su un sensore 3:2: un oggetto a 0,6 gradi a est sta nel cono ma
    **fuori dall'inquadratura**, perche' la mezza larghezza e' 0,556."""
    fuori = {"ra_deg": 100.6, "dec_deg": 0.0}
    assert geo.frame_radius_deg(CAMPO) > 0.6  # la foto arriva fin li'
    assert geo.in_frame(CAMPO, fuori["ra_deg"], fuori["dec_deg"]) is False

    dentro = {"ra_deg": 100.5, "dec_deg": 0.0}
    assert geo.in_frame(CAMPO, dentro["ra_deg"], dentro["dec_deg"]) is True


def test_the_rectangle_turns_with_the_frame():
    """La rotazione non e' un dettaglio: lo stesso oggetto e' dentro o fuori a seconda di come
    era orientata la camera. A 0 gradi il punto a 0,5 est sta dentro la larghezza (0,556); col
    sensore girato di 90 gradi quel lato diventa l'altezza (0,417), e il punto esce."""
    dritto = geo.in_frame(CAMPO, 100.5, 0.0)
    girato = geo.in_frame({**CAMPO, "rotation_deg": 90.0}, 100.5, 0.0)
    assert dritto is True and girato is False


def test_the_rectangle_turns_the_right_way_round():
    """A 90 gradi i due versi di rotazione sono indistinguibili -- il rettangolo si scambia i
    lati e basta -- quindi un test a 90 gradi non tiene ferma la convenzione. A 30 gradi si
    separano, ed e' li' che si vede: girando lo scarto **in avanti** invece che all'indietro,
    questo punto uscirebbe dall'inquadratura. La stessa mutazione equivale a ribaltare il segno
    dell'est: se il campo fosse specchiato, meta' delle pose ruotate direbbe il falso."""
    girato = {**CAMPO, "rotation_deg": 30.0}
    est, nord = geo.tangent_offset_deg(100.0, 0.0, 100.45, 0.30)
    assert (est, nord) == (pytest.approx(0.45, abs=1e-3), pytest.approx(0.30, abs=1e-3))
    assert geo.in_frame(girato, 100.45, 0.30) is True

    # lo stesso punto col campo girato dall'altra parte: fuori. E' la coppia che distingue.
    assert geo.in_frame({**CAMPO, "rotation_deg": -30.0}, 100.45, 0.30) is False


def test_a_big_object_counts_as_inside_even_with_its_centre_out():
    """Il pannello di un mosaico: l'oggetto e' piu' grande del campo, quindi il suo **centro**
    cade fuori mentre l'oggetto riempie la foto. Contare solo il centro direbbe che nella posa
    non c'e' niente, che e' il modo in cui si perde il soggetto di un mosaico."""
    assert geo.in_frame(CAMPO, 100.9, 0.0) is False  # un puntino li' non c'e'
    assert geo.in_frame(CAMPO, 100.9, 0.0, size_major_arcmin=120.0) is True  # 2 gradi: c'e' eccome


# Lo stesso campo, ma il solver non ha saputo dire come era girata la camera: matrice
# degenere. I lati ci sono, la rotazione no -- lo schema dice che succede a soluzione buona.
STORTO = {**CAMPO, "rotation_deg": None}


def test_without_the_rotation_it_falls_back_to_the_circle_and_says_so():
    """Senza sapere come e' orientato il sensore un rettangolo non si puo' disegnare. Li' non
    si scarta al buio: si usa il cerchio circoscritto, piu' largo, e chi legge lo sa."""
    assert geo.frame_shape(CAMPO) == "rectangle"
    assert geo.frame_shape(STORTO) == "circle"
    # 0,6 est: fuori dal rettangolo (mezza larghezza 0,556), dentro il cerchio (0,694)
    assert geo.in_frame(CAMPO, 100.6, 0.0) is False
    assert geo.in_frame(STORTO, 100.6, 0.0) is True


def test_without_any_side_nothing_gets_discarded():
    """Se del campo non si sa proprio niente -- header senza `NAXIS` e senza lati -- il cerchio
    non si puo' calcolare. Allora non si scarta: si tiene tutto. Un dato che manca a **noi** non
    e' una ragione per dire a qualcuno che nella sua foto non c'era."""
    cieco = {"ra_deg": 100.0, "dec_deg": 0.0, "scale_arcsec_px": None,
             "width_deg": None, "height_deg": None, "rotation_deg": None}  # fmt: skip
    assert geo.in_frame(cieco, 100.6, 0.0) is True
    assert geo.in_frame(cieco, 150.0, 0.0) is True


def test_on_the_circle_too_a_big_object_counts_as_inside():
    """La regola dell'oggetto piu' grande del campo vale in tutti e due i rami. Sul cerchio era
    scoperta: senza il raggio, il pannello di un mosaico su una posa senza rotazione perdeva il
    proprio soggetto -- e proprio li', dove del campo si sa meno, sbagliare costa di piu'."""
    assert geo.in_frame(STORTO, 100.9, 0.0) is False  # un puntino a 0,9: il cerchio arriva a 0,69
    assert geo.in_frame(STORTO, 100.9, 0.0, size_major_arcmin=120.0) is True  # due gradi: c'e'


def test_without_any_sky_nothing_can_be_said():
    """Una posa non risolta non ha campo: `in_frame` non deve inventare un `False`, che
    sarebbe uno scarto. Torna `None`, e chi chiama va per nome."""
    assert geo.in_frame({"ra_deg": None, "dec_deg": None}, 100.0, 0.0) is None
    assert geo.frame_shape({"ra_deg": None, "dec_deg": None}) is None


# --- la sovrapposizione: il filtro che sbaglia per difetto ------------------------------------


@pytest.mark.parametrize(
    ("sep", "size", "raggio", "atteso"),
    [
        (0.1, 10.0, 0.694, True),  # dentro e piccolo
        (2.0, 10.0, 0.694, False),  # lontano e piccolo: nella foto non c'e'
        (0.9, 120.0, 0.694, True),  # centro fuori ma l'oggetto e' grande: c'e' eccome
        (2.0, None, 0.694, True),  # dimensione ignota: non si scarta per un dato che ci manca
        (2.0, 10.0, None, True),  # campo ignoto: idem
    ],
)
def test_a_filter_that_discards_must_err_on_the_side_of_keeping(sep, size, raggio, atteso):
    """`overlaps_frame` decide chi resta in gara. Le sue tre guardie sono tutte necessarie:
    togliere un candidato per un dato che manca a **noi** e' il modo in cui si perde il
    soggetto giusto, e non se ne accorge nessuno."""
    assert geo.overlaps_frame(sep, size, raggio) is atteso
