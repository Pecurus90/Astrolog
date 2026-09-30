"""Le preferenze, il timbro del primo avvio, e cio' che manca per fare le notti.

Il wizard e' una superficie e nascera' col frontend: qui si prova cio' che la superficie usa
-- i passi, un timbro, e un'app che a mani vuote funziona e dice cosa le manca.

test-tolto: test_wizard_three_steps_and_the_stamp -- rinominata: il primo avvio ha un passo in piu'
"""

import pytest

ASIAGO = {"name": "Asiago", "latitude": 45.8667, "longitude": 11.5167}


# tutte le prove di questo file sono al sito buio: nessun servizio risponde
pytestmark = pytest.mark.usefixtures("offline")


def settings(client_vuoto):
    r = client_vuoto.get("/api/v1/settings")
    assert r.status_code == 200, r.text
    return r.json()


def patch(client_vuoto, **values):
    r = client_vuoto.patch("/api/v1/settings", json={"values": values})
    assert r.status_code == 200, r.text
    return r.json()


def test_settings_user_name(client_vuoto):
    """Il nome resta scritto se lo si scrive, e se non lo si scrive non c'e' un ripiego:
    niente "Utente", niente nome del computer."""
    assert settings(client_vuoto)["values"]["user_name"] is None

    assert patch(client_vuoto, user_name="Marco")["values"]["user_name"] == "Marco"
    assert settings(client_vuoto)["values"]["user_name"] == "Marco"  # e resta scritto

    assert patch(client_vuoto, user_name=None)["values"]["user_name"] is None


def test_the_settings_come_with_their_factory_values(client_vuoto):
    values = settings(client_vuoto)["values"]
    assert values["language"] == "it"
    assert values["sky_service_key"] is None
    assert values["onboarding_done_at"] is None


def test_an_unknown_setting_or_a_wrong_type_is_refused(client_vuoto):
    """Le chiavi sono un elenco chiuso: si respinge qui, dove si puo' rispondere col motivo."""
    r = client_vuoto.patch("/api/v1/settings", json={"values": {"colore_preferito": "blu"}})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "unknown_setting"

    r = client_vuoto.patch("/api/v1/settings", json={"values": {"user_name": 7}})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "wrong_type"

    assert settings(client_vuoto)["values"]["user_name"] is None  # e non ha scritto niente


def test_a_refused_write_leaves_the_good_keys_alone(client_vuoto):
    """Una scrittura o passa intera o non passa: meta' preferenze scritte sarebbe peggio.

    Due modi di essere respinta, e il secondo e' quello che conta: la chiave sconosciuta si
    ferma prima di scrivere, il tipo sbagliato si scopre a scrittura gia' cominciata -- e li'
    la chiave buona che l'ha preceduta deve tornare indietro."""
    r = client_vuoto.patch("/api/v1/settings", json={"values": {"user_name": "Marco", "boh": "x"}})
    assert r.status_code == 422
    assert settings(client_vuoto)["values"]["user_name"] is None

    r = client_vuoto.patch("/api/v1/settings", json={"values": {"language": "en", "user_name": 7}})
    assert r.status_code == 422 and r.json()["detail"]["code"] == "wrong_type"
    assert settings(client_vuoto)["values"]["language"] == "it"  # la buona e' tornata indietro


def test_no_site_no_nights_and_it_says_so(client_vuoto):
    """A mani vuote l'app funziona -- cataloga e cerca -- ma le notti non nascono, e lo DICE
    con un motivo invece di inventarsi un luogo."""
    # si guarda il sito e non l'elenco intero: li' dentro finisce tutto cio' che manca, e
    # nella suite manca sempre anche il solver (`conftest.dentro_il_recinto`)
    assert "no_active_site" in settings(client_vuoto)["missing"]

    client_vuoto.post("/api/v1/sites", json=ASIAGO)
    assert "no_active_site" not in settings(client_vuoto)["missing"]


def test_sites_without_a_home_one_are_not_enough(client_vuoto):
    """Le notti nascono nel fuso del luogo di casa. Se si cancella proprio quello, restano dei
    luoghi ma nessuno e' di casa: l'app lo chiede invece di eleggerne uno da sola."""
    casa = client_vuoto.post("/api/v1/sites", json=ASIAGO).json()
    monte = client_vuoto.post(
        "/api/v1/sites", json={**ASIAGO, "name": "Monte Grappa", "longitude": 11.80}
    ).json()
    assert casa["is_default"] is True and monte["is_default"] is False

    client_vuoto.delete(f"/api/v1/sites/{casa['id']}")
    assert "no_active_site" in settings(client_vuoto)["missing"]

    client_vuoto.post(f"/api/v1/sites/{monte['id']}/default")
    assert "no_active_site" not in settings(client_vuoto)["missing"]


def test_wizard_steps_and_the_stamp(client_vuoto, tmp_path):
    """I passi -- come mi chiamo, da dove osservo, dove stanno i file, la chiave Meteoblue -- e poi
    il timbro.
    Il timbro e' una data scritta, non un'euristica: "sembra vuoto" tornerebbe vero mesi
    dopo, dopo un azzeramento, e il wizard ricomparirebbe da solo."""
    prima = settings(client_vuoto)
    assert prima["wizard_done"] is False and "no_active_site" in prima["missing"]

    patch(client_vuoto, user_name="Marco")
    assert client_vuoto.post("/api/v1/sites", json=ASIAGO).status_code == 201
    cartella = tmp_path / "archivio"
    cartella.mkdir()
    r = client_vuoto.post("/api/v1/folders", json={"root_path": str(cartella)})
    assert r.status_code == 201, r.text

    dopo = client_vuoto.post("/api/v1/settings/wizard-done")
    assert dopo.status_code == 200
    timbro = dopo.json()["values"]["onboarding_done_at"]
    assert timbro and dopo.json()["wizard_done"] is True

    # riaprirlo dalle Impostazioni non riscrive il timbro: la prima volta e' una sola
    assert (
        client_vuoto.post("/api/v1/settings/wizard-done").json()["values"]["onboarding_done_at"]
        == timbro
    )


def test_skipping_the_wizard_stamps_it_just_the_same(client_vuoto):
    """Chi lo salta non se lo ritrova domani: saltare e completare scrivono lo stesso timbro.
    E l'app resta usabile: dice solo che senza un luogo le notti non nascono."""
    assert client_vuoto.post("/api/v1/settings/wizard-done").status_code == 200
    stato = settings(client_vuoto)
    assert stato["wizard_done"] is True
    assert "no_active_site" in stato["missing"]
