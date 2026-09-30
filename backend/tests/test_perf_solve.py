"""Il test di prestazioni del solver: secondi per posa col campo dato, confrontati con
l'ultima misura committata in `perf_baseline.json`.

Vincolo non ovvio: questo e' l'unico test che lancia **ASTAP vero**, e serve un FITS **vero**
-- una posa di stelle, che l'archivio sintetico non sa fabbricare (i suoi pixel sono rumore, e
un solver non ci trova niente). Percio' si salta finche' non gli si dice dove sono: con
`ASTROLOG_TEST_FITS` si indica un frame vero. Marcato `lento`: gira a richiesta, mai nel
cancello.
"""

import json
import os
import time
from pathlib import Path

import pytest
from astropy.io import fits

from astrolog import astap
from astrolog.units import field_deg, scale_arcsec_px

# Catturate all'import, PRIMA del recinto della suite: questo e' l'UNICO test che parla col
# solver vero, ed e' il motivo per cui esiste. Il recinto resta buono per tutti gli altri.
find_exe_vero = astap.find_exe
run_vero = astap._run

BASELINE = Path(__file__).with_name("perf_baseline.json")
GIRI = 5
# La misura fatta a mano su due corredi diversi da' 0,2 s a posa col campo dato: si accetta
# fino al doppio, perche' una CI e' piu' lenta di un portatile.
TOLLERANZA = 2.0


def _campione():
    percorso = os.environ.get("ASTROLOG_TEST_FITS")
    if not percorso or not Path(percorso).exists():
        pytest.skip("serve un FITS vero: ASTROLOG_TEST_FITS=<percorso di una posa di stelle>")
    exe = find_exe_vero()
    if not exe:
        pytest.skip("ASTAP non e' installato su questa macchina")
    return percorso, exe


@pytest.mark.lento
def test_solve_seconds_per_frame_does_not_regress(tmp_path):
    """Quanto costa una posa col campo e il puntamento dati. E' la misura che decide se un
    archivio si risolve in mezz'ora o in una notte."""
    percorso, exe = _campione()
    header = fits.getheader(percorso)
    # senza moltiplicare per il binning: e' la stessa regola dello stadio (XPIXSZ lo include
    # gia', e moltiplicare raddoppierebbe il campo)
    scala = scale_arcsec_px(header.get("XPIXSZ"), header.get("FOCALLEN"))
    campo = field_deg(header.get("NAXIS2"), scala)
    assert campo, "il FITS di prova deve dire focale e dimensione dei pixel"

    tempi = []
    for giro in range(GIRI):
        t0 = time.perf_counter()
        esito = astap.solve(
            percorso,
            tmp_path / f"g{giro}",
            field_deg=campo,
            ra_deg=header.get("RA"),
            dec_deg=header.get("DEC"),
            exe=exe,
            run=run_vero,
        )
        tempi.append(time.perf_counter() - t0)
        assert esito.ok, f"il FITS di prova non si risolve: {esito.reason}"

    misura = round(sorted(tempi)[len(tempi) // 2], 3)  # la mediana, non la media
    if "solve_seconds_per_frame" not in _baseline():
        _scrivi_baseline(misura)
        pytest.skip(f"prima misura: {misura} s a posa scritti in perf_baseline.json")
    atteso = _baseline()["solve_seconds_per_frame"]
    assert misura <= atteso * TOLLERANZA, f"{misura} s a posa contro {atteso} committati"


@pytest.mark.lento
def test_giving_the_field_is_what_makes_it_fast(tmp_path):
    """La leva della velocita' e' il campo, non il raggio di ricerca: e' la misura su cui e'
    costruito tutto lo stadio, e se un domani smettesse di essere vera lo si deve sapere."""
    percorso, exe = _campione()
    header = fits.getheader(percorso)
    # senza moltiplicare per il binning: e' la stessa regola dello stadio (XPIXSZ lo include
    # gia', e moltiplicare raddoppierebbe il campo)
    scala = scale_arcsec_px(header.get("XPIXSZ"), header.get("FOCALLEN"))
    coord = {"ra_deg": header.get("RA"), "dec_deg": header.get("DEC")}

    def quanto(campo, dove):
        t0 = time.perf_counter()
        esito = astap.solve(
            percorso, tmp_path / dove, field_deg=campo, exe=exe, run=run_vero, **coord
        )
        assert esito.ok
        return time.perf_counter() - t0

    col_campo = quanto(field_deg(header.get("NAXIS2"), scala), "con")
    senza = quanto(None, "senza")
    assert senza > col_campo * 2, f"col campo {col_campo:.2f}s, senza {senza:.2f}s"


def _baseline():
    return json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {}


def _scrivi_baseline(misura):
    dati = _baseline()
    dati["solve_seconds_per_frame"] = misura
    BASELINE.write_text(json.dumps(dati), encoding="utf-8")
