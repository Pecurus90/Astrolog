"""Il contrasto si **misura** sui valori veri del foglio, mai letto in una dichiarazione.

Axe, dentro jsdom, non ha layout e non carica CSS: un contrasto li' dentro non lo puo' misurare
nessuno, e senza queste prove la guardia di accessibilita' resterebbe verde per sempre senza aver
guardato un colore. La soglia viene da WCAG 2.2 (1.4.3 testo 4,5:1, 1.4.11 forme 3:1), non da noi,
e le coppie sono quelle che nell'app finiscono davvero una sull'altra.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import controlli_contrasto  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOGLIO = os.path.join(ROOT, *controlli_contrasto.STILI, controlli_contrasto.FOGLIO)


def test_black_on_white_is_the_highest_contrast_there_is():
    """Il conto, provato sui due estremi: 21:1 e' il massimo che esista."""
    assert round(controlli_contrasto.contrasto("#000000", "#ffffff"), 1) == 21.0
    assert controlli_contrasto.contrasto("#777777", "#777777") == 1.0


def test_a_colour_with_transparency_is_composed_on_its_background():
    """Un `rgba()` non ha un contrasto suo: si compone sul fondo su cui sta. Senza questo, una
    linea al 34% si leggerebbe come bianca piena e la misura direbbe una cosa falsa."""
    # il conto a mano: 255*.34 + 20*.66 = 100 (0x64), poi 21 -> 101 (0x65), 28 -> 105 (0x69)
    assert controlli_contrasto.colore("rgba(255,255,255,.34)", su="#14151c") == (0x64, 0x65, 0x69)
    # senza trasparenza il fondo non conta
    assert controlli_contrasto.colore("#14151c", su="#ffffff") == (0x14, 0x15, 0x1C)


def test_every_declared_pair_is_above_its_threshold():
    """La prova vera: ogni coppia dell'elenco, nei due temi, letta dal foglio."""
    assert controlli_contrasto.sotto_soglia(ROOT) == []


def test_the_two_themes_are_really_two():
    """**Che il tema chiaro sia stato letto davvero.** Senza questa riga la misura poteva girare
    due volte sullo scuro -- se il foglio scrivesse quel selettore in un altro modo la regex non
    lo troverebbe -- e tornare OK avendo guardato meta' del lavoro."""
    with open(FOGLIO, encoding="utf-8") as h:
        testo = h.read()
    scuro = controlli_contrasto._valori(testo, "scuro")
    chiaro = controlli_contrasto._valori(testo, "chiaro")
    assert scuro["--fondo-app"] != chiaro["--fondo-app"], "i due temi danno lo stesso fondo"
    assert scuro["--inchiostro"] != chiaro["--inchiostro"]


def test_a_sheet_whose_light_block_cannot_be_found_is_refused():
    """**La guardia vista rossa.** Il selettore del tema chiaro scritto altrimenti -- e' il foglio
    a deciderlo, e il foglio arriva da fuori -- deve fermare la misura, non farla passare."""
    with open(FOGLIO, encoding="utf-8") as h:
        rotto = h.read().replace(':root[data-tema="atlante"] {', ":root[data-tema='atlante'] {")
    with pytest.raises(ValueError, match="tema chiaro"):
        controlli_contrasto._valori(rotto, "chiaro")


def test_that_refusal_reaches_the_gate_as_a_line_not_a_traceback(tmp_path):
    """E arriva al cancello come **una riga di FAIL**: un traceback dice che la macchina si e'
    rotta, non che c'e' qualcosa da fare."""
    stili = tmp_path / "frontend" / "src" / "stili"
    stili.mkdir(parents=True)
    with open(FOGLIO, encoding="utf-8") as h:
        rotto = h.read().replace(':root[data-tema="atlante"] {', ":root[data-tema='atlante'] {")
    (stili / controlli_contrasto.FOGLIO).write_text(rotto, encoding="utf-8")
    colpe = controlli_contrasto.sotto_soglia(str(tmp_path))
    assert any("tema chiaro" in c for c in colpe), colpe


def test_the_whole_bortle_ramp_is_measured_not_just_its_ends():
    """**Tutte e nove le fasce**, non i due estremi.

    Una rampa la si legge insieme, e il centro e' dove due tinte vicine si somigliano di piu': se
    qualcuno misurasse solo `--bortle-1` e `--bortle-9` lascerebbe scoperto proprio quello. La
    regola sta scritta accanto a `FORME`, e senza questa prova nessun rosso cadrebbe togliendole
    da li' -- il commento resterebbe vero solo finche' qualcuno lo rilegge."""
    dentro = {sopra for sopra, _, _, _ in controlli_contrasto._coppie()}
    mancanti = [f"--bortle-{n}" for n in range(1, 10) if f"--bortle-{n}" not in dentro]
    assert not mancanti, f"fasce della scala non misurate: {mancanti}"


def test_the_glass_bar_is_measured_on_what_is_under_it():
    """Un velo non ha un colore suo. La barra in alto e' l'unico fondo non opaco che questa fetta
    monta: misurarlo come se fosse pieno vorrebbe dire leggere un contrasto che nessuno vede."""
    dentro = {(sopra, sotto) for sopra, sotto, _, _ in controlli_contrasto._coppie()}
    assert ("--inchiostro", "--velo-vetro") in dentro
    sul_nero = controlli_contrasto.colore("rgba(20,21,28,.86)")
    sulla_carta = controlli_contrasto.colore("rgba(20,21,28,.86)", su="#f4f5f8")
    assert sul_nero != sulla_carta, "il fondo velato non cambia con cio' che ha sotto"


def test_a_colour_pushed_below_the_threshold_is_caught(tmp_path):
    """**La guardia vista rossa.** Un inchiostro schiarito fino a sparire sul suo fondo deve
    diventare un rosso, o questa macchina non ha dimostrato niente."""
    foglio = FOGLIO
    with open(foglio, encoding="utf-8") as h:
        testo = h.read()
    rotto = testo.replace("--inchiostro-tenue:     #b4bcdb;", "--inchiostro-tenue:     #2a2c33;")
    assert rotto != testo, "il token da rompere non e' piu' scritto cosi'"
    finto = tmp_path / "frontend" / "src" / "stili"
    finto.mkdir(parents=True)
    (finto / controlli_contrasto.FOGLIO).write_text(rotto, encoding="utf-8")
    colpe = controlli_contrasto.sotto_soglia(str(tmp_path))
    assert any("inchiostro-tenue" in c for c in colpe), colpe


def test_a_colour_written_on_a_tint_in_channels_is_read():
    """Il v27 scrive i colori come `rgb(var(--tinta-velo) / .34)`, con la tinta in canali "R G B".
    Senza sostituire il `var()` dentro il colore quei token non si leggono, e sono proprio le
    linee e i veli che portano significato."""
    valori = {"--tinta-velo": "255 255 255", "--linea": "rgb(var(--tinta-velo) / .34)"}
    risolto = controlli_contrasto._risolvi("--linea", valori)
    assert risolto == "rgb(255 255 255 / .34)"
    # lo stesso conto a mano della prova sui colori a virgole: le due grafie danno lo stesso colore
    assert controlli_contrasto.colore(risolto, su="#14151c") == (0x64, 0x65, 0x69)
    assert controlli_contrasto.colore("rgb(20 21 28)") == (0x14, 0x15, 0x1C)


def test_a_tint_darkened_below_the_threshold_is_caught(tmp_path):
    """**La guardia vista rossa, attraverso la tinta.** Un token che legge la sua tinta in canali
    deve seguirla: spenta la tinta del velo, la linea che distingue uno stato sparisce, e la
    misura lo deve dire. Se la guardia leggesse il colore senza la tinta, resterebbe zitta."""
    with open(FOGLIO, encoding="utf-8") as h:
        testo = h.read()
    rotto = testo.replace("--tinta-velo:      205 220 255;", "--tinta-velo:      13 17 34;", 1)
    assert rotto != testo, "la tinta da spegnere non e' piu' scritta cosi'"
    finto = tmp_path / "frontend" / "src" / "stili"
    finto.mkdir(parents=True)
    (finto / controlli_contrasto.FOGLIO).write_text(rotto, encoding="utf-8")
    colpe = controlli_contrasto.sotto_soglia(str(tmp_path))
    assert any(c.startswith("scuro: --linea-significato su --fondo-carta = 1.00:1") for c in colpe)
