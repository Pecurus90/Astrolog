"""**Che luna e'**: il nome della fase, quanto e' illuminata, e le due strade per chiederlo --
un istante solo e molti insieme.

Sta in un file suo per il tetto di righe, e il taglio e' quello del mestiere: qui la fase, che e'
**geocentrica** e non chiede un sito; in `test_ephemeris_moon.py` il cielo di una notte -- sorgere,
tramontare, quanto sale, la curva -- che dipende da dove sei.

Le prove dichiarate come tolte da li' sono **spostate e non riscritte**, stesso nome e stesso corpo:
test-tolto: test_the_phase_is_one_of_the_eight_and_carries_its_light
test-tolto: test_the_phases_asked_together_are_the_ones_asked_one_by_one
test-tolto: test_two_lists_of_different_length_are_refused_instead_of_paired
test-tolto: test_asking_for_no_phases_asks_astropy_nothing
test-tolto: test_asking_the_phases_together_is_worth_it
test-tolto: test_the_phase_and_the_light_say_the_same_thing
test-tolto: test_waxing_comes_before_full_and_waning_after
test-tolto: test_every_one_of_the_eight_phases_is_reachable
test-tolto: test_the_phase_does_not_care_where_the_angle_started
test-tolto: test_the_illuminated_fraction_does_not_depend_on_where_you_are

Le date sono **nel futuro** apposta, come nell'altro file: e' li' che astropy, senza l'assetto
offline, proverebbe a scaricare i dati di orientamento della Terra.
"""

import datetime as dt
import inspect

import pytest

from astrolog.ephemeris import moon

pytestmark = pytest.mark.filterwarnings("ignore:Tried to get polar motions:")

QUANDO = dt.datetime(2027, 3, 14, 12, 0, tzinfo=dt.UTC)  # mezzogiorno UTC, nel futuro
CASA = (45.5455, 11.5354)  # Vicenza
POLO = (78.2232, 15.6267)  # Longyearbyen, sopra il circolo polare


def test_the_phase_is_one_of_the_eight_and_carries_its_light():
    """La fase e' una delle otto, e la frazione illuminata sta fra 0 e 100. Sono i due numeri che
    il piede della barra mostra, e nessuno dei due puo' uscire dal suo intervallo."""
    detto = moon.phase(QUANDO)

    assert detto["phase_key"] in moon.PHASES
    assert 0 <= detto["illumination_pct"] <= 100


def test_the_phases_asked_together_are_the_ones_asked_one_by_one():
    """Chiedere le fasi di molti istanti in un colpo da' **le stesse** di chiederle una per una.

    E' la prova che le due strade sono una casa sola: la pagina delle Notti chiede in blocco, il
    piede della barra chiede un istante solo, e se divergessero due schermi dello stesso archivio
    direbbero due lune diverse per la stessa notte."""
    giorni = [QUANDO + dt.timedelta(days=g) for g in range(10)]

    assert moon.phases(giorni) == [moon.phase(g) for g in giorni]


def test_two_lists_of_different_length_are_refused_instead_of_paired(monkeypatch):
    """Se i due conti che compongono una fase uscissero di lunghezza diversa, accoppiarli
    **in silenzio** darebbe a ogni istante il numero di un altro: la fase di una notte con
    l'illuminazione di un'altra, e nessuno potrebbe accorgersene guardando.

    Non e' un caso che astropy possa produrre oggi -- e' la ragione per cui l'accoppiamento e'
    dichiarato stretto -- quindi si forza qui, ed e' l'unico modo di vedere questa guardia rossa."""
    corte = moon._longitudini_eclittiche

    def una_di_meno(corpo, eclittica):
        return corte(corpo, eclittica)[:-1]

    monkeypatch.setattr(moon, "_longitudini_eclittiche", una_di_meno)

    with pytest.raises(ValueError, match="zip"):
        moon.phases([QUANDO, QUANDO + dt.timedelta(days=1)])


def test_asking_for_no_phases_asks_astropy_nothing():
    """Una pagina di notti puo' essere vuota, e un `Time([])` in astropy non e' un elenco vuoto:
    e' un errore. Il caso si chiude qui, non in chi chiama."""
    assert moon.phases([]) == []


@pytest.mark.lento
def test_asking_the_phases_together_is_worth_it():
    """Il conto in blocco esiste per il costo, quindi il costo si **misura** invece di scriverlo
    in un commento: cento istanti in una chiamata contro cento chiamate.

    La soglia e' larga (cinque volte) perche' la prova non deve cadere su una macchina lenta o
    carica: il guadagno vero, misurato qui, e' molto piu' grande -- ma e' il rapporto a dover
    restare vero, non il numero."""
    import time

    giorni = [QUANDO + dt.timedelta(days=g) for g in range(100)]

    t0 = time.perf_counter()
    moon.phases(giorni)
    insieme = time.perf_counter() - t0

    t0 = time.perf_counter()
    for g in giorni:
        moon.phase(g)
    una_per_una = time.perf_counter() - t0

    assert una_per_una > insieme * 5, f"insieme {insieme:.3f}s, una per una {una_per_una:.3f}s"


# Quanta luce puo' avere una fase, dedotto dalla banda di sei gradi che le da' il nome: la
# frazione illuminata e' `(1 - cos(elongazione)) / 2`, quindi al bordo della banda della luna
# nuova (6 gradi) vale lo 0,3%, e al bordo di quella piena (174 gradi) il 99,7%. Non sono numeri
# scelti: sono quelli, e se la banda cambia questi si ricavano di nuovo.
LUCE_DELLA_FASE = {
    "new": (0, 1),
    "waxing_crescent": (0, 45),
    "first_quarter": (44, 56),
    "waxing_gibbous": (55, 100),
    "full": (99, 100),
    "waning_gibbous": (55, 100),
    "last_quarter": (44, 56),
    "waning_crescent": (0, 45),
}


def test_the_phase_and_the_light_say_the_same_thing():
    """Il nome della fase e la frazione illuminata **non possono contraddirsi**: una "piena" al 40%
    o una "nuova" al 90% sono due conti che a schermo sembrano sensati ognuno per conto suo, e
    solo messi accanto si vede che uno dei due e' sbagliato.

    Non si scrivono date a memoria: si attraversa un **mese lunare** e si guarda che l'accordo
    regga su ogni campione. E' esattamente per non fidarsi di un fatto ricordato che questa prova
    e' fatta cosi' -- questa scala di numeri e' gia' entrata storta una volta, scritta a mente."""
    giorni = [QUANDO + dt.timedelta(days=g) for g in range(30)]
    letture = [moon.phase(q) for q in giorni]

    for letta in letture:
        minimo, massimo = LUCE_DELLA_FASE[letta["phase_key"]]
        assert minimo <= letta["illumination_pct"] <= massimo, letta

    # e in un mese non si incontra sempre la stessa fase
    assert len({letta["phase_key"] for letta in letture}) >= 6


def test_waxing_comes_before_full_and_waning_after():
    """**Crescente prima della piena, calante dopo.** E' il buco che tutte le altre prove
    lasciano aperto: un segno invertito nella differenza di longitudine scambia crescente con
    calante e basta -- la luce non cambia, perche' e' simmetrica, quindi l'accordo fra nome e
    luce regge lo stesso e nessuna prova cade. A schermo diventerebbe una luna che "cresce"
    mentre cala, e chi pianifica una notte al buio si troverebbe la luna piena.

    Non si scrive una data a memoria: si cerca **il massimo di luce** nel mese e si guarda cosa
    c'e' prima e dopo."""
    giorni = [QUANDO + dt.timedelta(days=g) for g in range(30)]
    luci = [moon.phase(q) for q in giorni]
    piu_piena = max(range(len(luci)), key=lambda i: luci[i]["illumination_pct"])

    assert 3 <= piu_piena <= len(luci) - 4, f"il massimo cade sul bordo del mese: {piu_piena}"
    assert luci[piu_piena - 3]["phase_key"].startswith("waxing"), luci[piu_piena - 3]
    assert luci[piu_piena + 3]["phase_key"].startswith("waning"), luci[piu_piena + 3]


def test_every_one_of_the_eight_phases_is_reachable():
    """Tutte e otto hanno una fetta di cerchio: una banda che non scatta mai e' un nome che
    nessuno leggera' -- e non si vede attraversando il cielo: un campione al giorno salta una
    banda larga dodici gradi in **una finestra di trenta giorni su sei** (misurato su 700
    finestre scorrevoli), e quando ne salta una ne salta una sola.

    Si gira il cerchio intero, grado per grado, sulla **regola** invece che sul cielo."""
    incontrate = [moon.phase_name(g) for g in range(360)]

    assert set(incontrate) == set(moon.PHASES), sorted(set(moon.PHASES) - set(incontrate))
    # e l'ordine e' quello del mese: nuova, crescente, primo quarto... senza salti
    in_ordine = [f for i, f in enumerate(incontrate) if i == 0 or f != incontrate[i - 1]]
    assert in_ordine == [*moon.PHASES, "new"], in_ordine


def test_the_phase_does_not_care_where_the_angle_started():
    """Un angolo si puo' presentare negativo o oltre il giro: la differenza di due longitudini lo
    fa spesso. Chi non lo riportasse nel cerchio direbbe la fase sbagliata di mezzo mese."""
    for grado in range(360):
        assert moon.phase_name(grado) == moon.phase_name(grado - 360)
        assert moon.phase_name(grado) == moon.phase_name(grado + 720)


def test_the_illuminated_fraction_does_not_depend_on_where_you_are():
    """La frazione illuminata e' **geocentrica**: la stessa da Vicenza e dalle Svalbard. Chi la
    calcolasse dal sito la farebbe variare di poco e senza motivo, e due persone che guardano la
    stessa luna leggerebbero due numeri diversi.

    La regola si prova **sulla forma**: `phase` non ha nessun posto dove mettere un sito. Una
    prova che confrontasse due chiamate uguali fra loro non potrebbe mai essere vista rossa."""
    quanti = inspect.signature(moon.phase).parameters

    assert list(quanti) == ["istante"], quanti
    # e l'unico posto che chiede un sito e' quello che ne ha bisogno davvero
    assert "latitude" in inspect.signature(moon.night_track).parameters
