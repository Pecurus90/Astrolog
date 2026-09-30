"""Quando il solver non c'e', l'app lo dice -- e ti lascia dire dove sta.

Senza ASTAP l'archivio si costruisce lo stesso: i file entrano, i nomi si mettono in ordine, le
ore si contano. Ma **non si sa cosa hai ripreso**, e questo va detto prima che qualcuno aspetti
mezz'ora una scansione che non riconoscera' niente. Il solver in se' (come si lancia, come si
legge la sua uscita) sta in `test_astap.py`.
"""

from pathlib import Path

from astrolog import astap
from astrolog.astap import find_exe as cerca_davvero
from astrolog.astap import where_exe as cerca_col_canale
from astrolog.db import config
from astrolog.db.connect import connect
from astrolog.spine.scan import scan_folder
from astrolog.spine.solve import solve_frames
from conftest import add_folder, write_light

# `cerca_davvero` e' catturata **all'import**, prima che il recinto della suite
# (`conftest.dentro_il_recinto`) sostituisca `astap.find_exe` con "non c'e' nessun solver". Le
# prove che guardano la ricerca in se' vogliono quella vera; quelle che guardano cosa fa l'app
# quando manca, la finta.


def settings_out(client):
    r = client.get("/api/v1/settings")
    assert r.status_code == 200, r.text
    return r.json()


def test_the_app_says_when_the_solver_is_missing(client, monkeypatch):
    """`GET /settings` dichiara `no_solver` fra le cose che mancano, con un codice e non una
    frase -- come fa gia' col sito di casa. E' la riga che il primo avvio guarda per decidere se
    fare la domanda in piu'."""
    monkeypatch.setattr(astap, "find_exe", lambda *a, **k: None)
    assert "no_solver" in settings_out(client)["missing"]

    monkeypatch.setattr(astap, "find_exe", lambda *a, **k: "C:/astap/astap.exe")
    assert "no_solver" not in settings_out(client)["missing"]


def test_the_declared_path_wins_over_the_automatic_search(tmp_path):
    """Chi ha gia' il suo ASTAP dice dove sta, e vince: la ricerca automatica sbaglia -- una
    copia vecchia in un'altra cartella, un nome diverso -- e quella e' la via d'uscita."""
    vero = tmp_path / "astap_cli.exe"
    vero.write_text("x", encoding="utf-8")
    altro = tmp_path / "trovato_a_caso.exe"
    altro.write_text("x", encoding="utf-8")

    assert cerca_davvero(declared=str(vero), env={}, which=lambda _n: str(altro)) == str(vero)


def test_a_declared_path_that_does_not_exist_is_nothing(tmp_path):
    """Dichiarato ma inesistente vale **niente**, non un ripiego di nascosto: chi ha scritto quel
    percorso deve accorgersi che e' sbagliato, invece di vedere l'app usare un altro solver e
    chiedersi perche' i risultati cambiano.

    La ricerca automatica qui **trova** qualcosa (`which`): e' l'unico modo di provare che il
    ripiego non scatta -- con una ricerca che non trova niente il `None` sarebbe uscito lo
    stesso, e il test sarebbe passato anche togliendo la regola.

    Questo e' il canale della **preferenza** (`declared`, scritta a schermo); il gemello sul
    canale della variabile d'ambiente sta in `test_astap.py`, dentro
    `test_a_declared_solver_beats_the_automatic_search`."""
    altro = tmp_path / "trovato_a_caso.exe"
    altro.write_text("x", encoding="utf-8")
    assert (
        cerca_davvero(declared=str(tmp_path / "non-c-e.exe"), env={}, which=lambda _n: str(altro))
        is None
    )


def test_a_declared_folder_is_not_a_solver(tmp_path):
    r"""Una **cartella** non e' un solver, neanche se esiste.

    Trovato dal vivo: indicando `C:\Program Files\astap` -- la cartella, non il programma
    dentro -- l'app rispondeva "Trovato" e poi avrebbe provato a lanciare una directory a ogni
    posa. E' l'errore piu' facile da fare, perche' quella cartella esiste davvero."""
    cartella = tmp_path / "astap"
    cartella.mkdir()

    assert cerca_davvero(declared=str(cartella), env={}, which=lambda _n: None) is None


def test_the_path_is_taken_as_windows_copies_it(tmp_path):
    """Il percorso si accetta **come lo incolla l'utente**: con le virgolette intorno e con gli
    spazi.

    Su Windows *Copia come percorso* (Shift + tasto destro) mette il percorso **fra
    virgolette**, ed e' il modo piu' comune di prenderlo senza scriverlo a mano. Rifiutarlo
    voleva dire mandare in faccia "li' non c'e' ASTAP" a chi aveva indicato il programma
    giusto, con la frase che parla d'altro (la cartella al posto del file)."""
    vero = tmp_path / "astap_cli.exe"
    vero.write_text("x", encoding="utf-8")

    for incollato in (f'"{vero}"', f"  {vero}  ", f"{vero}\n"):
        assert cerca_davvero(declared=incollato, env={}, which=lambda _n: None) == str(vero)


def test_the_declared_path_wins_over_the_environment_variable(tmp_path):
    """La preferenza scritta nell'app batte `ASTROLOG_ASTAP`: chi cambia solver lo fa a schermo,
    e non deve scoprire che una variabile d'ambiente messa mesi fa comanda ancora."""
    mio = tmp_path / "quello_che_voglio.exe"
    mio.write_text("x", encoding="utf-8")
    altro = tmp_path / "da_ambiente.exe"
    altro.write_text("x", encoding="utf-8")

    trovato = cerca_davvero(
        declared=str(mio), env={astap.ENV_EXE: str(altro)}, which=lambda _n: None
    )
    assert trovato == str(mio)


def test_the_preference_is_a_closed_key_with_its_factory_value():
    """Il percorso del solver e' una preferenza come le altre: chiave chiusa, tipo e valore di
    fabbrica in una casa sola. Senza, sarebbe una stringa che chiunque scrive dove capita."""
    assert config.KEYS["astap_path"][0] is str
    assert config.defaults()["astap_path"] is None


def test_writing_the_path_turns_the_warning_off(client, tmp_path, monkeypatch):
    """Scritto il percorso, l'avviso si spegne nella stessa risposta: e' cio' che fa sparire il
    passo del primo avvio senza che l'utente debba ricaricare per sapere se ha indovinato."""
    vero = tmp_path / "mio_astap.exe"
    vero.write_text("x", encoding="utf-8")
    monkeypatch.setattr(astap, "find_exe", cerca_davvero)  # quella vera, non quella del recinto
    r = client.patch("/api/v1/settings", json={"values": {"astap_path": str(vero)}})

    assert r.status_code == 200, r.text
    assert "no_solver" not in r.json()["missing"]
    assert Path(settings_out(client)["values"]["astap_path"]) == vero


def test_at_empty_hands_the_route_says_nothing_found(client):
    """**A mani vuote**: niente dichiarato, niente trovato. E' lo stato di chiunque al primo
    avvio, e l'unico test che passa dalla ricerca **del recinto** invece di rimettere quella vera.

    Serve a due cose, e la seconda e' il punto: prova che la sezione regge lo stato vuoto, e
    **tiene il recinto**. Togliendo `where_exe` da `conftest.dentro_il_recinto`, questa prova fa
    partire una ricerca vera sul PATH della macchina di chi sviluppa -- e su una macchina con
    ASTAP installato diventa rossa. Senza, quella riga del recinto non dimostra niente."""
    detto = client.get("/api/v1/solver")
    assert detto.status_code == 200, detto.text
    assert detto.json() == {"path": None, "source": None, "declared": None, "databases": []}


def test_astap_without_its_catalogue_is_a_thing_that_is_missing(client, tmp_path, monkeypatch):
    """**ASTAP senza catalogo stellare parte e non riconosce niente**: ogni posa fallisce con
    `no_star_database` e la corsa si ferma alla prima. E' l'errore di installazione piu' comune --
    il catalogo e' un download separato, che va scelto e preso a mano -- e finora si scopriva da
    una scansione tornata a mani vuote.

    Sta fra le cose che mancano, accanto al sito e al solver, perche' e' la stessa domanda: cosa
    manca all'app per fare il suo mestiere, detto **prima** di farlo aspettare."""
    cartella = tmp_path / "astap"
    cartella.mkdir()
    exe = cartella / "astap_cli.exe"
    exe.write_text("", encoding="utf-8")
    monkeypatch.setattr(astap, "where_exe", lambda *_a, **_k: (str(exe), "path"))
    monkeypatch.setattr(astap, "find_exe", lambda *_a, **_k: str(exe))

    manca = settings_out(client)["missing"]
    assert "no_star_database" in manca
    assert "no_solver" not in manca  # il programma c'e': l'allarme e' uno solo

    (cartella / "d80_0101.1476").write_text("", encoding="utf-8")
    assert "no_star_database" not in settings_out(client)["missing"]


def test_without_astap_nobody_complains_about_its_catalogue(client, monkeypatch):
    """Chi ASTAP non ce l'ha non si sente dire **anche** che gli manca il catalogo: e' il catalogo
    di un programma che non ha, e due allarmi per un problema solo mandano a cercare due cose."""
    monkeypatch.setattr(astap, "where_exe", lambda *_a, **_k: (None, None))
    manca = settings_out(client)["missing"]
    assert "no_solver" in manca
    assert "no_star_database" not in manca


def test_the_route_says_which_catalogues_are_installed(client, tmp_path, monkeypatch):
    """Quali cataloghi ci sono si legge: sapere **che** c'e' non basta a chi ne ha scaricato uno
    piccolo e si chiede perche' certe pose non si risolvono."""
    cartella = tmp_path / "astap"
    cartella.mkdir()
    exe = cartella / "astap_cli.exe"
    exe.write_text("", encoding="utf-8")
    for nome in ("d80_0101.1476", "v50_0101.1476"):
        (cartella / nome).write_text("", encoding="utf-8")
    monkeypatch.setattr(astap, "where_exe", lambda *_a, **_k: (str(exe), "path"))

    assert client.get("/api/v1/solver").json()["databases"] == ["d80", "v50"]


def test_the_route_says_where_the_solver_is_and_from_which_channel(client, tmp_path, monkeypatch):
    """La sezione *Il riconoscitore* non chiede "c'e'?" ma "**dove**, e da cosa l'hai dedotto?".

    Senza il canale, "trovato" non si puo' smentire: la ricerca automatica sbaglia proprio quando
    trova qualcosa, e chi guarda deve poter dire "no, non quello"."""
    vero = tmp_path / "astap_cli.exe"
    vero.write_text("x", encoding="utf-8")
    monkeypatch.setattr(astap, "where_exe", cerca_col_canale)  # quella vera, non quella del recinto

    client.patch("/api/v1/settings", json={"values": {"astap_path": str(vero)}})
    detto = client.get("/api/v1/solver")
    assert detto.status_code == 200, detto.text
    assert Path(detto.json()["path"]) == vero
    assert detto.json()["source"] == "declared"
    assert Path(detto.json()["declared"]) == vero


def test_a_path_that_leads_nowhere_stays_on_screen(client, tmp_path, monkeypatch):
    """Un percorso scritto e sbagliato **resta a schermo**: e' l'unica cosa che si puo'
    correggere, e nasconderlo lascerebbe una sezione che dice "non trovato" senza dire perche'."""
    monkeypatch.setattr(astap, "where_exe", cerca_col_canale)
    sbagliato = str(tmp_path / "non-c-e.exe")
    client.patch("/api/v1/settings", json={"values": {"astap_path": sbagliato}})

    detto = client.get("/api/v1/solver").json()
    assert detto["path"] is None and detto["source"] is None
    assert detto["declared"] == sbagliato


def test_looking_for_it_proposes_without_writing(client, tmp_path, monkeypatch):
    """*Cercalo tu* **propone e basta**: sovrascrivere di nascosto il percorso scritto a mano
    toglierebbe l'unica via d'uscita quando questa ricerca prende il programma sbagliato.

    Qui la preferenza punta a un percorso sbagliato e la ricerca automatica trova un altro
    programma: la rotta lo propone, e la preferenza **resta com'era**."""
    altro = tmp_path / "astap_cli"
    altro.write_text("x", encoding="utf-8")
    sbagliato = str(tmp_path / "non-c-e.exe")
    client.patch("/api/v1/settings", json={"values": {"astap_path": sbagliato}})
    monkeypatch.setattr(astap, "where_exe", lambda *a, **k: (str(altro), "path"))

    proposto = client.post("/api/v1/solver/search")
    assert proposto.status_code == 200, proposto.text
    assert Path(proposto.json()["path"]) == altro
    assert proposto.json()["source"] == "path"
    # e nessuno ha scritto niente: la preferenza e' quella di prima
    assert settings_out(client)["values"]["astap_path"] == sbagliato


def test_looking_for_it_ignores_what_is_declared(client, tmp_path, monkeypatch):
    """Cercare **ignorando la preferenza** e' il punto: con quella in mano la ricerca tornerebbe
    sempre cio' che l'utente ha gia' scritto, e il tasto non servirebbe a niente."""
    dichiarato = tmp_path / "quello_scritto.exe"
    dichiarato.write_text("x", encoding="utf-8")
    client.patch("/api/v1/settings", json={"values": {"astap_path": str(dichiarato)}})
    visti = []

    def spia(declared=None, **_k):
        visti.append(declared)
        return None, None

    monkeypatch.setattr(astap, "where_exe", spia)
    client.post("/api/v1/solver/search")
    assert visti == [None], visti


def test_the_run_launches_the_path_written_in_settings(db_path, tmp_path, monkeypatch):
    """La corsa lancia **quel** percorso, non uno cercato per conto suo.

    E' la meta' che conta: senza questa prova la preferenza sarebbe un campo che si compila,
    spegne l'avviso, e non cambia niente di cio' che l'app fa davvero -- e nessuno se ne
    accorgerebbe, perche' ogni altra prova dello stadio gli passa l'eseguibile a mano."""
    mio = tmp_path / "mio_astap.exe"
    mio.write_text("x", encoding="utf-8")
    write_light(tmp_path / "lib" / "a.fits")
    monkeypatch.setattr(astap, "find_exe", cerca_davvero)  # quella vera, non quella del recinto
    lanciati = []

    def spia(cmd, timeout_s):
        lanciati.append(cmd)
        return 1, ""  # non risolve: qui conta chi e' stato lanciato, non cosa ha trovato

    conn = connect(db_path)
    try:
        list(scan_folder(conn, add_folder(conn, tmp_path / "lib")))
        config.write(conn, "astap_path", str(mio))
        list(solve_frames(conn, run=spia, cache=tmp_path / "cache"))
    finally:
        conn.close()

    assert [c[0] for c in lanciati] == [str(mio)]
