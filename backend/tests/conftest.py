"""L'attrezzatura comune dei test: il recinto, i DB di prova, i FITS veri, il banco della pagina.

I FITS di prova si fabbricano con astropy in una cartella temporanea (mai FITS finti di sole
card ASCII: astropy non li legge). Il DB nasce dallo schema unico e da nient'altro.
"""

import hashlib
import os
import shutil
import socket
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from astropy.io import fits
from fastapi.testclient import TestClient

from astrolog import astap, place
from astrolog.api.app import create_app
from astrolog.catalog import bundle, load
from astrolog.db.connect import connect, create_database
from astrolog.spine import solve_store, stages, typeless_folders
from astrolog.spine.identify import identify_frames
from astrolog.spine.normalize import normalize_frames
from astrolog.spine.scan import scan_folder
from astrolog.weather import climate, forecast, history, meteoblue, sky

real_bundle = bundle.path  # catturato prima del recinto della suite


class SuiteInRete(BaseException):
    """Una prova ha chiamato un servizio vero senza fingerlo (`dentro_il_recinto`)."""


# I moduli che scaricano, ognuno col suo `_fetch` che le prove sostituiscono. Che l'elenco sia
# completo lo tiene `test_place.test_every_module_that_downloads_is_fenced`, dai sorgenti.
SCARICANO = (place, climate, forecast, history, meteoblue, sky)


@pytest.fixture(autouse=True)
def dentro_il_recinto(monkeypatch, tmp_path):
    r"""La suite non esce di casa: **non lancia ASTAP**, **non scrive nella cartella dati vera**
    e **non apre la rete**.

    Vale per tutti i test, non per quelli del solver: e' una rotta dell'API che ha portato il
    solve dentro la suite (`run.queue` lo accoda), e li' nessuno inietta niente. Senza questo
    recinto la suite lanciava il solver installato sulla macchina di chi sviluppa -- ricerche
    cieche da 60 s di tetto -- e gli faceva scrivere in `%LOCALAPPDATA%\AstroLog`, cioe' nella
    cartella dati dell'utente. Le due ricerche tornano "niente": e' il caso "ASTAP non c'e'
    ancora", che e' anche il primo avvio vero di chiunque. **Sono due** perche' una dice il
    percorso e l'altra anche il canale, e guardano tutte e due il disco e il PATH: sostituirne una
    sola lascerebbe l'altra a leggere la macchina di chi sviluppa. Che questa riga serva lo tiene
    fermo `test_at_empty_hands_the_route_says_nothing_found` -- **su una macchina con ASTAP
    installato**, dove senza la riga diventa rosso. Su una pulita, e in CI, resta verde: quella
    meta' e' dichiarata invece che nascosta, perche' il recinto promette piu' della sua guardia."""
    monkeypatch.setenv("ASTROLOG_DATA_DIR", str(tmp_path / "dati"))
    # E nemmeno il catalogo vero: 22.080 voci per ogni `create_app` sono diciotto secondi
    # regalati alla suite, e il cancello ha un tetto. Chi lo vuole lo passa a mano
    # (`test_catalog`) o cattura la funzione vera all'import (`test_perf_catalog`).
    monkeypatch.setattr(bundle, "path", lambda: None)
    monkeypatch.setattr(astap, "find_exe", lambda *a, **k: None)
    monkeypatch.setattr(astap, "where_exe", lambda *a, **k: (None, None))

    def boom(cmd, timeout_s):
        raise AssertionError(f"la suite ha lanciato ASTAP davvero: {cmd}")

    monkeypatch.setattr(astap, "_run", boom)

    # **E nemmeno la rete.** L'app gira su un NAS in una casa senza collegamento e su un portatile
    # in montagna: cio' che scarica non e' lento, e' rotto. Le effemeridi in particolare vivono
    # solo perche' `astrolog.ephemeris` disinnesca il download di astropy all'import -- e senza
    # questo recinto quella riga si poteva togliere lasciando la suite verde, perche' la macchina
    # di chi sviluppa la rete ce l'ha. Il recinto sta qui e non nel file di chi l'ha introdotta:
    # chi lo mette li' protegge se stesso e lascia scoperti gli altri.
    # **Il giro di casa resta aperto, e non e' rete.** Su Windows `asyncio` sveglia il proprio
    # ciclo con una coppia di socket verso 127.0.0.1, perche' li' non esiste una pipe che il
    # selettore sappia guardare (`proactor_events._make_self_pipe` -> `socket.socketpair`).
    # Chiuderlo fermerebbe ogni prova che monta l'app.
    # **I due recinti di rete alzano un errore che non e' un `Exception`, ed e' voluto**: l'app
    # cattura qualunque guasto per dire "servizio non raggiungibile" (`net.ask_why`), e un
    # `AssertionError` ci finiva dentro -- la prova restava verde e muta. Cosi' l'attraversa.
    def niente_rete(self, indirizzo, *resto):
        dove = indirizzo[0] if isinstance(indirizzo, tuple) else indirizzo
        if dove in ("127.0.0.1", "::1"):
            return vero_connect(self, indirizzo, *resto)
        raise SuiteInRete(f"la suite ha aperto la rete davvero: {indirizzo}")

    vero_connect = socket.socket.connect
    monkeypatch.setattr(socket.socket, "connect", niente_rete)

    # **Chi scarica si ferma prima di cercare il nome del servizio**: il recinto dei socket
    # ferma la connessione, ma la risoluzione del nome esce lo stesso. Chi collauda lo
    # scaricamento vero lo rimette da se', con `urlopen` finto (`test_place.py`).
    def niente_scaricamento(url, *resto, **chiavi):
        raise SuiteInRete(f"la suite ha chiamato la rete: {url}")

    for modulo in SCARICANO:
        monkeypatch.setattr(modulo, "_fetch", niente_scaricamento)
    # Il freno di una ricerca al secondo non rallenta la suite: chi lo prova lo rimette.
    monkeypatch.setattr(place, "SEARCH_MIN_INTERVAL_S", 0)
    monkeypatch.setattr(place, "_last_search", 0.0)


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "astrolog.db"
    create_database(path)
    return path


@pytest.fixture(scope="session")
def _catalog_template(tmp_path_factory):
    """Un DB col catalogo vero dentro, costruito **una volta** per tutta la suite.

    Le 22.080 voci costano 0,27 s a caricarle, e a chiederle sono decine di test: ricaricarle
    per ognuno vuol dire una dozzina di secondi su un cancello che ne ha sessanta in tutto
    (misurato: la suite passa da 53 a 35 secondi). I test non se lo passano, lo **copiano**
    (`db_path_col_catalogo`): qui si scrive, e due test che si passassero le righe scritte non
    sarebbero piu' due test."""
    path = tmp_path_factory.mktemp("catalogo") / "modello.db"
    create_database(path)
    conn = connect(path)
    try:
        assert load.load_catalog(conn, real_bundle()) > 20000
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")  # tutto nel .db: e' un file che si copia
    finally:
        conn.close()
    return path


@pytest.fixture
def db_path_col_catalogo(tmp_path, _catalog_template):
    """Un DB tutto suo col catalogo gia' dentro: una copia di file, non un caricamento."""
    # un nome diverso da quello di `db_path`: chiederli tutti e due nello stesso test farebbe
    # esplodere `create_database` su un file che c'e' gia', e l'errore non direbbe perche'
    path = tmp_path / "astrolog_col_catalogo.db"
    shutil.copy(_catalog_template, path)
    return path


@pytest.fixture
def archivio(db_path_col_catalogo):
    """Un DB col catalogo vero dentro. La connessione e' di funzione e il DB e' una copia sua:
    qui si SCRIVE, e due test che si passassero le righe scritte non sarebbero piu' due test."""
    conn = connect(db_path_col_catalogo)
    yield conn
    conn.close()


@pytest.fixture
def conn(db_path):
    c = connect(db_path)
    yield c
    c.close()


def populate(db_path, root):
    """Scansiona, normalizza e identifica fuori dall'app: la pagina si guarda su un archivio
    gia' fatto. Chi vuole anche il catalogo parte da `db_path_col_catalogo`."""
    conn = connect(db_path)
    try:
        list(scan_folder(conn, add_folder(conn, root)))
        list(normalize_frames(conn))
        # Le pose dell'archivio sintetico non hanno cielo: il solver non gira nella suite. Si
        # toccano solo quelle che il solver avrebbe davvero preso (`stages.ready`), e "stelle ma
        # nessuna soluzione" e' il cielo che non sa dire: un frame senza tipo resta una domanda.
        for frame_id in stages.ready(conn, "solve"):
            stages.set_status(conn, frame_id, "solve", "failed", reason="no_solution")
        typeless_folders.write(conn)  # come a fine cielo
        list(identify_frames(conn))
    finally:
        conn.close()


@pytest.fixture
def client_vuoto(db_path):
    """L'app a mani vuote: database nuovo, nessuna cartella, nessuna posa. E' il primo avvio
    vero di chiunque."""
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def rete_giu(monkeypatch):
    """Da qui in poi nessun servizio risponde: e' il caso del sito buio senza rete. Una funzione e
    non solo una fixture perche' c'e' chi la stacca a meta' prova."""

    def down(url, *resto, **chiavi):
        raise TimeoutError("rete assente")

    for modulo in SCARICANO:
        monkeypatch.setattr(modulo, "_fetch", down)


@pytest.fixture
def offline(monkeypatch):
    rete_giu(monkeypatch)


@pytest.fixture
def client(db_path, tmp_path):
    # l'import sta qui dentro perche' `synthetic` importa `write_fits` da questo file: in testa
    # sarebbe un giro chiuso, e nessuno dei due modulo si caricherebbe
    from synthetic import build_archive

    build_archive(tmp_path / "lib")
    populate(db_path, tmp_path / "lib")
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        yield c


def rows(conn, sql, args=()):
    return [dict(r) for r in conn.execute(sql, args)]


# Cio' che un attacco scriverebbe al posto di una chiave: lo usa chi prova che un valore
# arrivato da fuori non diventa mai un pezzo di SQL. Sta qui e non nei due file di prova
# perche' la marca che lo dichiara voluto vale sulla riga, e due righe sono due case.
ORDINE_OSTILE = "o.id; DROP TABLE objects"  # ddl-ok: input ostile, non SQL nostro


def one(conn, sql, args=()):
    r = conn.execute(sql, args).fetchone()
    return None if r is None else r[0]


def frame_by_file(conn, name):
    return conn.execute(
        "SELECT f.* FROM frames f JOIN positions p ON p.frame_id = f.id WHERE p.rel_path LIKE ?",
        (f"%{name}",),
    ).fetchone()


def scan(conn, root):
    return list(scan_folder(conn, add_folder(conn, root)))[-1]


def run_normalize(conn):
    return list(normalize_frames(conn))[-1]


@pytest.fixture
def archive(conn, tmp_path):
    """L'archivio sintetico, scansionato e normalizzato: la ricevuta di `normalize`.

    Sta qui e non in un file di test perche' lo chiedono in due -- le prove dello stadio e
    quelle dell'attrezzatura -- e copiarlo vorrebbe dire due banchi che possono divergere."""
    from synthetic import build_archive

    build_archive(tmp_path / "lib")
    scan(conn, tmp_path / "lib")
    return run_normalize(conn)


def review(client):
    r = client.get("/api/v1/review")
    assert r.status_code == 200, r.text
    return r.json()


def to_confirm_without(pagina, sezione):
    """Quanto conta la pagina di Da confermare tolta una sezione, ricomposto dai suoi campi: e' un
    oracolo scritto dalla pagina, non dal codice che conta, e un numero a memoria invecchierebbe."""
    gruppi = ("unfiltered", "unnamed", "rigless", "opticsless", "typeless", "mosaics")
    conti = {
        "lookalikes": len(pagina["lookalikes"]),
        "filters": len(pagina["filters"]),
        "objects": sum(1 for o in pagina["objects"] if not o["confirmed"]),
        "unclear": sum(1 for p in pagina["unclear"] if p["site"] is None),
        **{g: sum(1 for r in pagina[g] if r["answer"] is None) for g in gruppi},
    }
    assert sezione in conti, sezione
    return sum(n for nome, n in conti.items() if nome != sezione)


def apply(client, **body):
    r = client.post("/api/v1/review/apply", json=body)
    assert r.status_code == 200, r.text
    client.app.state.worker.join(10.0)
    return r.json()


def by_name(items, name):
    return next(i for i in items if i["name"] == name)


def settled(client, limit=100):
    """Gli oggetti gia' visti, che la pagina non elenca: tutti, pagina dopo pagina."""
    out, offset = [], 0
    while True:
        r = client.get(f"/api/v1/review/objects/settled?limit={limit}&offset={offset}")
        assert r.status_code == 200, r.text
        corpo = r.json()
        out += corpo["items"]
        offset += limit
        if offset >= corpo["total"]:
            return out


def all_objects(client):
    """Tutti gli oggetti come Da confermare li mostra: quelli in pagina e i gia' visti."""
    return review(client)["objects"] + settled(client)


def gear(client):
    r = client.get("/api/v1/gear")
    assert r.status_code == 200, r.text
    return r.json()


def correct(client, instrument_id, **body):
    """La scheda di un pezzo corretta dall'Attrezzatura: e' li' che si scrive, non piu' in Da
    confermare."""
    r = client.patch(f"/api/v1/gear/instruments/{instrument_id}", json=body)
    client.app.state.worker.join(10.0)
    return r


def senza_soggetti(gruppo):
    """Un gruppo di Da confermare senza cio' che il cielo ha trovato: chi prova la domanda lo
    confronta cosi', e i soggetti hanno le loro prove (`test_review_subjects.py`)."""
    return {k: v for k, v in gruppo.items() if k != "subjects"}


def da_rivedere(client):
    """Quante pose l'ultima normalizzazione ha lasciato da rivedere: e' il numero che dice se una
    posa e' a posto o se le manca ancora qualcosa, e senza guardarlo un filtro dato male e un
    filtro dato bene si assomigliano troppo."""
    stadi = client.app.state.worker.snapshot()["stages"]
    return next(s for s in stadi if s["name"] == "normalize")["tally"]["to_review"]


@pytest.fixture
def client_banco(db_path_col_catalogo):
    """Il banco misto, tre oggetti scelti uno per uno: un oggetto **sicuro** col suo cielo
    (M 31), uno **dubbio** col cielo (l'header dice M 45, il cielo dice M 31), e -- perche' il
    secondo trovera' la sigla e il nome comune di M 45 gia' presi da un orfano -- un oggetto di
    catalogo **senza nomi propri**, che e' il caso in cui il nome si legge dal catalogo."""
    from astrolog.spine.identify import identify_frames
    from identify_bench import M31, occupante, posa

    conn = connect(db_path_col_catalogo)
    try:
        occupante(conn, 9, ["M 45", "Pleiades"])
        posa(conn, obj="M 31", cielo=M31, hash_="sicuro")
        posa(conn, obj="M 45", cielo=M31, hash_="dubbio")
        list(identify_frames(conn))
        conn.commit()
    finally:
        conn.close()
    with TestClient(create_app(db_path_col_catalogo), base_url="http://localhost") as c:
        yield c


def db(client):
    return connect(client.app.state.db_path)


def write_fits(path, header=None, shape=(3, 4), dtype=np.int16, age_s=600):
    """Scrive un FITS REALE con le card date (astropy aggiunge SIMPLE/BITPIX/NAXIS*), con
    un mtime di `age_s` secondi fa: un file appena scritto la scansione lo salta apposta.
    I pixel sono rumore deterministico seminato dal percorso: ogni file scritto e' un frame
    a se'; una copia e' una copia perche' ha gli stessi byte (`shutil.copy`), come nel vero."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    h = fits.Header()
    for k, v in (header or {}).items():
        h[k] = v
    seed = int(hashlib.sha256(str(path).encode()).hexdigest()[:8], 16)
    data = np.random.default_rng(seed).integers(0, 1000, size=shape).astype(dtype)
    fits.PrimaryHDU(data=data, header=h).writeto(path, overwrite=True)
    settle(path, age_s)
    return str(path)


def write_light(path, obj="M 31", filt="Ha", date="2024-05-17T21:00:00", **extra):
    """Un frame light minimo ma completo: tipo, oggetto, filtro, esposizione, data."""
    header = {
        "IMAGETYP": "Light Frame",
        "OBJECT": obj,
        "FILTER": filt,
        "EXPTIME": 300.0,
        "DATE-OBS": date,
        **extra,
    }
    return write_fits(path, header, shape=(8, 8), dtype=np.float32)


def settle(path, age_s=600):
    """Il file risulta scritto `age_s` secondi fa: la scansione salta i file freschi."""
    past = time.time() - age_s
    os.utime(path, (past, past))


def add_folder(conn, root):
    """Una cartella registrata nel DB di prova; torna il suo id."""
    return conn.execute(
        "INSERT INTO folders(root_path, created_at) VALUES(?, 'now')", (str(root),)
    ).lastrowid


def sky_solved(conn, frame_id):
    """Cio' che il solver scrive di una posa risolta, senza lanciarlo: il cielo trovato, poi lo
    stadio fatto (`spine/solve.py`). Lo stadio fatto da solo e' il segno di uno stacco, che ha
    tolto il cielo, e la regola dell'attesa lo legge come non riconosciuto."""
    solve_store.save_wcs(
        conn,
        frame_id,
        ra_deg=202.47,
        dec_deg=47.2,
        scale=1.0,
        rotation=0.0,
        width=1.0,
        height=0.7,
        now="2026-03-15T00:00:00Z",
    )
    stages.set_status(conn, frame_id, "solve", "done")


def wait_until(pred, timeout=5.0):
    """Aspetta che `pred()` sia vero, senza dormire piu' del necessario."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if pred():
            return True
        time.sleep(0.01)
    return False


def blocking_reader(real, gate, seen, at=2):
    """Un `read_frame` che alla lettura numero `at` aspetta `gate`: cosi' un test puo'
    fermare la scansione in un punto noto."""

    def read(path):
        seen.append(path)
        if len(seen) == at:
            gate.wait(10.0)
        return real(path)

    return read


def unreadable_dir(monkeypatch, module, folder):
    """Fa fallire `os.scandir` su `folder` dentro `module` (permessi negati, mount caduto)."""
    real = os.scandir

    def fake(p):
        if os.path.normpath(str(p)) == os.path.normpath(str(folder)):
            raise OSError("permessi negati (mock)")
        return real(p)

    monkeypatch.setattr(module.os, "scandir", fake)


class ScanFinta(list):
    """Cio' che `os.scandir` restituisce: un iteratore che si CHIUDE, come gestore di contesto e
    con `close()`. Serve ai test che fingono una voce -- un collegamento, una cartella nascosta,
    un file solo online -- perche' una lista non basta."""

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def close(self):
        pass


class VoceFinta:
    """Una voce d'elenco finta: un file normale, se non si dice altro. I test la specializzano
    per fingere cio' che il sistema dice di una voce, senza toccare il disco."""

    name = ""

    def is_dir(self, follow_symlinks=True):
        return False

    def is_symlink(self):
        return False

    def is_junction(self):
        return False


class VoceAvvolta(VoceFinta):
    """Una voce vera con qualcosa di finto sopra: tutto cio' che non si finge lo dice lei."""

    def __init__(self, vera):
        self._vera, self.name = vera, vera.name

    def is_dir(self, follow_symlinks=True):
        return self._vera.is_dir(follow_symlinks=follow_symlinks)

    def is_symlink(self):
        return self._vera.is_symlink()

    def is_junction(self):
        return self._vera.is_junction()

    def stat(self, follow_symlinks=True):
        return self._vera.stat(follow_symlinks=follow_symlinks)


class CartellaLegata(VoceAvvolta):
    """Una sottocartella raggiunta da un collegamento (`junction=False`) o da una giunzione di
    Windows, come la vede `os.scandir` (i dettagli in `fits/walk._kind`)."""

    def __init__(self, vera, junction):
        super().__init__(vera)
        self._junction = junction

    def is_dir(self, follow_symlinks=True):
        return self._junction or follow_symlinks

    def is_symlink(self):
        return not self._junction

    def is_junction(self):
        return self._junction


def online_only(monkeypatch, *paths):
    """I file `paths` risultano "solo online" quando il walk elenca la loro cartella: il segno
    arriva con l'elenco, come su un disco vero. Si finge Windows, cosi' il test gira uguale su
    tutti e tre i sistemi; il resto della cartella resta com'e'."""
    from astrolog.fits import walk

    monkeypatch.setattr(walk, "PLATFORM", "win32")
    # `realpath` da tutte e due le parti: chi elenca puo' avere il percorso gia' risolto (la sonda
    # di Aggiungi cartella lo fa), e su Windows un nome breve non combacerebbe col suo nome lungo
    segnati = {os.path.normcase(os.path.realpath(str(p))) for p in paths}

    class _SoloOnline(VoceAvvolta):
        def stat(self, follow_symlinks=True):
            return SimpleNamespace(
                st_file_attributes=walk.FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS, st_flags=0
            )

    def change(cartella, voce):
        percorso = os.path.normcase(os.path.realpath(os.path.join(cartella, voce.name)))
        return _SoloOnline(voce) if percorso in segnati else voce

    fake_entries(monkeypatch, change)


def fake_entries(monkeypatch, change):
    """Ogni voce che il walk elenca passa da `change(cartella, voce)`, che la restituisce com'e'
    o finta: il modo di fingere cio' che il sistema dice di un file senza toccare il disco."""
    from astrolog.fits import walk

    real = os.scandir

    def fake(p):
        with real(p) as vere:
            return ScanFinta(change(str(p), v) for v in vere)

    monkeypatch.setattr(walk.os, "scandir", fake)


@pytest.fixture
def make_fits(tmp_path):
    def _make(name, header=None, **kw):
        return write_fits(tmp_path / name, header, **kw)

    return _make
