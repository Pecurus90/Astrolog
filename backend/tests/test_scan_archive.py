"""La scansione vista dall'archivio: le richieste dell'utente in `docs/domini/spina-scan.md`, una
per test, sulla porta della pipeline nuova (`api/scan_door.py`). FITS veri fabbricati con astropy,
DB nato da schema.sql. I test della vecchia scansione tolti: `tools/test_tolti.txt`."""

import os
from pathlib import Path

import pytest

import astrolog.pipeline.changes as changes_mod
import astrolog.pipeline.scan as pipeline_scan
import astrolog.pipeline.walk as walk_mod
from astrolog.api import scan_door
from astrolog.api.scan_door import scan_once
from astrolog.pipeline.scanner import Skip, Skipped
from astrolog.pipeline.walk import long_path
from astrolog.spine import frame_folder, typeless
from astrolog.spine.declarations import TypeAnswer
from astrolog.spine.stages import STAGES, WAITING_SQL, count_pending
from conftest import (
    add_folder,
    online_only,
    settle,
    unreadable_dir,
    write_fits,
    write_light,
)


def run(conn, folder_id, **kw):
    done = scan_once(conn, folder_id, **kw)
    assert done["done"]
    return done


def count(conn, sql):
    return conn.execute(sql).fetchone()[0]


# i file dei frame dell'archivio: la nuova tiene anche saltati e calibrazioni
FILES = (
    "SELECT COUNT(DISTINCT rel_path) FROM pipeline_files WHERE frame_id IN (SELECT id FROM frames)"
)
PRESENT = (
    "SELECT COUNT(*) FROM pipeline_files WHERE state = 'present'"
    " AND frame_id IN (SELECT id FROM frames)"
)
STATE = (
    "SELECT state FROM pipeline_files WHERE frame_id IN (SELECT id FROM frames) ORDER BY id DESC"
)


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
    assert count(conn, FILES) == 4


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
    assert count(conn, PRESENT) == 3


def test_scan_duplicate_header(conn, tmp_path):
    a = write_light(tmp_path / "a" / "x.fits", obj="M 51")
    os.makedirs(tmp_path / "b")
    with open(a, "rb") as src, open(tmp_path / "b" / "copia.fits", "wb") as dst:
        dst.write(src.read())
    settle(tmp_path / "b" / "copia.fits")
    done = run(conn, add_folder(conn, tmp_path))
    assert (done["new"], done["duplicates"]) == (1, 1)
    assert count(conn, "SELECT COUNT(*) FROM frames") == 1
    assert count(conn, FILES) == 2


def test_scan_missing_returns(conn, tmp_path):
    p = write_light(tmp_path / "a.fits")
    fid = add_folder(conn, tmp_path)
    run(conn, fid)
    with open(p, "rb") as f:
        data = f.read()
    os.remove(p)
    assert run(conn, fid)["missing"] == 1
    assert count(conn, "SELECT COUNT(*) FROM frames") == 1  # mai cancellato
    assert conn.execute(STATE).fetchone()[0] == "gone"
    with open(p, "wb") as f:
        f.write(data)
    settle(p)
    run(conn, fid)
    assert conn.execute(STATE).fetchone()[0] == "present"


def test_scan_skips_calibration(conn, tmp_path):
    """Nessun file di calibrazione entra in archivio, nelle parole di N.I.N.A. (DARKFLAT
    compreso), e nemmeno il file gia' sommato da un altro programma (ADR 0029)."""
    write_light(tmp_path / "light.fits")
    for name, typ in (("dark", "DARK"), ("flat", "FLAT"), ("bias", "BIAS"), ("df", "DARKFLAT")):
        write_fits(tmp_path / f"{name}.fits", {"IMAGETYP": typ, "EXPTIME": 1.0})
    write_fits(tmp_path / "master.fits", {"IMAGETYP": "LIGHT", "STACKCNT": 40, "OBJECT": "M 1"})
    done = run(conn, add_folder(conn, tmp_path))
    assert (done["found"], done["new"], done["skipped"]) == (6, 1, 5)
    assert count(conn, "SELECT COUNT(*) FROM frames") == 1
    assert count(conn, FILES) == 1


def _muto(tmp_path, name="muto.fits"):
    """Un file che non dice `IMAGETYP`: lo lasciano muto alcuni programmi di ripresa, e non si sa
    se e' una foto del cielo o un file di calibrazione (`pipeline/card.py`)."""
    write_fits(
        tmp_path / name,
        {"OBJECT": "M 13", "EXPTIME": 60.0, "DATE-OBS": "2024-05-17T21:00:00"},
    )


def _aspetta(conn):
    """Se qualcuno di questi frame aspetta di sapere che file e': il segno scritto sul frame, lo
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
    non entrano affatto e la ricevuta li conta per motivo, come quelli che lo dicono da soli; un
    light che dice di esserlo entra. Un frame gia' in archivio spostato li' invece entra
    (`test_review_typeless.py`). Cambiata la risposta, il file entra alla scansione dopo."""
    folder_id = add_folder(conn, tmp_path)
    chiave = frame_folder.folder_key(str(tmp_path))
    typeless.declare(conn, chiave, TypeAnswer.CALIBRATION)
    _muto(tmp_path, "dark.fits")
    write_light(tmp_path / "luce.fits")
    done = run(conn, folder_id)
    assert (done["new"], done["skipped"]) == (1, 1)
    assert done["skipped_by_reason"] == [{"reason": "calibration", "count": 1}]
    assert count(conn, "SELECT COUNT(*) FROM frames") == 1
    typeless.declare(conn, chiave, TypeAnswer.LIGHT)
    done = run(conn, folder_id)
    assert (done["new"], done["skipped"]) == (1, 0)


def _gone_and_back(conn, tmp_path):
    """Un file portato via e rimesso uguale, stessa data; torna la ricevuta del ritorno."""
    p = write_light(tmp_path / "a.fits")
    fid = add_folder(conn, tmp_path)
    run(conn, fid)
    fuori = tmp_path.parent / f"{tmp_path.name}-fuori.fits"
    os.rename(p, fuori)
    assert run(conn, fid)["missing"] == 1
    os.rename(fuori, p)
    return run(conn, fid)


def test_scan_a_pose_said_missing_found_unchanged_is_present_again(conn, tmp_path):
    """Una posa segnata "non trovata" che la scansione ritrova uguale torna presente."""
    _gone_and_back(conn, tmp_path)
    assert conn.execute(STATE).fetchone()[0] == "present"


@pytest.mark.xfail(strict=True, reason="issue 110: the receipt counts it nowhere")
def test_scan_a_pose_found_unchanged_is_counted_unchanged(conn, tmp_path):
    """Il ritorno uguale e' un file invariato nella ricevuta, come per la vecchia scansione."""
    assert _gone_and_back(conn, tmp_path)["unchanged"] == 1


def test_scan_touched_headers_and_late_copies_are_counted_one_by_one(conn, tmp_path):
    """Due file toccati sul disco con gli stessi pixel restano i loro frame; due copie arrivate
    dopo di un frame gia' in archivio sono due doppioni."""
    a = write_light(tmp_path / "a.fits", obj="M 1")
    b = write_light(tmp_path / "b.fits", obj="M 2")
    fid = add_folder(conn, tmp_path)
    run(conn, fid)
    for p in (a, b):
        settle(p, 300)  # same bytes, another date: read again, same pixels
    for copia in ("c.fits", "d.fits"):
        (tmp_path / copia).write_bytes(Path(a).read_bytes())
        settle(tmp_path / copia)
    done = run(conn, fid)
    assert (done["new"], done["duplicates"]) == (0, 2)
    assert count(conn, "SELECT COUNT(*) FROM frames") == 2


def test_scan_lets_in_a_folder_the_user_called_sky(conn, tmp_path):
    """Detto che in quella cartella ci sono foto del cielo, i file che arrivano dopo fanno la
    strada di un light da subito: la risposta vale anche per loro, senza ri-chiedere."""
    folder_id = add_folder(conn, tmp_path)
    typeless.declare(conn, frame_folder.folder_key(str(tmp_path)), TypeAnswer.LIGHT)
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


def test_the_wait_the_door_passes_is_at_least_30_seconds():
    """I 30 secondi sono quelli che passa la porta dell'utente (`scan_door.scan_events`); ogni
    altro test li passa a mano: portarli a zero farebbe entrare i file che la camera scrive."""
    assert scan_door.MIN_AGE_S >= 30


def test_scan_beyond_260_characters_reads_the_header(conn, tmp_path):
    """Il tratto lungo della scansione (stat e lettura sulla forma `\\\\?\\`), non solo il walk."""
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
    chiuso = write_light(tmp_path / "chiuso.fits", obj="M 2")
    (tmp_path / "rotto.fits").write_bytes(b"non e' un FITS\x00" * 50)
    settle(tmp_path / "rotto.fits")
    vera = pipeline_scan.scan_file

    def senza_permesso(p, size):
        return Skipped(p, Skip.UNREADABLE) if Path(p) == Path(chiuso) else vera(p, size)

    monkeypatch.setattr(pipeline_scan, "scan_file", senza_permesso)
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
    assert conn.execute(STATE).fetchone()[0] == "present"  # intatta
    assert conn.execute("SELECT status, reason FROM scan_runs ORDER BY id DESC").fetchone()[:] == (
        "aborted",
        "root_unreachable",
    )


def test_scan_root_gone_midway_aborts_without_marking_missing(conn, tmp_path, monkeypatch):
    """La cartella di rete cade mentre si leggono i file: ferma, lo dice, nessun 'non trovato'."""
    root = tmp_path / "nas"
    write_light(root / "a.fits")
    fid = add_folder(conn, root)
    run(conn, fid)
    for i in range(3):
        write_light(root / f"n{i}.fits", obj="M 2", date=f"2024-05-17T22:0{i}:00")
    letti, vera = [], pipeline_scan.scan_file

    def cade(p, size):
        if not letti:
            os.rename(root, tmp_path / "staccata")  # il NAS non risponde piu'
        letti.append(p)
        return vera(p, size)

    monkeypatch.setattr(pipeline_scan, "scan_file", cade)
    done = run(conn, fid)
    assert (done["status"], done["reason"], done["missing"]) == ("aborted", "root_unreachable", 0)
    assert len(letti) == 1  # fermata al primo file che il NAS non da' piu'
    assert count(conn, PRESENT) == 1


def test_scan_root_gone_before_the_files_are_looked_at_aborts(conn, tmp_path, monkeypatch):
    """Cade fra l'elenco e lo stat dei file: tutti 'non guardati', e la scansione lo dice ferma."""
    root = tmp_path / "nas"
    write_light(root / "a.fits")
    write_light(root / "b.fits", obj="M 2")
    fid = add_folder(conn, root)
    run(conn, fid)
    vera = changes_mod.walk_dir

    def elenca_e_cade(where):
        walk = vera(where)
        os.rename(root, tmp_path / "staccata")
        return walk

    monkeypatch.setattr(changes_mod, "walk_dir", elenca_e_cade)
    done = run(conn, fid)
    assert (done["status"], done["reason"], done["missing"]) == ("aborted", "root_unreachable", 0)
    assert count(conn, PRESENT) == 2


def test_scan_unreadable_subfolder_does_not_mark_its_frames_missing(conn, tmp_path, monkeypatch):
    sub = tmp_path / "chiusa"
    write_light(tmp_path / "a.fits")
    write_light(sub / "b.fits", obj="M 2")
    fid = add_folder(conn, tmp_path)
    assert run(conn, fid)["new"] == 2
    unreadable_dir(monkeypatch, walk_mod, sub)
    done = run(conn, fid)
    assert done["missing"] == 0 and len(done["unreadable_dirs"]) == 1
    assert count(conn, PRESENT) == 2


@pytest.mark.skipif(os.name != "nt", reason="Win32 strips a trailing dot: Windows only")
def test_scan_reads_a_folder_ending_with_a_dot_as_itself(conn, tmp_path):
    """'notte.' fatta da Mac o Linux su NTFS: prima letta come 'notte', i suoi frame persi."""
    dotted = "\\\\?\\" + str(tmp_path / "notte.")
    os.makedirs(dotted)
    write_light(Path(dotted) / "a.fits")
    write_light(tmp_path / "notte" / "b.fits", obj="M 2")
    done = run(conn, add_folder(conn, tmp_path))
    assert done["new"] == 2 and done["errors"] == 0


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
    aperti, vera = [], pipeline_scan.scan_file
    # un contesto suo: `monkeypatch.undo()` toglierebbe anche il recinto di tutta la suite
    with monkeypatch.context() as finto:
        online_only(finto, tmp_path / "b.fits")
        finto.setattr(pipeline_scan, "scan_file", lambda p, s: aperti.append(p) or vera(p, s))
        done = run(conn, fid)
    assert (done["new"], done["online_only"]) == (1, 1)
    assert done["found"] == 2  # incontrati tutti e due: uno letto, uno lasciato dov'e'
    assert not any(os.path.basename(p) == "b.fits" for p in aperti)
    assert count(conn, "SELECT online_only FROM scan_runs") == 1
    assert run(conn, fid)["new"] == 1  # di nuovo sul disco: entra


def test_scan_poses_under_a_folder_that_becomes_hidden_are_missing(conn, tmp_path):
    """Una cartella che diventa nascosta -- e' il caso del cestino -- esce dall'archivio: i suoi
    frame diventano "non trovati", e la ricevuta dice quale cartella ha lasciato fuori."""
    write_light(tmp_path / "sub" / "a.fits")
    fid = add_folder(conn, tmp_path)
    assert run(conn, fid)["new"] == 1
    (tmp_path / "sub").rename(tmp_path / ".sub")
    done = run(conn, fid)
    assert done["missing"] == 1
    assert [os.path.basename(d) for d in done["hidden_dirs"]] == [".sub"]


def test_scan_a_pose_left_online_only_is_not_missing(conn, tmp_path, monkeypatch):
    """Un frame gia' in archivio che l'utente lascia solo online non e' sparito: e' li', solo non
    sul disco. Non diventa "non trovata"."""
    write_light(tmp_path / "a.fits")
    fid = add_folder(conn, tmp_path)
    assert run(conn, fid)["new"] == 1
    online_only(monkeypatch, tmp_path / "a.fits")
    done = run(conn, fid)
    assert (done["missing"], done["online_only"]) == (0, 1)
    assert count(conn, PRESENT) == 1


def test_scan_names_the_hidden_folders_it_leaves_out(conn, tmp_path):
    """Una sottocartella nascosta resta fuori -- nel cestino ci sono i frame cancellati -- ma la
    ricevuta la nomina, come le illeggibili: chi ci tiene dei frame sa dove guardare."""
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
    write_fits(tmp_path / "dark.fits", {"IMAGETYP": "DARK"})
    done = run(conn, add_folder(conn, tmp_path))
    row = conn.execute("SELECT * FROM scan_runs").fetchone()
    assert row["status"] == "ok" and row["ended_at"] is not None
    assert (row["found"], row["new"], row["skipped"]) == (3, 2, 1)
    assert done["run_id"] == row["id"]


def test_scan_writes_canonical_dates_and_the_pixel_fingerprint(conn, tmp_path):
    write_light(tmp_path / "a.fits", date="2024-05-17T21:00:00.123")
    run(conn, add_folder(conn, tmp_path))
    row = conn.execute("SELECT date_obs, frame_hash FROM frames").fetchone()
    assert row["date_obs"] == "2024-05-17T21:00:00.123"
    assert len(row["frame_hash"]) == 64
