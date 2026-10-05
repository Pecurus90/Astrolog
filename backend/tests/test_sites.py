"""Il luogo da cui si osserva: si dice per nome o a mano, l'app ne ricava fuso e altitudine,
del cielo si dice quello che si sa, e uno solo e' quello di casa.

Vincolo di questi test: **non toccano internet**. Il recinto della suite (`conftest.py`) ferma
l'unica funzione di `place` che tocca la rete; chi vuole un servizio lo finge da se' (`answers`).
"""

import pytest
from fastapi.testclient import TestClient

from astrolog import place
from astrolog.api.app import create_app
from astrolog.clock import now_iso
from astrolog.db.connect import connect
from astrolog.spine.stages import mark_pending, set_status
from conftest import rete_giu

ASIAGO = {"name": "Asiago", "latitude": 45.8667, "longitude": 11.5167}


def answers(monkeypatch, by_url):
    """Un servizio finto che risponde in base a cosa c'e' nell'URL."""

    def fetch(url):
        for piece, payload in by_url.items():
            if piece in url:
                return payload
        raise AssertionError(f"nessuna risposta preparata per {url}")

    monkeypatch.setattr(place, "_fetch", fetch)


def create(client_vuoto, **body):
    r = client_vuoto.post("/api/v1/sites", json={**ASIAGO, **body})
    assert r.status_code == 201, r.text
    return r.json()


def sites(client_vuoto):
    r = client_vuoto.get("/api/v1/sites")
    assert r.status_code == 200, r.text
    return r.json()


# --- dire dove si osserva ------------------------------------------------------------------


def test_site_search_by_name(client_vuoto, monkeypatch):
    """Si scrive il nome del posto e si scelgono le coordinate da un elenco. Il servizio non
    scrive niente: la ricerca e' un gesto, e il luogo nasce solo quando lo si crea."""
    answers(
        monkeypatch,
        {
            "nominatim": [
                {
                    "display_name": "Asiago, Vicenza, Veneto, Italia",
                    "lat": "45.8667",
                    "lon": "11.5167",
                },
                {"display_name": "Asiago, Alberta, Canada", "lat": "53.5", "lon": "-113.5"},
            ]
        },
    )
    r = client_vuoto.get("/api/v1/places", params={"q": "Asiago"})
    assert r.status_code == 200, r.text
    found = r.json()["items"]
    assert [p["name"] for p in found][0].startswith("Asiago, Vicenza")
    assert found[0]["latitude"] == pytest.approx(45.8667)
    assert sites(client_vuoto)["total"] == 0  # cercare non crea niente


def test_searching_without_network_gives_an_empty_list_not_an_error(client_vuoto, offline):
    r = client_vuoto.get("/api/v1/places", params={"q": "Asiago"})
    assert r.status_code == 200
    assert r.json()["items"] == []


def test_site_manual_coordinates(client_vuoto, offline):
    """Senza rete si scrivono le coordinate a mano e il luogo nasce lo stesso: il fuso arriva
    comunque (si ricava offline), l'altitudine resta VUOTA -- mai zero di ripiego."""
    site = create(client_vuoto)
    assert site["latitude"] == pytest.approx(45.8667)
    assert site["timezone"] == "Europe/Rome"
    assert site["elevation_m"] is None
    assert site["sky_sqm"] is None and site["sky_source"] is None and site["bortle"] is None


def test_coordinates_outside_the_world_are_refused(client_vuoto, offline):
    for bad in ({"latitude": 91}, {"latitude": -91}, {"longitude": 181}, {"name": ""}):
        r = client_vuoto.post("/api/v1/sites", json={**ASIAGO, **bad})
        assert r.status_code == 422, (bad, r.text)


def test_two_sites_cannot_share_a_name(client_vuoto, offline):
    create(client_vuoto)
    r = client_vuoto.post("/api/v1/sites", json=ASIAGO)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "site_name_taken"


def test_site_elevation_arrives_from_the_coordinates(client_vuoto, monkeypatch):
    """L'altitudine non si chiede all'utente: si ricava dalle coordinate."""
    answers(monkeypatch, {"elevation": {"elevation": [1023.0]}})
    assert create(client_vuoto)["elevation_m"] == pytest.approx(1023.0)


def test_an_elevation_written_by_hand_wins_over_the_service(client_vuoto, monkeypatch):
    """Chi ha un GPS sotto mano ha ragione lui: il servizio non lo sovrascrive."""
    answers(monkeypatch, {"elevation": {"elevation": [1023.0]}})
    assert create(client_vuoto, elevation_m=1350.0)["elevation_m"] == pytest.approx(1350.0)


# --- il cielo: tre strade, un numero solo --------------------------------------------------


def test_site_sky_three_ways(client_vuoto, monkeypatch):
    """La luminosita' si misura, si fa chiedere al servizio, o si sceglie sulla scala: tre
    strade, un numero solo, e accanto sempre COME lo si sa."""
    answers(monkeypatch, {"lightpollutionmap": "0.5", "elevation": {"elevation": [1000.0]}})

    misurato = create(client_vuoto, name="Misurato", sky_sqm=21.3)
    assert misurato["sky_sqm"] == pytest.approx(21.3) and misurato["sky_source"] == "measured"

    scelto = create(client_vuoto, name="Scelto", bortle=4)
    assert scelto["sky_source"] == "scale"
    assert scelto["bortle"] == 4  # andata e ritorno: la classe scelta si ritrova

    # il servizio: solo con la chiave, che sta in Impostazioni e non nel wizard
    senza = create(client_vuoto, name="Senza chiave")
    assert senza["sky_sqm"] is None and senza["sky_source"] is None

    client_vuoto.patch("/api/v1/settings", json={"values": {"sky_service_key": "k"}})
    chiesto = create(client_vuoto, name="Chiesto")
    assert chiesto["sky_source"] == "service"
    assert chiesto["sky_sqm"] == pytest.approx(20.51, abs=0.02)


def test_the_bortle_is_derived_and_never_stored(client_vuoto, offline):
    """La classe si DERIVA e non si memorizza: non e' una colonna del database, e non compare
    mai da sola -- la misura le sta sempre accanto."""
    site = create(client_vuoto, sky_sqm=20.80)
    assert site["bortle"] == 4 and site["sky_sqm"] == pytest.approx(20.80)

    with connect(client_vuoto.app.state.db_path) as conn:
        row = conn.execute("SELECT * FROM sites WHERE id = ?", (site["id"],)).fetchone()
    assert "bortle" not in row.keys()  # noqa: SIM118 - Row itera i valori, non le chiavi

    client_vuoto.patch(f"/api/v1/sites/{site['id']}", json={"sky_sqm": 18.2})
    assert client_vuoto.get("/api/v1/sites").json()["items"][0]["bortle"] == 7


def test_a_sky_brightness_outside_the_scale_is_refused(client_vuoto, offline):
    for bad in ({"sky_sqm": 9.0}, {"sky_sqm": 24.0}, {"bortle": 0}, {"bortle": 10}):
        r = client_vuoto.post("/api/v1/sites", json={**ASIAGO, **bad})
        assert r.status_code == 422, (bad, r.text)


# --- piu' luoghi, uno di casa --------------------------------------------------------------


def test_sites_many_and_one_default(client_vuoto, offline):
    """Si aggiungono tutti i luoghi che si vogliono; uno solo e' quello di casa, e dirlo di
    un altro lo toglie al primo -- non ne restano due, mai."""
    casa = create(client_vuoto, name="Giardino di casa", is_default=True)
    monte = create(client_vuoto, name="Monte Grappa", latitude=45.87, longitude=11.80)
    assert casa["is_default"] is True and monte["is_default"] is False

    r = client_vuoto.post(f"/api/v1/sites/{monte['id']}/default")
    assert r.status_code == 200 and r.json()["is_default"] is True

    elenco = sites(client_vuoto)
    assert elenco["total"] == 2
    assert [s["is_default"] for s in elenco["items"] if s["id"] == casa["id"]] == [False]

    # e uno nato dopo non ruba il posto a quello di casa
    assert create(client_vuoto, name="Terzo", latitude=0.0, longitude=0.0)["is_default"] is False


def test_the_very_first_site_becomes_the_home_one_by_itself(db_path, offline):
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        assert create(c)["is_default"] is True


def test_editing_the_coordinates_recomputes_the_timezone(client_vuoto, offline):
    site = create(client_vuoto)
    r = client_vuoto.patch(
        f"/api/v1/sites/{site['id']}", json={"latitude": 40.71, "longitude": -74.01}
    )
    assert r.status_code == 200 and r.json()["timezone"] == "America/New_York"


def test_a_site_that_is_nowhere_is_not_found(client_vuoto, offline):
    assert client_vuoto.patch("/api/v1/sites/999", json={"name": "x"}).status_code == 404
    assert client_vuoto.delete("/api/v1/sites/999").status_code == 404
    assert client_vuoto.post("/api/v1/sites/999/default").status_code == 404


# --- cancellare, e cosa lo impedisce -------------------------------------------------------


def test_site_with_nights_is_not_deleted(client_vuoto, offline):
    """Un luogo che ha gia' delle notti non si perde per sbaglio: l'app si rifiuta e dice
    quante notti lo tengono."""
    site = create(client_vuoto)
    with connect(client_vuoto.app.state.db_path) as conn:
        for day in ("2024-05-17", "2024-05-18", "2024-09-01"):
            conn.execute(
                "INSERT INTO nights(site_id, night_date, created_at) VALUES(?, ?, ?)",
                (site["id"], day, now_iso()),
            )

    r = client_vuoto.delete(f"/api/v1/sites/{site['id']}")
    assert r.status_code == 409
    assert r.json()["detail"] == {"code": "site_has_nights", "nights": 3}
    assert sites(client_vuoto)["total"] == 1  # ed e' ancora li'


def test_a_site_without_nights_goes_away(client_vuoto, offline):
    site = create(client_vuoto)
    r = client_vuoto.delete(f"/api/v1/sites/{site['id']}")
    assert r.status_code == 200 and r.json() == {"site_id": site["id"], "deleted": True}
    assert sites(client_vuoto)["total"] == 0


def test_the_list_says_how_many_nights_hold_each_site(client_vuoto, offline):
    site = create(client_vuoto)
    with connect(client_vuoto.app.state.db_path) as conn:
        conn.execute(
            "INSERT INTO nights(site_id, night_date, created_at) VALUES(?, '2024-05-17', ?)",
            (site["id"], now_iso()),
        )
    assert sites(client_vuoto)["items"][0]["nights"] == 1


# --- cambiare un luogo ---------------------------------------------------------------------


def test_an_elevation_written_by_hand_in_a_change_wins_too(client_vuoto, offline):
    site = create(client_vuoto)
    r = client_vuoto.patch(f"/api/v1/sites/{site['id']}", json={"elevation_m": 1350.0})
    assert r.status_code == 200 and r.json()["elevation_m"] == pytest.approx(1350.0)


def test_moving_a_site_redoes_only_what_came_from_the_service(client_vuoto, monkeypatch):
    """La luminosita' chiesta al servizio e' una funzione delle coordinate: se il luogo si
    sposta, si richiede. Quella MISURATA e' la parola dell'utente, e nessuno la tocca."""
    answers(monkeypatch, {"lightpollutionmap": "0.5", "elevation": {"elevation": [1000.0]}})
    client_vuoto.patch("/api/v1/settings", json={"values": {"sky_service_key": "k"}})

    dal_servizio = create(client_vuoto, name="Dal servizio")
    assert dal_servizio["sky_source"] == "service"
    answers(monkeypatch, {"lightpollutionmap": "12.0", "elevation": {"elevation": [120.0]}})
    spostato = client_vuoto.patch(
        f"/api/v1/sites/{dal_servizio['id']}", json={"latitude": 45.46, "longitude": 9.19}
    ).json()
    assert spostato["sky_source"] == "service"
    assert spostato["sky_sqm"] == pytest.approx(17.37, abs=0.02)  # una citta': cielo peggiore
    assert spostato["elevation_m"] == pytest.approx(120.0)

    misurato = create(client_vuoto, name="Misurato", latitude=46.0, longitude=11.0, sky_sqm=21.3)
    fermo = client_vuoto.patch(
        f"/api/v1/sites/{misurato['id']}", json={"latitude": 46.1, "longitude": 11.1}
    ).json()
    assert fermo["sky_sqm"] == pytest.approx(21.3) and fermo["sky_source"] == "measured"


def test_renaming_a_site_onto_another_name_is_refused(client_vuoto, offline):
    create(client_vuoto)
    altro = create(client_vuoto, name="Monte Grappa", latitude=45.87, longitude=11.80)
    r = client_vuoto.patch(f"/api/v1/sites/{altro['id']}", json={"name": "Asiago"})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "site_name_taken"


def test_an_empty_field_says_why_it_is_empty(client_vuoto, offline):
    """Un campo vuoto porta il suo motivo: un null da solo non distingue "non l'ho saputo" da
    "non l'ho chiesto", e la pagina non saprebbe cosa scrivere."""
    site = create(client_vuoto)
    assert site["unknown"] == ["site_no_elevation", "site_no_sky"]
    assert "site_no_timezone" not in site["unknown"]  # il fuso si sa anche senza rete

    # anche in mezzo all'oceano un fuso c'e': e' di comodo, ma e' un nome vero
    mare = create(client_vuoto, name="In mezzo al mare", latitude=30.0, longitude=-40.0)
    assert mare["timezone"] == "Etc/GMT+3" and "site_no_timezone" not in mare["unknown"]


def test_a_full_site_has_nothing_unknown(client_vuoto, monkeypatch):
    answers(monkeypatch, {"elevation": {"elevation": [1023.0]}})
    assert create(client_vuoto, sky_sqm=21.3)["unknown"] == []


def test_an_impossible_sky_from_the_service_is_not_a_sky(client_vuoto, monkeypatch):
    """Un servizio che risponde una luminosita' assurda ha risposto un guasto: non si salva,
    e non diventa un errore in faccia a chi sta creando il luogo."""
    answers(monkeypatch, {"lightpollutionmap": "50000", "elevation": {"elevation": [120.0]}})
    client_vuoto.patch("/api/v1/settings", json={"values": {"sky_service_key": "k"}})
    site = create(client_vuoto)
    assert site["sky_sqm"] is None and site["sky_source"] is None
    assert "site_no_sky" in site["unknown"]


def test_a_field_sent_empty_is_cleared(client_vuoto, monkeypatch):
    """Mandare un campo a vuoto vuol dire cancellarlo: senza, una luminosita' sbagliata non si
    toglierebbe piu'.

    Si prova con la rete VIVA, ed e' il punto: con i servizi muti il campo finirebbe vuoto
    comunque, e il test resterebbe verde anche senza la regola."""
    answers(monkeypatch, {"lightpollutionmap": "0.5", "elevation": {"elevation": [1023.0]}})
    client_vuoto.patch("/api/v1/settings", json={"values": {"sky_service_key": "k"}})
    site = create(client_vuoto, sky_sqm=21.3, elevation_m=1000.0)
    dopo = client_vuoto.patch(
        f"/api/v1/sites/{site['id']}", json={"sky_sqm": None, "elevation_m": None}
    ).json()
    assert dopo["sky_sqm"] is None and dopo["sky_source"] is None
    assert dopo["elevation_m"] is None and dopo["elevation_source"] is None
    assert dopo["unknown"] == ["site_no_elevation", "site_no_sky"]


def test_a_required_field_sent_empty_is_refused_and_says_which(client_vuoto, offline):
    """Nome e coordinate non si cancellano: senza, il luogo non e' un luogo."""
    site = create(client_vuoto)
    for bad in ({"name": None}, {"latitude": None}, {"longitude": None}):
        r = client_vuoto.patch(f"/api/v1/sites/{site['id']}", json=bad)
        assert r.status_code == 422, (bad, r.text)
        assert r.json()["detail"]["code"] == "field_required"
        assert r.json()["detail"]["fields"] == list(bad)


def test_moving_a_site_keeps_what_the_user_wrote_and_redoes_what_came_from_the_service(
    client_vuoto, monkeypatch
):
    """Spostare il luogo rifa' cio' che dalle coordinate veniva, e lascia stare cio' che
    l'utente ha scritto. Per questo dell'altitudine si registra la provenienza, come del
    cielo: un numero rimasto attaccato a coordinate nuove sarebbe indistinguibile da una
    misura."""
    answers(monkeypatch, {"elevation": {"elevation": [1023.0]}})
    a_mano = create(client_vuoto, name="Scritta a mano", elevation_m=1350.0)
    dal_servizio = create(client_vuoto, name="Dal servizio", latitude=46.0, longitude=11.0)
    assert a_mano["elevation_source"] == "declared"
    assert dal_servizio["elevation_source"] == "service"

    rete_giu(monkeypatch)
    fermo = client_vuoto.patch(
        f"/api/v1/sites/{a_mano['id']}", json={"latitude": 45.87, "longitude": 11.80}
    ).json()
    assert fermo["elevation_m"] == pytest.approx(1350.0)  # e' la parola dell'utente
    assert fermo["elevation_source"] == "declared"

    svuotato = client_vuoto.patch(
        f"/api/v1/sites/{dal_servizio['id']}", json={"latitude": 45.46, "longitude": 9.19}
    ).json()
    # 1023 m attaccati alle coordinate di Milano sarebbero un numero che nessuno ha saputo
    assert svuotato["elevation_m"] is None and svuotato["elevation_source"] is None
    assert "site_no_elevation" in svuotato["unknown"]


def test_moving_a_site_empties_a_sky_that_came_from_the_service(client_vuoto, monkeypatch):
    """La stessa regola per il cielo: quello chiesto al servizio si richiede, e se il servizio
    tace resta vuoto col suo motivo invece di seguire il luogo altrove."""
    answers(monkeypatch, {"lightpollutionmap": "0.5", "elevation": {"elevation": [1000.0]}})
    client_vuoto.patch("/api/v1/settings", json={"values": {"sky_service_key": "k"}})
    site = create(client_vuoto)
    assert site["sky_source"] == "service"

    rete_giu(monkeypatch)
    spostato = client_vuoto.patch(
        f"/api/v1/sites/{site['id']}", json={"latitude": 45.46, "longitude": 9.19}
    ).json()
    assert spostato["sky_sqm"] is None and spostato["sky_source"] is None
    assert "site_no_sky" in spostato["unknown"]


def _notte(conn, site_id, data, source="detected"):
    return conn.execute(
        "INSERT INTO nights(site_id, night_date, site_source, created_at) VALUES(?, ?, ?, 'now')",
        (site_id, data, source),
    ).lastrowid


def test_moving_home_takes_along_the_nights_the_app_assigned(client_vuoto, offline):
    """Chi cambia il luogo di casa sta dicendo "da adesso osservo di qui": le notti che
    **l'app** aveva attribuito lo seguono, perche' erano un'ipotesi e non una scelta.

    Quelle che l'utente ha dichiarato no: sono una sua risposta, e nessuno stadio ha il potere
    di spostarla. E' la stessa regola del lucchetto sugli oggetti."""
    casa = create(client_vuoto)
    nuova = create(client_vuoto, name="Passo Rolle", latitude=46.30, longitude=11.79)
    with connect(client_vuoto.app.state.db_path) as conn:
        _notte(conn, casa["id"], "2024-05-17")
        _notte(conn, casa["id"], "2024-05-18", source="declared")

    assert client_vuoto.post(f"/api/v1/sites/{nuova['id']}/default").status_code == 200

    with connect(client_vuoto.app.state.db_path) as conn:
        righe = dict(conn.execute("SELECT night_date, site_id FROM nights").fetchall())
    assert righe["2024-05-17"] == nuova["id"], "la notte attribuita dall'app non ha seguito casa"
    assert righe["2024-05-18"] == casa["id"], "una notte dichiarata non si sposta da sola"


def test_a_night_that_would_collide_stays_where_it_is(client_vuoto, offline):
    """Due notti della stessa data non possono stare sullo stesso luogo. Se il trasloco ne
    creasse una gia' presente, quella resta dov'e' invece di far fallire il cambio: si perde
    un'attribuzione dubbia, mai una posa -- e l'utente puo' sempre spostarla a mano."""
    casa = create(client_vuoto)
    nuova = create(client_vuoto, name="Passo Rolle", latitude=46.30, longitude=11.79)
    with connect(client_vuoto.app.state.db_path) as conn:
        _notte(conn, casa["id"], "2024-05-17")
        _notte(conn, nuova["id"], "2024-05-17", source="declared")

    assert client_vuoto.post(f"/api/v1/sites/{nuova['id']}/default").status_code == 200

    with connect(client_vuoto.app.state.db_path) as conn:
        quante = conn.execute(
            "SELECT site_id, COUNT(*) FROM nights WHERE night_date = '2024-05-17' GROUP BY site_id"
        ).fetchall()
    assert dict(quante) == {casa["id"]: 1, nuova["id"]: 1}


def test_moving_home_to_another_timezone_puts_the_nights_back_in_the_queue(client_vuoto, offline):
    """Il fuso decide **dove si taglia** una notte: traslocando da Roma all'Arizona le date
    tagliate nel fuso vecchio non sono piu' vere. Le notti adottate non si limitano a cambiare
    luogo -- le loro pose tornano in coda per `group`, che le ritaglia col fuso nuovo.

    Senza, la colonna direbbe "YYYY-MM-DD nel fuso del sito" e sarebbe falsa proprio per le
    righe appena spostate."""
    casa = create(client_vuoto)
    lontano = create(client_vuoto, name="Deserto", latitude=33.45, longitude=-111.98)
    with connect(client_vuoto.app.state.db_path) as conn:
        notte = _notte(conn, casa["id"], "2024-05-17")
        frame = conn.execute(
            "INSERT INTO frames(frame_hash, image_type, date_obs, night_id, header_json,"
            " created_at) VALUES('h', 'light', '2024-05-18T18:00:00.000', ?, '[]', 'now')",
            (notte,),
        ).lastrowid
        mark_pending(conn, frame)
        set_status(conn, frame, "group", "done")

    assert client_vuoto.post(f"/api/v1/sites/{lontano['id']}/default").status_code == 200

    with connect(client_vuoto.app.state.db_path) as conn:
        riga = conn.execute(
            "SELECT status FROM frame_stages WHERE frame_id = ? AND stage = 'group'", (frame,)
        ).fetchone()
    assert riga["status"] == "pending", "la notte ha cambiato fuso e nessuno la ritaglia"


def test_two_nights_of_the_same_date_do_not_collide_while_moving(client_vuoto, offline):
    """Due notti della stessa data su due luoghi diversi, che traslocano **insieme**, si
    scontrerebbero fra loro: il database non ne ammette due uguali sullo stesso luogo. Si
    sposta la prima e l'altra resta dov'e', invece di far fallire il trasloco."""
    casa = create(client_vuoto)
    cima = create(client_vuoto, name="Cima", latitude=46.05, longitude=11.316)
    nuova = create(client_vuoto, name="Deserto", latitude=45.90, longitude=11.10)
    with connect(client_vuoto.app.state.db_path) as conn:
        _notte(conn, casa["id"], "2024-05-17")
        _notte(conn, cima["id"], "2024-05-17")

    assert client_vuoto.post(f"/api/v1/sites/{nuova['id']}/default").status_code == 200

    with connect(client_vuoto.app.state.db_path) as conn:
        dove = [r[0] for r in conn.execute("SELECT site_id FROM nights ORDER BY id")]
    assert dove.count(nuova["id"]) == 1, "una delle due deve aver traslocato"
    assert len(dove) == 2 and len(set(dove)) == 2, "l'altra resta dov'era, e nessuna si perde"


def test_a_site_where_there_is_no_timezone_says_so(client_vuoto, offline, monkeypatch):
    """Dove un fuso non si riconosce il campo resta vuoto COL SUO MOTIVO.
    La libreria dei confini un nome lo trova sempre, anche in mezzo all'oceano: qui si finge
    che non lo trovi, perche' una guardia mai vista rossa non ha dimostrato niente."""
    monkeypatch.setattr(place, "get_tz", lambda lon, lat: None)
    site = create(client_vuoto)
    assert site["timezone"] is None
    assert "site_no_timezone" in site["unknown"]
