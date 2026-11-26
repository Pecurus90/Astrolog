"""Lo stadio `normalize`: dai grezzi dell'header ai filtri, agli strumenti e ai setup
dell'utente. Una regola, un test che si rompe se la regola si rompe.

L'archivio di prova e' quello sintetico (`synthetic.py`), non quello di Marco: gli header
sono dei quattro software supportati piu' i casi che rompono le assunzioni.
"""

from astrolog.spine import signature, stages
from astrolog.spine import signature_page as cards
from astrolog.spine.normalize import normalize_frames
from conftest import (
    frame_by_file,
    one,
    rows,
    run_normalize,
    scan,
    write_fits,
    write_light,
)
from synthetic import build_archive

# the 14 synthetic files minus Voyager, SGP and the rewritten copy, skipped by the scan (ADR 0029)
SYNTHETIC_FRAMES = 11
# --- il corpus: cosa esce dai quattro software ------------------------------------------


def test_normalize_vocab_corpus(conn, archive):
    """Il vocabolario attraversa gli header dei quattro software: ogni frame esce con il suo
    software normalizzato, e i filtri riconosciuti diventano filtri con la loro banda."""
    assert archive["status"] == "ok" and archive["normalized"] == SYNTHETIC_FRAMES

    software = {
        r["software"]: r["n"]
        for r in rows(conn, "SELECT software, COUNT(*) n FROM frames GROUP BY 1")
    }
    # Voyager, SGP e la copia riscritta non entrano piu' (ADR 0029, 26/11/2026)
    assert software == {"N.I.N.A.": 8, "ASIAIR": 3}

    bands = {r["name"]: r["passband"] for r in rows(conn, "SELECT name, passband FROM filters")}
    assert bands["Lum"] == "L" and bands["R"] == "R"
    assert bands["L-eXtreme"] == "DUO_HAOIII"  # un modello di catalogo porta la sua banda
    assert bands["OSC"] == "OSC"  # ASIAIR a colori senza filtro: la matrice e' la banda
    assert bands["N"] == "UNKNOWN"  # una lettera fuori dalla lista: non si indovina
    assert bands["X"] == "UNKNOWN"


def test_normalize_never_guesses_a_letter(conn, archive):
    """`N` resta `N` con banda sconosciuta: e' una domanda, e la risposta la da' chi ha ripreso."""
    f = frame_by_file(conn, "N_001.fits")
    assert one(conn, "SELECT passband FROM filters WHERE id = ?", (f["filter_id"],)) == "UNKNOWN"
    assert f["filter_raw"] == "N"  # il grezzo si conserva sempre


def test_normalize_bayer_decides_when_filter_is_none(conn, archive):
    """`FILTER = none`: con la matrice di Bayer e' una camera a colori; senza, non si assume
    niente e il frame resta senza filtro, da chiedere."""
    colour_frame = frame_by_file(conn, "Light_001.fits")  # ASIAIR: nessun FILTER, BAYERPAT c'e'
    assert one(conn, "SELECT name FROM filters WHERE id = ?", (colour_frame["filter_id"],)) == "OSC"
    mono_frame = frame_by_file(conn, "none_001.fits")  # mono che dice "none", nessun BAYERPAT
    assert mono_frame["filter_id"] is None
    assert one(conn, "SELECT COUNT(*) FROM filters WHERE name = 'OSC'") == 1


def test_normalize_keeps_the_filter_screwed_on_a_colour_camera(conn, archive):
    """Una camera a colori con un duo-banda davanti non e' OSC: il filtro c'e' e vale."""
    f = frame_by_file(conn, "Light_003.fits")
    assert one(conn, "SELECT name FROM filters WHERE id = ?", (f["filter_id"],)) == "L-eXtreme"


# --- le regole imparate -------------------------------------------------------------------


def test_normalize_alias_learned(conn, tmp_path):
    """Una regola imparata in Da confermare ("questa grafia e' questo strumento") vale sopra il
    vocabolario, e vale anche per i frame gia' normalizzati quando si rifa' lo stadio."""
    build_archive(tmp_path / "lib")
    scan(conn, tmp_path / "lib")
    run_normalize(conn)
    spellings = one(
        conn, "SELECT COUNT(*) FROM instruments WHERE kind = 'camera' AND name LIKE 'ATR2600M%'"
    )
    assert spellings == 2  # senza regola, due grafie sono due strumenti

    conn.execute(
        "INSERT INTO header_aliases(kind, header_value, target_key, created_at)"
        " VALUES('camera', 'atr2600m', 'ATR2600M(USB2.0)', 'ora')"
    )
    ids = [r["id"] for r in rows(conn, "SELECT id FROM frames")]
    stages.invalidate(conn, ids, "normalize")
    run_normalize(conn)

    camera_id = one(conn, "SELECT id FROM instruments WHERE name = 'ATR2600M(USB2.0)'")
    frame = frame_by_file(conn, "L_002.fits")
    assert one(conn, "SELECT camera_id FROM rigs WHERE id = ?", (frame["rig_id"],)) == camera_id


def test_normalize_applies_a_filter_rule(conn, tmp_path):
    """La risposta "N e' il mio Ha 3nm" vale per tutti i frame di quel filtro."""
    write_light(tmp_path / "a.fits", filt="N")
    write_light(tmp_path / "b.fits", filt="N", date="2024-05-17T22:00:00")
    conn.execute(
        "INSERT INTO filters(name, passband, created_at) VALUES('Antlia Pro Ha 3nm', 'HA', 'ora')"
    )
    conn.execute(
        "INSERT INTO header_aliases(kind, header_value, target_key, created_at)"
        " VALUES('filter', 'n', 'Antlia Pro Ha 3nm', 'ora')"
    )
    scan(conn, tmp_path)
    run_normalize(conn)
    band_query = "SELECT fi.passband FROM frames f JOIN filters fi ON fi.id = f.filter_id"
    assert {r["passband"] for r in rows(conn, band_query)} == {"HA"}
    assert one(conn, "SELECT COUNT(*) FROM filters") == 1  # nessun filtro provvisorio in piu'


# --- la copia calibrata ---------------------------------------------------------------------


def test_normalize_calibrated_copy(conn, tmp_path):
    """Una copia N.I.N.A. che dice `CALSTAT` accanto al grezzo: stessa data, camera ed
    esposizione. E' lo stesso scatto, il grezzo vince, le ore non raddoppiano. La copia con
    `PROGRAM` o a pixel float non entra piu' (ADR 0029, 26/11/2026)."""
    same = {"INSTRUME": "ATR2600M", "date": "2024-10-31T21:00:00"}
    write_light(tmp_path / "raw.fits", **same)
    write_light(tmp_path / "cal.fits", CALSTAT="BDF", **same)
    scan(conn, tmp_path)
    assert run_normalize(conn)["copies"] == 1
    copy_row, raw_row = frame_by_file(conn, "cal.fits"), frame_by_file(conn, "raw.fits")
    assert copy_row["software"] == raw_row["software"] == "N.I.N.A."
    assert copy_row["rewrite_mark"] == "calibrated" and raw_row["rewrite_mark"] is None
    assert copy_row["copy_of"] == raw_row["id"] and raw_row["copy_of"] is None
    assert one(conn, "SELECT SUM(exposure_s) FROM frames WHERE copy_of IS NULL") == 300.0


def test_normalize_does_not_guess_between_two_twins_that_say_nothing(conn, tmp_path):
    """Lo stesso scatto due volte e nessun indizio su chi sia l'originale: si contano tutti e
    due (Marco, 10/9/2026). Indovinare fonderebbe due frame veri ripresi nello stesso istante,
    e far sparire cielo vero e' peggio di contarlo due volte."""
    same = {"INSTRUME": "ASI2600MM", "date": "2024-05-17T21:00:00"}
    write_light(tmp_path / "a.fits", SWCREATE="N.I.N.A. 3.1", **same)
    write_light(tmp_path / "b.fits", SWCREATE="N.I.N.A. 3.1", **same)
    scan(conn, tmp_path)
    assert run_normalize(conn)["copies"] == 0
    assert one(conn, "SELECT COUNT(*) FROM frames WHERE copy_of IS NULL") == 2


def test_normalize_a_marked_frame_without_a_twin_still_counts(conn, tmp_path):
    """Il marchio decide chi vince fra due gemelli, mai se un frame conta: chi ha tenuto solo
    il file calibrato le vede tutte."""
    write_light(tmp_path / "cal.fits", INSTRUME="ASI2600MM", CALSTAT="BDF")
    scan(conn, tmp_path)
    assert run_normalize(conn)["copies"] == 0
    assert one(conn, "SELECT SUM(exposure_s) FROM frames WHERE copy_of IS NULL") == 300.0


def test_normalize_does_not_call_a_second_pose_a_copy(conn, tmp_path):
    """Due frame veri della stessa notte con la stessa camera non sono una copia: la data
    e' diversa."""
    write_light(tmp_path / "a.fits", date="2024-05-17T21:00:00")
    write_light(tmp_path / "b.fits", date="2024-05-17T21:05:00")
    scan(conn, tmp_path)
    assert run_normalize(conn)["copies"] == 0
    assert one(conn, "SELECT COUNT(*) FROM frames WHERE copy_of IS NULL") == 2


# --- lo stadio come stadio ------------------------------------------------------------------


def test_normalize_is_incremental_and_idempotent(conn, tmp_path):
    """Girare due volte non cambia niente e non ricrea nulla: il secondo giro non ha lavoro."""
    build_archive(tmp_path / "lib")
    scan(conn, tmp_path / "lib")
    first_run = run_normalize(conn)
    before = one(conn, "SELECT COUNT(*) FROM filters") + one(conn, "SELECT COUNT(*) FROM rigs")
    second_run = run_normalize(conn)
    assert first_run["normalized"] == SYNTHETIC_FRAMES and second_run["normalized"] == 0
    assert (
        one(conn, "SELECT COUNT(*) FROM filters") + one(conn, "SELECT COUNT(*) FROM rigs") == before
    )
    assert stages.count_pending(conn, "normalize") == 0


def test_normalize_reopens_downstream_when_it_changes_something(conn, tmp_path):
    """Cambiare il filtro di un frame gia' lavorato rimette in coda cio' che dipende da lui,
    passando da `invalidate`: e' l'unica via."""
    write_light(tmp_path / "a.fits", filt="L")
    scan(conn, tmp_path)
    run_normalize(conn)
    fid = one(conn, "SELECT id FROM frames")
    conn.execute("INSERT INTO filters(name, passband, created_at) VALUES('Chroma L', 'L', 'ora')")
    conn.execute(
        "INSERT INTO header_aliases(kind, header_value, target_key, created_at)"
        " VALUES('filter', 'l', 'Chroma L', 'ora')"
    )
    stages.invalidate(conn, [fid], "normalize")  # e' cio' che fa la risposta dell'utente
    for stage in ("solve", "identify", "group"):
        # dopo l'invalidazione, e non prima: cosi' solo normalize puo' riaprirli, e il test
        # diventa rosso se lo stadio smette di chiamare `invalidate`
        stages.set_status(conn, fid, stage, "done")
    run_normalize(conn)
    statuses = {
        r["stage"]: r["status"] for r in rows(conn, "SELECT stage, status FROM frame_stages")
    }
    assert statuses["identify"] == "pending" and statuses["group"] == "pending"
    assert statuses["solve"] == "done"  # solve non dipende da normalize: non si tocca


def test_normalize_stop_leaves_a_coherent_prefix(conn, tmp_path):
    """Fermare ferma fra un frame e l'altro, a transazione chiusa: cio' che e' fatto e' fatto."""
    build_archive(tmp_path / "lib")
    scan(conn, tmp_path / "lib")
    gen = normalize_frames(conn)
    for i, _event in enumerate(gen):
        if i == 2:
            break
    gen.close()
    done_now = one(
        conn, "SELECT COUNT(*) FROM frame_stages WHERE stage='normalize' AND status='done'"
    )
    assert 0 < done_now < SYNTHETIC_FRAMES
    assert stages.count_pending(conn, "normalize") == SYNTHETIC_FRAMES - done_now


def test_normalize_survives_a_frame_without_anything(conn, tmp_path):
    """Un frame senza filtro, senza ottica e senza camera entra lo stesso e non rompe nulla."""
    write_light(tmp_path / "vuoto.fits", obj=None, filt=None)
    scan(conn, tmp_path)
    receipt = run_normalize(conn)
    assert receipt["status"] == "ok" and receipt["normalized"] == 1
    row = conn.execute("SELECT filter_id, rig_id FROM frames").fetchone()
    assert row["filter_id"] is None and row["rig_id"] is None
    assert stages.count_pending(conn, "normalize") == 0


def test_normalize_falls_back_when_a_rule_points_at_a_deleted_filter(conn, tmp_path):
    """Se l'utente cancella un filtro a cui una regola puntava, il frame non resta senza
    filtro in silenzio: si torna al vocabolario e lo si scrive nel log."""
    write_light(tmp_path / "a.fits", filt="L")
    conn.execute(
        "INSERT INTO header_aliases(kind, header_value, target_key, created_at)"
        " VALUES('filter', 'l', 'Un filtro cancellato', 'ora')"
    )
    scan(conn, tmp_path)
    run_normalize(conn)
    name = one(
        conn,
        "SELECT fi.name FROM frames f JOIN filters fi ON fi.id = f.filter_id",
    )
    assert name == "Lum"


def test_normalize_rig_focal_is_the_median_and_ignores_the_file_order(conn, archive):
    """Il rappresentante del gruppo di focali e' la mediana dei distinti, non la prima letta:
    con 561, 560 e 559 il setup si chiama 560 anche se il primo file letto porta 561."""
    focals = {r["focal_mm"] for r in rows(conn, "SELECT DISTINCT focal_mm FROM rigs")}
    assert focals == {560.0}  # 910 di Voyager e 1624 di SGP non entrano piu' (ADR 0029)


def test_normalize_a_zero_focal_length_does_not_explode(conn, tmp_path):
    """Una reflex che scrive FOCALLEN = 0 non e' "focale ignota": due frame cosi' devono finire
    nello stesso setup, non far cadere la corsa su un vincolo del database."""
    for i in range(2):
        write_light(
            tmp_path / f"a{i}.fits",
            date=f"2024-05-17T21:0{i}:00",
            FOCALLEN=0.0,
            TELESCOP="Reflex senza focale",
            INSTRUME="Canon EOS 700D",
        )
    scan(conn, tmp_path)
    receipt = run_normalize(conn)
    assert receipt["status"] == "ok" and receipt["errors"] == 0
    assert one(conn, "SELECT COUNT(*) FROM rigs") == 1


def test_normalize_a_broken_frame_does_not_stop_the_others(conn, tmp_path, monkeypatch):
    """Un frame che esplode diventa `failed` col suo perche', e la corsa va avanti: e' lo
    stesso patto della scansione, che conta i file illeggibili e continua."""
    import astrolog.spine.normalize as normalize_mod

    for i in range(3):
        write_light(tmp_path / f"a{i}.fits", obj=f"M {i}", date=f"2024-05-17T21:0{i}:00")
    scan(conn, tmp_path)
    real = normalize_mod.rig_for_frame

    # Gli argomenti si passano come arrivano: questo finto serve a far esplodere UN frame, non
    # a ricopiare la firma di chi fa il setup. Copiata, era rimasta indietro di un argomento e
    # faceva fallire tutti i frame con un `TypeError` invece dell'errore che il test vuole provare.
    def explode(conn_, frame, *args, **kwargs):
        if frame["object_raw"] == "M 1":
            raise RuntimeError("disco che sparisce")
        return real(conn_, frame, *args, **kwargs)

    monkeypatch.setattr(normalize_mod, "rig_for_frame", explode)
    receipt = run_normalize(conn)
    assert receipt["normalized"] == 2 and receipt["errors"] == 1
    recorded = rows(conn, "SELECT status, reason FROM frame_stages WHERE stage = 'normalize'")
    assert {r["status"] for r in recorded} == {"done", "failed"}
    assert [r["reason"] for r in recorded if r["status"] == "failed"] == ["internal_error"]


def test_normalize_the_raw_arriving_after_its_copy_still_wins(conn, tmp_path):
    """La copia entra per prima (la cartella del grezzo si scansiona dopo): quando il grezzo
    arriva, la copia torna in coda e smette di contare come un'altra ora di cielo. La copia e'
    la forma `CALSTAT`: quella con `PROGRAM` non entra piu' (ADR 0029, 26/11/2026)."""
    same = {"INSTRUME": "ATR2600M", "date": "2024-10-31T21:00:00"}
    write_light(tmp_path / "copie" / "cal.fits", CALSTAT="BDF", **same)
    scan(conn, tmp_path / "copie")
    assert run_normalize(conn)["copies"] == 0
    copy_id = frame_by_file(conn, "cal.fits")["id"]
    assert one(conn, "SELECT copy_of FROM frames WHERE id = ?", (copy_id,)) is None

    write_light(tmp_path / "grezzi" / "raw.fits", **same)  # ora arriva anche il grezzo
    scan(conn, tmp_path / "grezzi")
    receipt = run_normalize(conn)
    raw_id = frame_by_file(conn, "raw.fits")["id"]
    assert one(conn, "SELECT copy_of FROM frames WHERE id = ?", (copy_id,)) == raw_id
    # il grezzo nuovo piu' la copia vecchia, rientrata nello stesso giro
    assert receipt["normalized"] == receipt["total"] == 2
    assert receipt["copies"] == 1


def test_normalize_counts_what_is_left_to_confirm(conn, archive):
    """Il numero da confermare dice il vero: un filtro con banda sconosciuta (`N`) e un frame
    senza filtro contano, un filtro riconosciuto no."""
    assert archive["to_review"] == 3  # le due lettere N e X, piu' il mono che dice "none"
    # nove strumenti: un'ottica, tre camere, DUE montature -- l'ASIAIR del banco ne scrive due nomi
    # in TELESCOP -- piu' ruota e focheggiatore di N.I.N.A. e la camera di guida dell'ASIAIR; le
    # ottiche e camere di Voyager e SGP non entrano piu' (ADR 0029)
    assert archive["instruments"] == 9 and archive["rigs"] == 3


def test_normalize_an_unknown_focal_length_is_not_the_same_rig(conn, tmp_path):
    """Una focale ignota da una parte sola non e' "la stessa focale": due setup, non uno."""
    write_light(tmp_path / "a.fits", date="2024-05-17T21:00:00", TELESCOP="T", INSTRUME="C",
                FOCALLEN=559.0)  # fmt: skip
    write_light(tmp_path / "b.fits", date="2024-05-17T21:05:00", TELESCOP="T", INSTRUME="C")
    scan(conn, tmp_path)
    run_normalize(conn)
    assert {r["focal_mm"] for r in rows(conn, "SELECT focal_mm FROM rigs")} == {559.0, None}


def test_normalize_says_it_when_a_rule_is_stale(conn, tmp_path, caplog):
    """Il ripiego sul vocabolario non e' muto: chi legge il log sa che una regola punta a un
    filtro che non c'e' piu'."""
    write_light(tmp_path / "a.fits", filt="L")
    conn.execute(
        "INSERT INTO header_aliases(kind, header_value, target_key, created_at)"
        " VALUES('filter', 'l', 'Un filtro cancellato', 'ora')"
    )
    scan(conn, tmp_path)
    with caplog.at_level("WARNING", logger="astrolog.spine.normalize"):
        run_normalize(conn)
    assert any("filtro sparito" in r.message for r in caplog.records)


CARD = {"IMAGETYP": "Light Frame", "OBJECT": "M 31", "EXPTIME": 300.0}


def test_normalize_reads_the_colour_of_the_camera_not_of_the_single_pose(conn, tmp_path):
    """A essere a colori e' la CAMERA, non il frame: il programma che non scrive `BAYERPAT` non fa
    un frame mono in mezzo agli altri, nemmeno nel giro che scopre la camera: i file votano prima
    del giro. E una camera a colori non si chiede (Marco, 23/9/2026)."""
    for i, bayer in enumerate(({}, *[{"BAYERPAT": "RGGB"}] * 3)):
        write_fits(tmp_path / f"{i}.fits", {**CARD, "INSTRUME": "Cam", **bayer,
                                            "DATE-OBS": f"2024-05-17T21:0{i}:00"})  # fmt: skip
    scan(conn, tmp_path)
    assert run_normalize(conn)["to_review"] == 0
    assert one(conn, "SELECT camera_type FROM instruments WHERE name = 'Cam'") == "color"
    prima = frame_by_file(conn, "0.fits")
    assert one(conn, "SELECT name FROM filters WHERE id = ?", (prima["filter_id"],)) == "OSC"
    write_fits(tmp_path / "poi" / "4.fits", {**CARD, "INSTRUME": "Cam",
                                             "DATE-OBS": "2024-05-17T21:04:00"})  # fmt: skip
    scan(conn, tmp_path / "poi")
    run_normalize(conn)
    dopo = frame_by_file(conn, "4.fits")
    assert one(conn, "SELECT name FROM filters WHERE id = ?", (dopo["filter_id"],)) == "OSC"
    assert [g for g in cards.by_signature(conn) if g["asks_filter"]] == []


def test_normalize_a_copy_does_not_vote_the_colour_before_the_round(conn, tmp_path):
    """La copia calibrata non e' un altro frame, e non vota nemmeno prima del giro: un grezzo con la
    matrice e uno senza sono pari, la camera non e' a colori, e il frame senza matrice tiene il suo
    filtro -- e nessuna torna in coda a fine corsa per un voto che non era quello usato."""
    same = {**CARD, "INSTRUME": "Cam", "FILTER": "L"}
    write_fits(tmp_path / "a.fits", {**same, "DATE-OBS": "2024-05-17T21:00:00"})
    for name, extra in [("b.fits", {}), ("b_cal.fits", {"CALSTAT": "BDF"})]:
        write_fits(tmp_path / name, {**same, "DATE-OBS": "2024-05-17T21:01:00",
                                     "BAYERPAT": "RGGB", **extra})  # fmt: skip
    scan(conn, tmp_path)
    run_normalize(conn)
    assert one(conn, "SELECT camera_type FROM instruments WHERE name = 'Cam'") is None
    senza = one(
        conn,
        "SELECT fl.name FROM frames f JOIN filters fl ON fl.id = f.filter_id"
        " WHERE f.bayer_pattern IS NULL",
    )
    assert senza == "Lum"  # il nome che il vocabolario da' a `L`, non OSC
    assert stages.ready(conn, "normalize") == []


def test_normalize_passes_each_pose_once(conn, tmp_path, monkeypatch):
    """Il colore della camera si vota prima del giro, sui frame che avra' alla fine: il frame
    senza matrice sceglie il filtro sapendolo, e nessuna si rifa', ne' ora ne' alla corsa dopo."""
    for i, bayer in enumerate(({}, *[{"BAYERPAT": "RGGB"}] * 3)):
        write_fits(tmp_path / f"{i}.fits", {**CARD, "INSTRUME": "Cam", **bayer,
                                            "DATE-OBS": f"2024-05-17T21:0{i}:00"})  # fmt: skip
    scan(conn, tmp_path)
    from astrolog.spine import normalize as normalize_mod

    worked = []
    real = normalize_mod._one_frame

    def counted(c, frame_id, *args):
        worked.append(frame_id)
        return real(c, frame_id, *args)

    monkeypatch.setattr(normalize_mod, "_one_frame", counted)
    run_normalize(conn)
    assert len(worked) == len(set(worked)) == 4
    assert stages.ready(conn, "normalize") == []


def test_normalize_a_camera_answered_no_filter_gives_unfiltered_poses_one_row(conn, tmp_path):
    """ "Nessun filtro" sulla firma: i frame vanno sulla riga "nessun filtro", una sola, ritrovata
    anche rinominata. Se manca e il suo nome e' gia' di un altro filtro, il frame resta da
    rivedere."""
    for i in range(2):
        write_fits(tmp_path / f"{i}.fits", {**CARD, "INSTRUME": "Mono",
                                            "DATE-OBS": f"2024-05-17T21:0{i}:00"})  # fmt: skip
    scan(conn, tmp_path)
    assert run_normalize(conn)["to_review"] == 2  # nessuno ha risposto: non si inventa
    assert one(conn, "SELECT COUNT(*) FROM filters") == 0
    ids = [r["id"] for r in rows(conn, "SELECT id FROM frames")]

    def rinormalizza():
        stages.invalidate(conn, ids, "normalize")
        return run_normalize(conn)["to_review"]

    chiave = signature.key_of(signature.parts_of(rows(conn, "SELECT * FROM frames")[0]))
    signature.declare(conn, chiave, signature.Answer(filter=signature.FilterAnswer.NO_FILTER))
    assert rinormalizza() == 0
    assert [g["answer"]["filter"] for g in cards.by_signature(conn)] == ["no_filter"]
    assert rows(conn, "SELECT name, is_none FROM filters") == [{"name": "None", "is_none": 1}]
    conn.execute("UPDATE filters SET name = 'Nessun filtro'")
    assert rinormalizza() == 0 and one(conn, "SELECT COUNT(*) FROM filters") == 1
    conn.execute("UPDATE filters SET is_none = 0, name = 'None'")  # il nome c'e', la riga no
    assert rinormalizza() == 2
