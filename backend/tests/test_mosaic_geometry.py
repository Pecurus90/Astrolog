"""Due rettangoli risolti a confronto: si sovrappongono, uno contiene l'altro, o sono lontani.

E' la domanda che pone il contratto del mosaico, in `docs/domini/mosaico.md`: due pannelli sono
*"rettangoli che si toccano o si sovrappongono in parte, e nessuno contiene l'altro"*.

Il contenimento e' il discriminante -- la stessa ripresa rifatta, e il dithering, si
contengono a vicenda -- quindi qui si prova che i tre esiti si distinguono davvero.

Le coordinate sono vere: IC 405 dal catalogo (79.122833, 34.356167), il mosaico di quattro
pannelli del contratto. I centri dei pannelli escono dalla proiezione
dell'app, non da una sottrazione a mano: a questa declinazione uno scarto di mezzo grado in
ascensione retta porta anche 0,0015 gradi di nord, e un banco che lo ignorasse proverebbe
l'aritmetica invece della decisione.
"""

from astrolog.spine import mosaic_geometry as geom

# Il pannello di partenza: IC 405 e' 50 arcmin, il campo e' piu' stretto -- e' per questo che
# serve un mosaico.
IC405 = (79.122833, 34.356167)
LARGO, ALTO = 0.6, 0.4


def campo(ra, dec, width=LARGO, height=ALTO, rotation=0.0):
    """Un cielo misurato come lo scrive `solve` in `frame_wcs`."""
    return {
        "ra_deg": ra,
        "dec_deg": dec,
        "width_deg": width,
        "height_deg": height,
        "rotation_deg": rotation,
    }


# I centri misurati con la proiezione vera, dal centro di IC 405:
#   est +0.5000 -> i mezzi lati sommano 0.60, quindi si sovrappongono
#   est +0.6200 -> appena oltre: disgiunti
#   est +3.0021 -> lontani
ACCANTO = campo(79.728493, 34.356167)
APPENA_FUORI = campo(79.873852, 34.356167)
LONTANO = campo(82.756794, 34.356167)
PRIMO = campo(*IC405)


def test_two_panels_side_by_side_overlap_without_containing_each_other():
    """Il caso per cui il mosaico esiste: due inquadrature affiancate che condividono una
    striscia. Nessuna delle due contiene l'altra, quindi sono pannelli."""
    assert geom.overlap(PRIMO, ACCANTO) == "partial"


def test_the_same_framing_shot_twice_is_nested_and_never_a_mosaic():
    """La stessa ripresa rifatta -- e il dithering, che sposta di pochi secondi d'arco -- cade
    dentro il campo di prima: uno contiene l'altro, e non e' un mosaico. E' il discriminante che
    sostituisce la soglia di sovrapposizione che abbiamo deciso di non avere."""
    assert geom.overlap(PRIMO, campo(*IC405, width=0.3, height=0.2)) == "nested"


def test_a_field_just_past_the_edge_is_disjoint():
    """Il caso al pelo, che distingue un confronto vero da uno approssimativo: 0,62 gradi di
    scarto contro 0,60 di mezzi lati sommati. Si sfiorano e non si toccano."""
    assert geom.overlap(PRIMO, APPENA_FUORI) == "disjoint"


def test_two_far_fields_are_disjoint():
    assert geom.overlap(PRIMO, LONTANO) == "disjoint"


def test_a_rotated_panel_is_compared_in_its_own_axes():
    """La rotazione conta, e da sola cambia la risposta: lo stesso centro, girato di 90 gradi,
    presenta verso il vicino il lato corto invece del lungo.

    Il centro e' a est di 0,55 gradi (misurato). Dritto, i mezzi lati sommano 0,60 e i due campi
    si sovrappongono; girato, sommano 0,50 e non si toccano piu'. Un confronto che ignorasse la
    rotazione direbbe la stessa cosa nei due casi."""
    dritto = campo(79.789059, 34.356167)
    girato = campo(79.789059, 34.356167, rotation=90.0)
    assert geom.overlap(PRIMO, dritto) == "partial"
    assert geom.overlap(PRIMO, girato) == "disjoint"


def test_an_oblique_rotation_counts_with_both_its_terms():
    """A rotazione **obliqua** un rettangolo sporge di quanto dicono tutti e due i suoi lati.

    Con 30 gradi il campo vicino sporge verso A di 0,3598 gradi (il lato lungo per il coseno
    **piu'** il lato corto per il seno), e il confine cade a 0,6598. Il centro e' a 0,55: si
    toccano. Sbagliando il segno fra i due termini il confine scenderebbe a 0,4598 e la risposta
    sarebbe "lontani" -- e a 0 o 90 gradi quell'errore non si vedrebbe, perche' li' uno dei due
    termini e' sempre zero."""
    obliquo = campo(79.789059, 34.356167, rotation=30.0)
    assert geom.overlap(PRIMO, obliquo) == "partial"


def test_two_fields_separated_on_one_axis_only_are_disjoint():
    """Basta **un** asse che separi: due campi possono affiancarsi perfettamente in ascensione
    retta e non toccarsi lo stesso, perche' uno sta mezzo grado piu' a nord.

    Qui lo scarto e' 0,5000 gradi tutto in nord contro 0,40 di mezzi lati sommati -- separati --
    mentre in est e' 0,0000 contro 0,60 -- non separati. Chi pretendesse che a separare fossero
    tutti e due gli assi direbbe che questi due si sovrappongono."""
    piu_a_nord = campo(79.122833, 34.856167)
    assert geom.overlap(PRIMO, piu_a_nord) == "disjoint"


def test_it_is_the_difference_between_the_two_rotations_that_counts():
    """Fra due campi conta di quanto sono girati **l'uno rispetto all'altro**, non la somma.

    Qui e' il **primo** a essere ruotato, di 20 gradi, e il secondo no: lo scarto e' 0,30 in est
    e 0,6006 in nord, e i due non si toccano. Sommando le due rotazioni invece di sottrarle il
    conto direbbe che si sovrappongono -- e con un campo dritto l'errore non si vedrebbe, perche'
    li' somma e differenza sono lo stesso numero."""
    primo_ruotato = campo(*IC405, rotation=20.0)
    assert geom.overlap(primo_ruotato, campo(79.488869, 34.956167)) == "disjoint"


def test_one_axis_of_the_first_field_is_enough_to_separate():
    """Basta che **un** asse del primo campo separi. Scarto 0,6000 tutto in nord contro 0,20 di
    mezzo lato piu' quanto il vicino ruotato gli sporge incontro: separati su nord, non su est.

    Il secondo campo e' girato di 30 gradi apposta: con due campi dritti questo controllo e
    quello sugli assi del secondo diventano la stessa disuguaglianza, e uno coprirebbe l'altro."""
    girato = campo(79.122833, 34.956167, rotation=30.0)
    assert geom.overlap(PRIMO, girato) == "disjoint"


def test_one_axis_of_the_second_field_is_enough_too():
    """E vale anche al contrario: qui a separare sono gli assi del **secondo** campo, quello
    ruotato di 30 gradi, mentre quelli del primo da soli non basterebbero. Scarto 0,6000 in est e
    0,3022 in nord. Guardare gli assi di uno solo dei due lascerebbe passare questa coppia."""
    girato = campo(79.852246, 34.656167, rotation=30.0)
    assert geom.overlap(PRIMO, girato) == "disjoint"


def test_being_inside_on_one_axis_alone_is_not_containment():
    """Il contenimento vuole **tutti e due** gli assi. Due campi identici sfalsati di 0,1500 in
    nord stanno uno dentro l'altro in est e no in nord: sono due pannelli, non la stessa ripresa
    rifatta. Accontentarsi di un asse solo li dichiarerebbe "uno dentro l'altro" e il mosaico non
    nascerebbe."""
    sfalsato = campo(79.122833, 34.506167)
    assert geom.overlap(PRIMO, sfalsato) == "partial"


def test_the_offset_is_turned_the_right_way_into_the_other_axes():
    """Lo scarto si riscrive negli assi dell'altro campo girandolo **all'indietro** della sua
    rotazione. Qui lo scarto e' 0,3000 in est e 0,4506 in nord su un campo girato di 30 gradi: i
    due si toccano. Girandolo dalla parte sbagliata il conto direbbe che sono lontani."""
    girato = campo(79.488202, 34.806167, rotation=30.0)
    assert geom.overlap(PRIMO, girato) == "partial"


def test_a_smaller_field_pushed_sideways_is_not_contained():
    """Un campo piu' piccolo non e' "dentro" solo perche' e' piu' piccolo: conta **dove** sta.

    Il piccolo (0,3x0,2) e' spostato di 0,2000 gradi in est dentro il grande (0,6x0,4): il suo
    bordo esce, quindi si sovrappongono e basta. Il contenimento somma la sporgenza allo scarto
    (0,2000 + 0,15 = 0,35, oltre il mezzo lato di 0,30); **sottraendola** invece che sommandola
    il conto darebbe 0,05 e questa coppia verrebbe dichiarata "una dentro l'altra", cioe' la
    stessa ripresa rifatta -- e il mosaico non nascerebbe. Col piccolo nello stesso centro
    l'errore non si vedrebbe, perche' li' lo scarto e' zero.

    Si chiede nei due ordini: i rami "B dentro A" e "A dentro B" sono due, e uno solo non basta
    a provarli tutti e due."""
    piccolo = campo(79.365097, 34.356167, width=0.3, height=0.2)
    assert geom.overlap(PRIMO, piccolo) == "partial"
    assert geom.overlap(piccolo, PRIMO) == "partial"


def test_across_the_pole_only_the_true_projection_decides():
    """Vicino al polo la proiezione approssimata non sbaglia solo la misura: sbaglia la
    **direzione**.

    NGC 3172 sta a meno di un grado dal polo. Due campi puntati a mezzo giro di ascensione retta
    l'uno dall'altro stanno ai due lati del polo: lo scarto vero e' 1,8145 gradi tutto in
    **nord**, mentre la differenza per il coseno della declinazione lo dichiara 2,8491 gradi
    tutto in **est** -- il 57% in piu', e girato di novanta gradi. Con un campo di 2x2 gradi i
    due si toccano davvero; con l'approssimazione sarebbero lontani, e quel mosaico non
    nascerebbe mai. E' il caso che tiene onesta la scelta della proiezione."""
    polo = campo(176.808333, 89.093056, width=2.0, height=2.0)
    oltre = campo(356.808333, 89.093056, width=2.0, height=2.0)
    assert geom.overlap(polo, oltre) == "partial"


def test_without_the_rotation_it_answers_on_the_circle_instead_of_giving_up():
    """Lo schema dichiara che la rotazione puo' mancare a soluzione buona. Li' si sa quanto e'
    grande il campo ma non come era orientato: si usa il cerchio circoscritto, come fa gia'
    `identify_geometry`, invece di perdere il pannello. Sbagliare per eccesso costa una proposta
    rifiutata con un clic; escludere la posa costa un pannello perso in silenzio."""
    senza = dict(ACCANTO, rotation_deg=None)
    assert geom.overlap(PRIMO, senza) == "partial"


def test_a_field_without_sides_is_never_declared_far_away():
    """Un dato che manca a **noi** non allontana due campi. Senza i lati non si sa quanto e'
    grande l'inquadratura: dire "sono lontani" scarterebbe un pannello in silenzio, mentre dire
    che si sovrappongono al massimo costa una proposta da rifiutare con un clic."""
    senza_lati = {
        "ra_deg": 79.728493,
        "dec_deg": 34.356167,
        "width_deg": None,
        "height_deg": None,
        "rotation_deg": None,
    }
    assert geom.overlap(PRIMO, senza_lati) == "partial"


def test_without_the_sky_there_is_no_answer():
    """Una posa che il solver non ha risolto non si confronta con niente: `None`, che non e' ne'
    "si sovrappongono" ne' "sono lontani". Chi chiama deve poterlo distinguere."""
    assert geom.overlap(PRIMO, campo(None, None)) is None
    assert geom.overlap(campo(None, None), PRIMO) is None


# --- lo stesso puntamento, o due -----------------------------------------------------------
#
# Il confronto fra rettangoli da solo NON basta a dire "e' la stessa inquadratura rifatta": due
# pose dithered sono due rettangoli uguali appena sfalsati, cioe' `partial`, esattamente come due
# pannelli. Serve la vicinanza dei centri, e la misura e' **relativa al campo**.

DITHERATA = campo(79.127880, 34.356167)  # 0,0042 gradi dal primo: l'1,16% della mezza diagonale
ACCANTO_UN_PANNELLO = campo(79.728493, 34.356167)  # 0,5000 gradi: il 138,7%


def test_dithering_does_not_open_a_second_pointing():
    """Il dithering sposta la posa di pochi secondi d'arco per battere i difetti del sensore: e'
    la stessa inquadratura, e spezzarla in due pannelli inventerebbe un mosaico dal nulla.

    La documentazione di N.I.N.A. consiglia di spostarsi *"di circa 10 pixel della camera di
    ripresa"*, col suo esempio di 15 secondi d'arco: qui sono 0,0042 gradi, l'1,16% della mezza
    diagonale del campo."""
    assert geom.same_pointing(PRIMO, DITHERATA) is True


def test_two_panels_are_two_pointings():
    """Mezzo grado di scarto su questo campo e' il 138,7% della mezza diagonale: sono due
    inquadrature distinte, cioe' i due pannelli che il mosaico deve raccogliere."""
    assert geom.same_pointing(PRIMO, ACCANTO_UN_PANNELLO) is False


def test_the_same_gap_in_the_sky_depends_on_how_wide_the_field_is():
    """La misura e' **relativa al campo**, e questa e' la riga che lo prova.

    Lo stesso identico scarto di cielo -- mezzo grado -- e' un pannello nuovo su una focale
    lunga (il 138,7% della mezza diagonale) e la stessa inquadratura su un campo di 4x3 gradi
    (il 20,0%). Una soglia scritta in gradi non potrebbe dire tutte e due le cose, e sarebbe
    tarata sull'attrezzatura di chi l'ha scelta."""
    largo = campo(*IC405, width=4.0, height=3.0)
    largo_accanto = campo(79.728493, 34.356167, width=4.0, height=3.0)
    assert geom.same_pointing(largo, largo_accanto) is True
    assert geom.same_pointing(PRIMO, ACCANTO_UN_PANNELLO) is False


def test_between_two_different_fields_the_smaller_one_decides():
    """Fra due campi di misura diversa pesa il piu' piccolo: uno scarto che sul campo largo e'
    niente puo' essere un pannello intero su quello stretto, e guardare il grande unirebbe in
    silenzio due inquadrature distinte.

    Mezzo grado e' il 20,0% della mezza diagonale di un campo 4x3 e il 138,7% di uno 0,6x0,4."""
    largo = campo(*IC405, width=4.0, height=3.0)
    assert geom.same_pointing(largo, ACCANTO_UN_PANNELLO) is False


def test_without_the_field_size_two_poses_are_not_declared_the_same_pointing():
    """Senza i lati non si sa quanto e' grande l'inquadratura, quindi non si puo' dire "e' la
    stessa": dirlo unirebbe in silenzio due pannelli veri. Restano due puntamenti, e a decidere
    se si toccano sara' il confronto fra i campi -- che li' risponde "si sovrappongono" e manda
    la coppia all'utente invece di risolverla da sola.

    Senza cielo non c'e' risposta affatto: `None`, che non e' ne' si' ne' no."""
    senza_lati = dict(DITHERATA, width_deg=None, height_deg=None, rotation_deg=None)
    assert geom.same_pointing(PRIMO, senza_lati) is False
    assert geom.same_pointing(PRIMO, campo(None, None)) is None


def test_the_other_side_of_the_sky_is_never_the_same_pointing():
    """Due pose negli emisferi opposti non hanno nemmeno un piano tangente in comune: la
    proiezione non ci arriva e non torna nessuno scarto da misurare. Li' la risposta e' **no**, e
    non "non lo so": lasciare la coppia in sospeso la manderebbe a chiedere all'utente se mezzo
    cielo di distanza sia la stessa inquadratura.

    L'antipodo di IC 405 e' mezzo giro di ascensione retta con la declinazione cambiata di segno.
    Non e' un caso al limite: a 95 e a 110 gradi la proiezione uno scarto lo da' ancora."""
    antipodo = campo(259.122833, -34.356167)
    assert geom.same_pointing(PRIMO, antipodo) is False


def test_the_answer_does_not_depend_on_the_order():
    """La relazione fra due campi e' simmetrica: chiedere "A con B" o "B con A" da' la stessa
    risposta. Senza, il risultato dipenderebbe da come la corsa scorre le pose."""
    for altro in (ACCANTO, APPENA_FUORI, LONTANO, campo(*IC405, width=0.3, height=0.2)):
        assert geom.overlap(PRIMO, altro) == geom.overlap(altro, PRIMO), altro
