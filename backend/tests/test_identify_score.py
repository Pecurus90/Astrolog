"""Quale, fra gli oggetti nel campo, e' il soggetto.

Il fatto da cui parte tutto, misurato in `old/` su bersagli veri: **il candidato piu' vicino al
centro e' quello sbagliato**. Puntando dentro M 31 il piu' vicino e' M 32; sulla Rosetta e'
Ced 76; su M 101 e' la regione HII NGC 5447. Il soggetto e' l'oggetto grande e luminoso che
**contiene** il puntamento.

I casi qui sotto usano i valori **veri** del catalogo impacchettato, non numeri inventati: sono
proprio quelli che hanno imposto la formula, e se i pesi si spostano questi test lo dicono.
"""

import pytest

from astrolog.spine import identify_score as score

# Valori letti dal catalogo impacchettato. Il commento accanto e' cio' che il caso prova.
M31 = {"name": "M 31", "sep_deg": 0.4039, "size_major_arcmin": 177.83, "magnitude": 3.44}
M32 = {"name": "M 32", "sep_deg": 0.0030, "size_major_arcmin": 7.74, "magnitude": 8.13}
M101 = {"name": "M 101", "sep_deg": 0.1291, "size_major_arcmin": 23.99, "magnitude": 7.9}
NGC5447 = {"name": "NGC 5447", "sep_deg": 0.0, "size_major_arcmin": None, "magnitude": None}
ROSETTA = {"name": "NGC 2237", "sep_deg": 0.0723, "size_major_arcmin": 80.0, "magnitude": 9.0}
CED76 = {"name": "Ced 76", "sep_deg": 0.0, "size_major_arcmin": None, "magnitude": None}


# --- il fatto duro: il piu' vicino e' quello sbagliato ---------------------------------------


@pytest.mark.parametrize(
    ("soggetto", "vicino", "fov", "caso"),
    [
        (M31, M32, 1.8, "dentro M 31 il piu' vicino e' M 32, una galassia nana"),
        (M101, NGC5447, 0.6, "su M 101 il piu' vicino e' NGC 5447, una sua regione HII"),
        (ROSETTA, CED76, 1.0, "sulla Rosetta il piu' vicino e' Ced 76, una nebulosetta"),
    ],
)
def test_the_subject_is_the_one_that_contains_the_pointing(soggetto, vicino, fov, caso):
    """Sono i tre casi veri che hanno imposto il punteggio. Prendere il primo della lista per
    scarto crescente darebbe la risposta sbagliata in tutti e tre."""
    assert vicino["sep_deg"] < soggetto["sep_deg"], f"{caso}: il vicino non e' il piu' vicino"
    assert score.score_candidate(soggetto, fov) > score.score_candidate(vicino, fov), caso


def test_a_bright_one_at_the_edge_loses_to_a_faint_one_centred():
    """Il difetto strutturale che la formula corregge: un premio di luminosita' indipendente
    dalla geometria fa vincere l'oggetto brillante che nella foto quasi non c'e'."""
    bordo = {"name": "Ced 27", "sep_deg": 1.17, "size_major_arcmin": None, "magnitude": 5.27}
    centrata = {"name": "LBN 777", "sep_deg": 0.22, "size_major_arcmin": 20.0, "magnitude": None}
    assert score.score_candidate(centrata, 1.3) > score.score_candidate(bordo, 1.3)


def test_the_brightness_prize_shrinks_with_the_distance_from_the_centre():
    """**La magnitudine e' moltiplicata per la centratura, non sommata**, ed e' la regola
    centrale della formula: un premio di luminosita' che non guarda la geometria fa vincere
    l'oggetto brillante che nella foto quasi non c'e'. Qui si prova sul premio stesso, perche'
    un confronto fra due candidati resta vero anche con la somma e non tiene ferma la regola."""
    voce = {"name": "Ced 27", "size_major_arcmin": None}
    # al bordo la centratura vale zero, quindi la magnitudine non deve valere NIENTE: averla o
    # non averla dev'essere lo stesso punteggio. Sommandola, al bordo ne resterebbe tutta.
    al_bordo = {**voce, "sep_deg": 1.3}
    assert score.score_candidate({**al_bordo, "magnitude": 5.27}, 1.3) == pytest.approx(
        score.score_candidate({**al_bordo, "magnitude": None}, 1.3), abs=1e-9
    )
    # al centro invece vale tutta
    al_centro = {**voce, "sep_deg": 0.0}
    premio = score.score_candidate({**al_centro, "magnitude": 5.27}, 1.3) - score.score_candidate(
        {**al_centro, "magnitude": None}, 1.3
    )
    assert premio == pytest.approx(score.W_MAGNITUDE * score._magnitude_term(5.27), abs=1e-9)


def test_the_centring_bonus_is_worth_something():
    """Il peso della centratura non e' decorativo: azzerarlo cambia chi vince. Fra due
    candidati identici, quello centrato deve staccare quello al bordo **anche** senza
    magnitudine, e la differenza deve valere quanto il peso dichiarato."""
    muto = {"name": "Ced 27", "size_major_arcmin": None, "magnitude": None}
    centro = score.score_candidate({**muto, "sep_deg": 0.0}, 1.0)
    bordo = score.score_candidate({**muto, "sep_deg": 1.0}, 1.0)
    assert centro - bordo == pytest.approx(score.W_CONTAINMENT + score.W_CENTERING, abs=1e-9)
    assert score.W_CENTERING > 0


# --- il metro con cui si distinguono i candidati ----------------------------------------------


def test_the_ranking_metre_is_the_object_radius_not_a_fixed_degree():
    """Il metro e' il **raggio dell'oggetto**: un oggetto grande resta "contenente" a scarti
    maggiori, uno piccolo no. Quando era la tolleranza di accettazione valeva esattamente un
    grado per il 95% del catalogo, e il contenimento era identico per una galassia di 2 primi e
    una nebulosa di 50 -- la "separazione scalata sulla dimensione" non avveniva."""
    assert score.ranking_scale_deg(177.83) == pytest.approx(1.4819, abs=1e-3)  # M 31: il suo raggio
    assert score.ranking_scale_deg(7.74) == pytest.approx(0.0645, abs=1e-3)  # M 32: il suo
    assert score.ranking_scale_deg(600.0) == score.SCALE_CAP_DEG  # oltre il tetto
    assert score.ranking_scale_deg(None) == score.SEP_FLOOR_DEG  # ignota: il pavimento
    assert score.ranking_scale_deg(0.5) == score.SEP_FLOOR_DEG  # sotto il pavimento


def test_brightness_outweighs_containment():
    """Il commento dei pesi dichiara che **la magnitudine pesa un filo piu' del contenimento**,
    perche' e' il segnale che ribalta il clutter debole -- le nebulosette senza magnitudine, piu'
    vicine ma minori. E' una relazione fra due pesi, non un valore: si tiene ferma cosi'."""
    assert score.W_MAGNITUDE > score.W_CONTAINMENT


def test_the_floor_is_the_solver_error_not_the_goto_one():
    """`old/` aveva due pavimenti perche' il 94,5% delle sue pose non era risolto e le
    coordinate venivano dal GoTo. Qui `identify` gira **dopo** il solver: il pavimento e'
    l'errore del solver, e il gradino GoTo non si porta."""
    assert score.SEP_FLOOR_DEG == 0.05


# --- la centratura -----------------------------------------------------------------------------


def test_a_mosaic_panel_does_not_lose_its_own_subject():
    """Un oggetto piu' grande del pannello ha il centro **fuori** dal pannello. Normalizzando
    sul solo campo prendeva centratura zero, e con essa perdeva tutto il premio di luminosita':
    il soggetto del mosaico veniva svuotato proprio nelle sue pose."""
    magro = score.centering_term(0.55, 0.40, None)
    pieno = score.centering_term(0.55, 0.40, 150.0)
    assert magro == 0.0 and pieno == pytest.approx(0.67, abs=0.02)


def test_without_a_field_the_centring_is_neutral_and_does_not_add_up():
    """Senza campo non si puo' dire se un oggetto e' centrato: il termine vale 0,5, neutro. Ma
    **non entra come addendo**, perche' la stessa costante per tutti non cambia l'ordine e
    invece comprime i rapporti -- e la guardia dell'ambiguita' ragiona su un rapporto."""
    assert score.centering_term(1.0, None, 10.0) == 0.5
    senza = score.score_candidate(M31, None)
    con = score.score_candidate(M31, 1.8)
    assert senza < con  # l'addendo entra solo col campo noto

    # e senza campo l'addendo non c'e' proprio: il punteggio e' fatto solo dei quattro termini
    # che non guardano il campo. Se entrasse, ognuno prenderebbe lo stesso 0,6 in piu'.
    a_mano = (
        score.W_CONTAINMENT * (1.0 - min(1.0, M31["sep_deg"] / score.ranking_scale_deg(177.83)))
        + score.W_MAGNITUDE * score._magnitude_term(3.44) * 0.5
        + score.W_SIZE * score._size_term(177.83)
        + score.W_CATALOG * score.catalog_priority("M 31")
    )
    assert senza == pytest.approx(a_mano, abs=1e-9)


# --- la priorita' di catalogo -------------------------------------------------------------------


def test_a_faint_object_never_scores_worse_than_one_with_no_magnitude():
    """Il termine e' tagliato fra 3 e 12, e il taglio non e' cosmetico: **13.185 voci su
    22.080** stanno oltre la magnitudine 12 (si arriva a 24,9). Senza, il termine va negativo e
    un oggetto debole finisce sotto uno che la magnitudine non ce l'ha proprio -- l'opposto di
    "assente vale zero". E sotto il pavimento ci sono 23 voci, fra cui M 45 a 1,2."""
    assert score._magnitude_term(24.9) == 0.0  # il piu' debole del catalogo, non negativo
    assert score._magnitude_term(None) == 0.0
    assert score._magnitude_term(1.2) == score._magnitude_term(3.0)  # M 45: sotto il pavimento
    assert score._magnitude_term(3.0) == 1.0

    debole = {"name": "LDN 1", "sep_deg": 0.1, "size_major_arcmin": 10.0, "magnitude": 24.9}
    muto = {"name": "LDN 2", "sep_deg": 0.1, "size_major_arcmin": 10.0, "magnitude": None}
    assert score.score_candidate(debole, 1.0) == score.score_candidate(muto, 1.0)


def test_a_tiny_object_never_scores_worse_than_one_with_no_size():
    """Il gemello della prova qui sopra, sull'altro termine tagliato. **4.673 voci su 22.080**
    misurano meno di un primo (la piu' piccola 0,005'), e **31** stanno oltre i 316'. Senza il
    pavimento il termine va negativo e un oggetto minuscolo finisce sotto uno che la dimensione
    non ce l'ha; senza il tetto esce dallo 0..1 che l'intestazione dichiara."""
    assert score._size_term(0.005) == 0.0  # la piu' piccola del catalogo, non negativa
    assert score._size_term(None) == 0.0
    assert score._size_term(1560.0) == 1.0  # la piu' grande: dentro il tetto
    assert 0.0 < score._size_term(30.0) < 1.0

    minuscolo = {"name": "LDN 1", "sep_deg": 0.1, "size_major_arcmin": 0.005, "magnitude": 8.0}
    muto = {"name": "LDN 2", "sep_deg": 0.1, "size_major_arcmin": None, "magnitude": 8.0}
    assert score.score_candidate(minuscolo, 1.0) >= score.score_candidate(muto, 1.0)


def test_every_tier_of_the_catalogue_table_is_worth_what_it_says():
    """La tabella non e' decorativa: sono cinque gradini, e a parita' di geometria decidono
    loro. Provarli uno per uno e' l'unico modo di accorgersi se uno slitta."""
    assert score.catalog_priority("M 31") == 1.0
    assert score.catalog_priority("C 49") == 0.9
    assert score.catalog_priority("NGC 224") == 0.7
    assert score.catalog_priority("IC 434") == 0.55
    assert score.catalog_priority("Sh2 155") == 0.4
    for oscuro in ("LBN 452", "LDN 935", "vdB 141", "Ced 76", "B 33", "Abell 1", "RCW 49"):
        assert score.catalog_priority(oscuro) == 0.3, oscuro
    assert score.catalog_priority("PK 205+14.1") == 0.2  # non in tabella: il default


def test_the_search_radius_covers_the_whole_ranking_metre():
    """Le due costanti vivono in moduli diversi e devono restare uguali: se il cono fosse piu'
    stretto del metro del punteggio, un oggetto che "contiene" il puntamento resterebbe fuori
    dalla ricerca e il punteggio non lo vedrebbe mai. Nessun conto lo direbbe: il candidato
    semplicemente non arriva."""
    from astrolog.spine import identify_geometry as geometry

    assert geometry.MIN_SEARCH_RADIUS_DEG >= score.SCALE_CAP_DEG


def test_the_two_answers_to_is_it_in_the_photo_use_the_same_metre():
    """L'altra coppia che vive in moduli diversi e deve restare unita: `overlaps_frame` decide
    chi resta in gara, `centering_term` quanto premio prende, e tutti e due misurano con
    `campo + raggio dell'oggetto`. Se una delle due formule cambia si separano **in silenzio**:
    un candidato scartato dal filtro avrebbe ancora preso centratura, o uno tenuto in gara
    entrerebbe con premio zero e con lui a zero il premio di luminosita', che si moltiplica.

    Dove il raggio non si sa la regola non vale, ed e' voluto: li' `overlaps_frame` si astiene
    apposta -- non si scarta un candidato per un dato che manca a noi."""
    from astrolog.spine import identify_geometry as geometry

    for fov in (0.05, 0.2, 0.694, 3.0):
        for size in (0.5, 7.74, 177.83, 400.0):
            metro = fov + size / 2.0 / 60.0
            for sep in (0.0, metro / 2.0, metro * 0.999, metro * 1.001, metro + 1.0):
                in_gara = geometry.overlaps_frame(sep, size, fov)
                premio = score.centering_term(sep, fov, size)
                assert in_gara is (premio > 0.0), f"fov={fov} size={size} sep={sep}"
            # il bordo esatto: si resta in gara, ma di centratura non ne resta piu'
            assert geometry.overlaps_frame(metro, size, fov) is True
            assert score.centering_term(metro, fov, size) == 0.0


def test_the_catalogue_a_designation_comes_from_counts():
    """Messier e Caldwell sono cataloghi di oggetti che si fotografano; LBN e Ced raccolgono
    anche nebulosette che nessuno cerca. A parita' di geometria, il catalogo curato vince."""
    assert score.catalog_priority("M 31") > score.catalog_priority("NGC 224")
    assert score.catalog_priority("NGC 224") > score.catalog_priority("Ced 76")
    # il valore, non la costante: con un default alto un catalogo sconosciuto pareggerebbe
    # Messier, e sono 2.101 voci a prenderlo (PK, WR, Arp, Mel, HCG)
    assert score.catalog_priority("roba a caso") == 0.2
    assert score.catalog_priority("NGC 224") > score.CATALOG_PRIORITY_DEFAULT


# --- quando non si puo' decidere ------------------------------------------------------------


def test_two_separate_objects_with_close_scores_are_ambiguous():
    """M 81 e M 82 stanno a 0,61 gradi e in un campo largo ci stanno tutte e due: quale sia il
    soggetto lo sa solo chi ha scattato. Qui l'app non tira a indovinare, chiede."""
    m81 = {"name": "M 81", "sep_deg": 0.30, "size_major_arcmin": 21.63, "magnitude": 6.92}
    m82 = {"name": "M 82", "sep_deg": 0.32, "size_major_arcmin": 10.99, "magnitude": 8.3}
    assert score.is_ambiguous(m81, m82, separation_deg=0.6148) is True


def test_the_same_subject_written_twice_is_not_ambiguous():
    """L'ammasso della Rosetta (C 50) e la sua nebulosa (NGC 2237) distano 0,28 gradi: sono lo
    stesso soggetto descritto due volte, non due bersagli che contendono. Chiedere qui sarebbe
    far lavorare l'utente per niente."""
    nebulosa = {"name": "NGC 2237", "sep_deg": 0.05, "size_major_arcmin": 80.0, "magnitude": 9.0}
    # la voce si chiama `NGC 2239`: `C 50` e' una sua sigla, non il suo nome, e la priorita'
    # di catalogo legge proprio quel campo
    ammasso = {"name": "NGC 2239", "sep_deg": 0.30, "size_major_arcmin": 9.3, "magnitude": 4.8}
    assert score.is_ambiguous(nebulosa, ammasso, separation_deg=0.2744) is False


def test_a_companion_inside_its_host_is_not_a_rival():
    """M 32 e' una nana **dentro** M 31: nelle pose di M 31 c'e' sempre, e chiedere ogni volta
    quale delle due sia il soggetto sarebbe rumore. Dista 0,4039 gradi, cioe' quattro millesimi
    oltre la soglia fissa che aveva `old/`: e' il caso che ha fatto sostituire quella soglia col
    raggio, che risponde alla stessa domanda e viene dal catalogo."""
    assert score.is_ambiguous(M31, M32, separation_deg=0.4039) is False
    assert score.AMBIGUOUS_SEPARATION_DEG < 0.4039  # la soglia fissa l'avrebbe mandato a conferma


def test_a_host_bigger_than_its_guest_is_not_a_rival_either():
    """Il caso di sopra al contrario, e viene da pose vere: 40 pose di NGC 7023 (l'Iris) hanno
    nel campo LDN 1174, la nube oscura che l'avvolge. E' **il primo a stare dentro il secondo**
    -- 0,1001 gradi fra i centri contro un raggio di 0,3059 -- e guardare solo il raggio del
    primo (0,0833) mandava a conferma tutte e quaranta. La domanda giusta e' "uno contiene
    l'altro?", e non ha un verso privilegiato."""
    iris = {"name": "NGC 7023", "sep_deg": 0.0008, "size_major_arcmin": 10.0, "magnitude": 6.8}
    nube = {"name": "LDN 1174", "sep_deg": 0.0996, "size_major_arcmin": 36.71, "magnitude": None}
    assert score.is_ambiguous(iris, nube, separation_deg=0.1001, fov_radius_deg=0.806) is False


def test_containment_far_from_the_frame_is_not_containment():
    """Il contenimento geometrico da solo dichiarerebbe "lo stesso soggetto" cose che stanno a
    gradi di distanza: nel catalogo vero **44 coppie**, e fra queste NGC 1977 (il Running Man)
    contro M 42, che sono due bersagli distinti che nessuno confonde. Un oggetto grande contiene
    tutto cio' che gli cade dentro, e "gli appartiene" e' un'altra domanda -- quella sta in coda.

    Percio' il contenimento vale solo se i due sono vicini **rispetto all'inquadratura**, e il
    metro viene dalla foto invece che da una soglia: NGC 1977 dista 0,5454 gradi da M 42 e la
    foto ha raggio 0,2043, quindi si chiede. Senza campo noto non si pretende: `overlaps_frame`
    fa lo stesso, non si scarta per un dato che manca a noi."""
    running = {"name": "NGC 1977", "sep_deg": 0.0, "size_major_arcmin": 10.2, "magnitude": None}
    m42 = {"name": "M 42", "sep_deg": 0.5453, "size_major_arcmin": 90.0, "magnitude": 4.0}
    assert score.is_ambiguous(running, m42, separation_deg=0.5454, fov_radius_deg=0.2043) is True
    # la stessa coppia in una foto larga abbastanza da contenerli tutti e due: uno dentro l'altro
    assert score.is_ambiguous(running, m42, separation_deg=0.5454, fov_radius_deg=1.5) is False


def test_without_a_size_the_old_fixed_threshold_still_answers():
    """Se non si sa la dimensione di **nessuno dei due**, il raggio non si puo' calcolare: si
    ricade sulla soglia fissa invece di lasciar passare tutto."""
    # due voci senza dimensione, a pari scarto dal puntamento: quanto distino **fra loro**
    # dipende da che angolo stanno, e con questi scarti va da 0,01 a 0,91 gradi
    uno = {"name": "Ced 76", "sep_deg": 0.45, "size_major_arcmin": None, "magnitude": None}
    altro = {"name": "Ced 77", "sep_deg": 0.46, "size_major_arcmin": None, "magnitude": None}
    assert score.is_ambiguous(uno, altro, separation_deg=0.9) is True  # due oggetti: si chiede
    assert score.is_ambiguous(uno, altro, separation_deg=0.2) is False  # a ridosso: uno solo
    # e la soglia fissa non e' una scorciatoia per saltare l'inquadratura: gli stessi due, in
    # una foto piu' stretta della loro distanza, tornano a essere due. Sono 6.254 voci su
    # 22.080 a non avere dimensione, ed e' il clutter che affolla proprio i campi stretti.
    assert score.is_ambiguous(uno, altro, separation_deg=0.2, fov_radius_deg=0.05) is True


def test_one_candidate_alone_is_never_ambiguous():
    assert score.is_ambiguous(M31, None, separation_deg=None) is False


def test_a_competitive_score_is_needed_and_not_just_two_distinct_objects():
    """L'ambiguita' vuole **tutte e due** le condizioni. Due oggetti ben separati ma con
    punteggi lontani non sono un dubbio: il primo ha vinto, e chiedere sarebbe far lavorare
    l'utente per niente. E' la soglia sul rapporto a dirlo, e senza di lei ogni campo affollato
    finirebbe a conferma."""
    grosso = {"name": "M 31", "sep_deg": 0.0, "size_major_arcmin": 177.83, "magnitude": 3.44}
    minuscolo = {"name": "LDN 1", "sep_deg": 1.5, "size_major_arcmin": 2.0, "magnitude": None}
    assert score.is_ambiguous(grosso, minuscolo, separation_deg=1.5, fov_radius_deg=2.0) is False

    rapporto = score.score_candidate(minuscolo, 2.0) / score.score_candidate(grosso, 2.0)
    assert rapporto < score.AMBIGUOUS_SCORE_RATIO  # e' proprio la soglia a decidere, qui

    quasi_pari = {"name": "NGC 224", "sep_deg": 0.1, "size_major_arcmin": 150.0, "magnitude": 3.6}
    assert score.is_ambiguous(grosso, quasi_pari, separation_deg=1.5, fov_radius_deg=2.0) is True
