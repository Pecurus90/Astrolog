"""La **notte della posa**: da mezzogiorno a mezzogiorno nel fuso del posto, scritta quando la
posa entra (`scan`), e letta da chi la chiedeva in UTC. Quando casa cambia fuso:
`test_home_nights.py`.

La regola sta in CLAUDE.md ("Le date portano il fuso"); il fuso viene dalle coordinate dell'header,
se ci sono, o dal sito di casa, altrimenti e' UTC. Una posa che non dice quando e' stata ripresa
prende la data del file (Marco, 27/9/2026).
"""

import os
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from astrolog.api.app import create_app
from astrolog.clock import local_iso
from astrolog.spine.solve_store import SOLVE_ORDER_KEY
from conftest import db, populate, review, write_fits

TOKYO = {"SITELAT": 35.68, "SITELONG": 139.69}


def _posa(path, **header):
    card = {"IMAGETYP": "Light Frame", "EXPTIME": 300.0, "FILTER": "L", "INSTRUME": "ZWO ASI294MC"}
    return write_fits(path, {**card, **header})


def _notti(client):
    """`{file: (notte, fuso)}` delle pose, come le ha scritte la scansione."""
    with db(client) as conn:
        righe = conn.execute(
            "SELECT p.rel_path, f.local_night, f.local_tz FROM frames f"
            " JOIN positions p ON p.frame_id = f.id"
        ).fetchall()
    return {r["rel_path"].split("/")[-1]: (r["local_night"], r["local_tz"]) for r in righe}


def _apri(db_path, root):
    populate(db_path, root)
    return TestClient(create_app(db_path), base_url="http://localhost")


def _sul_disco(path, quando):
    """Il file come se fosse stato scritto in quell'istante UTC."""
    istante = datetime.fromisoformat(quando).replace(tzinfo=UTC).timestamp()
    os.utime(path, (istante, istante))


def test_in_the_east_the_night_is_cut_at_local_noon(db_path, tmp_path):
    """**La regola.** A Tokyo le 11:30 e le 13:30 UTC sono le 20:30 e le 22:30 di una stessa sera,
    anche se in UTC stanno ai due lati di mezzogiorno. La stessa notte la legge il solver, che
    risolve una posa per oggetto e notte (`solve_store.SOLVE_ORDER_KEY`)."""
    root = tmp_path / "lib"
    _posa(root / "a.fits", **{"DATE-OBS": "2026-03-14T11:30:00", **TOKYO})
    _posa(root / "b.fits", **{"DATE-OBS": "2026-03-14T13:30:00", **TOKYO})

    with _apri(db_path, root) as c:
        notti = _notti(c)
        with db(c) as conn:
            chiavi = conn.execute(f"SELECT {SOLVE_ORDER_KEY} FROM frames").fetchall()  # noqa: S608

    assert notti == {
        "a.fits": ("2026-03-14", "Asia/Tokyo"),
        "b.fits": ("2026-03-14", "Asia/Tokyo"),
    }
    assert {k[0].split("|")[1] for k in chiavi} == {"2026-03-14"}


def test_without_coordinates_the_home_site_gives_the_zone(db_path, tmp_path):
    """Una posa che non dice dove e' stata ripresa prende il fuso del sito di casa."""
    from astrolog.db.connect import connect

    with connect(db_path) as conn:
        conn.execute(
            "INSERT INTO sites(name, latitude, longitude, timezone, is_default, created_at)"
            " VALUES('Casa', 35.68, 139.69, 'Asia/Tokyo', 1, '2026-01-01T00:00:00Z')"
        )
    root = tmp_path / "lib"
    _posa(root / "a.fits", **{"DATE-OBS": "2026-03-14T11:30:00"})

    with _apri(db_path, root) as c:
        assert _notti(c) == {"a.fits": ("2026-03-14", "Asia/Tokyo")}


def test_without_coordinates_and_home_the_night_is_in_utc(db_path, tmp_path):
    """Senza coordinate e senza casa l'unico fuso che si sa e' quello del file: UTC."""
    root = tmp_path / "lib"
    _posa(root / "a.fits", **{"DATE-OBS": "2026-03-14T11:30:00"})

    with _apri(db_path, root) as c:
        assert _notti(c) == {"a.fits": ("2026-03-13", None)}


def test_a_pose_without_a_date_takes_the_date_of_its_file(db_path, tmp_path):
    """Senza `DATE-OBS` la notte e' quella in cui il file e' stato scritto sul disco."""
    root = tmp_path / "lib"
    percorso = _posa(root / "a.fits", **TOKYO)
    # le 05:00 UTC sono le 14:00 a Tokyo, gia' la notte del 17; in UTC sarebbe ancora quella del 16
    _sul_disco(percorso, "2024-05-17T05:00:00")

    with _apri(db_path, root) as c:
        assert _notti(c) == {"a.fits": ("2024-05-17", "Asia/Tokyo")}


def test_the_question_on_poses_without_a_name_says_their_hours(db_path, tmp_path):
    """Due oggetti senza nome e senza coordinate nella stessa notte sono una domanda sola (Marco,
    27/9/2026): la domanda dice dalla prima all'ultima posa, nel fuso della notte, cosi' chi
    risponde vede se e' una serie o due."""
    root = tmp_path / "lib"
    _posa(root / "a.fits", **{"DATE-OBS": "2026-03-14T11:30:00", **TOKYO})
    _posa(root / "b.fits", **{"DATE-OBS": "2026-03-14T13:40:00", **TOKYO})

    with _apri(db_path, root) as c:
        (gruppo,) = review(c)["unnamed"]

    assert (gruppo["first_frame"], gruppo["last_frame"]) == (
        "2026-03-14T20:30:00+09:00",
        "2026-03-14T22:40:00+09:00",
    )


def test_the_hours_are_those_of_the_poses_that_say_when(db_path, tmp_path):
    """La data del file da' la notte a chi non dice quando, ma non e' un'ora di ripresa: le ore
    della domanda sono quelle delle pose con `DATE-OBS`."""
    root = tmp_path / "lib"
    _posa(root / "a.fits", **{"DATE-OBS": "2026-03-14T11:30:00", **TOKYO})
    _sul_disco(_posa(root / "b.fits", **TOKYO), "2026-03-14T13:40:00")

    with _apri(db_path, root) as c:
        (gruppo,) = review(c)["unnamed"]

    assert (gruppo["frames"], gruppo["first_frame"], gruppo["last_frame"]) == (
        2,
        "2026-03-14T20:30:00+09:00",
        "2026-03-14T20:30:00+09:00",
    )


def test_an_hour_in_a_zone_that_does_not_exist_is_not_invented():
    """Un fuso che non esiste non si indovina: l'ora non si scrive, invece di scriverla in UTC
    come se fosse del posto."""
    assert local_iso("2026-03-14T11:30:00", "Da/Nessuna_Parte") is None
    assert local_iso("2026-03-14T11:30:00") == "2026-03-14T11:30:00+00:00"


def test_poses_without_a_date_from_two_years_are_two_questions(db_path, tmp_path):
    """Pose senza data e senza camera di due anni diversi sono due domande: la notte e' quella
    del file."""
    root = tmp_path / "lib"
    for nome, quando in (("a.fits", "2024-05-17T21:00:00"), ("b.fits", "2025-08-02T21:00:00")):
        percorso = write_fits(root / nome, {"IMAGETYP": "Light Frame", "EXPTIME": 300.0})
        _sul_disco(percorso, quando)

    with _apri(db_path, root) as c:
        notti = sorted(g["night"] for g in review(c)["rigless"])

    assert notti == ["2024-05-17", "2025-08-02"]
