"""Il corpus di header veri (`tests/header/*.txt`): ogni regola di lettura attraversa TUTTI
i file, non uno. Un file e' un header come testo, una card per riga (`KEY = valore /
commento`), preso da un archivio reale o da un post pubblico, mai scritto a mano da memoria;
le righe che iniziano con `#` dicono da dove viene. Nel corpus nessuna coordinata reale."""

import re
from pathlib import Path

import pytest

from astrolog.fits.frame_type import CALIBRATION_TYPES
from astrolog.fits.header_fields import extract_fields
from astrolog.fits.header_keys import KEYS
from astrolog.fits.header_wcs import solved, wcs_rotation_deg, wcs_scale
from astrolog.spine.rewrite import rewrite_mark
from astrolog.vocab.software import normalize_software

CORPUS = Path(__file__).with_name("header")
FILES = sorted(CORPUS.glob("*.txt"))
CARD_RE = re.compile(r"^([A-Z0-9_\-]{1,8})\s*=\s*(.*?)\s*(?:/(.*))?$")

# Il software atteso viene dal nome del file: e' la prova che il vocabolario lo riconosce.
# Nel corpus entrano solo i quattro di ripresa (Marco, 2026-09-06), e mancano Voyager e SGP.
EXPECTED_SOFTWARE = {"nina": "N.I.N.A.", "asiair": "ASIAIR"}


def _value(raw):
    raw = raw.strip()
    if raw.startswith("'"):
        return raw.strip("'").rstrip()
    if raw in ("T", "F"):
        return raw == "T"
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw)
        except ValueError:
            return raw or None


def load(path):
    header = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        m = CARD_RE.match(line)
        if m:
            header[m.group(1)] = _value(m.group(2))
    return header


def test_the_corpus_is_not_empty():
    assert len(FILES) >= 2


@pytest.mark.parametrize("path", FILES, ids=[p.stem for p in FILES])
def test_header_corpus_reads_every_file(path):
    header = load(path)
    fields = extract_fields(header, str(path))
    assert fields.image_type in CALIBRATION_TYPES | {"light", "unknown", "stack"}
    assert isinstance(fields.exposure_s, float) or fields.exposure_s is None
    assert fields.naxis1 and fields.naxis2
    stem = path.stem.split("_")[0]
    expected = EXPECTED_SOFTWARE[stem]
    assert normalize_software(fields.software_raw) == expected, fields.software_raw
    # Un file appena scattato non porta il marchio di riscrittura: se lo portasse, la regola
    # della copia calibrata scambierebbe un grezzo per una copia. E' l'unico banco vero che
    # quella regola ha -- gli header di chi elabora non entrano nel corpus, che e' dei quattro.
    assert rewrite_mark(header) is None


# Le chiavi che geolocalizzano, scritte a mano e NON prese da `KEYS`. E' il punto: la guardia
# deve guardare cio' che tradisce il luogo, non cio' che il lettore sa leggere -- costruita
# dagli alias, era cieca proprio sulla grafia nuova, e nel corpus sono finite le coordinate di
# casa a dieci metri. Qui dentro va ogni nome geografico che si incontra, letto o no.
GEO_KEYS = (
    "SITELAT", "SITELONG", "SITEELEV", "LAT-OBS", "LONG-OBS", "ALT-OBS",
    "OBSGEO-B", "OBSGEO-L", "OBSGEO-H", "OBSGEO-X", "OBSGEO-Y", "OBSGEO-Z",
    "CENTALT", "CENTAZ", "OBJCTALT", "OBJCTAZ", "ELEVATIO", "LATITUDE", "LONGITUD",
)  # fmt: skip


@pytest.mark.parametrize("path", FILES, ids=[p.stem for p in FILES])
def test_no_real_site_coordinates_in_the_corpus(path):
    """Non solo SITELAT/SITELONG: altezza e azimut a molti decimali, con data e coordinate,
    ricostruiscono il sito. Nel corpus stanno al grado, e la massa d'aria al decimo."""
    header = load(path)
    lette = ("site_lat", "site_lon", "site_elev")
    assert set(sum((KEYS[k] for k in lette), ())) <= set(GEO_KEYS), (
        "una grafia del luogo che il lettore conosce e la guardia no"
    )
    for key in GEO_KEYS:
        if key in header and header[key] is not None:
            assert float(header[key]) == int(float(header[key])), f"{key} non anonimizzata"
    if header.get("AIRMASS") is not None:
        assert round(float(header["AIRMASS"]), 1) == float(header["AIRMASS"]), (
            "AIRMASS non anonimizzata"
        )
    for key in ("OBSERVER", "SWOWNER"):
        assert header.get(key) in (None, "", "Osservatore", "ZWO"), key


def test_specific_lessons_from_the_corpus():
    """Le cose che il corpus insegna e che un lettore scritto su un software solo perde."""
    nina = extract_fields(load(CORPUS / "nina.txt"), "x")
    assert nina.date_obs == "2025-06-29T21:11:33.412"  # DATE-OBS (UTC), mai DATE-LOC
    assert nina.exposure_s == 120.0 and nina.image_type == "light"
    assert nina.instrument_raw == "ATR2600M(USB2.0)" and nina.focal_mm == 560.0
    crudo = load(CORPUS / "asiair.txt")
    asiair = extract_fields(crudo, "x")
    assert asiair.bayer_pattern == "RGGB" and asiair.instrument_raw == "Canon EOS 700D"
    assert asiair.pixel_size_um == 4.29  # float32 ripulita al confine del lettore
    # il cielo scritto nell'header non e' un campo della posa (lo misura il solver), ma le
    # funzioni che lo leggono sono le stesse, e qui si provano su un header VERO
    assert solved(crudo) is True and wcs_rotation_deg(crudo) is not None
    assert wcs_scale(crudo) == pytest.approx(1.58, abs=0.01)  # dalla matrice CD
    assert asiair.telescope_raw == "EQMod Mount"  # ASIAIR mette la montatura in TELESCOP
    # I tre pezzi che il programma nomina **sulla singola posa**, letti da header veri e non dal
    # banco sintetico -- che quelle sigle le scriviamo noi, e direbbe di si' anche se fossero
    # sbagliate. N.I.N.A. scrive ruota e focheggiatore, l'ASIAIR la camera di guida, e nessuno dei
    # due nomina la guida.
    assert nina.filter_wheel_raw == "ASCOM ToupTek FilterWheel"
    assert nina.focuser_raw == "ASCOM ToupTek AAF"
    assert nina.guide_camera_raw is None
    assert asiair.guide_camera_raw == "ZWO ASI120MM-S"
    assert asiair.filter_wheel_raw is None and asiair.focuser_raw is None


def test_the_same_software_writes_a_different_mount_for_every_user():
    """Tre utenti con l'ASIAIR, tre header veri: in `TELESCOP` c'e' la **montatura**, e il nome
    cambia da persona a persona.

    E' la ragione per cui il rimedio non puo' essere una lista di nomi di montature -- con un
    header solo quella lista sembrava la risposta giusta, e sarebbe fallita al secondo utente.
    Misurato il 14/9/2026 su 171 header di altri utenti: `EQMod Mount` per due di loro,
    `ZWO AM3` per un terzo. Se un giorno nel corpus restasse un ASIAIR solo, questo test cade e
    dice perche'."""
    asiair = [extract_fields(load(p), str(p)) for p in FILES if p.stem.split("_")[0] == "asiair"]
    assert len(asiair) >= 3, "servono tre ASIAIR, di utenti diversi"
    montature = {f.telescope_raw for f in asiair}
    assert montature >= {"EQMod Mount", "ZWO AM3"}, montature
