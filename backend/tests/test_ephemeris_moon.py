"""Che luna fa stanotte: fase, quanto e' illuminata, sorgere, tramontare, quanto sale e la curva
con cui ci arriva.

Portate da `old/`, che le aveva sul giro intero di una rotta; qui difendono **una regola per
prova**, e le regole sono quelle scritte nell'intestazione del modulo.

Le date sono **nel futuro** apposta: e' li' che astropy, senza l'assetto offline, prova a
scaricare i dati di orientamento della Terra e scoppia -- su una data passata la rete non le
serve, e una prova che gira solo su ieri non dimostra niente.
"""

import datetime as dt
import inspect
import zoneinfo

import pytest
from astropy.time import Time

from astrolog.ephemeris import (
    GRID_STEP_MIN,
    MAX_DECLINATION_DEG,
    RISESET_DEG,
    TRACK_STEP_MIN,
    bodies,
    moon,
)
from astrolog.ephemeris.grid import first_crossing, night_grid

# L'avviso che astropy da' sulle date oltre i suoi dati di orientamento della Terra: e' **cio'
# che abbiamo chiesto** con `auto_max_age = None`, e riguarda una precisione di arcosecondi che
# per sorgere e tramontare non si vede. Si dichiara qui invece di lasciarlo scorrere fra i rossi.
pytestmark = pytest.mark.filterwarnings("ignore:Tried to get polar motions:")

# Un posto vero, e uno dove la Luna puo' non sorgere affatto.
CASA = (45.5455, 11.5354)  # Vicenza
POLO = (78.2232, 15.6267)  # Longyearbyen, sopra il circolo polare
QUANDO = dt.datetime(2027, 3, 14, 12, 0, tzinfo=dt.UTC)  # mezzogiorno UTC, nel futuro


def test_importing_the_ephemeris_disarms_the_download():
    """**L'offline ha una macchina.** Era una promessa scritta in un'intestazione e in un
    contratto, e niente la difendeva: su una macchina con la rete -- cioe' in CI -- togliere le
    tre righe di `ephemeris/__init__.py` lasciava tutte le prove verdi.

    Qui si guarda l'assetto, non il risultato: il risultato dipende da quanto sono freschi i dati
    impacchettati con astropy, e una prova che dipende da quello dice cose diverse a sei mesi di
    distanza. Il recinto della rete per tutta la suite sta in `conftest.py`, che e' la sua casa.

    Due delle tre righe le ho viste rosse togliendole. La terza -- l'effemeride incorporata --
    **non si puo' vedere rossa oggi**, perche' `builtin` e' anche il valore di partenza di
    astropy: e' un chiodo, non una guardia, e varra' il giorno che qualcuno altrove ne scelga
    un'altra. Lo dico invece di lasciarlo credere provato."""
    from astropy.coordinates import solar_system_ephemeris
    from astropy.utils import iers

    assert iers.conf.auto_download is False
    assert iers.conf.auto_max_age is None
    assert solar_system_ephemeris.get() == "builtin"


def test_rise_and_set_are_told_for_a_normal_place():
    """Da un posto normale la Luna sorge e tramonta nelle ventiquattro ore, e i due istanti
    stanno dentro la finestra chiesta."""
    fine = QUANDO + dt.timedelta(hours=24)
    notte = moon.night_track(QUANDO, *CASA, hours=24)
    sorge, tramonta = notte.rise, notte.set

    assert sorge is not None and tramonta is not None
    for quando in (sorge, tramonta):
        assert QUANDO <= quando <= fine, quando


def test_a_moon_that_never_rises_is_a_fact_not_an_error():
    """Sopra il circolo polare capita che la Luna non attraversi l'orizzonte in tutta la finestra:
    e' un fatto, e si dice con `None`. Inventare un orario li' vorrebbe dire scrivere un numero
    che non esiste -- e chi legge non ha modo di accorgersene."""
    notte = moon.night_track(dt.datetime(2027, 6, 21, 12, 0, tzinfo=dt.UTC), *POLO, hours=24)

    assert notte.rise is None or notte.set is None, notte


def test_the_times_come_back_with_their_timezone():
    """Un istante senza fuso e' la data del server, non quella della notte dell'utente: e' il
    difetto che l'archivio ha gia' pagato una volta. Cio' che esce di qui porta UTC scritto, e chi
    lo mostra lo porta nel fuso del sito."""
    sorge = moon.night_track(QUANDO, *CASA, hours=24).rise

    assert sorge is not None
    assert sorge.tzinfo is not None


def test_asking_for_a_naive_instant_is_refused():
    """Un istante senza fuso non si indovina: `astropy` lo leggerebbe come UTC in silenzio, e su
    un sito in Arizona la notte sarebbe quella sbagliata di mezza giornata."""
    with pytest.raises(ValueError, match="fuso"):
        moon.phase(dt.datetime(2027, 3, 14, 12, 0))


def test_the_grid_covers_the_window_it_promises():
    """La griglia arriva **fino in fondo**: estremi inclusi. Una griglia che si ferma un passo
    prima perde l'ultimo attraversamento, e il tramonto sparisce senza che niente cada."""
    griglia = night_grid(QUANDO, hours=24, step_min=3)

    assert len(griglia) == 24 * 60 // 3 + 1
    assert griglia[0] == QUANDO
    assert griglia[-1] == QUANDO + dt.timedelta(hours=24)


def test_the_grid_covers_real_hours_even_when_the_clock_jumps():
    """Ventiquattro ore **vere**, anche la notte in cui l'orologio salta.

    Sommare un `timedelta` a un istante con un fuso vero fa aritmetica da orologio da parete: in
    primavera la griglia copriva 23 ore e **tornava indietro** di 57 minuti, in autunno ne
    copriva 25. Quel salto all'indietro creava un attraversamento che non esiste, e il tramonto
    usciva sbagliato di otto ore, con un orario che quella notte non era mai esistito.

    Le prove che c'erano usavano tutte UTC, dove l'ora legale non c'e': e' per questo che il
    difetto e' passato."""
    roma = zoneinfo.ZoneInfo("Europe/Rome")
    for giorno in (dt.date(2027, 3, 27), dt.date(2027, 10, 30)):  # le due notti del cambio
        inizio = dt.datetime(giorno.year, giorno.month, giorno.day, 12, tzinfo=roma)
        griglia = night_grid(inizio, hours=24, step_min=3)

        durata = (griglia[-1] - griglia[0]).total_seconds() / 3600
        assert durata == 24, (giorno, durata)
        # e non torna mai indietro: un passo all'indietro e' un attraversamento inventato
        assert all(b > a for a, b in zip(griglia, griglia[1:], strict=False)), giorno


def test_the_times_are_read_in_the_timezone_they_were_asked_in():
    """Il conto sta in UTC, ma l'ora che l'utente legge e' quella del suo sito: chi chiede da Roma
    riceve l'ora di Roma, con l'offset giusto per quel giorno."""
    roma = zoneinfo.ZoneInfo("Europe/Rome")
    inizio = dt.datetime(2027, 7, 15, 12, tzinfo=roma)  # ora legale: +02:00

    sorge = moon.night_track(inizio, *CASA, hours=24).rise

    assert sorge is not None
    assert sorge.utcoffset() == dt.timedelta(hours=2), sorge


def test_a_grid_without_a_timezone_is_refused():
    """Una griglia senza fuso non si sa dove comincia: ripiegare su UTC vorrebbe dire far nascere
    la notte di un sito in Arizona a mezzogiorno di Greenwich, in silenzio."""
    with pytest.raises(ValueError, match="fuso"):
        night_grid(dt.datetime(2027, 3, 14, 12), hours=24, step_min=3)


def test_the_window_and_the_step_have_no_fallback_value():
    """Ne' quante ore ne' il passo hanno un valore di riserva: scritto qui un ventiquattro di
    comodo, il giorno che il chiamante lo calcola bene questo mentirebbe in silenzio -- ed e'
    esattamente cio' che e' successo, perche' la notte del cambio d'ora non dura ventiquattro ore.

    La regola sta scritta in due intestazioni e non la difendeva niente: rimettere i valori di
    partenza lasciava la suite verde."""
    for funzione, senza_riserva in (
        (night_grid, ("hours", "step_min")),
        (moon.night_track, ("hours",)),
    ):
        parametri = inspect.signature(funzione).parameters
        for nome in senza_riserva:
            assert parametri[nome].default is inspect.Parameter.empty, (funzione, nome)


def test_the_sky_is_asked_once_for_the_whole_night_not_once_per_sample():
    """Le altezze si chiedono ad astropy **in un colpo solo**: una chiamata per campione sarebbero
    quattrocentottantuno conversioni di coordinate per una notte, e chi riscrivesse questo ciclo
    a uno a uno avrebbe solo una suite piu' lenta, senza che niente cada."""
    quante = 0
    vera = bodies.get_body

    def conta(*a, **k):
        nonlocal quante
        quante += 1
        return vera(*a, **k)

    bodies.get_body = conta
    try:
        moon.night_track(QUANDO, *CASA, hours=24)
    finally:
        bodies.get_body = vera

    assert quante == 1, quante


def test_the_crossing_is_interpolated_not_snapped_to_the_grid():
    """L'istante si **interpola** fra i due campioni: preso quello piu' vicino, l'orario
    sbaglierebbe fino a meta' passo -- un minuto e mezzo su una griglia da tre minuti, che a
    schermo e' un orario diverso."""
    istanti = night_grid(QUANDO, hours=1, step_min=30)  # tre campioni: 0, 30, 60 minuti
    # una retta che attraversa lo zero a un quarto del secondo intervallo
    quando = first_crossing(istanti, [10.0, 2.0, -6.0], 0.0, "down")

    assert quando is not None
    minuti = (quando - QUANDO).total_seconds() / 60
    assert 37 < minuti < 38, minuti


def test_no_crossing_is_none_not_an_invented_instant():
    """Una curva che non attraversa mai la soglia non ha un istante: `None`, non il primo
    campione. E' lo stesso degrado onesto della Luna circumpolare."""
    istanti = night_grid(QUANDO, hours=1, step_min=30)

    assert first_crossing(istanti, [10.0, 20.0, 30.0], 0.0, "down") is None


# test-tolto: test_rise_set_uses_the_horizon_of_the_almanacs_not_zero -- stessa regola, nome
# aggiornato perche' la funzione che nominava adesso si chiama night_track
def test_the_rising_uses_the_horizon_of_the_almanacs_not_zero():
    """La soglia con cui si dice sorta una Luna e' **meno 0,833 gradi** -- rifrazione dell'aria
    piu' raggio del disco, la convenzione degli almanacchi -- non lo zero geometrico.

    Senza questa riga si poteva portare `RISESET_DEG` a zero, o a meno cinque, e **tutte** le
    prove restavano verdi: quella sotto prova che `first_crossing` onori una soglia, non che
    `night_track` le passi quella giusta. A schermo sarebbe un orario spostato di qualche minuto,
    che nessuno distingue da uno buono."""
    assert RISESET_DEG == -0.833

    # e il sorgere cade dove l'altezza vale quella soglia, non dove vale zero
    inizio = dt.datetime(2027, 3, 14, 12, tzinfo=dt.UTC)
    sorge = moon.night_track(inizio, *CASA, hours=24).rise
    assert sorge is not None
    quanto_e_alta = moon.altitudes([sorge], *CASA)[0]
    assert abs(quanto_e_alta - RISESET_DEG) < 0.02, quanto_e_alta


def test_the_threshold_is_not_always_zero():
    """La soglia vera non e' zero: e' **meno 0,833 gradi**, l'orizzonte corretto per la rifrazione
    dell'aria e per il raggio del disco. Provando solo con zero, sommare invece di sottrarre la
    soglia da' lo stesso identico risultato -- e il difetto resta invisibile finche' qualcuno non
    guarda l'ora del tramonto e la trova spostata di qualche minuto."""
    istanti = night_grid(QUANDO, hours=1, step_min=30)
    # una curva che scende da +2 a -2: incrocia lo zero a meta', ma la soglia vera un po' dopo
    a_zero = first_crossing(istanti, [2.0, 0.0, -2.0], 0.0, "down")
    alla_soglia = first_crossing(istanti, [2.0, 0.0, -2.0], -0.833, "down")

    assert a_zero is not None and alla_soglia is not None
    assert alla_soglia > a_zero, (a_zero, alla_soglia)
    # e la differenza e' quella che la soglia impone, non un caso: 0,833 gradi su 2 per mezz'ora
    minuti = (alla_soglia - a_zero).total_seconds() / 60
    assert 12 < minuti < 13, minuti


def test_going_up_and_going_down_are_two_different_questions():
    """Sorgere e tramontare sono due direzioni, e una curva che sale **non** e' un tramonto. Senza
    questa riga, scambiare il verso di uno dei due confronti lascerebbe la suite verde: la Luna
    'tramonterebbe' quando sorge, e a schermo i due orari sarebbero invertiti."""
    istanti = night_grid(QUANDO, hours=1, step_min=30)
    sale = [-5.0, 0.0, 5.0]
    scende = [5.0, 0.0, -5.0]

    assert first_crossing(istanti, sale, -0.833, "up") is not None
    assert first_crossing(istanti, sale, -0.833, "down") is None
    assert first_crossing(istanti, scende, -0.833, "down") is not None
    assert first_crossing(istanti, scende, -0.833, "up") is None


def test_a_sample_sitting_exactly_on_the_threshold_still_counts_as_crossed():
    """Un campione che cade **esattamente** sulla soglia e' gia' attraversato, non ancora da
    attraversare: e' il bordo dove un confronto stretto invece che largo perde l'istante, e il
    sorgere sparisce per il tempo di un passo."""
    istanti = night_grid(QUANDO, hours=1, step_min=30)

    # sale e si ferma sulla soglia: e' sorta
    assert first_crossing(istanti, [-5.0, -0.833, -0.833], -0.833, "up") is not None
    # scende e si ferma sulla soglia: e' tramontata
    assert first_crossing(istanti, [5.0, -0.833, -0.833], -0.833, "down") is not None


def test_the_highest_point_of_the_night_is_told_with_its_instant():
    """Quanto sale la Luna stanotte e' il punto piu' alto della notte: **quando**, e a quanti gradi.
    Lo legge chi guarda il grafico in barra e chi aprira' il pannello.

    Si confronta con il massimo delle altezze sulla stessa griglia: prendere il minimo, o il
    primo campione, o l'altezza senza il suo istante lascerebbe un numero verosimile a schermo --
    16 gradi invece di 56 nessuno lo sa distinguere guardando."""
    notte = moon.night_track(QUANDO, *CASA, hours=24)
    istanti = night_grid(QUANDO, hours=24, step_min=GRID_STEP_MIN)
    alte = moon.altitudes(istanti, *CASA)

    piu_alto = notte.highest
    assert abs(piu_alto.altitude_deg - max(alte)) < 0.05, (piu_alto, max(alte))
    assert piu_alto.at == istanti[alte.index(max(alte))].astimezone(QUANDO.tzinfo)


def test_a_moon_that_never_rises_still_has_a_highest_point():
    """Una Luna che non attraversa mai l'orizzonte non ha un'ora di sorgere -- ma **sale lo
    stesso**, sotto l'orizzonte, e il suo punto piu' alto esiste e si dice.

    Senza questa riga il punto piu' alto poteva sparire insieme agli orari, e chi guarda sopra il
    circolo polare non leggerebbe piu' niente invece di leggere quanto poco sale."""
    notte = moon.night_track(dt.datetime(2027, 6, 21, 12, 0, tzinfo=dt.UTC), *POLO, hours=24)

    assert notte.rise is None or notte.set is None, notte
    assert notte.highest.at is not None
    assert isinstance(notte.highest.altitude_deg, float)


def test_the_curve_spans_the_whole_night_including_its_last_instant():
    """La curva arriva **fino in fondo alla notte**: il grafico che la disegna deve chiudere dove
    la notte chiude, o l'ultima mezz'ora sparisce dal disegno senza che niente cada.

    Le ore non sono un numero tondo apposta: con una finestra che non e' un multiplo del passo
    della curva, prendere un campione ogni tot **salta l'ultimo**. Con le finestre vere (23, 24,
    25 ore) il conto torna da solo, quindi una prova su quelle sarebbe verde comunque e non
    proverebbe niente."""
    ore = 23.1
    notte = moon.night_track(QUANDO, *CASA, hours=ore)
    istanti = night_grid(QUANDO, hours=ore, step_min=GRID_STEP_MIN)

    assert notte.track[0].at == istanti[0].astimezone(QUANDO.tzinfo)
    assert notte.track[-1].at == istanti[-1].astimezone(QUANDO.tzinfo)
    # e nessun punto due volte: quando la coda cade gia' sul salto, ripeterla sarebbe un segmento
    # lungo zero -- invisibile a schermo, e un punto in piu' nel conto
    quando = [p.at for p in notte.track]
    assert len(set(quando)) == len(quando), len(quando) - len(set(quando))


def test_the_curve_keeps_the_altitudes_below_the_horizon():
    """Sotto l'orizzonte l'altezza e' **negativa**, e non si taglia a zero: e' cio' che permette a
    chi disegna di mostrare dove la Luna entra ed esce, invece di una curva appoggiata al bordo.

    Era scritto nel contratto della rotta e non lo difendeva niente: sostituendo `round(alte[i],
    1)` con `round(max(alte[i], 0.0), 1)` **tutta** la suite restava verde. A schermo una curva
    appoggiata a zero sembra un grafico giusto, ed e' esattamente il difetto che non si vede."""
    notte = moon.night_track(QUANDO, *CASA, hours=24)
    alte = [p.altitude_deg for p in notte.track]

    assert min(alte) < -10, min(alte)
    # e il numero e' quello crudo del cielo, non una versione addolcita
    primo = night_grid(QUANDO, hours=24, step_min=GRID_STEP_MIN)[0]
    assert notte.track[0].altitude_deg == round(moon.altitudes([primo], *CASA)[0], 1)


def test_the_ceiling_is_the_highest_the_moon_can_ever_get_from_there():
    """Il tetto del sito: quanto in alto la Luna puo' arrivare da quella latitudine, **mai di
    piu'**. E' il bordo alto del grafico della notte, e dipende solo da dove sei -- per questo la
    stessa scala vale tutte le notti di quel posto, e due notti si confrontano a occhio.

    Vicenza sta a 45,5 gradi e la Luna arriva a 28,6 di declinazione: 90 meno la differenza fa
    73, che salito al multiplo di quindici fa **75**."""
    assert moon.sky_ceiling(45.5455) == 75
    assert moon.sky_ceiling(38.1) == 90  # Palermo: 80,5 -> 90
    assert moon.sky_ceiling(69.7) == 60  # Tromso: 48,9 -> 60


def test_in_the_tropics_the_moon_reaches_the_zenith_and_the_ceiling_stops_at_ninety():
    """Sotto i 28,6 gradi di latitudine la Luna passa **allo zenit**, e sopra i 90 non si va.

    La formula che ci e' arrivata dal disegno -- `90 - |lat| + 28,6` -- non lo sa: alle Canarie
    darebbe 90,5 e a Singapore **117**, cioe' un tetto di 120 contro i 90 che servono. E' la prova
    del trasloco, presa sul serio: l'archivio di chi sviluppa sta a 45 gradi, e li' il difetto non
    si vede mai."""
    for latitudine in (28.1, 20.0, 1.3, 0.0, -15.0):
        assert moon.sky_ceiling(latitudine) == 90, latitudine


def test_the_ceiling_never_falls_below_what_the_moon_really_reaches():
    """**"Mai di piu'" deve valere per costruzione, non per fortuna.**

    La costante che regge il tetto e' un limite superiore alla declinazione della Luna, e se e'
    anche solo un po' troppo piccola il tetto scende sotto la curva e il grafico la taglia. Il
    conto che gira -- le due inclinazioni medie sommate, 28,58 -- e' troppo piccolo: al lunistizio
    maggiore la Luna arriva a 28,72 (misurata ora per ora dal 2024 al 2026, e la prova `lento` qui
    sotto la rimisura). Con 28,58 il tetto restava sopra la Luna solo per la parallasse.

    Si spazza tutta la Terra, e non tre latitudini comode: le tre prove che c'erano stavano dove
    avanza piu' di un grado, quindi accorciare la costante a 28,0 le lasciava **tutte verdi**
    mentre a 43 gradi la Luna sfondava il tetto di mezzo grado."""
    misurata = 28.72  # la prova `lento` la rifa' dal cielo

    for decimi in range(0, 901):
        latitudine = decimi / 10
        puo_arrivare = 90 - max(0.0, latitudine - misurata)
        assert moon.sky_ceiling(latitudine) >= puo_arrivare, (latitudine, puo_arrivare)


@pytest.mark.lento
def test_the_declination_bound_is_not_smaller_than_the_real_moon():
    """Il limite superiore della declinazione si rimisura **sul cielo**, non si ricopia.

    Sta fra i `lento` perche' chiede tre anni di posizioni: il cancello non lo fa girare, ma senza
    di lui il 28,72 della prova qui sopra sarebbe un numero scritto a mano, e la costante si
    difenderebbe da sola."""
    inizio = dt.datetime(2024, 1, 1, tzinfo=dt.UTC)
    ogni_ora = [inizio + dt.timedelta(hours=i) for i in range(3 * 365 * 24)]
    dove_arriva = moon.get_body("moon", Time(ogni_ora)).dec.deg  # pyright: ignore[reportOptionalMemberAccess]
    quanto = [abs(float(d)) for d in dove_arriva]  # pyright: ignore[reportArgumentType, reportOptionalIterable]

    assert max(quanto) <= MAX_DECLINATION_DEG


def test_the_lit_limb_is_mirrored_south_of_the_equator():
    """Cresce a destra e cala a sinistra -- **e dall'emisfero sud al contrario**.

    Una crescente e' illuminata a destra da Vicenza e a sinistra da Auckland: chi guarda la stessa
    Luna dall'altra meta' del mondo la vede capovolta. Senza questa riga il disegno nascerebbe
    specchiato per meta' degli utenti, e da qui non se ne accorgerebbe nessuno -- e' la prova del
    trasloco applicata a una forma invece che a un numero."""
    for fase in ("waxing_crescent", "first_quarter", "waxing_gibbous"):
        assert moon.lit_side(fase, 45.5) == "right", fase
        assert moon.lit_side(fase, -36.8) == "left", fase
    for fase in ("waning_crescent", "last_quarter", "waning_gibbous"):
        assert moon.lit_side(fase, 45.5) == "left", fase
        assert moon.lit_side(fase, -36.8) == "right", fase


def test_the_ceiling_does_not_care_which_hemisphere_you_are_in():
    """Da 45 gradi sud la Luna sale esattamente quanto da 45 nord: cambia da che parte la guardi,
    non quanto alta arriva. Senza il valore assoluto, un sito australe avrebbe un tetto piu' alto
    di novanta e il grafico nascerebbe storto per meta' mondo."""
    for latitudine in (45.5455, 38.1, 69.7, 12.0):
        assert moon.sky_ceiling(-latitudine) == moon.sky_ceiling(latitudine), latitudine


def test_a_real_night_never_climbs_above_its_ceiling():
    """I due numeri devono stare insieme: **quanto sale stanotte** non puo' superare **quanto puo'
    salire da qui**. E' l'unica prova che lega il tetto al cielo vero invece che a una formula
    ricopiata: se il tetto fosse calcolato da un'altra latitudine, o con un segno sbagliato, una
    notte qualunque lo sfonderebbe."""
    for latitudine, longitudine in (CASA, POLO):
        notte = moon.night_track(QUANDO, latitudine, longitudine, hours=24)

        assert notte.highest.altitude_deg <= moon.sky_ceiling(latitudine), latitudine


def test_the_curve_step_is_a_multiple_of_the_sampling_step():
    """La curva si ricava dalla griglia prendendo un campione ogni tot: se il suo passo non e' un
    multiplo di quello della griglia, il "ogni quindici minuti" diventa un arrotondamento e i
    punti si spostano -- una curva che mente di poco, cioe' nel modo che non si vede."""
    assert TRACK_STEP_MIN % GRID_STEP_MIN == 0, (TRACK_STEP_MIN, GRID_STEP_MIN)
    assert TRACK_STEP_MIN > GRID_STEP_MIN


def test_the_curve_carries_its_instants_in_the_asked_timezone():
    """Gli istanti della curva tornano nel fuso da cui la notte e' stata chiesta, come gli orari:
    chi disegna il grafico ci scrive sopra le ore, e un UTC non dichiarato sposterebbe tutta la
    curva senza che niente sembri rotto."""
    roma = zoneinfo.ZoneInfo("Europe/Rome")
    inizio = dt.datetime(2027, 7, 15, 12, tzinfo=roma)  # ora legale: +02:00

    notte = moon.night_track(inizio, *CASA, hours=24)

    for punto in (notte.track[0], notte.track[-1], notte.highest):
        assert punto.at.utcoffset() == dt.timedelta(hours=2), punto


# Le tavole dell'USNO per due posti e una notte, lette il 20/9/2026 da
# <https://aa.usno.navy.mil/api/rstt/oneday>. Stanno scritte qui e non in un commento perche' una
# misura che ha chiuso un dubbio deve potersi **rifare**: senza data e coordinate, chi la ripete
# con un arrotondamento diverso conclude il contrario.
USNO = (
    # posto, lat, lon, fuso, levata, tramonto
    # Il tramonto di Cortina e' `None` **non perche' manchi**: cade alle 00:45 del giorno dopo, e
    # l'ora attesa qui sotto si costruisce sul giorno d'inizio. Un tramonto dopo mezzanotte -- che
    # per la Luna e' il caso normale -- confronterebbe il giorno sbagliato e il rosso stamperebbe
    # due orari identici.
    ("Cortina d'Ampezzo", 46.54, 12.14, 2, "16:32", None),
    ("Reykjavik", 64.13, -21.90, 0, "20:11", "21:51"),
)


@pytest.mark.parametrize(("posto", "lat", "lon", "fuso", "levata", "tramonto"), USNO)
def test_rise_and_set_match_the_usno_tables_within_a_minute(
    posto, lat, lon, fuso, levata, tramonto
):
    """La soglia di sorgere e tramontare **vale anche per la Luna**, ed e' misurato, non citato.

    L'USNO per la Luna usa una formula sua, con dentro la parallasse orizzontale -- quasi un grado
    -- mentre qui si usa lo stesso `RISESET_DEG` del Sole. Le nostre altezze pero' sono
    topocentriche, cioe' la parallasse e' gia' dentro il conto, e il numero torna.

    Reykjavik e' il caso che conta: quella notte la Luna resta su **un'ora e quaranta**, cioe'
    sorge quasi radente, ed e' li' che un errore di soglia varrebbe decine di minuti invece di
    uno. Il minuto che resta e' l'interpolazione fra due campioni a tre minuti, non la soglia.

    Senza questa prova il confronto vivrebbe in un commento, e nessuno saprebbe se vale ancora."""
    inizio = dt.datetime(2026, 9, 20, 12, tzinfo=dt.timezone(dt.timedelta(hours=fuso)))

    cielo = moon.night_track(inizio, lat, lon, hours=24)

    # **Un minuto**, non l'uguaglianza: l'USNO scrive i minuti tondi e noi interpoliamo fra due
    # campioni a tre minuti. E' la tolleranza che l'affermazione dichiara, quindi e' quella che si
    # misura -- chiedere l'uguale sarebbe una prova che cade per il motivo sbagliato.
    for quale, atteso in (("rise", levata), ("set", tramonto)):
        if atteso is None:
            continue
        ore, minuti = (int(p) for p in atteso.split(":"))
        quando = inizio.replace(hour=ore, minute=minuti)
        scarto = abs((getattr(cielo, quale) - quando).total_seconds())
        assert scarto <= 60, f"{posto} {quale}: {getattr(cielo, quale):%H:%M} contro {atteso}"
