"""Il campionamento dei setup col seeing previsto (ADR 0021) e il seeing rispetto al pavimento F di
ogni setup (ADR 0039), per notte: domini/meteo.md. Marco, 24/11/2026: per ogni setup, nella carta
Campionamento; la carta Seeing resta 2"/4"."""

import json

import pytest

from astrolog.weather import setups
from test_weather_forecast import db  # noqa: F401 - `db` e' una fixture


def seeing(valore=2.0, picco=None, stima=None):
    return {
        "code": "seeing",
        "value": valore,
        "peak": valore if picco is None else picco,
        "estimated_from": stima,
    }


def setup(scala=1.0, pavimento=0.9, rig_id=1, frames=0, manca=None):
    return setups.Rig(
        rig_id=rig_id,
        name=f"Setup {rig_id}",
        optics="Ottica",
        camera="Camera",
        frames=frames,
        scale_arcsec_px=scala,
        # come li scrive `rig_numbers` (SEEING_PER_SCALE): qui si leggono, non si rifanno
        seeing_from=2 * scala,
        seeing_to=3 * scala,
        floor_arcsec=pavimento,
        floor_missing=manca,
    )


@pytest.mark.parametrize(
    ("seeing_previsto", "atteso"),
    [(2.0, "ideal"), (1.9, "under"), (3.0, "ideal"), (3.1, "over"), (3.04, "ideal")],
)
def test_the_sampling_is_ideal_from_a_third_to_a_half_of_the_seeing_edges_included(
    seeing_previsto, atteso
):
    (riga,) = setups.judged(seeing(seeing_previsto), [setup(scala=1.0)])
    assert riga["sampling"] == atteso
    assert (riga["seeing_from"], riga["seeing_to"]) == (2.0, 3.0)


@pytest.mark.parametrize("seeing_previsto", [1.7, 2.6])
def test_the_sampling_is_judged_as_it_is_shown_to_a_tenth(seeing_previsto):
    """Scala 0,852: a schermo "ottimo con seeing fra 1,7 e 2,6″", e 1,7 o 2,6 sono ottimo."""
    (riga,) = setups.judged(seeing(seeing_previsto), [setup(scala=0.852)])
    assert (riga["seeing_from"], riga["seeing_to"]) == (1.7, 2.6)
    assert riga["sampling"] == "ideal"


@pytest.mark.parametrize(
    ("picco", "atteso"),
    [(0.89, "go"), (0.9, "marginal"), (1.55, "marginal"), (1.56, "nogo")],
)
def test_the_seeing_is_marginal_from_the_floor_and_nogo_from_root_three_floors(picco, atteso):
    """F = 0,9: incerto da 0,9, niente da 0,9 x 1,732 = 1,559 (FWHM doppia)."""
    (riga,) = setups.judged(seeing(0.5, picco=picco), [setup(pavimento=0.9)])
    assert riga["seeing_level"] == atteso


def test_the_seeing_word_comes_from_the_worst_hour_and_the_sampling_from_the_mean():
    """Come la carta Seeing (l'ora peggiore); il campionamento col seeing previsto della carta."""
    (riga,) = setups.judged(seeing(2.5, picco=4.0), [setup(scala=1.0, pavimento=2.0)])
    assert riga["sampling"] == "ideal"
    assert riga["seeing_level"] == "nogo"


def test_the_floor_is_judged_as_it_is_shown_to_a_tenth():
    """A schermo "limite del setup 0,7": un'ora a 0,7 e' gia' incerta."""
    (riga,) = setups.judged(seeing(0.5, picco=0.7), [setup(pavimento=0.74)])
    assert riga["floor_arcsec"] == 0.7
    assert riga["seeing_level"] == "marginal"


def test_a_setup_without_its_floor_keeps_the_sampling_and_says_what_it_lacks():
    manca = {"kind": "optics", "field": "aperture_mm"}
    (riga,) = setups.judged(seeing(2.0), [setup(pavimento=None, manca=manca)])
    assert riga["sampling"] == "ideal"
    assert riga["seeing_level"] is None
    assert riga["floor_missing"] == manca


@pytest.mark.parametrize(
    "notte",
    [None, seeing(None), {**seeing(None), "estimated_from": "jet"}],
)
def test_without_a_number_of_seeing_no_setup_is_judged(notte):
    assert setups.judged(notte, [setup()]) == []


def test_the_setups_come_most_used_first():
    righe = setups.judged(seeing(), [setup(rig_id=1, frames=5), setup(rig_id=2, frames=90)])
    assert [r["rig_id"] for r in righe] == [2, 1]


def _scrivi_setup(conn):
    conn.execute(
        "INSERT INTO gear_numbers VALUES('rig', 7, ?)",
        (
            json.dumps(
                {
                    "sampling": {"value": 1.0, "seeing_from": 2.0, "seeing_to": 3.0},
                    "seeing_floor": {"value": 0.9, "missing": None},
                    "label": {"name": "Notte in quota", "optics": "FRA400", "camera": "2600MM"},
                }
            ),
        ),
    )


def _scrivi_notte(conn, misura):
    conn.execute(
        "INSERT INTO weather_view VALUES(1, '2026-11-24', 'best_match', '2026-11-24T10:00:00Z',"
        " '[]', ?)",
        (json.dumps({"measures": [misura], "setups": []}),),
    )


def _setups_scritti(conn):
    (riga,) = conn.execute("SELECT summary_json FROM weather_view").fetchall()
    return json.loads(riga[0])["setups"]


def test_a_changed_setup_reaches_the_written_nights_at_the_next_step(db):  # noqa: F811
    _scrivi_notte(db, seeing(2.0, picco=1.2))
    _scrivi_setup(db)
    assert setups.step(db) is True
    (riga,) = _setups_scritti(db)
    assert riga["name"] == "Notte in quota"
    assert riga["optics"] == "FRA400"
    assert riga["seeing_level"] == "marginal"
    assert setups.step(db) is False  # gia' scritto: niente da fare


def test_a_setup_without_a_scale_stays_out(db):  # noqa: F811
    _scrivi_notte(db, seeing(2.0))
    db.execute(
        "INSERT INTO gear_numbers VALUES('rig', 8, ?)",
        (json.dumps({"sampling": {"value": None}, "seeing_floor": {"value": None}}),),
    )
    setups.step(db)
    assert _setups_scritti(db) == []
