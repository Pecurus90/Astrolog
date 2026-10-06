"""Lo stadio `solve`: il cielo di ogni posa, misurato da ASTAP.

Vincolo di questi test: **non lanciano ASTAP**. Il lancio si inietta e qui si passa un finto
che scrive l'esito che gli si dice. Cosi' la suite veloce gira anche su una macchina senza
solver, ed e' l'unico modo di provare i casi che sul vero non si producono a comando (il
timeout, la posa senza stelle, la cache che risponde al posto del solver).
"""

import os
import pathlib

import pytest

from astrolog import astap
from astrolog.db import idlist
from astrolog.db.connect import connect
from astrolog.spine import solve_store as store
from astrolog.spine import stages
from astrolog.spine.scan import scan_folder
from astrolog.spine.solve import solve_frames
from conftest import add_folder, write_light

# Un esito risolto, nella forma vera di ASTAP.
INI = """
PLTSOLVD=T
CRVAL1= 2.1080144893504479E+002
CRVAL2= 5.4349083378595992E+001
CD1_1= 1.4256340084600304E-005
CD1_2=-1.4392447113033648E-004
CD2_1= 1.4379401908293604E-004
CD2_2= 1.4226001018695530E-005
"""


def solver(esiti=None, stdout="HFD_MEDIAN=3,4\nSTARS=250\n"):
    """Un ASTAP finto. `esiti` dice, per numero di chiamata di solve, cosa scrivere: un testo
    lo si scrive nel `.ini`, `None` vuol dire "nessun file" (fallimento), un'eccezione la si
    solleva. Di suo risolve sempre."""
    chiamate = []

    def run(cmd, timeout_s):
        chiamate.append(cmd)
        # Il finto sporca come sporcherebbe il vero: ASTAP con `-extract` lascia un CSV
        # ACCANTO al FITS (ignorando `-o`), e con `-update` riscrive il FITS stesso. Senza
        # questo, il confronto della cartella prima/dopo non potrebbe fallire mai.
        sorgente = pathlib.Path(cmd[cmd.index("-f") + 1])
        if any(c.startswith("-extract") for c in cmd):
            sorgente.with_suffix(".csv").write_text("x,y,hfd\n", encoding="utf-8")
        if "-update" in cmd:
            sorgente.write_bytes(sorgente.read_bytes() + b" ")
        if "-analyse" in cmd:
            return 0, stdout
        quale = len([c for c in chiamate if "-analyse" not in c]) - 1
        esito = (esiti or {}).get(quale, INI)
        if isinstance(esito, Exception):
            raise esito
        base = cmd[cmd.index("-o") + 1]
        if esito is not None:
            pathlib.Path(f"{base}.ini").write_text(esito, encoding="utf-8")
        return (0 if esito else 1), ""

    run.calls = chiamate
    run.solves = lambda: [c for c in chiamate if "-analyse" not in c]
    return run


def archivio(tmp_path, sessioni=(("M 31", 3), ("M 42", 2))):
    """Un archivio di prova: piu' sessioni, ognuna con le sue pose. Le pose della stessa
    sessione hanno stesso oggetto e stessa notte, che e' come il solver le raggruppa."""
    root = tmp_path / "lib"
    for obj, quante in sessioni:
        for i in range(quante):
            write_light(
                root / obj / f"{i}.fits",
                obj=obj,
                date=f"2024-05-1{1 if obj == 'M 31' else 2}T2{i}:00:00",
                RA=10.5,
                DEC=41.2,
                FOCALLEN=530.0,
                XPIXSZ=3.76,
            )
    return root


def popola(db_path, root):
    conn = connect(db_path)
    try:
        list(scan_folder(conn, add_folder(conn, root)))
    finally:
        conn.close()


def corri(conn, run, **kw):
    """Fa girare lo stadio fino in fondo e torna la ricevuta."""
    return list(solve_frames(conn, exe="astap", run=run, **kw))[-1]


def id_per_percorso(conn):
    """`{percorso assoluto -> frame_id}`: e' cosi' che si legge l'ordine in cui lo stadio ha
    lavorato, guardando i comandi che ha composto."""
    righe = conn.execute(
        "SELECT p.rel_path, d.root_path, p.frame_id FROM positions p"
        " JOIN folders d ON d.id = p.folder_id"
    )
    return {os.path.normpath(os.path.join(root, rel)): fid for rel, root, fid in righe}


def ordine(conn, run):
    """I frame nell'ordine in cui il solver e' stato chiamato."""
    mappa = id_per_percorso(conn)
    return [mappa[os.path.normpath(c[c.index("-f") + 1])] for c in run.solves()]


def stato(conn, stage="solve"):
    return dict(conn.execute("SELECT frame_id, status FROM frame_stages WHERE stage = ?", (stage,)))


@pytest.fixture
def archivio_letto(db_path, tmp_path):
    root = archivio(tmp_path)
    popola(db_path, root)
    return root


# --- l'ordine ------------------------------------------------------------------------------


def test_solve_order_one_per_group(db_path, archivio_letto, tmp_path):
    """Prima UNA posa per sessione, poi tutte le altre. Su un archivio vero sono 300 solve per
    vedere tutto invece di 10.000: dopo un minuto ogni sessione ha il suo cielo."""
    conn = connect(db_path)
    run = solver()
    ricevuta = corri(conn, run, cache=tmp_path / "cache")

    # La chiave con cui il solver raggruppa si CHIEDE al modulo, non si ricopia: se la si
    # riscrivesse qui, il test resterebbe verde anche dopo averla cambiata di la'.
    sessione_di = dict(
        conn.execute(f"SELECT id, {store.SOLVE_ORDER_KEY} FROM frames")  # noqa: S608 - costante del modulo
    )
    quante = len(set(sessione_di.values()))
    assert quante == 2, "l'archivio di prova deve avere due sessioni"

    fatti = ordine(conn, run)
    prime = [sessione_di[i] for i in fatti[:quante]]
    assert len(set(prime)) == quante  # le prime sono una per sessione, tutte diverse

    assert ricevuta["solved"] == 5 and ricevuta["done"] is True
    assert set(stato(conn).values()) == {"done"}
    conn.close()


def test_the_second_pass_takes_the_most_recent_first(db_path, archivio_letto, tmp_path):
    """Dopo il primo giro si continua dalle pose piu' recenti: e' l'archivio che si sta
    guardando adesso, non quello di tre anni fa."""
    conn = connect(db_path)
    run = solver()
    corri(conn, run, cache=tmp_path / "cache")

    data_di = dict(conn.execute("SELECT id, date_obs FROM frames"))
    resto = [data_di[i] for i in ordine(conn, run)[2:]]
    assert resto == sorted(resto, reverse=True)
    conn.close()


# --- il FITS non si tocca -------------------------------------------------------------------


def test_solve_never_writes_fits(db_path, archivio_letto, tmp_path):
    """La regola assoluta: l'app legge i FITS e basta. Si guarda la cartella dell'utente prima
    e dopo -- nomi, dimensioni e date -- e non deve essere cambiato niente. E' anche la prova
    che `-extract` non e' entrato di nascosto: lascerebbe un CSV proprio li'."""
    prima = {p: (p.stat().st_size, p.stat().st_mtime_ns) for p in archivio_letto.rglob("*")}
    conn = connect(db_path)
    run = solver()
    corri(conn, run, cache=tmp_path / "cache")
    dopo = {p: (p.stat().st_size, p.stat().st_mtime_ns) for p in archivio_letto.rglob("*")}
    assert dopo == prima

    for cmd in run.calls:
        assert "-update" not in cmd
        assert not any(c.startswith("-extract") for c in cmd)
        if "-o" in cmd:  # cio' che scrive, lo scrive nella cache e da nessun'altra parte
            assert str(archivio_letto) not in cmd[cmd.index("-o") + 1]
    conn.close()


# --- la cache -------------------------------------------------------------------------------


def test_solve_cache_by_hash(db_path, archivio_letto, tmp_path):
    """Un frame risolto una volta non si ri-risolve: la cache e' per impronta, quindi
    sopravvive a un azzeramento del database, a uno spostamento del file e a una rinomina."""
    cache = tmp_path / "cache"
    conn = connect(db_path)
    corri(conn, solver(), cache=cache)
    assert len(list((cache / "solve").glob("*.ini"))) == 5

    # si rimette tutto da fare e si rilancia con un solver che esplode se chiamato
    stages.invalidate(conn, [r[0] for r in conn.execute("SELECT id FROM frames")], "solve")

    def mai(cmd, timeout_s):
        raise AssertionError(f"ha richiamato il solver: {cmd}")

    ricevuta = corri(conn, mai, cache=cache)
    assert ricevuta["cached"] == 5 and ricevuta["solved"] == 0
    assert set(stato(conn).values()) == {"done"}
    # e il cielo c'e' lo stesso
    assert conn.execute("SELECT COUNT(*) FROM frame_wcs").fetchone()[0] == 5
    conn.close()


def test_a_cached_sky_still_gets_its_quality_back(db_path, archivio_letto, tmp_path):
    """Dopo un azzeramento del database la cache ridà il cielo, ma HFD e stelle sono nel DB e
    se ne sono andati: si richiedono, o si perderebbero per sempre senza che nessuno lo dica.
    Costa una passata di analisi, non un solve."""
    cache = tmp_path / "cache"
    conn = connect(db_path)
    corri(conn, solver(), cache=cache)

    # l'azzeramento: gli stadi tornano da fare e le misure spariscono, la cache resta
    stages.invalidate(conn, [r[0] for r in conn.execute("SELECT id FROM frames")], "solve")
    conn.execute("DELETE FROM frame_metrics")

    run = solver(stdout="HFD_MEDIAN=5,5\nSTARS=99\n")
    ricevuta = corri(conn, run, cache=cache)
    assert ricevuta["cached"] == 5 and ricevuta["solved"] == 0  # il cielo non si ricalcola
    assert ricevuta["measured"] == 5  # la qualita' si'
    assert all("-analyse" in c for c in run.calls)  # e non si e' lanciato un solo solve
    riga = conn.execute("SELECT hfd_px, stars FROM frame_metrics LIMIT 1").fetchone()
    assert riga["hfd_px"] == pytest.approx(5.5) and riga["stars"] == 99
    conn.close()


def test_a_cached_sky_on_an_unplugged_disc_launches_nothing(db_path, archivio_letto, tmp_path):
    """La cache risponde anche a disco staccato, ma l'analisi vuole il file: senza il controllo
    sul percorso partirebbe un processo per posa su un file che non c'e'."""
    cache = tmp_path / "cache"
    conn = connect(db_path)
    corri(conn, solver(), cache=cache)
    stages.invalidate(conn, [r[0] for r in conn.execute("SELECT id FROM frames")], "solve")
    conn.execute("DELETE FROM frame_metrics")
    conn.execute("UPDATE positions SET status = 'missing'")

    run = solver()
    ricevuta = corri(conn, run, cache=cache)
    assert ricevuta["cached"] == 5 and ricevuta["measured"] == 0
    assert run.calls == []
    conn.close()


# --- cosa si salva ---------------------------------------------------------------------------


def test_the_measured_sky_is_what_gets_saved(db_path, archivio_letto, tmp_path):
    """Centro, scala, rotazione e campo vengono dalla soluzione, non dall'header: l'header
    sbaglia il centro di 4' in mediana e fino a 26'."""
    conn = connect(db_path)
    corri(conn, solver(), cache=tmp_path / "cache")
    riga = conn.execute("SELECT * FROM frame_wcs LIMIT 1").fetchone()
    assert riga["ra_deg"] == pytest.approx(210.8014, abs=0.001)  # non il 10.5 dell'header
    assert riga["dec_deg"] == pytest.approx(54.3491, abs=0.001)  # non il 41.2 dell'header
    assert riga["scale_arcsec_px"] == pytest.approx(0.5206, abs=0.001)
    assert riga["rotation_deg"] == pytest.approx(84.35, abs=0.05)
    assert riga["width_deg"] > 0 and riga["height_deg"] > 0
    assert riga["solved_at"]
    conn.close()


def test_hfd_and_stars_come_from_the_second_pass(db_path, archivio_letto, tmp_path):
    """HFD e stelle costano una passata in piu' e si prendono lo stesso: rileggere l'archivio
    un'altra volta costerebbe di piu' del tempo risparmiato adesso."""
    conn = connect(db_path)
    ricevuta = corri(conn, solver(), cache=tmp_path / "cache")
    riga = conn.execute("SELECT * FROM frame_metrics LIMIT 1").fetchone()
    assert riga["hfd_px"] == pytest.approx(3.4) and riga["stars"] == 250
    assert riga["source"] == "astap"
    assert riga["eccentricity"] is None  # e' di `measure`, non si inventa qui
    assert ricevuta["measured"] == 5
    conn.close()


def test_a_sky_without_a_rectangle_is_still_a_sky(db_path, tmp_path):
    """Centro e scala sono la soluzione; rotazione e campo sono il rettangolo che si disegna.
    Un esito che non dice l'orientamento, o un header che non dice quanti pixel ha il sensore,
    lasciano il rettangolo vuoto -- ma il cielo misurato resta, e non si butta via."""
    root = tmp_path / "lib"
    write_light(root / "a.fits", obj="M 31")
    popola(db_path, root)
    # un esito con centro e scala e senza matrice: la rotazione non si sa
    senza_rotazione = "PLTSOLVD=T\nCRVAL1=210.0\nCRVAL2=54.0\nCDELT1=1.4e-004\n"

    conn = connect(db_path)
    ricevuta = corri(conn, solver(esiti={0: senza_rotazione}), cache=tmp_path / "cache")
    assert ricevuta["solved"] == 1 and ricevuta["errors"] == 0
    riga = conn.execute("SELECT * FROM frame_wcs").fetchone()
    assert riga["ra_deg"] == pytest.approx(210.0) and riga["scale_arcsec_px"] > 0
    assert riga["rotation_deg"] is None  # non si sa, e non si inventa
    conn.close()


# --- quando non si risolve --------------------------------------------------------------------


def test_solve_failure_is_a_reason(db_path, archivio_letto, tmp_path):
    """Una posa che non si risolve resta in archivio col suo perche', e la corsa continua:
    nessuna ora persa dai totali, solo un cielo che manca."""
    conn = connect(db_path)
    ricevuta = corri(conn, solver(esiti={1: None, 3: TimeoutError()}), cache=tmp_path / "cache")

    assert ricevuta["solved"] == 3 and ricevuta["unsolved"] == 2
    stati = stato(conn)
    assert sorted(stati.values()) == ["done", "done", "done", "failed", "failed"]
    motivi = {
        r[0]
        for r in conn.execute(
            "SELECT reason FROM frame_stages WHERE stage = 'solve' AND status = 'failed'"
        )
    }
    assert motivi == {"no_solution", "timeout"}
    conn.close()


def test_a_failure_is_not_cached(db_path, archivio_letto, tmp_path):
    """Un fallimento non si mette in cache: domani ASTAP puo' avere un database piu' fitto, o
    la posa puo' ereditare un indizio da una sorella. Solo le soluzioni sono immutabili."""
    cache = tmp_path / "cache"
    conn = connect(db_path)
    corri(conn, solver(esiti=dict.fromkeys(range(5))), cache=cache)
    assert list((cache / "solve").glob("*.ini")) == []

    stages.invalidate(conn, [r[0] for r in conn.execute("SELECT id FROM frames")], "solve")
    ricevuta = corri(conn, solver(), cache=cache)
    assert ricevuta["solved"] == 5  # riprovate davvero, non date per perse
    conn.close()


def test_the_lost_sky_is_looked_up_from_the_list(db_path):
    """Chi ha perso il cielo si cerca partendo dalla lista: partire dagli stadi scorrerebbe ogni
    posa risolta dell'archivio a ogni fine scansione, anche con la lista vuota."""
    conn = connect(db_path)
    with idlist.holding(conn, []):
        piano = " ".join(r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + store.LOST_SKY))
    assert "sqlite_autoindex_frame_stages_1 (frame_id=?" in piano, piano
    assert "frame_stages_pending" not in piano, piano
    conn.close()


# Senza ASTAP: `test_solve_without_astap.py`.


# --- l'indizio che si eredita -------------------------------------------------------------------


def test_a_frame_without_a_pointing_hint_inherits_it_from_its_sister(db_path, tmp_path):
    """Una posa il cui header non dice dove puntava eredita l'indizio dalla sorella gia'
    risolta della sua sessione: e' cio' che la salva dai 23 secondi della ricerca cieca."""
    root = tmp_path / "lib"
    write_light(root / "a.fits", obj="M 31", date="2024-05-11T21:00:00", RA=10.5, DEC=41.2)
    write_light(root / "b.fits", obj="M 31", date="2024-05-11T22:00:00")  # senza puntamento
    popola(db_path, root)

    conn = connect(db_path)
    run = solver()
    corri(conn, run, cache=tmp_path / "cache")

    seconda = run.solves()[1]
    assert "-ra" in seconda, "la seconda posa avrebbe dovuto ereditare l'indizio"
    # e l'indizio ereditato e' quello MISURATO dalla sorella, non quello dell'header
    assert float(seconda[seconda.index("-ra") + 1]) == pytest.approx(210.8014 / 15, abs=0.001)
    conn.close()


def test_the_first_frame_of_a_session_without_a_hint_searches_blind(db_path, tmp_path):
    """Se nessuna sorella e' ancora risolta non si inventa un puntamento: si cerca in tutto il
    cielo e si paga."""
    root = tmp_path / "lib"
    write_light(root / "a.fits", obj="M 31", date="2024-05-11T21:00:00")
    popola(db_path, root)
    conn = connect(db_path)
    run = solver()
    corri(conn, run, cache=tmp_path / "cache")
    assert "-ra" not in run.solves()[0]
    conn.close()


# --- fermarsi, e i guasti veri ----------------------------------------------------------------


def test_stopping_leaves_a_coherent_prefix(db_path, archivio_letto, tmp_path):
    """Chi ferma la corsa a meta' trova le pose gia' risolte davvero risolte e le altre ancora
    da fare: si chiude fra un frame e l'altro, a transazione chiusa, mai a meta' di una."""
    conn = connect(db_path)
    corsa = solve_frames(conn, exe="astap", run=solver(), cache=tmp_path / "cache")
    next(corsa)
    next(corsa)
    corsa.close()  # e' cio' che fa il worker quando arriva lo Stop

    stati = stato(conn)
    assert sorted(stati.values()) == ["done", "done", "pending", "pending", "pending"]
    fatti = [i for i, st in stati.items() if st == "done"]
    assert conn.execute("SELECT COUNT(*) FROM frame_wcs").fetchone()[0] == len(fatti)
    conn.close()


def test_a_frame_that_explodes_does_not_stop_the_others(
    db_path, archivio_letto, tmp_path, monkeypatch
):
    """Un guasto nostro su una posa la segna `failed` col codice generico e la corsa continua:
    e' lo stesso patto della scansione, che conta i file illeggibili e va avanti."""
    from astrolog.spine import solve as modulo

    vero = modulo._field_hint
    rotto = {"quante": 0}

    def esplode(frame):
        rotto["quante"] += 1
        if rotto["quante"] == 2:
            raise RuntimeError("qualcosa di nostro si e' rotto")
        return vero(frame)

    monkeypatch.setattr(modulo, "_field_hint", esplode)
    conn = connect(db_path)
    ricevuta = corri(conn, solver(), cache=tmp_path / "cache")

    assert ricevuta["errors"] == 1 and ricevuta["solved"] == 4
    assert ricevuta["errors_detail"][0]["reason"].startswith("RuntimeError")
    motivi = {
        r[0]
        for r in conn.execute(
            "SELECT reason FROM frame_stages WHERE stage = 'solve' AND status = 'failed'"
        )
    }
    assert motivi == {"internal_error"}
    conn.close()


def test_a_frame_whose_disc_is_unplugged_waits_for_it(db_path, archivio_letto, tmp_path):
    """Il disco esterno staccato: la posa resta DA FARE e riprende quando torna. Nessuna
    chiamata al solver per un file che non c'e'."""
    conn = connect(db_path)
    conn.execute("UPDATE positions SET status = 'missing'")
    run = solver()
    ricevuta = corri(conn, run, cache=tmp_path / "cache")

    # nessun processo lanciato per un file che non c'e', ne' di solve ne' di analisi
    assert ricevuta["waiting"] == 5 and run.calls == []
    assert set(stato(conn).values()) == {"pending"}  # riattaccando il disco si riprende
    conn.close()


# --- le regole su cui la fetta e' costruita ------------------------------------------------


def test_solve_field_from_the_header(db_path, tmp_path):
    """Il campo passato al solver si CALCOLA dall'header, e non e' un numero qualunque: e' la
    leva della velocita' (la misura sta in `docs/domini/spina.md`). Si prova sul comando che parte
    davvero, partendo da un header con dentro focale e pixel."""
    root = tmp_path / "lib"
    write_light(root / "a.fits", obj="M 31", FOCALLEN=1000.0, XPIXSZ=3.76)
    popola(db_path, root)
    conn = connect(db_path)
    run = solver()
    corri(conn, run, cache=tmp_path / "cache")

    # 8 pixel di altezza a 0,7756"/px = 0,0017 gradi: piccolo, ma e' il numero dell'header
    atteso = 8 * (3.76 / 1000.0 * 206.265) / 3600
    passato = float(run.solves()[0][run.solves()[0].index("-fov") + 1])
    assert passato == pytest.approx(atteso, abs=0.001)
    assert passato > 0, "un campo a zero vuol dire che ASTAP se lo cerca da solo, molto piu' lento"
    conn.close()


def test_the_field_is_not_doubled_by_the_binning(db_path, tmp_path):
    """Il binning NON si moltiplica: `XPIXSZ` lo include gia', e moltiplicare darebbe un campo
    doppio su tutto un archivio a bin 2 -- che e' come non darlo."""
    root = tmp_path / "lib"
    write_light(root / "uno.fits", obj="M 31", FOCALLEN=1000.0, XPIXSZ=3.76, XBINNING=1)
    write_light(root / "due.fits", obj="M 42", FOCALLEN=1000.0, XPIXSZ=3.76, XBINNING=2)
    popola(db_path, root)
    conn = connect(db_path)
    run = solver()
    corri(conn, run, cache=tmp_path / "cache")
    campi = {float(c[c.index("-fov") + 1]) for c in run.solves()}
    assert len(campi) == 1, f"il binning ha cambiato il campo: {campi}"
    conn.close()


def test_the_cache_key_is_the_fingerprint_not_the_row_number(db_path, tmp_path):
    """La cache e' per IMPRONTA del frame. Si prova ricreando il database da zero: gli id
    ripartono e cambiano, i file no -- e la cache deve rispondere lo stesso. Con una chiave
    sul numero di riga questo test sarebbe rosso."""
    from astrolog.db.connect import create_database

    cache = tmp_path / "cache"
    root = archivio(tmp_path, sessioni=(("M 31", 2),))
    popola(db_path, root)
    conn = connect(db_path)
    corri(conn, solver(), cache=cache)
    hash_prima = {r[0] for r in conn.execute("SELECT frame_hash FROM frames")}
    conn.close()

    # il database si ricrea da zero, e per far cambiare gli id si legge prima un'altra cartella
    db_path.unlink()
    create_database(db_path)
    altra = tmp_path / "altra"
    write_light(altra / "x.fits", obj="M 42")
    popola(db_path, altra)
    popola(db_path, root)

    conn = connect(db_path)
    ids = {r[0] for r in conn.execute("SELECT id FROM frames WHERE frame_hash IN (?, ?)",
                                      tuple(hash_prima))}  # fmt: skip
    assert ids != {1, 2}, "gli id non sono cambiati: il test non proverebbe niente"

    def solo_la_nuova(cmd, timeout_s):
        if "-analyse" in cmd:  # la qualita' si richiede: sta nel DB, e il DB e' nuovo
            return 0, "HFD_MEDIAN=3,4\nSTARS=250\n"
        assert "x.fits" in " ".join(cmd), f"ha ri-risolto una posa che era gia' in cache: {cmd}"
        base = cmd[cmd.index("-o") + 1]
        pathlib.Path(f"{base}.ini").write_text(INI, encoding="utf-8")
        return 0, "HFD_MEDIAN=3,4\nSTARS=250\n"

    ricevuta = corri(conn, solo_la_nuova, cache=cache)
    assert ricevuta["cached"] == 2 and ricevuta["solved"] == 1
    conn.close()


def test_the_sister_must_be_of_the_same_object(db_path, tmp_path):
    """L'indizio si eredita solo da una posa dello STESSO oggetto. Due pose senza `OBJECT`
    riprese la stessa notte con lo stesso corredo finiscono nello stesso gruppo del solver pur
    guardando due punti di cielo diversi: ereditare li' manderebbe il solver nel posto
    sbagliato, e non risolverebbe -- mentre alla cieca ce l'avrebbe fatta."""
    root = tmp_path / "lib"
    write_light(root / "a.fits", obj="M 31", date="2024-05-11T21:00:00", RA=10.5, DEC=41.2)
    # stessa notte, stesso corredo, nessun oggetto: per il solver sono lo stesso gruppo
    write_light(root / "b.fits", obj="", date="2024-05-11T22:00:00")
    write_light(root / "c.fits", obj="", date="2024-05-11T23:00:00")
    popola(db_path, root)

    conn = connect(db_path)
    senza = [r[0] for r in conn.execute("SELECT id FROM frames WHERE object_raw IS NULL")]
    assert len(store.first_per_order_key(conn, senza)) == 1, (
        "le due senza oggetto devono stare nello stesso gruppo, o il test non prova niente"
    )

    run = solver()
    corri(conn, run, cache=tmp_path / "cache")
    senza_oggetto = [c for c in run.solves() if "a.fits" not in " ".join(c)]
    assert all("-ra" not in c for c in senza_oggetto), "ha ereditato da una sorella sbagliata"
    conn.close()


# --- ASTAP c'e' ma il suo catalogo no ------------------------------------------------------

# La frase e' quella VERA, letta da ASTAP CLI-2025.11.19 lanciato con `-d` su una cartella
# vuota: esce 1 e scrive questo. Non e' scritta a memoria, e non e' un'ipotesi.
SENZA_CATALOGO = "\nPLTSOLVD=F\nERROR=No star database found.\n"
# L'altro modo di essere installato a meta', e ASTAP lo dice con un'altra frase: il catalogo e'
# un download da ~1 GB, e interrotto a meta' e' comune quanto non fatto.
A_META = "\nPLTSOLVD=F\nERROR=Error reading star database.\n"
# Il finto risponde cosi' a OGNI chiamata: senza il catalogo ogni posa fallisce identica, e un
# finto che sbaglia solo la prima proverebbe il contrario dello scenario.
SEMPRE = {i: SENZA_CATALOGO for i in range(10)}


def test_astap_without_its_star_database_is_not_a_dead_end(db_path, archivio_letto, tmp_path):
    """L'errore di installazione piu' comune: ASTAP c'e' (il catalogo e' un download separato)
    ma non ha le sue stelle.

    Prima finiva nel ripiego `no_solution`, che e' **terminale**: le pose diventavano `failed`,
    Avvia non le riprovava mai piu', e l'unica uscita per l'utente era cancellare il database
    dell'app. Deve invece restare in coda, come quando ASTAP non c'e' affatto."""
    conn = connect(db_path)
    ricevuta = corri(conn, solver(esiti=SEMPRE), cache=tmp_path / "cache")

    assert set(stato(conn).values()) == {"pending"}, "nessuna posa deve diventare `failed`"
    assert ricevuta["unsolved"] == 0
    conn.close()


def test_a_missing_star_database_stops_the_run_and_says_so(db_path, archivio_letto, tmp_path):
    """Non si prova posa per posa cio' che fallira' identico su tutte.

    Senza il catalogo **ogni** posa fallira' allo stesso modo: lanciare ASTAP cinquemila volte
    per scoprirlo e' un'ora buttata, e la ricevuta direbbe solo "in attesa" senza dire perche'.
    Si ferma alla prima e lo dichiara, come la scansione fa con la radice sparita."""
    conn = connect(db_path)
    run = solver(esiti=SEMPRE)
    ricevuta = corri(conn, run, cache=tmp_path / "cache")

    assert (ricevuta["status"], ricevuta["reason"]) == ("aborted", "no_star_database")
    assert len(run.solves()) == 1, "ha continuato a lanciare ASTAP dopo averlo saputo"
    conn.close()


def test_the_real_astap_phrase_is_the_one_we_match():
    """La frase di ASTAP e' il contratto con un programma di qualcun altro: si confronta in
    minuscolo e per contenimento, perche' il testo esatto cambia da una versione all'altra --
    ma la parola chiave no. Qui si prova sul testo vero, non su uno inventato."""
    assert astap.from_ini(astap.read_ini_text(SENZA_CATALOGO)).reason == "no_star_database"
    assert astap.from_ini(astap.read_ini_text(A_META)).reason == "no_star_database"
