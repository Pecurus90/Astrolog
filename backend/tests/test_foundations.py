"""Le fondamenta della spina: un'identita' sola e stabile, il grafo negli archi, il
dichiarato su chiavi che sopravvivono, l'ordine del solver, le date canoniche,
nessun `running` nel DB. Una regola, un test che si rompe se la regola si rompe."""

import math
import os
import sqlite3
from dataclasses import asdict

import numpy as np
import pytest
from astropy.io import fits

from astrolog.clock import NIGHT_SQL, night_date
from astrolog.fits import header_read
from astrolog.fits.header_fields import canonical_utc, extract_fields
from astrolog.fits.header_read import frame_fingerprint, read_header
from astrolog.spine import header_asks, scan_store, solve_store, stages
from astrolog.spine import run as run_mod
from astrolog.spine import scan as scan_mod
from astrolog.spine.run import ORDER, queue
from astrolog.spine.scan import scan_folder
from astrolog.spine.stages import StageName
from conftest import add_folder, settle, write_light


def run(conn, fid):
    return list(scan_folder(conn, fid))[-1]


# --- identita' -------------------------------------------------------------------------


def test_fingerprint_survives_a_header_rewrite(tmp_path):
    """Un programma di elaborazione riscrive l'header lasciando i pixel: stesso frame."""
    p = write_light(tmp_path / "a.fits", obj="M 31")
    before = frame_fingerprint(p, read_header(p))
    with fits.open(p, mode="update") as hdul:
        hdul[0].header["HISTORY"] = "riscritto da un software di elaborazione"
        hdul[0].header["OBJECT"] = "M31 rinominato"
    assert frame_fingerprint(p, read_header(p)) == before


def test_fingerprint_differs_when_the_pixels_differ(tmp_path):
    """Due frame con header identico ma pixel diversi (il caso normale: rumore) sono due frame;
    lo stesso file copiato in due cartelle e' uno."""
    header = {"IMAGETYP": "Light", "OBJECT": "M 13", "EXPTIME": 60.0}
    rng = np.random.default_rng(1)
    paths = []
    for i in range(2):
        h = fits.Header()
        for k, v in header.items():
            h[k] = v
        p = tmp_path / f"f{i}.fits"
        fits.PrimaryHDU(data=rng.integers(0, 4000, (8, 8)).astype(np.int16), header=h).writeto(p)
        paths.append(str(p))
    a, b = (frame_fingerprint(p, read_header(p)) for p in paths)
    assert a != b
    copy = tmp_path / "copia.fits"
    copy.write_bytes((tmp_path / "f0.fits").read_bytes())
    assert frame_fingerprint(str(copy), read_header(str(copy))) == a


def test_fingerprint_of_a_mef_survives_a_header_rewrite(tmp_path):
    """In un file a piu' pagine l'offset dei pixel viene dal file, non dall'header combinato:
    un primario che cresce oltre un blocco da 2880 byte non sposta l'impronta."""
    rng = np.random.default_rng(3)
    primary = fits.PrimaryHDU()
    for i in range(30):
        primary.header[f"CARD{i:02d}"] = i
    image = fits.ImageHDU(data=rng.integers(0, 4000, (8, 8)).astype(np.int16))
    image.header["OBJECT"] = "M 31"
    p = tmp_path / "m.fits"
    fits.HDUList([primary, image]).writeto(p)
    before = frame_fingerprint(p, read_header(p))
    with fits.open(p, mode="update") as hdul:
        for i in range(60):
            hdul[0].header[f"EXTRA{i:02d}"] = "riscritto"
    assert frame_fingerprint(p, read_header(p)) == before


def test_fingerprint_reads_the_centre_so_a_black_border_does_not_merge_frames(tmp_path):
    """Due frame registrati hanno le prime righe a zero (bordo di registrazione): sono due
    frame diversi, e l'impronta deve dirlo."""
    paths = []
    for seed in (1, 2):
        data = np.zeros((400, 200), dtype=np.int16)  # 160 KB: 400 byte a riga
        # il rumore sta fra i byte 68.000 e 76.000: fuori dai primi 64 KB, dentro la
        # finestra centrale (48 KB - 112 KB). Con l'impronta vecchia i due file coincidono.
        data[170:190, 90:110] = np.random.default_rng(seed).integers(0, 4000, (20, 20))
        p = tmp_path / f"r{seed}.fits"
        fits.PrimaryHDU(data=data).writeto(p)
        paths.append(p)
    a, b = (frame_fingerprint(p, read_header(p)) for p in paths)
    assert a != b


@pytest.mark.parametrize("cards", [0, 60])
def test_the_pixels_start_where_astropy_says(tmp_path, cards):
    """Dove cominciano i pixel lo dice il file, non l'header che abbiamo in mano: se
    sbagliasse di un blocco, l'impronta guarderebbe altri byte e due frame diversi
    potrebbero coincidere. Vale a pagina singola e a piu' pagine."""
    header = fits.Header()
    for i in range(cards):
        header[f"C{i:02d}"] = i
    data = np.random.default_rng(4).integers(0, 4000, (20, 20)).astype(np.float32)
    single = tmp_path / f"s{cards}.fits"
    fits.PrimaryHDU(data=data, header=header).writeto(single)
    multi = tmp_path / f"m{cards}.fits"
    fits.HDUList([fits.PrimaryHDU(header=header), fits.ImageHDU(data=data)]).writeto(multi)

    for path in (single, multi):
        with fits.open(path) as hdul:
            expected = next(
                hdul.fileinfo(i) for i, h in enumerate(hdul) if h.header.get("NAXIS", 0)
            )
        start, span = header_read._data_block(str(path))
        assert (start, span) == (expected["datLoc"], expected["datSpan"]), path.name


def test_a_millisecond_truncated_mtime_is_still_unchanged(conn, tmp_path, monkeypatch):
    """Un NAS rimontato con un'altra precisione tronca l'mtime al millisecondo: i file non
    sono cambiati e **non si rileggono**.

    Guardare il contatore `unchanged` non basta, ed e' il difetto che questo test aveva: quel
    contatore sale per due strade -- il pre-controllo (dimensione e data), e la strada lunga in
    cui il file si riapre, si rilegge l'header, si rifa' l'impronta e si scopre che i pixel
    sono gli stessi. Col pre-controllo rotto la seconda strada teneva il test verde. Quindi si
    guarda cio' che conta davvero: che il file **non sia stato aperto**."""
    p = write_light(tmp_path / "a.fits")
    fid = add_folder(conn, tmp_path)
    run(conn, fid)
    st = os.stat(p)
    os.utime(p, (st.st_atime, math.floor(st.st_mtime * 1000) / 1000))

    letture = []
    vero = scan_mod.read_frame
    monkeypatch.setattr(scan_mod, "read_frame", lambda path: letture.append(path) or vero(path))
    assert run(conn, fid)["unchanged"] == 1
    assert letture == [], "il file e' stato riletto: il pre-controllo non ha funzionato"


def test_scan_uses_the_single_identity(conn, tmp_path):
    p = write_light(tmp_path / "a.fits")
    fid = add_folder(conn, tmp_path)
    run(conn, fid)
    row = conn.execute("SELECT frame_hash FROM frames").fetchone()
    assert len(row["frame_hash"]) == 64
    with fits.open(p, mode="update") as hdul:
        hdul[0].header["HISTORY"] = "riscritto"
    settle(p)
    done = run(conn, fid)
    assert (done["new"], done["unchanged"]) == (0, 1)  # stesso frame, header nuovo
    assert conn.execute("SELECT COUNT(*) FROM frames").fetchone()[0] == 1


# --- grafo -----------------------------------------------------------------------------


def test_downstream_follows_the_arcs():
    assert stages.downstream("solve") == ("solve", "identify", "group", "measure")
    assert stages.downstream("normalize") == ("normalize", "identify", "group")
    assert stages.downstream("measure") == ("measure",)


def test_the_queue_is_in_the_order_of_the_chain_whoever_asks(tmp_path):
    """La fila la decide `run.queue` e nessun altro: chi chiama dice COSA serve, mai in che
    ordine. Prima erano tre posti a deciderlo -- questo file, il pulsante Avvia e l'Applica di
    Da confermare -- e i tre non dicevano la stessa cosa."""
    db = str(tmp_path / "x.db")
    cartella = {"folder_id": 1, "run_id": 1}  # servono a `scan`, e solo a lui
    chiesti = [StageName.GROUP, StageName.SCAN, StageName.SOLVE]  # in disordine apposta
    # `solve` si porta dietro il nome e le notti (lo dice il grafo), e il tutto esce comunque
    # nell'ordine della catena, non in quello in cui e' stato chiesto
    fila = [s for s, _ in queue(db, chiesti, **cartella)]
    assert fila == ["scan", "solve", "identify", "group"]
    assert [s for s, _ in queue(db, ORDER, **cartella)] == list(ORDER)


def test_identify_drags_group_along(tmp_path):
    """Una posa che cambia oggetto cambia anche sessione: chiedere `identify` senza `group`
    la lascerebbe nella sessione di ieri, e nessuno la rimetterebbe a posto. `group` da solo
    invece resta solo: e' cio' che serve dopo una risposta sul luogo di una notte."""
    db = str(tmp_path / "x.db")
    assert [s for s, _ in queue(db, [StageName.IDENTIFY])] == ["identify", "group"]
    assert [s for s, _ in queue(db, [StageName.GROUP])] == ["group"]


def test_a_stage_with_no_work_is_an_error_not_a_shorter_queue(tmp_path):
    """`measure` esiste come stadio della posa ma non ha ancora un lavoro: chiederlo deve
    esplodere, non tornare una fila piu' corta in silenzio."""
    with pytest.raises(ValueError, match="measure"):
        queue(str(tmp_path / "x.db"), ["measure"])


def test_scanning_without_a_folder_is_an_error(tmp_path):
    """`scan` senza cartella e senza ricevuta esploderebbe dopo, dentro il generatore, nel
    thread del worker: la scansione risulterebbe partita e morirebbe muta."""
    with pytest.raises(ValueError, match="folder_id"):
        queue(str(tmp_path / "x.db"), [StageName.SCAN])


def test_scanning_without_a_receipt_is_an_error(tmp_path):
    """Lo stesso con la cartella ma senza ricevuta: un controllo sul solo `folder_id` passerebbe."""
    with pytest.raises(ValueError, match="run_id"):
        queue(str(tmp_path / "x.db"), [StageName.SCAN], folder_id=1)


def test_every_stage_closes_its_own_connection(tmp_path, monkeypatch):
    """Ogni stadio apre la sua connessione al DB e la chiude nel proprio `finally`: il worker
    non sa cosa sia uno stadio, e nessuno chiude al posto suo. Vale anche quando la corsa si
    ferma a meta' (Stop): il generatore si chiude, e il `finally` deve passare comunque."""
    chiuse = []

    class FintaConnessione:
        def close(self):
            chiuse.append(1)

    monkeypatch.setattr(run_mod, "connect", lambda *a, **k: FintaConnessione())
    monkeypatch.setattr(run_mod, "group_frames", lambda conn: iter([{"n": 1}, {"n": 2}]))
    ((_, fabbrica),) = run_mod.queue(str(tmp_path / "x.db"), [StageName.GROUP])

    list(fabbrica())  # corsa intera
    assert chiuse == [1]
    giro = fabbrica()  # corsa fermata a meta'
    next(giro)
    giro.close()
    assert chiuse == [1, 1]


def test_the_reader_extracts_exactly_what_gets_written(tmp_path):
    """La promessa in testa a `header_fields`: si legge SOLO cio' che finisce in `frames`.

    E' il difetto che questa fetta ha chiuso -- nove campi calcolati su ogni file e buttati --
    ed e' invisibile senza questa guardia, perche' `insert_frame` prende le colonne che gli
    servono e ignora in silenzio le chiavi in piu'. Vale nelle due direzioni: un campo che
    nessuno scrive e' lavoro sprecato, una colonna che nessuno estrae resta vuota per sempre."""
    estratti = set(asdict(extract_fields({}, "x"))) - {
        "path"
    }  # `path` non e' una colonna: e' il file
    # e i giudizi sul grezzo, che la scansione aggiunge ai campi prima di scrivere
    estratti |= set(header_asks.of({}))
    colonne = {scan_store._FIELD_OF.get(c, c) for c in scan_store.FRAME_COLUMNS}
    assert estratti == colonne


def test_invalidate_reopens_the_stage_and_everything_downstream(conn, tmp_path):
    write_light(tmp_path / "a.fits")
    run(conn, add_folder(conn, tmp_path))
    for s in stages.STAGES:
        stages.set_status(conn, 1, s, "done")
    stages.invalidate(conn, [1], "normalize")
    status = {r[0]: r[1] for r in conn.execute("SELECT stage, status FROM frame_stages")}
    assert status == {"solve": "done", "normalize": "pending", "identify": "pending",
                      "group": "pending", "measure": "done"}  # fmt: skip


def test_ready_waits_for_the_stages_upstream(conn, tmp_path):
    """Uno stadio vede una posa solo quando quelli da cui dipende hanno finito. L'ordine e'
    quello di arrivo: chi vuole un ordine suo se lo calcola (lo fa `solve`, ed e' l'unico)."""
    write_light(tmp_path / "b.fits", obj="NGC 7000", date="2024-05-17T22:00:00")
    write_light(tmp_path / "a.fits", obj="M 31", date="2024-05-17T21:00:00")
    run(conn, add_folder(conn, tmp_path))
    assert stages.ready(conn, "identify") == []  # solve e normalize non sono done
    for fid in (1, 2):
        stages.set_status(conn, fid, "solve", "done")
        stages.set_status(conn, fid, "normalize", "done")
    assert stages.ready(conn, "identify") == [1, 2]


def test_running_does_not_exist_in_the_db(conn, tmp_path):
    with pytest.raises(ValueError):
        stages.set_status(conn, 1, "solve", "running")
    assert "running" not in stages.StageStatus
    conn.execute(
        "INSERT INTO frames(frame_hash, image_type, header_json, created_at)"
        " VALUES('h1', 'light', '[]', 'now')"
    )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO frame_stages(frame_id, stage, status, updated_at)"
            " VALUES(1, 'solve', 'running', 'now')"
        )
    fid = add_folder(conn, tmp_path)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO scan_runs(folder_id, started_at, status) VALUES(?, 'now', 'running')",
            (fid,),
        )
    run_id = scan_store.start_run(conn, fid, "now")  # una corsa aperta: status NULL
    assert (
        conn.execute("SELECT status FROM scan_runs WHERE id = ?", (run_id,)).fetchone()[0] is None
    )


# --- dichiarato su chiavi stabili ----------------------------------------------------------


def test_declarations_and_aliases_key_on_stable_values(conn):
    conn.execute(
        "INSERT INTO declarations(entity_type, entity_key, field, value, created_at)"
        " VALUES('object', 'm-31', 'name', 'M 31', 'now')"
    )
    conn.execute(
        "INSERT INTO header_aliases(kind, header_value, target_key, created_at)"
        " VALUES('optics', 'askar 103apo', 'Askar 103 APO', 'now')"
    )
    conn.execute("DELETE FROM frames")  # un reset del rilevato
    assert conn.execute("SELECT COUNT(*) FROM declarations").fetchone()[0] == 1
    assert conn.execute("SELECT target_key FROM header_aliases").fetchone()[0] == "Askar 103 APO"
    with pytest.raises(Exception):  # noqa: B017 - niente numeri di riga nel dichiarato
        conn.execute("SELECT entity_id FROM declarations")


def test_a_single_frame_declares_only_its_object(conn):
    """L'utente risponde per gruppi; la sola risposta che scende sulla posa e' l'oggetto dei
    frame senza nome (ADR 0014, S2). Ogni altro campo per frame lo schema lo rifiuta."""
    conn.execute(
        "INSERT INTO declarations(entity_type, entity_key, field, value, created_at)"
        " VALUES('frame', 'abc123', 'object', 'name:Rosetta', 'now')"
    )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO declarations(entity_type, entity_key, field, value, created_at)"
            " VALUES('frame', 'abc123', 'filter', 'Ha', 'now')"
        )


# --- date canoniche --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("2024-05-17T21:00:00", "2024-05-17T21:00:00.000"),
        ("2024-05-17T21:00:00.1234567", "2024-05-17T21:00:00.123"),  # SGP a sette decimali
        ("2024-02-02T18:01:38.077877", "2024-02-02T18:01:38.077"),  # ASIAIR a sei
        ("2024-05-17T23:00:00+02:00", "2024-05-17T21:00:00.000"),  # un fuso esplicito
        ("2024-05-17T21:00:00Z", "2024-05-17T21:00:00.000"),
        ("non e' una data", None),
    ],
)
def test_dates_are_canonical_utc_with_milliseconds(raw, expected):
    assert canonical_utc(raw) == expected


def test_scan_writes_canonical_dates(conn, tmp_path):
    write_light(tmp_path / "a.fits", obj=" m31 ", date="2024-05-17T21:00:00.1234567",
                TELESCOP="Askar 103Apo", INSTRUME="ATR2600M")  # fmt: skip
    run(conn, add_folder(conn, tmp_path))
    row = conn.execute("SELECT date_obs FROM frames").fetchone()
    assert row["date_obs"] == "2024-05-17T21:00:00.123"


def test_the_solver_groups_by_night_not_by_calendar_day(conn, tmp_path):
    """Il solver risolve prima una posa per sessione, e la sessione tiene insieme la sera e il
    mattino dopo: le 22:00 del 17 e le 02:00 del 18 sono la stessa notte.

    La regola stava scritta in una colonna su ogni posa; adesso e' nella query di chi la usa,
    che e' l'unico. Il taglio e' a mezzogiorno UTC: qui si mette in fila, non si contano ore --
    la notte vera, col fuso del sito, la fa `group`."""
    write_light(tmp_path / "sera.fits", obj="M 31", date="2024-05-17T22:00:00")
    write_light(tmp_path / "mattino.fits", obj="M 31", date="2024-05-18T02:00:00")
    write_light(tmp_path / "altra.fits", obj="M 31", date="2024-05-19T22:00:00")
    # e un altro oggetto la STESSA notte: la sessione e' oggetto piu' notte, non solo notte
    write_light(tmp_path / "vicino.fits", obj="M 42", date="2024-05-17T23:00:00")
    run(conn, add_folder(conn, tmp_path))
    tutte = [r[0] for r in conn.execute("SELECT id FROM frames")]
    assert len(solve_store.first_per_order_key(conn, tutte)) == 3, (
        "due notti su M 31 piu' una su M 42: sera e mattino sono la stessa"
    )


def test_the_solver_keeps_two_rigs_of_the_same_night_apart(conn, tmp_path):
    """Stesso oggetto, stessa notte, ma due ottiche o due camere: sono cieli diversi (campo e
    scala diversi), e il solver ne deve risolvere uno per ciascuno. Se la chiave perdesse
    l'ottica -- o la camera -- questi frame finirebbero in un gruppo solo e tre quarti
    dell'archivio resterebbe senza cielo dopo il primo giro."""
    stesso = {"obj": "M 31", "date": "2024-05-17T22:00:00"}
    write_light(tmp_path / "a.fits", TELESCOP="Askar 103Apo", INSTRUME="ATR2600M", **stesso)
    write_light(tmp_path / "b.fits", TELESCOP="Askar 103Apo", INSTRUME="ATR2600M", **stesso)
    write_light(tmp_path / "c.fits", TELESCOP="RC 8", INSTRUME="ATR2600M", **stesso)  # altra ottica
    write_light(
        tmp_path / "d.fits", TELESCOP="Askar 103Apo", INSTRUME="ASI533MC", **stesso
    )  # altra camera  # noqa: E501
    run(conn, add_folder(conn, tmp_path))
    tutte = [r[0] for r in conn.execute("SELECT id FROM frames")]
    assert len(solve_store.first_per_order_key(conn, tutte)) == 3, (
        "a e b sono lo stesso corredo; c cambia l'ottica e d la camera"
    )


def test_the_night_in_sql_says_the_same_as_the_one_in_python(conn, tmp_path):
    """La notte della posa la scrive `scan` con `clock.night_date`, e la leggono in SQL
    `solve_store.SOLVE_ORDER_KEY` e `clock.NIGHT_SQL`, dentro una `GROUP BY`. Questo test le tiene
    incollate: le chiavi non si ricopiano, si chiedono al modulo, e la notte che ne esce deve essere
    quella di Python (qui senza sito, cioe' in UTC)."""
    istanti = [
        "2024-05-17T11:59:00",  # appena prima di mezzogiorno: e' ancora la notte di ieri
        "2024-05-17T12:00:00",  # mezzogiorno preciso: comincia la notte nuova
        "2024-05-17T22:00:00",
        "2024-05-18T02:00:00",  # il mattino dopo, stessa notte della sera
        "2024-12-31T23:30:00",  # a cavallo dell'anno
    ]
    for n, quando in enumerate(istanti):
        write_light(tmp_path / f"{n}.fits", obj="M 31", date=quando)
    run(conn, add_folder(conn, tmp_path))
    righe = conn.execute(
        f"SELECT date_obs, {solve_store.SOLVE_ORDER_KEY}, {NIGHT_SQL}"  # noqa: S608 - costanti dei moduli
        " FROM frames f"
    ).fetchall()
    assert len(righe) == len(istanti)
    for date_obs, chiave, notte in righe:
        assert chiave.split("|")[1] == night_date(date_obs), date_obs
        assert notte == night_date(date_obs), date_obs
