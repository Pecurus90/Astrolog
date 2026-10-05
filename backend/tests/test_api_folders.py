"""Le cartelle: si registrano nella forma che l'utente ritrova, si ritirano senza perdere niente,
raccontano quanti frame hanno dato senza far aspettare, e "Verifica ora" e' un gesto."""

import os
from pathlib import Path

from fastapi.testclient import TestClient

import astrolog
from astrolog.api import folders as folders_api
from astrolog.api import paths
from astrolog.api.app import create_app
from astrolog.db.connect import connect
from conftest import online_only, write_light


def add(client_vuoto, path):
    r = client_vuoto.post("/api/v1/folders", json={"root_path": str(path)})
    assert r.status_code == 201, r.text
    return r.json()


def folders(client_vuoto):
    return client_vuoto.get("/api/v1/folders").json()["items"]


def test_create_list_and_reachability(client_vuoto, tmp_path):
    root = tmp_path / "astro"
    root.mkdir()
    f = add(client_vuoto, root)
    assert f["root_path"] == os.path.realpath(str(root)) and f["reachable"] is True
    rows = folders(client_vuoto)
    assert rows[0]["id"] == f["id"] and rows[0]["frames"] == 0
    gone = tmp_path / "sparita"
    gone.mkdir()
    g = add(client_vuoto, gone)
    gone.rmdir()
    rows = {r["id"]: r for r in folders(client_vuoto)}
    assert rows[g["id"]]["reachable"] is False and rows[f["id"]]["reachable"] is True


def test_validation_rejects_relative_and_system_paths(client_vuoto, tmp_path):
    assert client_vuoto.post("/api/v1/folders", json={"root_path": "relativa/x"}).status_code == 422
    assert client_vuoto.post("/api/v1/folders", json={"root_path": ""}).status_code == 422
    if os.name == "nt":
        system_root = os.environ.get("SYSTEMROOT", r"C:\Windows")
        assert (
            client_vuoto.post("/api/v1/folders", json={"root_path": system_root}).status_code == 422
        )
    else:
        assert client_vuoto.post("/api/v1/folders", json={"root_path": "/etc"}).status_code == 422


def test_duplicate_is_409_and_retire_reactivate_keep_data(client_vuoto, tmp_path, db_path):
    root = tmp_path / "astro"
    write_light(root / "a.fits")
    f = add(client_vuoto, root)
    assert client_vuoto.post("/api/v1/folders", json={"root_path": str(root)}).status_code == 409
    assert client_vuoto.post(f"/api/v1/folders/{f['id']}/scan").status_code == 202
    client_vuoto.app.state.worker.join(10.0)
    assert folders(client_vuoto)[0]["frames"] == 1
    r = client_vuoto.delete(f"/api/v1/folders/{f['id']}")
    assert r.json() == {"folder_id": f["id"], "retired": True, "kept_frames": 1}
    assert folders(client_vuoto) == []
    # **E le sue letture restano leggibili**, col percorso dentro: togliere una cartella e' un
    # ritiro, la sua riga non sparisce, e la ricevuta esce da una giunzione **interna**
    # (`spine/scan_store.SELECT_RUN`). Che la riga non possa sparire lo tiene fermo lo schema --
    # `scan_runs.folder_id` la riferisce, e provato: sostituendo il ritiro con una cancellazione
    # vera si prende `FOREIGN KEY constraint failed`, non uno storico perso in silenzio.
    letture = client_vuoto.get("/api/v1/scan-runs").json()["items"]
    assert [riga["folder_id"] for riga in letture] == [f["id"]]
    assert letture[0]["folder_path"] == str(root)
    # A receipt says its folder is retired: otherwise the page shows a path that never updates.
    assert letture[0]["folder_retired"] is True
    c = connect(db_path)
    assert c.execute("SELECT COUNT(*) FROM frames").fetchone()[0] == 1
    c.close()
    assert client_vuoto.post(f"/api/v1/folders/{f['id']}/scan").status_code == 409
    again = add(client_vuoto, root)
    assert again["id"] == f["id"] and again["reactivated"] is True
    letture = client_vuoto.get("/api/v1/scan-runs").json()["items"]
    assert letture[0]["folder_retired"] is False
    assert client_vuoto.delete("/api/v1/folders/99999").status_code == 404
    client_vuoto.delete(f"/api/v1/folders/{f['id']}")
    assert client_vuoto.delete(f"/api/v1/folders/{f['id']}").json()["retired"] is False


def test_probe(client_vuoto, tmp_path):
    root = tmp_path / "astro"
    write_light(root / "a.fits")
    write_light(root / "b.fits", obj="M 2")
    p = client_vuoto.post("/api/v1/folders/probe", json={"root_path": str(root)}).json()
    assert p["reachable"] is True and p["fits_count"] == 2 and p["complete"] is True
    for x in root.iterdir():
        x.unlink()
    root.rmdir()
    p = client_vuoto.post("/api/v1/folders/probe", json={"root_path": str(root)}).json()
    assert (p["reachable"], p["fits_count"], p["complete"]) == (False, None, None)


def test_probe_counts_the_online_only_files_too(client_vuoto, tmp_path, monkeypatch):
    """Chi ha l'archivio sotto OneDrive non deve leggere "0 FITS" sulla cartella che ha appena
    scelto: i file solo online ci sono, anche se non sul disco."""
    root = tmp_path / "nuvola"
    write_light(root / "a.fits")
    write_light(root / "b.fits", obj="M 2")
    online_only(monkeypatch, root / "a.fits", root / "b.fits")
    p = client_vuoto.post("/api/v1/folders/probe", json={"root_path": str(root)}).json()
    assert p["fits_count"] == 2


def test_probe_stops_at_its_time_limit_and_says_so(client_vuoto, tmp_path, monkeypatch):
    """Su un archivio enorme o un NAS lento il conteggio non tiene ferma la pagina: si ferma al
    tetto e dice che sono "piu' di" quelli contati."""
    root = tmp_path / "grande"
    write_light(root / "sub" / "a.fits")
    monkeypatch.setattr(folders_api, "PROBE_SECONDS", -1)  # scaduto prima di cominciare
    p = client_vuoto.post("/api/v1/folders/probe", json={"root_path": str(root)}).json()
    assert (p["reachable"], p["complete"]) == (True, False)


def test_a_network_folder_is_accepted(client_vuoto, monkeypatch):
    """Una cartella di rete si registra. Niente rete vera nei test: il percorso non si risolve e
    la cartella risulta non raggiungibile, che la registrazione accetta."""
    rete = r"\\nas\astro\foto" if os.name == "nt" else "/mnt/nas/astro/foto"
    monkeypatch.setattr(paths.os.path, "realpath", lambda p: p)
    monkeypatch.setattr(folders_api, "root_readable", lambda p: False)
    r = client_vuoto.post("/api/v1/folders", json={"root_path": rete})
    assert r.status_code == 201, r.text
    assert (r.json()["root_path"], r.json()["reachable"]) == (rete, False)


def test_the_nas_folder_is_chosen_from_a_list(tmp_path, db_path):
    """Sul NAS in Docker l'utente non sa quale percorso ha la cartella dentro il container:
    l'app elenca le sottocartelle della radice dei dati, e si sceglie. Le nascoste non si
    propongono, e fuori dalla radice non si guarda."""
    radice = tmp_path / "library"
    for sotto in ("M31", "Notti/2024", ".cestino"):
        (radice / sotto).mkdir(parents=True)
    confinata = os.path.realpath(radice)
    app = create_app(db_path, data_root=confinata)
    with TestClient(app, base_url="http://localhost") as c:
        cima = c.get("/api/v1/folders/browse").json()
        assert (cima["path"], cima["parent"]) == (confinata, None)
        assert [f["name"] for f in cima["folders"]] == ["M31", "Notti"]
        notti = c.get("/api/v1/folders/browse", params={"path": cima["folders"][1]["path"]})
        assert [f["name"] for f in notti.json()["folders"]] == ["2024"]
        assert notti.json()["parent"] == confinata
        fuori = c.get("/api/v1/folders/browse", params={"path": str(tmp_path)})
        assert fuori.status_code == 422
        assert fuori.json()["detail"]["code"] == "path_outside_data_root"


def test_without_a_data_root_there_is_no_list(client_vuoto):
    """Sul desktop non c'e' una radice dei dati: la cartella si sceglie dal sistema, e l'app non
    elenca le cartelle della macchina a chi glielo chiede."""
    r = client_vuoto.get("/api/v1/folders/browse")
    assert r.status_code == 409 and r.json()["detail"]["code"] == "no_data_root"


def test_path_info_and_health(client_vuoto):
    info = client_vuoto.get("/api/v1/folders/path-info").json()
    assert info["family"] in ("windows", "posix") and "data_root" in info
    h = client_vuoto.get("/api/health").json()
    assert h["status"] == "ok" and h["api_version"]

    # Le tabelle contate sono le NOSTRE, quelle di `schema.sql`: SQLite si tiene le sue
    # (`sqlite_sequence`, che nasce con AUTOINCREMENT) e a schermo darebbero un numero che non
    # torna con lo schema. Il conto si rifa' dal file invece di scriverlo qui: un numero che una
    # macchina puo' contare non si congela in un test.
    schema = (Path(astrolog.__file__).parent / "schema.sql").read_text(encoding="utf-8")
    apertura = "CREATE TABLE "  # ddl-ok: si CONTANO le tabelle dello schema, non se ne crea nessuna
    nostre = sum(1 for riga in schema.splitlines() if riga.startswith(apertura))
    assert h["schema_tables"] == nostre, "contate anche le tabelle che SQLite si tiene per se'"
