"""Guidare ASTAP: il comando che gli si da', cosa non gli si da' mai, e come si legge cio'
che ha scritto.

Vincolo di questi test: **non lanciano ASTAP**. Il lancio si passa come argomento e qui si
passa un finto. Un test che chiamasse il solver vero fallirebbe su una macchina senza ASTAP,
e la suite veloce non puo' dipendere da un programma installato a parte.
"""

import pytest

from astrolog import astap

# Catturate all'import, PRIMA che il recinto della suite le sostituisca: questi test provano
# proprio loro, e con lo stub non proverebbero niente.
find_exe = astap.find_exe
where_exe = astap.where_exe
star_databases = astap.star_databases

# Un esito vero, copiato da una corsa su un frame da 26 megapixel: e' la forma che il modulo
# deve saper leggere, comprese le maiuscole e la notazione esponenziale.
INI_RISOLTO = """
PLTSOLVD=T
CRPIX1= 3.1265000000000000E+003
CRPIX2= 2.0885000000000000E+003
CRVAL1= 2.1080144893504479E+002
CRVAL2= 5.4349083378595992E+001
CDELT1= 1.4462882362362918E-004
CDELT2= 1.4449601734652654E-004
CROTA1= 8.4343059083835158E+001
CROTA2= 8.4349931755088974E+001
CD1_1= 1.4256340084600304E-005
CD1_2=-1.4392447113033648E-004
CD2_1= 1.4379401908293604E-004
CD2_2= 1.4226001018695530E-005
CMDLINE="astap_cli.exe" -f x.fits -o y -fov 0.59
"""

INI_FALLITO = """
PLTSOLVD=F
CMDLINE="astap_cli.exe" -f x.fits
ERROR=Not enough stars.
WARNING=Warning, small image dimensions!!
"""


def fake_run(codice=0, stdout="", scrive=None, esplode=None):
    """Un ASTAP finto: ricorda il comando, scrive i file che gli si dice, e puo' esplodere."""
    visti = []

    def run(cmd, timeout_s):
        visti.append(cmd)
        if esplode is not None:
            raise esplode
        for percorso, testo in (scrive or {}).items():
            percorso.write_text(testo, encoding="utf-8")
        return codice, stdout

    run.calls = visti
    return run


def comando(run):
    return run.calls[0]


def valore(cmd, opzione):
    """Il valore che segue un'opzione nel comando, o None se l'opzione non c'e'."""
    return cmd[cmd.index(opzione) + 1] if opzione in cmd else None


# --- il comando ---------------------------------------------------------------------------


def test_the_command_never_carries_the_two_forbidden_flags(tmp_path):
    """`-update` riscriverebbe il FITS dell'utente; `-extract` gli lascerebbe un CSV accanto,
    ignorando sia `-o` sia la cartella di lavoro. Sono le due regole assolute, e si provano
    sul comando perche' li' si possono provare senza lanciare niente."""
    run = fake_run(scrive={tmp_path / "e.ini": INI_RISOLTO})
    astap.solve(tmp_path / "x.fits", tmp_path / "e", exe="astap", run=run)
    cmd = comando(run)
    assert "-update" not in cmd
    assert not any(c.startswith("-extract") for c in cmd)


def test_solve_field_from_the_header(tmp_path):
    """Il campo inquadrato e' la leva della velocita': misurato, `-fov` col campo giusto vale
    0,2 s contro 2,3 s con `-fov 0`. Si ricava da altezza, pixel, binning e focale."""
    run = fake_run(scrive={tmp_path / "e.ini": INI_RISOLTO})
    astap.solve(tmp_path / "x.fits", tmp_path / "e", field_deg=0.59, exe="astap", run=run)
    assert valore(comando(run), "-fov") == "0.590"

    # senza focale o pixel nell'header il campo non si sa: si passa 0 e ASTAP lo cerca da se'
    run = fake_run(scrive={tmp_path / "e.ini": INI_RISOLTO})
    astap.solve(tmp_path / "x.fits", tmp_path / "e", field_deg=None, exe="astap", run=run)
    assert valore(comando(run), "-fov") == "0"


def test_the_pointing_hint_is_given_in_the_units_astap_wants(tmp_path):
    """`-ra` vuole ORE, non gradi, e `-spd` vuole la distanza dal polo sud, non la
    declinazione: sbagliarle non da' errore, da' il cielo di un altro punto del mondo."""
    run = fake_run(scrive={tmp_path / "e.ini": INI_RISOLTO})
    astap.solve(
        tmp_path / "x.fits", tmp_path / "e", ra_deg=210.945, dec_deg=54.35, exe="astap", run=run
    )
    cmd = comando(run)
    assert float(valore(cmd, "-ra")) == pytest.approx(14.063, abs=0.001)
    assert float(valore(cmd, "-spd")) == pytest.approx(144.35, abs=0.001)
    assert valore(cmd, "-r") == str(astap.SEARCH_RADIUS_DEG)


def test_without_a_pointing_hint_the_search_is_blind(tmp_path):
    """Senza indizio non si inventa un puntamento: si cerca in tutto il cielo. Costa cento
    volte di piu', ed e' il motivo per cui una posa eredita l'indizio dalla sorella."""
    run = fake_run(scrive={tmp_path / "e.ini": INI_RISOLTO})
    astap.solve(tmp_path / "x.fits", tmp_path / "e", exe="astap", run=run)
    cmd = comando(run)
    assert "-ra" not in cmd and "-spd" not in cmd
    assert valore(cmd, "-r") == str(astap.BLIND_RADIUS_DEG)


# --- l'esito ------------------------------------------------------------------------------


def test_a_solution_comes_back_with_the_sky_it_found(tmp_path):
    """L'esito buono si legge dal `.ini`, e le sue chiavi sono le stesse dell'header di un
    FITS: il lettore del WCS che gia' esiste lo legge senza modifiche."""
    run = fake_run(scrive={tmp_path / "e.ini": INI_RISOLTO})
    esito = astap.solve(tmp_path / "x.fits", tmp_path / "e", exe="astap", run=run)
    assert esito.ok is True and esito.reason is None
    assert esito.ra_deg == pytest.approx(210.8014, abs=0.001)
    assert esito.dec_deg == pytest.approx(54.3491, abs=0.001)
    assert esito.scale_arcsec_px == pytest.approx(0.5206, abs=0.001)
    assert esito.rotation_deg == pytest.approx(84.35, abs=0.05)


@pytest.mark.parametrize(
    "codice, ini, atteso",
    [
        (1, INI_FALLITO, "no_stars"),
        (1, "PLTSOLVD=F\nERROR=No solution found.\n", "no_solution"),
        (1, "PLTSOLVD=F\n", "no_solution"),
        (1, None, "no_solution"),  # nemmeno il file di esito
    ],
)
def test_a_failure_becomes_a_closed_reason(tmp_path, codice, ini, atteso):
    """Un fallimento porta un CODICE chiuso, mai la frase di ASTAP: le frasi cambiano da una
    versione all'altra e finirebbero a schermo in inglese."""
    scrive = {tmp_path / "e.ini": ini} if ini is not None else None
    run = fake_run(codice=codice, scrive=scrive)
    esito = astap.solve(tmp_path / "x.fits", tmp_path / "e", exe="astap", run=run)
    assert esito.ok is False and esito.reason == atteso
    assert esito.reason in astap.REASONS


def test_a_solver_that_never_comes_back_is_a_reason(tmp_path):
    """Un solver che si pianta non deve piantare l'archivio: scade e diventa un motivo."""
    run = fake_run(esplode=TimeoutError("scaduto"))
    esito = astap.solve(tmp_path / "x.fits", tmp_path / "e", exe="astap", run=run)
    assert esito.ok is False and esito.reason == "timeout"


def test_without_astap_there_is_no_crash_only_a_reason(tmp_path):
    """Al primo avvio ASTAP puo' non esserci ancora: l'archivio funziona lo stesso e le pose
    restano da risolvere, con scritto perche'."""
    esito = astap.solve(tmp_path / "x.fits", tmp_path / "e", exe=None, run=fake_run())
    assert esito.ok is False and esito.reason == "astap_missing"


def test_a_file_that_is_not_there_is_a_reason(tmp_path):
    """Il disco esterno staccato non e' un errore di sistema: e' una posa che non si e'
    potuta leggere adesso."""
    run = fake_run(codice=1, scrive={tmp_path / "e.ini": "PLTSOLVD=F\nERROR=File not found.\n"})
    esito = astap.solve(tmp_path / "manca.fits", tmp_path / "e", exe="astap", run=run)
    assert esito.ok is False and esito.reason == "file_missing"


# --- HFD e stelle -------------------------------------------------------------------------


def test_the_quality_numbers_are_read_with_their_decimal_comma(tmp_path):
    """ASTAP stampa i numeri nel formato della macchina: su un computer italiano `9,1`. Letti
    col punto diventerebbero 91 o zero, in silenzio."""
    run = fake_run(stdout="HFD_MEDIAN=9,1\nSTARS=61\n")
    hfd, stelle = astap.analyse(tmp_path / "x.fits", exe="astap", run=run)
    assert hfd == pytest.approx(9.1) and stelle == 61

    run = fake_run(stdout="HFD_MEDIAN=3.42\nSTARS=1204\n")
    hfd, stelle = astap.analyse(tmp_path / "x.fits", exe="astap", run=run)
    assert hfd == pytest.approx(3.42) and stelle == 1204


def test_quality_numbers_that_do_not_arrive_stay_empty(tmp_path):
    """Nessun numero inventato: se ASTAP non li stampa, restano vuoti."""
    for uscita in ("", "roba a caso", "HFD_MEDIAN=\nSTARS=\n", "HFD_MEDIAN=boh\n"):
        assert astap.analyse(tmp_path / "x.fits", exe="astap", run=fake_run(stdout=uscita)) == (
            None,
            None,
        ), uscita


def test_the_analyse_pass_writes_nothing_next_to_the_frame(tmp_path):
    """`-analyse` e' l'unica strada per HFD e stelle che non lasci file nella cartella
    dell'utente: `-extract` ci scriverebbe un CSV accanto, ignorando `-o`."""
    run = fake_run(stdout="HFD_MEDIAN=4,0\nSTARS=100\n")
    astap.analyse(tmp_path / "x.fits", exe="astap", run=run)
    cmd = comando(run)
    assert "-analyse" in cmd and not any(c.startswith("-extract") for c in cmd)
    assert "-o" not in cmd  # non scrive niente, quindi non ha dove scrivere


# --- trovare l'eseguibile -------------------------------------------------------------------


def test_a_declared_solver_beats_the_automatic_search(tmp_path):
    """Un ASTAP dichiarato batte la ricerca automatica: e' la via d'uscita quando questa
    sbaglia.

    Qui si guarda il canale della **variabile d'ambiente**, che e' di chi lancia l'app; sopra di
    lui c'e' la preferenza scritta a schermo, che vince su tutto -- quella sta in
    `test_solver_missing.py`."""
    finto = tmp_path / "mio_astap.exe"
    finto.write_text("", encoding="utf-8")
    trovato = find_exe(env={"ASTROLOG_ASTAP": str(finto)}, which=lambda n: "/altro/astap")
    assert trovato == str(finto)

    # dichiarato ma inesistente: si dice che non c'e', non si ripiega di nascosto
    assert find_exe(env={"ASTROLOG_ASTAP": str(tmp_path / "no")}, which=lambda n: "/x") is None


def test_otherwise_the_solver_is_looked_for_on_the_path(tmp_path):
    assert find_exe(env={}, which=lambda n: "/usr/bin/astap_cli" if "cli" in n else None) == (
        "/usr/bin/astap_cli"
    )
    assert find_exe(env={}, which=lambda n: None, candidates=()) is None

    # e un posto d'installazione che esiste come CARTELLA non e' un eseguibile: la stessa
    # regola del percorso dichiarato, sull'altro ramo
    cartella = tmp_path / "astap"
    cartella.mkdir()
    assert find_exe(env={}, which=lambda n: None, candidates=(str(cartella),)) is None


def test_the_search_says_which_of_its_four_channels_answered(tmp_path):
    """**Dove** non basta: serve **da cosa**.

    "Trovato" senza dire da dove non si puo' smentire, e la ricerca automatica sbaglia proprio
    quando trova qualcosa -- un ASTAP vecchio rimasto nel PATH, o quello di un altro utente in un
    posto noto. Chi legge la sezione deve poter dire "no, non quello" senza indovinare quale dei
    quattro canali ha risposto."""
    esiste = tmp_path / "astap_cli.exe"
    esiste.write_text("", encoding="utf-8")
    mai = lambda _: None  # noqa: E731

    assert where_exe(str(esiste), env={}, which=mai, candidates=()) == (
        str(esiste),
        "declared",
    )
    assert where_exe(env={astap.ENV_EXE: str(esiste)}, which=mai, candidates=()) == (
        str(esiste),
        "env",
    )
    assert where_exe(env={}, which=lambda n: f"/usr/bin/{n}", candidates=()) == (
        "/usr/bin/astap_cli",
        "path",
    )
    assert where_exe(env={}, which=mai, candidates=(str(esiste),)) == (
        str(esiste),
        "known_place",
    )
    # e quando non c'e', non c'e' **nessun** canale: un motivo senza percorso sarebbe una storia
    assert where_exe(env={}, which=mai, candidates=()) == (None, None)
    # dichiarato e inesistente: niente ripiego di nascosto, nemmeno sul canale
    assert where_exe(str(tmp_path / "no"), env={}, which=lambda n: "/x") == (None, None)


def test_the_star_databases_are_the_ones_next_to_the_program(tmp_path):
    r"""ASTAP senza il suo catalogo stellare **non riconosce niente**: il programma parte, e ogni
    posa fallisce con `no_star_database`. E' l'errore di installazione piu' comune, perche' il
    catalogo e' un download separato, che va scelto e preso a mano.

    Dove sta lo dice l'autore: *"they can be placed anywhere as long as all files are in the same
    directory"* (hnsky.org/astap.htm) -- cioe' **accanto all'eseguibile**. Si riconosce dal
    **nome**, non dall'estensione: la sigla, un trattino basso, la zona di cielo. Quali sigle
    esistano lo dice `astap.DB_KINDS`, che e' la loro casa. Letto da un'installazione vera: 1476
    file `d80_0101.1476` e simili in `C:\Program Files\astap`, accanto ad `astap_cli.exe`."""
    cartella = tmp_path / "astap"
    cartella.mkdir()
    exe = cartella / "astap_cli.exe"
    for nome in ("astap_cli.exe", "d80_0101.1476", "d80_0102.1476", "v50_0101.1476"):
        (cartella / nome).write_text("", encoding="utf-8")
    # e cio' che ASTAP si porta dietro e **non** e' un catalogo stellare
    for nome in ("deep_sky.csv", "dcraw.exe", "astap_install.txt", "unins000.dat"):
        (cartella / nome).write_text("", encoding="utf-8")

    assert star_databases(exe) == ("d80", "v50")

    # un programma senza catalogo accanto: nessuno, e si dice
    sola = tmp_path / "sola"
    sola.mkdir()
    (sola / "astap_cli.exe").write_text("", encoding="utf-8")
    assert star_databases(sola / "astap_cli.exe") == ()

    # e senza programma non c'e' nemmeno la domanda
    assert star_databases(None) == ()


@pytest.mark.parametrize(
    "nome, atteso",
    [
        ("d80_0101.1476", "d80"),
        # l'estensione cambia col formato, la sigla no: si guarda il nome
        ("g05_2.001", "g05"),
        ("h17_9.290", "h17"),  # una sigla vecchia, ancora installata da chi non l'ha tolta
        ("W08_1.1476", "w08"),  # scompattato da un altro sistema: le maiuscole non contano
        # e i quasi-casi, che cadono sul pelo: e' li' che un riconoscitore sbagliato passa
        ("d8_0101.1476", None),  # una cifra sola
        ("d80_0101", None),  # nessuna estensione
        ("d80-0101.1476", None),  # trattino invece del trattino basso
        ("deep_sky.csv", None),  # cio' che ASTAP si porta dietro e catalogo non e'
        # e una sigla che non e' di nessun catalogo: senza questa riga, un file qualunque in una
        # cartella condivisa faceva dire "catalogo stellare: x99" a chi non ce l'ha
        ("x99_1.1476", None),
    ],
)
def test_a_catalogue_file_is_recognised_by_its_name(tmp_path, nome, atteso):
    """La sigla si legge dal **nome**, con le sue regole: due cifre, un trattino basso, e un
    punto dopo la zona di cielo. I casi che contano sono quelli che cadono sul pelo -- un nome
    che somiglia e non lo e', e uno che lo e' con un'estensione che non avevamo previsto."""
    cartella = tmp_path / "astap"
    cartella.mkdir()
    exe = cartella / "astap_cli.exe"
    exe.write_text("", encoding="utf-8")
    (cartella / nome).write_text("", encoding="utf-8")

    assert star_databases(exe) == ((atteso,) if atteso else ())


def test_the_catalogue_of_another_installation_is_not_yours(tmp_path):
    r"""**Si guarda solo accanto all'eseguibile**, ed e' una scelta, non una dimenticanza.

    Guardare anche nelle cartelle d'installazione note sembra piu' generoso e invece mente: su una
    macchina che ha ASTAP installato, un eseguibile indicato **altrove** risulterebbe col catalogo
    perche' quel catalogo e' di un altro programma -- e l'app direbbe "tutto a posto" proprio nel
    caso che questa funzione esiste per prendere. Trovato dal vivo: un ASTAP finto in una cartella
    vuota risultava col `d80` di `C:\Program Files\astap`.

    Il prezzo e' dichiarato: chi tiene il catalogo in un terzo posto si sente dire che manca. Un
    "ti manca" di troppo si corregge guardando; un "ce l'hai" falso si scopre a lettura finita."""
    altrove = tmp_path / "opt" / "astap"
    altrove.mkdir(parents=True)
    (altrove / "d50_0101.1476").write_text("", encoding="utf-8")
    lontano = tmp_path / "bin"
    lontano.mkdir()
    exe = lontano / "astap_cli"
    exe.write_text("", encoding="utf-8")

    assert star_databases(exe) == ()


def test_a_link_is_followed_to_where_the_program_really_is(tmp_path):
    """Se l'eseguibile trovato e' un **collegamento**, il catalogo sta dove punta. Senza
    scioglierlo si guarderebbe la cartella del collegamento -- vuota -- e si direbbe che manca a
    un'installazione che ce l'ha."""
    vera = tmp_path / "opt" / "astap"
    vera.mkdir(parents=True)
    exe = vera / "astap_cli"
    exe.write_text("", encoding="utf-8")
    (vera / "d50_0101.1476").write_text("", encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    collegamento = bin_dir / "astap_cli"
    try:
        collegamento.symlink_to(exe)
    except (OSError, NotImplementedError):
        pytest.skip("questo sistema non lascia creare collegamenti senza privilegi")

    assert star_databases(collegamento) == ("d50",)


def test_a_folder_that_is_not_there_is_no_catalogue_and_no_crash(tmp_path):
    """Il disco staccato, la cartella sparita, i permessi negati: nessun catalogo, non uno
    schianto. E' la stessa regola del resto dell'app -- un guasto di lettura non ferma la
    pagina -- e senza questa riga il ramo del `suppress` non e' mai stato visto verde per la sua
    ragione."""
    assert star_databases(tmp_path / "mai-esistita" / "astap_cli") == ()


def test_where_and_find_never_disagree(tmp_path):
    """`find_exe` e' `where_exe` senza il canale: scritte come due ricerche, un giorno una
    troverebbe cio' che l'altra no, e la sezione direbbe il contrario della corsa.

    I casi sono **tutti i rami della ricerca**, compresi i due che escono a mani vuote da una
    dichiarazione sbagliata: sono la regola piu' sottile del modulo -- un percorso scritto e
    inesistente ferma la ricerca invece di ripiegare -- ed e' li' che due funzioni rispezzate
    divergerebbero per prime."""
    esiste = tmp_path / "astap_cli"
    esiste.write_text("", encoding="utf-8")
    nulla = str(tmp_path / "non-c-e")
    trova = lambda n: f"/usr/bin/{n}"  # noqa: E731 - la ricerca automatica trova sempre qualcosa
    for caso in (
        {"declared": str(esiste), "env": {}, "which": trova},
        {"declared": nulla, "env": {}, "which": trova},
        {"env": {astap.ENV_EXE: str(esiste)}, "which": trova},
        {"env": {astap.ENV_EXE: nulla}, "which": trova},
        {"env": {}, "which": trova},
        {"env": {}, "which": lambda _: None, "candidates": (str(esiste),)},
        {"env": {}, "which": lambda _: None, "candidates": ()},
    ):
        assert find_exe(**caso) == where_exe(**caso)[0], caso


def test_the_command_line_binary_is_preferred_to_the_windowed_one(tmp_path):
    """`astap_cli` non apre finestre: su un NAS senza schermo e' l'unico che funziona."""
    visti = []

    def which(name):
        visti.append(name)
        return f"/usr/bin/{name}"

    find_exe(env={}, which=which)
    assert visti[0] == "astap_cli"
