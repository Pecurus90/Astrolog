"""Il tempo di `astrolog.clock`: quanto e' durata una corsa e la mezzanotte di una notte.
`DATE-OBS` e' UTC, e la regola la dice il contratto, `docs/domini/spina.md`.
"""

from astrolog.clock import elapsed_s, midnight_of, night_date


def test_how_long_a_run_took_is_a_number_the_screen_can_show():
    """Quanto e' durata una lettura: i due istanti li ha il database, la **differenza** no -- e
    calcolarla a schermo andrebbe contro la regola che il backend manda cio' che lo schermo
    mostra. Sta qui perche' e' aritmetica sul tempo, nella grafia del DB.

    Si contano i **secondi**, non i minuti: una scansione di prova dura tre secondi, e
    arrotondarla a zero minuti direbbe che non e' successo niente."""
    assert elapsed_s("2026-09-20T21:00:00.000Z", "2026-09-20T21:00:03.500Z") == 3.5
    assert elapsed_s("2026-09-20T21:00:00.000Z", "2026-09-20T22:34:56.000Z") == 5696.0


def test_a_run_still_going_has_no_duration_yet():
    """Una corsa aperta non ha un `ended_at`, e la sua durata non e' **zero**: e' "non ancora".
    Uno zero a schermo direbbe che la lettura e' finita in un istante."""
    assert elapsed_s("2026-09-20T21:00:00.000Z", None) is None


def test_two_instants_that_cannot_be_read_are_no_duration():
    """Un istante illeggibile non diventa una durata inventata, e una fine **prima** dell'inizio
    nemmeno: un orologio spostato a meta' corsa darebbe una durata negativa, che a schermo e'
    peggio di un "non lo so"."""
    assert elapsed_s("ieri", "2026-09-20T21:00:00.000Z") is None
    assert elapsed_s(None, "2026-09-20T21:00:00.000Z") is None
    assert elapsed_s("2026-09-20T22:00:00.000Z", "2026-09-20T21:00:00.000Z") is None


def test_the_midnight_of_a_night_falls_on_the_day_after():
    """La mezzanotte di una notte e' quella del **giorno dopo**, e non e' un cavillo.

    Una notte va da mezzogiorno a mezzogiorno: la notte del 18 maggio comincia alle 12 del 18 e
    finisce alle 12 del 19, quindi la sua mezzanotte -- l'istante a cui si chiede che luna c'era
    -- cade il **19**. Prendere le 00:00 del 18 vorrebbe dire descrivere la notte precedente, con
    una luna vecchia di ventiquattr'ore."""
    quando = midnight_of("2024-05-18", "Europe/Rome")

    assert quando.isoformat() == "2024-05-19T00:00:00+02:00"


def test_the_midnight_of_a_night_belongs_to_that_night():
    """Il giro si chiude: la mezzanotte di una notte **appartiene a quella notte**.

    E' la promessa su cui poggia tutto -- l'istante a cui si chiede al cielo com'era quella notte
    -- e senza questa prova resterebbe scritta solo in un commento: se un domani la finestra si
    spostasse, `midnight_of` descriverebbe in silenzio la notte prima o quella dopo. Si prova su
    un mese intero, **cambio dell'ora compreso** (l'ultima domenica di ottobre), perche' e' li'
    che una notte dura 25 ore e le due regole potrebbero scollarsi."""
    for giorno in range(1, 32):
        notte = f"2024-10-{giorno:02d}"
        quando = midnight_of(notte, "Europe/Rome")

        assert quando is not None
        assert night_date(quando.isoformat(), "Europe/Rome") == notte, notte


def test_the_midnight_is_the_one_of_that_place():
    """Lo stesso giorno in due fusi e' un istante diverso: la mezzanotte di Roma e quella
    dell'Arizona distano nove ore, ed e' la ragione per cui il fuso si chiede."""
    roma = midnight_of("2024-05-18", "Europe/Rome")
    arizona = midnight_of("2024-05-18", "America/Phoenix")

    assert (arizona - roma).total_seconds() / 3600 == 9


def test_a_midnight_that_does_not_exist_still_lands_in_its_night():
    """A Santiago del Cile il cambio d'ora cade **a mezzanotte**: quella notte le 00:00 locali non
    esistono, l'orologio salta dalle 23:59 all'01:00. Non e' un caso da rifiutare -- la notte c'e'
    lo stesso -- quindi si prende l'istante che quel salto produce, e deve restare **dentro quella
    notte**, non scivolare in quella dopo."""
    quando = midnight_of("2024-09-07", "America/Santiago")

    assert quando is not None
    assert night_date(quando.isoformat(), "America/Santiago") == "2024-09-07"


def test_a_night_without_a_usable_timezone_has_no_midnight():
    """Un fuso che non si riconosce non da' una mezzanotte: chi chiede tace, invece di prendersi
    quella di Greenwich e descrivere il cielo di un altro posto."""
    assert midnight_of("2024-05-18", "Nowhere/Nohow") is None
    assert midnight_of("2024-05-18", None) is None
    assert midnight_of("non una data", "Europe/Rome") is None
