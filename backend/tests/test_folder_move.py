"""Una cartella spostata resta la stessa: stesso id, percorso nuovo, e le risposte "che file sono"
la seguono. Si sposta solo verso un posto che ha gli stessi file, e l'app lo riconosce da sola
quando si guarda dentro il posto nuovo."""

import os
import shutil

from astrolog.db.connect import connect
from astrolog.spine import folder_move, typeless, typeless_folders
from astrolog.spine.declarations import TypeAnswer
from astrolog.spine.stages import set_status
from conftest import add_folder, write_fits, write_light


def _frame(conn, folder_id, rel_path):
    """Un frame senza tipo che il cielo non sa dire, con la sua posizione: senza FITS."""
    frame_id = conn.execute(
        "INSERT INTO frames(frame_hash, image_type, header_json, created_at)"
        " VALUES(?, 'unknown', '[]', 'ora')",
        (f"{folder_id}:{rel_path}",),
    ).lastrowid
    conn.execute(
        "INSERT INTO positions(frame_id, folder_id, rel_path, filesize, mtime, seen_at)"
        " VALUES(?, ?, ?, 1, 1.0, 'ora')",
        (frame_id, folder_id, rel_path),
    )
    set_status(conn, frame_id, "solve", "failed", reason="no_solution")
    return frame_id


def _still(conn):
    frames = [tuple(r) for r in conn.execute("SELECT * FROM frames ORDER BY id")]
    places = [tuple(r) for r in conn.execute("SELECT * FROM positions ORDER BY id")]
    return frames, places


def test_a_moved_folder_takes_its_answer_and_its_frames_stay(conn):
    """La cartella risposta "calibrazione" su D:/Astro/dark, spostata a E:/Astro: la risposta vale
    per E:/Astro/dark, la pagina la elenca li', e i frame non si muovono."""
    folder_id = add_folder(conn, "D:/Astro")
    _frame(conn, folder_id, "dark/a.fits")
    typeless.declare(conn, "D:/Astro/dark", TypeAnswer.CALIBRATION)
    typeless_folders.write(conn)
    frames, _ = _still(conn)

    folder_move.move(conn, folder_id, "E:/Astro")

    root = conn.execute("SELECT root_path FROM folders WHERE id = ?", (folder_id,)).fetchone()
    assert root[0] == "E:/Astro"
    assert typeless.answer(conn, "E:/Astro/dark") == TypeAnswer.CALIBRATION
    assert typeless.answer(conn, "D:/Astro/dark") is None
    assert [r["key"] for r in typeless.by_folder(conn)] == ["E:/Astro/dark"]
    assert _still(conn)[0] == frames


def test_the_root_and_every_subfolder_move_and_a_neighbour_does_not(conn):
    """La radice, una sottocartella e una sotto-sottocartella passano al prefisso nuovo, nella forma
    delle chiavi (barre in avanti, niente barra in coda); D:/Astro2 non e' dentro D:/Astro."""
    folder_id = add_folder(conn, "D:\\Astro\\")
    add_folder(conn, "D:/Astro2")
    for key in ("D:/Astro", "D:/Astro/dark", "D:/Astro/a/b", "D:/Astro2/dark"):
        typeless.declare(conn, key, TypeAnswer.LIGHT)

    folder_move.move(conn, folder_id, "\\\\NAS\\Foto\\")

    keys = sorted(r[0] for r in conn.execute("SELECT entity_key FROM declarations"))
    assert keys == ["//NAS/Foto", "//NAS/Foto/a/b", "//NAS/Foto/dark", "D:/Astro2/dark"]


def _client_folder(client, root):
    r = client.post("/api/v1/folders", json={"root_path": str(root)})
    assert r.status_code == 201, r.text
    return r.json()


def _scanned(client, folder_id):
    assert client.post(f"/api/v1/folders/{folder_id}/scan").status_code == 202
    client.app.state.worker.join(10.0)


def _archive(root):
    """Un dark che la scansione salta, primo in ordine di percorso: il campione non lo conta."""
    write_fits(root / "0calib" / "d.fits", {"IMAGETYP": "Dark Frame"})
    write_light(root / "a.fits")
    write_light(root / "dark" / "b.fits", obj="M 2")
    write_light(root / "notte" / "M51" / "c.fits", obj="M 51")


def _count(db_path, sql):
    c = connect(db_path)
    try:
        return c.execute(sql).fetchone()[0]
    finally:
        c.close()


def test_moving_to_the_same_files_keeps_everything_and_a_scan_adds_nothing(
    client_vuoto, tmp_path, db_path
):
    old, new = tmp_path / "D" / "Astro", tmp_path / "E" / "Astro"
    _archive(old)
    f = _client_folder(client_vuoto, old)
    _scanned(client_vuoto, f["id"])
    c = connect(db_path)
    typeless.declare(c, f["root_path"].replace("\\", "/") + "/dark", TypeAnswer.CALIBRATION)
    c.close()
    frames = _count(db_path, "SELECT COUNT(*) FROM frames")
    shutil.copytree(old, new)
    shutil.rmtree(old)

    r = client_vuoto.post(f"/api/v1/folders/{f['id']}/move", json={"root_path": str(new)})

    assert r.status_code == 200, r.text
    assert (r.json()["id"], r.json()["root_path"]) == (f["id"], os.path.realpath(new))
    c = connect(db_path)
    new_key = os.path.realpath(new).replace("\\", "/")
    assert typeless.answer(c, new_key + "/dark") == TypeAnswer.CALIBRATION
    c.close()
    _scanned(client_vuoto, f["id"])
    assert _count(db_path, "SELECT COUNT(*) FROM frames") == frames
    assert _count(db_path, "SELECT COUNT(*) FROM positions") == frames
    assert _count(db_path, "SELECT COUNT(*) FROM positions WHERE status <> 'present'") == 0


def test_a_place_with_other_files_is_refused_and_nothing_changes(client_vuoto, tmp_path, db_path):
    """Stessi nomi, pixel diversi: non e' la stessa cartella. E nemmeno un posto vuoto."""
    old, other, empty = tmp_path / "D", tmp_path / "E", tmp_path / "vuota"
    write_light(old / "a.fits")
    write_light(other / "a.fits")  # i pixel vengono dal percorso: un altro file
    empty.mkdir()
    f = _client_folder(client_vuoto, old)
    _scanned(client_vuoto, f["id"])
    c = connect(db_path)
    typeless.declare(c, f["root_path"].replace("\\", "/"), TypeAnswer.LIGHT)
    c.close()

    for where in (other, empty):
        r = client_vuoto.post(f"/api/v1/folders/{f['id']}/move", json={"root_path": str(where)})
        assert r.status_code == 409, r.text
        assert r.json()["detail"]["code"] == "not_the_same_folder"
    c = connect(db_path)
    assert c.execute("SELECT root_path FROM folders").fetchone()[0] == f["root_path"]
    assert typeless.answer(c, f["root_path"].replace("\\", "/")) == TypeAnswer.LIGHT
    c.close()


def test_moving_onto_a_registered_folder_is_409(client_vuoto, tmp_path):
    a, b, gone = tmp_path / "a", tmp_path / "b", tmp_path / "ritirata"
    for p in (a, b, gone):
        p.mkdir()
    fa = _client_folder(client_vuoto, a)
    fb = _client_folder(client_vuoto, b)
    fg = _client_folder(client_vuoto, gone)
    client_vuoto.delete(f"/api/v1/folders/{fg['id']}")
    for target, owner in ((b, fb), (gone, fg)):
        r = client_vuoto.post(f"/api/v1/folders/{fa['id']}/move", json={"root_path": str(target)})
        assert r.status_code == 409
        assert r.json()["detail"] == {"code": "folder_exists", "folder_id": owner["id"]}
    r = client_vuoto.post("/api/v1/folders/99999/move", json={"root_path": str(b)})
    assert r.status_code == 404


def _probe(client, root):
    return client.post("/api/v1/folders/probe", json={"root_path": str(root)}).json()


def test_the_probe_recognises_an_unreachable_folder_moved_here(client_vuoto, tmp_path):
    old, new = tmp_path / "D" / "Astro", tmp_path / "E" / "Astro"
    _archive(old)
    f = _client_folder(client_vuoto, old)
    _scanned(client_vuoto, f["id"])
    new.parent.mkdir()
    os.rename(old, new)

    p = _probe(client_vuoto, new)

    assert p["moved_check"] == "found"
    assert p["moved_from"] == {"id": f["id"], "root_path": f["root_path"]}


def test_the_probe_recognises_a_retired_folder_and_moving_it_brings_it_back(client_vuoto, tmp_path):
    old, new = tmp_path / "vecchia", tmp_path / "nuova"
    _archive(old)
    f = _client_folder(client_vuoto, old)
    _scanned(client_vuoto, f["id"])
    client_vuoto.delete(f"/api/v1/folders/{f['id']}")
    shutil.copytree(old, new)

    p = _probe(client_vuoto, new)
    assert (p["moved_check"], p["moved_from"]["id"]) == ("found", f["id"])

    r = client_vuoto.post(f"/api/v1/folders/{f['id']}/move", json={"root_path": str(new)})
    assert r.status_code == 200, r.text
    assert r.json()["reactivated"] is True
    listed = client_vuoto.get("/api/v1/folders").json()["items"]
    assert [(x["id"], x["root_path"]) for x in listed] == [(f["id"], os.path.realpath(new))]


def test_a_copy_of_a_reachable_folder_is_not_a_move(client_vuoto, tmp_path):
    old, copy = tmp_path / "vecchia", tmp_path / "copia"
    _archive(old)
    f = _client_folder(client_vuoto, old)
    _scanned(client_vuoto, f["id"])
    shutil.copytree(old, copy)

    p = _probe(client_vuoto, copy)

    assert (p["moved_check"], p["moved_from"]) == ("none", None)


def test_the_probe_of_a_place_it_cannot_reach_does_not_look_for_a_move(client_vuoto, tmp_path):
    p = _probe(client_vuoto, tmp_path / "non-ce")
    assert (p["moved_check"], p["moved_from"]) == ("place_unreachable", None)
