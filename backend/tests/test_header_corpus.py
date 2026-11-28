"""Il corpus di header veri (`tests/header/*.txt`): ogni regola di lettura attraversa TUTTI
i file, non uno. Un file e' un header come testo, una card per riga (`KEY = valore /
commento`), preso da un archivio reale o da un post pubblico, mai scritto a mano da memoria;
le righe che iniziano con `#` dicono da dove viene. Nel corpus nessuna coordinata reale.
Lo legge il lettore dell'app (`pipeline/scanner.py`) e la scheda (`pipeline/card.py`)."""

import io
import re
from pathlib import Path

import pytest

from astrolog.fits.header_wcs import solved, wcs_rotation_deg, wcs_scale
from astrolog.pipeline.card import FrameType, read_card
from astrolog.pipeline.scanner import program_of, read_header
from astrolog.pipeline.values import Program
from astrolog.spine.rewrite import rewrite_mark
from conftest import corpus_lines, fits_bytes

CORPUS = Path(__file__).with_name("header")
FILES = sorted(CORPUS.glob("*.txt"))

# Il programma atteso viene dal nome del file: e' la prova che il lettore lo riconosce.
# Nel corpus entrano solo i programmi verificati (ADR 0029, 0033).
EXPECTED_PROGRAM = {"nina": Program.NINA, "asiair": Program.ASIAIR}


def load(path):
    """Le card come le legge la scansione: da un FITS fatto con quelle righe."""
    header = read_header(io.BytesIO(fits_bytes(corpus_lines(path.name))))
    assert header is not None, path.name
    return header.cards


def card_of(path):
    values = load(path)
    program = program_of(values)
    assert program is not None, path.name
    return read_card(program, values)


def test_the_corpus_is_not_empty():
    assert len(FILES) >= 2


@pytest.mark.parametrize("path", FILES, ids=[p.stem for p in FILES])
def test_header_corpus_reads_every_file(path):
    values = load(path)
    assert program_of(values) == EXPECTED_PROGRAM[path.stem.split("_")[0]]
    card = card_of(path)
    assert card.frame_type in set(FrameType)
    assert isinstance(card.exposure_s, float) or card.exposure_s is None
    assert card.width and card.height
    # Un file appena scattato non porta il marchio di riscrittura: se lo portasse, la regola
    # della copia calibrata scambierebbe un grezzo per una copia. E' l'unico banco vero che
    # quella regola ha -- gli header di chi elabora non entrano nel corpus.
    assert rewrite_mark(values) is None


# Le chiavi che geolocalizzano, scritte a mano e NON prese dal lettore. E' il punto: la guardia
# deve guardare cio' che tradisce il sito, non cio' che il lettore sa leggere -- costruita
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
    for key in GEO_KEYS:
        if isinstance(header.get(key), int | float):
            assert float(header[key]) == int(float(header[key])), f"{key} non anonimizzata"
    if isinstance(header.get("AIRMASS"), int | float):
        assert round(float(header["AIRMASS"]), 1) == float(header["AIRMASS"]), (
            "AIRMASS non anonimizzata"
        )
    for key in ("OBSERVER", "SWOWNER"):
        assert header.get(key) in (None, "", "Osservatore", "ZWO"), key


# Un sito si riconosce dal nome della chiave, non da un elenco: GEOLAT, SITE, OBSERVAT, una
# grafia che nessun programma ha ancora scritto. ALT/AZ: altezza e azimut del puntamento; LAT non
# dopo F o P, che e' la correzione del flat (FLATCOR) o la scala di lastra (PLATESCL).
PLACE_KEY = re.compile(
    r"(?<![FP])LAT|LONG|LON$|ELEV|GEO|SITE|OBSERVAT|LOCAT|^ALT|ALT(ITUDE)?$|AZ(IMUTH)?$"
)
PERSON_KEY = re.compile(r"OBSERVER|OWNER|AUTHOR|USER")
PLACEHOLDERS = (None, "", "Osservatore", "ZWO")


@pytest.mark.parametrize("path", FILES, ids=[p.stem for p in FILES])
def test_no_place_or_person_in_the_corpus_whatever_the_key_is_called(path):
    """Ogni chiave che per nome dice un sito porta al massimo il grado, o un testo di comodo; ogni
    chiave che dice una persona, un nome di comodo. `DATE-LOC` resta: dice il fuso, non il posto."""
    for key, value in load(path).items():
        if PLACE_KEY.search(key) and isinstance(value, int | float) and not isinstance(value, bool):
            assert float(value) == int(float(value)), f"{key} non anonimizzata"
        elif PLACE_KEY.search(key) or PERSON_KEY.search(key):
            assert value in PLACEHOLDERS, f"{key} = {value!r} puo' dire un posto o una persona"


def test_specific_lessons_from_the_corpus():
    """Le cose che il corpus insegna e che un lettore scritto su un software solo perde."""
    nina = card_of(CORPUS / "nina.txt")
    assert nina.start_utc is not None
    assert nina.start_utc.isoformat() == "2025-06-29T21:11:33.412000+00:00"  # DATE-OBS, UTC
    assert nina.exposure_s == 120.0 and nina.frame_type is FrameType.LIGHT
    assert nina.camera == "ATR2600M(USB2.0)" and nina.focal_mm == 560.0
    crudo = load(CORPUS / "asiair.txt")
    asiair = card_of(CORPUS / "asiair.txt")
    assert asiair.bayer is True and asiair.camera == "Canon EOS 700D"
    assert asiair.pixel_um == 4.29  # float32 ripulita al confine del lettore
    # il cielo scritto nell'header non e' un campo del frame (lo misura il solver), ma le
    # funzioni che leggono l'esito di ASTAP sono queste, e qui si provano su un header VERO
    assert solved(crudo) is True and wcs_rotation_deg(crudo) is not None
    assert wcs_scale(crudo) == pytest.approx(1.58, abs=0.01)  # dalla matrice CD
    assert asiair.mount == "EQMod Mount" and asiair.optics is None  # TELESCOP e' la montatura
    # I tre strumenti che il programma nomina **sul singolo frame**, letti da header veri e non dal
    # banco sintetico -- che quelle sigle le scriviamo noi, e direbbe di si' anche se fossero
    # sbagliate. N.I.N.A. scrive ruota e focheggiatore, l'ASIAIR la camera di guida, e nessuno dei
    # due nomina la guida.
    assert nina.filter_wheel == "ASCOM ToupTek FilterWheel"
    assert nina.focuser == "ASCOM ToupTek AAF"
    assert nina.guide_camera is None
    assert asiair.guide_camera == "ZWO ASI120MM-S"
    assert asiair.filter_wheel is None and asiair.focuser is None


def test_the_same_software_writes_a_different_mount_for_every_user():
    """Tre utenti con l'ASIAIR, tre header veri: in `TELESCOP` c'e' la **montatura**, e il nome
    cambia da persona a persona.

    E' la ragione per cui il rimedio non puo' essere una lista di nomi di montature -- con un
    header solo quella lista sembrava la risposta giusta, e sarebbe fallita al secondo utente.
    Misurato il 14/9/2026 su 171 header di altri utenti: `EQMod Mount` per due di loro,
    `ZWO AM3` per un terzo. Se un giorno nel corpus restasse un ASIAIR solo, questo test cade e
    dice perche'."""
    asiair = [card_of(p) for p in FILES if p.stem.split("_")[0] == "asiair"]
    assert len(asiair) >= 3, "servono tre ASIAIR, di utenti diversi"
    assert {c.mount for c in asiair} >= {"EQMod Mount", "ZWO AM3"}
    assert all(c.optics is None for c in asiair)
