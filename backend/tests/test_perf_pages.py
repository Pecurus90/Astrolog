"""Il budget delle pagine (passo 6.15): ogni GET che una pagina fa quando si apre, su un archivio
da 10.000 frame (`perf_archive.py`), contro la soglia scritta in `perf_budget.json` accanto alla
misura che l'ha data. Marcato `lento`: gira nel job lento della CI e nella Nightly.

La soglia e' quattro volte la misura, perche' il runner condiviso della CI e' arrivato a 3,2 volte
il portatile a codice fermo (Issue #63, come `test_perf_catalog.py`). Mai sotto 0,1 s e mai sopra
1 s, i due limiti di Nielsen [C NN/g "Response Times: The 3 Important Limits": "0.1 second is
about the limit for having the user feel that the system is reacting instantaneously"; "1.0
second is about the limit for the user's flow of thought to stay uninterrupted"]: sotto 0,1 s
nessuno vede la differenza, sopra 1 s una pagina interrompe chi la usa, qualunque fosse la misura.

Rimisurare dopo un passo che cambia una rotta: `ASTROLOG_RIMISURA=1 python -m pytest -m lento
tests/test_perf_pages.py`, poi si committa il json. Le misure dei frame non ci sono (la pipeline
nuova non gira qui): le rotte delle misure si leggono con i frame in attesa.
"""

import json
import math
import os
import shutil
import time
from pathlib import Path

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.api.deps import get_db
from astrolog.db.connect import connect
from conftest import rete_giu
from perf_archive import build, write_archive

BUDGET = Path(__file__).with_name("perf_budget.json")
CI_FACTOR = 4  # [P Issue #63] il runner condiviso fino a 3,2 volte il portatile
FLOOR_MS = 100  # [C Nielsen, 0.1 s] sotto, la risposta e' istantanea per chi guarda
CEILING_MS = 1000  # [C Nielsen, 1.0 s] sopra, il filo del pensiero si interrompe
RUNS = 5

# Le GET di ogni pagina all'apertura, coi parametri che manda il frontend (App.tsx, Notti.tsx:38,
# Archivio.tsx:35, SezioneOggetti.tsx:79...); {night}, {month} e {key} li sceglie l'archivio.
PAGE_ROUTES = [
    "/api/v1/settings",
    "/api/v1/backup",
    "/api/v1/review",
    "/api/v1/pipeline/status",
    "/api/v1/tonight",
    "/api/v1/nights?limit=1",
    "/api/v1/folders",
    "/api/v1/moon/calendar",
    "/api/v1/year",
    "/api/v1/weather",
    "/api/v1/nights?limit=20&offset=0",
    "/api/v1/nights?limit=7",
    # non la chiede una pagina: e' l'elenco piu' lungo che l'API da', e Notti la Luna la legge
    "/api/v1/nights?limit=500",
    "/api/v1/nights/calendar?month={month}",
    "/api/v1/nights/{night}",
    "/api/v1/nights/{night}/measures",
    "/api/v1/archive?limit=20&offset=0&sort=name",
    "/api/v1/objects/{key}",
    "/api/v1/objects/{key}/measures",
    "/api/v1/gear",
    "/api/v1/vocab/filter-models",
    "/api/v1/review/objects/settled?limit=5&offset=0",
    "/api/v1/sites",
    "/api/v1/scans?limit=20&offset=0",
    "/api/v1/solver",
    "/api/v1/folders/path-info",
    "/api/v1/search?q=M",
]


def threshold_ms(measured_ms):
    return min(max(math.ceil(measured_ms * CI_FACTOR), FLOOR_MS), CEILING_MS)


def over_budget(measured, budget):
    """Le rotte sopra la loro soglia, con la misura: vuoto se tutte ci stanno."""
    return {
        route: (ms, budget[route]["soglia_ms"])
        for route, ms in measured.items()
        if ms > budget[route]["soglia_ms"]
    }


def test_a_route_over_its_threshold_is_reported_and_one_under_is_not():
    budget = {"/a": {"misura_ms": 10, "soglia_ms": 100}, "/b": {"misura_ms": 10, "soglia_ms": 100}}
    assert over_budget({"/a": 101.0, "/b": 99.0}, budget) == {"/a": (101.0, 100)}


def test_the_threshold_is_four_times_the_measure_between_nielsen_limits():
    assert threshold_ms(0.6) == FLOOR_MS
    assert threshold_ms(90.0) == 360
    assert threshold_ms(400.0) == CEILING_MS


def test_every_written_threshold_follows_from_its_measure():
    """Una soglia scritta a mano, staccata dalla misura, sarebbe una taratura (principio 1)."""
    budget = json.loads(BUDGET.read_text(encoding="utf-8"))
    assert set(budget) == set(PAGE_ROUTES)
    for route, row in budget.items():
        assert row["soglia_ms"] == threshold_ms(row["misura_ms"]), route


@pytest.fixture(scope="module")
def big_archive(tmp_path_factory, _catalog_template):
    work = tmp_path_factory.mktemp("budget")
    db = work / "astrolog.db"
    shutil.copy(_catalog_template, db)
    write_archive(work / "lib")
    build(db, work / "lib")
    return db


def _fill(db):
    conn = connect(db)
    try:
        night_id, night_date = conn.execute(
            "SELECT n.id, n.night_date FROM nights n JOIN frames f ON f.night_id = n.id"
            " GROUP BY n.id ORDER BY COUNT(*) DESC LIMIT 1"
        ).fetchone()
        (key,) = conn.execute(
            "SELECT o.catalog_slug FROM objects o JOIN frames f ON f.object_id = o.id"
            " GROUP BY o.id ORDER BY COUNT(*) DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    return {"night": night_id, "month": night_date[:7], "key": key}


def _measure(client, routes, fill):
    """La migliore di cinque, dopo una lettura che scalda: si misura la rotta, non il primo
    accesso al file."""
    measured = {}
    for route in routes:
        path = route.format(**fill)
        assert client.get(path).status_code == 200, path
        times = []
        for _ in range(RUNS):
            t0 = time.perf_counter()
            client.get(path)
            times.append((time.perf_counter() - t0) * 1000)
        measured[route] = round(min(times), 1)
    return measured


@pytest.mark.lento
def test_every_page_route_stays_in_its_budget(big_archive, monkeypatch):
    if os.environ.get("PYTEST_XDIST_WORKER"):
        pytest.skip("una misura di tempo gira da sola, non sotto -n")
    rete_giu(monkeypatch)  # meteo e cielo di stanotte dalla cache, come al sito buio
    fill = _fill(big_archive)
    with TestClient(create_app(big_archive), base_url="http://localhost") as client:
        measured = _measure(client, PAGE_ROUTES, fill)
    if os.environ.get("ASTROLOG_RIMISURA"):
        rows = {r: {"misura_ms": ms, "soglia_ms": threshold_ms(ms)} for r, ms in measured.items()}
        BUDGET.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
        pytest.skip(f"misure scritte in {BUDGET.name}")
    budget = json.loads(BUDGET.read_text(encoding="utf-8"))
    assert over_budget(measured, budget) == {}


@pytest.mark.lento
def test_a_route_slowed_on_purpose_turns_the_budget_red(big_archive):
    """La guardia guarda: una connessione che tarda un secondo, sotto una rotta vera."""
    if os.environ.get("PYTEST_XDIST_WORKER"):
        pytest.skip("una misura di tempo gira da sola, non sotto -n")

    def slow_db(request: Request):
        time.sleep(CEILING_MS / 1000)
        conn = connect(request.app.state.db_path, check_same_thread=False)
        try:
            yield conn
        finally:
            conn.close()

    app = create_app(big_archive)
    app.dependency_overrides[get_db] = slow_db
    route = "/api/v1/sites"
    with TestClient(app, base_url="http://localhost") as client:
        measured = _measure(client, [route], _fill(big_archive))
    budget = json.loads(BUDGET.read_text(encoding="utf-8"))
    assert route in over_budget(measured, budget)
