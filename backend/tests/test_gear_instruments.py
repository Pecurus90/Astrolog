"""L'Attrezzatura, i pezzi: la scheda, le rinomine e le unioni.

Due regole, e ognuna ha qui la sua prova:

- **i campi di una scheda si chiedono solo se l'app ci fa qualcosa** (`docs/coda.md`, 7/9/2026),
  e quali siano per ogni tipo lo decide il backend: la pagina li mostra e basta;
- **si unisce solo dentro lo stesso tipo**, e solo dove un tipo ha grafie da unire.

La domanda "sono lo stesso pezzo?" di Da confermare ha il suo file: `test_review_lookalike.py`.

L'archivio e' quello sintetico: le camere mono non portano `BAYERPAT`, quindi il loro colore i
file non lo dicono, e la Canon a colori si'.
"""

import typing

import pytest

from astrolog.clock import now_iso
from astrolog.db.connect import connect
from astrolog.spine import declarations as decl
from astrolog.vocab.header_value import normalize_header_value
from conftest import apply, by_name, correct, gear, review


def test_the_colour_on_the_card_redoes_the_poses_only_when_it_changes_something(client):
    """ "Mono" su una camera che l'app tratta gia' da mono non sposta nessuna posa: rimetterle in
    coda e' lavoro che nasce morto. Misurato dall'auditor sull'archivio vero (15/9/2026): 432 pose
    rimesse in coda e **0** cambiate, 6.558 e 0 ridicendo mono all'altra camera. "A colori" invece
    cambia il filtro di quelle pose, e li' il giro serve."""
    mono = by_name(gear(client)["instruments"], "ATR2600M(USB2.0)")
    assert correct(client, mono["id"], camera_type="mono").json()["requeued"] == 0
    assert correct(client, mono["id"], camera_type="color").json()["requeued"] > 0


def test_answering_no_filter_writes_mono_on_the_card(client):
    """ "Nessun filtro" su una camera di cui i file non dicono il colore scrive mono sulla scheda
    (`unfiltered.declare`): e' la stessa risposta, e la scheda la mostra."""
    pezzi = {i["name"]: i for i in gear(client)["instruments"]}
    chiedono = [g["key"] for g in review(client)["unfiltered"]]
    camera = next(c for c in chiedono if pezzi[c]["camera_type"] is None)

    apply(client, unfiltered=[{"key": camera, "answer": "no_filter"}])

    assert by_name(gear(client)["instruments"], camera)["camera_type"] == "mono"


def test_renaming_a_piece_keeps_the_name_of_its_rig(client):
    """Il nome di un corredo sta sotto la chiave (ottica, camera, focale): rinominare la camera
    cambia la chiave, e senza portarsi dietro il nome il corredo tornava senza. La rinomina e il
    nome del corredo stanno a un clic l'uno dall'altro nella stessa pagina (auditor, 15/9/2026)."""
    page = gear(client)
    corredo = next(r for r in page["rigs"] if r["camera"] == "ATR2600M(USB2.0)")
    camera = by_name(page["instruments"], "ATR2600M(USB2.0)")
    _nomina(client, corredo["id"], "Principale")
    correct(client, camera["id"], name="ATR 2600M USB")
    dopo = next(r for r in gear(client)["rigs"] if r["camera"] == "ATR 2600M USB")
    assert dopo["name"] == "Principale"


def test_the_card_asks_only_what_the_app_uses(client):
    """Ottica: apertura e focale. Camera: colore e pixel. Montatura: quanto regge. Su tutti marca,
    modello, peso e nota. Il rapporto focale, il lato del sensore e la scala non ci sono mai: si
    derivano."""
    schede = gear(client)["cards"]
    comuni = {"brand", "model", "weight_kg", "notes"}
    assert set(schede["optics"]) == comuni | {"aperture_mm", "focal_mm"}
    assert set(schede["camera"]) == comuni | {"camera_type", "pixel_size_um"}
    assert set(schede["mount"]) == comuni | {"payload_kg"}


def test_every_field_of_the_card_is_one_the_answer_accepts():
    """La scheda si legge da un elenco e si scrive con un altro (`InstrumentCorrection`): un campo
    chiesto a schermo che la risposta non accetta verrebbe scartato in silenzio."""
    from astrolog.api.instrument_answer import CARD
    from astrolog.api.models_gear import InstrumentCorrection
    from astrolog.api.models_review import CardField

    mostrati = set(typing.get_args(CardField))
    assert mostrati <= set(InstrumentCorrection.model_fields)
    assert mostrati == {f for campi in CARD.values() for f in campi}


def test_a_piece_is_merged_only_into_one_of_its_kind(client):
    pezzi = gear(client)["instruments"]
    atr = by_name(pezzi, "ATR2600M")
    tenuta = by_name(pezzi, "ATR2600M(USB2.0)")
    assert tenuta["id"] in atr["mergeable_into"]
    assert atr["id"] not in atr["mergeable_into"]
    tipi = {p["id"]: p["kind"] for p in pezzi}
    assert {tipi[i] for i in atr["mergeable_into"]} == {"camera"}


def test_a_merge_into_a_piece_that_is_gone_is_refused_by_name(client):
    """La pagina vecchia: il pezzo in cui unire non c'e' piu' (un'altra scheda l'ha assorbito).
    Il rifiuto e' `not_found`, che la pagina dice per nome -- non un 500 che non dice niente.
    Senza questa prova la guardia di `gear.merge_instrument` si poteva rompere in silenzio: l'ha
    trovato la mutazione del cancello, girando un `or` in `and`."""
    atr = by_name(gear(client)["instruments"], "ATR2600M")
    r = correct(client, atr["id"], merge_into=99999)
    assert (r.status_code, r.json()["detail"]["code"]) == (404, "not_found")


def test_two_spellings_of_a_wheel_can_really_be_joined(client):
    """Offrire un'unione che poi **schianta** e' peggio che non offrirla. Ruota, focheggiatore e
    camera di guida stanno **sulla posa**, non sul corredo: staccando i soli corredi la riga
    assorbita non si cancella -- la chiave esterna la trattiene -- e la scrittura va a rotoli.

    Qui si prova il gesto intero, dalla rotta: si uniscono, la riga sparisce, le pose restano e
    tornano in coda perche' `normalize` le riagganci alla grafia tenuta."""
    with connect(client.app.state.db_path) as conn:
        altra = conn.execute(
            "INSERT INTO instruments(kind, name, detected, created_at)"
            " VALUES('filter_wheel', 'ToupTek EFW', 1, ?)",
            (now_iso(),),
        ).lastrowid
        # una posa il cui header non nomina ruote: la corsa dopo l'unione non la riaggancia
        posa = conn.execute(
            "SELECT id FROM frames WHERE filter_wheel_raw IS NULL ORDER BY id LIMIT 1"
        ).fetchone()["id"]
        conn.execute("UPDATE frames SET filter_wheel_id = ? WHERE id = ?", (altra, posa))
    tenuta = by_name(gear(client)["instruments"], "ASCOM ToupTek FilterWheel")

    r = correct(client, altra, merge_into=tenuta["id"])

    assert r.status_code == 200, r.text
    with connect(client.app.state.db_path) as conn:
        assert (
            conn.execute("SELECT COUNT(*) FROM instruments WHERE id = ?", (altra,)).fetchone()[0]
            == 0
        )
        riga = conn.execute("SELECT filter_wheel_id FROM frames WHERE id = ?", (posa,)).fetchone()
        assert riga["filter_wheel_id"] is None  # staccata, non portata via con la riga


def test_renaming_a_guide_camera_does_not_touch_a_rig_named_like_it(client):
    """La chiave di un corredo e' `ottica|camera|focale`, e porta i **nomi**. Seguire una rinomina
    guardando i soli nomi -- come si faceva -- riscriveva quella chiave anche quando a cambiare era
    una **camera di guida** che si chiama come la camera principale -- e i `GUIDECAM` degli header
    veri portano nomi della stessa famiglia. Il nome che avevi dato al corredo spariva."""
    with connect(client.app.state.db_path) as conn:
        camera = conn.execute(
            "SELECT name FROM instruments WHERE kind = 'camera' LIMIT 1"
        ).fetchone()["name"]
        guida = conn.execute(
            "INSERT INTO instruments(kind, name, detected, created_at)"
            " VALUES('guide_camera', ?, 1, ?)",
            (camera, now_iso()),
        ).lastrowid
    corredo = next(r for r in gear(client)["rigs"] if r["camera"] == camera)
    _nomina(client, corredo["id"], "Il grande")

    correct(client, guida, name="La mia guida")

    dopo = next(r for r in gear(client)["rigs"] if r["id"] == corredo["id"])
    assert dopo["name"] == "Il grande"


def test_merging_a_guide_camera_does_not_touch_a_rig_named_like_it(client):
    """La stessa cieca della rinomina, dall'altra porta: **unire** due camere di guida non deve
    riscrivere la chiave di un corredo che porta quel nome sulla camera principale. E' lo stesso
    `follow_rename`, chiamato dall'unione invece che dalla scheda."""
    with connect(client.app.state.db_path) as conn:
        camera = conn.execute(
            "SELECT name FROM instruments WHERE kind = 'camera' LIMIT 1"
        ).fetchone()["name"]
        omonima = conn.execute(
            "INSERT INTO instruments(kind, name, detected, created_at)"
            " VALUES('guide_camera', ?, 1, ?)",
            (camera, now_iso()),
        ).lastrowid
        conn.execute(
            "INSERT INTO instruments(kind, name, detected, created_at)"
            " VALUES('guide_camera', 'La mia guida', 1, ?)",
            (now_iso(),),
        )
    corredo = next(r for r in gear(client)["rigs"] if r["camera"] == camera)
    _nomina(client, corredo["id"], "Il grande")
    tenuta = by_name(gear(client)["instruments"], "La mia guida")

    correct(client, omonima, merge_into=tenuta["id"])

    dopo = next(r for r in gear(client)["rigs"] if r["id"] == corredo["id"])
    assert dopo["name"] == "Il grande"


def test_a_second_rename_carries_the_spelling_learned_by_the_first(client):
    """Una rinomina impara la grafia di un attimo prima, e basta: rinominando **di nuovo**, la
    regola vecchia continuava a portare al nome di mezzo, che non e' piu' di nessuno. La prima
    notte nuova con la grafia originale faceva rinascere quel pezzo -- senza scheda, senza
    risposte, con le ore spartite fra due righe -- e nessun test si rompeva."""
    camera = by_name(gear(client)["instruments"], "ATR2600M(USB2.0)")
    correct(client, camera["id"], name="ATR 2600M USB")

    correct(client, camera["id"], name="La principale")

    with connect(client.app.state.db_path) as conn:
        # la grafia che sta negli header, quella che una posa nuova porterebbe
        assert decl.instrument_name(conn, "camera", "ATR2600M(USB2.0)") == "La principale"


def test_renaming_a_piece_carries_the_spellings_it_absorbed(client):
    """Stessa catena, con in mezzo un'**unione**: la grafia assorbita punta al pezzo tenuto, e
    rinominare quel pezzo deve portarsela dietro. Altrimenti unire due grafie e poi dare un nome
    al risultato -- due clic nella stessa pagina -- rimette in piedi la riga appena assorbita."""
    pezzi = gear(client)["instruments"]
    assorbita, tenuta = by_name(pezzi, "ATR2600M"), by_name(pezzi, "ATR2600M(USB2.0)")
    correct(client, assorbita["id"], merge_into=tenuta["id"])

    correct(client, tenuta["id"], name="La principale")

    with connect(client.app.state.db_path) as conn:
        assert decl.instrument_name(conn, "camera", "ATR2600M") == "La principale"


def test_a_kind_without_spellings_offers_no_merge(client):
    """Un riduttore non ha grafie da unire (`ALIAS_KINDS`): offrirlo farebbe tornare un rifiuto."""
    with connect(client.app.state.db_path) as conn:
        for nome in ("Riduttore 0.8x", "Riduttore 0,8"):
            conn.execute(
                "INSERT INTO instruments(kind, name, detected, created_at)"
                " VALUES('reducer', ?, 0, ?)",
                (nome, now_iso()),
            )
    assert by_name(gear(client)["instruments"], "Riduttore 0.8x")["mergeable_into"] == []


def test_every_piece_the_files_name_is_listed_with_its_poses(client):
    """**Sei generi**, non tre: oltre a ottica e camera ci sono le montature (cio' che l'ASIAIR
    scrive in TELESCOP) e i tre pezzi che i programmi nominano sulla singola posa -- ruota,
    focheggiatore e camera di guida. Otto pose e non nove: la copia riscritta non e' un'altra
    posa."""
    pezzi = gear(client)["instruments"]
    kinds = {i["kind"] for i in pezzi}
    assert kinds == {"optics", "camera", "mount", "filter_wheel", "focuser", "guide_camera"}
    assert by_name(pezzi, "Askar 103Apo")["frames"] == 8
    assert by_name(pezzi, "ASCOM ToupTek FilterWheel")["frames"] == 8
    assert by_name(pezzi, "ASCOM ToupTek AAF")["frames"] == 8
    assert by_name(pezzi, "ZWO ASI120MM-S")["frames"] == 3
    assert by_name(pezzi, "Canon EOS 700D")["camera_type"] == "color"


def test_a_card_written_makes_the_piece_yours(client):
    """Una scheda compilata si legge com'e' scritta, e da quel momento il pezzo l'ha detto
    l'utente, non la spina."""
    askar = by_name(gear(client)["instruments"], "Askar 103Apo")
    scheda = {"brand": "Askar", "aperture_mm": 103.0, "weight_kg": 4.6, "notes": "quello di casa"}
    assert correct(client, askar["id"], **scheda).status_code == 200

    dopo = by_name(gear(client)["instruments"], "Askar 103Apo")
    assert (dopo["brand"], dopo["aperture_mm"], dopo["weight_kg"]) == ("Askar", 103.0, 4.6)
    assert dopo["detected"] is False


def test_the_card_shows_what_i_wrote_over_what_the_files_say(client):
    """Il pixel scritto sulla scheda si mostra al posto di quello letto dai file, ma non lo
    cancella: il rilevato resta nella sua colonna, e un ricalcolo non tocca la scheda."""
    atr = by_name(gear(client)["instruments"], "ATR2600M(USB2.0)")
    assert atr["pixel_size_um"] == 3.76
    correct(client, atr["id"], pixel_size_um=3.8)
    assert by_name(gear(client)["instruments"], "ATR2600M(USB2.0)")["pixel_size_um"] == 3.8
    with connect(client.app.state.db_path) as conn:
        riga = conn.execute("SELECT pixel_size_um FROM instruments WHERE id = ?", (atr["id"],))
        assert riga.fetchone()[0] == 3.76


MISURE = ("pixel_size_um", "aperture_mm", "focal_mm", "reducer_factor", "weight_kg",
          "payload_kg", "backfocus_mm")  # fmt: skip


def test_every_measure_of_the_card_is_in_the_guard():
    """L'elenco qui sopra e' scritto a mano, e una misura aggiunta domani alla scheda senza
    `gt=0` passerebbe muta. Qui si confronta con i campi veri del modello: chi ne aggiunge una
    trova questo test rosso, e deve decidere se e' una misura (e allora vale la regola) o no."""
    from astrolog.api.models_gear import InstrumentCorrection

    reali = {
        nome
        for nome, campo in InstrumentCorrection.model_fields.items()
        if float in getattr(campo.annotation, "__args__", ())
    }
    assert reali == set(MISURE), "una misura nuova nella scheda: vale anche per lei il gt=0?"


@pytest.mark.parametrize("misura", MISURE)
def test_a_measure_of_the_card_is_never_zero(client, misura):
    """ "Ignota, mai inventata" vale per **tutte** le misure della scheda, non solo per la focale
    che la risposta sulla cartella gia' protegge: uno zero non e' una misura, e' un vuoto scritto
    male. Entrato in scheda, chi ne deriva lo scarta in silenzio -- una focale 0 fa sparire la
    scala -- e nessuno saprebbe piu' distinguerlo da "non lo so"."""
    pezzo = by_name(gear(client)["instruments"], "Askar 103Apo")
    assert correct(client, pezzo["id"], **{misura: 0.0}).status_code == 422


def test_a_filter_wheel_with_no_slots_is_refused(client):
    """Gli alloggiamenti sono un conto, non una misura: zero filtri in una ruota non e' "non lo
    so", e' una ruota che non esiste."""
    pezzo = by_name(gear(client)["instruments"], "ASCOM ToupTek FilterWheel")
    assert correct(client, pezzo["id"], slots=0).status_code == 422


def test_merging_two_spellings_moves_the_poses_and_learns_the_rule(client):
    """Due grafie della stessa camera diventano un pezzo solo: si scrive la regola, la riga
    assorbita sparisce, e le pose che la usavano tornano al pezzo giusto da sole."""
    pezzi = gear(client)["instruments"]
    tenuta = by_name(pezzi, "ATR2600M(USB2.0)")
    assorbita = by_name(pezzi, "ATR2600M")
    assert assorbita["frames"] == 1

    out = correct(client, assorbita["id"], merge_into=tenuta["id"]).json()
    assert out["requeued"] >= 1 and out["run_started"] is True

    dopo = gear(client)["instruments"]
    assert "ATR2600M" not in [i["name"] for i in dopo]
    assert by_name(dopo, "ATR2600M(USB2.0)")["frames"] == 8  # 7 + quella unita
    with connect(client.app.state.db_path) as conn:
        regola = conn.execute(
            "SELECT target_key FROM header_aliases WHERE kind = 'camera' AND header_value = ?",
            ("atr2600m",),
        ).fetchone()
        assert regola["target_key"] == "ATR2600M(USB2.0)"
        assert conn.execute("SELECT COUNT(*) FROM frames WHERE rig_id IS NULL").fetchone()[0] == 0


def test_renaming_a_mount_learns_its_spelling(client):
    """Rinominare una montatura scrive la regola sulla grafia vecchia, come per ottiche e camere.
    Senza, alla scansione dopo la montatura rinasce col nome dell'header e i pezzi diventano tre."""
    montatura = by_name(gear(client)["instruments"], "EQMod Mount")
    correct(client, montatura["id"], name="La mia montatura")
    with connect(client.app.state.db_path) as conn:
        regola = conn.execute(
            "SELECT target_key FROM header_aliases WHERE kind = 'mount' AND header_value = ?",
            (normalize_header_value("EQMod Mount"),),
        ).fetchone()
    assert regola is not None, "la grafia vecchia non e' stata imparata"
    assert regola["target_key"] == "La mia montatura"


def test_two_mount_spellings_merge_like_a_camera(client):
    """Anche due grafie di montatura si uniscono, come quelle di una camera. Il banco porta due
    montature vere, e qui si prova il **meccanismo**: quale montatura sia davvero lo dice
    l'utente."""
    pezzi = gear(client)["instruments"]
    tenuta, assorbita = by_name(pezzi, "EQMod Mount"), by_name(pezzi, "ZWO AM3")
    assert correct(client, assorbita["id"], merge_into=tenuta["id"]).status_code == 200
    assert "ZWO AM3" not in [i["name"] for i in gear(client)["instruments"]]


def test_a_piece_is_not_merged_with_itself(client):
    """Unire un pezzo con se stesso lo cancellerebbe insieme ai suoi corredi: si rifiuta, e
    non si scrive niente."""
    askar = by_name(gear(client)["instruments"], "Askar 103Apo")
    r = correct(client, askar["id"], merge_into=askar["id"])
    assert r.status_code == 422 and r.json()["detail"]["code"] == "merge_refused"
    dopo = gear(client)
    assert by_name(dopo["instruments"], "Askar 103Apo")["frames"] == 8
    assert len(dopo["rigs"]) == 5


def test_the_name_of_a_rig_survives_a_merge(client):
    """Il nome del corredo sta fra le dichiarazioni, non nella riga rilevata: un'unione che
    cancella quel corredo non porta via il nome, che torna quando il corredo si rifa'."""
    rig = next(r for r in gear(client)["rigs"] if r["camera"] == "ATR2600M")
    _nomina(client, rig["id"], "Il piccolo")
    nominato = next(r for r in gear(client)["rigs"] if r["camera"] == "ATR2600M")
    assert nominato["name"] == "Il piccolo"

    pezzi = gear(client)["instruments"]
    assorbita, tenuta = by_name(pezzi, "ATR2600M"), by_name(pezzi, "ATR2600M(USB2.0)")
    correct(client, assorbita["id"], merge_into=tenuta["id"])
    with connect(client.app.state.db_path) as conn:
        riga = conn.execute(
            "SELECT value FROM declarations WHERE entity_type = 'rig' AND field = 'name'"
        ).fetchone()
        assert riga["value"] == "Il piccolo"  # il nome non e' sparito col corredo


def _nomina(client, rig_id, nome):
    r = client.patch(f"/api/v1/gear/rigs/{rig_id}", json={"name": nome})
    assert r.status_code == 200, r.text
