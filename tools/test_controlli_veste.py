"""Le classi della veste, e il foglio della consegna.

Una classe sbagliata non rompe niente -- non si applica, e la pagina resta nuda in quel punto senza
che nessuna prova cada -- e una classe copiata fuori dal suo mattone non la segnala nessuno il
giorno che il design la rinomina. Per questo si guardano a macchina.

Il contrasto sta in `test_controlli_contrasto.py`: e' un altro mestiere, e teneva questo file --
e il modulo che prova -- sopra il tetto di righe.

test-tolto: test_black_on_white_is_the_highest_contrast_there_is -- traslocato, come i sette qui
sotto, in `test_controlli_contrasto.py`: stessa casa del codice che prova.
test-tolto: test_a_colour_with_transparency_is_composed_on_its_background
test-tolto: test_every_declared_pair_is_above_its_threshold
test-tolto: test_the_two_themes_are_really_two
test-tolto: test_a_sheet_whose_light_block_cannot_be_found_is_refused
test-tolto: test_that_refusal_reaches_the_gate_as_a_line_not_a_traceback
test-tolto: test_the_glass_bar_is_measured_on_what_is_under_it
test-tolto: test_a_colour_pushed_below_the_threshold_is_caught
"""

import os
import re
import shutil
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import controlli_veste  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_every_sheet_guard_is_green_on_the_real_sheet():
    # tutti() is the only caller of some guards (the sky floors): run it on the real repo.
    assert [(what, bad) for what, bad in controlli_veste.tutti(ROOT) if bad] == []


def test_no_class_in_the_code_is_missing_from_the_sheet():
    """Ogni `as-*` scritta nell'app esiste nel foglio."""
    assert controlli_veste.classi_inventate(ROOT) == []


def test_the_class_the_whole_sheet_hangs_from_is_watched():
    """`.as-app` sta nella **pagina**, non nel codice: fuori da quella classe i mattoni hanno i
    colori ma non i reset ne' il contorno di fuoco. Un refuso li' spegne il fuoco da tastiera su
    tutta l'app, e nessuna prova del frontend lo vedrebbe -- in jsdom il body e' un altro."""
    letti = [p for p in controlli_veste._sorgenti(ROOT) if p.endswith("index.html")]
    assert letti, "la pagina non e' fra i file guardati"
    with open(letti[0], encoding="utf-8") as h:
        assert 'class="as-app"' in h.read()


def test_a_class_written_in_the_page_is_caught(tmp_path):
    """**La guardia vista rossa**, sulla pagina: una `as-*` sbagliata li' dentro e' un rosso."""
    stili = tmp_path / "frontend" / "src" / "stili"
    stili.mkdir(parents=True)
    (stili / controlli_veste.FOGLIO).write_text(".as-app { margin: 0; }\n", encoding="utf-8")
    (tmp_path / "frontend" / "index.html").write_text(
        '<html><body class="as-applicazione"></body></html>\n', encoding="utf-8"
    )
    assert controlli_veste.classi_inventate(str(tmp_path)) == ["as-applicazione"]


def test_a_class_built_in_pieces_is_said_not_skipped(tmp_path):
    """Una classe composta a pezzi non si puo' leggere: allora si **dice**. La fetta dopo e' *Da
    confermare*, dove le righe hanno stati (`--errore`, `--caricamento`): li' i `className={...}`
    arrivano, e una guardia che tace dove non arriva sembra che abbia guardato."""
    stili = tmp_path / "frontend" / "src" / "stili"
    stili.mkdir(parents=True)
    (stili / controlli_veste.FOGLIO).write_text(".as-riga { display: grid; }\n", encoding="utf-8")
    (tmp_path / "frontend" / "src" / "Riga.tsx").write_text(
        "export const a = <p className={`as-riga${stato}`} />\n"
        'export const b = <p className={rotta ? "as-riga" : "as-riga--errore"} />\n'
        # la forma piu' insidiosa: qui dentro la parola `as-` non compare nemmeno, e finche' la
        # guardia la cercava per dire "non so leggere" questa passava in silenzio
        "export const c = <p className={classeRiga(stato)} />\n",
        encoding="utf-8",
    )
    colpe = controlli_veste.classi_inventate(str(tmp_path))
    # ognuna delle tre e' un rosso, e **dice cosa ha visto**: la seconda si legge ed e' inventata;
    # la prima esce col pezzo attaccato (`as-riga${stato}`, che nel foglio non esiste); la terza
    # non si legge affatto, e allora lo dichiara col codice che non ha saputo leggere
    assert "as-riga--errore" in colpe
    assert "as-riga${stato}" in colpe
    mute = [c for c in colpe if "non so leggere" in c]
    assert [c for c in mute if "classeRiga" in c], colpe


def test_a_class_that_does_not_exist_is_caught(tmp_path):
    """**La guardia vista rossa.** Una classe inventata non si vede in nessun modo: non si applica,
    e nessuna prova cade. E' successo davvero, scrivendo questa fetta."""
    stili = tmp_path / "frontend" / "src" / "stili"
    stili.mkdir(parents=True)
    (stili / controlli_veste.FOGLIO).write_text(".as-voce { color: red; }\n", encoding="utf-8")
    (tmp_path / "frontend" / "src" / "Finta.tsx").write_text(
        'export const x = <a className="as-voce as-elenco-nudo">ciao</a>\n', encoding="utf-8"
    )
    assert controlli_veste.classi_inventate(str(tmp_path)) == ["as-elenco-nudo"]


def _radice_con_attesa(tmp_path, foglio, codice, attesa):
    """Una radice finta: il foglio, un file di codice e l'elenco delle classi in attesa."""
    stili = tmp_path / "frontend" / "src" / "stili"
    stili.mkdir(parents=True)
    (stili / controlli_veste.FOGLIO).write_text(foglio, encoding="utf-8")
    (tmp_path / "frontend" / "src" / "Pagina.tsx").write_text(codice, encoding="utf-8")
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "classi_in_attesa.txt").write_text(
        "# intestazione\n" + "".join(f"{c}\n" for c in attesa), encoding="utf-8"
    )
    return str(tmp_path)


def test_a_waiting_class_passes_and_a_new_missing_one_does_not(tmp_path):
    """**L'elenco in attesa copre solo cio' che dichiara** (ADR 0018): una classe del v10 scritta
    in una pagina non ancora ridisegnata passa, una classe nuova assente dal foglio resta rossa."""
    radice = _radice_con_attesa(
        tmp_path,
        ".as-carta { color: red; }\n",
        'export const x = <p className="as-carta as-vecchia as-inventata" />\n',
        ["as-vecchia"],
    )
    assert controlli_veste.classi_inventate(radice) == ["as-inventata"]


def test_the_waiting_list_only_shrinks(tmp_path):
    """**La guardia vista rossa sull'elenco.** Una voce che il codice non scrive piu', o che il
    foglio ora ha, e' un rosso: senza, l'elenco crescerebbe di voci morte e un giorno coprirebbe
    una classe inventata con lo stesso nome."""
    radice = _radice_con_attesa(
        tmp_path,
        ".as-carta { color: red; }\n.as-arrivata { color: red; }\n",
        'export const x = <p className="as-carta as-arrivata" />\n',
        ["as-arrivata", "as-sparita"],
    )
    assert controlli_veste.classi_inventate(radice) == [
        "tools/classi_in_attesa.txt: as-arrivata il foglio ora la ha, togli la voce",
        "tools/classi_in_attesa.txt: as-sparita il codice non la scrive piu', togli la voce",
    ]


def test_the_filter_variants_in_the_table_are_the_ones_the_brick_writes():
    """`MATTONI` elenca le varianti del filtro **a mano**, e il mattone le scrive nella sua mappa:
    due case dello stesso fatto. Una banda aggiunta al mattone e dimenticata qui non fa rumore --
    spegne la guardia **proprio su quella classe**, cioe' permette di ricopiare la mappa in
    un'altra pagina senza che nessuno lo dica, che e' il guasto per cui il mattone esiste. E una
    voce rimasta qui dopo che il mattone l'ha tolta e' una guardia che sorveglia il vuoto.

    Le due case restano due perche' hanno mestieri diversi: la mappa dice **che colore ha una
    banda**, la tabella dice **di chi e' quella classe**. Questa prova e' il legame."""
    casa = "frontend/src/FiltriUsati.tsx"
    with open(os.path.join(ROOT, *casa.split("/")), encoding="utf-8") as h:
        scritte = set(re.findall(r"as-filtro--[a-z0-9-]+", controlli_veste._senza_prosa(h.read())))
    assert scritte, "il mattone non scrive nessuna variante: la prova non guarda niente"

    elencate = {c for c in controlli_veste.MATTONI[casa] if c.startswith("as-filtro--")}

    assert scritte == elencate


def test_no_class_is_written_outside_its_brick():
    """Dove un mattone c'e', la sua classe si scrive li' dentro e basta."""
    assert controlli_veste.classi_fuori_casa(ROOT) == []


@pytest.mark.parametrize(
    "come",
    [
        'className="as-bottone as-bottone--primario"',
        'className={pieno ? "as-bottone" : "as-riga"}',
        "className={`as-bottone ${verso}`}",
        'const CLASSI = { primario: "as-bottone as-bottone--primario" }',
    ],
    ids=["scritta", "ternario", "composta", "in una mappa"],
)
def test_a_copy_of_a_brick_is_caught_however_it_is_written(tmp_path, come):
    """**La guardia vista rossa, nelle quattro forme in cui una copia nasce davvero.**

    Le tre dopo la prima sono quelle che contano: un mattone scrive la sua classe **cosi'** -- un
    ternario, una template, una mappa di varianti -- e chi lo ricopia parte da li'. Una guardia che
    vedesse solo `className="..."` direbbe verde proprio sulla copia, ed e' il difetto che ha fatto
    nascere questa guardia: `as-campo` e `as-bottone` erano finite in sette e dodici file **mentre**
    si riparava lo stesso difetto su un'altra classe."""
    fatto = tmp_path / "frontend" / "src"
    fatto.mkdir(parents=True)
    (fatto / "SezioneFinta.tsx").write_text(f"export const x = <p {come} />\n", encoding="utf-8")
    colpe = controlli_veste.classi_fuori_casa(str(tmp_path))
    assert colpe == ["frontend/src/SezioneFinta.tsx: as-bottone (sta in Bottone.tsx)"], colpe


def test_the_brick_itself_is_not_its_own_copy(tmp_path):
    """Il mattone scrive la sua classe: e' il suo mestiere. L'esenzione va per **percorso**, o un
    file che si chiama come lui si esenta da solo."""
    fatto = tmp_path / "frontend" / "src"
    (fatto / "pagine").mkdir(parents=True)
    for percorso in ("Bottone.tsx", "pagine/Bottone.tsx"):
        (fatto / percorso).write_text('export const x = <p className="as-bottone" />\n', "utf-8")
    colpe = controlli_veste.classi_fuori_casa(str(tmp_path))
    assert colpe == ["frontend/src/pagine/Bottone.tsx: as-bottone (sta in Bottone.tsx)"], colpe


def test_a_house_is_exempt_from_its_own_class_only(tmp_path):
    """**L'esenzione e' per la classe, non per il file.** Saltare il file intero appena e' una casa
    lo esentava da **tutti** gli altri mattoni: `Stanotte.tsx`, entrato nell'elenco come casa di
    `as-bortle-scala*`, avrebbe potuto riscrivere a mano `as-bottone` -- che e' esattamente il
    difetto trovato li' un'ora prima -- senza che niente lo dicesse."""
    fatto = tmp_path / "frontend" / "src"
    fatto.mkdir(parents=True)
    (fatto / "Stanotte.tsx").write_text(
        'export const x = <p className="as-bortle-scala as-bottone" />\n', encoding="utf-8"
    )
    colpe = controlli_veste.classi_fuori_casa(str(tmp_path))
    assert colpe == ["frontend/src/Stanotte.tsx: as-bottone (sta in Bottone.tsx)"], colpe


def test_a_class_named_in_prose_is_not_a_copy(tmp_path):
    """**I commenti non si leggono**: in una docstring una classe e' prosa. Senza, la guardia
    accusava `Campo.tsx` di ospitare `as-riga__conteggio`, che li' sta dentro una spiegazione.

    Sono i **commenti** a sparire, non i backtick: quelli delimitano ancora, e devono -- la forma
    `composta` quaranta righe sopra e' una copia scritta dentro una template."""
    fatto = tmp_path / "frontend" / "src"
    fatto.mkdir(parents=True)
    (fatto / "Nota.tsx").write_text(
        "/** Il conteggio vive in `as-riga__conteggio`, non qui. */\nexport const x = 1\n",
        encoding="utf-8",
    )
    assert controlli_veste.classi_fuori_casa(str(tmp_path)) == []


def test_the_class_the_audit_named_is_covered(tmp_path):
    """**`as-campo-modulo`, per nome** (`as-campo` fino al v31, che ha dato quel nome al campo di
    ricerca). E' la classe che l'audit ha trovato scritta a mano in sette file, e
    la guardia e' nata per quella: se l'elenco la dimenticasse, la macchina sarebbe verde proprio
    sul difetto che l'ha fatta nascere. Provato: togliendola da `MATTONI`, senza questa riga non
    cadrebbe nessun'altra prova."""
    fatto = tmp_path / "frontend" / "src"
    fatto.mkdir(parents=True)
    (fatto / "SezioneFinta.tsx").write_text(
        'export const x = <div className="as-campo-modulo" />\n', encoding="utf-8"
    )
    colpe = controlli_veste.classi_fuori_casa(str(tmp_path))
    assert colpe == ["frontend/src/SezioneFinta.tsx: as-campo-modulo (sta in Campo.tsx)"], colpe


def test_the_control_class_stays_with_the_control(tmp_path):
    """`as-campo__input` non e' `as-campo`: il mattone fa da involucro, il controllo resta di chi
    lo scrive. Senza questa distinzione la guardia griderebbe su ogni campo della pagina."""
    fatto = tmp_path / "frontend" / "src"
    fatto.mkdir(parents=True)
    (fatto / "SezioneFinta.tsx").write_text(
        'export const x = <input className="as-campo__input" />\n', encoding="utf-8"
    )
    assert controlli_veste.classi_fuori_casa(str(tmp_path)) == []


def test_no_alert_is_written_by_hand():
    """Ogni avviso dell'app passa da `Avviso`, che porta il segno non cromatico.

    Non e' solo un doppione: un `<p role="alert">` scritto a mano dice il suo esito **col colore
    soltanto**, e chi non distingue verde e rosso non lo legge (WCAG 2.2, 1.4.1). La regola stava
    scritta in prosa da quando `Avviso` e' nato, e si e' rotta dodici volte in nove file."""
    assert controlli_veste.avvisi_a_mano(ROOT) == []


@pytest.mark.parametrize(
    "come",
    [
        '<p role="alert">rotto</p>',
        "<p role='status'>fatto</p>",
        '<div role={"alert"}>rotto</div>',
        '<p role = "alert">rotto</p>',
        '<p role={rotto ? "alert" : "status"}>rotto</p>',
    ],
    ids=["alert", "status", "fra graffe", "con gli spazi", "ternario"],
)
def test_an_alert_written_by_hand_is_caught(tmp_path, come):
    """**La guardia vista rossa.** I due ruoli che `Avviso` sa fare sono i due che si cercano: chi
    ne scrive uno a mano si sta scrivendo un avviso, comunque lo chiami -- e le forme che contano
    sono quelle in cui una copia nasce davvero, cioe' quelle del mattone stesso."""
    fatto = tmp_path / "frontend" / "src"
    fatto.mkdir(parents=True)
    (fatto / "Pagina.tsx").write_text(f"export const x = {come}\n", encoding="utf-8")
    colpe = controlli_veste.avvisi_a_mano(str(tmp_path))
    assert colpe == ["frontend/src/Pagina.tsx: un avviso a mano (usa Avviso)"], colpe


def test_a_role_it_cannot_read_is_said_not_skipped(tmp_path):
    """**La forma del mattone.** `Avviso` scrive `role={ruolo}`: chi lo ricopia parte da li', e una
    guardia che vedesse solo le stringhe direbbe verde proprio sulla copia che conta. Dove non si
    legge nessun ruolo, si **dice** -- come fa `classi_inventate` con le classi."""
    fatto = tmp_path / "frontend" / "src"
    fatto.mkdir(parents=True)
    copia = "export const x = <p role={ruolo}>ciao</p>\n"
    (fatto / "Copia.tsx").write_text(copia, encoding="utf-8")
    colpe = controlli_veste.avvisi_a_mano(str(tmp_path))
    assert colpe == ["frontend/src/Copia.tsx: un ruolo che non so leggere (role={ruolo})"], colpe


def test_the_alert_brick_is_the_one_place_it_may_be_written(tmp_path):
    """`Avviso.tsx` scrive il ruolo: e' il suo mestiere. L'esenzione va per **percorso**, come per
    le classi, o un file che si chiama come lui si esenterebbe da solo."""
    fatto = tmp_path / "frontend" / "src"
    (fatto / "pagine").mkdir(parents=True)
    for percorso in ("Avviso.tsx", "pagine/Avviso.tsx"):
        (fatto / percorso).write_text('export const x = <p role="alert" />\n', encoding="utf-8")
    colpe = controlli_veste.avvisi_a_mano(str(tmp_path))
    assert colpe == ["frontend/src/pagine/Avviso.tsx: un avviso a mano (usa Avviso)"], colpe


def test_other_roles_are_not_alerts(tmp_path):
    """Un `role` qualunque non e' un avviso: la barra ha `group`, una sezione ha `region`. Una
    guardia che gridasse su quelli verrebbe spenta, e con lei la parte che serve."""
    fatto = tmp_path / "frontend" / "src"
    fatto.mkdir(parents=True)
    (fatto / "Pagina.tsx").write_text(
        'export const x = <nav role="group"><section role="region" /></nav>\n', encoding="utf-8"
    )
    assert controlli_veste.avvisi_a_mano(str(tmp_path)) == []


def test_the_sheets_are_the_ones_delivered():
    """L'impronta: il foglio e' quello della consegna, non una sua modifica."""
    assert controlli_veste.fogli_cambiati(ROOT) == []


def test_a_sheet_touched_by_hand_is_caught(tmp_path):
    """**La guardia vista rossa**, l'altra meta': una riga aggiunta al foglio si vede."""
    finto = tmp_path / "frontend" / "src" / "stili"
    finto.mkdir(parents=True)
    for nome in controlli_veste.IMPRONTE:
        # copia **binaria**: rileggere e riscrivere il testo su Windows cambia i fine riga, e
        # l'impronta cambierebbe per quello invece che per la modifica che si vuole provare
        shutil.copyfile(os.path.join(ROOT, "frontend", "src", "stili", nome), finto / nome)
    with open(finto / controlli_veste.FOGLIO, "ab") as h:
        h.write(b"\n.as-bottone { background: red; }\n")
    assert controlli_veste.fogli_cambiati(str(tmp_path)) == ["frontend/src/stili/astrolog.css"]


def test_rewritten_line_endings_say_so(tmp_path):
    """Un foglio identico ma con i fine riga di Windows: e' un rosso -- l'impronta e' sui byte --
    e deve **dire perche'**, o chi lo vede cerca una modifica che non c'e'."""
    finto = tmp_path / "frontend" / "src" / "stili"
    finto.mkdir(parents=True)
    for nome in controlli_veste.IMPRONTE:
        origine = os.path.join(ROOT, "frontend", "src", "stili", nome)
        with open(origine, "rb") as h:
            (finto / nome).write_bytes(h.read().replace(b"\n", b"\r\n"))
    colpe = controlli_veste.fogli_cambiati(str(tmp_path))
    # quanti sono lo dice l'elenco delle impronte, non un numero scritto qui, o un conto a mano
    # si romperebbe il giorno che la consegna cambia il numero dei fogli invece che per un
    # difetto. E **almeno uno**: con l'elenco vuoto il conteggio tornerebbe vero a vuoto.
    assert colpe, "nessun foglio guardato: l'elenco delle impronte e' vuoto"
    assert len(colpe) == len(controlli_veste.IMPRONTE), colpe
    assert all("fine riga" in c for c in colpe), colpe


@pytest.mark.parametrize("mancante", list(controlli_veste.IMPRONTE))
def test_a_missing_sheet_is_said_not_ignored(tmp_path, mancante):
    """Un foglio che non c'e' e' un rosso, non un elenco vuoto: un controllo che tace quando la
    cosa da controllare sparisce e' verde per il motivo sbagliato."""
    finto = tmp_path / "frontend" / "src" / "stili"
    finto.mkdir(parents=True)
    for nome in controlli_veste.IMPRONTE:
        if nome == mancante:
            continue
        shutil.copyfile(os.path.join(ROOT, "frontend", "src", "stili", nome), finto / nome)
    assert controlli_veste.fogli_cambiati(str(tmp_path)) == [f"frontend/src/stili/{mancante}"]
