"""Cio' che la scansione lascia fuori, e perche': i file saltati li conta per motivo, le cartelle
lasciate fuori le nomina, e i nomi dei non letti li tiene l'ultima scansione. Le richieste
dell'utente in `docs/domini/spina-scan.md`; FITS veri fabbricati con astropy e un DB nato da
schema.sql."""

import json
import logging
import os

from astrolog.api import scan_door
from astrolog.pipeline import changes as changes_mod
from astrolog.pipeline import scan as pipeline_scan
from astrolog.pipeline import scanner
from astrolog.spine.scan_store import start_run
from conftest import add_folder, settle, write_fits, write_light
from test_scan_archive import count, run


def test_a_file_that_breaks_the_reading_is_named_and_the_scan_goes_on(conn, tmp_path, monkeypatch):
    """Un file che manda in errore la lettura per un motivo che nessuno aspettava non tiene fuori
    quelli che vengono dopo (Marco, 2026-09-11): si salta, la ricevuta lo nomina, e il nome resta
    scritto a corsa finita. Vale per l'header e per la scheda che se ne legge."""
    for i in range(3):
        write_light(tmp_path / f"f{i}.fits", obj=f"M {i}")
    vero_header, vera_scheda = scanner._extract, pipeline_scan.read_card

    def header_imprevisto(path, fh, size):
        if path.name == "f0.fits":
            raise KeyError("una card che nessuno si aspettava (mock)")
        return vero_header(path, fh, size)

    def scheda_imprevista(program, values):
        if values.get("OBJECT") == "M 1":
            raise TypeError("un valore che nessuno si aspettava (mock)")
        return vera_scheda(program, values)

    monkeypatch.setattr(scanner, "_extract", header_imprevisto)
    monkeypatch.setattr(pipeline_scan, "read_card", scheda_imprevista)
    done = run(conn, add_folder(conn, tmp_path))
    assert (done["status"], done["new"], done["errors"]) == ("ok", 1, 2)
    rotti = [
        {"file": "f0.fits", "reason": "internal_error"},
        {"file": "f1.fits", "reason": "internal_error"},
    ]
    assert sorted(done["errors_detail"], key=lambda e: e["file"]) == rotti
    salvato = json.loads(count(conn, "SELECT errors_detail_json FROM scan_runs"))
    assert sorted(salvato, key=lambda e: e["file"]) == rotti
    assert not conn.in_transaction


def test_a_name_the_archive_cannot_write_is_named_and_the_scan_goes_on(conn, tmp_path, monkeypatch):
    """Un nome che non e' UTF-8 -- una condivisione Linux scritta da un sistema vecchio -- non si
    puo' scrivere nell'archivio: si nomina, leggibile, e la corsa va avanti, anche quando e' una
    cartella lasciata fuori. Il nome si finge: su Windows una cartella cosi' non si crea."""
    write_light(tmp_path / "b.fits")
    root, vera = str(tmp_path), changes_mod.walk_dir

    def con_nomi_storti(cartella):
        visto = vera(cartella)
        visto.hidden.append(os.path.join(root, ".sub_\udce9"))
        visto.unreachable.append(os.path.join(root, "chiusa_\udce9"))
        return visto

    monkeypatch.setattr(changes_mod, "walk_dir", con_nomi_storti)
    done = run(conn, add_folder(conn, tmp_path))
    assert (done["status"], done["new"]) == ("ok", 1)
    assert (done["hidden_dirs"], done["unreadable_dirs"]) == ([".sub_?"], ["chiusa_?"])
    salvate = "SELECT hidden_dirs_json, unreadable_dirs_json FROM scan_runs"
    assert [json.loads(v) for v in conn.execute(salvate).fetchone()] == [[".sub_?"], ["chiusa_?"]]
    json.dumps(done, ensure_ascii=False).encode("utf-8")  # la pagina lo riceve in JSON


def test_a_pose_that_can_no_longer_be_read_is_not_missing(conn, tmp_path):
    """Un frame gia' in archivio il cui file non si legge piu' (rovinato) e' li': la ricevuta lo
    nomina fra i non letti, ma non diventa "non trovato" e il frame resta."""
    write_light(tmp_path / "a.fits")
    fid = add_folder(conn, tmp_path)
    assert run(conn, fid)["new"] == 1
    (tmp_path / "a.fits").write_bytes(b"non e' piu' un FITS\x00" * 50)
    settle(tmp_path / "a.fits", 300)
    done = run(conn, fid)
    assert (done["errors"], done["missing"]) == (1, 0)
    present = "SELECT COUNT(*) FROM pipeline_files WHERE state = 'present' AND frame_id IS NOT NULL"
    assert count(conn, present) == 1
    assert count(conn, "SELECT COUNT(*) FROM pipeline_frames") == 1


def test_the_same_unexpected_fault_leaves_one_trace_in_the_log(conn, tmp_path, monkeypatch, caplog):
    """Un guasto imprevisto uguale su mille file lascia nel log una traccia per tipo, a ogni corsa:
    mille tracce da 1,2 KB riempirebbero i 20 MB del log e ne spingerebbero fuori cio' che c'era
    prima. Nella ricevuta i file restano nominati uno per uno, e si rileggono la volta dopo."""
    for i in range(3):
        write_light(tmp_path / f"f{i}.fits", obj=f"M {i}")

    def header_imprevisto(path, _fh, _size):
        guasto = KeyError if path.name == "f1.fits" else AttributeError
        raise guasto("una card che nessuno si aspettava (mock)")

    monkeypatch.setattr(scanner, "_extract", header_imprevisto)
    caplog.set_level(logging.ERROR)
    fid = add_folder(conn, tmp_path)
    assert run(conn, fid)["errors"] == 3
    assert len([r for r in caplog.records if r.exc_info]) == 2  # due tipi, due tracce
    run(conn, fid)
    assert len([r for r in caplog.records if r.exc_info]) == 4  # e la corsa dopo le riscrive


def _stopped(conn, db_path, folder_id):
    """Una corsa fermata dall'utente al primo file: il rotto e' gia' contato."""
    corsa = start_run(conn, folder_id, "2026-11-27T10:00:00.000Z")
    eventi = scan_door.scan_events(conn, folder_id, corsa, scan_door.direct(db_path))
    next(eventi)
    eventi.close()


def test_only_the_last_scans_of_a_folder_keep_the_names(conn, db_path, tmp_path):
    """L'elenco dei file non letti lo tiene l'ultima scansione di una cartella, e se non e' arrivata
    in fondo anche l'ultima che ci e' arrivata (Marco, 2026-09-11): quei file si riprovano a ogni
    scansione arrivata in fondo. Le altre tengono i numeri, e il database non cresce a ogni giro
    di un NAS, nemmeno se la condivisione cade a ogni giro; le altre cartelle non si toccano."""
    for cartella in ("qui", "altrove", "mai"):
        (tmp_path / cartella).mkdir()
        (tmp_path / cartella / "0_rotto.fits").write_bytes(b"non e' un FITS\x00" * 50)
        settle(tmp_path / cartella / "0_rotto.fits")
        write_light(tmp_path / cartella / "posa.fits")
    qui, altrove = add_folder(conn, tmp_path / "qui"), add_folder(conn, tmp_path / "altrove")
    mai = add_folder(conn, tmp_path / "mai")  # la condivisione che cade a ogni giro

    run(conn, altrove)
    _stopped(conn, db_path, mai)
    run(conn, qui)
    run(conn, qui)
    for i in range(2):  # da leggere: la fermata cade a meta'
        write_light(tmp_path / "qui" / f"nuova{i}.fits", obj=f"M {i}")
    _stopped(conn, db_path, qui)
    _stopped(conn, db_path, mai)
    righe = conn.execute(
        "SELECT folder_id, status, errors_detail_json IS NOT NULL FROM scan_runs ORDER BY id"
    ).fetchall()
    assert [tuple(r) for r in righe] == [
        (altrove, "ok", 1),
        (mai, "stopped", 0),  # nessuna arrivata in fondo: resta solo l'ultima
        (qui, "ok", 0),
        (qui, "ok", 1),  # l'ultima arrivata in fondo
        (qui, "stopped", 1),
        (mai, "stopped", 1),  # l'ultima
    ]


def test_the_receipt_counts_the_skipped_by_reason(conn, tmp_path):
    """La ricevuta dice quanti file ha saltato e perche', calibrazioni comprese (Marco,
    2026-09-11): un NAS con l'orologio avanti, che fa saltare gli stessi frame a ogni scansione
    come "ancora in scrittura", si vede invece di sparire dentro un numero. Un file gia' letto
    che diventa uno di questi non e' "non trovato"."""
    write_light(tmp_path / "light.fits")
    write_light(tmp_path / "era_luce.fits", obj="M 3")
    write_light(tmp_path / "era_vecchio.fits", obj="M 4")
    fid = add_folder(conn, tmp_path)
    run(conn, fid)
    write_fits(tmp_path / "dark.fits", {"IMAGETYP": "DARK", "EXPTIME": 1.0})
    write_fits(tmp_path / "era_luce.fits", {"IMAGETYP": "BIAS", "EXPTIME": 1.0}, age_s=300)
    # integrato altrove: fuori come elaborato da un altro programma (ADR 0029, Marco 26/11/2026)
    write_fits(tmp_path / "master.fits", {"IMAGETYP": "LIGHT", "STACKCNT": 40, "OBJECT": "M 1"})
    settle(write_light(tmp_path / "era_vecchio.fits", obj="M 5"), 0)
    done = run(conn, fid, min_age_s=30)
    atteso = {"calibration": 2, "rewritten": 1, "still_writing": 1}
    assert {e["reason"]: e["count"] for e in done["skipped_by_reason"]} == atteso
    assert done["missing"] == 0
    salvato = json.loads(
        count(conn, "SELECT skipped_by_reason_json FROM scan_runs ORDER BY id DESC")
    )
    assert {e["reason"]: e["count"] for e in salvato} == atteso


def test_a_left_out_folder_is_named_from_the_root_down(conn, tmp_path):
    """Una cartella lasciata fuori si nomina **dalla radice in giu'**, come un file non letto: il
    percorso intero e' quello della riga che sta sopra, e ripeterlo su ogni voce copre l'unica
    parola che distingue una cartella dall'altra."""
    write_light(tmp_path / "sotto" / "buona.fits")
    nascosta = tmp_path / "sotto" / ".cestino"
    nascosta.mkdir(parents=True)
    write_light(nascosta / "buttata.fits", obj="M 2")
    done = run(conn, add_folder(conn, tmp_path))
    assert done["hidden_dirs"] == ["sotto/.cestino"]
    assert json.loads(count(conn, "SELECT hidden_dirs_json FROM scan_runs")) == ["sotto/.cestino"]
