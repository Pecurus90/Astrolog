"""Dato il cielo misurato di una posa, cosa c'e' nel campo e quale e' il soggetto.

E' la prova che geometria, punteggio e catalogo dicono insieme la cosa giusta. Gira sul
**catalogo vero**, ai puntamenti **veri** dei tre casi che hanno imposto la formula: se un peso
si sposta, qui si vede.
"""

import math
import shutil

import pytest

from astrolog.db.connect import connect
from astrolog.spine import identify


def campo(ra, dec, larghezza, altezza, rotazione=0.0):
    """Un cielo misurato come lo scrive il solver."""
    return {"ra_deg": ra, "dec_deg": dec, "scale_arcsec_px": 1.0,
            "width_deg": larghezza, "height_deg": altezza, "rotation_deg": rotazione}  # fmt: skip


@pytest.fixture(scope="module")
def catalogo(_catalog_template, tmp_path_factory):
    """Il catalogo impacchettato vero: 22.080 voci, quelle che l'utente incontrera'.

    E' una **copia** del DB modello di `conftest`, costruito una volta per tutta la suite. Di
    modulo perche' nessuno dei test di questo file scrive, e a fixture di funzione la copia si
    rifarebbe per ognuno; ed e' una copia, invece del modello aperto in comune, perche' il
    giorno che uno scrivesse non lo sporcherebbe.

    **Ed e' il motivo per cui questa fixture non deve crescere**: una fixture di modulo si
    costruisce **prima** del recinto autouse di `conftest`, che e' di funzione. Qui non fa danno
    -- si scrive in `tmp_path_factory` -- ma il giorno che ci entrasse un `create_app` o uno
    `run.queue`, scriverebbe nella cartella dati vera dell'utente e nessuno se ne accorgerebbe."""
    path = tmp_path_factory.mktemp("catalogo_letto") / "catalogo.db"
    shutil.copy(_catalog_template, path)
    c = connect(path)
    yield c
    c.close()


# --- i tre casi che hanno imposto il punteggio -----------------------------------------------


@pytest.mark.parametrize(
    ("wcs", "soggetto", "piu_vicino", "caso"),
    [
        # puntando dentro M 31, il piu' vicino e' la nana M 32
        (campo(10.6743, 40.8653, 3.0, 2.0), "M 31", "M 32", "M 31 contro la sua nana"),
        # su M 101, il piu' vicino e' una sua regione HII
        (campo(210.6183, 54.2769, 1.0, 0.667), "M 101", "NGC 5447", "M 101 contro la sua HII"),
        # sulla Rosetta, il piu' vicino e' una nebulosetta senza nome
        (campo(97.6549, 5.0489, 1.66, 1.11), "NGC 2237", "Ced 76", "la Rosetta contro Ced 76"),
    ],
)
def test_the_subject_is_not_the_nearest_one(catalogo, wcs, soggetto, piu_vicino, caso):
    """Il fatto duro: su cinque bersagli su sei il candidato piu' vicino e' quello sbagliato.
    Prendere il primo per scarto crescente darebbe la risposta sbagliata in tutti e tre."""
    trovati = identify.candidates(catalogo, wcs)
    assert trovati, caso

    per_scarto = sorted(trovati, key=lambda c: c.sep_deg)
    assert per_scarto[0].name == piu_vicino, f"{caso}: non e' lui il piu' vicino"
    assert trovati[0].name == soggetto, f"{caso}: proposto {trovati[0].name}"


def test_the_candidates_come_sorted_by_score(catalogo):
    trovati = identify.candidates(catalogo, campo(10.6743, 40.8653, 3.0, 2.0))
    assert [c.score for c in trovati] == sorted((c.score for c in trovati), reverse=True)


# --- cosa e' nella foto, e cosa era solo li' vicino -------------------------------------------


def test_each_candidate_says_whether_it_is_really_in_the_picture(catalogo):
    """E' la ragione per cui il rettangolo esiste. Su un campo stretto centrato su M 31 la
    galassia riempie la foto; NGC 206, la sua nube stellare a 40 primi, nel cono ci finisce ma
    **nell'inquadratura no**. Sono due informazioni diverse e l'utente le vuole tutte e due:
    "e' nella foto" e "era li' accanto" non si dicono nello stesso modo."""
    per_nome = {
        c.name: c for c in identify.candidates(catalogo, campo(10.6848, 41.2691, 0.5, 0.35))
    }
    assert per_nome["M 31"].in_frame is True
    assert per_nome["NGC 206"].in_frame is False
    assert per_nome["NGC 206"].sep_deg < 1.0  # nel cono c'era eccome


def test_what_does_not_even_touch_the_frame_is_left_out(catalogo):
    """Chi filtra e' `overlaps_frame`, e sbaglia apposta per difetto. Con quel campo M 110 non
    sfiora nemmeno l'inquadratura: non e' un candidato improbabile, e' un oggetto che nella
    foto non c'e'. Allargando il campo torna in gara."""
    stretto = [c.name for c in identify.candidates(catalogo, campo(10.6848, 41.2691, 0.5, 0.35))]
    largo = [c.name for c in identify.candidates(catalogo, campo(10.6848, 41.2691, 3.0, 2.0))]
    assert "M 110" not in stretto
    assert "M 110" in largo


def test_a_narrow_field_still_finds_the_big_object_around_it(catalogo):
    """Su una focale lunga puntata dentro M 31, la galassia e' **piu' grande del campo** e il
    suo centro sta a un grado: cercando solo quanto e' larga la foto non tornerebbe mai, e la
    posa resterebbe senza soggetto."""
    lungo = campo(10.6743, 40.8653, 0.30, 0.20)  # mezza diagonale 0,18 gradi
    per_nome = {c.name: c for c in identify.candidates(catalogo, lungo)}
    assert "M 31" in per_nome
    # e ci deve arrivare **con la sua dimensione**: il centro di M 31 e' a 0,4 gradi, fuori dal
    # rettangolo, ma la galassia e' larga tre gradi e la foto e' tutta dentro di lei. Senza
    # passare la dimensione, la posa direbbe che nell'inquadratura non c'era niente.
    assert per_nome["M 31"].in_frame is True
    assert per_nome["M 31"].sep_deg > 0.3


def test_the_list_stops_at_a_handful(catalogo):
    """Serve a scegliere, non a leggere il catalogo: in un campo affollato i candidati sono
    decine, e oltre i primi nessuno guarda."""
    orione = campo(83.8187, -5.3897, 3.0, 2.0)
    assert len(identify.candidates(catalogo, orione, limit=100)) > 6, "il campo non e' affollato"
    assert len(identify.candidates(catalogo, orione)) == 6  # il valore, non la costante
    assert identify.CANDIDATES_LIMIT == 6


def test_the_pleiades_win_over_their_own_nebulosity(catalogo):
    """M 45 e' un ammasso avvolto da nebulosita' di riflessione, ognuna con la sua voce: chi
    fotografa le Pleiadi vuole leggere "M 45", non il nome della nebulosetta attorno a una
    delle sette stelle. E' il caso che il piano aveva scelto per provare un campo affollato di
    voci vere tutte dentro l'inquadratura."""
    trovati = identify.candidates(catalogo, campo(56.75, 24.1167, 3.0, 2.0))
    assert trovati[0].name == "M 45", f"proposto {trovati[0].name}"
    assert trovati[0].in_frame is True


def test_two_real_rivals_are_asked_about_and_a_companion_is_not(catalogo):
    """La prova end-to-end dell'ambiguita', partendo dal catalogo e non da numeri a mano.
    M 81 e M 82 sono due bersagli distinti che stanno nello stesso campo largo: quale sia il
    soggetto lo sa solo chi ha scattato, e l'app chiede. M 32 invece sta **dentro** M 31, c'e'
    in ogni sua posa, e chiedere sarebbe rumore."""
    from astrolog.spine import identify_geometry as geometry
    from astrolog.spine import identify_score as score

    def primi_due(wcs):
        due = identify.candidates(catalogo, wcs)[:2]
        est, nord = geometry.tangent_offset_deg(
            due[0].ra_deg, due[0].dec_deg, due[1].ra_deg, due[1].dec_deg
        )
        return due, math.hypot(est, nord), geometry.frame_radius_deg(wcs)

    due, fra_loro, fov = primi_due(campo(148.93, 69.37, 1.5, 1.0))
    assert {due[0].name, due[1].name} == {"M 81", "M 82"}
    assert score.is_ambiguous(due[0], due[1], separation_deg=fra_loro, fov_radius_deg=fov) is True

    due, fra_loro, fov = primi_due(campo(10.6743, 40.8653, 3.0, 2.0))
    assert {due[0].name, due[1].name} == {"M 31", "M 32"}
    assert score.is_ambiguous(due[0], due[1], separation_deg=fra_loro, fov_radius_deg=fov) is False


# --- la misura larga: il criterio su tutti i bersagli veri ------------------------------------


def test_pointing_at_a_real_target_proposes_that_target_back(catalogo):
    """La prova larga, e la sola che copra bersagli che non sono i tre scelti a mano: si punta
    al centro di **ogni** oggetto del catalogo che ha un nome comune e una dimensione -- 577,
    cioe' quelli che qualcuno fotografa davvero -- con un campo grande il doppio dell'oggetto, e
    si guarda se il criterio lo propone indietro.

    Il pavimento e' la rete contro lo spostamento di un peso: oggi si sta sopra il 97%, e
    **nessuno dei mancati e' un errore vero**. Dodici sono la relazione pezzo/tutto, che il
    criterio geometrico da solo non distingue e che sta in coda: `B 33` (Testa di Cavallo)
    propone `IC 434`, la nebulosa contro cui e' controluce, e `M 43` propone `M 42`. Tre sono
    voci doppie che portano lo stesso nome comune (`HCG 92` e `NGC 7318` sono tutti e due
    "Stephan's Quintet"; la terza differisce per un apostrofo). Gli altri due sono adiacenze --
    ma pezzo e adiacenza si distinguono a giudizio, non con un conto."""
    bersagli = catalogo.execute(
        "SELECT slug, ra_deg, dec_deg, size_major_arcmin FROM catalog_entries"
        " WHERE common_name IS NOT NULL AND size_major_arcmin IS NOT NULL"
    ).fetchall()
    assert len(bersagli) > 500, f"solo {len(bersagli)} bersagli: il catalogo non e' quello vero"

    presi = 0
    for b in bersagli:
        lato = max(b["size_major_arcmin"] / 60.0 * 2.0, 0.25)  # si inquadra largo il doppio
        wcs = campo(b["ra_deg"], b["dec_deg"], lato, lato * 2 / 3)
        proposti = identify.candidates(catalogo, wcs, limit=1)
        presi += bool(proposti and proposti[0].slug == b["slug"])
    quota = presi / len(bersagli)
    assert quota >= 0.95, f"solo {presi}/{len(bersagli)} ({quota:.1%}): un peso si e' spostato"


# --- senza cielo, e senza catalogo -------------------------------------------------------------


def test_without_a_measured_sky_there_are_no_candidates(catalogo):
    """Una posa non risolta non ha campo: qui non si inventa niente, e chi chiama va per nome."""
    assert identify.candidates(catalogo, {"ra_deg": None, "dec_deg": None}) == []


def test_without_a_catalogue_it_answers_an_empty_list(conn):
    """A mani vuote l'app funziona lo stesso: non sa dire cosa hai fotografato, e non esplode."""
    assert identify.candidates(conn, campo(10.6848, 41.2691, 3.0, 2.0)) == []
