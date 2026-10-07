"""La pagina **Notti**: *"quando ho ripreso, e cosa ho fatto quella sera"*.

L'Archivio racconta gli oggetti; questa racconta le notti. Una notte e' **una data piu' un
sito** (`docs/domini/notti.md`), e i numeri di una riga sono quelli della notte intera: gli
oggetti e i filtri stanno **dentro** la riga, non la moltiplicano.
"""

from dataclasses import asdict
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.clock import midnight_of
from astrolog.db.connect import connect
from astrolog.ephemeris import moon
from astrolog.spine import nights
from conftest import db
from group_bench import ROMA, corri, filtro, luogo, posa, prepara

ALTROVE = ("Cima Ekar", 45.8667, 11.5167, "Europe/Rome")


def nomi(conn, come_si_chiamano):
    """Il nome primario di un oggetto: senza, il nome lo darebbe il catalogo, che in un archivio
    di prova non e' caricato -- e la riga uscirebbe muta per una ragione che non c'entra."""
    for object_id, nome in come_si_chiamano.items():
        conn.execute(
            "INSERT INTO object_names(object_id, name, origin, is_primary)"
            " VALUES(?, ?, 'catalog', 1)",
            (object_id, nome),
        )


def notti(client, **parametri):
    risposta = client.get("/api/v1/nights", params=parametri)
    assert risposta.status_code == 200, risposta.text
    return risposta.json()


@pytest.fixture
def archivio(db_path):
    """Due notti a casa: il 17 maggio un oggetto solo in Ha, il 18 due oggetti e due filtri."""
    conn = connect(db_path)
    try:
        prepara(conn)
        nomi(conn, {1: "M 31", 2: "M 45"})
        luogo(conn, ROMA)
        ha, oiii = filtro(conn, "Ha"), filtro(conn, "OIII", "oiii")
        posa(conn, quando="2024-05-17T22:00:00Z", filtro_id=ha, esposizione=300.0, hash_="a1")
        posa(conn, quando="2024-05-17T23:00:00Z", filtro_id=ha, esposizione=300.0, hash_="a2")
        posa(conn, quando="2024-05-18T22:00:00Z", filtro_id=ha, esposizione=600.0, hash_="b1")
        posa(
            conn,
            quando="2024-05-18T23:00:00Z",
            oggetto=2,
            filtro_id=oiii,
            esposizione=120.0,
            hash_="b2",
        )
        corri(conn)
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def test_the_page_lists_the_nights_you_shot(archivio):
    """Le notti che ho ripreso, **dalla piu' recente**: chi apre la pagina sta quasi sempre
    guardando le ultime uscite, e l'ordine lo decide il backend -- due schermi dello stesso
    archivio non si mettono d'accordo per caso."""
    pagina = notti(archivio)
    assert [n["night_date"] for n in pagina["items"]] == ["2024-05-18", "2024-05-17"]
    assert pagina["total"] == 2


def test_a_night_says_where_you_were_and_what_you_shot(archivio):
    """Una riga per notte, e dentro **gli oggetti**: una notte con due oggetti resta una notte,
    o le sue ore andrebbero ricomposte a mente e due righe con la stessa data sembrerebbero un
    doppione."""
    prima = notti(archivio)["items"][0]
    assert prima["site"] == "Casa"
    assert prima["frames"] == 2
    assert prima["integration_s"] == 720.0
    assert [(o["name"], o["frames"]) for o in prima["objects"]] == [("M 31", 1), ("M 45", 1)]


def test_a_night_says_which_filters_and_how_long_each_one_ran(archivio):
    """I filtri con le loro ore, **dal piu' usato**: e' quello che dice com'e' andata la notte,
    e il giorno che la veste ne fa una barra proporzionale i numeri sono gia' quelli giusti."""
    prima = notti(archivio)["items"][0]
    assert [(f["name"], f["integration_s"]) for f in prima["filters"]] == [
        ("Ha", 600.0),
        ("OIII", 120.0),
    ]


def test_the_page_opens_with_what_the_whole_archive_holds(archivio):
    """In cima, l'archivio intero: e' la domanda che ci si fa aprendo la pagina, e non dipende da
    quante righe si stanno guardando."""
    totali = notti(archivio, limit=1)["totals"]
    assert totali == {"nights": 2, "frames": 4, "integration_s": 1320.0, "untimed": 0}


def test_the_archive_totals_read_the_frames_once_whatever_the_nights(archivio):
    """`notti.md`: il totale in cima non costa una query in piu' per riga, e' una sola
    sull'archivio. Con due notti, un conto per notte leggerebbe le pose due volte."""
    lette = []
    with db(archivio) as conn:
        conn.set_trace_callback(lette.append)
        nights.archive_totals(conn)
        conn.set_trace_callback(None)
    assert len([s for s in lette if "frames" in s]) == 1


def test_two_sites_on_the_same_date_stay_two_nights(archivio):
    """Stessa data, due postazioni: **due righe**. Accorparle sommerebbe le ore di due cieli
    diversi, e la riga direbbe un posto solo dove ce n'erano due."""
    with db(archivio) as conn:
        altro = luogo(conn, ALTROVE, casa=False)
        conn.execute(
            "INSERT INTO nights(site_id, night_date, site_source, created_at)"
            " VALUES(?, '2024-05-18', 'declared', '2026-01-01T00:00:00Z')",
            (altro,),
        )
        conn.commit()

    righe = [n for n in notti(archivio)["items"] if n["night_date"] == "2024-05-18"]
    assert sorted(n["site"] for n in righe) == ["Casa", "Cima Ekar"]


def test_a_rewritten_copy_is_not_another_hour_of_the_night(archivio):
    """Chi elabora tiene grezzo e calibrato nella stessa cartella: contarli tutti e due
    raddoppierebbe la notte. E' la stessa regola dell'Archivio, e la stessa casa."""
    prima = notti(archivio)["items"][0]
    with db(archivio) as conn:
        originale = conn.execute("SELECT id FROM frames WHERE frame_hash = 'b1'").fetchone()["id"]
        copia = posa(
            conn,
            quando="2024-05-18T22:00:00Z",
            filtro_id=None,
            esposizione=600.0,
            hash_="b1-copia",
            copia_di=originale,
        )
        conn.execute("UPDATE frames SET night_id = ? WHERE id = ?", (prima["id"], copia))
        conn.commit()

    dopo = next(n for n in notti(archivio)["items"] if n["id"] == prima["id"])
    assert (dopo["frames"], dopo["integration_s"]) == (prima["frames"], prima["integration_s"])


def test_a_pose_without_a_time_is_not_zero_hours_of_the_night(archivio):
    """Una posa che non dice quanto e' durata **non vale zero**: resta fuori dalla somma e si
    conta a parte, o "non lo sappiamo" e "zero ore" diventerebbero la stessa cosa."""
    prima = notti(archivio)["items"][0]
    with db(archivio) as conn:
        conn.execute(
            "UPDATE frames SET exposure_s = NULL WHERE frame_hash = 'b2'",
        )
        conn.commit()

    dopo = next(n for n in notti(archivio)["items"] if n["id"] == prima["id"])
    assert dopo["integration_s"] == 600.0, "la posa senza tempo non entra nella somma"
    assert dopo["untimed"] == 1


def test_the_page_counts_the_poses_still_waiting_for_an_answer(archivio):
    """Le pose che l'app ha fermato in attesa di una risposta non stanno in nessuna notte: se la
    pagina tace, quelle ore sembrano non essere mai esistite. Si contano **per dove si risponde**,
    perche' mandare a *Da confermare* chi deve dichiarare il sito vuol dire mandarlo davanti a un
    elenco dove non trovera' niente."""
    with db(archivio) as conn:
        posa(conn, quando="2024-06-01T22:00:00Z", coord=(34.0, -111.0), hash_="incerta")
        posa(conn, quando=None, hash_="senza data 1")
        posa(conn, quando=None, hash_="senza data 2")
        corri(conn)
        conn.commit()

    # **Dal gruppo piu' grosso**: chi apre la pagina deve vedere per primo cio' che gli tiene
    # fuori piu' ore, non cio' che il database restituisce per primo.
    assert notti(archivio)["waiting"] == [
        {"answer_at": "never", "frames": 2},
        {"answer_at": "review", "frames": 1},
    ]


def test_the_page_says_when_the_reading_is_not_over(archivio):
    """Chi apre Notti a meta' corsa vedrebbe tre notti e crederebbe di averne tre: il residuo
    della spina viaggia con la pagina, e viene dalla casa che lo conta gia' per la scansione."""
    assert notti(archivio)["still_reading"] == 0
    with db(archivio) as conn:
        posa(conn, quando="2024-06-02T22:00:00Z", hash_="daleggere")
        conn.commit()

    assert notti(archivio)["still_reading"] > 0


def test_a_frame_with_no_answer_to_give_does_not_send_you_anywhere(archivio):
    """Una posa che l'header non data non ha **nessuna** risposta da dare: non entra in nessuna
    notte e non c'e' niente da cliccare. Mandarla nel mucchio di *Da confermare* manderebbe
    l'utente davanti a un elenco dove quella posa non compare."""
    with db(archivio) as conn:
        posa(conn, quando=None, hash_="senza data")
        corri(conn)
        conn.commit()

    assert notti(archivio)["waiting"] == [{"answer_at": "never", "frames": 1}]


def test_the_ways_of_having_no_nights_are_different_answers(db_path):
    """Non avere notti ha quattro motivi, e la pagina deve poterli distinguere: **non hai frame**
    (totali a zero), **non hai detto dov'e' casa** (le pose sono ferme col loro motivo, e senza
    un sito non nasceranno mai), **non ci siamo ancora arrivati** (la spina ha lavoro da fare), e
    **le tue pose aspettano una risposta** (ci sono, ma sono tutte ferme su una domanda).
    Uno stato vuoto che li confonde manda l'utente a sistemare la cosa sbagliata."""
    conn = connect(db_path)
    try:
        prepara(conn)
        conn.commit()
        with TestClient(create_app(db_path), base_url="http://localhost") as c:
            vuoto = notti(c)
        assert (vuoto["totals"]["nights"], vuoto["waiting"], vuoto["still_reading"]) == (0, [], 0)

        posa(conn, quando="2024-05-17T22:00:00Z", hash_="senza casa")
        conn.commit()
        with TestClient(create_app(db_path), base_url="http://localhost") as c:
            leggendo = notti(c)
        assert leggendo["still_reading"] == 1, "c'e' lavoro da fare, non una domanda"

        corri(conn)
        conn.commit()
        with TestClient(create_app(db_path), base_url="http://localhost") as c:
            senza_casa = notti(c)
        assert senza_casa["waiting"] == [{"answer_at": "site", "frames": 1}]
        assert senza_casa["still_reading"] == 0

        # E il quarto: c'e' un sito, ma quella posa e' stata ripresa altrove e l'app chiede dove.
        luogo(conn, ROMA)
        posa(conn, quando="2024-05-18T22:00:00Z", coord=(34.0, -111.0), hash_="altrove")
        corri(conn)
        conn.commit()
        with TestClient(create_app(db_path), base_url="http://localhost") as c:
            in_attesa = notti(c)
        assert in_attesa["totals"]["nights"] == 0, "nessuna notte, ma non perche' manca tutto"
        # La posa di prima resta ferma sul sito -- nessuno l'ha rimessa in coda -- e quella nuova
        # aspetta una risposta in Da confermare: due gesti diversi, e la pagina li deve poter
        # nominare tutti e due.
        assert {v["answer_at"] for v in in_attesa["waiting"]} == {"review", "site"}
    finally:
        conn.close()


def test_a_night_says_which_moon_there_was(archivio):
    """Che luna c'era quella notte: e' la prima cosa che un astrofotografo ricorda di una
    nottata, e una piena cambia cosa si e' potuto riprendere.

    Si chiede alla **mezzanotte** della notte, nel fuso del sito: la Luna cambia mentre la notte
    passa, e un istante va scelto. Il numero non si conserva -- si ricalcola -- quindi qui si
    guarda che sia quello che le effemeridi dicono per quell'istante, non un valore atteso
    scritto a mano."""
    prima = notti(archivio)["items"][0]

    assert prima["moon"] == asdict(moon.phase(midnight_of(prima["night_date"], "Europe/Rome")))


def test_a_night_whose_site_has_no_timezone_says_nothing_about_the_moon(archivio):
    """Senza un fuso non c'e' una mezzanotte, quindi non c'e' una Luna: la riga tace invece di
    prendersi quella di Greenwich, che sarebbe il cielo di un altro posto."""
    with db(archivio) as conn:
        conn.execute("UPDATE sites SET timezone = 'Nowhere/Nohow'")
        conn.commit()

    assert all(n["moon"] is None for n in notti(archivio)["items"])


def test_the_moon_of_a_whole_page_costs_one_call(archivio):
    """Una pagina di cento notti chiede al cielo **una volta**, non cento.

    La guardia e' sul numero di chiamate, non sul tempo: un tempo dipende dalla macchina, il
    conto delle chiamate no -- ed e' quello che cambia se un domani la fase si chiede dentro il
    giro delle righe."""
    quante = []
    vero = moon.phases

    def contando(istanti):
        quante.append(len(istanti))
        return vero(istanti)

    with db(archivio) as conn:
        for g in range(3, 20):
            posa(conn, quando=f"2024-03-{g:02d}T22:00:00Z", esposizione=60.0, hash_=f"n{g}")
        corri(conn)
        conn.commit()

    with mock.patch.object(moon, "phases", contando):
        pagina = notti(archivio)

    assert len(pagina["items"]) > 10, "servono abbastanza notti perche' la domanda abbia senso"
    assert quante == [len(pagina["items"])], "una chiamata sola, con dentro tutte le notti"


def test_a_night_never_gets_another_nights_moon(archivio):
    """Le lune tornano **in fila** con le notti che le hanno chieste: se il cielo ne rendesse una
    di meno, accoppiarle a scorrimento darebbe a ogni notte la luna di un'altra -- un dato
    plausibile e sbagliato, che a schermo nessuno puo' smentire. Meglio non rispondere affatto.

    Si forza, perche' oggi non puo' succedere: e' l'unico modo di vedere questa guardia rossa."""
    vero = moon.phases

    # si ferma: meglio un guasto dichiarato di una luna attribuita alla notte sbagliata
    with (
        mock.patch.object(moon, "phases", lambda istanti: vero(istanti)[:-1]),
        pytest.raises(ValueError, match="zip"),
    ):
        archivio.get("/api/v1/nights")


def test_the_nights_list_is_paged_like_every_other(archivio):
    """Chi ha mille notti le vede tutte, a pagine: la pagina si allunga come l'Archivio, e il
    totale resta quello dell'archivio intero."""
    pagina = notti(archivio, limit=1)
    assert len(pagina["items"]) == 1 and pagina["total"] == 2
    seconda = notti(archivio, limit=1, offset=1)
    assert seconda["items"][0]["night_date"] == "2024-05-17"
    assert seconda["items"][0]["id"] != pagina["items"][0]["id"]


def test_a_night_is_asked_by_its_id_wherever_it_falls_in_the_list(archivio):
    """La ricerca apre una notte precisa (`/notti?notte=<id>`): la pagina la chiede da sola, anche
    se nell'elenco cadrebbe oltre le prime cento."""
    tutte = notti(archivio)["items"]
    vecchia = next(n for n in tutte if n["night_date"] == "2024-05-17")
    sola = notti(archivio, night=vecchia["id"])
    assert [n["id"] for n in sola["items"]] == [vecchia["id"]]
    assert sola["items"][0] == vecchia
    assert sola["total"] == 1


def test_a_night_that_does_not_exist_is_an_empty_list_not_an_error(archivio):
    """Un indirizzo vecchio, di una notte che non c'e' piu': nessuna riga, e la pagina lo dice."""
    vuota = notti(archivio, night=999_999)
    assert (vuota["items"], vuota["total"]) == ([], 0)
