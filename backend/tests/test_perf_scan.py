"""Il test di prestazioni della scansione: frame letti al secondo, confrontati con l'ultima
misura committata in `perf_baseline.json`. Rosso se peggiora oltre la meta'. Marcato
`lento`: gira a richiesta e in CI, non nel cancello."""

import json
import time
from pathlib import Path

import pytest

from astrolog.spine.scan import scan_folder
from conftest import add_folder, write_light

BASELINE = Path(__file__).with_name("perf_baseline.json")
N_FILES = 300
TOLERANCE = 0.5  # si accetta fino a meta' della velocita' committata: la CI e' piu' lenta


@pytest.mark.lento
def test_scan_frames_per_second_does_not_regress(conn, tmp_path):
    for i in range(N_FILES):
        write_light(
            tmp_path / f"n{i // 50}" / f"f{i}.fits",
            obj=f"M {i}",
            date=f"2024-05-17T21:{i // 60:02d}:{i % 60:02d}",
        )
    fid = add_folder(conn, tmp_path)
    t0 = time.perf_counter()
    done = list(scan_folder(conn, fid))[-1]
    rate = N_FILES / (time.perf_counter() - t0)
    assert done["new"] == N_FILES
    if not BASELINE.exists():
        BASELINE.write_text(json.dumps({"scan_frames_per_s": round(rate, 1)}), encoding="utf-8")
        pytest.skip(f"prima misura: {rate:.1f} frame/s scritti in perf_baseline.json")
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))["scan_frames_per_s"]
    assert rate >= baseline * TOLERANCE, f"{rate:.1f} frame/s contro {baseline} committati"
