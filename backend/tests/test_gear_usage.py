"""Quanto e' servito ogni pezzo lo scrive chi lavora le pose, e l'Attrezzatura lo legge e basta.

Marco, 22/9/2026: una lettura non calcola mai. I conti si fanno a fine giro di ogni stadio che
cambia le pose (`spine/gear_usage.py`) e si scrivono in `gear_usage`; la pagina li legge
(`spine/inventory.py`). I numeri stessi -- copie, pose senza tempo, montatura -- hanno le loro
prove in `test_api_gear.py`.
"""

import re
import sqlite3

import pytest

from astrolog.spine import (
    gear_usage,
    group,
    identify,
    normalize,
    solve,
    stages,
    typeless,
    typeless_answer,
    typeless_folders,
)
from astrolog.spine.group import group_frames
from astrolog.spine.identify import identify_frames
from astrolog.spine.solve import solve_frames
from conftest import add_folder, by_name, db, gear, run_normalize
from test_solve import solver
from test_typeless import _frame

CAMERA = "ATR2600M(USB2.0)"


def _pose(client):
    return by_name(gear(client)["instruments"], CAMERA)["frames"]


def test_the_page_reads_what_was_written_not_the_frames(client):
    """Una posa che cambia senza che nessuno stadio giri non sposta la pagina: la pagina non conta.
    Riscritto l'uso, come a fine giro, la pagina lo dice."""
    prima = _pose(client)
    with db(client) as conn:
        conn.execute(
            "UPDATE frames SET copy_of = (SELECT MIN(id) FROM frames) WHERE id = ("
            " SELECT f.id FROM frames f JOIN rigs g ON g.id = f.rig_id"
            " JOIN instruments c ON c.id = g.camera_id WHERE c.name = ?"
            " ORDER BY f.id DESC LIMIT 1)",
            (CAMERA,),
        )
    assert _pose(client) == prima
    with db(client) as conn:
        gear_usage.write(conn)
    assert _pose(client) == prima - 1


def _normalize(conn, pose, tmp_path):
    stages.invalidate(conn, pose, "normalize")
    run_normalize(conn)


def _solve(conn, pose, tmp_path):
    stages.invalidate(conn, pose, "solve")
    list(solve_frames(conn, exe="astap", run=solver({}), cache=tmp_path / "cache"))


def _identify(conn, pose, tmp_path):
    stages.invalidate(conn, pose, "identify")
    list(identify_frames(conn))


def _group(conn, pose, tmp_path):
    stages.invalidate(conn, pose, "group")
    list(group_frames(conn))


@pytest.mark.parametrize("stadio", [_normalize, _solve, _identify, _group])
def test_every_stage_that_moves_poses_writes_the_usage_at_the_end(client, tmp_path, stadio):
    """Corredo e filtro (normalize), cielo (solve), oggetto (identify), notte (group): ognuno
    cambia un numero della pagina, e ognuno lo riscrive a fine giro."""
    with db(client) as conn:
        pose = [r[0] for r in conn.execute("SELECT id FROM frames")]
        conn.execute("DELETE FROM gear_usage")
        stadio(conn, pose, tmp_path)
        scritte = conn.execute("SELECT COUNT(*) FROM gear_usage").fetchone()[0]
    assert scritte > 0


def test_a_piece_not_yet_counted_says_so_and_not_that_the_files_are_silent(client):
    """Un pezzo nato a meta' di un giro -- alla prima scansione, per minuti -- non ha ancora la sua
    riga: la pagina dice che non e' ancora contato. "L'app non puo' saperlo" e' un'altra cosa, ed
    e' una riga scritta coi conteggi vuoti, come per un riduttore che nessuna posa porta."""
    with db(client) as conn:
        conn.execute(
            "INSERT INTO instruments(kind, name, created_at) VALUES('camera', 'Appena nata', 'ora')"
        )
        conn.execute("INSERT INTO rigs(focal_mm, created_at) VALUES(333.0, 'ora')")
    pagina = gear(client)
    nata = by_name(pagina["instruments"], "Appena nata")
    assert (nata["counted"], nata["frames"]) == (False, None)
    corredo = next(r for r in pagina["rigs"] if r["focal_mm"] == 333.0)
    assert (corredo["counted"], corredo["frames"]) == (False, None)
    scritto = client.post("/api/v1/gear/instruments", json={"kind": "reducer", "name": "0.8x"})
    assert scritto.status_code == 201, scritto.text
    riduttore = by_name(gear(client)["instruments"], "0.8x")
    assert (riduttore["counted"], riduttore["frames"]) == (True, None)


def test_the_rewrite_is_all_or_nothing(client, monkeypatch):
    """Chi apre la pagina a meta' riscrittura non vede la tabella vuota, e una riscrittura che cade
    lascia quella di prima invece che mezza."""
    with db(client) as conn:
        prima = conn.execute("SELECT COUNT(*) FROM gear_usage").fetchone()[0]
        assert prima > 0
        storta = [{**r, "subject": "x"} for r in gear_usage._filtri(conn)][:1]
        monkeypatch.setattr(gear_usage, "_filtri", lambda conn: storta)
        with pytest.raises(sqlite3.IntegrityError):
            gear_usage.write(conn)
        assert conn.execute("SELECT COUNT(*) FROM gear_usage").fetchone()[0] == prima


_STADI = {
    "normalize": lambda conn, tmp: normalize.normalize_frames(conn),
    "solve": lambda conn, tmp: solve.solve_frames(
        conn, exe="astap", run=solver({}), cache=tmp / "cache"
    ),
    "identify": lambda conn, tmp: identify.identify_frames(conn),
    "group": lambda conn, tmp: group.group_frames(conn),
}


@pytest.mark.parametrize("nome", list(_STADI))
def test_a_stopped_round_writes_what_it_did(client, tmp_path, nome):
    """Una corsa fermata a meta' ha gia' spostato delle pose: l'uso si riscrive anche li'."""
    with db(client) as conn:
        pose = [r[0] for r in conn.execute("SELECT id FROM frames")]
        stages.invalidate(conn, pose, nome)
        conn.execute("DELETE FROM gear_usage")
        corsa = _STADI[nome](conn, tmp_path)
        next(corsa)
        corsa.close()
        assert conn.execute("SELECT COUNT(*) FROM gear_usage").fetchone()[0] > 0


@pytest.mark.parametrize("nome", list(_STADI))
def test_a_round_that_breaks_writes_what_it_did(client, tmp_path, monkeypatch, nome):
    """E una corsa che si rompe dopo aver lavorato qualche posa, lo stesso."""
    modulo = {"normalize": normalize, "solve": solve, "identify": identify, "group": group}[nome]
    vero = modulo.frame_safely
    chiamate = []

    def una_e_poi_rotto(*args, **kwargs):
        chiamate.append(1)
        if len(chiamate) > 1:
            raise RuntimeError("guasto finto")
        return vero(*args, **kwargs)

    monkeypatch.setattr(modulo, "frame_safely", una_e_poi_rotto)
    with db(client) as conn:
        pose = [r[0] for r in conn.execute("SELECT id FROM frames")]
        stages.invalidate(conn, pose, nome)
        conn.execute("DELETE FROM gear_usage")
        with pytest.raises(RuntimeError):
            list(_STADI[nome](conn, tmp_path))
        assert conn.execute("SELECT COUNT(*) FROM gear_usage").fetchone()[0] > 0


@pytest.mark.parametrize("nome", list(_STADI))
def test_a_stage_with_nothing_to_do_does_not_count_again(client, tmp_path, monkeypatch, nome):
    """Contare tutto costa, su un archivio grande: uno stadio che non ha lavorato nessuna posa non
    ha spostato niente, e non riconta."""
    chiamate = []
    monkeypatch.setattr(gear_usage, "write", lambda conn: chiamate.append(1))
    with db(client) as conn:
        list(_STADI[nome](conn, tmp_path))  # svuota cio' che il banco aveva lasciato in coda
        chiamate.clear()
        list(_STADI[nome](conn, tmp_path))
        assert chiamate == []
        pose = [r[0] for r in conn.execute("SELECT id FROM frames")]
        stages.invalidate(conn, pose, nome)
        list(_STADI[nome](conn, tmp_path))
    assert chiamate == [1]


def test_normalize_closes_each_round_once(client, monkeypatch):
    """La pulizia di fine giro della normalizzazione e' cara: una volta per giro lavorato, e mai
    su una corsa che non ha niente da fare."""
    calls = []
    monkeypatch.setattr(normalize, "_at_round_end", lambda *_: calls.append(1))
    with db(client) as conn:
        list(normalize.normalize_frames(conn))  # svuota cio' che il banco aveva lasciato in coda
        calls.clear()
        list(normalize.normalize_frames(conn))
        assert calls == []
        stages.invalidate(conn, [r[0] for r in conn.execute("SELECT id FROM frames")], "normalize")
        list(normalize.normalize_frames(conn))
    assert calls == [1]


@pytest.mark.parametrize(("voci", "attese"), [(22080, [1]), (0, [])])
def test_a_new_catalog_rewrites_the_names_it_gives(db_path, monkeypatch, voci, attese):
    """I nomi degli oggetti scritti nell'uso vengono anche dal catalogo: se all'avvio ne entra uno
    nuovo si riscrive, se era gia' quello non si riconta niente."""
    from astrolog.api import app
    from astrolog.catalog import load as catalog_load

    chiamate = []
    monkeypatch.setattr(catalog_load, "load_catalog", lambda conn: voci)
    monkeypatch.setattr(gear_usage, "write", lambda conn: chiamate.append(1))
    app._load_catalog(db_path)
    assert chiamate == attese


def test_calibration_answered_takes_its_night_object_and_sky_off_the_gear(conn):
    """ "Sono file di calibrazione" stacca notte, oggetto e cielo da quei frame, e nessuno stadio li
    lavora dopo: l'uso si riscrive nella risposta stessa, o l'Attrezzatura resterebbe a dire la
    notte, l'oggetto e la scala di un dark."""
    radice = add_folder(conn, "D:/Astro")
    corredo = conn.execute("INSERT INTO rigs(focal_mm, created_at) VALUES(500.0, 'ora')").lastrowid
    oggetto = conn.execute(
        "INSERT INTO objects(catalog_slug, created_at) VALUES('m-1', 'ora')"
    ).lastrowid
    sito = conn.execute(
        "INSERT INTO sites(name, latitude, longitude, created_at) VALUES('Casa', 45, 11, 'ora')"
    ).lastrowid
    notte = conn.execute(
        "INSERT INTO nights(site_id, night_date, created_at) VALUES(?, '2024-05-18', 'ora')",
        (sito,),
    ).lastrowid
    frame_id = _frame(conn, radice, "dark/a.fits", sky="done")
    conn.execute(
        "UPDATE frames SET rig_id = ?, object_id = ?, night_id = ? WHERE id = ?",
        (corredo, oggetto, notte, frame_id),
    )
    gear_usage.write(conn)

    def uso():
        return conn.execute(
            "SELECT scale_arcsec_px, objects_json, nights FROM gear_usage WHERE subject = 'rig'"
        ).fetchone()

    assert tuple(uso())[0] is not None and tuple(uso())[2] == 1
    typeless.declare(conn, "D:/Astro/dark", typeless.CALIBRATION)
    typeless_folders.write(conn)  # come a fine stadio: risolta dal cielo, chiede solo se risposta
    typeless_answer.apply_answer(conn, typeless.row_of(conn, "D:/Astro/dark"))
    assert tuple(uso()) == (None, "[]", 0)


@pytest.mark.parametrize(
    ("query", "indice"),
    [(gear_usage._CORREDI, "frames_rig"), (gear_usage._FILTRI, "frames_filter")],
    ids=["corredi", "filtri"],
)
def test_gear_usage_counts_rigs_and_filters_from_the_index_alone(conn, query, indice):
    """Chi scrive l'uso dell'Attrezzatura a fine giro conta le pose di ogni corredo e di ogni filtro
    dall'indice, senza la tabella: un indice sulla sola colonna gli farebbe leggere comunque la riga
    di ogni posa."""
    piano = " ".join(r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + query))
    assert re.search(rf"COVERING INDEX {indice}\b", piano), piano
