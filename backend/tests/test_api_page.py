"""La pagina servita dal backend, e la chiave che le viene consegnata.

"L'app si apre e basta" (Marco, 13/9/2026): e' il backend a servire la pagina, e le passa la
chiave di avvio mentre gliela manda -- nessuno incolla niente, e la chiave non finisce in un link
ne' in una cronologia. Qui si prova che la consegna avviene **senza aprire un buco**: le rotte
dell'API continuano a pretendere la chiave come prima.
"""

import pytest
from fastapi.testclient import TestClient

from astrolog.api import page
from astrolog.api.app import TOKEN_HEADER, create_app

CHIAVE = "gettone-di-prova"  # noqa: S105 - e' il soggetto della prova, non un segreto vero
# La seconda chiave sta in una costante e non nella riga che la assegna: cosi' quella riga non
# contiene nessuna stringa, e la presa del cancello sui segreti resta **accesa** invece di essere
# disarmata con `segreto-ok`. Una presa di sicurezza si spegne una riga comoda per volta.
ALTRA_CHIAVE = "gettone-numero-due"  # noqa: S105 - come sopra
# La chiave **storta**: una virgoletta e un tag, cioe' cio' che chiuderebbe l'attributo a meta'.
# Quella vera non li produce (`secrets.token_urlsafe`), ed e' esattamente il punto -- una
# sicurezza che dipende di nascosto da come un'altra funzione genera i suoi caratteri non e' una
# sicurezza, e finche' nessun test le collegava togliere lo sfuggimento non faceva cadere niente.
STORTA = 'x"><script>y'
PAGINA = "<!doctype html><html><head><title>AstroLog</title></head><body></body></html>"


@pytest.fixture
def costruita(tmp_path):
    """La cartella dove vive la pagina costruita: la pagina e i file che carica.

    I file ci sono **apposta**: una pagina vera ne carica sempre, e un banco che li omettesse
    direbbe di si' a una fetta che li lascia fuori -- e' successo, e li' il browser non prendeva
    una pagina bianca ma un 401."""
    web = tmp_path / "web"
    (web / "assets").mkdir(parents=True)
    (web / "index.html").write_text(PAGINA, encoding="utf-8")
    (web / "assets" / "app-1a2b3c.js").write_text("console.log('astrolog')\n", encoding="utf-8")
    return web


def _client(db_path, costruita=None, token=CHIAVE):
    app = create_app(db_path, token=token, web_dir=costruita)
    return TestClient(app, base_url="http://localhost")


def test_the_backend_serves_the_page(db_path, costruita):
    """La pagina la serve il backend, dalla sua stessa origine: cosi' non serve ne' un secondo
    programma che la serva, ne' il permesso di parlare fra due origini diverse."""
    with _client(db_path, costruita) as c:
        risposta = c.get("/")
    assert risposta.status_code == 200
    assert "<title>AstroLog</title>" in risposta.text


def test_the_page_is_handed_the_key_so_nobody_has_to_paste_it(db_path, costruita):
    """La chiave arriva alla pagina **dentro la risposta**, non dal file su disco: il file
    costruito non la contiene, e non deve -- cambia a ogni avvio, e un file che la portasse
    sarebbe una chiave scritta su disco in chiaro, dentro un pacchetto che si distribuisce."""
    with _client(db_path, costruita) as c:
        servita = c.get("/").text
    assert CHIAVE in servita
    assert CHIAVE not in (costruita / "index.html").read_text(encoding="utf-8")


def test_where_there_is_no_key_the_page_carries_none(db_path, costruita):
    """Sul NAS la chiave non c'e' (la rete di casa e' fidata) e la pagina non ne porta nessuna:
    non si inventa un valore finto per riempire il posto."""
    with _client(db_path, costruita, token=None) as c:
        servita = c.get("/").text
    assert "astrolog-token" not in servita  # nessuna consegna, non "nessuna chiave che somigli"
    assert "<title>AstroLog</title>" in servita


def test_serving_the_page_does_not_open_a_hole_in_the_api(db_path, costruita):
    """**La prova che conta**: la pagina si serve senza chiave -- deve, altrimenti nessuno la
    potrebbe aprire -- ma le rotte dell'API continuano a pretenderla. Un'apertura fatta per
    comodita' della pagina sarebbe l'archivio aperto a qualunque programma della macchina."""
    with _client(db_path, costruita) as c:
        assert c.get("/").status_code == 200
        assert c.get("/api/health").status_code == 401
        assert c.get("/api/health", headers={TOKEN_HEADER: CHIAVE}).status_code == 200


def test_the_files_the_page_loads_are_served_without_the_key_too(db_path, costruita):
    """**Il difetto che questa prova esiste per prendere.** Una pagina vera carica il suo
    JavaScript e il suo foglio di stile, e il browser li chiede **senza header**: se non fossero
    aperti non prenderebbero un 404 -- prenderebbero un **401**, e la finestra resterebbe vuota
    senza dire perche'. Nello stesso test si riafferma che l'API, li' accanto, non si e' aperta."""
    with _client(db_path, costruita) as c:
        assert c.get("/assets/app-1a2b3c.js").status_code == 200
        assert c.get("/api/health").status_code == 401


def test_the_page_does_not_stay_in_the_browser_cache(db_path, costruita):
    """La pagina porta la chiave, quindi non deve restare nella cache su disco del browser:
    sarebbe il segreto scritto in un file, cioe' proprio cio' che l'iniezione evita."""
    with _client(db_path, costruita) as c:
        assert c.get("/").headers["cache-control"] == "no-store"


def test_the_key_is_injected_at_every_request(db_path, costruita):
    """La chiave si mette dentro **a ogni richiesta**, non una volta all'avvio: nasce con
    l'avvio, il file costruito non cambia mai, e una pagina tenuta da parte porterebbe per
    sempre la chiave del primo avvio."""
    with _client(db_path, costruita) as c:
        assert CHIAVE in c.get("/").text
        c.app.state.token = ALTRA_CHIAVE
        seconda = c.get("/", headers={TOKEN_HEADER: ALTRA_CHIAVE}).text
    assert ALTRA_CHIAVE in seconda and CHIAVE not in seconda


def test_a_key_with_a_quote_in_it_does_not_escape_the_attribute(db_path, costruita):
    """La chiave si **sfugge** prima di entrare nell'attributo HTML.

    Oggi quella vera non ha caratteri da sfuggire -- `secrets.token_urlsafe` non li produce -- ma
    e' una sicurezza che dipende di nascosto da come un'altra funzione, in un altro file, genera
    i suoi caratteri: nessun test collegava le due cose, e togliere lo sfuggimento non faceva
    cadere niente (provato: il sabotaggio sopravviveva). Qui la chiave porta una virgoletta, e
    l'attributo deve restare un attributo invece di chiudersi a meta'."""
    with _client(db_path, costruita, token=STORTA) as c:  # noqa: S106 - l'esca della prova
        servita = c.get("/", headers={TOKEN_HEADER: STORTA}).text
    assert "<script>y" not in servita  # la virgoletta non ha chiuso l'attributo
    assert "&quot;&gt;&lt;script&gt;y" in servita


def test_a_page_without_a_head_still_gets_the_key(db_path, tmp_path):
    """Una pagina che non ha `<head>` riceve la chiave lo stesso, in testa al documento: senza
    questo ramo il build di domani potrebbe togliere quel segno e la chiave sparirebbe in
    silenzio -- la pagina si aprirebbe, e nessuna delle sue richieste funzionerebbe."""
    web = tmp_path / "nuda"
    web.mkdir()
    (web / "index.html").write_text("<html><body>senza testa</body></html>", encoding="utf-8")
    with _client(db_path, web) as c:
        servita = c.get("/").text
    assert CHIAVE in servita and "senza testa" in servita


def test_the_page_is_not_an_api_route(db_path, costruita):
    """La pagina sta fuori da `/api/v1` e fuori dall'OpenAPI: i tipi del frontend si **generano**
    da quello schema, e un file HTML in mezzo ai modelli sarebbe un tipo che non descrive niente."""
    with _client(db_path, costruita) as c:
        schema = c.get("/openapi.json").json()
    assert "/" not in schema["paths"]


def test_without_a_build_the_app_still_works(db_path, tmp_path):
    """Senza la pagina costruita l'app parte e l'API funziona: chi lavora solo sul backend non
    deve costruire il frontend per provarlo, e il primo avvio di chi clona non esplode.

    La cartella vuota se la **costruisce questa prova**, invece di contare sul fatto che la
    pagina non sia stata costruita sulla macchina: prima lo faceva, e passava per un'assenza --
    il giorno che qualcuno ha lanciato `npm run build` e' diventata rossa senza che niente fosse
    rotto. Una prova che dipende dallo stato della macchina non prova la regola che dichiara."""
    vuota = tmp_path / "mai-costruita"
    vuota.mkdir()
    with _client(db_path, vuota) as c:
        assert c.get("/api/health", headers={TOKEN_HEADER: CHIAVE}).status_code == 200
        assert c.get("/").status_code == 404


def test_the_page_lives_inside_the_package(db_path):
    """La pagina costruita sta **dentro** il pacchetto, ed e' cio' che `backend/pyproject.toml`
    copre con `web/**/*`. Se domani qualcuno la spostasse fuori, quella riga smetterebbe di
    coprirla e nessuno se ne accorgerebbe fino al giorno del pacchetto -- il giorno che quel
    commento dice di voler evitare. Che la ruota la porti davvero non si puo' provare finche'
    la cartella non esiste: qui si inchioda l'unica meta' che oggi puo' divergere."""
    assert (page.WEB_DIR.parent.name, page.WEB_DIR.name) == ("astrolog", "web")


def test_a_path_that_only_looks_like_the_assets_is_not_open(db_path, costruita):
    """`/assets` si apre per **prefisso**, e un prefisso senza barra aprirebbe anche
    `/assets-altro`: oggi li' non c'e' niente, ma e' la stessa famiglia del difetto per cui
    questa guardia esiste -- un confronto piu' largo di quanto qualcuno creda."""
    with _client(db_path, costruita) as c:
        assert c.get("/assets-altro/x.js").status_code == 401


def test_reloading_a_page_address_opens_the_app(db_path, costruita):
    """**Il difetto che questa prova esiste per prendere**, visto collaudando il 14/9/2026:
    `/da-confermare` rispondeva **401** con un JSON grezzo. Ricaricare la pagina, tornarci da un
    segnalibro o aprirne l'indirizzo non apriva l'app -- mentre l'intestazione del router promette
    il contrario ("un collegamento che si manda a qualcuno"), che e' la ragione per cui il router
    e' entrato. Sul NAS, dove l'app si usa da tablet, ricaricare e' il gesto piu' comune."""
    with _client(db_path, costruita) as c:
        risposta = c.get("/da-confermare")
    assert risposta.status_code == 200
    assert "<title>AstroLog</title>" in risposta.text
    assert CHIAVE in risposta.text  # con la chiave dentro, come la pagina di casa


def test_an_address_the_router_does_not_know_yet_still_opens_the_app(db_path, costruita):
    """Gli indirizzi delle pagine li conosce **il router**, che vive nel frontend: il backend non
    ne tiene l'elenco, altrimenti una pagina nuova risponderebbe 404 finche' qualcuno non si
    ricorda di aggiungerla anche qui -- lo stesso fatto in due case, e il 404 arriverebbe
    all'utente, non a chi ha dimenticato. Quindi un indirizzo di pagina apre l'app, e a dire
    "questa pagina non esiste" tocca al router."""
    with _client(db_path, costruita) as c:
        assert c.get("/una-pagina-di-domani").status_code == 200


def test_serving_more_addresses_does_not_open_the_api(db_path, costruita):
    """La contropartita, ed e' la meta' che conta: servire la pagina su piu' indirizzi **non apre
    un buco**. L'API resta chiusa senza chiave, e un percorso con un'estensione non e' un
    indirizzo di pagina -- e' un file, e gli unici file aperti restano quelli della pagina."""
    with _client(db_path, costruita) as c:
        assert c.get("/api/health").status_code == 401
        assert c.get("/api/v1/review").status_code == 401
        assert c.get("/assets-altro/x.js").status_code == 401
        assert c.get("/api").status_code == 401  # nemmeno senza la barra: non e' una pagina


def test_on_the_nas_where_there_is_no_key_a_file_is_still_not_a_page(db_path, costruita):
    """Sul NAS la chiave non c'e' -- la rete di casa e' fidata -- quindi il middleware non ferma
    niente, e **l'unica guardia che resta e' quella dentro il ripiego**: quella che distingue un
    indirizzo di pagina da un file. Senza di lei `/privato.json` (rimando-ok: e' un indirizzo che
    **non deve esistere**, ed e' il soggetto della prova) riceverebbe la pagina dell'app con un
    200: non un dato che esce, ma una risposta che mente su cosa c'e' li'.

    Misurata da un audit il 14/9/2026: togliendo quelle due righe la suite restava **tutta
    verde**, perche' ogni altra prova gira con la chiave e il 401 del middleware arriva prima.
    Era una regola scritta in un commento; questa e' la sua macchina."""
    with _client(db_path, costruita, token=None) as c:
        assert c.get("/da-confermare").status_code == 200
        assert c.get("/assets-altro/x.js").status_code == 404
        assert c.get("/privato.json").status_code == 404


def test_without_a_build_a_page_address_says_the_same_as_the_home(db_path, tmp_path):
    """Senza la pagina costruita un indirizzo di pagina risponde come `/`: **404**
    `page_not_built`, non una finestra vuota e non un 401 -- chi lavora solo sul backend deve
    poter leggere il perche' invece di indovinarlo."""
    vuota = tmp_path / "mai-costruita"
    vuota.mkdir()
    with _client(db_path, vuota) as c:
        assert c.get("/da-confermare").status_code == 404


def test_no_page_address_enters_the_openapi(db_path, costruita):
    """Nemmeno il ripiego entra nello schema: da li' si **generano** i tipi e le funzioni del
    client, e una rotta che risponde HTML su qualunque indirizzo diventerebbe una funzione del
    client che restituisce una pagina."""
    with _client(db_path, costruita) as c:
        schema = c.get("/openapi.json").json()
    assert [p for p in schema["paths"] if not p.startswith("/api/")] == []


def test_the_names_in_the_openapi_are_readable(db_path):
    """Dall'OpenAPI si **generano** i tipi e le funzioni del client: se i nomi delle operazioni
    sono quelli di default, il frontend si scrive contro identificatori come
    `review_api_v1_review_get`. I nomi si scelgono qui, una volta, prima che qualcuno ci scriva
    sopra: dopo, rinominarli e' un cambiamento che rompe chi li usa."""
    with _client(db_path) as c:
        schema = c.get("/openapi.json").json()
    operazioni = [d["operationId"] for p in schema["paths"].values() for d in p.values()]
    assert "review" in operazioni
    assert not any("_api_v1_" in o for o in operazioni)


def test_the_names_in_the_openapi_are_unique(db_path):
    """E devono restare **distinti**: il generatore ne ricava una funzione per operazione, e due
    nomi uguali diventano una funzione sola che ne nasconde un'altra -- in silenzio, perche' lo
    schema e' valido lo stesso. Due rotte che si chiamano come la loro funzione rendono la
    collisione possibile: questa e' la macchina che se ne accorge."""
    with _client(db_path) as c:
        schema = c.get("/openapi.json").json()
    operazioni = [d["operationId"] for p in schema["paths"].values() for d in p.values()]
    assert len(operazioni) == len(set(operazioni)), sorted(operazioni)
