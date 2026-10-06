"""Le otto situazioni del contratto: dato cio' che dice il nome e cio' che dice il cielo, quale
ramo, quale metodo, quale fiducia, e se si chiede conferma.

Una riga della tabella, un test. Si guarda il `branch` e non la prosa: un banco che distinguesse
i rami leggendo un motivo scritto a parole proverebbe il motivo, non la decisione.
"""

from pathlib import Path

import pytest

from astrolog.catalog import NamedEntry
from astrolog.spine import identify_decide as decide
from astrolog.spine.identify_score import Candidate

# Le coordinate vere: la separazione fra due candidati si misura su queste, e un test che le
# inventasse proverebbe l'aritmetica invece della decisione.
CIELO = {
    "m-31": (10.684792, 41.269056),
    "m-32": (10.674292, 40.865278),
    "m-45": (56.869167, 24.105278),
    "m-81": (148.888208, 69.065306),
    "m-82": (148.969708, 69.679389),
    "m-42": (83.818667, -5.389667),
    "m-43": (83.880750, -5.267472),
    "ngc-1973": (83.769917, -4.731778),
    "ngc-1977": (83.815833, -4.844333),
    "ngc-1980": (83.858292, -5.909889),
    "ngc-1981": (83.789958, -4.425056),
    "sh2-276": (81.867157, -3.965235),
}


# I campi della voce che la decisione non legge.
_VUOTA = dict(
    constellation="And",
    type_code="GALAXY",
    kinds_json=None,
    size_minor_arcmin=None,
    position_angle_deg=None,
    surface_brightness=None,
    distance_ly=None,
    opacity=None,
)


def voce(slug, name="M 31", size=180.0, mag=3.4, band="V", sep=0.0, in_frame=True):
    """Un candidato come lo consegna `identify.candidates`. La magnitudine e la sua banda
    possono mancare -- il catalogo non le ha per tutti --, e `in_frame` dice se il candidato e'
    dentro il rettangolo dell'inquadratura o solo sovrapposto."""
    ra, dec = CIELO[slug]
    return Candidate(
        **_VUOTA,
        slug=slug,
        name=name,
        common_name=None,
        ra_deg=ra,
        dec_deg=dec,
        size_major_arcmin=size,
        magnitude=mag,
        magnitude_band=band,
        sep_deg=sep,
        score=1.0,
        in_frame=in_frame,
    )


def sigla(slug, primary=1):
    """La voce che il catalogo restituisce cercando la sigla dell'header."""
    ra, dec = CIELO[slug]
    return NamedEntry(
        **_VUOTA,
        slug=slug,
        name="M 31",
        common_name=None,
        ra_deg=ra,
        dec_deg=dec,
        size_major_arcmin=None,
        magnitude=None,
        magnitude_band=None,
        is_primary=primary,
    )


# --- con il cielo -----------------------------------------------------------------------


def test_the_designation_and_the_sky_agree():
    d = decide.decide(raw_name="M 31", hit=sigla("m-31"), cands=[voce("m-31")], fov_radius_deg=1.0)
    assert d.branch == "name_and_sky_agree"
    assert (d.slug, d.method, d.confidence) == ("m-31", "coord_confirmed", "certain")
    assert d.review is False


def test_the_designation_settles_the_tie_when_the_sky_has_two_contenders():
    """M 81 nell'header, M 82 accanto che contende davvero: il cielo trova nel campo proprio la
    sigla scritta -- qui anche in cima --, quindi la sta confermando e non si chiede niente."""
    cands = [
        voce("m-81", "M 81", size=21.63, mag=6.92, sep=0.30),
        voce("m-82", "M 82", size=10.99, mag=8.3, sep=0.32),
    ]
    d = decide.decide(raw_name="M 81", hit=sigla("m-81"), cands=cands, fov_radius_deg=1.0)
    assert d.branch == "name_and_sky_agree"
    assert d.review is False


def test_the_sky_says_another_thing():
    """Il confine della regola: nel campo quella sigla **non c'e'** proprio, e allora si chiede.
    Il nome resta agganciato come ipotesi -- una posa non resta mai scollegata -- e chi mostra la
    domanda ha i candidati per dire cosa c'e' invece."""
    d = decide.decide(
        raw_name="M 31", hit=sigla("m-31"), cands=[voce("m-45", "M 45")], fov_radius_deg=1.0
    )
    assert d.branch == "sky_disagrees"
    assert (d.slug, d.method, d.confidence) == ("m-31", "coord_review", "low")
    assert d.review is True


def test_the_designation_in_the_field_wins_even_when_it_is_not_the_best_guess():
    """La sigla dell'header scioglie l'ambiguita' **ovunque stia fra i candidati**, non solo
    quando e' quello migliore: se il cielo la trova, la sta confermando. E' la definizione della
    spina -- *"se l'header dice un nome che sta nel campo, quello vince"* (Marco, 2026-09-12).

    Qui il cielo mette in cima M 42 e l'header dice `NGC 1977`: e' la Running Man, dentro lo
    stesso complesso, e chiedere non cambierebbe niente."""
    cands = [voce("m-42", "M 42", sep=0.1), voce("ngc-1977", "NGC 1977", sep=0.6)]
    d = decide.decide(raw_name="NGC 1977", hit=sigla("ngc-1977"), cands=cands, fov_radius_deg=1.0)
    assert d.branch == "name_and_sky_agree"
    assert (d.slug, d.method, d.confidence) == ("ngc-1977", "coord_confirmed", "certain")
    assert d.review is False


def test_the_designation_settles_it_from_anywhere_in_the_field():
    """Si cerca fra **tutti** i candidati, non fra i primi.

    Sono i primi sette come li consegna la spina sul catalogo vero, puntando il campo di
    `identify_bench.ORIONE` a 3x2 gradi -- lo stesso della posa in `test_identify_stage`:
    `NGC 1977`, la Running Man che l'header nomina, e' il **settimo** per punteggio, cioe'
    oltre i sei che la pagina mostra. Fermarsi ai primi la rimetterebbe in Da confermare."""
    cands = [
        voce("m-42", "M 42", size=90.0, mag=4.0, sep=0.0),
        voce("m-43", "M 43", size=20.0, mag=9.0, sep=0.136940),
        voce("ngc-1980", "NGC 1980", size=9.3, mag=2.5, sep=0.521714),
        voce("sh2-276", "Sh2 276", size=1200.0, mag=None, band=None, sep=2.410782),
        voce("ngc-1973", "NGC 1973", size=5.0, mag=7.0, band="B", sep=0.659679),
        voce("ngc-1981", "NGC 1981", size=9.0, mag=4.2, sep=0.965035),
        voce("ngc-1977", "NGC 1977", size=10.2, mag=None, band=None, sep=0.545341),
    ]
    d = decide.decide(raw_name="NGC 1977", hit=sigla("ngc-1977"), cands=cands, fov_radius_deg=1.0)
    assert d.branch == "name_and_sky_agree"
    assert d.slug == "ngc-1977"
    assert d.review is False


def test_the_designation_wins_even_with_its_centre_outside_the_frame():
    """`in_frame` e' un'informazione, non un filtro.

    I candidati sono gia' soltanto cio' che si sovrappone alla foto: un oggetto grande puo'
    avere il centro fuori dal rettangolo ed essere lo stesso il soggetto. Se l'header lo nomina,
    vince anche li' -- filtrare sul rettangolo rimetterebbe a chiedere proprio le pose che la
    regola deve chiudere."""
    cands = [
        voce("m-42", "M 42", size=90.0, mag=4.0),
        voce("ngc-1977", "NGC 1977", size=10.2, mag=None, band=None, in_frame=False),
    ]
    d = decide.decide(raw_name="NGC 1977", hit=sigla("ngc-1977"), cands=cands, fov_radius_deg=1.0)
    assert d.branch == "name_and_sky_agree"
    assert d.slug == "ngc-1977"
    assert d.review is False


def test_no_designation_and_one_sure_thing_in_the_sky():
    d = decide.decide(raw_name="Snapshot", hit=None, cands=[voce("m-31")], fov_radius_deg=1.0)
    assert d.branch == "sky_only"
    assert (d.slug, d.method, d.confidence) == ("m-31", "coord_confirmed", "certain")
    assert d.review is False


def test_no_designation_and_two_contenders_in_the_sky():
    """Senza un nome che scioglie il dubbio, due bersagli veri si chiedono."""
    cands = [
        voce("m-81", "M 81", size=21.63, mag=6.92, sep=0.30),
        voce("m-82", "M 82", size=10.99, mag=8.3, sep=0.32),
    ]
    d = decide.decide(raw_name=None, hit=None, cands=cands, fov_radius_deg=1.0)
    assert d.branch == "sky_ambiguous"
    assert (d.slug, d.method, d.confidence) == ("m-81", "coord_review", "low")
    assert d.review is True


def test_a_free_name_never_creates_an_object_when_the_sky_is_there():
    """Dove il cielo c'e', il cielo e' la misura e il nome e' un'etichetta: nessun oggetto
    fuori catalogo, mai."""
    d = decide.decide(raw_name="Andromeda_finale", hit=None, cands=[voce("m-31")], fov_radius_deg=1)
    assert d.slug == "m-31"
    assert d.name is None


def test_a_comet_never_takes_the_object_behind_it():
    """Una cometa era li' quella notte e non ci sara' la prossima: il cono restituirebbe
    l'oggetto fisso che le stava dietro, e lo direbbe sicuro di se'. Il cielo non si consulta."""
    d = decide.decide(
        raw_name="12P/Pons-Brooks", hit=None, cands=[voce("m-31")], fov_radius_deg=1.0
    )
    assert d.branch == "moving"
    assert (d.slug, d.name) == (None, "12P/Pons-Brooks")
    assert (d.method, d.confidence) == ("exact_name", "high")
    assert d.review is False


def test_a_comet_whose_designation_is_also_a_catalog_one_still_wins_the_sky():
    """Anche se la sigla esiste in catalogo: il lessico dei mobili si guarda per primo."""
    d = decide.decide(
        raw_name="C/2023 A3", hit=sigla("m-31"), cands=[voce("m-31")], fov_radius_deg=1.0
    )
    assert d.branch == "moving"


def test_a_fixed_object_is_not_taken_for_moving():
    """Il verso in cui la guardia sbaglia: chi cade fuori resta visibile e correggibile."""
    for nome in ("M 31", "NGC 7023", "Sh2 155", "C 49"):
        d = decide.decide(raw_name=nome, hit=sigla("m-31"), cands=[], fov_radius_deg=None)
        assert d.branch == "name_only", nome


# --- senza cielo ------------------------------------------------------------------------


def test_a_designation_without_sky_hangs_on_the_name():
    d = decide.decide(raw_name="M 31", hit=sigla("m-31"), cands=[], fov_radius_deg=None)
    assert d.branch == "name_only"
    assert (d.slug, d.method, d.confidence) == ("m-31", "exact_name", "high")
    assert d.review is False


def test_a_historic_name_without_sky_says_so():
    """`NGC 224` e' M 31, ma non e' il nome primario della voce: il metodo lo dice, e cosi'
    `historic_name` ha un produttore invece di essere un valore morto nello schema."""
    d = decide.decide(
        raw_name="NGC 224", hit=sigla("m-31", primary=0), cands=[], fov_radius_deg=None
    )
    assert d.branch == "name_only"
    assert (d.method, d.confidence) == ("historic_name", "high")


def test_the_sole_name_is_never_certain():
    """Il contratto: `certain` e' riservato a nome e cielo concordi."""
    d = decide.decide(raw_name="M 31", hit=sigla("m-31"), cands=[], fov_radius_deg=None)
    assert d.confidence != "certain"


def test_a_free_name_without_sky_becomes_an_object_of_its_own():
    """Le sette pose di M 101 del collaudo dicevano soltanto `Snapshot`: restano insieme sotto
    quel nome, e un gesto solo in Da confermare le sistema tutte (Marco, 2026-09-09)."""
    d = decide.decide(raw_name="Snapshot", hit=None, cands=[], fov_radius_deg=None)
    assert d.branch == "free_name_only"
    assert (d.slug, d.name) == (None, "Snapshot")
    assert (d.method, d.confidence) == ("exact_name", "low")
    assert d.review is True


def test_a_designation_the_catalog_does_not_know_is_a_free_name():
    """`NGC 99999` sembra una sigla ma non e' nessuno: vale quanto `Snapshot`, non di piu'."""
    d = decide.decide(raw_name="NGC 99999", hit=None, cands=[], fov_radius_deg=None)
    assert d.branch == "free_name_only"
    assert d.name == "NGC 99999"


@pytest.mark.parametrize("vuoto", [None, "", "   "])
def test_no_name_and_no_sky_leaves_no_object(vuoto):
    d = decide.decide(raw_name=vuoto, hit=None, cands=[], fov_radius_deg=None)
    assert d.branch == "nothing"
    assert (d.slug, d.name, d.method, d.confidence) == (None, None, None, None)
    assert d.review is False  # non e' una domanda: e' un elenco, e lo mostra Da confermare


# --- il vocabolario chiuso --------------------------------------------------------------


def test_every_branch_says_a_word_of_the_closed_vocabulary():
    """Nessun ramo puo' inventare un metodo o una fiducia: il database li rifiuterebbe, ma
    a valle e su una posa sola, mentre qui si vede tutto insieme."""
    casi = [
        dict(raw_name="M 31", hit=sigla("m-31"), cands=[voce("m-31")], fov_radius_deg=1.0),
        dict(raw_name="M 31", hit=sigla("m-31"), cands=[voce("m-45")], fov_radius_deg=1.0),
        dict(raw_name=None, hit=None, cands=[voce("m-31")], fov_radius_deg=1.0),
        dict(raw_name="M 31", hit=sigla("m-31"), cands=[], fov_radius_deg=None),
        dict(raw_name="NGC 224", hit=sigla("m-31", primary=0), cands=[], fov_radius_deg=None),
        dict(raw_name="Snapshot", hit=None, cands=[], fov_radius_deg=None),
        dict(raw_name=None, hit=None, cands=[], fov_radius_deg=None),
    ]
    for caso in casi:
        d = decide.decide(**caso)
        assert d.method in (*decide.IdentityMethod, None), d
        assert d.confidence in (*decide.IdentityConfidence, None), d
        assert d.branch in set(decide.Branch), d
        # o si aggancia una voce di catalogo, o si crea un oggetto col suo nome, mai tutti e due
        assert not (d.slug and d.name), d


def test_the_user_answer_is_in_the_vocabulary_but_no_branch_writes_it():
    """`user`/`user` e' la risposta dell'utente, che arriva da Da confermare e non da qui: se
    un ramo cominciasse a scriverla, sovrascriverebbe cio' che non si sovrascrive mai."""
    assert "user" in set(decide.IdentityMethod) and "user" in set(decide.IdentityConfidence)
    casi = [
        dict(raw_name="M 31", hit=sigla("m-31"), cands=[voce("m-31")], fov_radius_deg=1.0),
        dict(raw_name="Snapshot", hit=None, cands=[], fov_radius_deg=None),
        dict(raw_name=None, hit=None, cands=[voce("m-31")], fov_radius_deg=1.0),
    ]
    assert all(decide.decide(**c).method != "user" for c in casi)


@pytest.mark.sorgente
def test_the_branches_are_the_ones_the_contract_lists():
    """La colonna `branch` di `docs/domini/spina.md` e questa costante sono lo stesso elenco.

    I due vocabolari chiusi hanno la loro guardia contro il CHECK dello schema; la tabella delle
    situazioni non ne aveva nessuna, e poteva divergere in silenzio dal codice -- che e' proprio
    il difetto contro cui quelle guardie esistono."""
    contratto = Path(__file__).resolve().parents[2] / "docs" / "domini" / "spina.md"
    testo = contratto.read_text(encoding="utf-8")
    tabella = testo[testo.index("| il nome dice | il cielo dice |") :]
    tabella = tabella[: tabella.index("\n\n")]
    righe = tabella.splitlines()
    corpo = righe[righe.index(next(r for r in righe if "---" in r)) + 1 :]
    dal_contratto = {r.strip().strip("|").rsplit("|", 1)[-1].strip().strip("`") for r in corpo}
    assert dal_contratto == set(decide.Branch)


def test_every_branch_has_a_case_that_produces_it():
    """Il contratto e `Branch` si guardano a vicenda, ma un ramo scritto in tutti e due e mai
    prodotto da `decide` resterebbe verde. Qui ogni ramo vuole un caso che lo faccia nascere."""
    m81_m82 = [
        voce("m-81", "M 81", size=21.63, mag=6.92, sep=0.30),
        voce("m-82", "M 82", size=10.99, mag=8.3, sep=0.32),
    ]
    casi = [
        dict(raw_name="12P/Pons-Brooks", hit=None, cands=[], fov_radius_deg=None),
        dict(raw_name="M 31", hit=sigla("m-31"), cands=[voce("m-31")], fov_radius_deg=1.0),
        dict(raw_name="M 31", hit=sigla("m-31"), cands=[voce("m-45")], fov_radius_deg=1.0),
        dict(raw_name=None, hit=None, cands=[voce("m-31")], fov_radius_deg=1.0),
        dict(raw_name=None, hit=None, cands=m81_m82, fov_radius_deg=1.0),
        dict(raw_name="M 31", hit=sigla("m-31"), cands=[], fov_radius_deg=None),
        dict(raw_name="Snapshot", hit=None, cands=[], fov_radius_deg=None),
        dict(raw_name=None, hit=None, cands=[], fov_radius_deg=None),
    ]
    assert {decide.decide(**c).branch for c in casi} == set(decide.Branch)
