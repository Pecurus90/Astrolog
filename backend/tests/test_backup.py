"""Il backup delle risposte (ADR 0017): un file accanto al database, riscritto dopo ogni scrittura
dell'utente, proposto a un database nuovo. Dentro solo cio' che l'utente ha detto, per chiavi che
sopravvivono a un database ricreato: nomi, percorsi, impronte; mai un id."""

import json

from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.db import config
from astrolog.db.connect import connect, create_database
from astrolog.fits.header_read import frame_fingerprint, read_frame
from astrolog.spine import backup, folder_move, typeless
from astrolog.spine.declarations import TypeAnswer
from conftest import add_folder, write_light


def _file(db_path):
    return backup.path_for(db_path)


def _app(db_path):
    return TestClient(create_app(db_path), base_url="http://localhost")


def _risposte(c):
    """Una risposta di ogni via: impostazioni, chiave segreta, sito, cartella, strumento e filtro
    scritti a mano, risposta sul tipo di file."""
    assert c.patch("/api/v1/settings", json={"values": {"user_name": "Marco"}}).status_code == 200
    conn = connect(c.app.state.db_path)
    try:
        config.write(conn, "meteoblue_key", "segreta")
        conn.commit()
    finally:
        conn.close()
    sito = {"name": "Casa", "latitude": 45.6, "longitude": 11.7, "elevation_m": 120.0}
    assert c.post("/api/v1/sites", json=sito).status_code == 201
    pezzo = {"kind": "optics", "name": "Askar 103", "focal_mm": 700.0}
    assert c.post("/api/v1/gear/instruments", json=pezzo).status_code == 201
    filtro = {"name": "Ha Antlia", "bands": [{"band": "HA", "width_nm": 3.0}]}
    assert c.post("/api/v1/gear/filters", json=filtro).status_code == 201


def _dichiarato(db_path):
    conn = connect(db_path)
    try:
        data = backup.collect(conn, this_machine=True)
    finally:
        conn.close()
    data.pop("written_at")
    return data


def test_every_write_of_the_user_rewrites_the_file_and_a_new_database_gets_it_back(
    tmp_path, offline
):
    db = tmp_path / "astrolog.db"
    with _app(db) as c:
        assert not _file(db).exists()
        _risposte(c)
    prima = _dichiarato(db)
    assert json.loads(_file(db).read_text(encoding="utf-8"))["config"]["user_name"] == "Marco"

    db.unlink()  # il database perso: il file accanto resta
    with _app(db) as c:
        stato = c.get("/api/v1/backup").json()
        assert stato["offer"] == "found"
        assert (stato["last"]["sites"], stato["last"]["instruments"]) == (1, 1)
        assert c.post("/api/v1/backup/restore").json()["offer"] == "none"
    assert _dichiarato(db) == prima


def test_a_database_recreated_before_start_is_offered_the_file(tmp_path, offline):
    """`tools/reset_db.py` ricrea il database prima dell'avvio: senza risposte dentro, il file
    accanto si propone."""
    db = tmp_path / "astrolog.db"
    with _app(db) as c:
        _risposte(c)
    db.unlink()
    create_database(db)
    with _app(db) as c:
        assert c.get("/api/v1/backup").json()["offer"] == "found"


def test_a_database_in_use_is_not_offered_and_cannot_be_overwritten(tmp_path, offline):
    db = tmp_path / "astrolog.db"
    with _app(db) as c:
        _risposte(c)
    with _app(db) as c:  # lo stesso database riaperto: il file e' il suo
        assert c.get("/api/v1/backup").json()["offer"] == "none"
        r = c.post("/api/v1/backup/restore")
        assert (r.status_code, r.json()["detail"]["code"]) == (409, "no_backup_offered")


def test_declining_starts_from_scratch(tmp_path, offline):
    db = tmp_path / "astrolog.db"
    with _app(db) as c:
        _risposte(c)
    db.unlink()
    with _app(db) as c:
        assert c.post("/api/v1/backup/decline").json()["offer"] == "none"
        assert c.post("/api/v1/backup/restore").status_code == 409
    assert _dichiarato(db)["sites"] == []


def test_the_stages_never_write_the_file(db_path, tmp_path):
    """Scansione e spina sono l'app che lavora, non l'utente che dice: il file non si muove."""
    write_light(tmp_path / "lib" / "a.fits")
    with _app(db_path) as c:
        folder = c.post("/api/v1/folders", json={"root_path": str(tmp_path / "lib")}).json()
        scritto = _file(db_path).stat().st_mtime_ns
        c.post(f"/api/v1/folders/{folder['id']}/scan")
        c.app.state.worker.join(10.0)
    assert _file(db_path).stat().st_mtime_ns == scritto


def test_the_export_carries_no_service_key_and_no_solver_path(tmp_path, offline):
    db = tmp_path / "astrolog.db"
    with _app(db) as c:
        _risposte(c)
        astap = tmp_path / "astap_cli.exe"
        astap.write_bytes(b"")
        scelto = {"values": {"astap_path": str(astap)}}
        assert c.patch("/api/v1/settings", json=scelto).status_code == 200
        esportato = c.get("/api/v1/backup/export")
    assert "attachment" in esportato.headers["content-disposition"]
    assert "meteoblue_key" not in esportato.json()["config"]
    assert "astap_path" not in esportato.json()["config"]
    automatico = json.loads(_file(db).read_text(encoding="utf-8"))["config"]
    assert automatico["meteoblue_key"] == "segreta"
    assert automatico["astap_path"] == str(astap)


def test_an_export_imported_elsewhere_adds_without_deleting(tmp_path, offline):
    a, b = tmp_path / "a" / "astrolog.db", tmp_path / "b" / "astrolog.db"
    a.parent.mkdir()
    b.parent.mkdir()
    with _app(a) as c:
        _risposte(c)
        esportato = c.get("/api/v1/backup/export").json()
    with _app(b) as c:
        c.post("/api/v1/sites", json={"name": "Montagna", "latitude": 46.5, "longitude": 12.1})
        assert c.post("/api/v1/backup/import", json=esportato).status_code == 200
        nomi = sorted(s["name"] for s in c.get("/api/v1/sites").json()["items"])
    assert nomi == ["Casa", "Montagna"]


def test_a_file_that_is_not_a_backup_is_refused(client_vuoto):
    r = client_vuoto.post("/api/v1/backup/import", json={"version": 99})
    assert (r.status_code, r.json()["detail"]["code"]) == (422, "not_a_backup")


def test_the_answers_keep_their_keys_and_the_folder_its_sample(conn, tmp_path):
    """Le risposte di Da confermare tornano con la loro chiave; la cartella col campione di file
    che la riconosce sull'altra macchina."""
    folder_id = add_folder(conn, "D:/Astro")
    conn.execute(
        "INSERT INTO frames(frame_hash, image_type, header_json, created_at)"
        " VALUES('impronta-1', 'unknown', '[]', 'ora')"
    )
    conn.execute(
        "INSERT INTO positions(frame_id, folder_id, rel_path, filesize, mtime, seen_at)"
        " VALUES(1, ?, 'dark/a.fits', 1, 1.0, 'ora')",
        (folder_id,),
    )
    typeless.declare(conn, "D:/Astro/dark", TypeAnswer.CALIBRATION)
    data = backup.collect(conn, this_machine=True)
    assert data["folders"][0]["sample"] == [["dark/a.fits", "impronta-1"]]
    assert any(d["entity_key"] == "D:/Astro/dark" for d in data["declarations"])

    create_database(tmp_path / "nuovo.db")
    altro = connect(tmp_path / "nuovo.db")
    backup.restore(altro, data)
    assert typeless.answer(altro, "D:/Astro/dark") == TypeAnswer.CALIBRATION
    campione = altro.execute("SELECT sample_json FROM folders").fetchone()[0]
    assert json.loads(campione) == [["dark/a.fits", "impronta-1"]]


def test_a_restored_folder_without_frames_is_recognised_by_its_sample(tmp_path):
    """Sull'altra macchina la cartella torna senza frame: lo spostamento la riconosce dal campione,
    e le risposte seguono il percorso nuovo."""
    nuovo = tmp_path / "E" / "Astro"
    write_light(nuovo / "dark" / "a.fits")
    db = tmp_path / "astrolog.db"
    with _app(db) as c:
        sonda = c.post("/api/v1/folders/probe", json={"root_path": str(nuovo)}).json()
        assert sonda["moved_check"] == "none"
    conn = connect(db)
    header, block = read_frame(str(nuovo / "dark" / "a.fits"))
    impronta = frame_fingerprint(str(nuovo / "dark" / "a.fits"), header, block)
    backup.restore(
        conn,
        {
            "version": backup.VERSION,
            "folders": [
                {
                    "root_path": "D:/Astro",
                    "name": None,
                    "retired_at": None,
                    "sample": [["dark/a.fits", impronta]],
                }
            ],  # fmt: skip
            "declarations": [
                {
                    "entity_type": "folder",
                    "entity_key": "D:/Astro/dark",
                    "field": "image_type",
                    "value": "calibration",
                    "created_at": "ora",
                }  # fmt: skip
            ],
        },
    )
    vecchia = conn.execute("SELECT id FROM folders").fetchone()[0]
    assert folder_move.same_files(conn, vecchia, str(nuovo), [str(nuovo / "dark" / "a.fits")])
    folder_move.move(conn, vecchia, str(nuovo))
    assert typeless.answer(conn, f"{nuovo.as_posix()}/dark") == TypeAnswer.CALIBRATION


def test_no_row_id_goes_in_the_file(conn):
    """Due database con le stesse risposte danno lo stesso file: un id di riga lo cambierebbe."""
    conn.execute("INSERT INTO filters(name, passband, created_at) VALUES('Ha Antlia', 'HA', 'ora')")
    data = backup.collect(conn, this_machine=True)
    assert "id" not in data["filters"][0]


def test_a_file_with_broken_entries_is_refused_not_a_crash(client_vuoto):
    r = client_vuoto.post(
        "/api/v1/backup/import", json={"version": backup.VERSION, "sites": [{"name": "x"}]}
    )
    assert (r.status_code, r.json()["detail"]["code"]) == (422, "not_a_backup")


def test_a_solver_path_that_is_not_on_this_machine_is_not_restored(conn, tmp_path):
    """Un percorso di Windows dentro Docker fermerebbe la ricerca di ASTAP: resta fuori."""
    backup.restore(
        conn, {"version": backup.VERSION, "config": {"astap_path": "C:/nonce/astap.exe"}}
    )
    assert config.read(conn).astap_path is None
    vero = tmp_path / "astap.exe"
    vero.write_bytes(b"")
    backup.restore(conn, {"version": backup.VERSION, "config": {"astap_path": str(vero)}})
    assert config.read(conn).astap_path == str(vero)
