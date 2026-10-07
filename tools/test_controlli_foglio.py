"""I numeri del foglio contro chi li contraddice: i pavimenti del cielo.

Prima casa di `controlli_foglio.py`. La guardia nasce da un difetto vero: un nostro elenco di
numeri finito dentro un file che non possiamo correggere. Le prove sulla soglia della riga sono
uscite col v27 (`tools/test_tolti.txt`).
"""

import os
import pathlib
import shutil
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import controlli_foglio  # noqa: E402


def _radice_col_foglio(tmp_path, testo):
    """Una radice finta con dentro il foglio e `units.py`: e' cio' che le due guardie leggono."""
    stili = tmp_path / "frontend" / "src" / "stili"
    stili.mkdir(parents=True)
    (stili / controlli_foglio.FOGLIO).write_text(testo, encoding="utf-8")
    unita = tmp_path / "backend" / "astrolog"
    unita.mkdir(parents=True)
    shutil.copyfile(os.path.join(ROOT, "backend", "astrolog", "units.py"), unita / "units.py")
    return str(tmp_path)


def _consegna():
    with open(
        os.path.join(ROOT, "frontend", "src", "stili", controlli_foglio.FOGLIO), encoding="utf-8"
    ) as h:
        return h.read()


def test_a_sky_floor_quoted_in_the_sheet_that_drifted_is_blocked(tmp_path):
    """I pavimenti della scala sono un **nostro** fatto scritto in casa loro: il foglio non si
    emenda, quindi il giorno che la nostra tabella cambia quel commento dice il falso e nessuno
    se ne accorge."""
    storto = _consegna().replace("4 = 20,80", "4 = 20,40", 1)
    colpe = controlli_foglio.pavimenti_del_cielo(_radice_col_foglio(tmp_path, storto))
    assert colpe == ["astrolog.css: la scala dice 4 = 20.4, l'app usa 20.8"], colpe


def test_a_sheet_that_stopped_quoting_the_floors_is_said(tmp_path):
    """Sparito il commento, la guardia non ha piu' niente da confrontare: lo dice invece di
    passare verde. Un controllo che tace quando la cosa da controllare sparisce e' verde per il
    motivo sbagliato."""
    senza = _consegna()
    for classe, pavimento in (
        ("1", "21,76"),
        ("2", "21,60"),
        ("3", "21,30"),
        ("4", "20,80"),
        ("5", "19,25"),
        ("6", "18,50"),
        ("7", "18,00"),
        ("8", "17,00"),
    ):
        senza = senza.replace(f"{classe} = {pavimento}", "")
    colpe = controlli_foglio.pavimenti_del_cielo(_radice_col_foglio(tmp_path, senza))
    assert colpe == ["astrolog.css: il commento della scala non cita piu' nessun pavimento"], colpe


def test_one_missing_sky_floor_is_said_not_only_all_of_them(tmp_path):
    """Il cambio **parziale** e' quello probabile, e una guardia che confronta solo cio' che il
    foglio cita ancora tacerebbe: sparito un pavimento, non c'e' piu' niente da confrontare per
    quella classe."""
    senza = _consegna().replace("4 = 20,80 \u00b7", "", 1)
    colpe = controlli_foglio.pavimenti_del_cielo(_radice_col_foglio(tmp_path, senza))
    assert colpe == ["astrolog.css: la scala non cita piu' il pavimento della classe 4 (20.8)"], (
        colpe
    )


def test_a_floors_literal_that_became_computed_says_what_to_do(tmp_path):
    """La guardia legge `BORTLE_FLOORS` **senza eseguire il modulo**: se smette di essere un
    letterale non puo' piu' leggerlo. Lo dice con una frase che nomina il file e la scelta, invece
    di lasciare una traccia che nomina un numero di riga e nient'altro."""
    radice = _radice_col_foglio(tmp_path, _consegna())
    unita = pathlib.Path(radice) / "backend" / "astrolog" / "units.py"
    testo = unita.read_text(encoding="utf-8")
    inizio = testo.index("BORTLE_FLOORS = ")
    fine = testo.index(chr(10) + "BORTLE_TOP", inizio)
    unita.write_text(
        testo[:inizio] + "BORTLE_FLOORS = tuple(zip(range(1, 9), _pavimenti()))" + testo[fine:],
        encoding="utf-8",
    )
    with pytest.raises(LookupError, match="non e' piu' un letterale"):
        controlli_foglio.pavimenti_del_cielo(radice)
