"""Lo stadio di scansione: le richieste dell'utente in `docs/domini/spina.md`, una per test.
Tutto su FITS veri fabbricati con astropy e su un DB nato da schema.sql."""

import json
import os

import numpy as np
from astropy.io import fits

import astrolog.fits.walk as walk_mod
import astrolog.spine.scan as scan_mod
from astrolog.fits.header_read import HeaderReadError
from astrolog.spine import frame_folder, typeless
from astrolog.spine.scan import scan_folder
from astrolog.spine.stages import STAGES, WAITING_SQL, count_pending
from conftest import (
    CartellaLegata,
    add_folder,
    fake_entries,
    online_only,
    settle,
    unreadable_dir,
    write_fits,
    write_light,
)


def run(conn, folder_id, **kw):
    events = list(scan_folder(conn, folder_id, **kw))
    assert events[-1]["done"]
    return events[-1]


def count(conn, sql):
    return conn.execute(sql).fetchone()[0]


def test_scan_walk_finds_everything_and_never_touches_the_files(conn, tmp_path):
    root = tmp_path / "IC 405 - Nebulosa"
    for i in range(3):
        write_light(
            root / "notte 1" / f"posa n° {i} à.fits", obj="IC 405", date=f"2024-12-23T21:0{i}:00"
        )
    write_light(root / "b.fit", obj="M 31")
    before = {p: (p.stat().st_size, p.stat().st_mtime) for p in root.rglob("*.fit*")}
    done = run(conn, add_folder(conn, root))
    assert (done["status"], done["found"], done["new"]) == ("ok", 4, 4)
    assert {p: (p.stat().st_size, p.stat().st_mtime) for p in root.rglob("*.fit*")} == before
    assert count(conn, "SELECT COUNT(*) FROM frames") == 4
    assert count(conn, "SELECT COUNT(*) FROM positions") == 4


def test_scan_reads_header_only(conn, tmp_path):
    """Un file con l'header intero ma SENZA il blocco dei pixel entra lo stesso: la
    scansione non ha bisogno dei pixel. Se qualcuno li leggesse, questo test diventa rosso."""
    path = write_light(tmp_path / "a.fits", obj="M 42")
    with open(path, "rb") as f:
        raw = f.read()
    end = raw.index(b"END" + b" " * 77)
    header_only = raw[: ((end // 2880) + 1) * 2880]
    with open(path, "wb") as f:
        f.write(header_only)
    settle(path)
    done = run(conn, add_folder(conn, tmp_path))
    assert done["new"] == 1 and done["errors"] == 0
    assert conn.execute("SELECT object_raw FROM frames").fetchone()[0] == "M 42"


def test_scan_stores_raw_fields_and_marks_every_stage_pending(conn, tmp_path):
    write_light(
        tmp_path / "a.fits",
        obj="m31",
        filt="Ha 7nm",
        TELESCOP="Askar 103APO",
        INSTRUME="ZWO ASI2600MM",
        SWCREATE="N.I.N.A. 3.1",
        BAYERPAT="RGGB",
        XPIXSZ=3.76,
        FOCALLEN=700.0,
        GAIN=100,
        SITELAT=45.5,
        SITELONG=9.2,
    )
    run(conn, add_folder(conn, tmp_path))
    row = conn.execute("SELECT * FROM frames").fetchone()
    assert (row["object_raw"], row["filter_raw"], row["telescope_raw"]) == (
        "m31",
        "Ha 7nm",
        "Askar 103APO",
    )
    assert (row["software_raw"], row["bayer_pattern"], row["pixel_size_um"]) == (
        "N.I.N.A. 3.1",
        "RGGB",
        3.76,
    )
    assert row["image_type"] == "light" and row["header_json"].startswith("[")
    assert row["filter_id"] is None and row["object_id"] is None  # normalize non e' passato
    assert {r[0] for r in conn.execute("SELECT stage FROM frame_stages")} == set(STAGES)
    for stage in STAGES:
        assert count_pending(conn, stage) == 1


def test_scan_incremental(conn, tmp_path):
    for i in range(3):
        write_light(tmp_path / f"f{i}.fits", obj=f"M {i}")
    fid = add_folder(conn, tmp_path)
    first = run(conn, fid)
    second = run(conn, fid)
    assert (first["new"], second["new"], second["unchanged"]) == (3, 0, 3)
    assert count(conn, "SELECT COUNT(*) FROM frames") == 3
    # un file rinominato resta lo stesso frame, con la posizione nuova e la vecchia sparita
    os.rename(tmp_path / "f0.fits", tmp_path / "rinominato.fits")
    third = run(conn, fid)
    assert count(conn, "SELECT COUNT(*) FROM frames") == 3
    assert (third["new"], third["missing"]) == (0, 1)
    assert count(conn, "SELECT COUNT(*) FROM positions WHERE status = 'present'") == 3


def test_scan_duplicate_header(conn, tmp_path):
    a = write_light(tmp_path / "a" / "x.fits", obj="M 51")
    os.makedirs(tmp_path / "b")
    with open(a, "rb") as src, open(tmp_path / "b" / "copia.fits", "wb") as dst:
        dst.write(src.read())
    settle(tmp_path / "b" / "copia.fits")
    done = run(conn, add_folder(conn, tmp_path))
    assert (done["new"], done["duplicates"]) == (1, 1)
    assert count(conn, "SELECT COUNT(*) FROM frames") == 1
    assert count(conn, "SELECT COUNT(*) FROM positions") == 2


def test_scan_missing_returns(conn, tmp_path):
    p = write_light(tmp_path / "a.fits")
    fid = add_folder(conn, tmp_path)
    run(conn, fid)
    with open(p, "rb") as f:
        data = f.read()
    os.remove(p)
    assert run(conn, fid)["missing"] == 1
    assert count(conn, "SELECT COUNT(*) FROM frames") == 1  # mai cancellato
    assert conn.execute("SELECT status FROM positions").fetchone()[0] == "missing"
    with open(p, "wb") as f:
        f.write(data)
    settle(p)
    run(conn, fid)
    assert conn.execute("SELECT status FROM positions").fetchone()[0] == "present"


def test_scan_skips_calibration(conn, tmp_path):
    """Nessun file di calibrazione entra in archivio -- e non solo nella grafia di chi l'ha
    scritto per primo: le grafie sono quelle di programmi diversi (`Dark Frame` dello standard,
    `DARKFLAT` di N.I.N.A., il trattino, il plurale) piu' i due casi in cui il tipo NON sta in
    `IMAGETYP`: la libreria che lo dichiara in `OBJECT` e il file gia' sommato."""
    write_light(tmp_path / "light.fits")
    for name, typ in (
        ("dark", "Dark"),
        ("flat", "Flat Field"),
        ("bias", "Bias Frame"),
        ("df", "Dark Flat"),
        ("df2", "DARK-FLAT"),
        ("darks", "darks"),
    ):
        write_fits(tmp_path / f"{name}.fits", {"IMAGETYP": typ, "EXPTIME": 1.0})
    # il tipo non e' in IMAGETYP: lo dice il nome del target, o il fatto che sia una somma
    write_fits(tmp_path / "lib.fits", {"IMAGETYP": "LIGHT", "OBJECT": "flats", "EXPTIME": 1.0})
    write_fits(tmp_path / "master.fits", {"IMAGETYP": "Light", "NCOMBINE": 40, "OBJECT": "M 1"})
    done = run(conn, add_folder(conn, tmp_path))
    assert (done["found"], done["new"], done["skipped"]) == (9, 1, 8)
    assert count(conn, "SELECT COUNT(*) FROM frames") == 1
    assert count(conn, "SELECT COUNT(*) FROM positions") == 1


def _muto(tmp_path, name="muto.fits"):
    """Un file che non dice `IMAGETYP`: lo lasciano muto alcuni programmi di ripresa, e non si sa
    se e' una foto del cielo o un file di calibrazione. Quali siano lo dice
    `astrolog/fits/frame_type.py`, che e' la casa di quella decisione.

    test-tolto: test_scan_unknown_type_enters -- rinominato in
    `test_scan_unknown_type_enters_and_waits_before_the_object`, che prova anche l'attesa."""
    write_fits(
        tmp_path / name,
        {"OBJECT": "M 13", "EXPTIME": 60.0, "DATE-OBS": "2024-05-17T21:00:00"},
    )


def _aspetta(conn):
    """Se qualcuno di questi frame aspetta di sapere che file e': il segno scritto sulla posa, lo
    stesso che legge chi decide chi e' pronto (`spine/stages.py`)."""
    sql = f"SELECT COUNT(*) FROM frames f WHERE {WAITING_SQL}"  # noqa: S608 - una costante
    return conn.execute(sql).fetchone()[0] > 0


def test_scan_unknown_type_enters_and_waits_before_the_object(conn, tmp_path):
    """Un file senza `IMAGETYP` entra -- non si perde -- e aspetta che il cielo dica che file e':
    finche' non lo sa non ha un oggetto, quindi non diventa ore e non finisce fra i Frame senza
    nome, dove la domanda e' "cosa hai ripreso" e non "che file e'"."""
    _muto(tmp_path)
    done = run(conn, add_folder(conn, tmp_path))
    assert done["new"] == 1
    assert conn.execute("SELECT image_type FROM frames").fetchone()[0] == "unknown"
    assert _aspetta(conn)


def test_scan_skips_a_folder_the_user_called_calibration(conn, tmp_path):
    """Detto che in quella cartella ci sono file di calibrazione, i file nuovi che arrivano dopo
    non entrano affatto e la ricevuta li conta per motivo, come quelli che lo dicono da soli. Un
    frame gia' in archivio spostato li' invece entra (`test_review_typeless.py`)."""
    folder_id = add_folder(conn, tmp_path)
    typeless.declare(conn, frame_folder.folder_key(str(tmp_path)), typeless.CALIBRATION)
    _muto(tmp_path, "dark.fits")
    done = run(conn, folder_id)
    assert (done["new"], done["skipped"]) == (0, 1)
    assert done["skipped_by_reason"] == [{"reason": "calibration", "count": 1}]
    assert count(conn, "SELECT COUNT(*) FROM frames") == 0


def test_scan_lets_in_a_folder_the_user_called_sky(conn, tmp_path):
    """Detto che in quella cartella ci sono foto del cielo, i file che arrivano dopo fanno la
    strada di un light da subito: la risposta vale anche per loro, senza ri-chiedere."""
    folder_id = add_folder(conn, tmp_path)
    typeless.declare(conn, frame_folder.folder_key(str(tmp_path)), typeless.LIGHT)
    _muto(tmp_path)
    done = run(conn, folder_id)
    assert done["new"] == 1
    assert not _aspetta(conn)


def test_scan_partial_file(conn, tmp_path):
    fresh = write_light(tmp_path / "fresh.fits")
    write_light(tmp_path / "old.fits", obj="M 2")
    settle(fresh, 0)  # ancora in scrittura
    fid = add_folder(conn, tmp_path)
    done = run(conn, fid, min_age_s=30)
    assert (done["new"], done["skipped"]) == (1, 1)
    assert done["skipped_by_reason"] == [{"reason": "still_writing", "count": 1}]
    settle(fresh, 120)
    assert run(conn, fid, min_age_s=30)["new"] == 1  # alla scansione dopo entra


def test_the_default_wait_is_the_one_that_runs_in_production(conn, tmp_path):
    """I 30 secondi di attesa sono il **default**, ed e' quello che gira davvero: la corsa
    vera non passa `min_age_s` (`spine/run.py`). Ogni altro test lo passa a mano, quindi il
    valore che conta non era pinnato da nessuno: portarlo a zero lasciava la suite verde e
    faceva entrare in archivio i file che la camera sta ancora scrivendo."""
    assert scan_mod.DEFAULT_MIN_AGE_S >= 30
    adesso = write_light(tmp_path / "adesso.fits")
    settle(adesso, 0)  # appena scritto: la camera potrebbe non aver finito
    fid = add_folder(conn, tmp_path)
    done = run(conn, fid)  # senza min_age_s: come in produzione
    assert (done["new"], done["skipped"]) == (0, 1)
    assert done["skipped_by_reason"] == [{"reason": "still_writing", "count": 1}]


def test_scan_beyond_260_characters_reads_the_header(conn, tmp_path):
    """Il tratto lungo della scansione (stat + astropy sulla forma `\\\\?\\`), non solo il walk."""
    from astrolog.fits.walk import long_path

    deep = str(tmp_path)
    while len(deep) < 300:
        deep = os.path.join(deep, "Nebulosa della Testa di Cavallo - IC 434 - sessione lunga")
    os.makedirs(long_path(deep), exist_ok=True)
    write_light(long_path(os.path.join(deep, "frame.fits")), obj="IC 434")
    done = run(conn, add_folder(conn, tmp_path))
    assert (done["new"], done["errors"]) == (1, 0)
    assert conn.execute("SELECT object_raw FROM frames").fetchone()[0] == "IC 434"


def test_scan_bad_header_counted(conn, tmp_path, monkeypatch):
    """Un file che non si legge si conta, e la ricevuta lo nomina con un codice e non con la
    frase dell'eccezione: un file senza permessi e un file rotto sono due motivi diversi."""
    write_light(tmp_path / "ok.fits")
    write_light(tmp_path / "chiuso.fits", obj="M 2")
    (tmp_path / "rotto.fits").write_bytes(b"non e' un FITS\x00" * 50)
    settle(tmp_path / "rotto.fits")
    vera = scan_mod.read_frame

    def senza_permesso(p):
        if os.path.basename(p) == "chiuso.fits":
            raise HeaderReadError(p, PermissionError(13, "accesso negato (mock)"))
        return vera(p)

    monkeypatch.setattr(scan_mod, "read_frame", senza_permesso)
    done = run(conn, add_folder(conn, tmp_path))
    assert (done["new"], done["errors"]) == (1, 2)
    assert done["errors_detail"] == [
        {"file": "chiuso.fits", "reason": "file_unreadable"},
        {"file": "rotto.fits", "reason": "header_unreadable"},
    ]


def test_scan_root_gone_aborts(conn, tmp_path):
    root = tmp_path / "nas"
    write_light(root / "a.fits")
    fid = add_folder(conn, root)
    run(conn, fid)
    os.remove(root / "a.fits")
    os.rmdir(root)
    done = run(conn, fid)
    assert (done["status"], done["reason"]) == ("aborted", "root_unreachable")
    assert conn.execute("SELECT status FROM positions").fetchone()[0] == "present"  # intatta
    assert conn.execute("SELECT status, reason FROM scan_runs ORDER BY id DESC").fetchone()[:] == (
        "aborted",
        "root_unreachable",
    )


def test_scan_root_gone_midway_aborts_without_marking_missing(conn, tmp_path, monkeypatch):
    """La condivisione cade DURANTE la scansione: `aborted`, e i file gia' in archivio non
    diventano "non trovato"."""
    root = tmp_path / "nas"
    for i in range(4):
        write_light(root / f"f{i}.fits", obj=f"M {i}")
    fid = add_folder(conn, root)
    run(conn, fid)
    real_stat = os.stat
    calls = []

    def stat_then_vanish(path, *a, **kw):
        calls.append(path)
        if len(calls) == 2:
            for p in root.iterdir():
                p.unlink()
            root.rmdir()
        return real_stat(path, *a, **kw)

    monkeypatch.setattr(scan_mod.os, "stat", stat_then_vanish)
    done = run(conn, fid)
    assert (done["status"], done["reason"]) == ("aborted", "root_unreachable")
    assert done["missing"] == 0
    assert count(conn, "SELECT COUNT(*) FROM positions WHERE status = 'present'") == 4


def test_scan_root_gone_while_reading_a_header_aborts(conn, tmp_path, monkeypatch):
    """Il caso vero su NAS: la condivisione cade dentro la lettura dell'header (la parte
    lenta), che esce come HeaderReadError. Deve essere `aborted`, non `ok` con N errori."""
    root = tmp_path / "nas"
    for i in range(4):
        write_light(root / f"f{i}.fits", obj=f"M {i}")
    fid = add_folder(conn, root)
    real = scan_mod.read_frame
    calls = []

    def read_then_vanish(path):
        calls.append(path)
        if len(calls) == 2:
            for p in root.iterdir():
                p.unlink()
            root.rmdir()
        return real(path)

    monkeypatch.setattr(scan_mod, "read_frame", read_then_vanish)
    done = run(conn, fid)
    assert (done["status"], done["reason"], done["errors"]) == ("aborted", "root_unreachable", 0)


def test_scan_file_growing_while_read_is_skipped(conn, tmp_path, monkeypatch):
    p = write_light(tmp_path / "a.fits")
    real = scan_mod.read_frame

    def read_and_grow(path):
        result = real(path)
        with open(p, "ab") as f:
            f.write(b"\0" * 2880)  # il software sta ancora scrivendo i pixel
        return result

    monkeypatch.setattr(scan_mod, "read_frame", read_and_grow)
    done = run(conn, add_folder(conn, tmp_path))
    assert (done["new"], done["skipped"]) == (0, 1)
    assert done["skipped_by_reason"] == [{"reason": "still_writing", "count": 1}]


def test_scan_root_unreadable_right_after_the_precheck_aborts(conn, tmp_path, monkeypatch):
    """Il pre-controllo passa, ma il walk non riesce ad aprire la radice: `aborted`, e le
    posizioni restano com'erano."""
    write_light(tmp_path / "a.fits")
    fid = add_folder(conn, tmp_path)
    run(conn, fid)

    def walk_that_cannot_open_the_root(root, found=None, unreadable=None, **_):
        unreadable.append(root)
        return []

    monkeypatch.setattr(scan_mod, "walk_dir", walk_that_cannot_open_the_root)
    done = run(conn, fid)
    assert (done["status"], done["reason"], done["missing"]) == ("aborted", "root_unreachable", 0)
    assert conn.execute("SELECT status FROM positions").fetchone()[0] == "present"


def test_scan_unreadable_subfolder_does_not_mark_its_frames_missing(conn, tmp_path, monkeypatch):
    sub = tmp_path / "chiusa"
    write_light(tmp_path / "a.fits")
    write_light(sub / "b.fits", obj="M 2")
    fid = add_folder(conn, tmp_path)
    assert run(conn, fid)["new"] == 2
    unreadable_dir(monkeypatch, walk_mod, sub)
    done = run(conn, fid)
    assert done["missing"] == 0 and len(done["unreadable_dirs"]) == 1
    assert count(conn, "SELECT COUNT(*) FROM positions WHERE status = 'present'") == 2


def test_scan_unreadable_dirs(conn, tmp_path, monkeypatch):
    write_light(tmp_path / "a.fits")
    sub = tmp_path / "chiusa"
    write_light(sub / "b.fits")
    unreadable_dir(monkeypatch, walk_mod, sub)
    done = run(conn, add_folder(conn, tmp_path))
    assert done["new"] == 1 and len(done["unreadable_dirs"]) == 1


def test_scan_does_not_download_an_online_only_file(conn, tmp_path, monkeypatch):
    """Un file solo online non si apre -- aprirlo lo scaricherebbe --: si conta nella ricevuta,
    e quando torna sul disco la scansione dopo lo prende."""
    write_light(tmp_path / "a.fits")
    write_light(tmp_path / "b.fits", obj="M 2", date="2024-05-17T22:00:00")
    fid = add_folder(conn, tmp_path)
    aperti, vera = [], scan_mod.read_frame
    # un contesto suo: `monkeypatch.undo()` toglierebbe anche il recinto di tutta la suite
    with monkeypatch.context() as finto:
        online_only(finto, tmp_path / "b.fits")
        finto.setattr(scan_mod, "read_frame", lambda p: aperti.append(p) or vera(p))
        done = run(conn, fid)
    assert (done["new"], done["online_only"]) == (1, 1)
    assert done["found"] == 2  # incontrati tutti e due: uno letto, uno lasciato dov'e'
    assert not any(os.path.basename(p) == "b.fits" for p in aperti)
    assert count(conn, "SELECT online_only FROM scan_runs") == 1
    assert run(conn, fid)["new"] == 1  # di nuovo sul disco: entra


def test_scan_a_missing_pose_that_comes_back_online_only_is_present_again(
    conn, tmp_path, monkeypatch
):
    """Una posa "non trovata" che ricompare solo online e' di nuovo li': torna presente, come se
    fosse tornata sul disco."""
    posa, altrove = tmp_path / "a.fits", tmp_path / "a.bak"
    write_light(posa)
    fid = add_folder(conn, tmp_path)
    run(conn, fid)
    posa.rename(altrove)
    assert run(conn, fid)["missing"] == 1
    altrove.rename(posa)
    online_only(monkeypatch, posa)
    run(conn, fid)
    assert count(conn, "SELECT COUNT(*) FROM positions WHERE status = 'present'") == 1


def test_scan_names_the_linked_folders_it_does_not_follow(conn, tmp_path, monkeypatch):
    """Una sottocartella raggiunta da una giunzione o da un collegamento non si percorre, ma la
    ricevuta la nomina: invece di "0 file" senza una ragione, l'utente vede dove guardare."""
    write_light(tmp_path / "a.fits")
    write_light(tmp_path / "giunzione" / "b.fits", obj="M 2")
    fake_entries(
        monkeypatch, lambda _c, v: CartellaLegata(v, junction=True) if v.name == "giunzione" else v
    )
    done = run(conn, add_folder(conn, tmp_path))
    assert done["new"] == 1
    assert [os.path.basename(d) for d in done["linked_dirs"]] == ["giunzione"]
    assert "giunzione" in conn.execute("SELECT linked_dirs_json FROM scan_runs").fetchone()[0]


def test_scan_poses_under_a_folder_that_becomes_hidden_are_missing(conn, tmp_path):
    """Una cartella che diventa nascosta -- e' il caso del cestino -- esce dall'archivio: le sue
    pose diventano "non trovate", e la ricevuta dice quale cartella ha lasciato fuori."""
    write_light(tmp_path / "sub" / "a.fits")
    fid = add_folder(conn, tmp_path)
    assert run(conn, fid)["new"] == 1
    (tmp_path / "sub").rename(tmp_path / ".sub")
    done = run(conn, fid)
    assert done["missing"] == 1
    assert [os.path.basename(d) for d in done["hidden_dirs"]] == [".sub"]


def test_scan_a_pose_left_online_only_is_not_missing(conn, tmp_path, monkeypatch):
    """Una posa gia' in archivio che l'utente lascia solo online non e' sparita: e' li', solo non
    sul disco. Non diventa "non trovata"."""
    write_light(tmp_path / "a.fits")
    fid = add_folder(conn, tmp_path)
    assert run(conn, fid)["new"] == 1
    online_only(monkeypatch, tmp_path / "a.fits")
    done = run(conn, fid)
    assert (done["missing"], done["online_only"]) == (0, 1)
    assert count(conn, "SELECT COUNT(*) FROM positions WHERE status = 'present'") == 1


def test_scan_names_the_hidden_folders_it_leaves_out(conn, tmp_path):
    """Una sottocartella nascosta resta fuori -- nel cestino ci sono le pose cancellate -- ma la
    ricevuta la nomina, come le illeggibili: chi ci tiene delle pose sa dove guardare."""
    write_light(tmp_path / "a.fits")
    write_light(tmp_path / ".nascosta però" / "b.fits", obj="M 2")
    done = run(conn, add_folder(conn, tmp_path))
    assert done["new"] == 1
    assert [os.path.basename(d) for d in done["hidden_dirs"]] == [".nascosta però"]
    # il nome si salva com'e', leggibile anche aprendo il database: accenti compresi
    salvato = conn.execute("SELECT hidden_dirs_json FROM scan_runs").fetchone()[0]
    assert ".nascosta però" in salvato


def test_scan_receipt(conn, tmp_path):
    for i in range(2):
        write_light(tmp_path / f"f{i}.fits", obj=f"M {i}")
    write_fits(tmp_path / "dark.fits", {"IMAGETYP": "Dark"})
    done = run(conn, add_folder(conn, tmp_path))
    row = conn.execute("SELECT * FROM scan_runs").fetchone()
    assert row["status"] == "ok" and row["ended_at"] is not None
    assert (row["found"], row["new"], row["skipped"]) == (3, 2, 1)
    assert done["run_id"] == row["id"]


def test_scan_stop_leaves_a_coherent_prefix(conn, tmp_path):
    """Fermare lascia un prefisso coerente, e la ricevuta della corsa fermata porta i file non
    letti fin li'."""
    (tmp_path / "0_rotto.fits").write_bytes(b"non e' un FITS\x00" * 50)
    settle(tmp_path / "0_rotto.fits")
    for i in range(5):
        write_light(tmp_path / f"f{i}.fits", obj=f"M {i}")
    gen = scan_folder(conn, add_folder(conn, tmp_path))
    for event in gen:
        if event.get("new") == 2:
            break
    gen.close()  # e' cio' che fa il worker su Stop
    assert count(conn, "SELECT COUNT(*) FROM frames") == 2
    row = conn.execute("SELECT status, new, errors_detail_json FROM scan_runs").fetchone()
    assert (row["status"], row["new"]) == ("stopped", 2)
    rotto = [{"file": "0_rotto.fits", "reason": "header_unreadable"}]
    assert json.loads(row["errors_detail_json"]) == rotto


def test_scan_writes_canonical_dates_and_the_pixel_fingerprint(conn, tmp_path):
    write_light(tmp_path / "a.fits", date="2024-05-17T21:00:00.123")
    run(conn, add_folder(conn, tmp_path))
    row = conn.execute("SELECT date_obs, frame_hash FROM frames").fetchone()
    assert row["date_obs"] == "2024-05-17T21:00:00.123"
    assert len(row["frame_hash"]) == 64


def test_scan_multi_hdu_counts_as_one_frame(conn, tmp_path):
    fits.HDUList(
        [
            fits.PrimaryHDU(),
            fits.ImageHDU(
                data=np.zeros((4, 4), dtype=np.int16),
                header=fits.Header({"OBJECT": "M 31", "EXPTIME": 300.0, "IMAGETYP": "LIGHT"}),
            ),
        ]
    ).writeto(tmp_path / "m.fits")
    settle(tmp_path / "m.fits")
    assert run(conn, add_folder(conn, tmp_path))["new"] == 1
