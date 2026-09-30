"""Il Sole: le fasce del cielo lungo la notte, e i casi in cui non sono cinque.

Due mestieri, due banchi. **La regola** -- come una curva di altezze diventa fasce -- si prova su
curve **scritte a mano**: e' li' che stanno i casi che alle nostre latitudini non capitano mai, e
una prova che per vederli deve aspettare il cielo giusto non si scrive. **L'astronomia** si prova
su posti e date veri, poche volte, per sapere che le soglie sono attaccate al cielo giusto.

Le soglie vengono dall'USNO (`docs/domini/effemeridi.md`), non dalla cava.
"""

import datetime as dt

import pytest

from astrolog.ephemeris import ASTRO_DEG, CIVIL_DEG, NAUTICAL_DEG, RISESET_DEG, corpi
from astrolog.ephemeris.grid import night_grid
from astrolog.ephemeris.sun import altitudes, night_bands, sky_at, sky_bands

MEZZOGIORNO = dt.datetime(2026, 1, 15, 12, tzinfo=dt.timezone(dt.timedelta(hours=1)))


def istanti(quanti, passo_min=3):
    return [MEZZOGIORNO + dt.timedelta(minutes=passo_min * i) for i in range(quanti)]


def quali(fasce):
    return [f["kind"] for f in fasce]


# --- La regola: da una curva di altezze alle fasce. Niente cielo, solo numeri.


def test_the_bands_cover_the_window_with_no_gaps_and_no_overlaps():
    """Le fasce **coprono la finestra intera**, attaccate una all'altra.

    E' la promessa su cui poggia chi le disegna: sono rettangoli affiancati, e un buco
    sarebbe una striscia di fondo che non vuol dire niente -- indistinguibile da un dato
    mancante."""
    quando = istanti(9)
    fasce = sky_bands(quando, [5.0, 2.0, -1.0, -4.0, -8.0, -14.0, -20.0, -25.0, -30.0])

    assert fasce[0]["starts_at"] == quando[0]
    assert fasce[-1]["ends_at"] == quando[-1]
    for prima, dopo in zip(fasce, fasce[1:], strict=False):
        assert prima["ends_at"] == dopo["starts_at"]


def test_the_evening_goes_down_through_the_four_thresholds_in_order():
    """Scendendo, il cielo passa per **tutte e cinque** le fasce nell'ordine giusto: nessuna
    si salta e nessuna si ripete."""
    quando = istanti(9)
    fasce = sky_bands(quando, [5.0, 2.0, -1.0, -4.0, -8.0, -14.0, -20.0, -25.0, -30.0])

    assert quali(fasce) == ["day", "civil", "nautical", "astronomical", "dark"]


def test_a_night_that_never_leaves_the_dark_is_one_single_band():
    """La notte polare: il Sole non arriva mai alla soglia astronomica, e la finestra e'
    **una fascia sola**. Cinque fasce disegnate li' sarebbero cinque bugie."""
    quando = istanti(5)
    fasce = sky_bands(quando, [-28.0, -30.0, -31.0, -30.0, -28.0])

    assert quali(fasce) == ["dark"]
    assert (fasce[0]["starts_at"], fasce[0]["ends_at"]) == (quando[0], quando[-1])


def test_a_window_that_never_leaves_the_day_is_one_single_band():
    """Il giorno polare, l'altro estremo: il Sole non tramonta, e non c'e' nessun buio da
    mostrare. Zero non e' un buco: e' una risposta."""
    quando = istanti(5)
    fasce = sky_bands(quando, [10.0, 8.0, 6.0, 8.0, 10.0])

    assert quali(fasce) == ["day"]


def test_the_dark_that_begins_and_does_not_end_is_measured_to_the_edge():
    """**Il terzo caso**, che non e' polare e non e' normale: il buio comincia dentro la
    finestra e non finisce. Nel progetto di prima e' stato scoperto dopo, e contarlo come
    "niente buio" su una notte buia quasi tutta e' il difetto che ne era uscito. L'ultima
    fascia arriva al bordo della finestra, non si tronca prima."""
    quando = istanti(5)
    fasce = sky_bands(quando, [-14.0, -17.0, -19.0, -22.0, -25.0])

    assert quali(fasce) == ["astronomical", "dark"]
    assert fasce[-1]["ends_at"] == quando[-1]


def test_a_window_that_starts_already_dark_has_no_invented_beginning():
    """L'altra meta' dello stesso caso: la finestra comincia **gia'** al buio. La prima
    fascia parte dal primo istante, non da un attraversamento che non c'e' stato."""
    quando = istanti(5)
    fasce = sky_bands(quando, [-25.0, -22.0, -19.0, -16.0, -13.0])

    assert quali(fasce) == ["dark", "astronomical"]
    assert fasce[0]["starts_at"] == quando[0]


def test_a_boundary_falls_between_the_two_samples_that_straddle_it():
    """Il confine si **interpola**, non si aggancia al campione piu' vicino: il passo della
    griglia decide quanto fitta e' la ricerca, non di quanto si sbaglia. Qui il Sole passa da
    -5 a -7 in tre minuti, e la soglia civile sta a meta'.

    **Tre campioni, non due**: il confine si interpola fra il campione e il **successivo**, e con
    due soli il successivo e' anche l'ultimo -- quindi un conto fatto sull'intera finestra invece
    che su un passo darebbe lo stesso numero, e la prova sarebbe verde per il motivo sbagliato."""
    quando = istanti(3)
    fasce = sky_bands(quando, [-5.0, -7.0, -9.0])

    confine = fasce[0]["ends_at"]
    assert confine == quando[0] + dt.timedelta(minutes=1.5)


def test_a_step_that_skips_a_band_still_names_it():
    """Un salto che scavalca una fascia intera non la cancella: fra i due campioni ci sono
    due confini, e la fascia in mezzo esiste anche se nessun campione ci e' caduto dentro.
    Non capita con la griglia vera -- il Sole scende di poco meno di un grado ogni tre
    minuti, al massimo -- ma una regola che vale solo a passo fitto non e' una regola."""
    quando = istanti(2, passo_min=120)
    fasce = sky_bands(quando, [-4.0, -14.0])

    assert quali(fasce) == ["civil", "nautical", "astronomical"]


def test_a_night_goes_down_and_comes_back_up_through_the_same_bands():
    """La forma vera di una notte: il Sole scende, tocca il fondo, e risale.

    Le fasce si leggono a **coppie di campioni consecutivi**, in ordine: confrontando un campione
    con quello sbagliato -- il precedente invece del successivo -- la sequenza si scompone, e
    nessuna delle prove a curva monotona se ne accorgerebbe."""
    quando = istanti(3, passo_min=240)

    fasce = sky_bands(quando, [-4.0, -20.0, -4.0])

    assert quali(fasce) == [
        "civil",
        "nautical",
        "astronomical",
        "dark",
        "astronomical",
        "nautical",
        "civil",
    ]


def test_without_two_samples_there_are_no_bands():
    """Niente fasce inventate su una finestra che non c'e'."""
    assert sky_bands([], []) == []
    assert sky_bands(istanti(1), [5.0]) == []


def test_the_thresholds_are_the_ones_the_contract_cites():
    """Le quattro soglie sono quelle dell'USNO, e stanno in una casa sola: qui si guarda che
    siano quelle, perche' un numero cambiato a mano non farebbe cadere nient'altro."""
    assert (RISESET_DEG, CIVIL_DEG, NAUTICAL_DEG, ASTRO_DEG) == (-0.833, -6.0, -12.0, -18.0)


@pytest.mark.parametrize(
    ("dove", "quando", "attese"),
    [
        # Vicenza a meta' gennaio: una notte qualunque alle nostre latitudini, con tutte e cinque
        # le fasce due volte -- si scende la sera e si risale la mattina.
        (
            (45.55, 11.55),
            dt.datetime(2026, 1, 15, 12, tzinfo=dt.timezone(dt.timedelta(hours=1))),
            9,
        ),
        # Tromso al solstizio d'estate: il Sole non tramonta, e la finestra e' tutta giorno.
        (
            (69.65, 18.96),
            dt.datetime(2026, 6, 21, 12, tzinfo=dt.timezone(dt.timedelta(hours=2))),
            1,
        ),
    ],
)
def test_the_sky_of_a_real_place_has_the_bands_that_place_really_has(dove, quando, attese):
    """L'astronomia, provata dove si vede: a meta' strada le fasce sono cinque e tornano, al
    circolo polare d'estate e' **una sola**. Le soglie senza il cielo giusto dietro sarebbero
    quattro numeri qualunque."""
    griglia = night_grid(quando, hours=24, step_min=3)
    fasce = sky_bands(griglia, altitudes(griglia, *dove))

    assert len(fasce) == attese


def test_a_real_polar_night_never_sees_the_day():
    """Longyearbyen a meta' gennaio: **il giorno non c'e'**, e nemmeno il crepuscolo civile -- il
    Sole a mezzogiorno arriva sui dieci gradi sotto l'orizzonte e non piu' su. Il buio c'e',
    in mezzo, ed e' la fascia piu' lunga.

    Vale la pena provarlo su un posto vero perche' e' il caso in cui una tela costruita sugli
    attraversamenti sbaglia: il tramonto non c'e', e da li' non si capisce se e' notte o se e'
    giorno."""
    quando = dt.datetime(2026, 1, 15, 12, tzinfo=dt.timezone(dt.timedelta(hours=1)))
    griglia = night_grid(quando, hours=24, step_min=3)

    fasce = sky_bands(griglia, altitudes(griglia, 78.22, 15.65))

    assert "day" not in quali(fasce)
    assert "civil" not in quali(fasce)
    assert quali(fasce)[len(fasce) // 2] == "dark"


def test_the_bands_come_back_in_the_timezone_they_were_asked_in():
    """Gli istanti tornano **nel fuso da cui sono stati chiesti**, non in UTC.

    Chi li mostra taglia l'ora dalla stringa (`i18n.oraDelSito`), quindi un istante in UTC
    diventerebbe a schermo l'ora di Greenwich: un'ora sbagliata d'inverno e due d'estate, su ogni
    bordo di fascia e nella frase del buio. E' la gemella della prova della Luna."""
    inizio = dt.datetime(2026, 1, 15, 12, tzinfo=dt.timezone(dt.timedelta(hours=1)))

    fasce = night_bands(inizio, 45.55, 11.55, hours=24)

    assert fasce[0]["starts_at"] == inizio
    for fascia in fasce:
        assert fascia["starts_at"].utcoffset() == inizio.utcoffset(), fascia
        assert fascia["ends_at"].utcoffset() == inizio.utcoffset(), fascia


def test_the_sun_is_asked_once_for_the_whole_night_not_once_per_sample():
    """Una chiamata sola per tutta la griglia, come per la Luna.

    Misurato chiedendolo campione per campione: **1.435 ms contro 56** su una notte a Vicenza,
    cioe' un secondo e mezzo dentro `GET /tonight`. La Luna ha la sua guardia e passa da
    `get_body`; il Sole passa da `get_sun`, e senza questa riga meta' della regola era scoperta."""
    quante = 0
    vera = corpi.get_sun

    def conta(*a, **k):
        nonlocal quante
        quante += 1
        return vera(*a, **k)

    corpi.get_sun = conta
    try:
        night_bands(MEZZOGIORNO, 45.55, 11.55, hours=24)
    finally:
        corpi.get_sun = vera

    assert quante == 1, quante


def test_a_step_that_climbs_across_two_bands_names_them_in_the_right_order():
    """Salendo, i confini escono **al rovescio** di quando si scende.

    E' l'altra meta' di `test_a_step_that_skips_a_band_still_names_it`, e senza di lei un ordine
    fisso passava: da -20 a -4 uscivano fasce con gli istanti al contrario -- `civil` da 13:45 a
    13:00, cioe' **meno quarantacinque minuti** -- e nessuna prova cadeva."""
    quando = istanti(2, passo_min=120)

    fasce = sky_bands(quando, [-20.0, -4.0])

    assert quali(fasce) == ["dark", "astronomical", "nautical", "civil"]
    for fascia in fasce:
        assert fascia["ends_at"] > fascia["starts_at"], fascia


def test_the_sun_asked_the_fast_way_agrees_with_the_slow_one():
    """Le due strade per il Sole danno la stessa altezza, e la veloce si puo' tenere.

    E' la macchina del ramo che `corpi.altezze` prende per il Sole: **125 ms contro 38** per una
    differenza che qui si misura invece di scriverla in un commento. La soglia e' un centesimo di
    grado -- trentasei secondi d'arco -- che e' mille volte meno del passo fra due soglie di
    crepuscolo: se le due strade divergessero davvero, si vedrebbe molto prima."""
    from astropy.coordinates import AltAz, EarthLocation, get_body
    from astropy.time import Time

    quando = night_grid(MEZZOGIORNO, hours=24, step_min=60)
    dove = EarthLocation(lat=45.55, lon=11.55)
    momenti = Time([corpi.quando(i) for i in quando])
    lenta = get_body("sun", momenti, dove).transform_to(AltAz(obstime=momenti, location=dove))

    veloce = altitudes(quando, 45.55, 11.55)

    scarti = [abs(a - float(b)) for a, b in zip(veloce, lenta.alt.deg, strict=True)]
    assert max(scarti) < 0.01, max(scarti)


def test_the_sky_at_an_instant_is_the_band_that_holds_it():
    """Chi vuole solo in che cielo cade un'ora non paga la notte campionata minuto per minuto, e
    legge la stessa cosa: la fascia che contiene quell'istante."""
    fasce = night_bands(MEZZOGIORNO, 45.87, 11.51, hours=24)
    ore = [MEZZOGIORNO + dt.timedelta(minutes=30 + 60 * h) for h in range(24)]
    attese = [next(f["kind"] for f in fasce if f["starts_at"] <= o < f["ends_at"]) for o in ore]
    assert sky_at(ore, 45.87, 11.51) == attese
    assert {"day", "dark"} <= set(attese)
