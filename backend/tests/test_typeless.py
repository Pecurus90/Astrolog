"""Le regole della domanda "che file e' questo", provate da sole.

Un file che non dice `IMAGETYP` non e' un light: potrebbe essere una foto del cielo o un file di
calibrazione. Lo dice il cielo (Marco, 23/9/2026): risolto e' una foto, senza stelle e' una
calibrazione, e solo dove il cielo non sa dire si chiede. Finche' non si sa, quel frame **aspetta
una risposta, non il suo turno**: non e' pronto per l'oggetto ne' per cio' che viene dopo, e non
conta nel residuo della spina. Qui si guarda la REGOLA, senza API; che poi l'app la faccia davvero
lo guarda `test_review_typeless.py`.
"""

import importlib

import pytest

from astrolog.spine import declarations as decl
from astrolog.spine import frame_folder, solve_store, typeless, typeless_answer, typeless_folders
from astrolog.spine.stages import STAGES, count_pending, invalidate, mark_pending, ready, set_status
from conftest import add_folder, sky_solved

CHIAVI = [
    ("il file sta nella radice", "D:/Astro", "", "D:/Astro"),
    ("una sottocartella", "D:/Astro", "dark/", "D:/Astro/dark"),
    ("tre livelli", "D:/Astro", "2026-03-14/M51/LIGHT/", "D:/Astro/2026-03-14/M51/LIGHT"),
    ("le barre di Windows", "D:\\Astro", "dark/", "D:/Astro/dark"),
    ("una cartella di rete", "\\\\NAS\\Foto", "dark/", "//NAS/Foto/dark"),
    ("la radice con la barra in coda", "D:/Astro/", "dark/", "D:/Astro/dark"),
    ("spazi e accenti", "D:/Astro", "notte 1/perseidi a'/", "D:/Astro/notte 1/perseidi a'"),
]  # fmt: skip


def _frame(conn, folder_id, rel_path, *, image_type="unknown", copy_of=None,
           sky: str | None = "no_solution", normalized=False):  # fmt: skip
    """Un frame con la sua posizione, senza scrivere un FITS. `sky` e' cio' che il cielo ha detto:
    `None` se non l'ha ancora guardato, `"done"` se l'ha risolto, altrimenti il motivo per cui ha
    rinunciato -- di norma "nessuna soluzione", cioe' il cielo che non sa dire."""
    frame_id = conn.execute(
        "INSERT INTO frames(frame_hash, image_type, copy_of, header_json, created_at)"
        " VALUES(?, ?, ?, '[]', 'ora')",
        (f"{folder_id}:{rel_path}", image_type, copy_of),
    ).lastrowid
    conn.execute(
        "INSERT INTO positions(frame_id, folder_id, rel_path, filesize, mtime, seen_at)"
        " VALUES(?, ?, ?, 1, 1.0, 'ora')",
        (frame_id, folder_id, rel_path),
    )
    mark_pending(conn, frame_id, "ora")
    if normalized:  # l'oggetto aspetta anche la normalizzazione
        set_status(conn, frame_id, "normalize", "done")
    if sky == "done":
        sky_solved(conn, frame_id)
    elif sky is not None:
        set_status(conn, frame_id, "solve", "failed", reason=sky)
    return frame_id


def _cartelle(conn):
    """Le cartelle della domanda come le scriverebbe la fine di uno stadio: qui si prova la
    regola del conto, e le pose si fanno a mano."""
    typeless_folders.write(conn)
    return typeless.by_folder(conn)


def _riga(conn, key):
    typeless_folders.write(conn)
    return typeless.row_of(conn, key)


@pytest.mark.parametrize(
    "radice, sotto, attesa", [c[1:] for c in CHIAVI], ids=[c[0] for c in CHIAVI]
)
def test_the_key_of_a_folder_says_the_same_thing_in_sql_and_in_python(conn, radice, sotto, attesa):
    """La chiave della cartella si compone in due lingue -- in Python per la pagina, in SQL per chi
    deve confrontarla dentro una query (`spine/stages.py`) -- e devono dire la stessa cosa. Se
    divergessero, una cartella risposta resterebbe "senza risposta" per la spina, e quei frame non
    ripartirebbero mai."""
    folder_id = add_folder(conn, radice)
    _frame(conn, folder_id, f"{sotto}a.fits")
    sql = f"SELECT ({frame_folder.KEY_OF_FRAME}) AS k FROM frames f"  # noqa: S608 - una costante
    riga = conn.execute(sql).fetchone()
    assert frame_folder.folder_key(radice, sotto) == attesa
    assert riga["k"] == attesa


def test_the_frames_of_a_folder_are_those_whose_first_live_position_is_there(conn):
    """Chi risponde prende le pose della cartella della riga: non quelle delle sue sottocartelle,
    non quelle di una cartella accanto che si chiama quasi uguale, non quelle la cui prima
    posizione viva sta in un'altra cartella. Anche quando la cartella e' la radice."""
    radice = add_folder(conn, "D:/Astro")
    # ai due capi dell'ordine: segni che vengono prima dello `0`, dopo la `z`, sopra l'ASCII,
    # l'ultimo carattere
    ultimi = ["!.fits", "-0.fits", "0.fits", "zz.fits", "\u00e9.fits", "\U0010ffff.fits"]
    qui = [
        _frame(conn, radice, "dark/a.fits"),
        *(_frame(conn, radice, f"dark/{u}") for u in ultimi),
    ]
    _frame(conn, radice, "dark/sotto/b.fits")
    _frame(conn, radice, "dark2/c.fits")
    in_radice = [_frame(conn, radice, "dark.fits"), *(_frame(conn, radice, u) for u in ultimi)]
    altrove = _frame(conn, add_folder(conn, "C:/Prima"), "e.fits")
    conn.execute(
        "INSERT INTO positions(frame_id, folder_id, rel_path, filesize, mtime, seen_at)"
        " VALUES(?, ?, 'dark/e.fits', 1, 1.0, 'ora')",
        (altrove, radice),
    )

    def pose(sub):
        return sorted(
            r["id"] for r in frame_folder.frames_in(conn, {"root": "D:/Astro", "sub": sub})
        )

    assert pose("dark/") == sorted(qui)
    assert pose("") == sorted(in_radice)


def test_the_frames_of_a_folder_are_looked_up_from_the_folder(conn):
    """Si parte dalla cartella e si scende per indice alle sue posizioni: partire dalle pose
    ricomporrebbe la cartella di ognuna dell'archivio, a ogni risposta."""
    piano = " ".join(
        r[3]
        for r in conn.execute("EXPLAIN QUERY PLAN " + frame_folder._IN_FOLDER, ("", "", "", ""))
    )
    assert "SEARCH p USING INDEX sqlite_autoindex_positions_1 (folder_id=? AND rel_path>?" in piano
    assert "SCAN" not in piano, piano


def test_the_groups_are_the_folders_that_hold_the_files(conn):
    """Si chiede per cartella (Marco, 17/9/2026): chi riprende tiene dark e flat in cartelle loro,
    quindi una risposta chiude una cartella intera. La piu' numerosa in cima."""
    radice = add_folder(conn, "D:/Astro")
    _frame(conn, radice, "2026-03-14/dark/a.fits")
    _frame(conn, radice, "2026-03-14/dark/b.fits")
    _frame(conn, radice, "2026-03-21/M51/c.fits")
    assert [(g["key"], g["frames"]) for g in _cartelle(conn)] == [
        ("D:/Astro/2026-03-14/dark", 2),
        ("D:/Astro/2026-03-21/M51", 1),
    ]


def test_only_the_frames_whose_header_does_not_say_the_type_are_asked(conn):
    """Un file che dice di essere un light non e' una domanda: la domanda nasce dal silenzio
    dell'header, non dalla cartella."""
    radice = add_folder(conn, "D:/Astro")
    _frame(conn, radice, "M51/detto.fits", image_type="light")
    assert _cartelle(conn) == []
    _frame(conn, radice, "M51/muto.fits")
    assert [(g["key"], g["frames"]) for g in _cartelle(conn)] == [("D:/Astro/M51", 1)]


def test_a_copy_does_not_count_as_another_frame(conn):
    """Le copie riscritte non si contano a video, come in ogni conteggio dell'app: le ore di una
    copia le conta il suo originale."""
    radice = add_folder(conn, "D:/Astro")
    originale = _frame(conn, radice, "M51/a.fits")
    _frame(conn, radice, "M51/a_copia.fits", copy_of=originale)
    assert [g["frames"] for g in _cartelle(conn)] == [1]


def test_a_folder_with_only_copies_is_not_a_question(conn):
    """Una cartella dove ogni frame e' la copia di un altro non chiede niente: non c'e' nessun
    frame di cui dire che file e', e una domanda su zero frame non si capisce."""
    radice = add_folder(conn, "D:/Astro")
    originale = _frame(conn, radice, "M51/a.fits")
    _frame(conn, radice, "copie/a_copia.fits", copy_of=originale)
    assert [g["key"] for g in _cartelle(conn)] == ["D:/Astro/M51"]


def test_a_folder_stays_a_question_until_someone_answers(conn):
    """Senza risposta la cartella non ne porta nessuna; con la risposta, la risposta resta scritta
    sulla sua riga. Quanto conta nella pagina lo prova `test_review_typeless.py`."""
    radice = add_folder(conn, "D:/Astro")
    _frame(conn, radice, "dark/a.fits")
    riga = _riga(conn, "D:/Astro/dark")
    assert riga["answer"] is None
    typeless.declare(conn, "D:/Astro/dark", typeless.CALIBRATION)
    riga = _riga(conn, "D:/Astro/dark")
    assert riga["answer"] == typeless.CALIBRATION


@pytest.mark.parametrize("scritto", ["luce", "", None, 42])
def test_an_answer_that_cannot_be_read_is_no_answer(conn, scritto):
    """Una riga storta vale **nessuna risposta**: i frame restano ad aspettare invece di diventare
    ore su un'ipotesi. Le due parole ammesse sono quelle del vocabolario, non una qualunque."""
    radice = add_folder(conn, "D:/Astro")
    _frame(conn, radice, "dark/a.fits")
    decl.write_declaration(conn, decl.FOLDER, "D:/Astro/dark", decl.FOLDER_TYPE, scritto, "ora")
    assert typeless.answer(conn, "D:/Astro/dark") is None
    assert _riga(conn, "D:/Astro/dark")["answer"] is None


def test_a_frame_without_a_type_goes_to_the_sky_first(conn):
    """E' il cielo a dire che file e' (Marco, 23/9/2026): il frame senza tipo va al solver come
    gli altri, e intanto non e' ne' una domanda ne' pronto per l'oggetto."""
    radice = add_folder(conn, "D:/Astro")
    muto = _frame(conn, radice, "dark/a.fits", sky=None)
    assert ready(conn, "solve") == [muto]
    assert _cartelle(conn) == []


def test_a_frame_the_sky_solves_is_a_photo_of_the_sky(conn):
    """Risolto sul cielo: e' una foto, va avanti come un light e non si chiede."""
    radice = add_folder(conn, "D:/Astro")
    muto = _frame(conn, radice, "M51/a.fits", sky="done", normalized=True)
    assert ready(conn, "identify") == [muto]
    assert _cartelle(conn) == []


def test_a_frame_without_stars_is_calibration_and_is_not_asked(conn):
    """Nessuna stella: e' un file di calibrazione -- un dark, un bias, un flat -- e resta fuori
    dalle ore senza chiedere. Anche il `failed` del cielo, che per un light manda avanti dal nome,
    qui non manda avanti niente: e' proprio li' che un dark diventerebbe ore."""
    radice = add_folder(conn, "D:/Astro")
    muto = _frame(conn, radice, "dark/a.fits", sky="no_stars", normalized=True)
    assert muto not in ready(conn, "identify")
    assert _cartelle(conn) == []
    assert count_pending(conn, "identify") == 0


def test_stars_without_a_solution_are_the_sky_that_cannot_say(conn):
    """Stelle ma nessuna soluzione, o il tempo scaduto: il cielo non sa dire, e si chiede. Il
    frame aspetta davanti all'oggetto, non davanti al cielo."""
    radice = add_folder(conn, "D:/Astro")
    for motivo in ("no_solution", "timeout"):
        muto = _frame(conn, radice, f"M51/{motivo}.fits", sky=motivo)
        assert muto not in ready(conn, "identify")
    assert [(g["key"], g["frames"]) for g in _cartelle(conn)] == [("D:/Astro/M51", 2)]


def test_an_asked_folder_counts_every_frame_its_answer_moves(conn):
    """La risposta vale per la cartella: una cartella che si chiede conta tutti i suoi frame senza
    tipo, anche quelli che il cielo ha gia' deciso, perche' la risposta li sposta tutti."""
    radice = add_folder(conn, "D:/Astro")
    _frame(conn, radice, "mista/a.fits")
    _frame(conn, radice, "mista/b.fits", sky="no_stars")
    _frame(conn, radice, "mista/c.fits", sky="done")
    assert [g["frames"] for g in _cartelle(conn)] == [3]


def test_calibration_written_by_the_user_holds_even_where_the_sky_solved(conn):
    """La risposta e' scritta, e vince sul cielo: un frame risolto in una cartella detta di
    calibrazione non va avanti."""
    radice = add_folder(conn, "D:/Astro")
    muto = _frame(conn, radice, "dark/a.fits", sky="done", normalized=True)
    _frame(conn, radice, "dark/b.fits")
    typeless.declare(conn, "D:/Astro/dark", typeless.CALIBRATION)
    assert muto not in ready(conn, "identify")


def test_a_frame_that_waits_is_not_work_left_to_do(conn):
    """Un frame che aspetta una risposta non e' lavoro in coda: il residuo del cielo e di cio' che
    viene dopo resta a zero. Se contasse, ogni Avvia ripartirebbe per niente e sul NAS la cadenza
    automatica girerebbe a vuoto per sempre. La normalizzazione invece si fa lo stesso: i filtri e
    gli strumenti di quel file si leggono comunque."""
    radice = add_folder(conn, "D:/Astro")
    _frame(conn, radice, "dark/a.fits")
    residuo = {s: count_pending(conn, s) for s in STAGES}
    assert [s for s, quanti in residuo.items() if quanti] == ["normalize"]


def test_another_answer_does_not_send_a_waiting_frame_on(conn):
    """Una risposta data in un'altra sezione -- la camera di quei frame, l'oggetto -- rimette
    in coda i frame, e quello che aspetta il suo tipo **non** deve partire per questo. E' la
    ragione per cui il fermo e' scritto sulla posa e non fra gli stati degli stadi: uno stato lo
    cancellerebbe proprio questa `invalidate`."""
    radice = add_folder(conn, "D:/Astro")
    frame_id = _frame(conn, radice, "dark/a.fits")
    invalidate(conn, [frame_id], "normalize")
    assert ready(conn, "identify") == []
    assert count_pending(conn, "identify") == 0


def test_saying_it_is_a_photo_of_the_sky_sends_those_frames_on(conn):
    """ "E' una foto del cielo" rimette in coda i frame di quella cartella: da li' in poi fanno la
    strada di un light: il cielo non li aveva risolti, e l'oggetto si prende dal nome."""
    radice = add_folder(conn, "D:/Astro")
    frame_id = _frame(conn, radice, "M51/a.fits", normalized=True)
    typeless.declare(conn, "D:/Astro/M51", typeless.LIGHT)
    assert typeless_answer.apply_answer(conn, _riga(conn, "D:/Astro/M51")) == [frame_id]
    assert ready(conn, "identify") == [frame_id]


def test_saying_it_is_calibration_leaves_those_frames_where_they_are(conn):
    """ "E' un file di calibrazione" non manda avanti niente: i file di calibrazione nuovi non
    entrano, e questi, gia' entrati, restano dove sono, senza diventare ore."""
    radice = add_folder(conn, "D:/Astro")
    muto = _frame(conn, radice, "dark/a.fits")
    typeless.declare(conn, "D:/Astro/dark", typeless.CALIBRATION)
    typeless_answer.apply_answer(conn, _riga(conn, "D:/Astro/dark"))
    assert muto not in ready(conn, "identify")


def test_changing_idea_to_calibration_takes_back_what_the_sky_had_written(conn):
    """Chi risponde "sono foto del cielo" e poi cambia idea non lascia in archivio le ore di quei
    frame: l'oggetto, la notte e la sessione che il cielo aveva attaccato si staccano. Gli oggetti
    rimasti senza frame li spazza `identify` alla prima corsa, e una corsa parte perche' quei frame
    tornano fra quelli rimessi in coda."""
    radice = add_folder(conn, "D:/Astro")
    frame_id = _frame(conn, radice, "dark/a.fits")
    oggetto = conn.execute("INSERT INTO objects(created_at) VALUES('ora')").lastrowid
    conn.execute("UPDATE frames SET object_id = ? WHERE id = ?", (oggetto, frame_id))
    conn.execute(
        "INSERT INTO frame_wcs(frame_id, ra_deg, dec_deg, scale_arcsec_px, solved_at)"
        " VALUES(?, 1.0, 2.0, 1.0, 'ora')",
        (frame_id,),
    )
    solve_store.save_metrics(conn, frame_id, hfd_px=3.1, stars=800, now="ora")
    typeless.declare(conn, "D:/Astro/dark", typeless.CALIBRATION)
    assert typeless_answer.apply_answer(conn, _riga(conn, "D:/Astro/dark")) == [frame_id]
    riga = conn.execute("SELECT object_id, night_id, session_id FROM frames").fetchone()
    assert tuple(riga) == (None, None, None)
    # anche il cielo misurato: il solver cerca un cielo gia' trovato per lo stesso `OBJECT`
    # (`solve_store.sister_solution`), e un file di calibrazione non deve suggerire dove puntare
    assert conn.execute("SELECT COUNT(*) FROM frame_wcs").fetchone()[0] == 0
    # e le stelle contate quando lo si credeva un light: le ha scritte una passata che quel frame
    # non rifara' piu', e resterebbero li' a dire la qualita' di un dark
    assert conn.execute("SELECT COUNT(*) FROM frame_metrics").fetchone()[0] == 0


def test_changing_idea_back_to_sky_gives_the_frames_their_sky_again(conn):
    """ "Calibrazione" stacca il cielo trovato; tornare a "foto del cielo" deve ridarglielo, o quel
    frame resterebbe per sempre un light senza cielo, con l'oggetto preso dal nome. Si rimette in
    fila dal cielo, che rilegge la soluzione dalla sua cache."""
    radice = add_folder(conn, "D:/Astro")
    frame_id = _frame(conn, radice, "M51/a.fits", sky="done", normalized=True)
    senza = _frame(conn, radice, "M51/b.fits", normalized=True)  # il cielo non sapeva dire
    for risposta in (typeless.CALIBRATION, typeless.LIGHT):
        typeless.declare(conn, "D:/Astro/M51", risposta)
        typeless_answer.apply_answer(conn, _riga(conn, "D:/Astro/M51"))
    assert ready(conn, "solve") == [frame_id]
    # quello che il cielo non aveva risolto non si rimanda al solver: la rinuncia non e' in cache,
    # e rifarla costerebbe fino al tempo massimo per lo stesso esito
    assert ready(conn, "identify") == [senza]


def test_a_frame_that_kept_its_sky_is_not_sent_back_to_the_solver(conn):
    """ "Foto del cielo" rimanda al solver solo chi ha perso la soluzione: un frame risolto che la
    tiene ancora non si rilavora."""
    radice = add_folder(conn, "D:/Astro")
    _frame(conn, radice, "M51/a.fits", sky="done", normalized=True)
    _frame(conn, radice, "M51/b.fits")
    typeless.declare(conn, "D:/Astro/M51", typeless.LIGHT)
    typeless_answer.apply_answer(conn, _riga(conn, "D:/Astro/M51"))
    assert ready(conn, "solve") == []


def test_the_answer_is_found_from_the_path_before_a_file_is_read(conn):
    """La scansione deve sapere cosa fare **prima** di scrivere il frame: la chiave si compone dal
    percorso del file, con le stesse barre in avanti della cartella."""
    typeless.declare(conn, "D:/Astro/dark", typeless.CALIBRATION)
    assert typeless.answer_at(conn, "D:\\Astro", "dark/a.fits") == typeless.CALIBRATION
    assert typeless.answer_at(conn, "D:/Astro", "M51/a.fits") is None


def test_a_folder_answered_stays_on_the_page_with_its_frames(conn):
    """Un gruppo risposto resta in pagina coi suoi frame: e' cosi' che si cambia idea, e senza i
    frame non si saprebbe piu' di cosa si sta parlando."""
    radice = add_folder(conn, "D:/Astro")
    _frame(conn, radice, "dark/a.fits")
    typeless.declare(conn, "D:/Astro/dark", typeless.CALIBRATION)
    righe = _cartelle(conn)
    assert [(g["key"], g["frames"], g["answer"]) for g in righe] == [
        ("D:/Astro/dark", 1, typeless.CALIBRATION)
    ]


@pytest.mark.parametrize("stadio", ["identify", "group"])
def test_a_frame_that_goes_back_to_waiting_during_a_run_is_skipped(conn, monkeypatch, stadio):
    """Uno stadio sceglie i frame all'inizio. Se nel frattempo la cartella di uno di loro cambia --
    una cartella tolta mentre la corsa gira (`api/folders.py`) -- quel frame torna ad aspettare, e
    lo stadio non deve riattaccargli oggetto o notte: nessuno lo staccherebbe piu'."""
    modulo = importlib.import_module(f"astrolog.spine.{stadio}")
    radice = add_folder(conn, "D:/Astro")
    frame_id = _frame(conn, radice, "M51/a.fits", normalized=True)
    conn.execute(
        "UPDATE frames SET object_raw = 'M 51', date_obs = '2026-03-14T21:00:00' WHERE id = ?",
        (frame_id,),
    )
    conn.execute(
        "INSERT INTO sites(name, latitude, longitude, timezone, is_default, created_at)"
        " VALUES('Casa', 45.4, 11.9, 'Europe/Rome', 1, 'ora')"
    )
    typeless.declare(conn, "D:/Astro/M51", typeless.LIGHT)
    if stadio == "group":
        list(importlib.import_module("astrolog.spine.identify").identify_frames(conn))

    def e_intanto_la_cartella_cambia(c, stage, limit=None, frame_id=None):
        scelti = ready(c, stage, limit, frame_id)
        if frame_id is None:
            typeless.declare(c, "D:/Astro/M51", typeless.CALIBRATION)
        return scelti

    monkeypatch.setattr(modulo, "ready", e_intanto_la_cartella_cambia)
    list(getattr(modulo, f"{stadio}_frames")(conn))
    # cio' che scrive quello stadio: l'oggetto `identify`, la notte `group`
    colonna = "object_id" if stadio == "identify" else "night_id"
    riga = conn.execute(f"SELECT {colonna} FROM frames WHERE id = ?", (frame_id,))  # noqa: S608
    assert riga.fetchone()[0] is None
