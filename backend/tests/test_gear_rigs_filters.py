"""I gesti dell'Attrezzatura sui **corredi**, sui **filtri** e sull'**unione di due pezzi**, dalla
stessa mano di *Da confermare* (Marco, 25/9/2026).

Regole, e il test che le rompe:

* **Un corredo prende un nome dall'Attrezzatura**, e il nome resta alla riga.
* **Un filtro rinominato o unito non rinasce**: la regola imparata vale anche sul nome che il
  vocabolario da' (`L` diventa `Lum`), dopo il colore -- quindi una posa con la matrice resta OSC.
* **Un filtro si unisce solo in uno con la banda nota**, mai alla riga "nessun filtro" ne' da lei.
* **Un modello del catalogo che non esiste si rifiuta**, prima di scrivere.
* **Due pezzi si uniscono anche dall'Attrezzatura**, dalla stessa mano di *Da confermare*.
"""

import pytest

from astrolog.spine.normalize import normalize_frames
from astrolog.spine.scan import scan_folder
from conftest import by_name, db, write_light


def _gear(client):
    return client.get("/api/v1/gear").json()


def _filtro(client, nome):
    return by_name(_gear(client)["filters"], nome)


def _scansiona_un_altro(client, tmp_path, filtro, **header):
    """Un frame nuovo con quel filtro scritto nell'header, letto e normalizzato. Prima si aspetta
    il lavoro che il gesto ha fatto ripartire: due normalizzazioni insieme si chiudono il
    database a vicenda, o questa legge il frame prima che l'altra abbia finito."""
    client.app.state.worker.join(10.0)
    write_light(tmp_path / "lib" / "nina" / "dopo.fits", filt=filtro, INSTRUME="ATR2600M", **header)
    with db(client) as conn:
        list(scan_folder(conn, 1))
        list(normalize_frames(conn))
        riga = conn.execute(
            "SELECT fi.name FROM frames f JOIN positions p ON p.frame_id = f.id"
            " LEFT JOIN filters fi ON fi.id = f.filter_id WHERE p.rel_path LIKE '%dopo.fits'"
        ).fetchone()
    return riga["name"]


def test_a_rig_gets_its_name_from_the_gear_page(client):
    rig = _gear(client)["rigs"][0]
    r = client.patch(f"/api/v1/gear/rigs/{rig['id']}", json={"name": "Il principale"})
    assert r.status_code == 200, r.text
    # un nome non cambia il senso di nessuna posa: niente da rifare, e il lavoro non parte
    assert (r.json()["requeued"], r.json()["run_started"]) == (0, False)
    assert next(g for g in _gear(client)["rigs"] if g["id"] == rig["id"])["name"] == "Il principale"


def test_a_renamed_recognised_filter_does_not_come_back(client, tmp_path):
    lum = _filtro(client, "Lum")
    r = client.patch(f"/api/v1/gear/filters/{lum['id']}", json={"name": "Astronomik L"})
    assert r.status_code == 200, r.text
    assert _scansiona_un_altro(client, tmp_path, "L") == "Astronomik L"
    assert "Lum" not in [f["name"] for f in _gear(client)["filters"]], "il filtro e' rinato"


def test_a_colour_frame_stays_osc_after_a_rename(client, tmp_path):
    """La regola imparata vale sul nome che il vocabolario da', dopo il colore: una posa con la
    matrice che scrive `L` e' OSC, e rinominare `Lum` non la porta sul filtro mono."""
    lum = _filtro(client, "Lum")
    client.patch(f"/api/v1/gear/filters/{lum['id']}", json={"name": "Astronomik L"})
    assert _scansiona_un_altro(client, tmp_path, "L", BAYERPAT="RGGB") == "OSC"


def test_a_merged_recognised_filter_does_not_come_back(client, tmp_path):
    lum, ha = _filtro(client, "Lum"), _filtro(client, "H\u03b1")
    r = client.patch(f"/api/v1/gear/filters/{lum['id']}", json={"merge_into": ha["id"]})
    assert r.status_code == 200, r.text
    assert _scansiona_un_altro(client, tmp_path, "L") == "H\u03b1"
    assert "Lum" not in [f["name"] for f in _gear(client)["filters"]], "il filtro e' rinato"


def test_the_card_of_a_filter_is_written_from_the_gear_page(client):
    lum = _filtro(client, "Lum")
    corpo = {"brand": "Astronomik", "model": "L-2"}
    assert client.patch(f"/api/v1/gear/filters/{lum['id']}", json=corpo).status_code == 200
    assert {k: _filtro(client, "Lum")[k] for k in ("brand", "model")} == corpo


def test_a_filter_is_never_merged_into_or_from_no_filter(client):
    with db(client) as conn:
        conn.execute(
            "INSERT INTO filters(name, passband, is_none, created_at)"
            " VALUES('None', 'NONE', 1, 'ora')"
        )
        nessuno = conn.execute("SELECT id FROM filters WHERE is_none = 1").fetchone()[0]
    lum = _filtro(client, "Lum")
    for da, verso in ((lum["id"], nessuno), (nessuno, lum["id"])):
        r = client.patch(f"/api/v1/gear/filters/{da}", json={"merge_into": verso})
        assert r.status_code == 422 and r.json()["detail"]["code"] == "merge_refused"


def test_a_filter_is_merged_only_into_one_with_a_known_band(client):
    """La stessa regola della tendina di *Da confermare*: un filtro di cui non si sa la banda non
    dice cosa c'era davanti, e l'Attrezzatura non lo offre come destinazione."""
    lum, h = _filtro(client, "Lum"), _filtro(client, "H")
    assert h["id"] not in lum["mergeable_into"]
    r = client.patch(f"/api/v1/gear/filters/{lum['id']}", json={"merge_into": h["id"]})
    assert (r.status_code, r.json()["detail"]["code"]) == (422, "merge_refused")


def test_a_merge_into_a_filter_that_is_gone_says_the_page_is_old(client):
    lum = _filtro(client, "Lum")
    r = client.patch(f"/api/v1/gear/filters/{lum['id']}", json={"merge_into": 99999})
    assert (r.status_code, r.json()["detail"]["code"]) == (404, "not_found")


def test_a_catalog_model_that_does_not_exist_is_refused(client):
    lum = _filtro(client, "Lum")
    r = client.patch(f"/api/v1/gear/filters/{lum['id']}", json={"catalog_id": "non-esiste"})
    assert r.status_code == 404
    assert _filtro(client, "Lum")["model"] is None


def test_two_pieces_are_merged_from_the_gear_page_too(client):
    pezzi = {p["name"]: p for p in _gear(client)["instruments"]}
    assorbita, tenuta = pezzi["ATR2600M"], pezzi["ATR2600M(USB2.0)"]
    assert tenuta["id"] in assorbita["mergeable_into"]
    r = client.patch(
        f"/api/v1/gear/instruments/{assorbita['id']}", json={"merge_into": tenuta["id"]}
    )
    assert r.status_code == 200, r.text
    assert "ATR2600M" not in [p["name"] for p in _gear(client)["instruments"]]


def test_a_merge_the_spine_refuses_is_said(client):
    askar = by_name(_gear(client)["instruments"], "Askar 103Apo")
    r = client.patch(f"/api/v1/gear/instruments/{askar['id']}", json={"merge_into": askar["id"]})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "merge_refused"


@pytest.mark.parametrize(
    ("risposta", "scritte"),
    [
        ({}, 0),
        ({"bands": [{"band": "HA"}]}, 1),
        ({"is_none": True}, 1),
        ({"brand": "Baader"}, 1),
        ({"merge_into": "Lum"}, 1),
    ],
)
def test_a_filter_answer_counts_only_when_it_writes_something(client, risposta, scritte):
    """La ricevuta dell'Applica conta le risposte che hanno scritto qualcosa: una scheda vuota no,
    la banda, "nessun filtro", un campo o un'unione si'."""
    h = next(f for f in client.get("/api/v1/review").json()["filters"] if f["name"] == "H")
    if "merge_into" in risposta:
        risposta = {"merge_into": _filtro(client, "Lum")["id"]}
    r = client.post("/api/v1/review/apply", json={"filters": [{"id": h["id"], **risposta}]})
    assert r.status_code == 200, r.text
    assert r.json()["changed"] == scritte


def test_a_filter_written_by_hand_takes_the_mono_frames_and_leaves_the_colour_ones_osc(
    client, tmp_path
):
    """Scritto `Blue`, come lo scrive il tuo programma, prende le pose mono che il vocabolario
    chiamerebbe `B`."""
    r = client.post("/api/v1/gear/filters", json={"name": "Blue", "bands": [{"band": "B"}]})
    assert r.status_code == 201, r.text
    assert _scansiona_un_altro(client, tmp_path, "Blue") == "Blue"


def test_a_colour_frame_stays_osc_after_a_filter_written_by_hand(client, tmp_path):
    """Una posa con la matrice che scrive `Blue` resta OSC, come dopo una rinomina."""
    client.post("/api/v1/gear/filters", json={"name": "Blue", "bands": [{"band": "B"}]})
    assert _scansiona_un_altro(client, tmp_path, "Blue", BAYERPAT="RGGB") == "OSC"


def test_a_filter_you_already_have_under_the_app_name_is_not_written_twice(client):
    """Scansionato l'archivio, le pose `L` stanno su `Lum`: scrivere a mano `L` farebbe due righe
    dello stesso filtro con le ore divise. Si rifiuta, e si rinomina quello che c'e'."""
    r = client.post("/api/v1/gear/filters", json={"name": "L", "bands": [{"band": "L"}]})
    assert (r.status_code, r.json()["detail"]["code"]) == (409, "spelling_taken")


def test_a_mono_frame_that_writes_the_app_name_goes_to_the_filter_written_by_hand(client, tmp_path):
    client.post("/api/v1/gear/filters", json={"name": "Blue", "bands": [{"band": "B"}]})
    assert _scansiona_un_altro(client, tmp_path, "B") == "Blue"


def test_a_colour_frame_that_writes_the_app_name_stays_osc_after_a_filter_written_by_hand(
    client, tmp_path
):
    """Il grezzo uguale al nome del vocabolario (`B`) aggancia la regola gia' prima del colore:
    su una posa a colori una banda larga non c'e', la matrice e' il filtro, e resta OSC."""
    client.post("/api/v1/gear/filters", json={"name": "Blue", "bands": [{"band": "B"}]})
    assert _scansiona_un_altro(client, tmp_path, "B", BAYERPAT="RGGB") == "OSC"


def test_a_colour_frame_that_writes_the_app_name_stays_osc_after_a_rename(client, tmp_path):
    lum = _filtro(client, "Lum")
    client.patch(f"/api/v1/gear/filters/{lum['id']}", json={"name": "Astronomik L"})
    assert _scansiona_un_altro(client, tmp_path, "Lum", BAYERPAT="RGGB") == "OSC"


def test_an_answer_on_a_word_the_vocabulary_does_not_know_stays_on_a_colour_camera(
    client, tmp_path
):
    """La matrice vince solo dove il vocabolario sa gia' che la parola e' una banda larga. Una
    risposta di Da confermare su `Filtro1` -- per un UV/IR-cut si risponde "e' il mio L" -- resta
    la tua anche su una camera a colori: e' la tua parola, non una deduzione."""
    from astrolog.spine import declarations

    with db(client) as conn:
        declarations.learn(conn, "filter", "Filtro1", "Lum")
    assert _scansiona_un_altro(client, tmp_path, "Filtro1", BAYERPAT="RGGB") == "Lum"
