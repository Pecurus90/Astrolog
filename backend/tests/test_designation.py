"""Da un nome scritto come capita alla coppia `(catalogo, numero)`.

E' il punto in cui l'archivio di chiunque incontra la grafia di chiunque: N.I.N.A. scrive
`M 31`, SGP `M31`, uno a mano `messier 31`, e un altro copia dal catalogo `M 031`. Se una di
queste grafie cade fuori, le ore di quell'oggetto si sparpagliano su due voci.
"""

import pytest

from astrolog.catalog import bundle, designation

# Catturata all'import, PRIMA del recinto della suite: il giro completo qui sotto ha bisogno
# del catalogo vero, ed e' l'unica prova che copre ogni designazione che l'app incontrera'.
real_bundle = bundle.path


@pytest.mark.parametrize(
    ("scritto", "atteso"),
    [
        ("M 31", ("M", "31")),
        ("M31", ("M", "31")),
        ("m31", ("M", "31")),
        ("M  31", ("M", "31")),
        (" M 31 ", ("M", "31")),
        ("M 031", ("M", "31")),
        ("M-31", ("M", "31")),
        ("Messier 31", ("M", "31")),
        ("messier 31", ("M", "31")),
        ("NGC 224", ("NGC", "224")),
        ("ngc224", ("NGC", "224")),
        ("NGC 0224", ("NGC", "224")),
        ("IC 434", ("IC", "434")),
        ("Barnard 33", ("B", "33")),
        ("B 33", ("B", "33")),
        ("Caldwell 49", ("C", "49")),
        ("Abell 1656", ("Abell", "1656")),
        ("vdB 141", ("vdB", "141")),
        ("van den Bergh 141", ("vdB", "141")),
        ("Melotte 20", ("Mel", "20")),
        ("Cederblad 214", ("Ced", "214")),
        ("WR 134", ("WR", "134")),
        # dentro un nome per esteso spazio e trattino sono la stessa cosa, e possono mancare:
        # chi cerca non sa quale delle tre grafie sia quella "giusta"
        ("Wolf-Rayet 134", ("WR", "134")),
        ("Wolf Rayet 134", ("WR", "134")),
        ("wolfrayet 134", ("WR", "134")),
        ("van-den-Bergh 141", ("vdB", "141")),
        ("vandenbergh 141", ("vdB", "141")),
        ("PK 205+14.1", ("PK", "205+14.1")),
        ("Perek-Kohoutek 205+14.1", ("PK", "205+14.1")),
        ("WR 148a", ("WR", "148A")),
        ("B 117a", ("B", "117A")),
    ],
)
def test_a_designation_reads_the_same_however_it_is_written(scritto, atteso):
    assert designation.parse(scritto) == atteso


@pytest.mark.parametrize(
    "scritto", ["Sh2 155", "Sh2-155", "sh2155", "SH2 155", "Sh2 0155", "Sharpless 155"]
)
def test_sharpless_survives_its_digit_in_the_prefix(scritto):
    """`Sh2` porta una cifra nel prefisso, e una regola "lettere, poi numero" lo spezza in
    `SH` + `2155`: sono 313 voci Sharpless irraggiungibili, e sono proprio quelle che si
    scrivono negli header a banda stretta -- Cave, Cuore, Anima, Proboscide, Tulipano."""
    assert designation.parse(scritto) == ("Sh2", "155")


def test_ngc_and_ic_keep_their_letter_suffix():
    """`NGC 7331A` non e' `NGC 7331`: e' un vicino diverso, e perdere la lettera vorrebbe
    dire attribuire le ore all'oggetto sbagliato."""
    assert designation.parse("NGC 7331A") == ("NGC", "7331A")
    assert designation.parse("ngc 7331a") == ("NGC", "7331A")
    assert designation.parse("IC 1396A") == ("IC", "1396A")


def test_lynds_stays_unreadable_on_purpose():
    """Lynds e' l'autore sia di LBN (nebulose brillanti) sia di LDN (oscure): `Lynds 33` e'
    ambiguo, e indovinare manderebbe sull'oggetto sbagliato. Nessun risultato e' meglio di
    uno falso."""
    assert designation.parse("Lynds 33") is None
    assert designation.parse("LBN 33") == ("LBN", "33")
    assert designation.parse("LDN 33") == ("LDN", "33")


@pytest.mark.parametrize("niente", ["", "   ", None, "roba a caso", "Andromeda", "42", "NGC"])
def test_what_is_not_a_designation_is_not_invented(niente):
    """La maggior parte dei nomi che l'utente scrive nell'header non sono sigle: sono nomi
    comuni, o nomi di file. Leggerli come sigle sarebbe peggio che non leggerli."""
    assert designation.parse(niente) is None


def test_the_key_is_the_same_for_every_spelling():
    """La chiave e' cio' che si scrive nel database e cio' che si cerca: se due grafie dello
    stesso oggetto dessero chiavi diverse, l'indice non le farebbe incontrare."""
    chiavi = {designation.key(s) for s in ("M 31", "M31", "m  31", "M 031", "Messier 31")}
    assert chiavi == {"M|31"}
    assert designation.key("roba a caso") is None


def test_every_designation_in_the_catalogue_reads_back():
    """Il giro completo: ogni designazione del catalogo vero, in quattro grafie, deve tornare
    quella di partenza. E' la prova che chiude il buco di `Sh2`, e la sola che copre le
    ventiquattromila sigle che l'app incontrera' davvero invece di una decina scelte a mano."""
    file = real_bundle()
    assert file, "il catalogo impacchettato non c'e'"
    _, voci = bundle.read(file)
    sigle = [(c, n) for v in voci for c, n in (v.get("n") or ())]
    assert len(sigle) > 20000, f"solo {len(sigle)} designazioni: il file non e' quello vero"

    rotte = []
    for catalogo, numero in sigle:
        forme = [f"{catalogo} {numero}", f"{catalogo}{numero}", f"{catalogo.lower()}  {numero}"]
        if catalogo != "PK":
            # una coordinata galattica e' gia' impaginata: uno zero in piu' la cambia
            forme.append(f" {catalogo.upper()} 0{numero} ")
        rotte += [
            (s, designation.parse(s))
            for s in forme
            if designation.parse(s) != (catalogo, numero.upper())
        ]
    assert rotte == [], f"{len(rotte)} grafie non tornano, es. {rotte[:5]}"
