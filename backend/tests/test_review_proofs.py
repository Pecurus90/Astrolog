"""Da confermare, **le prove** accanto alle domande (tavola v82 di Design, `Da confermare.dc.html`):
cio' che serve per rispondere senza andare a memoria arriva dall'API gia' fatto, il frontend lo
scrive e basta.

* Un oggetto in dubbio porta le sue **notti** e **ottica e camera** dei suoi frame, e se il cielo
  **ha gia' guardato**: "non ancora cercato" non e' "nessun oggetto trovato".
* Un filtro dalla banda ignota porta gli **oggetti nel campo** e **ottica e camera**.
* Due grafie della stessa camera portano il **sensore**.

L'archivio sintetico (`tests/synthetic.py`): M 31 in dubbio, cinque frame su due notti, quattro
con `ATR2600M(USB2.0)` e uno con `ATR2600M`, tutti dietro l'Askar 103Apo; il filtro `N` su un frame
di NGC 6888.
"""

from astrolog.spine import stages
from conftest import by_name, db, review

ASKAR = "Askar 103Apo"


def _frame_di(client, nome):
    with db(client) as conn:
        return conn.execute(
            "SELECT frame_id FROM positions WHERE rel_path LIKE ?", (f"%{nome}",)
        ).fetchone()[0]


def test_a_doubt_carries_its_nights_and_its_optics_and_camera(client):
    m31 = by_name(review(client)["objects"], "M 31")
    assert m31["nights"] == ["2024-10-31", "2024-11-01"]
    assert m31["rigs"] == [
        {"optics": ASKAR, "camera": "ATR2600M(USB2.0)", "frames": 4},
        {"optics": ASKAR, "camera": "ATR2600M", "frames": 1},
    ]


def test_a_doubt_says_whether_the_sky_has_looked_yet(client):
    """Nel sintetico il cielo ha guardato senza trovare niente: e' cercato. Un frame che torna in
    coda per il solve fa dire "non ancora cercato" a tutta la scheda."""
    assert by_name(review(client)["objects"], "M 31")["searched"] is True
    with db(client) as conn:
        stages.invalidate(conn, [_frame_di(client, "nina/L_003.fits")], stages.StageName.SOLVE)
    assert by_name(review(client)["objects"], "M 31")["searched"] is False


def test_a_filter_with_an_unknown_band_carries_the_objects_and_the_rigs_of_its_frames(client):
    n = by_name(review(client)["filters"], "N")
    assert n["subjects"] == [{"name": "NGC 6888", "frames": 1}]
    assert n["rigs"] == [{"optics": ASKAR, "camera": "ATR2600M(USB2.0)", "frames": 1}]


def test_two_spellings_of_one_camera_carry_the_sensor(client):
    (coppia,) = review(client)["lookalikes"]
    assert (coppia["width_px"], coppia["height_px"], coppia["pixel_um"]) == (4, 3, 3.76)
