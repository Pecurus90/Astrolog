"""Eliminare un pezzo dalla pagina Attrezzatura (Marco, 21/10/2026; tavola v82): **solo un pezzo
senza frame**. Uno che ne tiene si rifiuta e la pagina dice chi lo usa: nessuna ora si perde. Un
pezzo scelto in un setup ne esce; l'ottica o la camera di un setup non escono, il setup e' loro.
"""

from unittest import mock

from astrolog.api import work
from test_api_gear_write import archivio, cercato, crea, pezzo, scegli, vuoto  # noqa: F401


def elimina(client, piece_id):
    return client.delete(f"/api/v1/gear/instruments/{piece_id}")


def elimina_filtro(client, filter_id):
    return client.delete(f"/api/v1/gear/filters/{filter_id}")


def filtro_nella_pagina(client, nome):
    pagina = client.get("/api/v1/gear").json()
    return next((f for f in pagina["filters"] if f["name"] == nome), None)


def test_a_piece_without_frames_goes_away(archivio):  # noqa: F811
    nato = crea(archivio, kind="focuser", name="EAF").json()["id"]

    risposta = elimina(archivio, nato)

    assert risposta.status_code == 204, risposta.text
    assert cercato(archivio, "focuser", "EAF") is None


def test_a_piece_with_frames_is_refused_and_says_who_uses_it(archivio):  # noqa: F811
    """La regola e' la stessa per i pezzi che le pose portano da se' (l'ottica, via il setup):
    il rifiuto dice quanti frame e di quali setup, perche' la pagina lo scriva."""
    ottica = pezzo(archivio, "optics", "TS 130 APO")
    rig = archivio.get("/api/v1/gear").json()["rigs"][0]["id"]

    risposta = elimina(archivio, ottica["id"])

    assert risposta.status_code == 409, risposta.text
    assert risposta.json()["detail"] == {"code": "in_use", "frames": 2, "rigs": [rig]}
    assert cercato(archivio, "optics", "TS 130 APO") is not None


def test_a_spacer_on_a_rig_with_frames_is_refused(archivio):  # noqa: F811
    """Nessun frame porta un distanziale: le sue ore sono quelle dei setup che lo montano, e
    tolto si perderebbero (visto dal revisore, 12/11)."""
    rig = archivio.get("/api/v1/gear").json()["rigs"][0]["id"]
    distanziale = crea(archivio, kind="spacer", name="D10").json()["id"]
    archivio.put(f"/api/v1/gear/rigs/{rig}/spacers", json={"piece_ids": [distanziale]})

    risposta = elimina(archivio, distanziale)

    assert risposta.status_code == 409, risposta.text
    assert risposta.json()["detail"] == {"code": "in_use", "frames": 2, "rigs": [rig]}


def test_the_page_knows_before_asking_which_rigs_hold_a_piece(archivio):  # noqa: F811
    """«Esce anche da {setup}» e «Lo usano N frame di {setup}» si scrivono prima del gesto:
    la pagina legge da ogni pezzo i setup che lo tengono, coi frame e se l'hai scelto tu."""
    rig = archivio.get("/api/v1/gear").json()["rigs"][0]["id"]
    montatura = crea(archivio, kind="mount", name="EQ6-R").json()["id"]
    with mock.patch.object(work, "after", return_value=True):
        scegli(archivio, rig, "mount", montatura)

    assert pezzo(archivio, "mount", "EQ6-R")["in_rigs"] == [
        {"rig_id": rig, "frames": 0, "chosen": True}
    ]
    assert pezzo(archivio, "optics", "TS 130 APO")["in_rigs"] == [
        {"rig_id": rig, "frames": 2, "chosen": False}
    ]


def test_a_chosen_piece_without_frames_leaves_the_rig(archivio):  # noqa: F811
    rig = archivio.get("/api/v1/gear").json()["rigs"][0]["id"]
    montatura = crea(archivio, kind="mount", name="EQ6-R").json()["id"]
    with mock.patch.object(work, "after", return_value=True):
        scegli(archivio, rig, "mount", montatura)

    assert elimina(archivio, montatura).status_code == 204

    parti = archivio.get("/api/v1/gear").json()["rigs"][0]["parts"]
    assert not any(p["kind"] == "mount" for p in parti)
    # rinato con lo stesso nome, non torna scelto: la scelta era del pezzo eliminato
    di_nuovo = crea(archivio, kind="mount", name="EQ6-R").json()["id"]
    assert pezzo(archivio, "mount", "EQ6-R")["id"] == di_nuovo
    assert pezzo(archivio, "mount", "EQ6-R")["in_rigs"] == []


def test_the_optics_of_a_rig_without_frames_is_refused(archivio):  # noqa: F811
    """Un setup scritto a mano e mai usato e' fatto della sua ottica e della sua camera:
    togliergliele lo lascerebbe a meta'. Rifiuto col suo codice, nessun frame in gioco."""
    camera = crea(archivio, kind="camera", name="ASI533MC").json()["id"]
    ottica = crea(archivio, kind="optics", name="RedCat 51").json()["id"]
    nuovo = archivio.post(
        "/api/v1/gear/rigs", json={"optics_id": ottica, "camera_id": camera, "focal_mm": 250}
    ).json()["id"]

    risposta = elimina(archivio, camera)

    assert risposta.status_code == 409, risposta.text
    assert risposta.json()["detail"] == {"code": "in_rig", "rigs": [nuovo]}


def test_a_declared_card_goes_with_the_piece(archivio):  # noqa: F811
    """Rinato con lo stesso nome, un pezzo non eredita la scheda di quello eliminato."""
    nato = crea(archivio, kind="focuser", name="EAF", step_um=1.5).json()["id"]
    elimina(archivio, nato)

    crea(archivio, kind="focuser", name="EAF")

    assert pezzo(archivio, "focuser", "EAF")["step_um"] is None


def test_a_filter_without_frames_goes_away_one_with_frames_stays(archivio):  # noqa: F811
    nuovo = archivio.post(
        "/api/v1/gear/filters", json={"name": "Antlia 3nm", "bands": [{"band": "HA"}]}
    ).json()["id"]
    ha = filtro_nella_pagina(archivio, "Ha")
    assert ha is not None

    assert elimina_filtro(archivio, nuovo).status_code == 204
    assert filtro_nella_pagina(archivio, "Antlia 3nm") is None
    rifiuto = elimina_filtro(archivio, ha["id"])
    assert rifiuto.status_code == 409
    assert rifiuto.json()["detail"]["code"] == "in_use"
    assert rifiuto.json()["detail"]["frames"] == 1


def test_nothing_goes_away_while_the_archive_is_being_read(archivio):  # noqa: F811
    nato = crea(archivio, kind="focuser", name="EAF").json()["id"]
    with mock.patch.object(archivio.app.state.worker, "is_running", return_value=True):
        risposta = elimina(archivio, nato)

    assert (risposta.status_code, risposta.json()["detail"]["code"]) == (409, "worker_busy")
    assert cercato(archivio, "focuser", "EAF") is not None


def test_a_piece_that_is_not_there_is_not_found(vuoto):  # noqa: F811
    assert elimina(vuoto, 9999).status_code == 404
    assert elimina_filtro(vuoto, 9999).status_code == 404
