"""Lo stadio `identify` che scrive: da una posa a un oggetto dell'archivio.

Gira sul **catalogo vero** e su un DB nato da `schema.sql`: e' cio' che l'utente incontrera'.
Qui si prova cosa finisce nel database -- quante righe, con che nome, con che fiducia -- non che
il generatore giri.
"""

from astrolog.db.connect import connect, create_database
from astrolog.spine import object_answer as risposta
from astrolog.spine.stages import invalidate
from group_bench import corri as raggruppa
from group_bench import luogo
from identify_bench import M31, M45, NOTTE, ORIONE, corri, nomi_di, occupante, oggetto_di, posa

# --- cosa finisce nel database ----------------------------------------------------------


def test_a_solved_frame_gets_its_object_with_the_catalog_names(archivio):
    frame = posa(archivio, obj="M 31", cielo=M31)
    ricevuta = corri(archivio)

    obj = oggetto_di(archivio, frame)
    assert obj["catalog_slug"] == "m-31"
    assert (obj["identity_method"], obj["identity_confidence"]) == ("coord_confirmed", "certain")
    assert obj["identified_at"]
    assert ricevuta["linked"] == 1 and ricevuta["new_objects"] == 1 and ricevuta["errors"] == 0
    # Il nome grezzo `M 31` E' la sigla che il catalogo ha appena dato all'oggetto: non e' un
    # nome conteso, e non deve contare come tale. Senza questa riga, `add_name` poteva tornare
    # a rifiutare i nomi gia' propri e nessun test se ne accorgeva.
    assert ricevuta["name_taken"] == 0
    # la sigla principale e' il nome dell'oggetto; il nome comune sta accanto
    nomi = nomi_di(archivio, obj["id"])
    assert nomi["M 31"] == ("catalog", 1)
    assert any(o == "catalog" and p == 0 for o, p in nomi.values())


def test_the_raw_header_name_is_always_kept(archivio):
    """Anche quando non ha deciso niente: e' cio' che l'utente ha scritto."""
    frame = posa(archivio, obj="Andromeda_finale", cielo=M31)
    corri(archivio)
    obj = oggetto_di(archivio, frame)
    assert obj["catalog_slug"] == "m-31"
    assert nomi_di(archivio, obj["id"])["Andromeda_finale"] == ("raw", 0)


def test_two_frames_of_the_same_galaxy_make_one_object(archivio):
    """E' il difetto contro cui esiste tutta questa casella: due righe e le ore si sparpagliano.
    Le due pose arrivano scritte in due modi diversi, come negli header veri."""
    a = posa(archivio, obj="M31", cielo=M31, hash_="a")
    b = posa(archivio, obj="Messier 31", cielo=M31, hash_="b")
    corri(archivio)
    assert oggetto_di(archivio, a)["id"] == oggetto_di(archivio, b)["id"]
    assert archivio.execute("SELECT COUNT(*) FROM objects").fetchone()[0] == 1


def test_an_unsolved_frame_hangs_on_the_name(archivio):
    """La situazione che prima non poteva accadere: nessun cielo, ma l'header dice una sigla."""
    frame = posa(archivio, obj="M 31", solve="failed")
    corri(archivio)
    obj = oggetto_di(archivio, frame)
    assert obj["catalog_slug"] == "m-31"
    assert (obj["identity_method"], obj["identity_confidence"]) == ("exact_name", "high")


def test_an_unsolved_frame_with_a_historic_name_says_so(archivio):
    frame = posa(archivio, obj="NGC 224", solve="failed")
    corri(archivio)
    assert oggetto_di(archivio, frame)["identity_method"] == "historic_name"


def test_an_unsolved_frame_with_a_free_name_becomes_an_object_of_its_own(archivio):
    """Le sette pose di M 101 del collaudo dicevano soltanto `Snapshot`: restano insieme."""
    a = posa(archivio, obj="Snapshot", solve="failed", hash_="a")
    b = posa(archivio, obj="Snapshot", solve="failed", hash_="b")
    ricevuta = corri(archivio)
    obj = oggetto_di(archivio, a)
    assert obj["catalog_slug"] is None
    assert (obj["identity_method"], obj["identity_confidence"]) == ("exact_name", "low")
    assert nomi_di(archivio, obj["id"])["Snapshot"] == ("raw", 1)
    assert oggetto_di(archivio, b)["id"] == obj["id"]
    assert ricevuta["new_objects"] == 1 and ricevuta["review"] == 2


def test_a_frame_with_no_name_and_no_sky_is_skipped_not_left_pending(archivio):
    """`pending` per sempre vorrebbe dire un residuo che non cala mai e un pulsante Avvia che
    parte a vuoto a ogni clic. Le pose si leggeranno da questo codice in Da confermare."""
    frame = posa(archivio, solve="failed")
    ricevuta = corri(archivio)
    riga = archivio.execute(
        "SELECT status, reason FROM frame_stages WHERE frame_id = ? AND stage = 'identify'",
        (frame,),
    ).fetchone()
    assert (riga["status"], riga["reason"]) == ("skipped", "no_name_no_sky")
    riga_frame = archivio.execute("SELECT object_id FROM frames WHERE id = ?", (frame,)).fetchone()
    assert riga_frame[0] is None
    assert ricevuta["waiting"] == 1 and ricevuta["linked"] == 0


def test_the_sky_disagreeing_with_the_name_hangs_the_name_and_asks(archivio):
    """Il contratto: il ramo Da confermare aggancia comunque, e nessuna ora si perde."""
    frame = posa(archivio, obj="M 31", cielo=M45)
    ricevuta = corri(archivio)
    obj = oggetto_di(archivio, frame)
    assert obj["catalog_slug"] == "m-31"  # il nome resta l'ipotesi
    assert obj["identity_confidence"] == "low"
    assert ricevuta["review"] == 1


def test_a_designation_past_the_shortlist_still_settles_it(archivio):
    """Il tetto dei candidati serve a **mostrarli**, non a decidere.

    Campo vero di Orione, 3x2 gradi: `NGC 1977` e' il **settimo** per punteggio, cioe' fuori dai
    sei che la pagina mostra. L'header lo nomina, quindi il cielo lo sta confermando e non si
    chiede niente. Passando alla decisione la lista tagliata, questa posa finiva in Da
    confermare -- ed e' il caso che la regola nuova doveva chiudere."""
    frame = posa(archivio, obj="NGC 1977", cielo=ORIONE, campo=(3.0, 2.0))
    ricevuta = corri(archivio)
    obj = oggetto_di(archivio, frame)
    assert obj["catalog_slug"] == "ngc-1977"
    assert (obj["identity_method"], obj["identity_confidence"]) == ("coord_confirmed", "certain")
    assert ricevuta["review"] == 0


# --- cosa NON si rovina -----------------------------------------------------------------


def test_a_doubt_from_one_frame_is_not_erased_by_the_next(archivio):
    """`low` e' assorbente: un oggetto su cui una posa ha lasciato un dubbio resta da confermare
    finche' l'utente non risponde."""
    posa(archivio, obj="M 31", cielo=M45, hash_="a")  # dubbia: il cielo dice un'altra cosa
    posa(archivio, obj="M 31", cielo=M31, hash_="b")  # sicura
    corri(archivio)
    obj = archivio.execute("SELECT * FROM objects WHERE catalog_slug = 'm-31'").fetchone()
    assert obj["identity_confidence"] == "low"


def test_one_unsolved_frame_does_not_downgrade_forty_confirmed_ones(archivio):
    """Il caso vero dell'Iris: 40 pose col cielo e una che il solver non ha risolto. Tenere
    sempre la fiducia piu' dubbiosa faceva scrivere `exact_name` / `high` a un oggetto che il
    cielo aveva confermato quaranta volte -- non cambiava cosa l'app chiede, ma lo raccontava
    sbagliato. Solo `low` e' una domanda, e solo `low` resta."""
    posa(archivio, obj="M 31", solve="failed", hash_="a")  # dal solo nome
    posa(archivio, obj="M 31", cielo=M31, hash_="b")  # confermata dal cielo
    corri(archivio)
    obj = archivio.execute("SELECT * FROM objects WHERE catalog_slug = 'm-31'").fetchone()
    assert (obj["identity_method"], obj["identity_confidence"]) == ("coord_confirmed", "certain")


def test_the_user_answer_is_never_overwritten(archivio):
    """La sola regola che questo stadio ha il potere di violare in silenzio."""
    archivio.execute(
        "INSERT INTO objects(id, catalog_slug, identity_method, identity_confidence, created_at)"
        " VALUES(9, 'm-31', 'user', 'user', 'now')"
    )
    # con una posa gia' attaccata: un oggetto a zero pose e' un residuo e la spazzata lo toglie
    sua = archivio.execute(
        "INSERT INTO frames(frame_hash, image_type, header_json, created_at)"
        " VALUES('gia-sua', 'light', '[]', 'now')"
    ).lastrowid
    archivio.execute("UPDATE frames SET object_id = 9 WHERE id = ?", (sua,))
    frame = posa(archivio, obj="M 31", cielo=M45)  # una posa dubbia, che vorrebbe abbassare
    corri(archivio)
    obj = oggetto_di(archivio, frame)
    assert (obj["id"], obj["identity_method"], obj["identity_confidence"]) == (9, "user", "user")


def test_a_name_already_taken_is_not_stolen_and_is_counted(archivio):
    """Un nome, un oggetto. Due oggetti diversi con lo stesso nome grezzo nell'header capitano,
    e l'indice unico del database li fermerebbe con un errore: qui non si arriva a chiederlo.

    E non cade in silenzio: e' l'unica eccezione a "il nome grezzo si tiene sempre", quindi si
    conta -- se un giorno quel contatore diventasse grande, vorrebbe dire che due oggetti si
    contendono un nome molto piu' spesso di quanto si crede."""
    posa(archivio, obj="Snapshot", cielo=M31, hash_="a")  # il cielo dice M 31
    posa(archivio, obj="Snapshot", cielo=M45, hash_="b")  # lo stesso nome, un altro cielo
    ricevuta = corri(archivio)
    assert ricevuta["errors"] == 0 and ricevuta["new_objects"] == 2
    assert ricevuta["name_taken"] == 1  # il secondo oggetto non si prende `Snapshot`
    padroni = archivio.execute(
        "SELECT COUNT(DISTINCT object_id) FROM object_names WHERE name = 'Snapshot'"
    ).fetchone()[0]
    assert padroni == 1


def test_an_object_is_never_born_without_a_primary_name(archivio):
    """Il caso vero: il catalogo non si era caricato al primo giro, un oggetto fuori catalogo si
    e' preso la sigla `M 31`, e ora il catalogo c'e'. La voce vera non puo' avere quel nome --
    e senza questa regola nasceva **senza nome primario**, cioe' un oggetto che l'Archivio non
    sa come chiamare."""
    occupante(archivio, 9, ["M 31"])
    frame = posa(archivio, obj="M 31", cielo=M31)
    corri(archivio)
    obj = oggetto_di(archivio, frame)
    assert obj["catalog_slug"] == "m-31" and obj["id"] != 9
    primari = [n for n, (_, p) in nomi_di(archivio, obj["id"]).items() if p]
    assert primari == ["Andromeda Galaxy"]  # il nome comune, perche' la sigla era gia' presa


def test_an_object_whose_names_are_all_taken_still_knows_what_it_is(archivio):
    """Il caso limite: sia la sigla sia il nome comune sono gia' di altri. Serve un oggetto nato
    senza catalogo che si e' preso `NGC 7318`, e la voce `HCG 92` che porta lo stesso nome
    comune (nel catalogo 110 voci si spartiscono 42 nomi comuni). L'oggetto nasce senza nomi
    propri, e regge perche' ha `catalog_slug`: il catalogo sa come si chiama. Cio' che NON deve
    succedere e' che si perda la posa, o che il conteggio dei nomi rifiutati menta."""
    occupante(archivio, 9, ["NGC 7318", "Stephan's Quintet"])
    frame = posa(archivio, obj="NGC 7318", solve="failed")
    ricevuta = corri(archivio)

    obj = oggetto_di(archivio, frame)
    assert obj["catalog_slug"] == "ngc-7318" and obj["id"] != 9
    assert nomi_di(archivio, obj["id"]) == {}
    assert ricevuta["errors"] == 0 and ricevuta["linked"] == 1
    assert ricevuta["name_taken"] == 3  # i due di catalogo piu' il grezzo


def test_two_objects_outside_the_catalog_can_coexist(archivio):
    """L'indice unico su `catalog_slug` non li fa litigare: in SQLite i NULL non contendono. Se
    fosse falso, TUTTE le pose senza cielo dopo la prima finirebbero `failed`."""
    posa(archivio, obj="Snapshot", solve="failed", hash_="a")
    posa(archivio, obj="Test", solve="failed", hash_="b")
    ricevuta = corri(archivio)
    assert ricevuta["errors"] == 0 and ricevuta["new_objects"] == 2


def test_a_comet_does_not_take_the_object_behind_it(archivio):
    """Sul database vero: una cometa col suo cielo misurato non diventa la galassia che le
    stava dietro."""
    frame = posa(archivio, obj="12P/Pons-Brooks", cielo=M31)
    corri(archivio)
    obj = oggetto_di(archivio, frame)
    assert obj["catalog_slug"] is None
    assert nomi_di(archivio, obj["id"])["12P/Pons-Brooks"] == ("raw", 1)


def test_running_the_stage_twice_changes_nothing(archivio):
    """Rifare uno stadio riscrive, non duplica."""
    posa(archivio, obj="M 31", cielo=M31)
    corri(archivio)
    conta = lambda: (  # noqa: E731
        archivio.execute("SELECT COUNT(*) FROM objects").fetchone()[0],
        archivio.execute("SELECT COUNT(*) FROM object_names").fetchone()[0],
    )
    prima = conta()
    archivio.execute("UPDATE frame_stages SET status = 'pending' WHERE stage = 'identify'")
    corri(archivio)
    assert conta() == prima


def test_the_sweep_runs_on_an_already_grouped_archive(archivio):
    """La sequenza dell'Applica su un archivio gia' raggruppato, che schiantava l'app.

    Premere Applica rimette in coda `identify`, che stacca le pose e **poi** spazza gli oggetti
    rimasti a zero pose: in quel momento l'oggetto e' vuoto ma la **sessione** del giro
    precedente lo punta ancora. Senza il `CASCADE` su `sessions.object_id` era `FOREIGN KEY
    constraint failed` -- sull'archivio vero, 11.005 pose, 0,16 s dopo l'inizio di `identify` e
    3,4 s dopo l'Applica, e la corsa moriva li'.

    La sessione se ne va con l'oggetto e non porta via niente: `group`, che nella catena viene
    subito dopo, la rifa'. Qui si guarda la fine della catena, che e' cio' che l'utente vede."""
    frame = posa(archivio, obj="M 31", cielo=M31, quando=NOTTE)
    luogo(archivio)
    corri(archivio)
    raggruppa(archivio)
    assert archivio.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1

    invalidate(archivio, [frame], "identify")
    ricevuta = corri(archivio)
    assert ricevuta["errors"] == 0
    raggruppa(archivio)

    assert oggetto_di(archivio, frame)["catalog_slug"] == "m-31"
    # la posa non ha perso la sua sessione: `group` gliel'ha rifatta nella stessa catena
    assert archivio.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1
    assert archivio.execute("SELECT session_id FROM frames WHERE id = ?", (frame,)).fetchone()[0]


def test_the_sweep_leaves_the_sessions_of_the_objects_it_keeps(archivio):
    """L'altra meta' del `CASCADE`: cio' che **non** deve prendere.

    La guardia qui sopra prova che la corsa non muore; questa prova che una cancellazione
    allargata non porta via una posa a nessuno. Due oggetti nella stessa notte, e solo il primo
    si svuota (l'utente ha risposto su quello): la sessione dell'altro, e la `session_id` delle
    sue pose, devono restare quelle di prima. Con una posa sola in archivio -- lo scenario delle
    altre due guardie -- un `DELETE` troppo largo non avrebbe niente da portare via, e passerebbe
    lo stesso."""
    mio = posa(archivio, obj="M 31", cielo=M31, quando=NOTTE, hash_="a")
    altrui = posa(archivio, obj="M 45", cielo=M45, quando=NOTTE, hash_="b")
    luogo(archivio)
    corri(archivio)
    raggruppa(archivio)
    sessione_altrui = archivio.execute(
        "SELECT session_id FROM frames WHERE id = ?", (altrui,)
    ).fetchone()[0]
    assert archivio.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 2

    risposta.correct_object(archivio, "m-31", slug="m-83")
    invalidate(archivio, [mio], "identify")
    ricevuta = corri(archivio)

    assert ricevuta["swept"] == 1  # se ne va m-31, che e' rimasto a zero pose
    assert (
        archivio.execute("SELECT session_id FROM frames WHERE id = ?", (altrui,)).fetchone()[0]
        == sessione_altrui
    )
    assert archivio.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1
    assert archivio.execute("SELECT COUNT(*) FROM nights").fetchone()[0] == 1


def test_a_frame_still_queued_at_the_solver_is_left_alone(archivio):
    """ASTAP non c'e' ancora: le pose aspettano il loro cielo, non un nome dato in fretta."""
    posa(archivio, obj="M 31", solve="pending")
    ricevuta = corri(archivio)
    assert ricevuta["total"] == 0
    assert archivio.execute("SELECT COUNT(*) FROM objects").fetchone()[0] == 0


def test_the_stage_works_without_a_catalog(tmp_path):
    """A mani vuote: nessun catalogo caricato. L'app cataloga e conta le ore lo stesso, e il
    nome dell'header diventa l'oggetto."""
    path = tmp_path / "vuoto.db"
    create_database(path)
    conn = connect(path)
    try:
        frame = posa(conn, obj="M 31", cielo=M31)
        ricevuta = corri(conn)
        obj = oggetto_di(conn, frame)
        assert obj["catalog_slug"] is None and obj["identity_confidence"] == "low"
        assert nomi_di(conn, obj["id"])["M 31"] == ("raw", 1)
        assert ricevuta["errors"] == 0
    finally:
        conn.close()
