"""I mosaici scritti, dopo: cosa succede quando le pose cambiano camera, perdono il cielo, o un
pannello nuovo lega due mosaici. Il banco e' quello di `test_mosaic.py`; le regole stanno in
`spine/mosaic.py` e nel contratto `docs/domini/mosaico.md`.
"""

import pytest

from astrolog.spine import declarations as decl
from astrolog.spine import mosaic, typeless_answer
from test_mosaic import (
    ALTRA_NOTTE,
    NOTTE,
    SI,
    A,
    B,
    C,
    D,
    E,
    chiave_di,
    posa,
    prepara,
    proposti,
    rispondi,
)


def test_a_pose_changing_camera_stays_in_its_mosaic(archivio):
    """Si dice di che camera sono le pose (*Frame senza camera*), le pose ripassano da `group`, e
    il mosaico resta com'era: la sua chiave non porta la camera."""
    prepara(archivio)
    pose = [posa(archivio, A, corredo=None), posa(archivio, B, corredo=None)]
    riga = rispondi(archivio, SI)

    archivio.execute("UPDATE frames SET rig_id = 1")
    mosaic.place(archivio, pose)

    assert [chiave_di(archivio, p) for p in pose] == [riga["key"]] * 2
    nuovo = posa(archivio, C, corredo=1)
    assert chiave_di(archivio, nuovo) == riga["key"]


def test_merging_two_spellings_of_a_camera_joins_the_confirmed_mosaic(archivio):
    """Due grafie della stessa camera hanno ripreso la stessa regione, e solo una ha la risposta:
    unite, le pose dell'altra entrano nel mosaico confermato invece di restare una domanda
    sovrapposta."""
    prepara(archivio)
    posa(archivio, A, corredo=1)
    posa(archivio, B, corredo=1)
    altre = [posa(archivio, A, corredo=2), posa(archivio, B, corredo=2)]
    riga = next(m for m in proposti(archivio) if m["frames"] == 2)
    mosaic.write_answer(archivio, riga["key"], SI)
    confermato = chiave_di(archivio, 1) or chiave_di(archivio, altre[0])

    archivio.execute("UPDATE frames SET rig_id = 1")
    mosaic.place(archivio, altre)

    assert [(m["panels"], m["frames"], m["answer"]) for m in proposti(archivio)] == [
        (2, 4, decl.MOSAIC_YES)
    ]
    assert [chiave_di(archivio, p) for p in altre] == [confermato] * 2


def test_a_pose_told_its_camera_later_joins_the_confirmed_mosaic(archivio):
    """Un frame arrivato senza camera apre un pannello suo; detta la camera, entra nel pannello
    del corredo vero, e con lui nel mosaico gia' confermato."""
    prepara(archivio)
    posa(archivio, A)
    posa(archivio, B)
    riga = rispondi(archivio, SI)
    tardi = posa(archivio, A, corredo=None)

    archivio.execute("UPDATE frames SET rig_id = 1 WHERE id = ?", (tardi,))
    mosaic.place(archivio, [tardi])

    assert chiave_di(archivio, tardi) == riga["key"]
    assert [m["panels"] for m in proposti(archivio)] == [2]


def test_a_pose_that_loses_its_sky_leaves_the_mosaic(archivio):
    """Un frame dichiarato file di calibrazione perde il cielo: esce dal suo pannello e dal
    mosaico, con le sue ore, e un pannello rimasto vuoto non lega piu' i vicini."""
    prepara(archivio)
    posa(archivio, A)
    posa(archivio, B)
    ponte = posa(archivio, C)
    rispondi(archivio, SI)

    typeless_answer.detach(archivio, [ponte])
    mosaic.place(archivio, [])

    (riga,) = proposti(archivio)
    assert (riga["panels"], riga["frames"]) == (2, 2)
    assert chiave_di(archivio, ponte) is None


def test_an_emptied_panel_does_not_link_its_neighbours(archivio):
    """Il pannello di B resta vuoto quando la sua posa perde il cielo: un frame nuovo su C, che
    toccherebbe solo B, non finisce nel mosaico di A."""
    prepara(archivio)
    posa(archivio, A)
    b = posa(archivio, B)
    typeless_answer.detach(archivio, [b])
    mosaic.place(archivio, [])

    posa(archivio, C)

    assert proposti(archivio) == []


def test_a_mosaic_never_mixes_two_rigs(archivio):
    """La posa piu' vecchia di un mosaico senza risposta cambia corredo e ne apre uno nuovo: la
    chiave nata da lei non puo' riportarla nel mosaico vecchio, che vive ancora nell'altro."""
    prepara(archivio)
    vecchia = posa(archivio, A, corredo=None, quando=NOTTE)
    posa(archivio, B, corredo=None, quando=ALTRA_NOTTE)
    archivio.execute("UPDATE frames SET rig_id = 1 WHERE id = ?", (vecchia,))
    mosaic.place(archivio, [vecchia])

    posa(archivio, B, corredo=1)

    corredi = archivio.execute(
        "SELECT mosaic_id, COUNT(DISTINCT COALESCE(rig_id, -1)) FROM panels"
        " WHERE mosaic_id IS NOT NULL GROUP BY mosaic_id"
    ).fetchall()
    assert corredi and all(quanti == 1 for _, quanti in corredi)


def test_a_confirmed_mosaic_left_with_one_panel_is_not_a_mosaic(archivio):
    """Il pannello di A perde la sua posa: quello che resta e' un soggetto ripreso normalmente, e
    le sue pose tornano al loro oggetto invece di fare un mosaico di un pannello."""
    prepara(archivio)
    a = posa(archivio, A)
    b = posa(archivio, B)
    rispondi(archivio, SI)

    typeless_answer.detach(archivio, [a])
    mosaic.place(archivio, [])

    assert chiave_di(archivio, b) is None


def test_an_answer_from_an_old_page_on_a_single_panel_is_refused(archivio):
    """La pagina vecchia mostrava A+B; poi B perde il cielo e resta un pannello solo. Rispondere
    da quella pagina e' rispondere a un mosaico che non c'e' piu', e si dice."""
    prepara(archivio)
    posa(archivio, A)
    b = posa(archivio, B)
    (vecchia,) = proposti(archivio)
    typeless_answer.detach(archivio, [b])
    mosaic.place(archivio, [])

    with pytest.raises(LookupError):
        mosaic.write_answer(archivio, vecchia["key"], SI)


def test_a_panel_keeps_its_rig_while_some_of_its_poses_are_still_there(archivio):
    """Una sola delle due pose di un pannello cambia camera: il pannello resta del corredo delle
    altre, o una posa nuova di quel corredo nello stesso punto ne aprirebbe un terzo."""
    prepara(archivio)
    prima = posa(archivio, A)
    posa(archivio, A)
    posa(archivio, B)
    rispondi(archivio, SI)
    archivio.execute("UPDATE frames SET rig_id = 2 WHERE id = ?", (prima,))
    mosaic.place(archivio, [prima])

    posa(archivio, A)

    (riga,) = proposti(archivio)
    assert (riga["panels"], riga["frames"]) == (2, 4), "la posa spostata resta nel suo pannello"
    assert chiave_di(archivio, prima) == riga["key"]


def test_the_centre_does_not_break_across_ra_zero(archivio):
    """Due pannelli ai due lati di RA 0: il centro sta fra loro, non dall'altra parte del cielo."""
    prepara(archivio)
    posa(archivio, (359.75, 10.0))
    posa(archivio, (0.25, 10.0))
    (riga,) = proposti(archivio)
    assert min(riga["ra_deg"], 360 - riga["ra_deg"]) < 0.1


def test_a_panel_joining_two_questions_makes_one(archivio):
    """Un pannello in mezzo lega due mosaici senza risposta: diventano uno."""
    prepara(archivio)
    for cielo in (A, B, D, E):
        posa(archivio, cielo)
    assert [m["panels"] for m in proposti(archivio)] == [2, 2]
    posa(archivio, C)
    assert [m["panels"] for m in proposti(archivio)] == [5]


def test_a_panel_joining_an_answer_and_a_question_takes_the_answer(archivio):
    """Uno dei due ha una risposta: l'altro entra in lui, e la risposta vale per tutti."""
    prepara(archivio)
    for cielo in (A, B, D, E):
        posa(archivio, cielo)
    rispondi(archivio, SI, riga=1)
    posa(archivio, C)
    (riga,) = proposti(archivio)
    assert (riga["panels"], riga["answer"]) == (5, decl.MOSAIC_YES)


def test_a_panel_joining_two_answers_does_not_merge_them(archivio):
    """Due risposte dell'utente non si fondono in silenzio: il pannello entra nel piu' vecchio."""
    prepara(archivio)
    for cielo in (A, B, D, E):
        posa(archivio, cielo)
    rispondi(archivio, SI, riga=0)
    rispondi(archivio, decl.MOSAIC_NO, riga=1)
    posa(archivio, C)
    assert [(m["panels"], m["answer"]) for m in proposti(archivio)] == [
        (3, decl.MOSAIC_YES),
        (2, decl.MOSAIC_NO),
    ]
