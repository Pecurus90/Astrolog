"""Da confermare: la pagina che elenca le domande su cio' che la scansione ha trovato, e
l'Applica che trasforma le risposte in regole valide per tutto l'archivio.

L'archivio di prova e' quello sintetico: dentro ci sono di proposito le lettere sole dei
filtri, la stessa camera scritta in due modi e una montatura al posto dell'ottica. La sezione
Oggetti della stessa pagina sta in `test_review_objects.py`, col suo banco misto.
"""

import re
import threading
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from astrolog.api import review as review_api
from astrolog.api import review_page
from astrolog.api.app import create_app
from astrolog.api.review import unanswered
from astrolog.clock import now_iso
from astrolog.db.connect import connect
from astrolog.spine import stages
from astrolog.vocab.filters import UNKNOWN
from conftest import apply, by_name, db, review, unnamed_cards, wait_until, write_light

# --- l'elenco -------------------------------------------------------------------------


def _filtro(page, nome):
    """Un filtro della pagina, da domanda o fra le scelte: i due elenchi insieme sono tutti."""
    return by_name(page["filters"] + page["filter_choices"], nome)


def test_the_filter_question_does_not_scan_the_whole_archive_per_filter(client):
    """La domanda sui filtri conta le pose dei soli filtri sconosciuti, e le trova con l'indice:
    senza, e' una scansione dell'archivio intero per ogni filtro, anche quando non c'e' niente da
    chiedere."""
    with db(client) as conn:
        plan = " ".join(
            r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + review_api._FILTERS, (UNKNOWN,))
        )
    assert "INDEX frames_filter" in plan, plan


def test_a_group_counts_until_someone_answers():
    """Ogni sezione a gruppi -- camere, pose senza camera, senza ottica, senza nome, mosaici,
    cartelle senza tipo -- conta con la stessa regola: una risposta, anche un no, chiude."""
    assert unanswered([{"answer": None}]) == 1
    assert unanswered([{"answer": {"camera": "Cam"}}]) == 0
    assert unanswered([{"answer": "no"}]) == 0


def test_only_the_filters_the_app_does_not_know_are_asked(client):
    """In Filtri solo i filtri che l'app non riconosce (Marco, 25/9/2026): "che filtro e' H?". Uno
    che il vocabolario riconosce non e' una domanda -- non si elenca e non si conta -- e sta fra
    le scelte. Uno sconosciuto resta una domanda finche' non gli si risponde: vederlo non e'
    rispondere, e un Applica a vuoto non lo spegne."""
    page = review(client)
    aperti = [f["name"] for f in page["filters"]]
    assert aperti, "il banco deve avere almeno un filtro con la banda da dire"
    assert all(f["passband"] == UNKNOWN for f in page["filters"])
    assert "Lum" not in aperti and "Lum" in [f["name"] for f in page["filter_choices"]]

    apply(client)

    dopo = review(client)
    assert [f["name"] for f in dopo["filters"]] == aperti
    assert dopo["to_confirm"] >= len(aperti)


def test_the_most_used_filters_come_first(client):
    """I piu' usati per primi: l'ordine e' una decisione del backend, e la pagina non lo tocca.
    Si guarda che non risalga mai, invece di scrivere i numeri del banco: quelli cambiano, la
    regola no."""
    ultimo = review(client)["filters"][-1]
    with db(client) as conn:
        # l'ultimo prende tutte le pose: i conti del banco da soli sono pari, e non si ordinerebbe
        conn.execute(
            "UPDATE frames SET filter_id = ? WHERE filter_id <> ? OR filter_id IS NULL",
            (ultimo["id"], ultimo["id"]),
        )
    filtri = review(client)["filters"]
    assert len(filtri) > 1, "il banco deve avere due filtri da rispondere, o non si ordina niente"
    assert filtri[0]["id"] == ultimo["id"]
    pose = [f["frames"] for f in filtri]
    assert pose == sorted(pose, reverse=True), pose


def test_review_lists_what_was_found(client):
    """La pagina porta in una risposta le domande aperte -- i filtri da dire, le grafie che
    sembrano un pezzo solo -- e gli oggetti coi conteggi. L'attrezzatura non c'e': un pezzo nuovo
    non e' una domanda, si vede nell'Attrezzatura (Marco, 25/9/2026)."""
    page = review(client)
    assert "instruments" not in page and "rigs" not in page
    assert [(q["name"], q["into_name"]) for q in page["lookalikes"]] == [
        ("ATR2600M", "ATR2600M(USB2.0)")
    ]

    assert _filtro(page, "Lum")["passband"] == "L"
    assert _filtro(page, "H")["passband"] == "UNKNOWN"
    assert _filtro(page, "OSC")["passband"] == "OSC"

    oggetti = {o["name"]: o["frames"] for o in page["objects"]}
    assert oggetti["M 31"] == 5 and oggetti["NGC 6888"] == 2
    # le due pose ASIAIR senza OBJECT: senza nome e senza cielo, elencate per cartella
    assert sum(g["frames"] for g in unnamed_cards(page)) == 2

    # le domande aperte e gli oggetti non ancora visti: prima si poteva leggere "0 da confermare"
    # con tutto l'archivio senza un nome. E le schede sull'attrezzatura, finche' non si risponde
    # (`test_review_gear.py`).
    # gli oggetti contano anche le schede delle pose senza nome
    atteso = len(page["lookalikes"]) + len(page["filters"]) + len(page["objects"])
    atteso += len(page["gear"])
    # le pose ASIAIR, che la camera la dicono e l'ottica no: una scheda che chiede l'ottica
    ottica = [(g["camera"], g["frames"]) for g in page["gear"] if g["asks_optics"]]
    assert ottica == [("Canon EOS 700D", 3)]
    assert page["to_confirm"] == atteso


def test_review_is_empty_on_an_empty_archive(db_path):
    """A mani vuote la pagina non mente: nessuna voce, niente da confermare."""
    with TestClient(create_app(db_path), base_url="http://localhost") as c:
        page = review(c)
        assert page["lookalikes"] == [] and page["filters"] == [] and page["rig_choices"] == []
        assert page["objects"] == [] and page["to_confirm"] == 0


# --- l'Applica ------------------------------------------------------------------------


def test_review_only_new_things(client):
    """La pagina chiede solo cio' che non ha una risposta, e un Applica senza risposte non spegne
    niente (ADR 0014, S4). E un pezzo nuovo non e' una domanda (Marco, 25/9/2026)."""
    domande = review(client)["to_confirm"]
    assert domande > 0
    out = apply(client)
    assert "confirmed" not in out
    assert review(client)["to_confirm"] == domande

    nuovo = client.app.state.db_path
    with connect(nuovo) as conn:
        conn.execute(
            "INSERT INTO instruments(kind, name, detected, created_at)"
            " VALUES('camera', 'ASI533MC', 1, ?)",
            (now_iso(),),
        )
    assert review(client)["to_confirm"] == domande


@pytest.mark.parametrize("ieri", [{"instruments": [], "rigs": []}, {"seen": {"objects": 9}}])
def test_an_answer_with_a_field_we_do_not_know_is_refused(client, ieri):
    """Una pagina aperta prima di un aggiornamento del server manda i nomi di ieri: `instruments`
    e `rigs`, o `seen` (ADR 0014, S4). Scartarli in silenzio farebbe credere a quella pagina di
    aver detto qualcosa; sul NAS e' lo scenario ordinario -- una scheda lasciata aperta sul tablet
    -- quindi si risponde 422 e la pagina lo dice."""
    r = client.post("/api/v1/review/apply", json=ieri)
    assert r.status_code == 422, r.text

    with db(client) as conn:
        quante = conn.execute("SELECT COUNT(*) FROM declarations").fetchone()[0]
    assert quante == 0, "rifiutata la richiesta, ma l'archivio e' stato scritto lo stesso"


def test_review_declares_a_filter_with_its_bands(client):
    """Un duo-banda si dichiara con le sue due larghezze, e la banda canonica si ricava da
    quelle: un fatto, una casa."""
    page = review(client)
    h = by_name(page["filters"], "H")
    out = apply(
        client,
        filters=[
            {
                "id": h["id"],
                "name": "Optolong L-Ultimate",
                "brand": "Optolong",
                "model": "L-Ultimate",
                "bands": [{"band": "HA", "width_nm": 3.0}, {"band": "OIII", "width_nm": 3.0}],
            }
        ],
    )
    assert out["changed"] == 1 and out["requeued"] >= 1

    # risposto, non e' piu' una domanda: sta fra i tuoi filtri
    dopo = review(client)
    assert "H" not in [f["name"] for f in dopo["filters"]]
    assert by_name(dopo["filter_choices"], "Optolong L-Ultimate")["passband"] == "DUO_HAOIII"
    with db(client) as conn:
        riga = conn.execute("SELECT brand FROM filters WHERE id = ?", (h["id"],)).fetchone()
        assert riga["brand"] == "Optolong"
        bande = conn.execute("SELECT band, width_nm FROM filter_bands").fetchall()
        assert {b["band"]: b["width_nm"] for b in bande} == {"HA": 3.0, "OIII": 3.0}


def test_a_model_from_the_catalog_answers_the_question(client):
    """Scegliere un modello in commercio e' una risposta intera: la banda e' quella del modello, la
    domanda si chiude e i frame tornano in lavorazione. Il modello porta la banda, non le bande
    fisiche: senza, la riga restava UNKNOWN e la domanda aperta con la risposta data."""
    h = _filtro(review(client), "H")
    out = apply(client, filters=[{"id": h["id"], "catalog_id": "optolong-l-extreme",
                                  "brand": "Optolong", "model": "L-eXtreme",
                                  "name": "Optolong L-eXtreme"}])  # fmt: skip
    assert out["requeued"] == h["frames"]
    dopo = review(client)
    assert "Optolong L-eXtreme" not in [f["name"] for f in dopo["filters"]]
    assert _filtro(dopo, "Optolong L-eXtreme")["passband"] == "DUO_HAOIII"


@pytest.mark.parametrize("verso", ["nessun filtro", "un altro sconosciuto"])
def test_one_of_mine_is_one_of_the_choices(client, verso):
    """ "E' uno dei miei" si sceglie fra i filtri con la banda nota: unire una grafia nella riga
    "nessun filtro" insegnerebbe una regola che risponde per ogni camera, e unirla a un altro
    filtro sconosciuto lascerebbe la domanda aperta con una risposta data."""
    page = review(client)
    h = _filtro(page, "H")
    with db(client) as conn:
        if verso == "nessun filtro":
            conn.execute(
                "INSERT INTO filters(name, passband, is_none, created_at)"
                " VALUES('None', 'NONE', 1, 'ora')"
            )
            dove = conn.execute("SELECT id FROM filters WHERE is_none = 1").fetchone()[0]
        else:
            dove = next(f["id"] for f in page["filters"] if f["id"] != h["id"])
    corpo = {"filters": [{"id": h["id"], "merge_into": dove}]}
    r = client.post("/api/v1/review/apply", json=corpo)
    assert (r.status_code, r.json()["detail"]["code"]) == (422, "merge_refused")


def test_review_declares_no_filter_at_all(client):
    """ "Nessun filtro" e' una riga esplicita, non un vuoto: si dichiara, e ce n'e' una sola."""
    page = review(client)
    osc = _filtro(page, "OSC")
    apply(client, filters=[{"id": osc["id"], "name": "Nessun filtro", "is_none": True}])
    with db(client) as conn:
        righe = conn.execute("SELECT name, is_none FROM filters WHERE is_none = 1").fetchall()
        assert [(r["name"], r["is_none"]) for r in righe] == [("Nessun filtro", 1)]
        # la riga OSC era un filtro trovato: rinominarla impara la regola sulla sua grafia
        regola = conn.execute(
            "SELECT target_key FROM header_aliases WHERE kind = 'filter' AND header_value = 'osc'"
        ).fetchone()
        assert regola["target_key"] == "Nessun filtro"


def test_review_apply_refuses_while_the_worker_is_busy(client, tmp_path):
    """Un lavoro alla volta: se il worker sta gia' lavorando, l'Applica non scrive niente e
    lo dice, invece di lasciare l'archivio a meta'."""
    gate = threading.Event()
    seen = []
    import astrolog.spine.run as run_mod

    real = run_mod.normalize_frames

    def slow(conn):
        seen.append(1)
        gate.wait(10.0)
        yield from real(conn)

    altra = tmp_path / "altra"
    write_light(altra / "a.fits", obj="M 99")
    fid = client.post("/api/v1/folders", json={"root_path": str(altra)}).json()["id"]
    with mock.patch.object(run_mod, "normalize_frames", slow):
        client.post(f"/api/v1/folders/{fid}/scan")
        assert wait_until(lambda: seen != [])
        r = client.post("/api/v1/review/apply", json={})
        assert r.status_code == 409 and r.json()["detail"]["code"] == "worker_busy"
        gate.set()
        client.app.state.worker.join(10.0)
    with db(client) as conn:
        assert conn.execute("SELECT COUNT(*) FROM declarations").fetchone()[0] == 0


def test_review_merges_two_filters(client):
    """Anche due grafie di filtro si uniscono: la regola resta, le pose passano all'altro."""
    page = review(client)
    tenuto = _filtro(page, "Lum")
    assorbito = _filtro(page, "H")
    out = apply(client, filters=[{"id": assorbito["id"], "merge_into": tenuto["id"]}])
    assert out["requeued"] == assorbito["frames"]
    dopo = review(client)
    assert "H" not in [f["name"] for f in dopo["filters"]]
    with db(client) as conn:
        regola = conn.execute(
            "SELECT target_key FROM header_aliases WHERE kind = 'filter' AND header_value = 'h'"
        ).fetchone()
        assert regola["target_key"] == "Lum"


def test_renaming_a_filter_carries_the_spelling_it_absorbed(client):
    """La catena vale anche per i filtri, perche' la regola la scrive la **stessa** casa: unisci
    `H` in `Lum`, poi rinomini `Lum`, e la regola su `h` deve seguire. Ferma da sola, portava a un
    filtro che non esiste piu', e la prossima posa con `H` ne faceva rinascere uno."""
    page = review(client)
    tenuto, assorbito = _filtro(page, "Lum"), _filtro(page, "H")
    apply(client, filters=[{"id": assorbito["id"], "merge_into": tenuto["id"]}])

    apply(client, filters=[{"id": tenuto["id"], "name": "Luminanza"}])

    with db(client) as conn:
        regola = conn.execute(
            "SELECT target_key FROM header_aliases WHERE kind = 'filter' AND header_value = 'h'"
        ).fetchone()
        assert regola["target_key"] == "Luminanza"


def test_review_says_when_a_name_is_taken(client):
    """Dare a un filtro il nome di un altro non e' un errore di sistema: e' una risposta con
    il suo perche', e non scrive niente."""
    page = review(client)
    h = by_name(page["filters"], "H")
    r = client.post("/api/v1/review/apply", json={"filters": [{"id": h["id"], "name": "Lum"}]})
    assert r.status_code == 409 and r.json()["detail"]["code"] == "name_taken"
    assert by_name(review(client)["filters"], "H")["name"] == "H"


def test_review_a_card_alone_does_not_redo_the_work(client):
    """Scrivere marca e peso non cambia cosa vuol dire una posa: non si rilavora niente.

    Questo test e' caduto **una volta** in parallelo (10/9/2026), e di quel giro e' rimasta una
    riga `FAILED` e nient'altro: mai riprodotto in 140 giri, e la causa scritta allora era
    un'ipotesi che il codice smentisce. Per questo l'asserzione porta con se' la scheda del
    filtro -- la prossima volta che cade, la causa arriva col rosso invece di dover essere
    indovinata a posteriori."""
    page = review(client)
    lum = _filtro(page, "Lum")
    out = apply(client, filters=[{"id": lum["id"], "brand": "Baader", "model": "L 2 pollici"}])
    assert (out["changed"], out["requeued"]) == (1, 0), _scheda_del_filtro(client, lum)


def _scheda_del_filtro(client, prima):
    """Cosa dice il database di quel filtro, per il messaggio di un rosso: com'era la scheda
    quando la pagina l'ha mostrata, com'e' adesso, le sue bande e quante pose lo usano."""
    with db(client) as conn:
        riga = conn.execute("SELECT * FROM filters WHERE id = ?", (prima["id"],)).fetchone()
        bande = [
            dict(b)
            for b in conn.execute("SELECT * FROM filter_bands WHERE filter_id = ?", (prima["id"],))
        ]
        pose = conn.execute(
            "SELECT COUNT(*) FROM frames WHERE filter_id = ?", (prima["id"],)
        ).fetchone()[0]
    return (
        f"la scheda in pagina: {prima}\n"
        f"la riga adesso: {dict(riga) if riga else None}\n"
        f"le bande: {bande}\n"
        f"pose con questo filtro: {pose}"
    )


def test_pipeline_run_picks_up_the_work_left_behind(client):
    """Il pulsante Avvia ha una rotta: raccoglie il lavoro rimasto in coda, e se il worker
    sta gia' lavorando lo dice."""
    with db(client) as conn:
        ids = [r[0] for r in conn.execute("SELECT id FROM frames")]
        stages.invalidate(conn, ids, "normalize")
        # `populate` ha gia' segnato il solve come non risolto: qui si prova il pulsante, e
        # rimetterlo da fare e' l'unico modo di avere del lavoro di solve che aspetta
        for frame_id in ids:
            stages.set_status(conn, frame_id, "solve", "pending")
        assert stages.count_pending(conn, "normalize") == len(ids)
    assert client.post("/api/v1/pipeline/run").status_code == 200
    client.app.state.worker.join(10.0)
    with db(client) as conn:
        assert stages.count_pending(conn, "normalize") == 0
        # il solve aspetta ancora (nella suite ASTAP non c'e'): finche' c'e' lavoro, il
        # pulsante lavora davvero
        assert stages.count_pending(conn, "solve") == len(ids)
    assert client.post("/api/v1/pipeline/run").json()["worker"]["state"] == "running"
    client.app.state.worker.join(10.0)

    # dato il cielo, tocca a identify: il pulsante raccoglie anche quello
    with db(client) as conn:
        for frame_id in ids:
            stages.set_status(conn, frame_id, "solve", "done")
    assert client.post("/api/v1/pipeline/run").json()["worker"]["state"] == "running"
    client.app.state.worker.join(10.0)
    with db(client) as conn:
        assert stages.count_pending(conn, "identify") == 0

    # e quando non resta piu' niente da fare, non occupa il worker
    assert client.post("/api/v1/pipeline/run").json()["worker"]["state"] != "running"


def test_the_button_picks_up_group_when_it_is_the_only_one_left(client):
    """Fermare a meta' di `group` lascia delle pose in coda **solo** per lui: gli stadi a monte
    sono gia' a posto. Se il pulsante non lo conoscesse, la pagina mostrerebbe un residuo che
    "Riprendi" dichiara inesistente, e a sbloccarlo sarebbe solo la scansione dopo -- con in
    mezzo le sessioni gia' staccate, che e' proprio lo stato che la spazzata esiste per
    togliere."""
    with db(client) as conn:
        ids = [r[0] for r in conn.execute("SELECT id FROM frames")]
        for frame_id in ids:
            stages.set_status(conn, frame_id, "group", "pending")
        assert stages.count_pending(conn, "identify") == 0, "il banco non prova quello che dice"
        assert stages.count_pending(conn, "group") == len(ids)

    assert client.post("/api/v1/pipeline/run").json()["worker"]["state"] == "running"
    client.app.state.worker.join(10.0)
    with db(client) as conn:
        assert stages.count_pending(conn, "group") == 0


def test_the_scan_receipt_survives_a_normalize_run(client, tmp_path):
    """Dopo un'Applica il worker sta facendo altro, ma la ricevuta dell'ultima scansione si
    vede ancora: e' quella che l'utente vuole leggere."""
    altra = tmp_path / "altra"
    write_light(altra / "a.fits", obj="M 99")
    fid = client.post("/api/v1/folders", json={"root_path": str(altra)}).json()["id"]
    client.post(f"/api/v1/folders/{fid}/scan")
    client.app.state.worker.join(10.0)
    prima = client.get("/api/v1/pipeline/status").json()["scan"]
    assert prima["receipt"]["status"] == "ok"

    apply(client)
    dopo = client.get("/api/v1/pipeline/status").json()["scan"]
    assert dopo["receipt"] is not None and dopo["receipt"]["id"] == prima["receipt"]["id"]


def test_the_rig_choices_count_the_poses_from_the_index(client):
    """La tendina dei corredi conta le pose di ogni corredo dall'indice, senza leggere la tabella:
    la chiedono la pagina e ogni Applica con una risposta sulla camera."""
    with db(client) as conn:
        plan = " ".join(r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + review_page.USED_RIGS))
    assert re.search(r"COVERING INDEX frames_rig\b", plan), plan
