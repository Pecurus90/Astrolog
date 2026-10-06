"""La sezione dei luoghi di Da confermare: *"queste pose da quale luogo?"*.

E' la domanda che sblocca le pose che `group` ha fermato perche' le coordinate dell'header
dicono un altro posto. L'app non indovina -- un GPS o una rete possono sbagliare, e una notte
attribuita male e' un dato falso che nessuno rilegge -- quindi chiede, **per gruppo e mai per
posa**, proponendo i luoghi che l'utente ha gia' dichiarato.
"""

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.clock import now_iso
from astrolog.db.connect import connect
from astrolog.spine import coordinates
from astrolog.spine import declarations as decl
from astrolog.spine.group import SITE_UNCLEAR
from conftest import apply, db, review
from group_bench import ARIZONA, ROMA, VICINO, corri, luogo, notte_di, posa, prepara, stato


def test_unclear_coordinates_start_from_the_two_ways_a_pose_concerns_them(conn):
    """Una posa riguarda i luoghi incerti per due strade -- ferma su un posto incerto, o in una
    notte a cui hai detto il luogo -- e ognuna si cerca col suo indice: partire dagli stadi di tutto
    l'archivio vorrebbe dire passare da ogni posa a ogni apertura di Da confermare."""
    piano = [r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + coordinates._ROWS, (SITE_UNCLEAR,))]
    ferme = [p for p in piano if "frame_stages_pending" in p]
    assert ferme and all("(stage=? AND status=?)" in p for p in ferme), piano
    assert any("INDEX frames_night" in p for p in piano), piano


LONTANO = (46.05, 11.316)  # 59 km da casa


@pytest.fixture
def client(db_path):
    """Un archivio con un luogo di casa e tre notti: una a casa, due riprese altrove -- che
    sono le pose che l'app ha fermato e su cui chiedera'."""
    conn = connect(db_path)
    try:
        prepara(conn)
        luogo(conn, ROMA)
        luogo(conn, ("Cima Ekar", 45.8667, 11.5167, "Europe/Rome"), casa=False)
        posa(conn, quando="2024-05-17T22:00:00Z", hash_="casa")
        posa(conn, quando="2024-05-18T22:00:00Z", coord=VICINO, hash_="fuori1")
        posa(conn, quando="2024-05-19T22:00:00Z", coord=VICINO, hash_="fuori2")
        posa(conn, quando="2024-05-20T22:00:00Z", coord=LONTANO, hash_="lontano")
        corri(conn)
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def notti(pagina):
    return pagina["unclear"]


def test_the_nights_section_asks_about_the_places_that_do_not_add_up(client):
    """Un gruppo per **posto**, non per posa e nemmeno per notte: la risposta e' un fatto sul
    posto, e vale per tutte le notti riprese li'. Le due pose a 12 km sono una domanda sola."""
    trovate = notti(review(client))
    assert len(trovate) == 2, "un gruppo per posto: 12 km e 59 km"
    vicina = next(n for n in trovate if n["frames"] == 2)
    assert vicina["distance_km"] == pytest.approx(11.9, abs=0.5)
    assert sorted(vicina["nights"]) == ["2024-05-18", "2024-05-19"]
    assert vicina["latitude"] == pytest.approx(VICINO[0], abs=0.01)


def test_a_place_says_what_the_sky_found_there(client):
    """Cosa hai ripreso in quel posto, per ricordare dov'eri (`test_review_subjects`)."""
    vicina = next(n for n in notti(review(client)) if n["frames"] == 2)
    assert vicina["subjects"] == {
        "found": [{"name": "m-31", "frames": 2}],
        "not_found": 0,
        "not_yet": 0,
    }


def test_the_places_are_proposed_with_my_sites_the_nearest_first(client):
    """Si risponde cliccando, come per i filtri e per gli oggetti: l'app mette davanti i luoghi
    che ho gia' dichiarato, il piu' vicino in cima -- e' un ordine, non una scelta."""
    lontana = next(n for n in notti(review(client)) if n["frames"] == 1)
    nomi = [c["name"] for c in lontana["candidates"]]
    assert nomi == ["Cima Ekar", "Casa"], "il piu' vicino a quelle coordinate va in cima"
    assert lontana["candidates"][0]["distance_km"] < lontana["candidates"][1]["distance_km"]


def test_the_nearest_place_stays_first_even_when_two_look_the_same(client):
    """L'ordine e' sulla distanza **vera**, non su quella arrotondata per lo schermo.

    Due luoghi a 5,31 e 5,34 km dallo stesso punto incerto: a schermo dicono tutti e due
    `5.3`, ma in cima deve restare il piu' vicino. Ordinando i candidati dopo averli arrotondati
    i due pareggiano, e siccome l'ordinamento e' stabile l'ordine cade su come il database
    restituisce i luoghi: il primo che l'utente clicca sarebbe il piu' lontano.

    I due luoghi si inseriscono **al contrario** apposta -- prima il lontano -- o il pareggio
    lascerebbe l'ordine giusto per caso e questo banco direbbe di si' senza provare niente."""
    with db(client) as conn:
        luogo(conn, ("Piu' lontano", 45.551976, 11.667, "Europe/Rome"), casa=False)
        luogo(conn, ("Piu' vicino", 45.552246, 11.667, "Europe/Rome"), casa=False)
        conn.commit()
    vicina = next(n for n in notti(review(client)) if n["frames"] == 2)
    primi = vicina["candidates"][:2]
    assert primi[0]["distance_km"] == primi[1]["distance_km"], "a schermo devono pareggiare"
    assert [c["name"] for c in primi] == ["Piu' vicino", "Piu' lontano"], vicina["candidates"]


def test_a_distance_leaves_the_api_as_the_screen_shows_it(client):
    """Quindici decimali non sono una misura: sono la rappresentazione di una float. Il backend
    manda cio' che lo schermo mostra, quindi si arrotonda **una volta**, dove la distanza esce, e
    la pagina formatta e basta. Vale per la distanza da casa e per quella dei luoghi da cliccare.

    Non si arrotonda dentro `place.distance_km`: quella serve anche a decidere se due coordinate
    sono lo stesso posto (`group.SAME_PLACE_KM`), e li' arrotondare sposterebbe la soglia."""
    for posto in notti(review(client)):
        quanto = posto["distance_km"]
        assert quanto is None or quanto == round(quanto, 1), quanto
        for vicino in posto["candidates"]:
            assert vicino["distance_km"] == round(vicino["distance_km"], 1), vicino


def test_answering_where_i_was_puts_those_poses_in_their_night(client):
    """La risposta scrive la notte **dichiarata** e rimette in coda le pose: al giro dopo hanno
    la loro notte, sul luogo che ho detto io."""
    pagina = review(client)
    gruppo = next(n for n in notti(pagina) if n["frames"] == 2)
    cima = next(c for c in gruppo["candidates"] if c["name"] == "Cima Ekar")

    esito = apply(client, unclear=[{"key": gruppo["key"], "site_id": cima["id"]}])
    assert esito["changed"] == 1 and esito["requeued"] == 2

    with db(client) as conn:
        righe = conn.execute(
            "SELECT n.night_date, n.site_id, n.site_source, COUNT(f.id) AS pose FROM nights n"
            " JOIN frames f ON f.night_id = n.id WHERE n.site_id = ? GROUP BY n.id",
            (cima["id"],),
        ).fetchall()
    assert {r["night_date"] for r in righe} == {"2024-05-18", "2024-05-19"}
    assert all(r["site_source"] == "declared" and r["pose"] == 1 for r in righe)

    dopo = notti(review(client))
    risposto = next(n for n in dopo if n["key"] == gruppo["key"])
    assert risposto["site"] == "Cima Ekar", "la risposta resta accanto al gruppo, per cambiarla"
    assert [n["key"] for n in dopo if n["site"] is None] != [gruppo["key"]], "non si richiede"


def test_an_answered_place_stays_on_the_page_but_no_longer_counts(client):
    """Un posto risposto resta in pagina, per poter cambiare idea, ma **non conta piu'** fra le cose
    da confermare: come le camere."""
    pagina = review(client)
    gruppo = next(n for n in notti(pagina) if n["frames"] == 2)
    cima = next(c for c in gruppo["candidates"] if c["name"] == "Cima Ekar")
    apply(client, unclear=[{"key": gruppo["key"], "site_id": cima["id"]}])

    dopo = review(client)
    assert gruppo["key"] in [n["key"] for n in notti(dopo)], "resta in pagina"
    schede = _domande(dopo)
    aperti = [n for n in notti(dopo) if n["site"] is None]
    assert len(aperti) == len(notti(dopo)) - 1
    assert dopo["to_confirm"] == len(schede) + len(aperti), "il posto risposto non si conta"


def test_the_answer_holds_for_the_nights_that_will_come(client):
    """La risposta e' un fatto sul **posto**: una posa nuova ripresa li' non fa richiedere
    niente. E' la stessa promessa della regola sui nomi degli oggetti."""
    gruppo = next(n for n in notti(review(client)) if n["frames"] == 2)
    cima = next(c for c in gruppo["candidates"] if c["name"] == "Cima Ekar")
    apply(client, unclear=[{"key": gruppo["key"], "site_id": cima["id"]}])

    with db(client) as conn:
        nuova = posa(conn, quando="2024-06-01T22:00:00Z", coord=VICINO, hash_="nuova")
        conn.commit()
        corri(conn)
        conn.commit()
        assert stato(conn, nuova) == ("done", None)
        assert notte_di(conn, nuova)["site_id"] == cima["id"]


def test_answering_that_i_was_at_home_is_an_answer_too(client):
    """Il caso piu' probabile di tutti: "il GPS ha sbagliato, ero a casa". E' una risposta come
    le altre, quindi la notte che ne nasce e' **dichiarata** -- se nascesse `detected` il
    trasloco di casa se la porterebbe via e la spazzata potrebbe cancellarla."""
    gruppo = next(n for n in notti(review(client)) if n["frames"] == 1)
    casa = next(c for c in gruppo["candidates"] if c["name"] == "Casa")
    apply(client, unclear=[{"key": gruppo["key"], "site_id": casa["id"]}])
    with db(client) as conn:
        righe = conn.execute(
            "SELECT site_source FROM nights WHERE site_id = ? AND night_date = '2024-05-20'",
            (casa["id"],),
        ).fetchall()
    assert [r["site_source"] for r in righe] == ["declared"]


def test_a_wrong_answer_can_be_changed(client):
    """Un clic sbagliato attribuisce centinaia di pose: si deve poter tornare indietro. Il
    gruppo resta in pagina con la risposta accanto, e rispondere di nuovo sposta tutto."""
    gruppo = next(n for n in notti(review(client)) if n["frames"] == 2)
    cima = next(c for c in gruppo["candidates"] if c["name"] == "Cima Ekar")
    casa = next(c for c in gruppo["candidates"] if c["name"] == "Casa")
    apply(client, unclear=[{"key": gruppo["key"], "site_id": cima["id"]}])

    esito = apply(client, unclear=[{"key": gruppo["key"], "site_id": casa["id"]}])
    assert esito["requeued"] == 2, "cambiare idea deve rimettere in coda le pose gia' sistemate"
    with db(client) as conn:
        dove = conn.execute(
            "SELECT s.name, COUNT(f.id) AS pose FROM frames f JOIN nights n ON n.id = f.night_id"
            " JOIN sites s ON s.id = n.site_id WHERE f.frame_hash LIKE 'fuori%' GROUP BY s.id"
        ).fetchall()
    assert [(r["name"], r["pose"]) for r in dove] == [("Casa", 2)]


def test_a_site_deleted_after_the_answer_makes_the_app_ask_again(client):
    """La risposta viaggia sul NOME del sito. Se quel sito sparisce -- o cambia nome -- la
    risposta non aggancia piu': l'app torna a chiedere invece di ripiegare su casa, che
    sarebbe attribuire delle pose a un posto che nessuno ha detto."""
    gruppo = next(n for n in notti(review(client)) if n["frames"] == 2)
    cima = next(c for c in gruppo["candidates"] if c["name"] == "Cima Ekar")
    apply(client, unclear=[{"key": gruppo["key"], "site_id": cima["id"]}])

    with db(client) as conn:
        conn.execute("UPDATE sites SET name = 'Un altro nome' WHERE id = ?", (cima["id"],))
        conn.commit()
        for frame in conn.execute(
            "SELECT id FROM frames WHERE frame_hash LIKE 'fuori%'"
        ).fetchall():
            conn.execute(
                "UPDATE frame_stages SET status = 'pending', reason = NULL"
                " WHERE stage = 'group' AND frame_id = ?",
                (frame["id"],),
            )
        conn.commit()
        corri(conn)
        conn.commit()
        fermi = conn.execute(
            "SELECT COUNT(*) FROM frame_stages s JOIN frames f ON f.id = s.frame_id"
            " WHERE s.stage = 'group' AND s.reason = 'site_unclear'"
            " AND f.frame_hash LIKE 'fuori%'"
        ).fetchone()[0]
    assert fermi == 2, "una risposta che non aggancia piu' deve tornare a essere una domanda"
    # e la pagina dice la stessa cosa dello stadio: nessuna risposta accanto, e il posto conta
    pagina = review(client)
    posto = next(n for n in notti(pagina) if n["key"] == gruppo["key"])
    assert posto["site"] is None
    schede = _domande(pagina)
    aperti = [n for n in notti(pagina) if n["site"] is None]
    assert posto in aperti and pagina["to_confirm"] == len(schede) + len(aperti)


def test_a_calibrated_copy_is_not_another_pose(client):
    """La regola di questa pagina: una copia riscritta non e' un'altra posa, e nei conteggi non
    entra. Vale anche qui, dove il numero e' cio' che fa capire quanto pesa la domanda."""
    prima = next(n for n in notti(review(client)) if n["frames"] == 2)
    with db(client) as conn:
        originale = conn.execute("SELECT id FROM frames WHERE frame_hash = 'fuori1'").fetchone()[
            "id"
        ]
        copia = posa(conn, quando="2024-05-18T22:00:00Z", coord=VICINO, hash_="copia")
        conn.execute("UPDATE frames SET copy_of = ? WHERE id = ?", (originale, copia))
        conn.commit()
        corri(conn)
        conn.commit()
    dopo = next(n for n in notti(review(client)) if n["key"] == prima["key"])
    assert dopo["frames"] == 2, "la copia calibrata non si conta"


def test_the_nights_shown_are_in_the_timezone_of_those_coordinates(db_path):
    """Le date accanto alla domanda sono le notti **di dove l'utente era**, non di casa:
    chiedere "da dove hai ripreso" e mostrare accanto le date di un altro fuso sarebbe una
    risposta a meta'.

    Le 18:00 UTC del 18 maggio, in Arizona, sono le 11:00 del mattino: la notte e' quella del
    17, che sta finendo. Col fuso di casa (Roma) sarebbero le 20:00, cioe' la notte del 18."""
    conn = connect(db_path)
    try:
        prepara(conn)
        luogo(conn, ROMA)
        posa(conn, quando="2024-05-18T18:00:00Z", coord=ARIZONA[1:3], hash_="deserto")
        corri(conn)
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        gruppo = notti(review(c))[0]
    assert gruppo["nights"] == ["2024-05-17"]


def test_the_answer_does_not_follow_a_reused_row_number(client):
    """Gli id delle righe si riusano: un sito senza notti si puo' cancellare, e il prossimo che
    nasce eredita il suo numero. Se la risposta viaggiasse sull'id, quelle pose finirebbero **in
    silenzio** su un luogo che nessuno ha mai indicato -- e' la stessa lezione delle risposte
    sugli oggetti, dove la chiave e' lo slug e mai la riga."""
    gruppo = next(n for n in notti(review(client)) if n["frames"] == 1)
    cima = next(c for c in gruppo["candidates"] if c["name"] == "Cima Ekar")
    apply(client, unclear=[{"key": gruppo["key"], "site_id": cima["id"]}])

    with db(client) as conn:
        conn.execute("DELETE FROM nights WHERE site_id = ?", (cima["id"],))
        conn.execute("DELETE FROM sites WHERE id = ?", (cima["id"],))
        nuovo = conn.execute(
            "INSERT INTO sites(name, latitude, longitude, timezone, created_at)"
            " VALUES('Un altro posto', 40.0, 10.0, 'Europe/Rome', ?)",
            (now_iso(),),
        ).lastrowid
        assert nuovo == cima["id"], "SQLite non ha riusato l'id: il test non prova niente"
        conn.execute(
            "UPDATE frame_stages SET status = 'pending', reason = NULL WHERE stage = 'group'"
        )
        conn.commit()
        corri(conn)
        conn.commit()
        dove = conn.execute(
            "SELECT s.name FROM frames f JOIN nights n ON n.id = f.night_id"
            " JOIN sites s ON s.id = n.site_id WHERE f.frame_hash = 'lontano'"
        ).fetchone()
    assert dove is None, "la risposta ha seguito il numero di riga su un luogo mai indicato"


def test_an_answer_to_a_place_that_is_not_there_is_a_404(client):
    r = client.post("/api/v1/review/apply", json={"unclear": [{"key": "non|esiste", "site_id": 1}]})
    assert r.status_code == 404 and r.json()["detail"]["code"] == "not_found"


def test_an_answer_to_a_site_that_does_not_exist_is_refused(client):
    gruppo = notti(review(client))[0]
    r = client.post(
        "/api/v1/review/apply", json={"unclear": [{"key": gruppo["key"], "site_id": 999}]}
    )
    assert r.status_code == 404 and r.json()["detail"]["code"] == "not_found"


def test_an_archive_with_nothing_to_ask_asks_nothing(client_pulito):
    """Se tutte le pose sono a casa, la sezione non esiste: l'app non inventa una domanda."""
    pagina = review(client_pulito)
    assert notti(pagina) == []
    # e il contatore non porta domande che non ci sono: conta solo le schede da confermare
    assert pagina["to_confirm"] == len(_domande(pagina))


def _domande(pagina):
    """Le altre domande della pagina: gli oggetti senza risposta, i filtri da dire, le grafie
    che sembrano un pezzo solo."""
    oggetti = [o for o in pagina["objects"] if o["answer"] is None]
    return oggetti + pagina["filters"] + pagina["lookalikes"]


@pytest.fixture
def client_pulito(db_path):
    conn = connect(db_path)
    try:
        prepara(conn)
        luogo(conn, ROMA)
        posa(conn, quando="2024-05-17T22:00:00Z", hash_="casa")
        corri(conn)
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def test_the_places_to_answer_count_in_what_is_left_to_confirm(client):
    """Sono lavoro che aspetta una risposta: entrano nel contatore della pagina. E **non** si
    chiudono con l'Applica come le schede -- "ho visto la pagina" non e' una risposta a "da
    dove hai ripreso", e finche' non rispondi l'app deve continuare a chiedere."""
    pagina = review(client)
    schede = _domande(pagina)
    assert pagina["to_confirm"] == len(schede) + len(notti(pagina)) == len(schede) + 2

    apply(client)  # un'Applica vuota: conferma cio' che si e' visto, non risponde
    dopo = review(client)
    assert len(notti(dopo)) == 2, "una domanda aperta non si chiude guardandola"
    assert dopo["to_confirm"] == 2, "restano solo le due domande: le schede sono confermate"


def test_the_answer_is_written_where_it_survives_a_reset(client):
    """La risposta vive in `declarations`, sulle coordinate: azzerare il derivato non la porta
    via, ed e' quello che la rende una risposta e non un lucchetto."""
    gruppo = next(n for n in notti(review(client)) if n["frames"] == 1)
    casa = next(c for c in gruppo["candidates"] if c["name"] == "Casa")
    apply(client, unclear=[{"key": gruppo["key"], "site_id": casa["id"]}])
    with db(client) as conn:
        assert decl.site_for_coordinates(conn, gruppo["key"]) == "Casa"


def test_a_place_already_answered_stays_with_its_nights(db_path):
    """Un posto a cui l'utente ha gia' risposto resta in elenco con la sua notte: coordinate in
    Arizona, risposta "ero a casa", e la notte e' quella del 18."""
    conn = connect(db_path)
    try:
        prepara(conn)
        luogo(conn, ROMA)
        posa(
            conn,
            quando="2024-05-18T22:00:00.000",
            coord=(34.0, -111.0),
            hash_="gps sballato",
        )
        corri(conn)
        conn.commit()
    finally:
        conn.close()

    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        gruppo = next(n for n in notti(review(c)) if n["frames"] == 1)
        casa = next(s for s in gruppo["candidates"] if s["name"] == "Casa")
        apply(c, unclear=[{"key": gruppo["key"], "site_id": casa["id"]}])
        risposto = next(n for n in notti(review(c)) if n["frames"] == 1)

    assert risposto["site"] == "Casa"
    assert risposto["nights"] == ["2024-05-18"], risposto["nights"]
