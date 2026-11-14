"""Il Bortle misurato a schermo (docs/domini/sito.md): l'app propone, l'utente sceglie «Usa» o
«Lascia»; dopo «Lascia» si ripropone solo se la classe misurata cambia; i dati scarsi si dicono."""

import json

import test_site_sky as sky
from astrolog.api.deps import get_db
from astrolog.db.connect import connect, create_database
from astrolog.spine import backup
from conftest import LATER
from test_sites import create as _create_site


def create(client, **body):
    """Il cielo segue dietro le quinte: lo si aspetta prima di scriverne uno finto."""
    site = _create_site(client, **body)
    client.app.state.behind.join(10.0)
    return site


_MARKS = json.dumps([{"month": (10 + i) % 12 + 1, "measured": i % 2 == 0} for i in range(12)])


def test_the_site_says_its_twelve_months_as_written(client_vuoto, db_path, offline):
    site = create(client_vuoto, bortle=4)
    _measured(db_path, site["id"], 21.4)
    assert _site(client_vuoto, site["id"])["measured"]["month_marks"] == json.loads(_MARKS)


def _measured(db_path, site_id, sqm, nights=40, months=10):
    conn = connect(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO site_sky_measures (site_id, nights, months, sqm, first_night,"
        " last_night, marks_json, computed_at)"
        " VALUES (?, ?, ?, ?, '2025-01-10', '2025-10-20', ?, ?)",
        (site_id, nights, months, sqm, _MARKS, LATER),
    )
    conn.commit()
    conn.close()


def _site(client, site_id):
    (site,) = [s for s in client.get("/api/v1/sites").json()["items"] if s["id"] == site_id]
    return site


def test_the_measures_propose_another_class(client_vuoto, db_path, offline):
    site = create(client_vuoto, bortle=6)
    _measured(db_path, site["id"], 21.4)
    measured = _site(client_vuoto, site["id"])["measured"]
    assert measured == {
        "status": "enough", "nights": 40, "months": 10, "sqm": 21.4, "bortle": 4,
        "first_night": "2025-01-10", "last_night": "2025-10-20", "propose": True,
        "month_marks": json.loads(_MARKS),
    }  # fmt: skip


def test_the_same_class_is_not_proposed(client_vuoto, db_path, offline):
    site = create(client_vuoto, sky_sqm=21.35)
    _measured(db_path, site["id"], 21.4)
    assert _site(client_vuoto, site["id"])["measured"]["propose"] is False


def test_a_site_without_a_sky_is_proposed_one(client_vuoto, db_path, offline):
    """Marco, 5/11/2026: e' il caso in cui la misura serve di piu'."""
    site = create(client_vuoto)
    assert site["sky_sqm"] is None
    _measured(db_path, site["id"], 21.4)
    assert _site(client_vuoto, site["id"])["measured"]["propose"] is True


def test_too_few_data_say_how_many_nights_in_how_many_months(client_vuoto, db_path, offline):
    site = create(client_vuoto, bortle=4)
    assert site["measured"] == {
        "status": "too_few", "nights": 0, "months": 0, "sqm": None, "bortle": None,
        "first_night": None, "last_night": None, "propose": False, "month_marks": [],
    }  # fmt: skip
    _measured(db_path, site["id"], None, nights=5, months=3)
    measured = _site(client_vuoto, site["id"])["measured"]
    assert (measured["status"], measured["nights"], measured["months"]) == ("too_few", 5, 3)
    assert measured["propose"] is False


def test_use_writes_the_measure_with_its_nights(client_vuoto, db_path, offline):
    site = create(client_vuoto, bortle=6)
    _measured(db_path, site["id"], 21.4)
    r = client_vuoto.post(f"/api/v1/sites/{site['id']}/sky/use")
    assert r.status_code == 200, r.text
    used = r.json()
    assert (used["sky_sqm"], used["sky_source"], used["sky_nights"]) == (21.4, "frames", 40)
    assert used["bortle"] == 4 and used["measured"]["propose"] is False


def test_use_without_enough_data_is_refused(client_vuoto, db_path, offline):
    site = create(client_vuoto, bortle=6)
    _measured(db_path, site["id"], None, nights=5, months=3)
    r = client_vuoto.post(f"/api/v1/sites/{site['id']}/sky/use")
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "site_sky_not_measured"


def test_dismissed_it_comes_back_only_when_the_class_changes(client_vuoto, db_path, offline):
    site = create(client_vuoto, bortle=6)
    _measured(db_path, site["id"], 21.4)
    r = client_vuoto.post(f"/api/v1/sites/{site['id']}/sky/dismiss")
    assert r.status_code == 200, r.text
    assert r.json()["measured"]["propose"] is False
    assert r.json()["sky_source"] == "scale"  # il sito resta com'era
    _measured(db_path, site["id"], 21.38)  # stessa classe: tace
    assert _site(client_vuoto, site["id"])["measured"]["propose"] is False
    _measured(db_path, site["id"], 21.0)  # classe 5: di nuovo
    assert _site(client_vuoto, site["id"])["measured"]["propose"] is True


def test_a_sky_written_by_hand_is_not_counted_in_nights(client_vuoto, db_path, offline):
    site = create(client_vuoto, bortle=6)
    _measured(db_path, site["id"], 21.4)
    client_vuoto.post(f"/api/v1/sites/{site['id']}/sky/use")
    r = client_vuoto.patch(f"/api/v1/sites/{site['id']}", json={"sky_sqm": 20.0})
    assert (r.json()["sky_source"], r.json()["sky_nights"]) == ("measured", None)


def test_use_and_dismiss_survive_a_lost_database(client_vuoto, db_path, tmp_path, offline):
    """Sono risposte dell'utente (ADR 0017): tornano dal file, legate al sito per nome."""
    used = create(client_vuoto, bortle=6)
    kept = create(client_vuoto, name="Monte", latitude=46.0, longitude=11.0, bortle=6)
    _measured(db_path, used["id"], 21.4)
    _measured(db_path, kept["id"], 21.4)
    client_vuoto.post(f"/api/v1/sites/{used['id']}/sky/use")
    client_vuoto.post(f"/api/v1/sites/{kept['id']}/sky/dismiss")
    conn = connect(db_path)
    data = backup.collect(conn, this_machine=True)
    conn.close()
    create_database(tmp_path / "nuovo.db")
    other = connect(tmp_path / "nuovo.db")
    backup.restore(other, data)
    rows = other.execute(
        "SELECT s.name, s.sky_source, s.sky_nights, d.bortle FROM sites s"
        " LEFT JOIN site_sky_dismissed d ON d.site_id = s.id ORDER BY s.name"
    ).fetchall()
    other.close()
    assert [tuple(r) for r in rows] == [("Asiago", "frames", 40, None), ("Monte", "scale", None, 4)]


def test_a_file_without_nights_restores_a_sky_from_the_frames(client_vuoto, db_path, offline):
    """Un file scritto prima del passo 27 non porta `sky_nights`: il cielo del file vale intero,
    non mezzo sopra la misura dai frame (il CHECK lo rifiuterebbe)."""
    site = create(client_vuoto, bortle=6)
    _measured(db_path, site["id"], 21.4)
    client_vuoto.post(f"/api/v1/sites/{site['id']}/sky/use")
    old = {"name": site["name"], "latitude": site["latitude"], "longitude": site["longitude"],
           "sky_sqm": 20.5, "sky_source": "measured"}  # fmt: skip
    conn = connect(db_path)
    backup.restore(conn, {"version": backup.VERSION, "sites": [old]})
    row = conn.execute("SELECT sky_sqm, sky_source, sky_nights FROM sites").fetchone()
    conn.close()
    assert tuple(row) == (20.5, "measured", None)


def test_an_imported_site_finds_its_sky_on_the_frames_already_there(
    client_vuoto, db_path, tmp_path, offline
):
    """Anche l'import e' una scrittura dei siti: il cielo si riscrive dietro le quinte, senza
    aspettare la scansione."""
    conn = connect(db_path)
    sky._nights_in_four_seasons(conn, sky._measured(conn, tmp_path))
    conn.commit()
    conn.close()
    sites = [{"name": "Casa", "latitude": 45.494, "longitude": 11.5218, "is_default": 1}]
    r = client_vuoto.post("/api/v1/backup/import", json={"version": backup.VERSION, "sites": sites})
    assert r.status_code == 200
    client_vuoto.app.state.behind.join(10.0)
    (casa,) = client_vuoto.get("/api/v1/sites").json()["items"]
    assert (casa["measured"]["status"], casa["measured"]["nights"]) == ("enough", 4)


def test_a_new_site_finds_its_sky_on_the_frames_already_there(
    client_vuoto, db_path, tmp_path, offline
):
    conn = connect(db_path)
    sky._nights_in_four_seasons(conn, sky._measured(conn, tmp_path))
    conn.commit()
    conn.close()
    casa = create(client_vuoto, name="Casa", latitude=45.494, longitude=11.5218)
    measured = _site(client_vuoto, casa["id"])["measured"]
    assert (measured["status"], measured["nights"], measured["propose"]) == ("enough", 4, True)


def test_a_dismissal_stays_with_the_place_not_with_the_name(client_vuoto, db_path, offline):
    """Spostato il sito, il «Lascia» del posto vecchio non zittisce la misura del posto nuovo."""
    site = create(client_vuoto, bortle=6)
    _measured(db_path, site["id"], 21.4)
    client_vuoto.post(f"/api/v1/sites/{site['id']}/sky/dismiss")
    client_vuoto.patch(f"/api/v1/sites/{site['id']}", json={"latitude": 46.0})
    client_vuoto.app.state.behind.join(10.0)
    _measured(db_path, site["id"], 21.4)
    assert _site(client_vuoto, site["id"])["measured"]["propose"] is True


def _sky_asked(client, monkeypatch) -> list[bool]:
    asked: list[bool] = []
    monkeypatch.setattr(client.app.state.behind, "refresh_sky", lambda: asked.append(True))
    return asked


def test_a_new_home_and_a_deleted_site_rewrite_the_sky(client_vuoto, monkeypatch, offline):
    """Casa vince entro 1 km: cambiarla o cancellare un sito sposta i frame da un sito all'altro."""
    create(client_vuoto, bortle=6)
    other = create(client_vuoto, name="Monte", latitude=46.0, longitude=11.0)
    asked = _sky_asked(client_vuoto, monkeypatch)
    assert client_vuoto.post(f"/api/v1/sites/{other['id']}/default").status_code == 200
    assert asked == [True]
    assert client_vuoto.delete(f"/api/v1/sites/{other['id']}").status_code == 200
    assert asked == [True, True]


def _written_meanwhile(client, db_path, when: str):
    """Ogni richiesta ha una connessione che, prima di eseguire `when`, lascia scrivere un'altra
    connessione, come il cielo riscritto da Behind fra una lettura e una scrittura della rotta."""

    def get_db_with_a_writer_in_between():
        conn = connect(db_path, check_same_thread=False)

        def between(statement: str) -> None:
            if when in statement:
                other = connect(db_path)
                other.execute("INSERT OR IGNORE INTO pipeline_filters (name) VALUES (?)", ("x",))
                other.commit()
                other.close()

        conn.set_trace_callback(between)
        try:
            yield conn
        finally:
            conn.close()

    client.app.dependency_overrides[get_db] = get_db_with_a_writer_in_between


def test_a_site_write_waits_for_the_sky_written_behind(client_vuoto, db_path, offline):
    """CI 42102084200: la rotta leggeva in una transazione differita, Behind scriveva e chiudeva,
    e la scrittura della rotta trovava la sua lettura vecchia: "database is locked"."""
    _written_meanwhile(client_vuoto, db_path, "INSERT INTO sites(")
    r = client_vuoto.post(
        "/api/v1/sites", json={"name": "Casa", "latitude": 45.5, "longitude": 11.5}
    )
    assert r.status_code == 201, r.text


def test_moving_a_site_empties_a_sky_measured_on_its_frames(client_vuoto, db_path, offline):
    """La misura era di quel posto: attaccata a coordinate nuove sarebbe indistinguibile."""
    site = create(client_vuoto, bortle=6)
    _measured(db_path, site["id"], 21.4)
    client_vuoto.post(f"/api/v1/sites/{site['id']}/sky/use")
    r = client_vuoto.patch(f"/api/v1/sites/{site['id']}", json={"latitude": 46.0})
    moved = r.json()
    assert (moved["sky_sqm"], moved["sky_source"], moved["sky_nights"]) == (None, None, None)
    assert "site_no_sky" in moved["unknown"]
