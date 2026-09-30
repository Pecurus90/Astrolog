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


def test_un_lotto_chiede_tutti_gli_identificatori_in_una_volta_sola():
    """Su quattromila voci, una richiesta per oggetto sarebbe quattromila richieste: la
    politica del servizio non le gradisce e nessuno le aspetterebbe."""
    viste = []
    simbad.misure(["M 31", "M 42", "NGC 224"], posta=finto(tabella([], []), viste))
    assert len(viste) == 1
    for sigla in ("M 31", "M 42", "NGC 224"):
        assert f"'{sigla}'" in viste[0]


def test_un_apice_nel_nome_non_rompe_la_query():
    """Gli apici si raddoppiano: e' l'escaping SQL, e senza di lui un nome con l'apice
    romperebbe la stringa -- o peggio, la riscriverebbe."""
    viste = []
    simbad.misure(["Barnard's Loop"], posta=finto(tabella([], []), viste))
    assert "'Barnard''s Loop'" in viste[0]


def test_si_chiede_la_magnitudine_in_banda_v_e_le_dimensioni():
    """Sono i due buchi che questa raccolta esiste per riempire. La V e non la B: e' la banda
    con cui si giudica un oggetto."""
    viste = []
    simbad.misure(["M 31"], posta=finto(tabella([], []), viste))
    q = viste[0]
    assert "galdim_majaxis" in q and "galdim_minaxis" in q
    assert "flux" in q and "'V'" in q


def test_i_nomi_si_chiedono_un_catalogo_per_volta():
    """SIMBAD tiene i nomi propri come identificatori `NAME ...`: una query per catalogo li
    prende tutti. E' il motivo per cui riempire 21.000 nomi costa 18 richieste."""
    viste = []
    simbad.nomi("NGC", posta=finto(tabella([], []), viste))
    assert "NGC %" in viste[0] and "NAME %" in viste[0]


# --- come si riaggancia --------------------------------------------------------------------


def test_la_risposta_si_riaggancia_alla_sigla_chiesta_non_a_quella_di_simbad():
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


def test_si_chiede_ogni_spaziatura_perche_simbad_allinea_il_numero():
    """`M   1`, `M  11`, `M 110`: il numero sta in un campo a larghezza fissa che cambia col
    catalogo e non e' documentato. Chiedere con la nostra grafia non trova NIENTE, in silenzio.
    Si chiedono tutte le forme: e' una lista piu' lunga, non una richiesta in piu'."""
    viste = []
    simbad.misure(["M 11"], posta=finto(tabella([], []), viste))
    assert "'M  11'" in viste[0] and "'M   11'" in viste[0]
    assert len(viste) == 1  # sempre una richiesta sola


def test_i_cataloghi_che_simbad_chiama_in_un_altro_modo():
    """Misurato: chiedendo `Abell 1136` non risponde nessuno, chiedendo `ACO  1136` si'."""
    assert any(f.startswith("ACO") for f in simbad.forme("Abell 1136"))
    assert any(f.startswith("Barnard") for f in simbad.forme("B 33"))
    assert any(f.startswith("APG") for f in simbad.forme("Arp 168"))
    assert all(f.startswith("NGC") for f in simbad.forme("NGC 224"))


def test_il_nome_proprio_perde_il_prefisso_di_simbad():
    """Negli identificatori il nome vero e' preceduto da `NAME `: cosi' com'e' finirebbe a
    schermo come "NAME Rosette Nebula"."""
    risposta = tabella(["catcode", "proper"], [["NGC 2237", "NAME Rosette Nebula"]])
    assert simbad.nomi("NGC", posta=finto(risposta)) == {"NGC 2237": "Rosette Nebula"}


# --- quando qualcosa non c'e' o non va -----------------------------------------------------


def test_una_voce_che_simbad_non_conosce_non_e_un_errore():
    """Chi manca dalla risposta non e' un guasto: e' una voce che il servizio non conosce, e
    il chiamante deve poterselo ricordare per non richiederla ogni volta."""
    risposta = tabella(
        ["id", "main_id", "galdim_majaxis", "galdim_minaxis", "flux"],
        [["M 31", "M  31", 199.5, 70.8, 3.44]],
    )
    fuori = simbad.misure(["M 31", "LDN 9999"], posta=finto(risposta))
    assert set(fuori) == {"M 31"}


def test_un_guasto_di_rete_non_si_confonde_mai_con_una_voce_assente():
    """Registrare un guasto di rete come "SIMBAD non lo conosce" vorrebbe dire non chiederlo
    mai piu': l'errore propaga, e chi chiama decide se ritentare."""
    for guasto in (TimeoutError("scaduto"), OSError("rete giu'")):
        with pytest.raises(simbad.SimbadNonRispondeError):
            simbad.misure(["M 31"], posta=finto(guasto))


def test_una_risposta_che_non_si_capisce_e_un_guasto_non_un_vuoto():
    """Un servizio che risponde HTML o JSON storto non sta dicendo "non lo conosco"."""
    for storta in ("<html>errore</html>", {"nessuna": "colonna"}, None):
        with pytest.raises(simbad.SimbadNonRispondeError):
            simbad.misure(["M 31"], posta=finto(storta))


def test_i_valori_assenti_restano_vuoti_mai_zero():
    """Una dimensione a zero sarebbe un oggetto puntiforme, e una magnitudine a zero un
    oggetto luminosissimo: due bugie al posto di "non lo so"."""
    risposta = tabella(
        ["id", "main_id", "galdim_majaxis", "galdim_minaxis", "flux"],
        [["M 31", "M  31", None, None, None]],
    )
    voce = simbad.misure(["M 31"], posta=finto(risposta))["M 31"]
    assert voce["size_major_arcmin"] is None and voce["magnitude"] is None


# --- la cortesia verso il servizio ---------------------------------------------------------


def test_fra_un_lotto_e_l_altro_si_aspetta():
    """Il servizio e' pubblico e gratuito: si va piano. La pausa si passa da fuori, cosi' i
    test non aspettano davvero."""
    attese = []
    sigle = [f"NGC {i}" for i in range(simbad.LOTTO * 2 + 1)]
    simbad.misure(sigle, posta=finto(tabella([], [])), pausa=attese.append)
    assert len(attese) == 2 and all(a == simbad.PAUSA_S for a in attese)


def test_un_lotto_non_supera_la_misura_dichiarata():
    """Il lotto si conta in SIGLE, non in stringhe: ognuna ne genera cinque, e un lotto troppo
    grosso farebbe una query che il servizio rifiuta."""
    viste = []
    sigle = [f"NGC {i}" for i in range(simbad.LOTTO + 5)]
    simbad.misure(sigle, posta=finto(tabella([], []), viste), pausa=lambda _: None)
    assert len(viste) == 2
    stringhe = viste[0].count("'NGC")
    assert stringhe == simbad.LOTTO * len(simbad.SPAZI)


def test_chi_chiama_si_identifica():
    """La politica del servizio lo pretende, e un client anonimo viene bloccato."""
    assert simbad.USER_AGENT.startswith("AstroLog/") and "http" in simbad.USER_AGENT


def test_un_identificatore_che_non_abbiamo_chiesto_si_butta():
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


def test_anche_i_nomi_si_chiedono_col_nome_che_simbad_usa():
    """La mappa dei cataloghi vale anche qui: `LIKE 'Abell %'` non trova niente, perche' li'
    SIMBAD scrive `ACO`. E il codice torna con la NOSTRA sigla, o nessuno saprebbe a quale
    voce appartiene."""
    viste = []
    risposta = tabella(["catcode", "proper"], [["ACO  1656", "NAME Coma Cluster"]])
    fuori = simbad.nomi("Abell", posta=finto(risposta, viste))
    assert "ACO %" in viste[0]
    assert fuori == {"Abell 1656": "Coma Cluster"}
