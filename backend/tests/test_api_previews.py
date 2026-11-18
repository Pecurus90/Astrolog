"""L'anteprima di una produzione (passo 33.2): la foto che l'utente carica sulla carta
dell'Archivio. Si legge dai byte, si riduce, segue rinomine e correzioni, viaggia nel backup."""

import io

import numpy as np
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image

from astrolog.api.app import create_app
from astrolog.db.connect import connect, create_database
from astrolog.spine import previews


def foto(fmt="JPEG", size=(3000, 2000), mode="RGB", **salva) -> bytes:
    out = io.BytesIO()
    Image.new(mode, size, 120 if mode in ("L", "I;16") else (200, 40, 40)).save(out, fmt, **salva)
    return out.getvalue()


def riga_con_produzione(client):
    """La prima riga d'oggetto che ha una produzione, col suo posto."""
    for riga in client.get("/api/v1/archive", params={"limit": 50}).json()["items"]:
        if riga["panels"] is None and riga["previews"]:
            return riga
    pytest.fail("l'archivio di prova non ha una produzione: la prova non guarda niente")


def metti(client, url, corpo, tipo="image/jpeg"):
    return client.put(url, content=corpo, headers={"Content-Type": tipo})


def test_a_card_has_one_empty_place_per_production(client):
    """Prima di ogni foto: un posto per produzione, coi suoi indirizzi, e nessuna data."""
    riga = riga_con_produzione(client)
    assert len(riga["previews"]) == len(riga["productions"])
    assert all(p["at"] is None for p in riga["previews"])
    assert len({p["url"] for p in riga["previews"]}) == len(riga["previews"])


def test_a_photo_put_is_read_back_shrunk_and_named_on_the_card(client):
    riga = riga_con_produzione(client)
    posto = riga["previews"][0]

    r = metti(client, posto["url"], foto("PNG"), "image/png")
    assert r.status_code == 200, r.text
    assert r.json()["at"] is not None

    letta = client.get(posto["url"])
    assert letta.status_code == 200
    assert letta.headers["content-type"] == "image/jpeg"
    assert "gzip" not in letta.headers.get("content-encoding", "")
    assert Image.open(io.BytesIO(letta.content)).size == (1200, 800)
    di_nuovo = client.get(posto["url"], headers={"If-None-Match": letta.headers["etag"]})
    assert di_nuovo.status_code == 304

    carta = next(
        o
        for o in client.get("/api/v1/archive", params={"limit": 50}).json()["items"]
        if o["key"] == riga["key"]
    )
    assert carta["previews"][0]["at"] == r.json()["at"]


def test_what_is_not_a_photo_is_refused_with_its_reason(client):
    posto = riga_con_produzione(client)["previews"][0]
    r = metti(client, posto["url"], b"SIMPLE  =                    T", "image/jpeg")
    assert (r.status_code, r.json()["detail"]["code"]) == (422, "not_an_image")
    # il tipo dichiarato non decide: un TIFF detto JPEG resta un TIFF
    r = metti(client, posto["url"], foto("TIFF", (40, 40)), "image/jpeg")
    assert r.json()["detail"]["code"] == "not_an_image"
    assert client.get(posto["url"]).json()["detail"]["code"] == "no_preview"


def test_a_photo_past_the_limit_is_refused_before_it_is_read(client, monkeypatch):
    monkeypatch.setattr(previews, "MAX_BYTES", 1000)
    posto = riga_con_produzione(client)["previews"][0]
    r = metti(client, posto["url"], foto())
    assert (r.status_code, r.json()["detail"]["code"]) == (413, "too_large")


def test_too_many_pixels_are_refused_from_the_header(client, monkeypatch):
    monkeypatch.setattr(previews, "MAX_PIXELS", 1000)
    posto = riga_con_produzione(client)["previews"][0]
    r = metti(client, posto["url"], foto())
    assert (r.status_code, r.json()["detail"]["code"]) == (422, "too_many_pixels")


def test_a_photo_past_pillows_bomb_guard_is_too_big_not_unreadable():
    """Oltre la soglia di Pillow (~89 Mpx) la foto e' troppo grande, non illeggibile."""
    with pytest.raises(previews.PreviewError) as e:
        previews.shrink(foto("PNG", (10000, 9500), "L"))
    assert e.value.code == "too_many_pixels"


def test_an_unknown_row_or_production_is_said(client):
    r = client.put("/api/v1/archive/preview", params={"key": "nessuno", "production": "1:1"},
                   content=foto())  # fmt: skip
    assert (r.status_code, r.json()["detail"]["code"]) == (404, "object_not_found")
    riga = riga_con_produzione(client)
    r = client.put("/api/v1/archive/preview", params={"key": riga["key"], "production": "999:999"},
                   content=foto())  # fmt: skip
    assert r.json()["detail"]["code"] == "production_not_found"
    r = client.put("/api/v1/archive/preview", params={"key": riga["key"]}, content=foto())
    assert (r.status_code, r.json()["detail"]["code"]) == (422, "production_required")


def test_removing_takes_the_photo_and_its_file(client, db_path):
    posto = riga_con_produzione(client)["previews"][0]
    metti(client, posto["url"], foto())
    cartella = previews.folder_of(db_path)
    assert len(list(cartella.glob("*.jpg"))) == 1
    assert client.delete(posto["url"]).status_code == 204
    assert list(cartella.glob("*.jpg")) == []
    assert client.delete(posto["url"]).json()["detail"]["code"] == "no_preview"


def test_a_sixteen_bit_grey_png_is_not_burnt_white():
    """Un'elaborazione finita in scala di grigi a 16 bit: `convert` lo taglierebbe."""
    grigio = Image.fromarray(np.full((50, 60), 30000, dtype=np.uint16))
    out = io.BytesIO()
    grigio.save(out, "PNG")
    piccola = Image.open(io.BytesIO(previews.shrink(out.getvalue())))
    assert 100 < piccola.getpixel((10, 10))[0] < 140


def test_a_phone_photo_stands_up_and_loses_its_exif():
    exif = Image.Exif()
    exif[0x0112] = 6  # ruotata di 90 gradi, come la scrive il telefono
    exif[0x010F] = "telefono"  # la marca: con lei uscirebbero ora e GPS
    piccola = Image.open(io.BytesIO(previews.shrink(foto(size=(300, 200), exif=exif))))
    assert piccola.size == (200, 300)
    assert not piccola.getexif()


def test_the_colour_profile_stays():
    profilo = b"\x00" * 128 + b"profilo finto"
    try:
        piccola = Image.open(io.BytesIO(previews.shrink(foto(size=(30, 20), icc_profile=profilo))))
    except previews.PreviewError:
        pytest.skip("Pillow rifiuta un profilo finto: si prova solo che lo passa")
    assert piccola.info.get("icc_profile") == profilo


def _scrivi(conn, ottica, camera, sha, chiave="m31"):
    conn.execute(
        "INSERT INTO production_previews (owner_kind, owner_key, optics, camera, sha256,"
        " updated_at) VALUES ('object', ?, ?, ?, ?, 'x')",
        (chiave, ottica, camera, sha * 64),
    )


def _posti(conn):
    return sorted(
        conn.execute("SELECT owner_key, optics, camera, sha256 FROM production_previews"),
        key=str,
    )


def test_a_renamed_camera_takes_its_photos_and_wins(db_path):
    """Rinomina: vince cio' che si sposta, come le dichiarazioni."""
    conn = connect(db_path)
    _scrivi(conn, "RedCat", "ASI vecchia", "a")
    _scrivi(conn, "RedCat", "ASI nuova", "b")
    previews.follow_instrument(conn, "camera", "ASI vecchia", "ASI nuova", merging=False)
    assert [tuple(r) for r in _posti(conn)] == [("m31", "RedCat", "ASI nuova", "a" * 64)]


def test_a_merged_camera_leaves_the_kept_photo(db_path):
    """Unione: vince il pezzo che resta; la foto dell'altro esce."""
    conn = connect(db_path)
    _scrivi(conn, "RedCat", "ASI vecchia", "a")
    _scrivi(conn, "RedCat", "ASI nuova", "b")
    _scrivi(conn, "Esprit", "ASI vecchia", "c")
    previews.follow_instrument(conn, "camera", "ASI vecchia", "ASI nuova", merging=True)
    assert {tuple(r) for r in _posti(conn)} == {
        ("m31", "Esprit", "ASI nuova", "c" * 64),
        ("m31", "RedCat", "ASI nuova", "b" * 64),
    }


def test_a_filter_renamed_touches_no_photo(db_path):
    conn = connect(db_path)
    _scrivi(conn, "RedCat", "ASI", "a")
    previews.follow_instrument(conn, "filter_wheel", "ASI", "Altro", merging=False)
    assert len(_posti(conn)) == 1


def test_a_corrected_object_takes_its_photos_along(db_path):
    """Correzione in Da confermare: la foto va con l'oggetto, dove il bersaglio non ne ha una."""
    conn = connect(db_path)
    _scrivi(conn, "RedCat", "ASI", "a", chiave="ngc 224 sbagliato")
    _scrivi(conn, "Esprit", "ASI", "b", chiave="ngc 224 sbagliato")
    _scrivi(conn, "Esprit", "ASI", "c", chiave="m31")
    previews.follow_object(conn, "ngc 224 sbagliato", "m31")
    assert {(r[0], r[1], r[3][0]) for r in _posti(conn)} == {
        ("m31", "RedCat", "a"),
        ("m31", "Esprit", "c"),
        ("ngc 224 sbagliato", "Esprit", "b"),
    }


def test_the_correction_of_da_confermare_moves_the_photo(db_path):
    """La strada vera: `correct_object`, non la funzione della foto chiamata a mano."""
    from astrolog.spine.object_answer import correct_object

    conn = connect(db_path)
    _scrivi(conn, "RedCat", "ASI", "a", chiave="m 31 scritto male")
    correct_object(conn, "m 31 scritto male", slug="m31")
    assert [r[0] for r in _posti(conn)] == ["m31"]


def _file(db_path, sha):
    cartella = previews.folder_of(db_path)
    cartella.mkdir(exist_ok=True)
    (cartella / f"{sha * 64}.jpg").write_bytes(b"jpeg")


def _file_rimasti(db_path):
    return sorted(p.name[0] for p in previews.folder_of(db_path).glob("*.jpg"))


@pytest.mark.parametrize("unendo", [False, True])
def test_a_photo_left_by_a_renamed_or_merged_camera_leaves_the_disk(db_path, unendo):
    """#92: la foto che perde il posto non resta su disco; quella che lo tiene si'."""
    from astrolog.api.review_write import writing

    conn = connect(db_path)
    _scrivi(conn, "RedCat", "ASI vecchia", "a")
    _scrivi(conn, "RedCat", "ASI nuova", "b")
    conn.commit()
    for sha in "ab":
        _file(db_path, sha)
    with writing(conn):
        previews.follow_instrument(conn, "camera", "ASI vecchia", "ASI nuova", merging=unendo)
    assert _file_rimasti(db_path) == (["b"] if unendo else ["a"])


def test_a_merge_rolled_back_keeps_both_photos(db_path):
    """#92: un Apply che fallisce dopo la fusione rimette il posto, e il posto il suo file."""
    from astrolog.api.review_write import writing

    conn = connect(db_path)
    _scrivi(conn, "RedCat", "ASI vecchia", "a")
    _scrivi(conn, "RedCat", "ASI nuova", "b")
    conn.commit()
    for sha in "ab":
        _file(db_path, sha)
    with pytest.raises(HTTPException), writing(conn):
        previews.follow_instrument(conn, "camera", "ASI vecchia", "ASI nuova", merging=True)
        raise LookupError("seconda coppia non piu' chiesta")
    assert len(_posti(conn)) == 2
    assert _file_rimasti(db_path) == ["a", "b"]


def test_a_restored_slot_drops_the_photo_it_replaces(db_path):
    """#92: il ripristino che cambia la foto di un posto toglie la vecchia dal disco."""
    from astrolog.spine.backup import restore

    conn = connect(db_path)
    _scrivi(conn, "RedCat", "ASI", "a")
    for sha in "ab":
        _file(db_path, sha)
    voce = {"owner_kind": "object", "owner_key": "m31", "optics": "RedCat", "camera": "ASI"}
    restore(conn, {"previews": [{**voce, "sha256": "b" * 64, "updated_at": "y"}]}, db_path=db_path)
    assert _file_rimasti(db_path) == ["b"]


def test_the_export_carries_the_photo_and_the_import_puts_it_back(client, tmp_path):
    """Marco, 18/11: le foto stanno dentro Esporta. Il file accanto al database le nomina solo."""
    posto = riga_con_produzione(client)["previews"][0]
    metti(client, posto["url"], foto())
    esportato = client.get("/api/v1/backup/export").json()
    [voce] = esportato["previews"]
    assert voce["jpeg"]

    altrove = tmp_path / "altrove" / "astrolog.db"
    altrove.parent.mkdir()
    create_database(altrove)
    with TestClient(create_app(altrove), base_url="http://localhost") as nuovo:
        r = nuovo.post("/api/v1/backup/import", json=esportato)
        assert r.status_code == 200, r.text
    conn = connect(altrove)
    [(sha,)] = conn.execute("SELECT sha256 FROM production_previews").fetchall()
    assert previews.read(altrove, sha) is not None


def test_a_forged_photo_in_an_import_is_not_a_backup(client):
    esportato = client.get("/api/v1/backup/export").json()
    esportato["previews"] = [{"owner_kind": "object", "owner_key": "m31", "optics": None,
                              "camera": None, "sha256": "a" * 64, "updated_at": "x",
                              "jpeg": "bm9uIGUnIHVuYSBmb3Rv"}]  # fmt: skip
    r = client.post("/api/v1/backup/import", json=esportato)
    assert (r.status_code, r.json()["detail"]["code"]) == (422, "not_a_backup")


def test_an_imported_name_cannot_reach_a_file_outside_the_folder(client, db_path):
    """Un posto senza foto nomina solo un hash: un '../' non legge ne' cancella altro."""
    vittima = db_path.parent / "vittima.jpg"
    vittima.write_bytes(foto(size=(20, 20)))
    esportato = client.get("/api/v1/backup/export").json()
    esportato["previews"] = [{"owner_kind": "object", "owner_key": "m31", "optics": None,
                              "camera": None, "sha256": "./" * 27 + "../vittima",
                              "updated_at": "x"}]  # fmt: skip
    assert client.post("/api/v1/backup/import", json=esportato).status_code == 200
    assert connect(db_path).execute("SELECT 1 FROM production_previews").fetchall() == []
    assert vittima.exists()


def test_the_schema_refuses_a_name_that_is_not_a_hash(db_path):
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError):
        _scrivi(connect(db_path), "RedCat", "ASI", ".")  # 64 caratteri, nessuno esadecimale


def test_the_file_beside_the_database_names_photos_without_carrying_them(client, db_path):
    from astrolog.spine import backup

    posto = riga_con_produzione(client)["previews"][0]
    metti(client, posto["url"], foto())
    [voce] = backup.read(backup.path_for(db_path))["previews"]
    assert "jpeg" not in voce
    assert previews.read(db_path, voce["sha256"]) is not None
