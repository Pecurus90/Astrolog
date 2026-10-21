"""Il client SIMBAD: cosa chiede, come riaggancia le risposte, e cosa fa quando qualcosa va
storto.

Vincolo di questi test: **non toccano la rete**. Il trasporto si passa come argomento e qui
si passa un finto -- come `fetch=` in `place.py` e `run=` in `astap.py`. Un test che chiamasse
il servizio vero fallirebbe il giorno che CDS cambia una colonna, e non girerebbe in aereo.
"""

import pytest

import simbad


def finto(risposta, ricorda=None):
    """Un SIMBAD finto: risponde una tabella e ricorda le query ricevute."""

    def posta(url, query, timeout_s):
        if ricorda is not None:
            ricorda.append(query)
        if isinstance(risposta, Exception):
            raise risposta
        return risposta

    return posta


def tabella(colonne, righe):
    """La forma con cui TAP risponde in JSON: le colonne dichiarate, poi i dati."""
    return {"metadata": [{"name": c} for c in colonne], "data": righe}


# --- cosa si chiede ------------------------------------------------------------------------


def test_a_batch_asks_all_identifiers_at_once():
    """Su quattromila voci, una richiesta per oggetto sarebbe quattromila richieste: la
    politica del servizio non le gradisce e nessuno le aspetterebbe."""
    viste = []
    simbad.misure(["M 31", "M 42", "NGC 224"], posta=finto(tabella([], []), viste))
    assert len(viste) == 1
    for sigla in ("M 31", "M 42", "NGC 224"):
        assert f"'{sigla}'" in viste[0]


def test_an_apostrophe_in_the_name_does_not_break_the_query():
    """Gli apici si raddoppiano: e' l'escaping SQL, e senza di lui un nome con l'apice
    romperebbe la stringa -- o peggio, la riscriverebbe."""
    viste = []
    simbad.misure(["Barnard's Loop"], posta=finto(tabella([], []), viste))
    assert "'Barnard''s Loop'" in viste[0]


def test_v_band_magnitude_and_dimensions_are_requested():
    """Sono i due buchi che questa raccolta esiste per riempire. La V e non la B: e' la banda
    con cui si giudica un oggetto."""
    viste = []
    simbad.misure(["M 31"], posta=finto(tabella([], []), viste))
    q = viste[0]
    assert "galdim_majaxis" in q and "galdim_minaxis" in q
    assert "flux" in q and "'V'" in q


def test_names_are_requested_one_catalog_at_a_time():
    """SIMBAD tiene i nomi propri come identificatori `NAME ...`: una query per catalogo li
    prende tutti. E' il motivo per cui riempire 21.000 nomi costa 18 richieste."""
    viste = []
    simbad.nomi("NGC", posta=finto(tabella([], []), viste))
    assert "NGC %" in viste[0] and "NAME %" in viste[0]


# --- come si riaggancia --------------------------------------------------------------------


def test_the_answer_rejoins_the_designation_asked_not_the_simbad_one():
    """Il finto risponde con la grafia VERA di SIMBAD (`ACO  1136`), che non e' quella che
    abbiamo in catalogo (`Abell 1136`) -- cambia il nome del catalogo, non solo la spaziatura.
    Se il riaggancio non riportasse indietro la nostra, il dato finirebbe in un cassetto che
    nessuno apre, e la voce risulterebbe "sconosciuta a SIMBAD"."""
    risposta = tabella(
        ["id", "main_id", "galdim_majaxis", "galdim_minaxis", "flux"],
        [["ACO  1136", "ACO  1136", 12.0, 10.0, 15.5]],
    )
    fuori = simbad.misure(["Abell 1136"], posta=finto(risposta))
    assert set(fuori) == {"Abell 1136"}
    assert fuori["Abell 1136"]["size_major_arcmin"] == 12.0


def test_every_spacing_is_requested_because_simbad_aligns_the_number():
    """`M   1`, `M  11`, `M 110`: il numero sta in un campo a larghezza fissa che cambia col
    catalogo e non e' documentato. Chiedere con la nostra grafia non trova NIENTE, in silenzio.
    Si chiedono tutte le forme: e' una lista piu' lunga, non una richiesta in piu'."""
    viste = []
    simbad.misure(["M 11"], posta=finto(tabella([], []), viste))
    assert "'M  11'" in viste[0] and "'M   11'" in viste[0]
    assert len(viste) == 1  # sempre una richiesta sola


def test_catalogs_that_simbad_calls_another_way():
    """Misurato: chiedendo `Abell 1136` non risponde nessuno, chiedendo `ACO  1136` si'."""
    assert any(f.startswith("ACO") for f in simbad.forme("Abell 1136"))
    assert any(f.startswith("Barnard") for f in simbad.forme("B 33"))
    assert any(f.startswith("APG") for f in simbad.forme("Arp 168"))
    assert all(f.startswith("NGC") for f in simbad.forme("NGC 224"))


def test_the_proper_name_loses_the_simbad_prefix():
    """Negli identificatori il nome vero e' preceduto da `NAME `: cosi' com'e' finirebbe a
    schermo come "NAME Rosette Nebula"."""
    risposta = tabella(["catcode", "proper"], [["NGC 2237", "NAME Rosette Nebula"]])
    assert simbad.nomi("NGC", posta=finto(risposta)) == {"NGC 2237": "Rosette Nebula"}


# --- quando qualcosa non c'e' o non va -----------------------------------------------------


def test_an_entry_simbad_does_not_know_is_not_an_error():
    """Chi manca dalla risposta non e' un guasto: e' una voce che il servizio non conosce, e
    il chiamante deve poterselo ricordare per non richiederla ogni volta."""
    risposta = tabella(
        ["id", "main_id", "galdim_majaxis", "galdim_minaxis", "flux"],
        [["M 31", "M  31", 199.5, 70.8, 3.44]],
    )
    fuori = simbad.misure(["M 31", "LDN 9999"], posta=finto(risposta))
    assert set(fuori) == {"M 31"}


def test_a_network_failure_is_never_taken_for_a_missing_entry():
    """Registrare un guasto di rete come "SIMBAD non lo conosce" vorrebbe dire non chiederlo
    mai piu': l'errore propaga, e chi chiama decide se ritentare."""
    for guasto in (TimeoutError("scaduto"), OSError("rete giu'")):
        with pytest.raises(simbad.SimbadNonRispondeError):
            simbad.misure(["M 31"], posta=finto(guasto))


def test_an_unreadable_answer_is_a_failure_not_an_empty_result():
    """Un servizio che risponde HTML o JSON storto non sta dicendo "non lo conosco"."""
    for storta in ("<html>errore</html>", {"nessuna": "colonna"}, None):
        with pytest.raises(simbad.SimbadNonRispondeError):
            simbad.misure(["M 31"], posta=finto(storta))


def test_absent_values_stay_empty_never_zero():
    """Una dimensione a zero sarebbe un oggetto puntiforme, e una magnitudine a zero un
    oggetto luminosissimo: due bugie al posto di "non lo so"."""
    risposta = tabella(
        ["id", "main_id", "galdim_majaxis", "galdim_minaxis", "flux"],
        [["M 31", "M  31", None, None, None]],
    )
    voce = simbad.misure(["M 31"], posta=finto(risposta))["M 31"]
    assert voce["size_major_arcmin"] is None and voce["magnitude"] is None


# --- la cortesia verso il servizio ---------------------------------------------------------


def test_it_waits_between_batches():
    """Il servizio e' pubblico e gratuito: si va piano. La pausa si passa da fuori, cosi' i
    test non aspettano davvero."""
    attese = []
    sigle = [f"NGC {i}" for i in range(simbad.LOTTO * 2 + 1)]
    simbad.misure(sigle, posta=finto(tabella([], [])), pausa=attese.append)
    assert len(attese) == 2 and all(a == simbad.PAUSA_S for a in attese)


def test_a_batch_does_not_exceed_the_declared_size():
    """Il lotto si conta in SIGLE, non in stringhe: ognuna ne genera cinque, e un lotto troppo
    grosso farebbe una query che il servizio rifiuta."""
    viste = []
    sigle = [f"NGC {i}" for i in range(simbad.LOTTO + 5)]
    simbad.misure(sigle, posta=finto(tabella([], []), viste), pausa=lambda _: None)
    assert len(viste) == 2
    stringhe = viste[0].count("'NGC")
    assert stringhe == simbad.LOTTO * len(simbad.SPAZI)


def test_the_caller_identifies_itself():
    """La politica del servizio lo pretende, e un client anonimo viene bloccato."""
    assert simbad.USER_AGENT.startswith("AstroLog/") and "http" in simbad.USER_AGENT


def test_an_identifier_we_did_not_ask_for_is_dropped():
    """SIMBAD puo' rispondere con un identificatore diverso da quelli chiesti (un alias
    dell'oggetto). Accettarlo vorrebbe dire attribuire il dato di un oggetto a un altro, che
    e' il guasto peggiore che questa raccolta possa fare."""
    risposta = tabella(
        ["id", "main_id", "galdim_majaxis", "galdim_minaxis", "flux"],
        [["APG  10", "APG  10", 5.0, 4.0, 12.0], ["M  11", "M  11", 14.0, 14.0, 5.8]],
    )
    fuori = simbad.misure(["M 11"], posta=finto(risposta))
    assert set(fuori) == {"M 11"}
    assert fuori["M 11"]["magnitude"] == 5.8


def test_names_too_are_requested_with_the_name_simbad_uses():
    """La mappa dei cataloghi vale anche qui: `LIKE 'Abell %'` non trova niente, perche' li'
    SIMBAD scrive `ACO`. E il codice torna con la NOSTRA sigla, o nessuno saprebbe a quale
    voce appartiene."""
    viste = []
    risposta = tabella(["catcode", "proper"], [["ACO  1656", "NAME Coma Cluster"]])
    fuori = simbad.nomi("Abell", posta=finto(risposta, viste))
    assert "ACO %" in viste[0]
    assert fuori == {"Abell 1656": "Coma Cluster"}
