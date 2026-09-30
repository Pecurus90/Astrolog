"""Cosa rimette in coda un cambio dei luoghi: le pose ferme che il cambio puo' sbloccare, e solo
quelle; le notti di un luogo spostato; il trasloco di casa che non tocca le notti degli altri
luoghi. Le regole stanno in `spine/site_requeue.py` e in `docs/domini/sito.md`.
"""

from astrolog import place
from astrolog.db.connect import connect
from astrolog.spine import declarations as decl
from astrolog.spine.stages import mark_pending, set_status
from test_sites import _notte, create


def _in_attesa(conn, perche_, night=None, coord=(45.6, 11.667)):
    """Una posa ferma da `group` col suo perche', ripresa a quelle coordinate, con la sua notte e
    l'istante da cui viene."""
    frame = conn.execute(
        "INSERT INTO frames(frame_hash, image_type, date_obs, local_night, night_instant,"
        " night_id, header_json, created_at, site_lat, site_lon) VALUES(?, 'light',"
        " '2024-05-18T18:00:00.000', '2024-05-18', '2024-05-18T18:00:00.000', ?, '[]', 'now',"
        " ?, ?)",
        (f"h-{perche_}-{night}-{coord}", night, *coord),
    ).lastrowid
    mark_pending(conn, frame)
    set_status(conn, frame, "group", "skipped" if perche_ else "done", reason=perche_)
    return frame


def _stato_di(client_vuoto, frame):
    with connect(client_vuoto.app.state.db_path) as conn:
        return conn.execute(
            "SELECT status FROM frame_stages WHERE frame_id = ? AND stage = 'group'", (frame,)
        ).fetchone()["status"]


def test_declaring_a_site_puts_the_waiting_frames_back_in_the_queue(client_vuoto, offline):
    """Le pose ferme perche' il posto non si sapeva ripartono quando si dichiara un sito: ora
    l'app puo' saperlo da sola, e se non puo' la domanda torna."""
    create(client_vuoto)
    with connect(client_vuoto.app.state.db_path) as conn:
        frame = _in_attesa(conn, "site_unclear")
    create(client_vuoto, name="Montagna", latitude=45.6, longitude=11.667)
    assert _stato_di(client_vuoto, frame) == "pending"


def test_a_change_that_cannot_help_puts_nothing_back_in_the_queue(client_vuoto, offline):
    """Un sito nuovo lontano dalle pose ferme, o un sito che cambia solo il cielo, non puo' dire
    da solo dove fossero: rimetterle in coda farebbe rifare a `group` lo stesso lavoro."""
    create(client_vuoto)
    with connect(client_vuoto.app.state.db_path) as conn:
        frame = _in_attesa(conn, "site_unclear")
    lontano = create(client_vuoto, name="Deserto", latitude=33.45, longitude=-111.98)
    r = client_vuoto.patch(f"/api/v1/sites/{lontano['id']}", json={"sky_sqm": 21.5})
    assert r.status_code == 200, r.text
    assert _stato_di(client_vuoto, frame) == "skipped"


def test_renaming_a_site_to_the_name_an_answer_says_puts_those_frames_back(client_vuoto, offline):
    """La risposta per quelle coordinate nomina un sito che non c'era piu'; rinominato un sito
    con quel nome, la risposta aggancia di nuovo, e quelle pose ripartono. Le altre no."""
    create(client_vuoto)
    cima = create(client_vuoto, name="Cima", latitude=46.05, longitude=11.316)
    with connect(client_vuoto.app.state.db_path) as conn:
        decl.declare_coordinates(conn, place.coordinates_key(45.6, 11.667), "Rifugio")
        risposta = _in_attesa(conn, "site_unclear")
        altra = _in_attesa(conn, "site_unclear", coord=(44.0, 10.0))
    r = client_vuoto.patch(f"/api/v1/sites/{cima['id']}", json={"name": "Rifugio"})
    assert r.status_code == 200, r.text
    assert (_stato_di(client_vuoto, risposta), _stato_di(client_vuoto, altra)) == (
        "pending",
        "skipped",
    )


def test_fixing_a_site_without_a_timezone_frees_the_frames_waiting_for_it(
    client_vuoto, monkeypatch, offline
):
    """Casa non ha un fuso -- mare aperto -- e i frame senza coordinate aspettano per quello.
    Corrette le coordinate, il fuso c'e': quei frame ripartono, anche se non hanno coordinate da
    avvicinare e il nome non e' cambiato."""
    # come la vera: senza coordinate nessun fuso
    finta = lambda lat, lon: None if lon is None or lon < -20 else "Europe/Rome"  # noqa: E731
    monkeypatch.setattr(place, "timezone_of", finta)
    casa = create(client_vuoto, name="Barca", latitude=0.0, longitude=-30.0)
    with connect(client_vuoto.app.state.db_path) as conn:
        frame = _in_attesa(conn, "site_no_timezone", coord=(None, None))
    r = client_vuoto.patch(
        f"/api/v1/sites/{casa['id']}", json={"latitude": 45.5, "longitude": 11.5}
    )
    assert r.status_code == 200, r.text
    assert _stato_di(client_vuoto, frame) == "pending"


def test_moving_home_leaves_the_nights_of_the_other_sites_alone(client_vuoto, offline):
    """Le notti che l'app ha messo su un altro sito dichiarato, per le coordinate, restano sue:
    il trasloco di casa porta con se' solo le notti di casa."""
    casa = create(client_vuoto)
    cima = create(client_vuoto, name="Cima", latitude=46.05, longitude=11.316)
    nuova = create(client_vuoto, name="Deserto", latitude=45.90, longitude=11.10)
    with connect(client_vuoto.app.state.db_path) as conn:
        _notte(conn, cima["id"], "2024-05-19")
    assert client_vuoto.post(f"/api/v1/sites/{nuova['id']}/default").status_code == 200
    with connect(client_vuoto.app.state.db_path) as conn:
        (dove,) = conn.execute(
            "SELECT site_id FROM nights WHERE night_date = '2024-05-19'"
        ).fetchone()
    assert dove == cima["id"] != casa["id"]


def test_moving_a_site_puts_its_nights_back_in_the_queue(client_vuoto, offline):
    """Spostato un sito, le notti che l'app gli aveva dato per le coordinate si rifanno: le
    coordinate delle pose potrebbero non cadere piu' li'. Quelle nate da una risposta no."""
    create(client_vuoto)
    cima = create(client_vuoto, name="Cima", latitude=46.05, longitude=11.316)
    with connect(client_vuoto.app.state.db_path) as conn:
        frame = _in_attesa(conn, None, night=_notte(conn, cima["id"], "2024-05-19"))
        detta = _in_attesa(
            conn, None, night=_notte(conn, cima["id"], "2024-05-20", source="declared")
        )
    r = client_vuoto.patch(f"/api/v1/sites/{cima['id']}", json={"latitude": 46.3})
    assert r.status_code == 200, r.text
    assert (_stato_di(client_vuoto, frame), _stato_di(client_vuoto, detta)) == ("pending", "done")


def test_the_first_site_frees_the_frames_waiting_for_a_home(client_vuoto, offline):
    """A mani vuote le pose si fermano perche' casa non c'e'; il primo sito diventa casa, e
    ripartono tutte, anche quelle senza coordinate."""
    with connect(client_vuoto.app.state.db_path) as conn:
        frame = _in_attesa(conn, "no_active_site", coord=(None, None))
    create(client_vuoto)
    assert _stato_di(client_vuoto, frame) == "pending"


def test_a_second_site_does_not_free_the_frames_waiting_for_a_home(client_vuoto, offline):
    """Un secondo sito, lontano, non e' casa: le pose ferme perche' casa non c'era restano dove
    sono -- a liberarle e' la casa, non un sito qualunque."""
    create(client_vuoto)
    with connect(client_vuoto.app.state.db_path) as conn:
        frame = _in_attesa(conn, "no_active_site", coord=(None, None))
    create(client_vuoto, name="Deserto", latitude=33.45, longitude=-111.98)
    assert _stato_di(client_vuoto, frame) == "skipped"
