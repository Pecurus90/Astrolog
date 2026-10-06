"""Da confermare, "sono lo stesso pezzo?": due grafie della stessa camera, e l'app lo fa notare.

Marco, 15/9/2026: `ATR2600M` e `ATR2600M(USB2.0)` sono la stessa camera vista da due driver, e la
pagina deve chiederlo. Un'unione non si disfa, quindi la regola chiede una **prova positiva** e
non la sola assenza di differenze: la regola larga proponeva `Canon EF (50mm)` con `(200mm)`,
`C8` con `C8 (Hyperstar)`, `Atik 460EX (Mono)` con `(Color)`. Il criterio sta in
`api/lookalike.py`.

Le prove guardano sempre il pezzo INSERITO: ha zero pose, quindi e' il piu' leggero e il solo che
puo' essere chiesto. Guardare l'altro farebbe passare la prova per la sola regola della direzione,
qualunque cosa dica la regola sotto esame. L'archivio sintetico ha `ATR2600M` (1 posa) e
`ATR2600M(USB2.0)` (7), mono e con pixel 3,76; `QHY268M` e `ASI2600MM Pro` a 3,76; la Canon a colori
a 4,29.
"""

from astrolog.api import lookalike
from astrolog.clock import now_iso
from astrolog.db.connect import connect
from conftest import apply, correct, review

PIXEL = 3.76  # quello delle camere mono dell'archivio sintetico


def _pezzo(client, kind, name, **colonne):
    campi = {"kind": kind, "name": name, "detected": 1, "created_at": now_iso(), **colonne}
    with connect(client.app.state.db_path) as conn:
        conn.execute(
            f"INSERT INTO instruments({', '.join(campi)}) VALUES({', '.join('?' * len(campi))})",  # noqa: S608 - colonne scritte qui
            list(campi.values()),
        )


def _id(client, name):
    with connect(client.app.state.db_path) as conn:
        return conn.execute("SELECT id FROM instruments WHERE name = ?", (name,)).fetchone()[0]


def _proposte(client, *nomi):
    """Per ogni nome, il pezzo in cui la pagina propone di unirlo: `None` se non chiede."""
    domande = {q["name"]: q["into_id"] for q in review(client)["lookalikes"]}
    return [domande.get(n) for n in nomi]


def test_two_spellings_of_the_same_camera_are_proposed_for_a_merge(client):
    """Fra parentesi il driver scrive un'annotazione, non il modello -- lo stesso principio per
    cui l'indice ASCOM `(1)` si toglie gia'. Si chiede sulla grafia con meno pose, verso quella
    con piu' pose, e una volta sola."""
    tenuta = _id(client, "ATR2600M(USB2.0)")
    assert _proposte(client, "ATR2600M", "ATR2600M(USB2.0)") == [tenuta, None]


def test_spaces_signs_and_capitals_do_not_make_another_model(client):
    _pezzo(client, "camera", "ATR-2600 M", pixel_size_um=PIXEL)
    _pezzo(client, "camera", "atr2600m (usb3.0)", pixel_size_um=PIXEL)
    tenuta = _id(client, "ATR2600M(USB2.0)")
    assert _proposte(client, "ATR-2600 M", "atr2600m (usb3.0)") == [tenuta] * 2


def test_a_mono_declared_on_one_spelling_stays_with_the_one_the_files_leave_blank(client):
    """Il caso di Marco: dice "mono" su `ATR2600M(USB2.0)`, e `ATR2600M` -- il cui colore i file non
    dicono, perche' una mono non porta la matrice -- deve restare chiesta verso di lei. E' per
    questo che il colore che manca vale mono: se fosse un valore a se', una risposta data su una
    sola grafia separerebbe le due."""
    tenuta = _id(client, "ATR2600M(USB2.0)")
    assert correct(client, tenuta, camera_type="mono").status_code == 200
    assert _proposte(client, "ATR2600M") == [tenuta]


def test_a_name_that_only_starts_the_same_is_another_model(client):
    """`QHY268M` e `QHY268MC`, `ASI2600MM` e `ASI2600MM Pro`: cominciano uguale, e sono modelli
    diversi con lo stesso pixel. Nei due versi: il nuovo e' il piu' lungo, o il piu' corto."""
    for nome in ("QHY268MC", "ATR2600M Pro", "ASI2600MM"):
        _pezzo(client, "camera", nome, pixel_size_um=PIXEL)
    assert _proposte(client, "QHY268MC", "ATR2600M Pro", "ASI2600MM") == [None, None, None]


def test_the_pixel_must_be_known_and_equal_for_both(client):
    """La prova positiva: lo stesso sensore. Un pixel diverso sono due sensori, e un pixel che uno
    dei due non dice non prova niente."""
    _pezzo(client, "camera", "ATR2600M (USB3.0)", pixel_size_um=4.63)
    _pezzo(client, "camera", "QHY700M")
    _pezzo(client, "camera", "QHY700M (USB)", pixel_size_um=PIXEL)
    # e tutte e due senza: due silenzi non sono lo stesso sensore
    _pezzo(client, "camera", "QHY800M")
    _pezzo(client, "camera", "QHY800M (USB)")
    nomi = ("ATR2600M (USB3.0)", "QHY700M (USB)", "QHY800M (USB)")
    assert _proposte(client, *nomi) == [None, None, None]


def test_the_colour_must_be_the_same_and_unknown_is_not_colour(client):
    """`Atik 460EX (Mono)` accanto a `Atik 460EX (Color)`: una mono letta dai file non ha il
    colore scritto, quindi un confronto fatto solo sui valori noti a tutte e due non la fermerebbe
    mai. Il colore che manca vale mono, e mono non e' "a colori": una sola che lo dice basta."""
    _pezzo(client, "camera", "Atik 460EX (Color)", camera_type="color", pixel_size_um=4.54)
    _pezzo(client, "camera", "Atik 460EX (Mono)", pixel_size_um=4.54)
    _pezzo(client, "camera", "Canon EOS 700D (mod)", camera_type="mono", pixel_size_um=4.29)
    assert _proposte(client, "Atik 460EX (Mono)", "Canon EOS 700D (mod)") == [None, None]


def test_only_cameras_are_proposed(client):
    """Marco ha chiesto delle camere, ed e' li' che esiste una prova (il sensore). Un'ottica o una
    montatura non ne hanno: `Canon EF (50mm)` e `(200mm)` sarebbero proposte per il solo nome."""
    _pezzo(client, "optics", "Canon EF (200mm)", pixel_size_um=PIXEL)
    _pezzo(client, "optics", "Canon EF (50mm)", pixel_size_um=PIXEL)
    assert _proposte(client, "Canon EF (50mm)") == [None]


def test_at_equal_frames_the_first_arrived_is_kept(client):
    _pezzo(client, "camera", "QHY600M", pixel_size_um=PIXEL)
    _pezzo(client, "camera", "QHY600M (USB)", pixel_size_um=PIXEL)
    assert _proposte(client, "QHY600M (USB)") == [_id(client, "QHY600M")]


def test_names_that_clean_down_to_nothing_are_not_the_same_name(client):
    """Un nome in un alfabeto non latino, ridotto a lettere e cifre, resta vuoto: due nomi vuoti
    non sono lo stesso nome."""
    _pezzo(client, "camera", "Камера", pixel_size_um=PIXEL)
    _pezzo(client, "camera", "Вторая камера", pixel_size_um=PIXEL)
    assert _proposte(client, "Вторая камера") == [None]


def test_seeing_the_page_does_not_answer_the_question(client):
    """L'app non puo' sapere se sono lo stesso pezzo (Marco, 25/9/2026): un Applica a vuoto non e'
    una risposta, e la domanda resta nel conto."""
    prima = review(client)
    apply(client, seen=prima["seen"])
    dopo = review(client)
    assert _proposte(client, "ATR2600M") == [_id(client, "ATR2600M(USB2.0)")]
    assert dopo["to_confirm"] == prima["to_confirm"] - sum(
        # seeing confirms the found objects; a group card waits for its answer
        1
        for o in prima["objects"]
        if o["group"] is None and not o["confirmed"]
    )


def test_a_yes_merges_the_two_spellings(client):
    """Si' e' l'unione: la grafia leggera sparisce, le sue pose passano all'altra, e la domanda con
    lei."""
    leggera, tenuta = _id(client, "ATR2600M"), _id(client, "ATR2600M(USB2.0)")
    fatto = apply(client, lookalikes=[{"id": leggera, "into_id": tenuta, "same": True}])
    assert fatto["changed"] == 1
    with connect(client.app.state.db_path) as conn:
        assert not conn.execute("SELECT 1 FROM instruments WHERE id = ?", (leggera,)).fetchone()
    assert review(client)["lookalikes"] == []


def test_a_no_silences_the_pair_for_good_whichever_way_it_leans(client):
    """No e' una risposta come un si': senza, l'unico modo di far tacere una domanda sbagliata
    sarebbe accettarla, e un'unione non si disfa. Vale anche quando la grafia che era piu' leggera
    diventa la piu' usata, e la domanda si girerebbe."""
    leggera, tenuta = _id(client, "ATR2600M"), _id(client, "ATR2600M(USB2.0)")
    apply(client, lookalikes=[{"id": leggera, "into_id": tenuta, "same": False}])
    assert review(client)["lookalikes"] == []
    with connect(client.app.state.db_path) as conn:
        suo = conn.execute("SELECT id FROM rigs WHERE camera_id = ?", (leggera,)).fetchone()[0]
        conn.execute(
            "UPDATE frames SET rig_id = ?"
            " WHERE rig_id IN (SELECT id FROM rigs WHERE camera_id = ?)",
            (suo, tenuta),
        )
    assert review(client)["lookalikes"] == []


def test_a_no_survives_a_rename_of_the_other_camera(client):
    """Il no nomina l'altra camera, e i nomi cambiano: rinominata dall'Attrezzatura con una grafia
    che resta la stessa camera, la domanda non deve tornare."""
    leggera, tenuta = _id(client, "ATR2600M"), _id(client, "ATR2600M(USB2.0)")
    apply(client, lookalikes=[{"id": leggera, "into_id": tenuta, "same": False}])
    assert correct(client, tenuta, name="ATR2600M (USB2.0)").status_code == 200
    assert review(client)["lookalikes"] == []


def test_two_noes_from_the_same_camera_both_hold(client):
    """Una camera puo' dire no a piu' di una grafia: il secondo no non cancella il primo. Qui la
    terza grafia prende le pose della tenuta, si risponde no anche a lei, e poi le pose tornano:
    la prima coppia non deve riaprirsi."""
    _pezzo(client, "camera", "ATR2600M (USB3)", pixel_size_um=PIXEL)
    leggera, tenuta = _id(client, "ATR2600M"), _id(client, "ATR2600M(USB2.0)")
    terza = _id(client, "ATR2600M (USB3)")
    apply(
        client,
        lookalikes=[
            {"id": leggera, "into_id": tenuta, "same": False},
            {"id": terza, "into_id": tenuta, "same": False},
        ],
    )
    with connect(client.app.state.db_path) as conn:
        conn.execute("UPDATE rigs SET camera_id = ? WHERE camera_id = ?", (terza, tenuta))
    # la tenuta e la terza hanno gia' il loro no: si chiede solo la leggera verso la terza
    assert _proposte(client, "ATR2600M", "ATR2600M(USB2.0)") == [terza, None]
    apply(client, lookalikes=[{"id": leggera, "into_id": terza, "same": False}])
    with connect(client.app.state.db_path) as conn:
        conn.execute("UPDATE rigs SET camera_id = ? WHERE camera_id = ?", (tenuta, terza))
    assert _proposte(client, "ATR2600M") == [None]


def test_an_answer_on_a_pair_the_page_no_longer_asks_is_refused(client):
    """Una coppia che non e' piu' chiesta e' una pagina vecchia: si dice, e non si unisce niente."""
    leggera, tenuta = _id(client, "ATR2600M"), _id(client, "ATR2600M(USB2.0)")
    corpo = {"lookalikes": [{"id": tenuta, "into_id": leggera, "same": True}]}
    r = client.post("/api/v1/review/apply", json=corpo)
    assert r.status_code == 404, r.text
    assert _proposte(client, "ATR2600M") == [tenuta]


def test_the_cameras_do_not_search_the_rigs_row_by_row(client):
    """Il conto delle pose di ogni camera non deve cercare i corredi **una volta per coppia**
    (posa, camera): e' cio' che rendeva la pagina lenta su un archivio grande. Il piano e'
    deterministico: si chiede a SQLite invece di cronometrare."""
    with connect(client.app.state.db_path) as conn:
        piano = [
            r["detail"]
            for r in conn.execute("EXPLAIN QUERY PLAN " + lookalike._CAMERAS, ("[1, 2]",))
        ]
    assert not any("CORRELATED" in riga for riga in piano), piano


def test_lookalike_counts_only_the_cameras_of_a_pair(client, monkeypatch):
    """Le pose si contano solo per le camere che stanno in un gruppo di almeno due: le altre non
    diventano mai una domanda, e contarle vorrebbe dire scorrere l'archivio per ogni camera."""
    contate = []
    vero = lookalike._frames_of

    def conta(conn, ids):
        contate.append(set(ids))
        return vero(conn, ids)

    monkeypatch.setattr(lookalike, "_frames_of", conta)
    with connect(client.app.state.db_path) as conn:
        domande = lookalike.lookalikes(conn)
    assert domande, "il banco non ha coppie: la prova non guarda niente"
    assert contate == [{_id(client, "ATR2600M"), _id(client, "ATR2600M(USB2.0)")}]


def test_lookalike_does_not_count_a_pair_already_answered_no(client, monkeypatch):
    """Un gruppo in cui ogni coppia ha gia' avuto un no non chiede piu' niente, qualunque camera
    sia la piu' usata: contarne le pose vorrebbe dire scorrere l'archivio a ogni apertura, per
    sempre, proprio per chi ha due camere dello stesso modello."""
    leggera, tenuta = _id(client, "ATR2600M"), _id(client, "ATR2600M(USB2.0)")
    apply(client, lookalikes=[{"id": leggera, "into_id": tenuta, "same": False}])
    contate = []
    vero = lookalike._frames_of
    monkeypatch.setattr(lookalike, "_frames_of", lambda c, ids: contate.append(ids) or vero(c, ids))
    with connect(client.app.state.db_path) as conn:
        assert lookalike.lookalikes(conn) == []
    assert contate == []


def test_the_same_pair_twice_in_one_apply_is_refused(client):
    """Due risposte sulla stessa coppia nello stesso Applica sono una pagina che non sa cosa manda:
    si dice, e non si scrive nessuna delle due."""
    leggera, tenuta = _id(client, "ATR2600M"), _id(client, "ATR2600M(USB2.0)")
    coppia = {"id": leggera, "into_id": tenuta}
    corpo = {"lookalikes": [{**coppia, "same": False}, {**coppia, "same": True}]}
    r = client.post("/api/v1/review/apply", json=corpo)
    assert r.status_code == 404, r.text
    assert _proposte(client, "ATR2600M") == [tenuta]


def test_the_pairs_that_weigh_most_come_first(client):
    """In cima la coppia con piu' pose, fra le due grafie: e' dove una risposta sposta di piu'."""
    _pezzo(client, "camera", "QHY600M", pixel_size_um=4.63)
    _pezzo(client, "camera", "QHY600M (USB)", pixel_size_um=4.63)
    assert [q["name"] for q in review(client)["lookalikes"]] == ["ATR2600M", "QHY600M (USB)"]


def test_a_pixel_from_the_sky_is_not_the_proof(client):
    """Il pixel ricavato dal cielo porta l'errore della focale -- un riduttore che l'header non
    conta lo sposta --, quindi non prova che il sensore sia lo stesso: un'unione non si disfa."""
    _pezzo(client, "camera", "QHY600M", pixel_from_sky_um=PIXEL)
    _pezzo(client, "camera", "QHY600M (USB)", pixel_from_sky_um=PIXEL)
    assert _proposte(client, "QHY600M (USB)") == [None]
