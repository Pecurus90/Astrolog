"""Una cartella che ne contiene altre gia' in elenco le sostituisce, se l'utente lo chiede (Marco
22/10 e 25/11/2026): i frame, le loro posizioni e le risposte restano, si leggono solo i file
nuovi. Una cartella dentro una gia' in elenco si rifiuta col perche'."""

from astrolog.db.transaction import transaction
from astrolog.spine import folder_move, typeless, typeless_folders
from astrolog.spine.declarations import TypeAnswer
from conftest import add_folder, wait_until, write_light
from test_folder_move import _frame


def _places(conn):
    return [
        tuple(r)
        for r in conn.execute("SELECT id, frame_id, folder_id, rel_path FROM positions ORDER BY id")
    ]


def test_the_outer_folder_takes_the_frames_of_the_inner_ones(conn):
    """D:/Astro assorbe D:/Astro/M31 e D:/Astro/M42: stesse posizioni (stesso id, stesso frame),
    ora di D:/Astro col prefisso della sottocartella; le interne si ritirano."""
    outer = add_folder(conn, "D:/Astro")
    m31 = add_folder(conn, "D:/Astro/M31")
    m42 = add_folder(conn, "D:\\Astro\\M42\\")
    a = _frame(conn, m31, "a.fits")
    b = _frame(conn, m42, "n1/b.fits")
    before = _places(conn)

    with transaction(conn):
        folder_move.absorb(conn, outer)

    assert _places(conn) == [
        (before[0][0], a, outer, "M31/a.fits"),
        (before[1][0], b, outer, "M42/n1/b.fits"),
    ]
    retired = conn.execute(
        "SELECT id FROM folders WHERE retired_at IS NOT NULL ORDER BY id"
    ).fetchall()
    assert [r[0] for r in retired] == [m31, m42]


def test_the_answers_of_the_inner_folders_still_hold(conn):
    """Le risposte stanno sulla chiave del percorso intero: D:/Astro/M31/dark resta calibrazione,
    e la domanda la elenca sotto la cartella esterna."""
    outer = add_folder(conn, "D:/Astro")
    m31 = add_folder(conn, "D:/Astro/M31")
    frame = _frame(conn, m31, "dark/a.fits")
    typeless.declare(conn, "D:/Astro/M31/dark", TypeAnswer.CALIBRATION)
    typeless_folders.write(conn)
    asks = conn.execute("SELECT asks_type FROM frames WHERE id = ?", (frame,)).fetchone()[0]

    with transaction(conn):
        folder_move.absorb(conn, outer)

    assert typeless.answer(conn, "D:/Astro/M31/dark") == TypeAnswer.CALIBRATION
    assert [r["key"] for r in typeless.by_folder(conn)] == ["D:/Astro/M31/dark"]
    assert conn.execute("SELECT asks_type FROM frames WHERE id = ?", (frame,)).fetchone()[0] == asks


def test_a_neighbour_with_the_same_prefix_is_not_inside(conn):
    """D:/Astro2 non e' dentro D:/Astro: resta sua, attiva."""
    outer = add_folder(conn, "D:/Astro")
    other = add_folder(conn, "D:/Astro2")
    _frame(conn, other, "a.fits")

    with transaction(conn):
        folder_move.absorb(conn, outer)

    assert _places(conn)[0][2:] == (other, "a.fits")
    assert (
        conn.execute("SELECT retired_at FROM folders WHERE id = ?", (other,)).fetchone()[0] is None
    )


def test_a_retired_folder_inside_gives_its_frames_too(conn):
    """Ritirata, la cartella dentro non e' nella domanda, ma i suoi file sono sotto la nuova:
    le sue posizioni passano alla esterna invece di rileggerli."""
    outer = add_folder(conn, "D:/Astro")
    old = add_folder(conn, "D:/Astro/vecchia")
    conn.execute("UPDATE folders SET retired_at = 'ora' WHERE id = ?", (old,))
    frame = _frame(conn, old, "a.fits")

    with transaction(conn):
        folder_move.absorb(conn, outer)

    assert _places(conn)[0][1:] == (frame, outer, "vecchia/a.fits")


def test_held_and_holder_say_which_folders_overlap(conn):
    """Solo le attive contano per la domanda; la stessa cartella non e' ne' dentro ne' intorno."""
    m31 = add_folder(conn, "D:/Astro/M31")
    gone = add_folder(conn, "D:/Astro/M42")
    conn.execute("UPDATE folders SET retired_at = 'ora' WHERE id = ?", (gone,))
    _frame(conn, m31, "a.fits")

    held = folder_move.held(conn, "D:/Astro")
    assert [(r.id, r.root_path, r.frames) for r in held] == [(m31, "D:/Astro/M31", 1)]
    assert folder_move.held(conn, "D:/Astro/M31") == []
    outer = folder_move.holder(conn, "D:/Astro/M31/n1")
    assert outer is not None and outer.id == m31
    assert folder_move.holder(conn, "D:/Astro/M31") is None
    assert folder_move.holder(conn, "D:/Astro/M42/n1") is None


def _client_add(client, root, replaces=None):
    body = {"root_path": str(root)}
    if replaces is not None:
        body["replaces"] = replaces
    return client.post("/api/v1/folders", json=body)


def test_adding_a_folder_around_registered_ones_asks_first(client_vuoto, tmp_path):
    """Senza `replaces` la cartella esterna non si registra: 409 con le cartelle che contiene e i
    loro frame, per la domanda."""
    m31, m42 = tmp_path / "M31", tmp_path / "M42"
    m31.mkdir()
    m42.mkdir()
    first = _client_add(client_vuoto, m31).json()
    second = _client_add(client_vuoto, m42).json()

    r = _client_add(client_vuoto, tmp_path)

    assert r.status_code == 409, r.text
    assert r.json()["detail"] == {
        "code": "folder_contains",
        "folders": [
            {"id": first["id"], "root_path": first["root_path"], "frames": 0},
            {"id": second["id"], "root_path": second["root_path"], "frames": 0},
        ],
    }
    assert len(client_vuoto.get("/api/v1/folders").json()["items"]) == 2


def test_replacing_keeps_the_frames_and_a_scan_reads_only_the_new_files(client_vuoto, tmp_path):
    """Sostituisci: la esterna prende i frame della interna, la interna sparisce dall'elenco, e la
    scansione dopo trova come nuovo solo il file fuori da M31."""
    m31 = tmp_path / "M31"
    m31.mkdir()
    write_light(m31 / "a.fits")
    inner = _client_add(client_vuoto, m31).json()
    assert _scanned(client_vuoto, inner["id"])["new"] == 1
    write_light(tmp_path / "b.fits", date="2024-05-18T21:00:00")

    r = _client_add(client_vuoto, tmp_path, replaces=[inner["id"]])

    assert r.status_code == 201, r.text
    outer = r.json()
    assert outer["frames"] == 1
    assert [f["id"] for f in client_vuoto.get("/api/v1/folders").json()["items"]] == [outer["id"]]
    receipt = _scanned(client_vuoto, outer["id"])
    assert (receipt["new"], receipt["unchanged"]) == (1, 1)


def test_replacing_with_another_list_than_the_folders_inside_asks_again(client_vuoto, tmp_path):
    """La risposta vale per le cartelle che l'utente ha visto: una aggiunta nel frattempo, o un id
    che non c'entra, rifa' la domanda invece di sostituire cio' che non ha visto."""
    m31, m42 = tmp_path / "M31", tmp_path / "M42"
    m31.mkdir()
    m42.mkdir()
    first = _client_add(client_vuoto, m31).json()
    _client_add(client_vuoto, m42)

    r = _client_add(client_vuoto, tmp_path, replaces=[first["id"]])

    assert r.status_code == 409, r.text
    assert r.json()["detail"]["code"] == "folder_contains"


def test_the_probe_says_what_adding_would_do(client_vuoto, tmp_path):
    """La sonda dice prima del tasto chi contiene e dentro chi sta: la pagina propone o rifiuta."""
    sub = tmp_path / "M31"
    sub.mkdir()
    inner = _client_add(client_vuoto, sub).json()

    around = client_vuoto.post("/api/v1/folders/probe", json={"root_path": str(tmp_path)}).json()
    within = client_vuoto.post("/api/v1/folders/probe", json={"root_path": str(sub / "x")}).json()

    held = {"id": inner["id"], "root_path": inner["root_path"], "frames": 0}
    assert (around["holds"], around["inside"]) == ([held], None)
    assert (within["holds"], within["inside"]) == ([], held)


def test_a_folder_inside_a_registered_one_is_refused_with_it(client_vuoto, tmp_path):
    """I suoi file si leggono gia': 409 con la cartella che la contiene, anche se era ritirata."""
    sub = tmp_path / "n1"
    sub.mkdir()
    outer = _client_add(client_vuoto, tmp_path).json()

    r = _client_add(client_vuoto, sub)

    assert r.status_code == 409, r.text
    assert r.json()["detail"] == {
        "code": "folder_inside",
        "folder_id": outer["id"],
        "root_path": outer["root_path"],
    }


def test_a_retired_folder_inside_a_registered_one_does_not_come_back(client_vuoto, tmp_path):
    """Riaggiungere una cartella ritirata che ora sta dentro una attiva non la riattiva: i suoi
    file li legge gia' la esterna."""
    sub = tmp_path / "n1"
    sub.mkdir()
    inner = _client_add(client_vuoto, sub).json()
    client_vuoto.delete(f"/api/v1/folders/{inner['id']}")
    _client_add(client_vuoto, tmp_path)

    r = _client_add(client_vuoto, sub)

    assert r.status_code == 409, r.text
    assert r.json()["detail"]["code"] == "folder_inside"


def _scanned(client, folder_id):
    """Scansiona e torna la ricevuta di quella cartella."""
    assert client.post(f"/api/v1/folders/{folder_id}/scan").status_code == 202
    client.app.state.worker.join(30.0)

    def receipt():
        runs = client.get("/api/v1/scan-runs").json()["items"]
        return next((r for r in runs if r["folder_id"] == folder_id and r["ended_at"]), None)

    assert wait_until(lambda: receipt() is not None)
    return receipt()
