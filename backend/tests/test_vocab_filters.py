"""Il vocabolario dei filtri, rivisto con Marco: solo le grafie che N.I.N.A., ASIAIR, Voyager
e SGP possono scrivere; il catalogo dei modelli per primo; marca e larghezza spogliate; la
spazzatura a None; la camera a colori che schiaccia a OSC tranne i filtri che si avvitano
davanti. `bayer` e' un booleano: il lettore FITS ha gia' detto se c'e' la matrice."""

import json
from pathlib import Path

import pytest

from astrolog.vocab import filters
from astrolog.vocab.filters import (
    BANDS,
    BRAND_PREFIXES,
    FILTER_MAP,
    NARROWBAND_CLIP,
    PASSBANDS,
    Passband,
    model_of,
    models,
    normalize_filter,
    passband_from_bands,
    passband_of,
)

CASES = [
    ("ha", "Hα"), ("hα", "Hα"), ("h-a", "Hα"), ("h_a", "Hα"), ("halpha", "Hα"),
    ("h-alpha", "Hα"), ("h alpha", "Hα"), ("hydrogen", "Hα"), ("hydrogen-alpha", "Hα"),
    ("[ha]", "Hα"), ("[hα]", "Hα"), ("ha 3nm", "Hα"), ("ha 5nm", "Hα"), ("ha 7nm", "Hα"),
    ("halpha 3nm", "Hα"), ("halpha 5nm", "Hα"),
    ("oiii", "OIII"), ("o3", "OIII"), ("o-iii", "OIII"), ("o_iii", "OIII"), ("[oiii]", "OIII"),
    ("oxygen", "OIII"), ("oxygen iii", "OIII"), ("oiii 3nm", "OIII"), ("oiii 5nm", "OIII"),
    ("oiii 7nm", "OIII"),
    ("sii", "SII"), ("s2", "SII"), ("s-ii", "SII"), ("s_ii", "SII"), ("[sii]", "SII"),
    ("sulfur", "SII"), ("sulphur", "SII"), ("sulfur ii", "SII"), ("sii 3nm", "SII"),
    ("sii 5nm", "SII"),
    ("hb", "Hβ"), ("hbeta", "Hβ"), ("h-beta", "Hβ"), ("hβ", "Hβ"),
    ("l", "Lum"), ("lum", "Lum"), ("luminance", "Lum"), ("luma", "Lum"), ("lum filter", "Lum"),
    ("clear", "Lum"), ("clr", "Lum"),
    ("r", "R"), ("red", "R"), ("r filter", "R"), ("g", "G"), ("green", "G"), ("g filter", "G"),
    ("b", "B"), ("blue", "B"), ("b filter", "B"),
    ("rgb", "RGB"), ("rgbcolor", "RGB"), ("rgb filter", "RGB"),
    ("osc", "OSC"), ("bayer", "OSC"), ("raw", "OSC"), ("color", "OSC"), ("colour", "OSC"),
    ("l-extreme", "L-eXtreme"), ("lextreme", "L-eXtreme"), ("l extreme", "L-eXtreme"),
    ("optolong l-extreme", "L-eXtreme"), ("l-enhance", "L-eNhance"), ("lenhance", "L-eNhance"),
    ("l enhance", "L-eNhance"), ("optolong l-enhance", "L-eNhance"), ("l-ultimate", "L-Ultimate"),
    ("lultimate", "L-Ultimate"), ("alp-t", "ALP-T"), ("alpt", "ALP-T"), ("antlia alp-t", "ALP-T"),
    ("antlia dual", "Dual-NB"), ("triad", "Triad"), ("triband", "Triad"), ("tri-band", "Triad"),
    ("idas nbz", "NBZ"), ("nbz", "NBZ"), ("quad", "QuadBand"), ("quadband", "QuadBand"),
    ("quad-band", "QuadBand"), ("quad nb", "QuadBand"), ("dual", "Dual-NB"), ("dual-nb", "Dual-NB"),
    ("dualnb", "Dual-NB"), ("dual narrowband", "Dual-NB"), ("idas lps", "LPS"), ("lps", "LPS"),
    ("lps-d1", "LPS-D1"), ("lps-p2", "LPS-P2"), ("cls", "CLS"), ("cls-ccd", "CLS"),
    ("idas cls", "CLS"), ("uhc", "UHC"), ("uhc-s", "UHC-S"),
    ("ir-cut", "IR-Cut"), ("ircut", "IR-Cut"), ("uv/ir cut", "IR-Cut"),
]  # fmt: skip


@pytest.mark.parametrize("raw, expected", CASES)
def test_spellings_to_canonical(raw, expected):
    assert normalize_filter(raw, bayer=False) == expected


REMOVED = ["h", "o", "s", "n", "656", "656nm", "500nm", "650nm", "486nm", "ir", "ir 685", "uv",
           "nb", "narrowband", "nii", "n2"]  # fmt: skip


@pytest.mark.parametrize("raw", REMOVED)
def test_removed_spellings_are_no_longer_guessed(raw):
    """Le voci tolte con Marco: una lettera sola, una lunghezza d'onda, un filtro planetario,
    un generico "banda stretta", l'NII. Non si indovinano: restano un nome libero (o None se
    sono spazzatura), e Da confermare chiede."""
    out = normalize_filter(raw, bayer=False)
    assert out not in {"Hα", "OIII", "SII", "NII", "Hβ", "R", "G", "B", "IR", "UV", "NB"}


def test_none_no_filter_open_are_not_a_band():
    for raw in ("none", "no filter", "nofilter", "no-filter", "unfiltered", "open"):
        assert normalize_filter(raw, bayer=False) == "None", raw
        assert normalize_filter(raw, bayer=True) == "OSC", raw


def test_fallback_keeps_inner_case():
    assert normalize_filter("moon", bayer=False) == "Moon"
    assert normalize_filter("ZWO", bayer=False) == "ZWO"
    assert normalize_filter("deepSkyDad", bayer=False) == "DeepSkyDad"
    assert normalize_filter("LeNhAnCe", bayer=False) == "L-eNhance"


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("7nm Ha", "Hα"),
        ("Astrodon Ha", "Hα"),
        ("3nm OIII", "OIII"),
        ("Chroma SII", "SII"),
        ("ZWO Ha", "Hα"),
        ("Optolong OIII 3nm", "OIII"),
        ("Baader Ha 7nm", "Hα"),
        ("Antlia SII 3nm", "SII"),
        ("Askar Ha", "Hα"),
        ("baader l", "Lum"),
        ("astrodon r", "R"),
    ],  # fmt: skip
)
def test_brand_and_width_are_stripped(raw, expected):
    assert normalize_filter(raw, bayer=False) == expected


def test_brands_come_from_the_catalog_plus_the_wheel_brands():
    assert {"baader", "antlia", "askar", "idas", "svbony", "optolong", "zwo"} <= BRAND_PREFIXES
    assert {"astrodon", "chroma"} <= BRAND_PREFIXES


def test_junk_is_none_but_bayer_makes_it_osc():
    for raw in ("3", "12", "-", "--", "DSLR", "dslr"):
        assert normalize_filter(raw, bayer=False) is None, raw
    assert normalize_filter("3", bayer=True) == "OSC"


def test_bayer_squashes_broadband_but_keeps_clip_filters_and_models():
    assert normalize_filter(None, bayer=True) == "OSC"
    assert normalize_filter(None, bayer=False) is None
    for raw in ("R", "green", "blue", "lum", "rgb"):
        assert normalize_filter(raw, bayer=True) == "OSC", raw
    assert normalize_filter("Ha", bayer=True) == "Hα"
    assert normalize_filter("uhc", bayer=True) == "UHC"
    assert normalize_filter("Askar D2", bayer=True) == "Colour Magic D2"
    assert normalize_filter("SV220", bayer=True) == "SV220"
    assert normalize_filter("Askar D2", bayer=False) == "Colour Magic D2"


def test_edge_cases_and_errors():
    assert normalize_filter(" ", bayer=False) == " "
    assert normalize_filter("Ha", bayer=False) == "Hα"
    with pytest.raises(Exception):  # noqa: B017 - un numero non e' un nome: solleva
        normalize_filter(656, bayer=False)


def test_models_and_map_do_not_contradict_each_other():
    contested = [
        (k, FILTER_MAP[k], model_of(k).name)
        for k in FILTER_MAP
        if model_of(k) is not None and model_of(k).name != FILTER_MAP[k]
    ]
    assert contested == []
    families = set(FILTER_MAP.values())
    assert [(m.id, n) for m in models() for n in [m.name, *m.aliases] if n in families] == []
    names = [m.name for m in models()]
    assert len(set(names)) == len(names)
    assert model_of("CLS") is None and model_of("UV/IR Cut") is None
    assert model_of("Askar D2") is not None


def test_every_canonical_name_has_a_passband_in_the_closed_domain():
    for canonical in set(FILTER_MAP.values()) | NARROWBAND_CLIP | {"None"}:
        assert passband_of(canonical) in PASSBANDS, canonical
    for m in models():
        assert m.passband in PASSBANDS, m.id
        assert passband_of(m.name) == m.passband
    assert passband_of("Hα") == "HA" and passband_of("Lum") == "L"
    assert passband_of("None") == "NONE" and passband_of("QualcosaDiIgnoto") == "UNKNOWN"
    assert not {"IR", "UV", "NB", "NII"} & PASSBANDS  # tolte con Marco
    assert "HB" in PASSBANDS


@pytest.mark.parametrize(
    "bands, expected",
    [
        (["HA"], "HA"),
        (["OIII"], "OIII"),
        (["HA", "OIII"], "DUO_HAOIII"),
        (["OIII", "HA"], "DUO_HAOIII"),  # l'ordine in cui le dichiari non conta
        (["SII", "OIII"], "DUO_SIIOIII"),
        (["HA", "SII"], "MULTI_NB"),  # una coppia senza nome suo
        (["HA", "OIII", "SII"], "TRI_NB"),
        (["HA", "OIII", "SII", "HB"], "MULTI_NB"),
        (["HA", "HA"], "HA"),  # la stessa banda due volte e' una banda
        ([], "UNKNOWN"),
        (["banda inventata"], "UNKNOWN"),  # fuori dal dominio chiuso non si conta
    ],
)
def test_passband_from_the_declared_bands(bands, expected):
    assert passband_from_bands(bands) == expected


@pytest.mark.parametrize(
    "bands, expected",
    [
        (["L", "R", "G"], "UNKNOWN"),  # tre bande larghe non hanno un'etichetta: non si inventa
        (["L", "R"], "UNKNOWN"),  # nemmeno due
        (["HA", "SII"], "MULTI_NB"),  # due strette senza un nome loro, quello si'
        (["HA", "OIII", "SII", "HB"], "MULTI_NB"),
        (["HA", "OIII", "SII"], "TRI_NB"),
        (["OSC"], "UNKNOWN"),  # "OSC" e' un'etichetta, non una banda che si dichiara
        (["NONE", "HA"], "HA"),  # "nessun filtro" non e' una banda: resta solo Ha
        (["UNKNOWN"], "UNKNOWN"),
        (["DUO_HAOIII"], "UNKNOWN"),  # nemmeno un'etichetta derivata si puo' dichiarare
    ],
)
def test_only_physical_bands_count(bands, expected):
    assert passband_from_bands(bands) == expected
    assert set(BANDS).isdisjoint({"DUO_HAOIII", "TRI_NB", "MULTI_NB", "OSC", "NONE", "UNKNOWN"})


def test_the_enum_and_the_file_the_frontend_reads_list_the_same_bands():
    """`filters.json` `passbands` is what the frontend pill test reads: it must not drift."""
    data = json.loads(Path(filters.__file__).with_name("filters.json").read_text(encoding="utf-8"))
    assert set(data["passbands"]) == {str(p) for p in Passband}
