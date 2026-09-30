"""La parola dell'utente sullo stadio `identify`: le correzioni e le regole imparate.

Le due strade non si sovrappongono mai -- la regola vale dove il cielo non c'e', la correzione
sposta cio' che il cielo ha deciso -- ed e' il punto che e' costato tre giri di revisione: qui
c'e' un test per ognuna delle due versioni sbagliate. Cosa finisce nel database in generale sta
in `test_identify_stage.py`.
"""

import pytest

from astrolog.spine import declarations as decl
from astrolog.spine import object_answer as risposta
from astrolog.spine.stages import invalidate
from group_bench import corri as raggruppa
from group_bench import luogo
from identify_bench import M31, M45, M83, NOTTE, corri, nomi_di, oggetto_di, posa

# --- la parola dell'utente ---------------------------------------------------------------


def test_the_user_correction_moves_the_frames(archivio):
    """La casella che regge la sezione Oggetti: l'utente dice che cio' che il cielo chiama
    `m-31` per lui e' M 45, e le pose ci devono andare.

    Il lucchetto `user` non basta: protegge l'OGGETTO, non la posa. Senza questa correzione
    `identify` rifarebbe la sua strada dal cielo e riaggancerebbe tutto a M 31, e la risposta
    dell'utente sarebbe muta al primo ricalcolo."""
    a = posa(archivio, obj="M 31", cielo=M31, hash_="a")
    b = posa(archivio, obj="M 31", cielo=M31, hash_="b")
    risposta.correct_object(archivio, "m-31", slug="m-45")
    corri(archivio)

    for frame in (a, b):
        obj = oggetto_di(archivio, frame)
        assert obj["catalog_slug"] == "m-45"
        # cio' che nasce da una dichiarazione E' dichiarato, e da li' in poi e' lucchettato
        assert (obj["identity_method"], obj["identity_confidence"]) == ("user", "user")
    assert archivio.execute("SELECT COUNT(*) FROM objects").fetchone()[0] == 1


def test_a_correction_can_point_to_a_name_outside_the_catalog(archivio):
    """L'oggetto giusto puo' non stare in catalogo: una cometa, un campo stellare, una cosa che
    l'utente chiama a modo suo. La correzione porta un nome invece di uno slug."""
    frame = posa(archivio, obj="M 31", cielo=M31)
    risposta.correct_object(archivio, "m-31", name="Il mio campo")
    corri(archivio)

    obj = oggetto_di(archivio, frame)
    assert obj["catalog_slug"] is None
    assert nomi_di(archivio, obj["id"])["Il mio campo"] == ("user", 1)


def test_a_correction_survives_a_second_run(archivio):
    """Una dichiarazione non si consuma: vale a ogni ricalcolo, per sempre."""
    frame = posa(archivio, obj="M 31", cielo=M31)
    risposta.correct_object(archivio, "m-31", slug="m-45")
    corri(archivio)
    archivio.execute("UPDATE frame_stages SET status = 'pending' WHERE stage = 'identify'")
    corri(archivio)
    assert oggetto_di(archivio, frame)["catalog_slug"] == "m-45"


def test_a_correction_on_a_free_name_moves_those_frames_too(archivio):
    """Non solo gli oggetti di catalogo: le sette pose che dicono `Snapshot` e che il solver non
    ha risolto sono il caso per cui la sezione Oggetti esiste."""
    frame = posa(archivio, obj="Snapshot", solve="failed")
    risposta.correct_object(archivio, "Snapshot", slug="m-101")
    corri(archivio)
    assert oggetto_di(archivio, frame)["catalog_slug"] == "m-101"


def test_a_ring_of_corrections_stops_where_it_is(archivio):
    """`m-31` -> `m-45` e `m-45` -> `m-31`: la catena si segue, ma un anello si ferma dove si
    chiude. Applicare il passo che riporta indietro rimetterebbe la posa esattamente da dove era
    partita, quindi si guarda PRIMA di applicarlo: si esce su `m-45`, che e' l'ultima parola
    dell'utente che aggiunge qualcosa."""
    frame = posa(archivio, obj="M 31", cielo=M31)
    risposta.correct_object(archivio, "m-31", slug="m-45")
    risposta.correct_object(archivio, "m-45", slug="m-31")
    corri(archivio)
    assert oggetto_di(archivio, frame)["catalog_slug"] == "m-45"


def test_a_correction_without_its_prefix_is_ignored_not_trimmed(archivio):
    """Il prefisso del bersaglio si **verifica**, non si presume.

    Una riga senza prefisso l'ha scritta qualcuno che non e' passato da `correct_object`;
    tagliarla alla cieca darebbe un nome storpiato, e l'app sposterebbe delle pose su un oggetto
    inventato invece di lasciarle dove il cielo le ha messe. Si ignora, e si scrive nel log."""
    archivio.execute(
        "INSERT INTO declarations(entity_type, entity_key, field, value, created_at)"
        " VALUES('object', 'm-31', 'correction', 'm-45', 'now')"
    )
    assert risposta.correction_of(archivio, "m-31") is None
    frame = posa(archivio, obj="M 31", cielo=M31)
    corri(archivio)
    assert oggetto_di(archivio, frame)["catalog_slug"] == "m-31"  # non si e' mosso


def test_a_correction_to_a_slug_the_catalog_does_not_know_is_ignored(archivio):
    """Una dichiarazione non puo' far sparire delle pose: se il bersaglio non esiste, si resta
    su cio' che il cielo dice, e la posa e' agganciata comunque."""
    frame = posa(archivio, obj="M 31", cielo=M31)
    risposta.correct_object(archivio, "m-31", slug="non-esiste")
    ricevuta = corri(archivio)
    assert oggetto_di(archivio, frame)["catalog_slug"] == "m-31"
    assert ricevuta["errors"] == 0


def test_an_object_left_without_frames_disappears(archivio):
    """Rispondere sposta le pose, e cio' che resta indietro non e' piu' un oggetto.

    Non e' un dettaglio di pulizia: senza, dopo aver risposto l'utente rilegge la pagina e trova
    ancora "NGC 7023 -- 0 pose" (misurato sulle 41 pose vere dell'Iris), e quella riga **tiene in
    ostaggio i suoi nomi** -- e' lei che si prende `NGC 7023` e costringe l'oggetto vero a
    nascere senza nomi propri. Un oggetto e' cio' che e' stato fotografato: senza pose non e'
    stato fotografato."""
    frame = posa(archivio, obj="M 31", cielo=M31)
    corri(archivio)

    risposta.correct_object(archivio, "m-31", slug="m-45")
    archivio.execute("UPDATE frame_stages SET status = 'pending' WHERE stage = 'identify'")
    corri(archivio)

    # Si guarda lo SLUG e non l'id: la spazzata cancella l'oggetto e lo rifa' con un numero
    # nuovo, quindi un test che cercasse l'id vecchio non troverebbe niente.
    assert (
        archivio.execute("SELECT COUNT(*) FROM objects WHERE catalog_slug = 'm-31'").fetchone()[0]
        == 0
    )
    assert archivio.execute("SELECT COUNT(*) FROM objects").fetchone()[0] == 1
    assert archivio.execute("SELECT COUNT(*) FROM object_names").fetchone()[0] > 0
    # e il nome torna libero: l'oggetto vero se lo prende
    nuovo_obj = oggetto_di(archivio, frame)
    assert nuovo_obj["catalog_slug"] == "m-45"
    assert "M 45" in nomi_di(archivio, nuovo_obj["id"])


def test_an_object_with_a_session_disappears_too_and_frees_its_names(archivio):
    """Lo stesso, su un archivio **gia' raggruppato**: e' il caso vero, perche' chi risponde
    dalla pagina ha gia' le sue notti in casa.

    Misurato: risparmiare l'oggetto finche' una sessione lo punta -- la strada che evita lo
    schianto senza toccare lo schema -- lo lascia in piedi a zero pose con `M 31` in ostaggio, e
    nessuno lo ripassa piu' (dopo l'Applica le pose sono `done`). Cioe' rimette esattamente il
    difetto che questa spazzata esisteva per togliere. La sessione se ne va con l'oggetto, e
    `group` la rifa' subito dopo."""
    frame = posa(archivio, obj="M 31", cielo=M31, quando=NOTTE)
    luogo(archivio)
    corri(archivio)
    raggruppa(archivio)

    risposta.correct_object(archivio, "m-31", slug="m-45")
    invalidate(archivio, [frame], "identify")
    ricevuta = corri(archivio)
    raggruppa(archivio)

    assert ricevuta["swept"] == 1 and ricevuta["name_taken"] == 0
    assert (
        archivio.execute("SELECT COUNT(*) FROM objects WHERE catalog_slug = 'm-31'").fetchone()[0]
        == 0
    )
    # il nome grezzo non e' rimasto in ostaggio: l'oggetto nuovo se l'e' preso
    nuovo = oggetto_di(archivio, frame)
    assert nuovo["catalog_slug"] == "m-45"
    assert "M 31" in nomi_di(archivio, nuovo["id"])
    # e la posa ha di nuovo la sua sessione: quella vecchia e' andata via, non la posa
    assert archivio.execute("SELECT session_id FROM frames WHERE id = ?", (frame,)).fetchone()[0]
    assert archivio.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1


def test_the_header_name_survives_the_sweep_in_one_single_run(archivio):
    """**Una corsa sola**, che e' tutto cio' che l'app fa dopo una risposta.

    Prima la pulizia girava a fine corsa: la grafia dell'header restava dell'oggetto vecchio
    mentre si assegnavano i nomi, poi il vecchio spariva **portandosela via col CASCADE**, e
    `NGC 7023` -- cio' che l'utente aveva scritto -- non c'era piu' in archivio. Dichiaravo che
    "la corsa dopo" l'avrebbe ripresa: in produzione quella corsa **non esiste**, perche' dopo
    l'Applica la posa e' `done` e nessuno la rimette in coda. Il test che lo copriva rimetteva
    `pending` a mano, cioe' faceva una cosa che l'app non fa mai."""
    frame = posa(archivio, obj="M 31", cielo=M31)
    corri(archivio)
    risposta.correct_object(archivio, "m-31", slug="m-45")

    archivio.execute("UPDATE frame_stages SET status = 'pending' WHERE stage = 'identify'")
    r = corri(archivio)

    obj_id = oggetto_di(archivio, frame)["id"]
    assert nomi_di(archivio, obj_id)["M 31"] == ("raw", 0), "il nome dell'utente e' sparito"
    assert r["swept"] == 1 and r["name_taken"] == 0


def test_even_an_object_the_user_answered_goes_when_it_has_no_frames(archivio):
    """Anche gli oggetti `user`, e l'eccezione contraria era un errore mio.

    L'avevo scritta pensando "l'utente lo ha creato, le sue pose arrivano dopo". Ma con questo
    disegno **l'utente non crea oggetti**: crea correzioni, e gli oggetti li fa `identify` quando
    una posa ci va. Un oggetto `user` a zero pose e' quindi sempre un residuo -- e si vede
    correggendo due volte: rispondi LDN 1174, poi ti ricorreggi, e LDN 1174 restava li' a zero
    pose **tenendosi la sigla `NGC 7023`**, cosi' che l'oggetto vero ripiegava su "Iris Nebula".

    Non si perde niente: l'oggetto e' un derivato, la parola dell'utente vive in `declarations` e
    quella non si tocca."""
    frame = posa(archivio, obj="M 31", cielo=M31)
    corri(archivio)
    risposta.correct_object(archivio, "m-31", slug="m-45")
    archivio.execute("UPDATE frame_stages SET status = 'pending' WHERE stage = 'identify'")
    corri(archivio)
    assert oggetto_di(archivio, frame)["catalog_slug"] == "m-45"

    risposta.correct_object(archivio, "m-45", slug="m-101")  # "no, mi ero sbagliato"
    archivio.execute("UPDATE frame_stages SET status = 'pending' WHERE stage = 'identify'")
    corri(archivio)

    obj = oggetto_di(archivio, frame)
    assert obj["catalog_slug"] == "m-101"
    assert archivio.execute("SELECT COUNT(*) FROM objects").fetchone()[0] == 1
    # e il nome che il catalogo gli da' non e' rimasto in ostaggio del residuo
    assert "M 101" in nomi_di(archivio, obj["id"])
    # la parola dell'utente e' al sicuro dove vive davvero
    assert risposta.correction_of(archivio, "m-45") == ("catalog", "m-101")


def test_a_second_answer_corrects_the_first(archivio):
    """Correggere un clic sbagliato e' la seconda cosa piu' probabile su questa pagina.

    Prima la catena si fermava al primo passo e la seconda risposta veniva ignorata **in
    silenzio**: l'API rispondeva 200 e non succedeva niente."""
    frame = posa(archivio, obj="M 31", cielo=M31)
    corri(archivio)
    risposta.correct_object(archivio, "m-31", slug="m-45")
    risposta.correct_object(archivio, "m-45", slug="m-101")  # "no, mi ero sbagliato"

    archivio.execute("UPDATE frame_stages SET status = 'pending' WHERE stage = 'identify'")
    corri(archivio)
    assert oggetto_di(archivio, frame)["catalog_slug"] == "m-101"


def test_the_user_lock_lands_on_an_object_that_already_existed(archivio):
    """Il lucchetto non puo' dipendere dal fatto che il bersaglio sia nuovo.

    Prima `_restate` passava dalla scala delle fiducie, che non conosce `user`: rispondendo su
    un oggetto **gia' in archivio** il lucchetto non si scriveva, l'oggetto restava `low`, e la
    pagina lo rimetteva in cima coi candidati -- all'utente che aveva appena risposto."""
    a = posa(archivio, obj="M 45", cielo=M45, hash_="a")  # crea m-45, sicuro
    b = posa(archivio, obj="M 31", cielo=M31, hash_="b")
    corri(archivio)
    risposta.correct_object(archivio, "m-31", slug="m-45")

    archivio.execute("UPDATE frame_stages SET status = 'pending' WHERE stage = 'identify'")
    corri(archivio)
    obj = oggetto_di(archivio, b)
    assert obj["catalog_slug"] == "m-45" and obj["id"] == oggetto_di(archivio, a)["id"]
    assert (obj["identity_method"], obj["identity_confidence"]) == ("user", "user")


# --- la regola imparata: "quando l'header dice X, e' Y" ---------------------------------


def test_a_learned_rule_names_a_future_frame_without_asking_again(archivio):
    """La promessa della pagina: la risposta vale anche per le pose future con quello stesso
    nome, e su una posa senza cielo il nome e' l'unica fonte che c'e'."""
    decl.learn(archivio, "object", "Snapshot", "m-101")
    frame = posa(archivio, obj="Snapshot", solve="failed")
    ricevuta = corri(archivio)
    obj = oggetto_di(archivio, frame)
    assert obj["catalog_slug"] == "m-101"
    # `user` perche' una regola nasce da una risposta: il cielo non la contraddice (non c'e'),
    # quindi vale come parola dell'utente e nessuna posa successiva puo' abbassarla
    assert (obj["identity_method"], obj["identity_confidence"]) == ("user", "user")
    assert ricevuta["review"] == 0  # non si richiede: l'utente ha gia' risposto per la grafia


def test_a_learned_rule_does_not_touch_a_frame_that_has_a_sky(archivio):
    """**Il difetto peggiore di questa fetta, e va tenuto rosso.**

    Una regola e' una stringa di testo; il cielo e' una misura, ed e' migliore. Dove il cielo
    c'e', la regola non si guarda proprio: questa posa ha fotografato M 83 e su M 83 resta, con
    la fiducia piena, anche se una regola dice che `Snapshot` sarebbe M 31.

    Le due versioni sbagliate che ci sono volute per arrivarci: applicata alla decisione, la
    regola batteva il cielo e **lucchettava** -- la posa finiva su M 31 con `user`/`user` e
    nessuna domanda, cioe' il danno che "la regola solo se la grafia non e' ambigua" doveva
    impedire, aggirato dal lato lettura. Spostata sul nome, metteva il nome corretto in
    conflitto col cielo originale e l'app **richiedeva su tutte le pose a cui l'utente aveva
    appena risposto** (41, misurate sull'Iris)."""
    decl.learn(archivio, "object", "Snapshot", "m-31")
    frame = posa(archivio, obj="Snapshot", cielo=M83)  # il cielo dice M 83, la regola dice M 31
    ricevuta = corri(archivio)

    obj = oggetto_di(archivio, frame)
    assert obj["catalog_slug"] == "m-83", "una stringa di testo ha battuto una misura"
    assert (obj["identity_method"], obj["identity_confidence"]) == ("coord_confirmed", "certain")
    assert ricevuta["review"] == 0


def test_a_correction_moves_the_frames_the_sky_named(archivio):
    """Dove il cielo c'e', a portare la parola dell'utente e' la **correzione**, non la regola:
    e' agganciata a cio' che l'app ha dedotto guardando il cielo, quindi non entra mai in
    conflitto con lui. E' il caso vero dell'Iris: rispondi, e le pose ci vanno senza che l'app
    richieda niente."""
    a = posa(archivio, obj="M 83", cielo=M83, hash_="a")
    b = posa(archivio, obj="M 83", cielo=M83, hash_="b")
    corri(archivio)
    risposta.correct_object(archivio, "m-83", slug="m-101")

    archivio.execute("UPDATE frame_stages SET status = 'pending' WHERE stage = 'identify'")
    ricevuta = corri(archivio)
    for frame in (a, b):
        obj = oggetto_di(archivio, frame)
        assert obj["catalog_slug"] == "m-101"
        assert (obj["identity_method"], obj["identity_confidence"]) == ("user", "user")
    assert ricevuta["review"] == 0, "l'app richiede su pose a cui l'utente ha gia' risposto"


def test_a_correction_closes_the_question_on_a_doubtful_object(archivio):
    """**Il caso per cui la sezione Oggetti esiste**: l'header dice `M 45`, il cielo dice un'altra
    cosa, e l'app chiede. L'utente clicca il candidato, e la domanda si chiude.

    Prima la correzione spostava le pose ma lasciava l'oggetto `low`: la pagina lo rimetteva in
    cima coi suoi candidati e l'app poteva richiedere all'infinito -- ogni clic scriveva una
    risposta e nessuno chiudeva la domanda, proprio sui due rami in cui chiede davvero. La
    correzione e' agganciata alla chiave che la pagina mostrava, quindi e' la risposta a
    QUELLA domanda."""
    frame = posa(archivio, obj="M 45", cielo=M31)
    ricevuta = corri(archivio)
    assert ricevuta["review"] == 1  # il ramo `sky_disagrees`: l'app chiede, ed e' giusto
    assert oggetto_di(archivio, frame)["identity_confidence"] == "low"

    risposta.correct_object(archivio, "m-45", slug="m-31")  # l'utente clicca il candidato
    archivio.execute("UPDATE frame_stages SET status = 'pending' WHERE stage = 'identify'")
    ricevuta = corri(archivio)

    obj = oggetto_di(archivio, frame)
    assert obj["catalog_slug"] == "m-31"
    assert (obj["identity_method"], obj["identity_confidence"]) == ("user", "user")
    assert ricevuta["review"] == 0, "l'app richiede cio' a cui l'utente ha appena risposto"


def test_a_doubt_on_a_locked_object_is_not_counted(archivio):
    """La ricevuta conta le richieste che la pagina fara' davvero.

    Su un oggetto lucchettato dall'utente il dubbio di una posa non arriva a schermo -- la
    pagina guarda `objects.identity_confidence`, e li' c'e' `user` -- quindi contarlo darebbe
    "1 da rivedere" con lo schermo che ne mostra zero, e nella spina i conti della ricevuta
    sono l'unica diagnostica che c'e'. Che quella posa non abbia oggi un modo di farsi notare
    e' un'altra cosa, ed e' in coda."""
    posa(archivio, obj="M 31", cielo=M31, hash_="a")
    corri(archivio)
    risposta.correct_object(archivio, "m-31", slug="m-45")
    archivio.execute("UPDATE frame_stages SET status = 'pending' WHERE stage = 'identify'")
    corri(archivio)  # ora m-45 e' lucchettato

    frame = posa(archivio, obj="M 45", cielo=M31, hash_="b")  # header m-45, cielo un'altra cosa
    ricevuta = corri(archivio)
    assert oggetto_di(archivio, frame)["identity_confidence"] == "user"
    assert ricevuta["review"] == 0, "una domanda contata che la pagina non fara' mai"


def test_a_rule_keeps_the_header_spelling_among_the_names(archivio):
    """La regola cambia il nome che DECIDE, non cio' che l'utente ha scritto.

    Il vincolo in testa al file vale su ogni posa: la grafia dell'header entra in `object_names`,
    e cade solo se e' gia' di un altro oggetto -- e allora si scrive nel log. Sul ramo della
    regola cadeva in silenzio, e l'Archivio mostrava un oggetto che non ricordava piu'
    l'etichetta con cui l'utente chiamava quelle pose."""
    decl.learn(archivio, "object", "Iris finale", "m-31")
    frame = posa(archivio, obj="Iris finale", solve="failed")
    corri(archivio)
    obj = oggetto_di(archivio, frame)
    assert obj["catalog_slug"] == "m-31"
    assert nomi_di(archivio, obj["id"])["Iris finale"] == ("raw", 0)


def test_a_learned_rule_is_read_however_the_header_spells_it(archivio):
    """La regola si scrive e si cerca sulla stessa chiave: **pulita** dalle parole di tavolozza
    e normalizzata. Erano due chiavi diverse -- si scriveva `snapshot lrgb` e si cercava
    `snapshot` -- quindi su una grafia come `M31 LRGB`, che e' il caso per cui
    `vocab/object_label.py` esiste, la regola non poteva scattare mai."""
    decl.learn(archivio, "object", "  Snapshot LRGB ", "m-101")
    frame = posa(archivio, obj="SNAPSHOT rgb", solve="failed")
    corri(archivio)
    assert oggetto_di(archivio, frame)["catalog_slug"] == "m-101"


def test_a_correction_still_applies_on_top_of_a_rule(archivio):
    """La regola da' il nome, la correzione sposta l'oggetto: si sommano, non si escludono.
    Prima la regola faceva `return` e la catena non veniva nemmeno consultata."""
    decl.learn(archivio, "object", "Snapshot", "m-45")
    risposta.correct_object(archivio, "m-45", slug="m-101")
    frame = posa(archivio, obj="Snapshot", solve="failed")
    corri(archivio)
    assert oggetto_di(archivio, frame)["catalog_slug"] == "m-101"


def test_a_rule_towards_a_free_name_works_too(archivio):
    """Il bersaglio di una regola puo' non stare in catalogo: lo schema dice il nome pulito
    **o** lo slug, e chi fotografa una cometa ha diritto alla sua regola."""
    decl.learn(archivio, "object", "Snapshot", "La mia cometa")
    frame = posa(archivio, obj="Snapshot", solve="failed")
    corri(archivio)
    obj = oggetto_di(archivio, frame)
    assert obj["catalog_slug"] is None
    assert "La mia cometa" in nomi_di(archivio, obj["id"])


def test_two_spellings_that_clean_to_the_same_thing_count_as_one(archivio):
    """L'ambiguita' di una grafia si valuta **ripulita**, come la si cerca.

    `Snapshot LRGB` e `Snapshot RGB` sono due stringhe diverse in tabella ma la stessa grafia:
    valutandole grezze ognuna sembra puntare a un oggetto solo, e si scriverebbe una regola su
    un segnaposto che sta su due cieli -- esattamente cio' che la regola sull'ambiguita' esiste
    per impedire."""
    a = posa(archivio, obj="Snapshot LRGB", cielo=M31, hash_="a")
    b = posa(archivio, obj="Snapshot RGB", cielo=M83, hash_="b")
    corri(archivio)
    assert oggetto_di(archivio, a)["id"] != oggetto_di(archivio, b)["id"]

    risposta.declare_object(archivio, "m-31", slug="m-45")
    regole = [
        r[0]
        for r in archivio.execute("SELECT header_value FROM header_aliases WHERE kind='object'")
    ]
    assert regole == [], f"scritta una regola su un segnaposto: {regole}"


@pytest.mark.parametrize(
    "chiave, slug, nome",
    [
        ("", "m-45", None),
        (None, "m-45", None),
        ("m-31", "m-45", "Il mio campo"),
        ("m-31", None, None),
    ],
    ids=["chiave vuota", "chiave assente", "due bersagli", "nessun bersaglio"],
)
def test_a_correction_wants_one_key_and_one_target(chiave, slug, nome):
    """La correzione vuole **una chiave e un bersaglio solo**, e si rifiuta prima di scrivere.

    Senza chiave non si sa cosa si sta correggendo e la riga finirebbe agganciata al nulla; con
    slug e nome insieme -- o con nessuno dei due -- a scegliere quale vince saremmo noi, e nessuna
    delle due scelte e' quella dell'utente.

    Il rifiuto arriva **prima** di toccare il database, ed e' per questo che qui non serve nessun
    archivio: passare `None` al posto della connessione e' la prova che non ci si arriva."""
    with pytest.raises(ValueError):
        risposta.correct_object(None, chiave, slug=slug, name=nome)


def test_the_instant_the_apply_gives_is_the_one_written(archivio):
    """Un Applica, un istante: l'ora che il chiamante passa e' quella che finisce scritta, nella
    correzione come nella conferma.

    Senza, ogni riga prenderebbe l'ora della propria chiamata: le scritture di una stessa risposta
    smetterebbero di condividere un istante, e sarebbe una perdita che nessuna pagina mostra e di
    cui nessuno si accorgerebbe."""
    posa(archivio, obj="M 31", cielo=M31)
    corri(archivio)
    quando = "2024-05-17T22:00:00Z"
    risposta.declare_object(archivio, "m-31", slug="m-45", now=quando)
    righe = archivio.execute(
        "SELECT entity_key, field, created_at FROM declarations WHERE entity_type = 'object'"
    ).fetchall()
    assert {r["field"] for r in righe} == {risposta.CORRECTION, decl.CONFIRMED}
    assert {r["created_at"] for r in righe} == {quando}
