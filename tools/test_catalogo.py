"""Lo snellimento del catalogo: quali campi restano, e cosa diventa la magnitudine.

Le regole sono decisioni di prodotto prese da Marco l'8/9/2026, non gusto: un campo resta se
l'app ci decide qualcosa o se chi legge la scheda lo cercherebbe. Qui si prova la regola, su
voci finte: il catalogo vero e' un dato, e un test che dipendesse da lui si romperebbe alla
prossima ricostruzione.
"""

import catalogo


def voce(**extra):
    """Una voce minima e valida, da variare."""
    base = {
        "slug": "m-31",
        "name": "M 31",
        "ra": 10.684,
        "dec": 41.269,
        "constellation": "And",
        "type_code": "GALAXY",
        "kind": "galaxy",
        "n": [["M", "31"], ["NGC", "224"]],
        "src": {"_": "openngc"},
    }
    return {**base, **extra}


def test_i_campi_che_restano_sono_diciannove_e_si_chiamano_cosi():
    """L'elenco e' chiuso: un campo nuovo che arrivasse da una fonte non entra di nascosto."""
    assert len(catalogo.CAMPI) == len(set(catalogo.CAMPI))
    assert set(catalogo.CAMPI) >= {
        "slug", "name", "ra", "dec", "constellation", "type_code",
        "size_major_arcmin", "size_minor_arcmin", "position_angle_deg",
        "magnitude", "magnitude_band", "surface_brightness", "distance_ly",
        "opacity", "common_name",
    }  # fmt: skip


def test_i_quattro_campi_tolti_non_passano():
    """`redshift` porta rumore (245 ammassi aperti ne hanno uno che dovrebbe essere zero),
    `hubble_type` e' da specialista, `object_type` ripete il tipo nostro, e l'`id` si
    rinumera a ogni ricostruzione: l'identita' e' lo slug."""
    snella = catalogo.snellisci(
        [voce(redshift=0.001, hubble_type="SA(s)b", object_type="G", id=42)]
    )[0]
    for tolto in ("redshift", "hubble_type", "object_type", "id"):
        assert tolto not in snella, tolto
    assert snella["slug"] == "m-31"


def test_la_magnitudine_diventa_un_campo_solo_con_la_sua_banda():
    """Due colonne costringevano chi legge a rifare la cascata "prima V poi B" e a sbagliarla.
    Un campo con la banda accanto dice la verita' una volta: e copre il 69% invece del 28%."""
    tutte_e_due = catalogo.snellisci([voce(magnitude_v=3.4, magnitude_b=4.3)])[0]
    assert tutte_e_due["magnitude"] == 3.4 and tutte_e_due["magnitude_band"] == "V"

    solo_b = catalogo.snellisci([voce(magnitude_b=17.1)])[0]
    assert solo_b["magnitude"] == 17.1 and solo_b["magnitude_band"] == "B"

    solo_v = catalogo.snellisci([voce(magnitude_v=8.0)])[0]
    assert solo_v["magnitude"] == 8.0 and solo_v["magnitude_band"] == "V"

    nessuna = catalogo.snellisci([voce()])[0]
    assert "magnitude" not in nessuna and "magnitude_band" not in nessuna

    for s in (tutte_e_due, solo_b, solo_v):
        assert "magnitude_v" not in s and "magnitude_b" not in s


def test_una_magnitudine_senza_banda_non_esiste():
    """Il numero da solo non si sa cosa valga: una V e una B della stessa voce differiscono
    anche di un paio di magnitudini su una nebulosa rossa."""
    for s in catalogo.snellisci([voce(magnitude_v=3.4), voce(magnitude_b=4.3), voce()]):
        assert ("magnitude" in s) == ("magnitude_band" in s)


def test_i_campi_vuoti_non_si_scrivono():
    """Assenza dichiarata, non chiave con dentro `null`: e' cosi' che il file resta piccolo e
    che "non lo so" si distingue da "zero"."""
    snella = catalogo.snellisci([voce(size_major_arcmin=None, common_name=None)])[0]
    assert "size_major_arcmin" not in snella and "common_name" not in snella


def test_la_provenienza_segue_i_campi_che_restano():
    """`src` dice da dove viene ogni valore: quando un campo esce, esce anche la sua riga di
    provenienza, o resterebbe a parlare di un dato che non c'e' piu'."""
    snella = catalogo.snellisci(
        [
            voce(
                magnitude_v=3.4,
                redshift=0.001,
                src={"_": "openngc", "magnitude_v": "stellarium_dso", "redshift": "simbad"},
            )
        ]
    )[0]
    assert "redshift" not in snella["src"]
    assert snella["src"]["magnitude"] == "stellarium_dso"  # segue il valore, non il vecchio nome


def test_le_sigle_restano_intere_e_in_ordine():
    """La prima sigla e' la principale, ed e' la stessa per sempre: e' l'ancora fra due
    ricostruzioni del catalogo, dove gli id invece si rinumerano."""
    snella = catalogo.snellisci([voce()])[0]
    assert snella["n"] == [["M", "31"], ["NGC", "224"]]


def test_snellire_due_volte_da_lo_stesso_risultato():
    """Lo strumento gira anche su un catalogo gia' snellito (dopo un arricchimento): non deve
    perdere la magnitudine gia' fusa ne' rifondere niente."""
    una = catalogo.snellisci([voce(magnitude_v=3.4, magnitude_b=4.3)])
    due = catalogo.snellisci(una)
    assert una == due


def test_una_voce_senza_coordinate_non_e_una_voce():
    """Senza cielo non si puo' ne' riconoscere ne' disegnare: si scarta, e si dice quante."""
    tenute, scartate = catalogo.snellisci_con_scarti([voce(), voce(slug="x", ra=None)])
    assert len(tenute) == 1 and scartate == ["x"]


# --- l'arricchimento ------------------------------------------------------------------------


def test_l_arricchimento_riempie_i_buchi_e_non_sovrascrive_mai():
    """La regola del vecchio, pagata: le sorgenti si SOMMANO, non si sostituiscono. Un valore
    che abbiamo gia' e' stato scelto da una cascata di precedenze fra fonti curate; lasciarlo
    riscrivere da un servizio esterno vorrebbe dire buttare via quella scelta in silenzio."""
    voci = [voce(magnitude=3.4, magnitude_band="V"), voce(slug="ngc-2237", n=[["NGC", "2237"]])]
    misure = {
        "M 31": {"magnitude": 99.0, "size_major_arcmin": 199.5, "size_minor_arcmin": 70.8},
        "NGC 2237": {"magnitude": 9.0, "size_major_arcmin": 80.0, "size_minor_arcmin": None},
    }
    fuori, conto = catalogo.arricchisci(voci, nomi={}, misure=misure)

    assert fuori[0]["magnitude"] == 3.4  # la nostra resta
    assert fuori[0]["size_major_arcmin"] == 199.5  # il buco si riempie
    assert fuori[1]["magnitude"] == 9.0
    assert "size_minor_arcmin" not in fuori[1]  # SIMBAD non lo sapeva: resta vuoto
    assert conto["magnitude"] == 1 and conto["size_major_arcmin"] == 2


def test_un_valore_arrivato_da_simbad_lo_dichiara():
    """Chi legge deve poter sapere che quel numero non viene da OpenNGC ma da un servizio
    interrogato una volta: e' la stessa provenienza per campo che il catalogo usa gia'."""
    fuori, _ = catalogo.arricchisci(
        [voce()], nomi={}, misure={"M 31": {"size_major_arcmin": 199.5}}
    )
    assert fuori[0]["src"]["size_major_arcmin"] == "simbad"
    assert fuori[0]["src"]["_"] == "openngc"  # la prevalente non cambia


def test_il_nome_arriva_da_una_qualunque_delle_sigle():
    """Una voce ha piu' sigle e SIMBAD conosce il nome sotto una sola: cercarlo solo sulla
    principale perderebbe i nomi di meta' catalogo."""
    fuori, conto = catalogo.arricchisci([voce()], nomi={"NGC 224": "Andromeda Galaxy"}, misure={})
    assert fuori[0]["common_name"] == "Andromeda Galaxy"
    assert conto["common_name"] == 1


def test_un_nome_che_abbiamo_gia_non_si_tocca():
    """Vale anche qui: le correzioni curate hanno l'ultima parola, e una di esse e' proprio un
    nome sbagliato dalle fonti."""
    fuori, conto = catalogo.arricchisci(
        [voce(common_name="Andromeda")], nomi={"M 31": "Andromeda Galaxy"}, misure={}
    )
    assert fuori[0]["common_name"] == "Andromeda" and conto["common_name"] == 0


def test_le_sigle_da_chiedere_sono_solo_quelle_che_servono():
    """Non si chiede a un servizio pubblico cio' che gia' si sa: si chiedono solo le voci a cui
    manca almeno uno dei due campi che l'arricchimento riempie."""
    voci = [
        voce(magnitude=3.4, magnitude_band="V", size_major_arcmin=199.5, size_minor_arcmin=70.8),
        voce(slug="ngc-2237", n=[["NGC", "2237"]]),
    ]
    assert catalogo.da_chiedere(voci) == ["NGC 2237"]


def test_le_voci_che_simbad_non_conosce_non_si_richiedono():
    """Una voce interrogata e non trovata si ricorda. Un guasto di rete no: quello si ritenta."""
    voci = [voce(slug="ldn-9999", n=[["LDN", "9999"]])]
    assert catalogo.da_chiedere(voci, assenti={"LDN 9999"}) == []


def test_una_magnitudine_presa_da_simbad_dichiara_la_sua_banda():
    """La query chiede la banda V: se il valore entrasse senza dirlo, resterebbe un numero
    muto in mezzo ad altri che la banda ce l'hanno."""
    fuori, _ = catalogo.arricchisci([voce()], nomi={}, misure={"M 31": {"magnitude": 3.44}})
    assert fuori[0]["magnitude"] == 3.44 and fuori[0]["magnitude_band"] == "V"


def test_la_spaziatura_di_simbad_non_fa_perdere_l_aggancio():
    """SIMBAD scrive le sigle con DUE spazi (`NGC  4490`), noi con uno. Agganciare sulla
    stringa cruda faceva fallire tutto in silenzio: nessun errore, solo nomi che non
    arrivavano. La si normalizza su tutti e due i lati."""
    fuori, conto = catalogo.arricchisci(
        [voce(slug="ngc-4490", n=[["NGC", "4490"]])],
        nomi={"NGC  4490": "Cocoon Galaxy"},
        misure={},
    )
    assert fuori[0]["common_name"] == "Cocoon Galaxy" and conto["common_name"] == 1


def test_una_sigla_travestita_da_nome_non_diventa_un_nome():
    """SIMBAD tiene sotto `NAME ...` anche designazioni di altri cataloghi: `VV 543E`,
    `Her 36`, `IRAS F13373+0105 SE`. Scritte nella scheda sarebbero peggio della sigla che
    sostituiscono, perche' sembrerebbero un nome vero."""
    for finta in ("VV 543E", "Her 36", "IRAS F13373+0105 SE", "NGC 7538 IRS 1-3", "3C 273"):
        assert not catalogo.e_un_nome(finta), finta
    for vera in ("Cocoon Galaxy", "Keyhole Nebula", "the Mice", "Rosette Nebula", "Andromeda"):
        assert catalogo.e_un_nome(vera), vera


def test_le_sigle_travestite_non_entrano_nel_catalogo():
    fuori, conto = catalogo.arricchisci([voce()], nomi={"M 31": "VV 543E"}, misure={})
    assert "common_name" not in fuori[0] and conto["common_name"] == 0


# --- le correzioni curate -------------------------------------------------------------------


CORREZIONI = [
    {"catalogo": "IC", "designazione": "434", "campo": "common_name",
     "da": "Flame Nebula", "a": None, "perche": "e' NGC 2024"},
    {"catalogo": "M", "designazione": "11", "campo": "common_name",
     "da": "Amas de l'Ecu de Sobieski", "a": "Wild Duck Cluster", "perche": "era in francese"},
]  # fmt: skip


def test_una_correzione_curata_ha_l_ultima_parola():
    """Sono valori che una fonte AFFERMA e che sappiamo falsi. SIMBAD dice che `IC 434` e' la
    Flame Nebula: non lo e', e' NGC 2024. Senza le correzioni l'arricchimento reintroduce un
    errore che qualcuno aveva gia' trovato e chiuso a mano."""
    voci = [voce(slug="ic-434", n=[["IC", "434"]], common_name="Flame Nebula")]
    fuori, tolte = catalogo.correggi(voci, CORREZIONI)
    assert "common_name" not in fuori[0] and tolte == 1


def test_una_correzione_puo_anche_sostituire():
    voci = [voce(slug="m-11", n=[["M", "11"]], common_name="Amas de l'Ecu de Sobieski")]
    fuori, _ = catalogo.correggi(voci, CORREZIONI)
    assert fuori[0]["common_name"] == "Wild Duck Cluster"


def test_una_correzione_scaduta_si_fa_sentire():
    """Il campo `da` dice quale valore sbagliato ci si aspetta. Se la fonte nel frattempo si e'
    corretta, la pezza non serve piu' e va tolta: continuare ad applicarla alla cieca
    sovrascriverebbe un dato ormai giusto."""
    voci = [voce(slug="ic-434", n=[["IC", "434"]], common_name="Horsehead region")]
    with __import__("pytest").raises(catalogo.CorrezioneScadutaError):
        catalogo.correggi(voci, CORREZIONI, severa=True)


def test_una_correzione_su_una_voce_che_non_c_e_non_e_un_errore_silenzioso():
    """Il catalogo cambia: una correzione che non trova piu' la sua voce va detta, non
    ignorata."""
    fuori, tolte = catalogo.correggi([voce()], CORREZIONI)
    assert tolte == 0 and len(fuori) == 1


def test_quando_una_correzione_cancella_un_valore_cancella_anche_la_sua_provenienza():
    """`src` dice da dove viene ogni valore. Una riga che sopravvivesse al valore cancellato
    resterebbe a raccontare la fonte di un dato che non c'e' piu'."""
    voci = [
        voce(
            slug="ic-434",
            n=[["IC", "434"]],
            common_name="Flame Nebula",
            src={"_": "openngc", "common_name": "simbad"},
        )
    ]
    fuori, _ = catalogo.correggi(voci, CORREZIONI)
    assert "common_name" not in fuori[0]
    assert "common_name" not in fuori[0]["src"]


# --- le voci che il servizio non conosce ------------------------------------------------------


def test_le_voci_trovate_non_finiscono_fra_le_sconosciute():
    """E' il difetto peggiore che questa fetta ha avuto: le voci che SIMBAD aveva riconosciuto
    finivano in lista nera perche' il confronto non passava dalla normalizzazione, e da li' in
    poi non venivano piu' chieste -- in silenzio, per sempre. 1.368 voci su 2.024."""
    ignote = catalogo.sconosciute(["M 11", "LDN 9999"], {"M  11": {"magnitude": 5.8}})
    assert ignote == ["LDN 9999"]


def test_chi_era_gia_sconosciuto_resta_sconosciuto():
    ignote = catalogo.sconosciute(["M 11"], {"M  11": {}}, gia_note={"LDN 9999"})
    assert ignote == ["LDN 9999"]


def test_una_correzione_gia_applicata_non_e_una_scadenza():
    """Il valore che si trova E' quello che la correzione voleva mettere: e' il suo effetto,
    non un segno che la fonte si e' corretta. Gridare qui bloccherebbe ogni ricostruzione."""
    voci = [voce(slug="m-11", n=[["M", "11"]], common_name="Wild Duck Cluster")]
    fuori, fatte = catalogo.correggi(voci, CORREZIONI, severa=True)
    assert fuori[0]["common_name"] == "Wild Duck Cluster" and fatte == 0


def test_lo_snellimento_ha_un_chiamante_e_rifa_l_artefatto(tmp_path, monkeypatch):
    """E' il passo che produce il file che spediamo: senza un comando che lo faccia,
    l'artefatto non sarebbe rifacibile da niente nel repo, e nessuno saprebbe piu' da dove
    viene."""
    import json

    import arricchisci_catalogo

    sorgente = tmp_path / "sorgente.json"
    sorgente.write_text(
        json.dumps(
            {
                "built_at": "2026-08-25T00:00:00+00:00",
                "objects": [voce(magnitude_v=3.4, redshift=0.1), voce(slug="x", n=[["NGC", "1"]])],
            }
        ),
        encoding="utf-8",
    )
    dest = tmp_path / "dati"
    dest.mkdir()
    monkeypatch.setattr(arricchisci_catalogo, "DATI", dest)

    prodotto = arricchisci_catalogo.snellisci_da(sorgente)
    assert prodotto.parent == dest and prodotto.name.startswith("catalogo-2026")
    _, voci = catalogo.leggi(prodotto)
    assert len(voci) == 2
    assert "redshift" not in voci[0] and voci[0]["magnitude"] == 3.4

    # Rifarlo con un contenuto DIVERSO lascia UN file solo: due in cartella si caricherebbero
    # a caso. Il contenuto deve cambiare, o cambia anche il nome: con la stessa sorgente il
    # file si sovrascriverebbe da se' e questa guardia non potrebbe fallire mai.
    sorgente.write_text(
        json.dumps({"built_at": "2026-08-25T00:00:00+00:00", "objects": [voce()]}),
        encoding="utf-8",
    )
    secondo = arricchisci_catalogo.snellisci_da(sorgente)
    assert secondo.name != prodotto.name
    assert [p.name for p in dest.glob("catalogo-*.json")] == [secondo.name]


def test_la_lista_delle_sconosciute_scade_quando_cambiano_le_regole(tmp_path, monkeypatch):
    """Le voci "che SIMBAD non conosce" lo sono **con le regole con cui si e' chiesto**. Il
    giorno che si scopre che un catalogo ha un altro nome, quelle voci non erano sconosciute:
    erano chieste male. Senza questa scadenza resterebbero fuori per sempre, in silenzio --
    ed e' lo stesso difetto della lista avvelenata, un livello piu' in giu'."""
    import json

    import arricchisci_catalogo as strumento
    import simbad

    lista = tmp_path / "assenti.json"
    monkeypatch.setattr(strumento, "ASSENTI", lista)
    lista.write_text(
        json.dumps({"regole": strumento.regole_di_richiesta(), "sigle": ["LDN 9999"]}),
        encoding="utf-8",
    )
    assert strumento.assenti_note() == {"LDN 9999"}

    # si scopre che un catalogo si chiama in un altro modo: la lista non vale piu'
    monkeypatch.setattr(simbad, "ALTRO_NOME", {**simbad.ALTRO_NOME, "Sh2": "SH  2-"})
    assert strumento.assenti_note() == set()
