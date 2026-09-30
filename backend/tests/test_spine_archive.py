"""La barra dell'Archivio: cercare, filtrare, ordinare.

Il banco ha il **catalogo vero** dentro, perche' meta' di cio' che si prova qui viene da li': la
costellazione di un oggetto, il catalogo a cui appartiene, e le designazioni con cui si puo'
cercare (`M 31` e `NGC 224` sono la stessa cosa). Un catalogo finto proverebbe le nostre query
contro i nostri dati, che e' un banco che si fa dire di si'.
"""

import pytest

from astrolog.spine import archive, objects
from conftest import ORDINE_OSTILE
from group_bench import filtro as nasce_filtro

ORA = "2026-09-22T12:00:00Z"


def oggetto(conn, nome, slug=None):
    """Un oggetto dell'archivio. Con `nome=None` **non ha nomi propri**: non e' un caso di scuola
    -- un oggetto di catalogo nasce cosi' quando la sigla era gia' di un altro (`spine/objects.py`)
    -- e il suo nome lo da' il catalogo."""
    riga = conn.execute(
        "INSERT INTO objects(catalog_slug, identity_confidence, created_at) VALUES(?, 'high', ?)",
        (slug, ORA),
    ).lastrowid
    if nome is not None:
        conn.execute(
            "INSERT INTO object_names(object_id, name, origin, is_primary)"
            " VALUES(?, ?, 'catalog', 1)",
            (riga, nome),
        )
    return riga


def posa(conn, oggetto_id, *, filtro=None, secondi=300.0):
    return conn.execute(
        "INSERT INTO frames(frame_hash, image_type, header_json, created_at, object_id,"
        " filter_id, exposure_s) VALUES(?, 'light', '[]', ?, ?, ?, ?)",
        (f"h{conn.total_changes}-{oggetto_id}", ORA, oggetto_id, filtro, secondi),
    ).lastrowid


def banco(conn):
    """Sei oggetti scelti per far lavorare tutte e tre le tendine e tutti e tre gli ordini: tre
    Messier (che in alfabetico nudo uscirebbero storti: `M 103` prima di `M 13`), uno NGC e uno IC
    in altre costellazioni, e uno che il catalogo non conosce. L'elenco di cio' che ne esce sta in
    `test_the_archive_is_sorted_by_name_and_a_name_is_catalogue_then_number`."""
    ha, lum = nasce_filtro(conn, "Ha 3nm", "ha"), nasce_filtro(conn, "Lum", "l")
    pezzi = {
        "M 31": oggetto(conn, "M 31", "m-31"),
        "M 13": oggetto(conn, "M 13", "m-13"),
        # il caso che separa l'alfabeto dal numero: in alfabetico nudo `M 103` viene **prima** di
        # `M 13`. Senza di lui la prova dell'ordine passava anche togliendo il `CAST`.
        "M 103": oggetto(conn, "M 103", "m-103"),
        "NGC 7000": oggetto(conn, "NGC 7000", "ngc-7000"),
        "Il campo dietro casa": oggetto(conn, "Il campo dietro casa"),
        # senza nomi propri: c'e' e si conta, ma nessuna riga di `object_names` lo nomina
        "IC 1396": oggetto(conn, None, "ic-1396"),
    }
    # le ore: NGC 7000 il doppio di M 31, M 13 il meno; i frame vanno all'incontrario per M 13,
    # cosi' "per ore" e "per frame" non danno lo stesso elenco per caso
    for _ in range(4):
        posa(conn, pezzi["NGC 7000"], filtro=ha, secondi=600.0)
    for _ in range(4):
        posa(conn, pezzi["M 31"], filtro=lum, secondi=300.0)
    for _ in range(6):
        posa(conn, pezzi["M 13"], filtro=lum, secondi=60.0)
    posa(conn, pezzi["Il campo dietro casa"], secondi=30.0)
    return pezzi


def nomi(righe):
    """Come la pagina li chiama: il nome proprio se c'e', se no quello del catalogo. Si legge dalla
    casa dei nomi e non dalla colonna, o la prova non guarderebbe cio' che l'utente vede."""
    return [objects.display_name(r) for r in righe]


def test_the_archive_is_sorted_by_name_and_a_name_is_catalogue_then_number(archivio):
    """**L'Archivio e' un inventario** (Marco, 22/9/2026: *"la parte delle riprese con le date
    avviene gia' con le notti"*), quindi si apre in ordine di nome. Ma per nome non vuol dire
    l'alfabeto nudo: li' `M 13` finirebbe dopo `M 103` e nessuno riconoscerebbe l'ordine. Si legge
    catalogo e poi **numero**, e chi un catalogo non ce l'ha va in fondo."""
    banco(archivio)

    righe, _ = archive.page(archivio, limit=50, offset=0)

    assert nomi(righe) == ["IC 1396", "M 13", "M 31", "M 103", "NGC 7000", "Il campo dietro casa"]


def test_by_hours_and_by_frames_are_two_different_orders(archivio):
    """Due ordini diversi sugli stessi oggetti: se fossero lo stesso elenco, uno dei due bottoni
    non servirebbe a niente e nessuno se ne accorgerebbe."""
    banco(archivio)

    per_ore, _ = archive.page(archivio, limit=50, offset=0, sort="hours")
    per_frame, _ = archive.page(archivio, limit=50, offset=0, sort="frames")

    assert nomi(per_ore)[:3] == ["NGC 7000", "M 31", "M 13"]
    assert nomi(per_frame)[:3] == ["M 13", "NGC 7000", "M 31"]


@pytest.mark.parametrize("ordine", ["hours", "frames"])
def test_two_objects_that_tie_do_not_shuffle_between_pages(archivio, ordine):
    """Due oggetti a pari merito, una pagina per volta: senza un ultimo criterio che non pareggia
    mai, SQLite e' libero di darli in ordine diverso alle due domande, e la seconda pagina
    ripeterebbe la riga della prima o ne salterebbe una.

    Per ore e per frame il pareggio e' il caso normale -- due serate uguali. **Per nome no**: un
    nome appartiene a un oggetto solo (indice globale in `schema.sql`) e una designazione a una
    voce sola, quindi li' due righe non possono pareggiare, e l'ordine si prova altrove.

    Questa prova da sola **non basta**, e il perche' vale la riga: togliendo `o.id` resta verde,
    perche' SQLite sceglie lo stesso piano per le due domande e finisce per dare lo stesso ordine.
    L'assenza del criterio finale e' una libreta' che oggi non usa -- quella la guarda la prova
    qui sotto, che legge la regola invece dell'effetto."""
    gemelli = [oggetto(archivio, "Il campo grande"), oggetto(archivio, "Il campo piccolo")]
    for riga in gemelli:
        posa(archivio, riga, secondi=300.0)

    prima, _ = archive.page(archivio, limit=1, offset=0, sort=ordine)
    seconda, _ = archive.page(archivio, limit=1, offset=1, sort=ordine)

    assert {prima[0]["id"], seconda[0]["id"]} == set(gemelli)


def test_every_order_ends_with_something_that_never_ties():
    """Ogni ordine chiude con la chiave della riga, che non si ripete mai: una riga e' un oggetto
    o un mosaico, e nessuno dei due ha la chiave dell'altro. Senza, a pari merito SQLite e'
    **libero** di dare le righe come vuole, e due pagine consecutive potrebbero ripetere una riga o
    saltarne una: oggi non succede perche' il piano e' lo stesso, domani basta un indice nuovo."""
    for chiave, ordine in archive.ORDINI.items():
        assert ordine.rstrip().endswith("r.chiave"), chiave


def test_the_sort_is_a_key_from_a_closed_list(archivio):
    """Cio' che arriva da fuori non diventa un pezzo di `ORDER BY`: e' una chiave di un elenco
    chiuso. Una funzione che si fa passare l'ordinamento da fuori e' una porta aperta."""
    with pytest.raises(KeyError):
        archive.page(archivio, limit=50, offset=0, sort=ORDINE_OSTILE)


def test_the_route_and_the_spine_know_the_same_three_orders():
    """Gli ordini sono un elenco chiuso scritto **due volte**: il `Literal` della rotta, che li
    rifiuta prima di arrivare qui, e le chiavi di `ORDINI`, che li traducono in SQL. Il frontend
    la sua copia non ce l'ha -- legge l'OpenAPI -- ma il backend si', e una voce aggiunta al
    `Literal` e dimenticata qui sarebbe un `KeyError` non catturato, cioe' un 500 in faccia
    all'utente. Questa prova e' il legame."""
    from typing import get_args

    from astrolog.api.archive import Sort

    assert set(get_args(Sort)) == set(archive.ORDINI)


@pytest.mark.parametrize("scritto", ["m31", "M 31", "  M31  ", "ngc 224", "224"])
def test_you_find_an_object_by_any_name_it_is_known_by(archivio, scritto):
    """`M 31` e `NGC 224` sono la stessa galassia, e chi cerca scrive come gli viene. Si guardano
    i nomi dell'oggetto **e** le designazioni del catalogo: cercare solo nel nome che la pagina
    mostra vorrebbe dire non trovare la propria galassia scrivendone l'altra sigla."""
    banco(archivio)

    righe, quanti = archive.page(archivio, limit=50, offset=0, q=scritto)

    assert nomi(righe) == ["M 31"]
    assert quanti == 1


def test_the_wildcards_of_like_are_not_wildcards_for_who_types_them(archivio):
    """`%` e `_` sono i jolly di `LIKE`. Senza scudo, cercare `_` da solo tornerebbe **tutto**
    l'archivio e `100%` qualunque nome che comincia per 100: chi scrive quei segni sta cercando
    quei segni, e una ricerca che ignora meta' di cio' che hai battuto e' peggio di una che non
    trova niente, perche' sembra che abbia funzionato."""
    banco(archivio)
    oggetto(archivio, "Campo 100% buio")

    righe, _ = archive.page(archivio, limit=50, offset=0, q="100%")
    solo_trattino, _ = archive.page(archivio, limit=50, offset=0, q="_")

    assert nomi(righe) == ["Campo 100% buio"]
    assert solo_trattino == []


def test_the_order_by_name_does_not_read_bytes(archivio):
    """Senza `COLLATE NOCASE` si ordina sui byte: `vdB` finirebbe **dopo** `WR`, e ogni nome che
    l'utente scrive in minuscolo dopo tutti quelli in maiuscolo. Chi da' i nomi a mano vedrebbe un
    archivio che sembra rotto, e il banco di prima non se ne accorgeva perche' aveva un solo
    oggetto senza catalogo e tutte sigle maiuscole."""
    oggetto(archivio, "WR 134", "wr-134")
    oggetto(archivio, "vdB 141", "vdb-141")
    # le casse **invertite**: sui byte `Zeta` verrebbe prima di `alfa`, perche' tutte le
    # maiuscole precedono tutte le minuscole. Con due nomi della stessa cassa la prova non
    # guarderebbe la colonna del nome, solo quella del catalogo.
    oggetto(archivio, "Zeta del campo")
    oggetto(archivio, "alfa del campo")

    righe, _ = archive.page(archivio, limit=50, offset=0)

    assert nomi(righe) == ["vdB 141", "WR 134", "alfa del campo", "Zeta del campo"]


def test_a_name_with_an_accented_capital_can_be_found(archivio):
    """La cassa la piega SQLite, e `LOWER()` non tocca l'Unicode. Piegandola in Python con
    `.lower()` -- che invece lo tocca -- i due lati non si incontravano piu': un nome con una
    maiuscola accentata diventava **irraggiungibile**, nemmeno scrivendolo identico. Non e' un
    caso di laboratorio: i nomi li scrive chi ha fatto il file, nella sua lingua.

    Il limite che resta e' dichiarato: la cassa si piega solo sull'ASCII, quindi una accentata
    minuscola non trova la sua maiuscola -- ma almeno la stessa grafia funziona, dai due lati.

    Il nome si compone **col codice**, non si incolla: un carattere incollato in un file di prova
    passa inosservato in un diff e cambia significato con la codifica di chi lo riapre."""
    banco(archivio)
    accentato = chr(0xC9) + "psilon Lyrae"  # la E maiuscola accentata, scritta col codice
    oggetto(archivio, accentato)

    identico, _ = archive.page(archivio, limit=50, offset=0, q=accentato)
    pezzo, _ = archive.page(archivio, limit=50, offset=0, q="psilon Lyrae")

    assert nomi(identico) == [accentato]
    assert nomi(pezzo) == [accentato]


def test_searching_for_nothing_is_not_searching(archivio):
    """Uno spazio, o il campo svuotato, non e' una ricerca che non trova niente: e' nessuna
    ricerca. Altrimenti cancellare cio' che si era scritto lascerebbe l'archivio vuoto."""
    banco(archivio)

    righe, _ = archive.page(archivio, limit=50, offset=0, q="   ")

    # tutti e sei, **compreso quello senza nomi propri**: trattare il vuoto come una ricerca che
    # non trova niente lo farebbe sparire, ed e' proprio l'oggetto piu' difficile da accorgersene
    assert len(righe) == 6


def test_you_can_narrow_down_to_one_catalogue(archivio):
    """Il catalogo di un oggetto e' quello della sua designazione principale (`catalog_names`),
    non una parola dello slug: gli slug li scriviamo noi, le designazioni le porta il catalogo."""
    banco(archivio)

    righe, quanti = archive.page(archivio, limit=50, offset=0, catalog="M")

    assert nomi(righe) == ["M 13", "M 31", "M 103"]
    assert quanti == 3


def test_you_can_narrow_down_to_one_constellation(archivio):
    """La costellazione viene dal catalogo, col codice IAU. Un oggetto che il catalogo non conosce
    non ne ha, e non deve comparire sotto nessuna."""
    banco(archivio)

    righe, _ = archive.page(archivio, limit=50, offset=0, constellation="Cyg")

    assert nomi(righe) == ["NGC 7000"]


def test_you_can_narrow_down_to_one_filter(archivio):
    """ "Cosa ho ripreso in Ha" e' la domanda per cui questa tendina esiste. Si guarda **se almeno
    una posa** di quell'oggetto ha quel filtro, non quale sia il filtro dominante."""
    banco(archivio)

    righe, _ = archive.page(archivio, limit=50, offset=0, filter_name="Ha 3nm")

    assert nomi(righe) == ["NGC 7000"]


def test_the_count_is_what_you_found_not_what_you_have(archivio):
    """Con un filtro acceso, dire quanti ne hai **in tutto** sarebbe un numero che mente: la
    conta e' quella delle righe che passano, ed e' anche cio' che dice se c'e' un'altra pagina."""
    banco(archivio)

    _, tutti = archive.page(archivio, limit=1, offset=0)
    _, stretti = archive.page(archivio, limit=1, offset=0, catalog="M")

    assert (tutti, stretti) == (6, 3)


def test_the_choices_are_only_what_the_archive_has(archivio):
    """Le tendine elencano cio' che **tu** hai, non cio' che il catalogo conosce: offrirgli tutto
    a chi ne usa tre e' una tendina che fa perdere tempo. E' la stessa regola delle ore per
    genere: per archivio, non per elenco fisso.

    Il "molte piu'" si **conta** qui invece di scriverlo a memoria in una frase."""
    banco(archivio)
    nel_catalogo = {
        "catalogs": archivio.execute(
            "SELECT COUNT(DISTINCT catalog) FROM catalog_names WHERE is_primary = 1"
        ).fetchone()[0],
        "constellations": archivio.execute(
            "SELECT COUNT(DISTINCT constellation) FROM catalog_entries"
        ).fetchone()[0],
    }

    scelte = archive.choices(archivio)

    assert scelte["catalogs"] == ["IC", "M", "NGC"]
    assert scelte["constellations"] == ["And", "Cas", "Cep", "Cyg", "Her"]
    assert scelte["filters"] == ["Ha 3nm", "Lum"]
    for dove, quante in nel_catalogo.items():
        assert quante > len(scelte[dove]) * 3, (
            f"il catalogo ha {quante} {dove}: se fossero pochi come quelli dell'archivio, questa"
            " prova non guarderebbe niente"
        )


def test_the_dropdowns_are_sorted_like_the_rows(archivio):
    """Le tendine e le righe ordinano la **stessa cosa**: se una leggesse i byte e l'altra no,
    `vdB` uscirebbe prima di `WR` nell'elenco e dopo nella tendina, sulla stessa pagina. E i nomi
    dei filtri li scrive l'utente nell'header: li' non e' un'ipotesi, capita."""
    oggetto(archivio, "WR 134", "wr-134")
    oggetto(archivio, "vdB 141", "vdb-141")
    nasce_filtro(archivio, "ha stretto", "ha")
    zeta = nasce_filtro(archivio, "Zenith", "l")
    posa(archivio, oggetto(archivio, "Un campo"), filtro=zeta)
    posa(archivio, oggetto(archivio, "Un altro"), filtro=nasce_filtro(archivio, "b largo", "b"))

    scelte = archive.choices(archivio)

    assert scelte["catalogs"] == ["vdB", "WR"]
    assert scelte["filters"] == ["b largo", "Zenith"]


def test_an_archive_with_nothing_in_it_offers_no_choices(archivio):
    """A mani vuote le tendine sono vuote, non piene di tutto il catalogo: chi ha appena
    installato l'app non ha ancora nessun catalogo e nessuna costellazione."""
    assert archive.choices(archivio) == {
        "catalogs": [],
        "constellations": [],
        "filters": [],
        "mosaics": False,
    }
