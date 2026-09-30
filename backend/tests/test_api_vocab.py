"""I filtri in commercio, come li vede la pagina: la tendina da cui si dichiara un filtro.

L'elenco vive nel vocabolario (`vocab/filters.py`) e fino al 14/9/2026 non usciva da nessuna
rotta: il contratto della spina prometteva la tendina, lo schema prevedeva gia' `catalog_id`
("id del modello di catalogo, NULL se nome libero") e `FilterEdit` lo accettava -- mancava solo
l'uscita, quindi la tendina non era disegnabile.

Si prova qui e non in `test_settings.py` perche' e' un'altra cosa: quelle sono le preferenze di
chi usa l'app, questo e' un vocabolario che l'app si porta dentro e non cambia mai.
"""

from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.vocab import filters as vocab


def test_the_filter_models_come_out_whole(client_vuoto):
    """Tutti quelli che il vocabolario conosce, nessuno di meno: una tendina che ne mostra una
    parte fa scrivere a mano un filtro che l'app avrebbe saputo compilare."""
    r = client_vuoto.get("/api/v1/vocab/filter-models")
    assert r.status_code == 200, r.text
    usciti = r.json()["items"]
    assert len(usciti) == len(vocab.models())
    assert {m["id"] for m in usciti} == {m["id"] for m in vocab.models()}


def test_a_model_says_what_the_screen_shows_and_nothing_else(client_vuoto):
    """Marca, nome e banda: e' cio' che si legge in tendina. Gli **alias** restano dentro -- sono
    il modo in cui l'app riconosce una grafia nell'header, non una cosa da mostrare: a schermo
    sarebbero rumore, e in un'API sono una forma che poi qualcuno usa."""
    uno = client_vuoto.get("/api/v1/vocab/filter-models").json()["items"][0]
    assert sorted(uno) == ["brand", "id", "name", "passband"]


def test_the_order_is_the_one_you_search_in(client_vuoto):
    """L'ordine e' una decisione del backend -- `models()` dichiara di essere "l'ordine con cui si
    cerca in tendina" -- e deve arrivare intatto: se il frontend dovesse riordinare, quella
    promessa sarebbe scritta in un commento e due case direbbero due ordini."""
    usciti = [m["id"] for m in client_vuoto.get("/api/v1/vocab/filter-models").json()["items"]]
    assert usciti == [m["id"] for m in vocab.models()]


def test_it_does_not_need_the_archive(client_vuoto):
    """Un vocabolario non e' un dato dell'utente: si legge anche a mani vuote, appena installato,
    senza una posa in archivio."""
    assert client_vuoto.get("/api/v1/vocab/filter-models").json()["items"]


def test_it_does_not_open_the_database(tmp_path):
    """**Non apre il database**, e qui si dimostra invece di dichiararlo.

    La prova di sopra usa un archivio vero e vuoto: passerebbe anche se la rotta lo aprisse. Qui
    l'app punta a un file che **non esiste** -- aprirlo fallirebbe -- e la rotta risponde lo
    stesso. E' la ragione per cui un vocabolario si legge appena installati: e' impacchettato col
    programma, non e' roba dell'utente."""
    inesistente = tmp_path / "non-c-e" / "astrolog.db"
    with TestClient(create_app(inesistente), base_url="http://localhost") as c:
        r = c.get("/api/v1/vocab/filter-models")
    assert r.status_code == 200, r.text
    assert len(r.json()["items"]) == len(vocab.models())
