"""La sezione Oggetti di Da confermare: cosa l'app ha capito, e cosa succede quando rispondo.

La pagina e l'Applica per l'attrezzatura stanno in `test_review.py`; qui c'e' il **banco misto**,
che ci vuole: sull'archivio sintetico ogni oggetto e' dubbio e senza cielo, quindi tre guardie su
questa sezione erano vere per caso -- provato rompendo il codice e vedendo i test restare verdi.
"""

from unittest import mock

import pytest
from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.spine import declarations as decl
from astrolog.spine import object_answer, objects, stages
from astrolog.spine.identify import identify_frames
from conftest import all_objects, apply, by_name, db, populate, review, settled, unnamed_cards
from identify_bench import M45
from synthetic import build_archive


@pytest.fixture
def client_col_catalogo(db_path_col_catalogo, tmp_path):
    """Come `client`, ma col catalogo vero dentro: serve dove si guardano i candidati, che
    senza catalogo non esistono."""
    build_archive(tmp_path / "lib")
    populate(db_path_col_catalogo, tmp_path / "lib")
    with TestClient(create_app(db_path_col_catalogo), base_url="http://localhost") as c:
        yield c


# --- la sezione Oggetti -------------------------------------------------------------------


def test_apply_does_not_silence_an_object_the_app_is_still_unsure_about(client_banco):
    """Un oggetto su cui l'app ha un **dubbio** e' una domanda aperta: la pagina lo mette in cima
    e gli da' i candidati del cielo da cliccare. "Ho visto la pagina" non e' una risposta a "quale
    oggetto era", quindi l'Applica non lo spegne -- lo spegne solo la risposta.

    Il banco misto serve proprio qui: l'oggetto **sicuro** deve continuare a spegnersi vedendolo
    (la pagina e' anche un inventario, e un conto che non puo' tornare a zero e' rumore), il
    **dubbio** no. Su un banco dove tutti gli oggetti sono dubbi questa distinzione sarebbe vera
    per caso.

    Il dubbio si guarda **coi suoi candidati**, che e' quello che `object_still_open` chiede: un
    dubbio senza niente da cliccare non e' una domanda aperta, e restare acceso gli impedirebbe
    per sempre di tornare a zero."""
    page = review(client_banco)
    dubbi = sorted(
        o["key"] for o in page["objects"] if o["confidence"] == "low" and o["candidates"]
    )
    assert dubbi, "il banco misto deve avere un oggetto dubbio coi candidati da cliccare"

    apply(client_banco, seen=page["seen"])

    dopo = all_objects(client_banco)
    ancora = {o["key"]: o for o in dopo if o["confidence"] == "low" and o["candidates"]}
    assert sorted(ancora) == dubbi, "un dubbio e' sparito senza che nessuno gli rispondesse"
    for chiave, riga in ancora.items():
        assert riga["confirmed"] is False, f"{chiave}: spento senza avergli risposto"
    assert by_name(dopo, "M 31")["confirmed"] is True

    # E l'altra meta', che senza questa riga non ha nessuna guardia: un dubbio **senza** candidati
    # si spegne vedendolo. Non e' una svista, e' la promessa che il conto puo' tornare a zero --
    # senza niente da cliccare, quella domanda non si chiuderebbe mai (`review_page.py`).
    muti = [o for o in dopo if o["confidence"] == "low" and not o["candidates"]]
    assert muti, "il banco misto deve avere anche un dubbio senza niente da cliccare"
    for riga in muti:
        assert riga["confirmed"] is True, f"{riga['key']}: resta acceso e nessuno puo' spegnerlo"


def test_the_objects_section_shows_the_archive_objects_not_the_header_spellings(client):
    """Prima elencava le grafie grezze raggruppate: una riga per `M 31`, una per `M31`, e i
    conteggi che si sparpagliavano. Ora e' l'oggetto dell'archivio, con dentro tutte le sue
    grafie."""
    page = review(client)
    m31 = by_name(page["objects"], "M 31")
    assert m31["id"] and m31["frames"] == 5
    assert m31["method"] == "exact_name" and m31["confidence"] == "low"
    assert m31["confirmed"] is False
    # senza catalogo caricato l'oggetto e' fuori catalogo, e non e' un guasto
    assert m31["slug"] is None


def test_an_object_carries_its_hours_and_the_copy_does_not_count(client):
    """Le ore arrivano fino alla pagina, ed e' la stessa regola del conteggio: M 31 ha cinque pose
    da 120 secondi **piu' una copia riscritta** con lo stesso tempo, quindi 600 secondi e non 720.
    Un numero esatto e non un "maggiore di zero": una guardia che si accontenta di un positivo
    resterebbe verde anche contando le copie."""
    m31 = by_name(review(client)["objects"], "M 31")
    assert (m31["frames"], m31["integration_s"], m31["untimed"]) == (5, 600.0, 0)


def test_the_ones_to_decide_come_first(client_banco):
    """La regola della pagina: in cima cio' su cui l'app ha un dubbio, sotto gli altri.
    Chi apre deve vedere il lavoro, non scorrere per trovarlo."""
    page = review(client_banco)
    livelli = [o["confidence"] for o in page["objects"]]
    assert "low" in livelli and set(livelli) != {"low"}, "il banco non e' misto: non prova niente"
    dubbi = [c for c in livelli if c == "low"]
    assert livelli[: len(dubbi)] == dubbi


def test_the_objects_count_in_what_is_left_to_confirm(client):
    """Prima gli oggetti non entravano nel contatore della pagina: si poteva leggere `0 da
    confermare` con tutto l'archivio senza un nome."""
    page = review(client)
    da_confermare = [o for o in page["objects"] if not o["confirmed"]]
    assert da_confermare
    assert page["to_confirm"] >= len(da_confermare)


def test_the_frames_with_no_name_and_no_sky_are_asked_by_group(client):
    """Si chiede per gruppo, mai per file: `le N pose di quella notte, puntate li', non hanno un
    oggetto`."""
    page = review(client)
    gruppi = unnamed_cards(page)
    assert gruppi
    for gruppo in gruppi:
        assert gruppo["key"] and gruppo["frames"] > 0


def test_a_doubtful_object_carries_the_candidates_the_sky_found(client_col_catalogo):
    """Il contratto: quando il cielo dice un'altra cosa, la pagina mostra **cosa c'e' invece a
    quelle coordinate**. Li scrive chi identifica (`test_object_candidates.py`)."""
    conn = db(client_col_catalogo)
    try:
        # una posa di M 31 col cielo di M 45: e' il ramo `sky_disagrees`, e va a conferma
        frame_id = conn.execute("SELECT id FROM frames ORDER BY id LIMIT 1").fetchone()[0]
        conn.execute("UPDATE frames SET object_raw = 'M 31' WHERE id = ?", (frame_id,))
        conn.execute(
            "INSERT INTO frame_wcs(frame_id, ra_deg, dec_deg, scale_arcsec_px, width_deg,"
            " height_deg, rotation_deg, solved_at)"
            " VALUES(?, ?, ?, 2.0, 1.5, 1.0, 0, 'x')",
            (frame_id, *M45),
        )
        stages.set_status(conn, frame_id, "solve", "done")
        stages.invalidate(conn, [frame_id], "identify")
        conn.commit()
        list(identify_frames(conn))
        conn.commit()
    finally:
        conn.close()

    page = review(client_col_catalogo)
    dubbio = next(o for o in page["objects"] if o["confidence"] == "low" and o["candidates"])
    nomi = [c["name"] for c in dubbio["candidates"]]
    assert "M 45" in nomi  # cio' che c'e' davvero a quelle coordinate
    for c in dubbio["candidates"]:
        # il punteggio decide l'ordine, e lo schermo non lo mostra: non viaggia
        assert c["slug"] and "in_frame" in c and "score" not in c


def test_a_sure_object_carries_no_candidates(client_banco):
    """I candidati costano un cono: si scrivono solo per cio' su cui si deve decidere.

    Il banco e' misto apposta: l'oggetto sicuro ha un cielo, quindi i candidati li AVREBBE --
    e' la sola forma in cui questo test puo' fallire se il filtro sparisce."""
    page = review(client_banco)
    sicuri = [o for o in page["objects"] if o["confidence"] != "low"]
    assert sicuri, "il banco non ha nessun oggetto sicuro: il test non prova niente"
    for o in sicuri:
        assert o["candidates"] == []


def test_an_object_of_the_catalog_with_no_names_of_its_own_is_named_by_the_catalog(client_banco):
    """Il secondo passo del nome. `M 45` e "Pleiades" erano gia' di un altro oggetto, quindi la
    voce vera e' nata senza nomi propri: il suo nome si legge dal catalogo per `catalog_slug`.
    Un `JOIN` naturale su `object_names` qui mostrerebbe una scheda vuota."""
    page = review(client_banco)
    m45 = next(o for o in page["objects"] if o["slug"] == "m-45")
    conn = db(client_banco)
    try:
        propri = conn.execute(
            "SELECT COUNT(*) FROM object_names WHERE object_id = ?", (m45["id"],)
        ).fetchone()[0]
    finally:
        conn.close()
    assert propri == 0
    assert m45["name"] == "M 45"


def test_answering_on_an_object_moves_its_frames_and_locks_it(client_col_catalogo):
    """Il giro intero: si risponde, e le pose ci vanno davvero. Non basta scrivere la
    dichiarazione -- `identify` deve rifare il lavoro e portarcele."""
    page = review(client_col_catalogo)
    m31 = by_name(page["objects"], "M 31")
    esito = apply(client_col_catalogo, objects=[{"key": m31["key"], "slug": "m-45"}],
                  seen=page["seen"])  # fmt: skip
    # sei e non cinque: si rimette in coda anche la copia riscritta, che un oggetto ce l'ha
    # come le altre -- e' solo nei CONTEGGI a schermo che non vale un'ora in piu'
    assert esito["changed"] == 1 and esito["requeued"] == 6

    conn = db(client_col_catalogo)
    try:
        riga = conn.execute(
            "SELECT o.catalog_slug, o.identity_method, COUNT(f.id) pose FROM objects o"
            " JOIN frames f ON f.object_id = o.id WHERE o.catalog_slug = 'm-45' GROUP BY o.id"
        ).fetchone()
        assert riga is not None, "le pose non sono arrivate all'oggetto dichiarato"
        # sei pose attaccate, cinque che contano: la copia riscritta ci va come le altre
        assert (riga["identity_method"], riga["pose"]) == ("user", 6)
    finally:
        conn.close()


def test_a_designation_written_by_hand_is_the_catalog_entry(client_col_catalogo):
    """Chi scrive `M 45` a mano intende la voce del catalogo, non un oggetto fuori catalogo che si
    chiama cosi': le sue ore finirebbero su due voci, una accanto all'altra."""
    page = review(client_col_catalogo)
    m31 = by_name(page["objects"], "M 31")
    apply(client_col_catalogo, objects=[{"key": m31["key"], "name": "m45"}],
          seen=page["seen"])  # fmt: skip
    conn = db(client_col_catalogo)
    try:
        slug = conn.execute(
            "SELECT o.catalog_slug FROM objects o JOIN frames f ON f.object_id = o.id"
            " WHERE o.identity_method = 'user' GROUP BY o.id"
        ).fetchall()
        assert [r[0] for r in slug] == ["m-45"]
    finally:
        conn.close()


def test_two_targets_are_refused_even_when_the_name_is_a_designation(client_col_catalogo):
    """Risolvere la sigla non deve fondere uno slug e un nome in un bersaglio solo: con tutti e due
    la spina rifiuta, anche se il nome e' una sigla che il catalogo conosce."""
    m31 = by_name(review(client_col_catalogo)["objects"], "M 31")
    conn = db(client_col_catalogo)
    try:
        with pytest.raises(ValueError):
            object_answer.declare_object(
                conn, m31["key"].removeprefix("object:"), slug="m-45", name="m 31"
            )
    finally:
        conn.close()


@pytest.mark.parametrize("scritto", ["Il mio campo", "NGC 99999"])
def test_a_name_the_catalog_does_not_have_stays_a_name_even_with_the_catalog(
    client_col_catalogo, scritto
):
    """Col catalogo caricato, un nome libero -- e una sigla ben fatta che il catalogo non ha --
    restano un nome scritto: la sigla si risolve solo dove la voce c'e'."""
    page = review(client_col_catalogo)
    m31 = by_name(page["objects"], "M 31")
    apply(client_col_catalogo, objects=[{"key": m31["key"], "name": scritto}],
          seen=page["seen"])  # fmt: skip
    oggetti = {o["name"]: o["slug"] for o in all_objects(client_col_catalogo)}
    assert scritto in oggetti and oggetti[scritto] is None


def test_an_answer_can_name_an_object_the_catalog_does_not_know(client):
    """Una cometa, un campo stellare, una cosa che l'utente chiama a modo suo: si scrive il
    nome invece di cliccare un candidato."""
    page = review(client)
    m31 = by_name(page["objects"], "M 31")
    apply(client, objects=[{"key": m31["key"], "name": "Il mio campo"}], seen=page["seen"])

    conn = db(client)
    try:
        riga = conn.execute(
            "SELECT o.id, n.origin FROM objects o JOIN object_names n ON n.object_id = o.id"
            " WHERE n.name = 'Il mio campo'"
        ).fetchone()
        assert riga is not None and riga["origin"] == "user"
    finally:
        conn.close()


def test_an_answer_becomes_a_rule_when_the_header_spelling_is_not_ambiguous(client):
    """La promessa della pagina: le risposte diventano regole riusabili. `M 31` nell'archivio
    sintetico punta a un oggetto solo, quindi la regola si impara."""
    page = review(client)
    apply(client, objects=[{"key": by_name(page["objects"], "M 31")["key"], "name": "Andromeda"}],
          seen=page["seen"])  # fmt: skip

    conn = db(client)
    try:
        regole = {
            r["header_value"]: r["target_key"]
            for r in conn.execute("SELECT * FROM header_aliases WHERE kind = 'object'")
        }
        assert regole, "nessuna regola imparata"
        assert set(regole.values()) == {"Andromeda"}
    finally:
        conn.close()


def test_an_answer_does_not_become_a_rule_when_the_spelling_is_a_placeholder(client):
    """`Snapshot` su due cieli diversi non e' un nome, e' un segnaposto: una regola su quella
    grafia tirerebbe su un oggetto pose che guardavano tutt'altro (scelta di Marco,
    2026-09-09)."""
    conn = db(client)
    try:
        ids = [r[0] for r in conn.execute("SELECT id FROM frames ORDER BY id LIMIT 2")]
        conn.execute("UPDATE frames SET object_raw = 'Snapshot' WHERE id IN (?, ?)", ids)
        for frame_id in ids:
            stages.invalidate(conn, [frame_id], "identify")
        # due oggetti distinti che portano la stessa grafia grezza
        conn.execute("UPDATE frames SET object_id = NULL WHERE id IN (?, ?)", ids)
        for n, frame_id in enumerate(ids):
            oid = conn.execute(
                "INSERT INTO objects(identity_method, identity_confidence, created_at)"
                " VALUES('exact_name', 'low', 'now')"
            ).lastrowid
            conn.execute(
                "INSERT INTO object_names(object_id, name, origin, is_primary)"
                " VALUES(?, ?, 'raw', 1)",
                (oid, f"Snapshot {n}"),
            )
            conn.execute("UPDATE frames SET object_id = ? WHERE id = ?", (oid, frame_id))
        conn.commit()
        primo = conn.execute(
            "SELECT n.name FROM object_names n JOIN objects o ON o.id = n.object_id"
            " WHERE o.catalog_slug IS NULL AND n.is_primary = 1 ORDER BY o.id DESC LIMIT 1"
        ).fetchone()[0]
    finally:
        conn.close()

    page = review(client)
    apply(
        client, objects=[{"key": f"object:{primo}", "name": "La mia nebulosa"}], seen=page["seen"]
    )

    conn = db(client)
    try:
        regole = [
            r["header_value"]
            for r in conn.execute("SELECT * FROM header_aliases WHERE kind = 'object'")
        ]
        assert "Snapshot" not in regole
    finally:
        conn.close()


def test_applying_confirms_the_objects_that_were_on_the_page(client):
    """Confermare e' una dichiarazione: un oggetto e' "nuovo" finche' non lo si e' visto una
    volta, e la pagina si ripropone solo quando arriva qualcosa di mai visto."""
    page = review(client)
    assert any(not o["confirmed"] for o in page["objects"])
    apply(client, seen=page["seen"])
    assert not any(o["confirmed"] for o in review(client)["objects"])
    visti = settled(client)
    assert visti and all(o["confirmed"] for o in visti)


def test_a_seen_object_that_has_something_to_click_stays_on_top(client_banco):
    """Un oggetto gia' visto che ha dei candidati da cliccare -- un dubbio nato dopo, o confermato
    per altre strade -- e' ancora una domanda: resta in cima, non si chiude fra i gia' visti."""
    dubbio = next(
        o for o in review(client_banco)["objects"] if o["confidence"] == "low" and o["candidates"]
    )
    with db(client_banco) as conn:
        decl.confirm(conn, "object", dubbio["key"])
    assert dubbio["key"] in {o["key"] for o in review(client_banco)["objects"]}
    assert dubbio["key"] not in {o["key"] for o in settled(client_banco)}


def test_the_settled_objects_leave_the_page_and_come_in_pages(client_banco):
    """Gli oggetti gia' visti, senza niente da scegliere, non stanno fra le domande (Marco,
    27/9/2026): la pagina ne dice quanti sono, e si leggono a pagine. In cima restano quelli con
    qualcosa da cliccare e quelli nuovi, che contano fra le cose da confermare; nessuno si perde e
    nessuno sta in due posti."""
    prima = review(client_banco)
    tutti = {o["key"] for o in prima["objects"]}
    assert prima["settled_objects"] == 0  # a pagina mai vista, ogni oggetto e' nuovo
    apply(client_banco, seen=prima["seen"])

    dopo = review(client_banco)
    aperti = {o["key"] for o in dopo["objects"]}
    assert all(o["confidence"] == "low" or not o["confirmed"] for o in dopo["objects"])
    certi = [o["key"] for o in settled(client_banco, limit=1)]
    assert len(certi) == dopo["settled_objects"] > 0
    assert len(set(certi)) == len(certi) and not aperti & set(certi)
    assert aperti | set(certi) == tutti


def test_an_answer_with_both_a_slug_and_a_name_is_refused(client):
    """Sono la stessa domanda, non due: accettarli tutti e due vorrebbe dire scegliere noi
    quale vince, e nessuna delle due scelte e' cio' che l'utente ha chiesto."""
    page = review(client)
    m31 = by_name(page["objects"], "M 31")
    r = client.post(
        "/api/v1/review/apply",
        json={"objects": [{"key": m31["key"], "slug": "m-45", "name": "Andromeda"}]},
    )
    assert r.status_code == 422, r.text


def test_an_answer_on_an_object_that_is_not_there_is_a_404(client):
    r = client.post(
        "/api/v1/review/apply", json={"objects": [{"key": "object:non-c-e", "slug": "m-45"}]}
    )
    assert r.status_code == 404, r.text


@pytest.mark.parametrize("banco", ["client", "client_banco"])
def test_every_object_is_found_again_by_the_key_the_page_gives_it(request, banco):
    """La risposta cerca l'oggetto per la chiave che la pagina gli ha dato (`objects.by_key`), e
    la pagina gliela da' con `objects.stable_key`: lo slug di catalogo o il nome primario. Non e'
    la ricerca per nome di `identify` (`identify_store.object_by_name`), che guarda tutte le
    grafie: e' un'altra domanda, e le due non vanno unite."""
    with db(request.getfixturevalue(banco)) as conn:
        oggetti = objects.listing(conn)
        # fuori catalogo su tutti e due i banchi; di catalogo solo sul banco misto
        assert any(o["catalog_slug"] is None for o in oggetti)
        assert banco == "client" or any(o["catalog_slug"] for o in oggetti)
        for oggetto in oggetti:
            ritrovato = objects.by_key(conn, objects.stable_key(oggetto))
            assert ritrovato is not None and ritrovato["id"] == oggetto["id"], oggetto


def test_an_answer_travels_on_a_stable_key_not_on_a_row_number(client_banco):
    """Lo schema lo dice per le dichiarazioni, e vale anche per la risposta che le crea: una
    chiave stabile, **mai un numero di riga**.

    Qui il caso si **costruisce**: l'oggetto sparisce e un altro nasce sul suo numero di riga.
    In archivio non capita piu' da solo -- `objects.id` e' AUTOINCREMENT, perche' Da confermare
    usa i numeri di riga per dire "ho visto fin qui" -- ma la regola non deve dipendere da
    questo: una risposta viaggia sulla chiave, e su un id sbagliato deve dire 404, non colpire in
    silenzio l'oggetto che quel numero ce l'ha adesso."""
    page = review(client_banco)
    m45 = next(o for o in page["objects"] if o["slug"] == "m-45")
    assert m45["key"] == "object:m-45"

    # l'oggetto sparisce e un altro nasce sul suo numero di riga (scritto a mano: vedi sopra)
    conn = db(client_banco)
    try:
        vecchio_id = m45["id"]
        conn.execute("UPDATE frames SET object_id = NULL WHERE object_id = ?", (vecchio_id,))
        conn.execute("DELETE FROM objects WHERE id = ?", (vecchio_id,))
        conn.execute(
            "INSERT INTO objects(id, catalog_slug, identity_method, identity_confidence,"
            " created_at) VALUES(?, 'm-101', 'coord_confirmed', 'certain', 'now')",
            (vecchio_id,),
        )
        conn.commit()
    finally:
        conn.close()

    r = client_banco.post(
        "/api/v1/review/apply", json={"objects": [{"key": m45["key"], "slug": "m-31"}]}
    )
    assert r.status_code == 404, "la risposta ha colpito l'oggetto sbagliato invece di dire 404"


def test_an_answer_to_a_slug_the_catalog_does_not_know_is_refused_at_once(client_banco):
    """Non si scrive una dichiarazione verso il nulla: prima si controlla che quella voce ci
    sia. Senza, l'Applica rispondeva 200, scriveva la correzione, imparava una regola verso di
    lei e la confermava -- e solo lo stadio, molto dopo, scopriva che non esisteva e lo metteva
    in un log che nessuno legge."""
    page = review(client_banco)
    m45 = next(o for o in page["objects"] if o["slug"] == "m-45")
    r = client_banco.post(
        "/api/v1/review/apply", json={"objects": [{"key": m45["key"], "slug": "non-esiste"}]}
    )
    assert r.status_code == 422, r.text
    assert r.json()["detail"]["code"] == "unknown_target"


def test_a_mixed_answer_runs_both_stages(client):
    """Rispondere su un filtro e su un oggetto insieme fa ripartire tutti e due i lavori, e in
    quest'ordine: con la sola normalizzazione la risposta sugli oggetti restava ferma finche'
    l'utente non cliccava Avvia -- e lui aveva appena cliccato Applica. In coda c'e' `group`,
    perche' una posa che cambia oggetto cambia anche sessione.

    Il banco e' l'archivio sintetico e non il banco misto: li' non c'e' nessun pezzo da
    dichiarare (le pose sono `INSERT` diretti, `rigs` e' vuota), quindi la risposta non era mai
    davvero mista e questa guardia e' rimasta verde per un giro intero col ramo scoperto."""
    page = review(client)
    h = by_name(page["filters"], "H")
    primo = page["objects"][0]
    with mock.patch.object(client.app.state.worker, "start") as start:
        apply(
            client,
            objects=[{"key": primo["key"], "name": "La mia cometa"}],
            filters=[{"id": h["id"], "bands": [{"band": "HA", "width_nm": 3.0}]}],
            seen=page["seen"],
        )
    assert [s.name for s in start.call_args[0][0]] == ["normalize", "identify", "group"]


def test_an_answer_on_a_filter_alone_also_redoes_the_names_and_the_nights(client):
    """Il difetto trovato dall'audit: rispondere su un **filtro** rimetteva in coda anche il
    nome e le notti (`invalidate` lo fa: cambiano i vocabolari, cambia cio' che quelle pose
    vogliono dire), ma l'Applica accodava la sola normalizzazione -- e i due stadi restavano
    `pending` finche' l'utente non cliccava Avvia. Il grafo era scritto due volte: in
    `stages.DEPENDS` e, per una coppia sola, in `run`. Ora chi tira dietro chi lo dice il
    grafo, e basta."""
    page = review(client)
    h = by_name(page["filters"], "H")
    with mock.patch.object(client.app.state.worker, "start") as start:
        apply(
            client,
            filters=[{"id": h["id"], "bands": [{"band": "HA", "width_nm": 3.0}]}],
            seen=page["seen"],
        )
    assert [s.name for s in start.call_args[0][0]] == ["normalize", "identify", "group"]


def test_an_answer_on_the_objects_alone_leaves_the_normalization_alone(client):
    """Il gemello dell'altra meta': rifare la normalizzazione per una risposta sui soli oggetti
    sarebbe rileggere vocabolari che nessuno ha toccato."""
    page = review(client)
    primo = page["objects"][0]
    with mock.patch.object(client.app.state.worker, "start") as start:
        apply(
            client,
            objects=[{"key": primo["key"], "name": "La mia cometa"}],
            seen=page["seen"],
        )
    assert [s.name for s in start.call_args[0][0]] == ["identify", "group"]
