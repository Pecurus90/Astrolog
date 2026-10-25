"""Il backup delle risposte (ADR 0017): un file accanto al database, riscritto dopo ogni scrittura
dell'utente, proposto a un database nuovo. Dentro solo cio' che l'utente ha detto, per chiavi che
sopravvivono a un database ricreato: nomi, percorsi, impronte; mai un id."""

import json
import os
import threading

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


def test_a_scan_writes_the_file_only_for_a_new_sample(db_path, tmp_path):
    """Il file e' cio' che hai detto, piu' i file-campione che riconoscono le cartelle su un'altra
    macchina: la prima scansione ce li mette (Marco, 25/10/2026). Una scansione che non cambia il
    campione non lo tocca."""
    write_light(tmp_path / "lib" / "a.fits")
    with _app(db_path) as c:
        folder = c.post("/api/v1/folders", json={"root_path": str(tmp_path / "lib")}).json()
        c.post(f"/api/v1/folders/{folder['id']}/scan")
        c.app.state.worker.join(10.0)
        dentro = backup.read(_file(db_path))
        assert dentro is not None and [f["sample"] for f in dentro["folders"]] != [[]]
        scritto = _file(db_path).stat().st_mtime_ns
        c.post(f"/api/v1/folders/{folder['id']}/scan")
        c.app.state.worker.join(10.0)
    assert _file(db_path).stat().st_mtime_ns == scritto


def test_a_scan_reading_before_an_answer_cannot_write_after_it(db_path, monkeypatch):
    """La scansione legge il database, l'utente risponde e scrive il file, poi la scansione
    scrive: senza un solo scrittore alla volta il file perdeva quella risposta."""
    conn = connect(db_path, check_same_thread=False)
    cartella = add_folder(conn, "D:/Astro")
    backup.write(conn, db_path)
    vera, letto, via = backup.collect, threading.Event(), threading.Event()

    def lenta(c, **k):
        dati = vera(c, **k)
        letto.set()
        via.wait(10.0)
        return dati

    def risponde():
        c = connect(db_path)
        c.execute(
            "INSERT INTO header_aliases(kind, header_value, target_key, created_at)"
            " VALUES('camera', 'atr', 'ATR2600M', 'ora')"
        )
        backup.write(c, db_path)
        c.close()

    monkeypatch.setattr(backup, "collect", lenta)
    scansione = threading.Thread(target=backup.write_if_new_sample, args=(conn, db_path))
    # un file letto dopo l'ultimo backup: il campione e' nuovo, e la scansione scrive
    frame = conn.execute(
        "INSERT INTO frames(frame_hash, image_type, header_json, created_at)"
        " VALUES('h1', 'light', '[]', 'ora')"
    ).lastrowid
    conn.execute(
        "INSERT INTO positions(frame_id, folder_id, rel_path, filesize, mtime, seen_at)"
        " VALUES(?, ?, 'a.fits', 1, 1.0, 'ora')",
        (frame, cartella),
    )
    scansione.start()
    assert letto.wait(10.0)
    monkeypatch.setattr(backup, "collect", vera)
    utente = threading.Thread(target=risponde)
    utente.start()
    # senza un solo scrittore la risposta finisce qui; con, aspetta la scansione
    utente.join(1.0)
    via.set()
    scansione.join(10.0)
    utente.join(10.0)
    dati = backup.read(backup.path_for(db_path))
    assert dati is not None and len(dati["header_aliases"]) == 1


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


def test_an_import_obeys_the_rules_of_the_settings_page(client_vuoto):
    """Un file scritto a mano non vale piu' della pagina: un numero fuori scala renderebbe buone
    tutte le notti, o nessuna."""
    fuori = {"version": backup.VERSION, "config": {"moon_broadband_max_pct": "500"}}
    r = client_vuoto.post("/api/v1/backup/import", json=fuori)
    assert (r.status_code, r.json()["detail"]["code"]) == (422, "not_a_backup")
    impostazioni = client_vuoto.get("/api/v1/settings").json()
    assert "500" not in json.dumps(impostazioni)


def test_an_import_brings_no_key_and_no_solver_path(client_vuoto, tmp_path):
    """Cio' che l'export non porta non entra dall'import: la chiave Meteoblue si scrive solo dopo
    la prova sull'account, e un solver dichiarato da un file scelto da altri si eseguirebbe."""
    eseguibile = tmp_path / "qualcosa.exe"
    eseguibile.write_bytes(b"")
    portato = {
        "meteoblue_key": "mai-provata",
        "sky_service_key": "x",
        "astap_path": str(eseguibile),
    }
    r = client_vuoto.post(
        "/api/v1/backup/import", json={"version": backup.VERSION, "config": portato}
    )
    assert r.status_code == 200
    conn = connect(client_vuoto.app.state.db_path)
    try:
        letto = config.read(conn)
    finally:
        conn.close()
    assert (letto.meteoblue_key, letto.sky_service_key, letto.astap_path) == (None, None, None)


def test_an_import_on_the_nas_keeps_folders_inside_the_data_root(tmp_path, db_path):
    """Una cartella che c'e' qui ma fuori dalla radice dei dati non entra; una che qui non c'e'
    torna per lo spostamento (ADR 0017); una dentro entra nella forma che l'aggiunta scriverebbe."""
    radice = tmp_path / "library"
    (radice / "M31").mkdir(parents=True)
    fuori = tmp_path / "privata"
    fuori.mkdir()
    altrove = tmp_path / "altro-computer" / "foto"
    cartella = lambda p: {"root_path": str(p), "name": p.name, "retired_at": None, "sample": []}  # noqa: E731
    app = create_app(db_path, data_root=os.path.realpath(radice))
    with TestClient(app, base_url="http://localhost") as c:
        r = c.post(
            "/api/v1/backup/import",
            json={
                "version": backup.VERSION,
                "folders": [cartella(radice / "M31"), cartella(fuori)],
            },
        )
        assert (r.status_code, r.json()["detail"]["code"]) == (422, "path_outside_data_root")
        assert c.get("/api/v1/folders").json()["total"] == 0
        r = c.post(
            "/api/v1/backup/import",
            json={
                "version": backup.VERSION,
                "folders": [cartella(radice / "M31"), cartella(altrove)],
            },
        )
        assert r.status_code == 200, r.text
        percorsi = sorted(f["root_path"] for f in c.get("/api/v1/folders").json()["items"])
    assert percorsi == sorted([os.path.realpath(radice / "M31"), str(altrove)])
