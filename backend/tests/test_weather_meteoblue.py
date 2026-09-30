"""Il seeing Meteoblue con la chiave dell'utente: letto ora per ora, chiesto con la cadenza che il
tetto dei crediti concede, e la chiave che non esce mai intera.

Le risposte finte hanno la forma di quelle vere, misurate il 26/9/2026 con una chiave gratuita.
"""

import io
import json
import urllib.error
from datetime import datetime, timedelta

import pytest

from astrolog.db import config
from astrolog.weather import meteoblue, sky
from test_weather_forecast import ADESSO, SITO, db, righe  # noqa: F401 - `db` e' una fixture
from test_weather_sky import Instradato, aria, settetimer

CHIAVE = "segretissima1234"


def seeing(inizio="2026-09-25 00:00", ore=169, valore=0.9):
    t0 = datetime.fromisoformat(inizio)
    return {
        "metadata": {"utc_timeoffset": 0.0},
        "units": {"time": "YYYY-MM-DD hh:mm", "windspeed": "ms-1"},
        "data_1h": {
            "time": [(t0 + timedelta(hours=i)).strftime("%Y-%m-%d %H:%M") for i in range(ore)],
            "seeing_arcsec": [valore] * ore,
            "jetstream": [17.0] * ore,
        },
    }


def rifiuto(url):
    return urllib.error.HTTPError(url, 403, "Forbidden", {}, io.BytesIO(b"no"))  # type: ignore[arg-type]


def servizi(**cambi):
    return Instradato(**{
        "7timer": settetimer(), "air-quality": aria(), "packages/seeing-1h": seeing(), **cambi
    })  # fmt: skip


def con_la_chiave(conn):
    config.write(conn, "meteoblue_key", CHIAVE)


def chiesti_a_meteoblue(finto):
    return [u for u in finto.chiesti if "seeing-1h" in u]


def test_the_seeing_is_read_hour_by_hour_in_utc_as_a_single_value():
    tempi, serie = meteoblue.parse(seeing(ore=2, valore=1.24))
    assert [t.isoformat() for t in tempi] == [
        "2026-09-25T00:00:00+00:00",
        "2026-09-25T01:00:00+00:00",
    ]
    assert serie == {"seeing_from": [1.24, 1.24], "seeing_to": [1.24, 1.24]}


def test_the_offset_the_service_declares_is_applied():
    risposta = seeing(ore=1)
    risposta["metadata"]["utc_timeoffset"] = 2.0
    tempi, _ = meteoblue.parse(risposta)
    assert tempi[0].isoformat() == "2026-09-24T22:00:00+00:00"


@pytest.mark.parametrize(
    "storta",
    [
        "<html/>",
        {},
        {"data_1h": {}},
        {"data_1h": {"time": ["ieri"]}},
        {"data_1h": {"time": ["2026-09-25 00:00"], "seeing_arcsec": []}},
    ],
)
def test_an_answer_that_is_not_a_seeing_forecast_is_refused(storta):
    with pytest.raises(meteoblue.BadAnswerError):
        meteoblue.parse(storta)


def test_without_a_key_meteoblue_is_never_asked(db):  # noqa: F811
    finto = servizi()
    sky.refresh(db, SITO, fetch=finto, now=ADESSO)
    assert chiesti_a_meteoblue(finto) == []
    assert "meteoblue" not in {r["source"] for r in righe(db)}


def test_with_a_key_the_seeing_is_written_and_not_asked_again_before_its_time(db):  # noqa: F811
    """Il tetto gratuito regge circa tre chiamate al giorno: si chiede al massimo ogni dodici ore,
    e il conto sopravvive a un riavvio perche' l'ultimo tentativo e' scritto."""
    con_la_chiave(db)
    finto = servizi()
    sky.refresh(db, SITO, fetch=finto, now=ADESSO)
    assert len(chiesti_a_meteoblue(finto)) == 1
    assert "meteoblue" in {r["source"] for r in righe(db)}
    sky.refresh(db, SITO, fetch=finto, now=ADESSO + timedelta(hours=11, minutes=59))
    assert len(chiesti_a_meteoblue(finto)) == 1
    sky.refresh(db, SITO, fetch=finto, now=ADESSO + timedelta(hours=12))
    assert len(chiesti_a_meteoblue(finto)) == 2


def test_meteoblue_is_asked_at_most_twice_a_day_and_the_credits_would_allow_more():
    """Il minimo di dodici ore decide: il tetto dei crediti ne reggerebbe di piu'."""
    assert meteoblue.MIN_GAP_H == 12
    assert meteoblue.CALLS_PER_YEAR > 2 * 365  # il tetto non e' cio' che frena


def test_a_key_the_service_refuses_drops_its_seeing_and_says_why(db):  # noqa: F811
    """Una chiave rifiutata non vale piu': il suo seeing vecchio non resta a fingere di essere
    quello di stanotte, e il seeing torna a 7Timer."""
    con_la_chiave(db)
    sky.refresh(db, SITO, fetch=servizi(), now=ADESSO)
    rifiutata = servizi(**{"packages/seeing-1h": rifiuto("https://x?apikey=" + CHIAVE)})
    sky.refresh(db, SITO, fetch=rifiutata, now=ADESSO + timedelta(hours=12))
    assert "meteoblue" not in {r["source"] for r in righe(db)}
    assert "7timer" in {r["source"] for r in righe(db)}
    assert meteoblue.last_attempt(db, SITO["id"])["status"] == "refused"


def test_a_silent_service_keeps_the_seeing_it_gave_last_time(db):  # noqa: F811
    """Un silenzio non dice niente della chiave: resta il seeing di prima."""
    con_la_chiave(db)
    sky.refresh(db, SITO, fetch=servizi(), now=ADESSO)
    prima = [tuple(r) for r in righe(db) if r["source"] == "meteoblue"]
    muto = servizi(**{"packages/seeing-1h": TimeoutError()})
    sky.refresh(db, SITO, fetch=muto, now=ADESSO + timedelta(hours=12))
    assert [tuple(r) for r in righe(db) if r["source"] == "meteoblue"] == prima
    assert meteoblue.last_attempt(db, SITO["id"])["status"] == "unreachable"


def test_the_key_never_reaches_the_log(db, caplog):  # noqa: F811
    caplog.set_level("DEBUG")
    con_la_chiave(db)
    sky.refresh(db, SITO, fetch=servizi(**{"packages/seeing-1h": TimeoutError(CHIAVE)}), now=ADESSO)
    sky.refresh(
        db,
        SITO,
        fetch=servizi(**{"packages/seeing-1h": rifiuto(CHIAVE)}),
        now=ADESSO + timedelta(hours=12),
    )
    assert caplog.records
    assert CHIAVE not in caplog.text
    assert all(
        CHIAVE not in json.dumps(getattr(r, "__dict__", {}), default=str) for r in caplog.records
    )


def test_the_key_is_tried_on_the_account_before_it_is_kept():
    conto = {"items": [{"request_type": "seeing-1h", "request_credits": 8000}], "metadata": {}}
    assert meteoblue.check_key(CHIAVE, fetch=Instradato(**{"account/usage": conto})) == "ok"
    assert (
        meteoblue.check_key(CHIAVE, fetch=Instradato(**{"account/usage": rifiuto("x")}))
        == "refused"
    )
    assert (
        meteoblue.check_key(CHIAVE, fetch=Instradato(**{"account/usage": {"x": 1}})) == "bad_answer"
    )
    assert (
        meteoblue.check_key(CHIAVE, fetch=Instradato(**{"account/usage": TimeoutError()}))
        == "unreachable"
    )


def test_the_seeing_is_asked_for_seven_days_in_utc():
    """Sette notti, come dicono il primo avvio e la guida; e in UTC, come ogni altra fonte."""
    indirizzo = meteoblue.url(45.87, 11.51, CHIAVE)
    assert "forecastDays=7" in indirizzo
    assert "tz=UTC" in indirizzo


def guasto(codice):
    return urllib.error.HTTPError("x", codice, "x", {}, io.BytesIO(b""))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("codice", "esito"),
    [
        (400, "refused"),
        (401, "refused"),
        (403, "refused"),
        (429, "refused"),
        (500, "unreachable"),
        (503, "unreachable"),
    ],
)
def test_only_a_refusal_of_the_key_is_a_refusal_and_a_broken_service_is_not(codice, esito):
    """Un 503 e' il servizio giu', non la chiave sbagliata: dirlo rifiuto manderebbe a cambiare
    una chiave buona."""
    assert (
        meteoblue.check_key(CHIAVE, fetch=Instradato(**{"account/usage": guasto(codice)})) == esito
    )


def test_a_short_key_never_comes_out_whole():
    assert config.hint("abcd") == "..."
    assert config.hint("abcde") == "...bcde"
    assert config.hint(None) is None
