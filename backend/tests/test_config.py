"""Le preferenze: chiavi chiuse, tipo per chiave, valori di fabbrica con la loro fonte."""

import pytest

from astrolog.db import config


def test_every_key_has_a_type_and_a_source():
    for key, (kind, value, why) in config.KEYS.items():
        assert kind in (str, int, float), key
        assert why, key
        assert value is None or isinstance(value, kind), key
    assert config.defaults()["language"] == "it"


def test_read_overlays_saved_values_with_the_key_type(conn):
    assert config.read(conn)["language"] == "it"
    config.write(conn, "language", "en")
    config.write(conn, "user_name", "2024")  # un nome che sembra un numero resta testo
    values = config.read(conn)
    assert (values["language"], values["user_name"]) == ("en", "2024")
    assert isinstance(values["user_name"], str)
    with pytest.raises(KeyError):
        config.write(conn, "chiave_inventata", 1)
    with pytest.raises(ValueError):
        config.write(conn, "user_name", 12)  # si respinge in scrittura
    config.write(conn, "user_name", None)
    assert config.read(conn)["user_name"] is None


def test_the_weather_model_is_one_of_those_the_service_offers(conn):
    """Di fabbrica il modello che il servizio sceglie per il posto; un nome fuori elenco si
    respinge in scrittura, invece di dare una pagina vuota in lettura."""
    assert config.read(conn)["weather_model"] == "best_match"
    config.write(conn, "weather_model", "icon_seamless")
    assert config.read(conn)["weather_model"] == "icon_seamless"
    with pytest.raises(ValueError):
        config.write(conn, "weather_model", "windy")
