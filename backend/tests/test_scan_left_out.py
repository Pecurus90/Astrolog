"""Cio' che la scansione lascia fuori, e perche': i file saltati li conta per motivo, le cartelle
lasciate fuori le nomina, e i nomi dei non letti li tiene l'ultima scansione. Le richieste
dell'utente in `docs/domini/spina-scan.md`; FITS veri fabbricati con astropy e un DB nato da
schema.sql."""

import json

from astrolog.api import scan_door
from astrolog.spine.scan_store import start_run
from conftest import add_folder, settle, write_fits, write_light
from test_scan_archive import count, run


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
