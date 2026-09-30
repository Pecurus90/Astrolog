"""Tre giudizi che dipendono solo da cio' che il file dice -- la camera, il filtro, l'ottica -- si
scrivono sulla posa quando la scansione la legge, e le pagine di Da confermare li filtrano in SQL
invece di rileggere l'archivio (`spine/header_asks.py`). Il grezzo non cambia, quindi nessuno deve
riscriverli: la prova e' che su ogni posa dicono cio' che direbbero le regole sul suo grezzo."""

import re

import pytest

from astrolog.spine import header_asks, rig_optics, rigless, unfiltered
from astrolog.spine.night_rig import asks_camera
from astrolog.spine.rig_optics import names_the_optics
from astrolog.spine.unfiltered import says_no_filter
from astrolog.vocab.software import normalize_software
from conftest import rows, scan, write_light
from synthetic import build_archive


def test_every_frame_carries_what_its_raw_header_asks(conn, tmp_path):
    build_archive(tmp_path / "lib")
    write_light(tmp_path / "lib" / "muta" / "senza_camera.fits")  # nessun INSTRUME
    scan(conn, tmp_path / "lib")
    pose = rows(conn, "SELECT * FROM frames")
    assert pose, "il banco non ha pose: la prova non guarda niente"
    for p in pose:
        atteso = (
            int(asks_camera(p["instrument_raw"])),
            int(says_no_filter(p["filter_raw"])),
            int(names_the_optics(normalize_software(p["software_raw"]), p["telescope_raw"])),
        )
        assert (p["asks_camera"], p["asks_filter"], p["names_optics"]) == atteso, p["id"]
    # il banco ha tutti e due i lati di ogni giudizio, o la prova sarebbe vera per caso
    for colonna in ("asks_camera", "asks_filter", "names_optics"):
        assert {p[colonna] for p in pose} == {0, 1}, colonna


def test_the_fallback_is_what_an_empty_header_asks(conn):
    """Chi scrive una posa senza passare dai giudizi -- una prova, un'inserzione a mano -- prende
    il ripiego dello schema: deve essere cio' che le regole dicono di un header vuoto."""
    ripiego = {
        r["name"]: int(r["dflt_value"])
        for r in conn.execute("PRAGMA table_info(frames)")
        if r["name"] in header_asks.of({})
    }
    assert ripiego == header_asks.of({})


@pytest.mark.parametrize(
    ("query", "indice"),
    [
        (rigless._BY_GROUP, "frames_asks_camera"),
        (rig_optics._BY_RIG, "frames_no_optics"),
        (unfiltered._BY_CAMERA, "frames_asks_filter"),
    ],
    ids=["rigless", "rig_optics", "unfiltered"],
)
def test_each_reader_finds_its_poses_through_the_index(conn, query, indice):
    """Senza il suo indice, ogni lettore scorre l'archivio intero a ogni apertura della pagina,
    anche quando non c'e' niente da chiedere: si chiede il piano a SQLite invece di cronometrare."""
    piano = " ".join(r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + query))
    assert re.search(rf"INDEX {indice}\b", piano), piano
