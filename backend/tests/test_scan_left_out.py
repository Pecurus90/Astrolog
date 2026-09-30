"""Cio' che la scansione lascia fuori, e perche': un file che non legge lo nomina col suo codice e
va avanti, i file saltati li conta per motivo. Le richieste dell'utente in
`docs/domini/spina.md`; FITS veri fabbricati con astropy e un DB nato da schema.sql."""

import json
import os
import sqlite3

import pytest

import astrolog.spine.scan as scan_mod
from astrolog.spine.scan import scan_folder
from conftest import add_folder, online_only, settle, write_fits, write_light
from test_spine_scan import count, run


def test_a_file_that_breaks_the_reading_is_named_and_the_scan_goes_on(conn, tmp_path, monkeypatch):
    """Un file che manda in errore la lettura per un motivo che nessuno aspettava non tiene fuori
    quelli che vengono dopo (Marco, 2026-09-11): si salta, anche quando e' solo online, la
    ricevuta lo nomina, l'evento dice quale file era, e il nome resta scritto a corsa finita."""
    for i in range(3):
        write_light(tmp_path / f"f{i}.fits", obj=f"M {i}")
    online_only(monkeypatch, tmp_path / "f2.fits")
    vera = scan_mod.extract_fields

    def card_imprevista(header, path):
        if os.path.basename(path) == "f0.fits":
            raise ValueError("una card che nessuno si aspettava (mock)")
        return vera(header, path)

    def guasto(*_args):
        raise ValueError("un guasto che nessuno aspettava (mock)")

    monkeypatch.setattr(scan_mod, "extract_fields", card_imprevista)
    monkeypatch.setattr(scan_mod, "_not_on_disk", guasto)
    events = list(scan_folder(conn, add_folder(conn, tmp_path)))
    done = events[-1]
    assert (done["status"], done["new"], done["errors"]) == ("ok", 1, 2)
    atteso = [
        {"file": "f2.fits", "reason": "internal_error"},
        {"file": "f0.fits", "reason": "internal_error"},
    ]
    assert done["errors_detail"] == atteso
    assert (events[0]["file"], events[0]["errors"]) == ("f0.fits", 2)
    assert json.loads(count(conn, "SELECT errors_detail_json FROM scan_runs")) == atteso


def test_a_name_the_archive_cannot_write_is_named_and_the_scan_goes_on(conn, tmp_path, monkeypatch):
    """Un nome che non e' UTF-8 -- una condivisione Linux scritta da un sistema vecchio -- non si
    puo' scrivere nell'archivio: si nomina, leggibile, e la corsa va avanti, anche quando il file
    e' solo online o e' una cartella lasciata fuori. Il nome si finge: su Windows un file cosi'
    non si crea."""
    write_light(tmp_path / "b.fits")
    root, vero = str(tmp_path), scan_mod.walk_dir

    def con_nomi_storti(cartella, **accumulatori):
        trovati = vero(cartella, **accumulatori)
        accumulatori["online_only"].append(os.path.join(root, "nuvola_\udce9.fits"))
        accumulatori["hidden"].append(os.path.join(root, ".sub_\udce9"))
        accumulatori["unreadable"].append(os.path.join(root, "chiusa_\udce9"))
        accumulatori["linked"].append(os.path.join(root, "link_\udce9"))
        return [os.path.join(root, "M31_\udce9.fits"), *trovati]

    monkeypatch.setattr(scan_mod, "walk_dir", con_nomi_storti)
    events = list(scan_folder(conn, add_folder(conn, tmp_path)))
    done = events[-1]
    assert (done["status"], done["new"], done["errors"]) == ("ok", 1, 2)
    atteso = [
        {"file": "nuvola_?.fits", "reason": "name_not_utf8"},
        {"file": "M31_?.fits", "reason": "name_not_utf8"},
    ]
    assert done["errors_detail"] == atteso
    assert json.loads(count(conn, "SELECT errors_detail_json FROM scan_runs")) == atteso
    lasciate = [
        os.path.basename(done[k][0]) for k in ("hidden_dirs", "unreadable_dirs", "linked_dirs")
    ]
    assert lasciate == [".sub_?", "chiusa_?", "link_?"]
    for event in events:  # la pagina li riceve in JSON: ogni nome deve potersi scrivere
        json.dumps(event, ensure_ascii=False).encode("utf-8")


def test_a_pose_that_can_no_longer_be_read_is_not_missing(conn, tmp_path):
    """Una posa gia' in archivio il cui file non si legge piu' (rovinato, o bloccato da un altro
    programma) e' li': la ricevuta la nomina fra i non letti, ma non diventa "non trovata"."""
    write_light(tmp_path / "a.fits")
    fid = add_folder(conn, tmp_path)
    assert run(conn, fid)["new"] == 1
    (tmp_path / "a.fits").write_bytes(b"non e' piu' un FITS\x00" * 50)
    settle(tmp_path / "a.fits", 300)
    done = run(conn, fid)
    assert (done["errors"], done["missing"]) == (1, 0)
    assert count(conn, "SELECT COUNT(*) FROM positions WHERE status = 'present'") == 1


def test_a_database_fault_stops_the_scan_and_the_receipt_says_so(conn, tmp_path, monkeypatch):
    """Il database che non risponde (disco pieno, occupato da un altro programma) non e' un file
    che non si legge: la corsa si ferma col suo motivo, invece di dire "3.000 file non letti" di
    file sani. E la ricevuta si chiude comunque, anche a transazione aperta, coi file non letti
    fin li' -- quando il database risponde per scriverla."""
    (tmp_path / "0_rotto.fits").write_bytes(b"non e' un FITS\x00" * 50)
    settle(tmp_path / "0_rotto.fits")
    for i in range(2):
        write_light(tmp_path / f"f{i}.fits", obj=f"M {i}")
    fid = add_folder(conn, tmp_path)
    rotto = [{"file": "0_rotto.fits", "reason": "header_unreadable"}]
    ultima = (
        "SELECT status, reason, new, ended_at, errors_detail_json FROM scan_runs ORDER BY id DESC"
    )

    def pieno(*_args):
        raise sqlite3.OperationalError("database or disk is full (mock)")

    def pieno_a_meta(db, *_args):
        db.execute("BEGIN")
        raise sqlite3.OperationalError("database or disk is full (mock)")

    # su un file: la corsa si ferma li', non conta il guasto come un file non letto
    with monkeypatch.context() as finto, pytest.raises(sqlite3.OperationalError):
        finto.setattr(scan_mod.store, "insert_frame", pieno)
        list(scan_folder(conn, fid))
    riga = conn.execute(ultima).fetchone()
    assert (riga["status"], riga["reason"], riga["new"]) == ("error", "database_error", 0)
    assert json.loads(riga["errors_detail_json"]) == rotto
    # a fine corsa, con la transazione aperta: la ricevuta si chiude lo stesso
    with monkeypatch.context() as finto, pytest.raises(sqlite3.OperationalError):
        finto.setattr(scan_mod.store, "mark_missing", pieno_a_meta)
        list(scan_folder(conn, fid))
    riga = conn.execute(ultima).fetchone()
    assert (riga["status"], riga["reason"], riga["new"]) == ("error", "database_error", 2)
    assert riga["ended_at"] is not None and json.loads(riga["errors_detail_json"]) == rotto
    assert not conn.in_transaction


def test_the_same_unexpected_fault_leaves_one_trace_in_the_log(conn, tmp_path, monkeypatch, caplog):
    """Un guasto imprevisto uguale su mille file lascia nel log una traccia per tipo, a ogni corsa:
    mille tracce da 1,2 KB riempirebbero i 20 MB del log e ne spingerebbero fuori cio' che c'era
    prima. Nella ricevuta i file restano nominati uno per uno."""
    for i in range(3):
        write_light(tmp_path / f"f{i}.fits", obj=f"M {i}")

    def card_imprevista(_header, path):
        guasto = KeyError if os.path.basename(path) == "f1.fits" else ValueError
        raise guasto("una card che nessuno si aspettava (mock)")

    monkeypatch.setattr(scan_mod, "extract_fields", card_imprevista)
    fid = add_folder(conn, tmp_path)
    assert run(conn, fid)["errors"] == 3
    assert len([r for r in caplog.records if r.exc_info]) == 2  # due tipi, due tracce
    run(conn, fid)
    assert len([r for r in caplog.records if r.exc_info]) == 4  # e la corsa dopo le riscrive


def test_only_the_last_scans_of_a_folder_keep_the_names(conn, tmp_path, monkeypatch):
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

    def pieno(*_args):
        raise sqlite3.OperationalError("database or disk is full (mock)")

    def ferma(cartella):
        corsa = scan_folder(conn, cartella)
        next(corsa)  # il file rotto e' gia' contato quando arriva lo Stop
        corsa.close()

    run(conn, altrove)
    ferma(mai)
    run(conn, qui)
    run(conn, qui)
    ferma(qui)
    ferma(mai)
    with monkeypatch.context() as finto, pytest.raises(sqlite3.OperationalError):
        finto.setattr(scan_mod.store, "mark_missing", pieno)
        list(scan_folder(conn, qui))
    righe = conn.execute(
        "SELECT folder_id, status, errors_detail_json IS NOT NULL FROM scan_runs ORDER BY id"
    ).fetchall()
    assert [tuple(r) for r in righe] == [
        (altrove, "ok", 1),
        (mai, "stopped", 0),  # nessuna arrivata in fondo: resta solo l'ultima
        (qui, "ok", 0),
        (qui, "ok", 1),  # l'ultima arrivata in fondo
        (qui, "stopped", 0),
        (mai, "stopped", 1),
        (qui, "error", 1),  # l'ultima
    ]


def test_the_receipt_counts_the_skipped_by_reason(conn, tmp_path):
    """La ricevuta dice quanti file ha saltato e perche', calibrazioni comprese (Marco,
    2026-09-11): un NAS con l'orologio avanti, che fa saltare le stesse pose a ogni scansione
    come "ancora in scrittura", si vede invece di sparire dentro un numero."""
    write_light(tmp_path / "light.fits")
    write_fits(tmp_path / "dark.fits", {"IMAGETYP": "Dark", "EXPTIME": 1.0})
    write_fits(tmp_path / "bias.fits", {"IMAGETYP": "Bias Frame", "EXPTIME": 1.0})
    write_fits(tmp_path / "master.fits", {"IMAGETYP": "Light", "NCOMBINE": 40, "OBJECT": "M 1"})
    settle(write_light(tmp_path / "fresco.fits", obj="M 2"), 0)
    done = run(conn, add_folder(conn, tmp_path), min_age_s=30)
    atteso = {"calibration": 2, "stack": 1, "still_writing": 1}
    assert {e["reason"]: e["count"] for e in done["skipped_by_reason"]} == atteso
    salvato = json.loads(count(conn, "SELECT skipped_by_reason_json FROM scan_runs"))
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
