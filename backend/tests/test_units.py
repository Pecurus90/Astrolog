"""Le unita' e i numeri: la scala dal corredo, il raggio di un oggetto, il rumore della float32
tolto dove il dato entra. Portati da old/ (numeri dell'archivio reale)."""

import pytest

from astrolog import units
from astrolog.units import (
    F32_SIGNIFICANT_DIGITS,
    SQM_MAX,
    SQM_MIN,
    believable_sqm,
    bortle_of,
    field_deg,
    focal_buckets,
    scale_arcsec_px,
    sqm_from_brightness,
    sqm_of_bortle,
    strip_float32_noise,
)


def test_the_scale_from_the_rig():
    assert scale_arcsec_px(3.76, 530.0) == pytest.approx(3.76 / 530.0 * 206.265)
    assert scale_arcsec_px(None, 530.0) is None and scale_arcsec_px(3.76, 0) is None


def test_the_radius_of_an_object_is_half_its_size_in_degrees():
    """Il catalogo da' la dimensione maggiore in primi d'arco; chi confronta col campo vuole il
    raggio in gradi."""
    assert units.radius_deg(60.0) == pytest.approx(0.5)
    assert units.radius_deg(None) == 0.0 and units.radius_deg(0) == 0.0


def test_float32_noise():
    assert strip_float32_noise(4.28999996185303) == 4.29
    assert strip_float32_noise(-10.1000003814697) == -10.1
    assert strip_float32_noise(3.4000000953674316) == 3.4
    for v in (3.76, 0.0, -5.5, 1234.5, 1e-9, 1.234567, 206.2648):
        assert strip_float32_noise(v) == v
    assert strip_float32_noise(None) is None
    assert F32_SIGNIFICANT_DIGITS == 7
    assert strip_float32_noise(1.23456789) == 1.234568


def test_focal_jitter_collapses_to_one_group():
    m = focal_buckets([559.0, 560.0, 561.0])
    assert m[559.0] == m[560.0] == m[561.0] == 560.0  # la mediana dei distinti


def test_focal_distinct_configurations_stay_apart():
    m = focal_buckets([300.0, 560.0])
    assert m[300.0] == 300.0 and m[560.0] == 560.0


def test_focal_buckets_do_not_depend_on_the_order():
    assert focal_buckets([561.0, 300.0, 559.0, 560.0]) == focal_buckets(
        [300.0, 559.0, 560.0, 561.0]
    )


def test_focal_boundary_of_five_percent():
    assert (
        focal_buckets([580.0, 600.0])[580.0] == focal_buckets([580.0, 600.0])[600.0]
    )  # 600 <= 609
    apart = focal_buckets([580.0, 620.0])
    assert apart[580.0] != apart[620.0]  # 620 > 609


def test_focal_anchor_stops_the_chain():
    """Senza l'ancoraggio al minimo 560 -> 570 -> 590 finirebbero in un gruppo solo."""
    m = focal_buckets([560.0, 570.0, 590.0])
    assert m[560.0] == m[570.0] and m[560.0] != m[590.0]


def test_focal_unknown_and_nonsense_stay_out():
    assert list(focal_buckets([None, 0.0, -5.0, 300.0])) == [300.0]
    assert focal_buckets([]) == {}


def test_the_field_in_degrees_comes_from_the_pixels_and_the_scale():
    """Il campo inquadrato e' cio' che rende veloce il solver: si
    ricava da quanti pixel ha il sensore e da quanto vale un pixel."""
    # 4176 pixel a 0,5085"/px = 0,59 gradi: e' il frame vero su cui la misura e' stata fatta
    assert field_deg(4176, 0.5085) == pytest.approx(0.59, abs=0.005)
    assert field_deg(1000, 3.6) == pytest.approx(1.0)

    # un dato che manca non si inventa: chi non sa il campo lo fa cercare al solver
    for pixel, scala in ((None, 1.0), (0, 1.0), (100, None), (100, 0), (-10, 1.0), (100, -1)):
        assert field_deg(pixel, scala) is None, (pixel, scala)


def test_a_sky_outside_the_scale_is_not_a_sky():
    """Sotto la soglia c'e' un piazzale illuminato, sopra non esiste un posto sulla Terra: un
    servizio che risponde fuori da li' ha risposto un guasto, e un guasto non si salva."""
    assert believable_sqm(21.3) == 21.3
    assert believable_sqm(SQM_MIN) == SQM_MIN
    assert believable_sqm(SQM_MAX) == SQM_MAX
    for assurdo in (8.34, 9.99, 23.01, 40.0, -3.0):
        assert believable_sqm(assurdo) is None, assurdo
    assert believable_sqm(None) is None


def test_bortle_from_sky_brightness():
    """La classe di cielo si RICAVA dalla luminosita', non si memorizza. I confini sono una
    consuetudine e il codice lo dice; qui si prova che la scala e' monotona e che cade dove la
    tabella dei siti di astrofotografia la mette -- e' il numero con cui l'utente confrontera'
    il nostro, e una scala spostata di due classi glielo farebbe sembrare sbagliato."""
    assert bortle_of(22.0) == 1 and bortle_of(21.8) == 1
    assert bortle_of(21.7) == 2 and bortle_of(21.5) == 3
    assert bortle_of(21.2) == 4 and bortle_of(20.0) == 5
    assert bortle_of(18.8) == 6 and bortle_of(18.2) == 7
    assert bortle_of(17.5) == 8 and bortle_of(16.5) == 9
    # The source's own floors (class 4 from 20.8, 5 from 19.25), and its 4.5 read as 5: never
    # more generous than the number the user will compare ours with.
    assert bortle_of(20.8) == 4 and bortle_of(20.79) == 5 and bortle_of(20.5) == 5
    assert bortle_of(19.25) == 5 and bortle_of(19.24) == 6
    classi = [bortle_of(s / 100) for s in range(1600, 2210)]
    assert classi == sorted(classi, reverse=True)  # piu' buio = classe piu' bassa, sempre
    assert bortle_of(None) is None


def test_the_sky_scale_goes_both_ways():
    """Chi sceglie il cielo dall'elenco dei nove ritrova la sua classe: andata e ritorno
    stabili, o l'utente vedrebbe cambiare la scelta appena fatta."""
    for classe in range(1, 10):
        assert bortle_of(sqm_of_bortle(classe)) == classe
    assert sqm_of_bortle(1) > sqm_of_bortle(9)  # la classe 1 e' il cielo piu' scuro


def test_sky_brightness_becomes_a_measurable_number():
    """Il servizio da' la luce ARTIFICIALE in millicandele per metro quadro: il cielo vero e'
    quella piu' il fondo naturale, e si legge in magnitudini per arcosecondo quadrato."""
    assert sqm_from_brightness(0.0) == pytest.approx(21.98, abs=0.01)  # solo il cielo naturale
    assert sqm_from_brightness(1.0) == pytest.approx(19.91, abs=0.01)
    assert sqm_from_brightness(100.0) == pytest.approx(15.08, abs=0.01)
    assert sqm_from_brightness(None) is None
    assert sqm_from_brightness(-1.0) is None  # una luminosita' negativa non e' un dato
    # due decimali, come il cielo scelto dalla scala: un terzo non e' una misura, e si leggerebbe
    for luce in (0.0, 1.0, 0.37, 100.0):
        assert sqm_from_brightness(luce) == round(sqm_from_brightness(luce), 2)
    # piu' luce artificiale, cielo piu' chiaro: la scala e' invertita e non deve sfuggire
    assert sqm_from_brightness(10.0) < sqm_from_brightness(1.0)


def test_two_points_across_zero_hours_are_close():
    """Il salto dell'ascensione retta a 0/360: due punti a 0,5 e 359,5 gradi distano UN grado,
    non trecentocinquantanove. E' il caso per cui la separazione passa dai versori invece che
    dalle differenze di coordinate -- e senza questa prova la formula piana passava la suite
    intera, perche' nessun bersaglio dei test sta a cavallo delle zero ore."""
    assert units.angular_separation_deg(0.5, 0.0, 359.5, 0.0) == pytest.approx(1.0, abs=1e-9)
    assert units.angular_separation_deg(359.9, 20.0, 0.1, 20.0) == pytest.approx(0.188, abs=1e-3)


def test_the_separation_of_a_point_from_itself_is_zero():
    """Due versori paralleli danno un prodotto scalare come 1.0000000000000002, e `acos` di
    quello solleva: il taglio a [-1, 1] non e' prudenza, e' cio' che tiene in piedi la ricerca
    per cono su ogni oggetto che coincide col puntamento."""
    assert units.angular_separation_deg(83.82, -5.39, 83.82, -5.39) == 0.0
    assert units.separation_deg_from_cosine(1.0000000000000002) == 0.0
    assert units.separation_deg_from_cosine(-1.0000000000000002) == pytest.approx(180.0)


def test_the_separation_knows_the_poles_and_the_antipodes():
    """I due estremi, coi valori che si sanno a mente: il polo dista 90 gradi dall'equatore, e
    due punti opposti 180."""
    assert units.angular_separation_deg(0.0, 90.0, 123.0, 0.0) == pytest.approx(90.0)
    assert units.angular_separation_deg(0.0, 0.0, 180.0, 0.0) == pytest.approx(180.0)


def test_the_separation_matches_the_real_pair_the_catalog_knows():
    """M 81 e M 82 distano 0,6148 gradi: e' il numero su cui e' tarato il giudizio di
    ambiguita' di `identify_score`, e viene da un'altra strada che questa formula."""
    assert units.angular_separation_deg(148.8882, 69.0653, 148.9684, 69.6797) == pytest.approx(
        0.6148, abs=5e-4
    )


def test_the_pixel_from_the_sky_needs_every_piece():
    """Senza focale o senza binning non si ricava niente: un dato che manca non vale 1."""
    from astrolog.units import pixel_um_from_scale

    assert pixel_um_from_scale(1.385, 560.0, 1) is not None
    assert pixel_um_from_scale(1.385, None, 1) is None
    assert pixel_um_from_scale(1.385, 560.0, None) is None
    assert pixel_um_from_scale(None, 560.0, 1) is None
