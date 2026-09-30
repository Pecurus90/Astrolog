"""I numeri del foglio contro chi li contraddice: la soglia della riga e i pavimenti del cielo.

Prima casa di `controlli_foglio.py`. Le due guardie nascono da due difetti veri: una soglia che
rendeva **irraggiungibile per costruzione** la forma che il montaggio del fornitore mostra (e che
e' costata una consegna intera), e un nostro elenco di numeri finito dentro un file che non
possiamo correggere.
"""

import os
import pathlib
import re
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


def test_the_row_threshold_below_the_narrowest_card_is_green():
    """La consegna di adesso: la riga si affianca dentro la carta del primo avvio."""
    assert controlli_foglio.soglia_della_riga(ROOT) == []


def test_a_row_that_never_fits_side_by_side_is_blocked(tmp_path):
    """La contraddizione che e' costata una consegna, riprodotta: la soglia sopra la larghezza
    della carta piu' stretta vuol dire che li' la riga e' incolonnata **sempre**, per
    costruzione. Nessuna prova del frontend puo' vederlo -- in jsdom il foglio non si applica --
    e l'impronta dice solo "e' cambiato", mai "e' sbagliato"."""
    rotto = _consegna().replace(
        "@container colonna (max-width: 420px)", "@container colonna (max-width: 720px)", 1
    )
    colpe = controlli_foglio.soglia_della_riga(_radice_col_foglio(tmp_path, rotto))
    assert colpe and "720px" in colpe[0] and "680px" in colpe[0], colpe


def test_the_guard_reads_the_row_block_not_the_first_threshold_it_meets(tmp_path):
    """Il foglio ha piu' soglie di colonna con la stessa forma, e una sola riguarda la riga: una
    guardia che prendesse la prima che incontra direbbe il falso in tutti e due i versi.

    Il "piu' d'una" non si scrive come numero, si **conta qui**: scritto in prosa, la prossima
    consegna lo falsificherebbe in silenzio."""
    senza_commenti = controlli_foglio._senza_commenti(_consegna())
    blocchi = re.findall(
        r"@container colonna \(max-width:\s*(\d+)px\)\s*\{(.*?)^\}",
        senza_commenti,
        re.S | re.M,
    )
    con_la_riga = [s for s, corpo in blocchi if re.search(r"(^|[\s,}])\.as-riga\s*[,{.]", corpo)]
    assert len(blocchi) > 1, "una soglia sola: questa prova non prova piu' niente"
    assert con_la_riga == ["420"], con_la_riga

    # e spostando **tutte le altre**, la guardia resta verde: guarda il blocco giusto
    altre = _consegna().replace("(max-width: 720px)", "(max-width: 999px)")
    assert controlli_foglio.soglia_della_riga(_radice_col_foglio(tmp_path, altre)) == []


def test_a_sky_floor_quoted_in_the_sheet_that_drifted_is_blocked(tmp_path):
    """I pavimenti della scala sono un **nostro** fatto scritto in casa loro: il foglio non si
    emenda, quindi il giorno che la nostra tabella cambia quel commento dice il falso e nessuno
    se ne accorge -- la scelta sui pavimenti 4 e 5 e' aperta in `docs/coda.md` proprio ora."""
    storto = _consegna().replace("4 = 20,40", "4 = 20,80", 1)
    colpe = controlli_foglio.pavimenti_del_cielo(_radice_col_foglio(tmp_path, storto))
    assert colpe == ["astrolog.css: la scala dice 4 = 20.8, l'app usa 20.4"], colpe


def test_a_sheet_that_stopped_quoting_the_floors_is_said(tmp_path):
    """Sparito il commento, la guardia non ha piu' niente da confrontare: lo dice invece di
    passare verde. Un controllo che tace quando la cosa da controllare sparisce e' verde per il
    motivo sbagliato."""
    senza = _consegna()
    for classe, pavimento in (
        ("1", "21,76"),
        ("2", "21,60"),
        ("3", "21,30"),
        ("4", "20,40"),
        ("5", "19,10"),
        ("6", "18,50"),
        ("7", "18,00"),
        ("8", "17,00"),
    ):
        senza = senza.replace(f"{classe} = {pavimento}", "")
    colpe = controlli_foglio.pavimenti_del_cielo(_radice_col_foglio(tmp_path, senza))
    assert colpe == ["astrolog.css: il commento della scala non cita piu' nessun pavimento"], colpe


def test_a_comment_naming_the_row_does_not_raise_a_false_alarm(tmp_path):
    """Il foglio spiega ogni regola in prosa, e un commento che **nomina** `.as-riga` dentro il
    blocco di un altro mattone la farebbe trovare dove non sta. Qui il costo dell'errore non e'
    simmetrico: un falso rosso blocca il cancello su un file che non possiamo emendare, e l'unica
    uscita sarebbe emendare la guardia."""
    bugiardo = _consegna().replace(
        "@container colonna (max-width: 720px) {",
        "@container colonna (max-width: 720px) {"
        + chr(10)
        + "  /* qui NON si tocca .as-riga, che ha la sua */",
        1,
    )
    assert controlli_foglio.soglia_della_riga(_radice_col_foglio(tmp_path, bugiardo)) == []


def test_one_missing_sky_floor_is_said_not_only_all_of_them(tmp_path):
    """Il cambio **parziale** e' quello probabile -- la classe 4 e' proprio quella in discussione
    -- e una guardia che confronta solo cio' che il foglio cita ancora tacerebbe: sparito un
    pavimento, non c'e' piu' niente da confrontare per quella classe."""
    senza = _consegna().replace("4 = 20,40 \u00b7", "", 1)
    colpe = controlli_foglio.pavimenti_del_cielo(_radice_col_foglio(tmp_path, senza))
    assert colpe == ["astrolog.css: la scala non cita piu' il pavimento della classe 4 (20.4)"], (
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
