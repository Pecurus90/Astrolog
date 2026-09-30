"""Un pannello conta nel suo mosaico solo se ne regge una parte: almeno il 25% del tempo del
pannello piu' lungo (Marco, 27/9/2026; il perche' e le fonti in `spine/mosaic_weight.py`).

Il caso vero e' la Rosetta: dopo un giro al meridiano non ricentrato, poche pose spostate aprivano
un secondo "pannello", e l'app proponeva un mosaico che nessuno aveva ripreso. Gli aiutanti del
banco sono quelli di `test_mosaic.py`, con le sue coordinate di IC 405.
"""

from astrolog.spine import mosaic, typeless_answer
from test_mosaic import SI, A, B, C, chiave_di, posa, prepara, proposti, rispondi


def _pannello(conn, cielo, quante, **kw):
    return [posa(conn, cielo, **kw) for _ in range(quante)]


def test_two_stray_poses_beside_a_panel_are_not_a_mosaic(archivio):
    """**La regola.** Dieci pose e, accanto, due: il 20% del lavoro non e' un pannello, e non c'e'
    nessun mosaico da proporre."""
    prepara(archivio)
    _pannello(archivio, A, 10)
    _pannello(archivio, B, 2)

    assert proposti(archivio) == []


def test_a_panel_shot_less_than_the_others_still_counts(archivio):
    """Un pannello vero ripreso meno degli altri -- una notte contro quattro -- resta un pannello:
    il 25% del pannello piu' lungo conta, e il mosaico si propone con tutte e due le parti."""
    prepara(archivio)
    _pannello(archivio, A, 8)
    _pannello(archivio, B, 2)

    assert [(m["panels"], m["frames"]) for m in proposti(archivio)] == [(2, 10)]


def test_the_share_is_measured_on_the_time_of_the_poses(archivio):
    """Si misura il tempo, non il numero di pose: quattro pose da 10 secondi accanto a quattro da
    120 sono l'8% del lavoro, e non fanno un pannello."""
    prepara(archivio)
    _pannello(archivio, A, 4)
    _pannello(archivio, B, 4, tempo=10.0)

    assert proposti(archivio) == []


def test_without_the_time_the_share_is_measured_on_the_poses(archivio):
    """Se i file non dicono quanto sono durate le pose, si contano le pose: due accanto a quattro
    sono la meta', e il mosaico c'e'."""
    prepara(archivio)
    _pannello(archivio, A, 4, tempo=None)
    _pannello(archivio, B, 2, tempo=None)

    assert [m["panels"] for m in proposti(archivio)] == [2]


def test_without_the_time_few_poses_still_do_not_count(archivio):
    """Anche contando le pose la regola e' la stessa: due mute accanto a dieci mute sono il 20%."""
    prepara(archivio)
    _pannello(archivio, A, 10, tempo=None)
    _pannello(archivio, B, 2, tempo=None)

    assert proposti(archivio) == []


def test_a_pose_that_leaves_for_another_rig_reweighs_the_mosaic(archivio):
    """Il peso segue anche le pose che se ne vanno: una posa di B che risulta di un altro corredo
    esce dal pannello, e B, sceso al 20%, non fa piu' un mosaico."""
    prepara(archivio)
    _pannello(archivio, A, 10)
    via = _pannello(archivio, B, 3)[0]

    archivio.execute("UPDATE frames SET rig_id = 2 WHERE id = ?", (via,))
    mosaic.place(archivio, [via])

    assert proposti(archivio) == []


def test_poses_that_turn_out_to_be_calibration_reweigh_the_mosaic(archivio):
    """E quelle che la risposta "file di calibrazione" stacca dal cielo: il pannello piu' lungo
    scende, e quello che prima non contava adesso conta."""
    prepara(archivio)
    lunghe = _pannello(archivio, A, 10)
    _pannello(archivio, B, 2)

    typeless_answer.detach(archivio, lunghe[:8])

    assert [m["panels"] for m in proposti(archivio)] == [2]


def test_a_confirmed_mosaic_does_not_take_poses_that_do_not_count(archivio):
    """Un pannello di troppo poco accanto a un mosaico confermato non entra nel mosaico: le sue
    pose restano senza la chiave, e cioe' col loro oggetto nell'Archivio."""
    prepara(archivio)
    dentro = _pannello(archivio, A, 8) + _pannello(archivio, B, 8)
    rispondi(archivio, SI)

    sperse = _pannello(archivio, C, 1)

    assert [m["panels"] for m in proposti(archivio)] == [2]
    assert chiave_di(archivio, sperse[0]) is None
    assert all(chiave_di(archivio, p) is not None for p in dentro)


def test_the_centre_of_the_mosaic_does_not_lean_towards_a_panel_that_does_not_count(archivio):
    """Il centro, e il nome che ne viene, si prendono dai pannelli che contano: le pose spostate
    accanto a B non tirano il centro verso di se'."""
    prepara(archivio)
    _pannello(archivio, A, 8)
    _pannello(archivio, B, 8)
    _pannello(archivio, C, 1)

    (mosaico,) = proposti(archivio)
    assert abs(mosaico["ra_deg"] - (A[0] + B[0]) / 2) < 0.01


def test_without_the_catalog_the_name_comes_from_the_panels_that_count(archivio):
    """Dove il catalogo non ha niente, il nome proposto e' il soggetto con piu' pose -- fra i
    pannelli che contano: venti pose brevissime accanto, che non reggono niente del lavoro, non
    danno il nome al mosaico."""
    prepara(archivio)
    # vicino al polo sud, dove il catalogo non ha voci: mezzo grado l'uno dall'altro
    vuoto = [(60.0, -85.0), (65.737, -85.0), (71.474, -85.0)]
    _pannello(archivio, vuoto[0], 8)
    _pannello(archivio, vuoto[1], 8)
    _pannello(archivio, vuoto[2], 20, oggetto=2, tempo=1.0)

    (mosaico,) = proposti(archivio)
    assert mosaico["proposed"] == "IC 401"


def test_a_confirmed_mosaic_whose_other_panel_stops_counting_is_not_one_anymore(archivio):
    """Il peso cambia con le pose che arrivano: se uno dei due pannelli scende sotto il 25%, il
    mosaico resta con un pannello solo, e un pannello solo non e' un mosaico."""
    prepara(archivio)
    primo = _pannello(archivio, A, 3)
    _pannello(archivio, B, 3)
    rispondi(archivio, SI)

    _pannello(archivio, A, 10)  # A arriva a 13: B, con 3, e' sotto il 25%

    assert proposti(archivio) == []
    assert chiave_di(archivio, primo[0]) is None


def test_poses_without_the_size_of_their_field_make_no_mosaic(archivio):
    """Senza le misure del campo non si sa cosa inquadra una posa: non apre un pannello, e due pose
    identiche non diventano un mosaico."""
    prepara(archivio)
    pose = _pannello(archivio, A, 2, campo=(None, None))

    assert proposti(archivio) == []
    righe = archivio.execute(
        "SELECT panel_id FROM frames WHERE id IN (?, ?)", tuple(pose)
    ).fetchall()
    assert [r[0] for r in righe] == [None, None]
