"""I vocabolari dei nomi: la pulizia del nome dell'oggetto (le sigle le sa il catalogo),
il software di ripresa (i quattro supportati e basta), i valori dell'header per gli alias."""

import pytest

from astrolog.vocab.header_value import normalize_header_value
from astrolog.vocab.object_label import clean_object_name
from astrolog.vocab.software import normalize_software


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("M 31", "M 31"),
        ("  Andromeda  ", "Andromeda"),
        ("m31", "m31"),  # la sigla non si riscrive qui: e' identify, col catalogo
        ("Caldwell 14", "Caldwell 14"),
        ("M42 RGB", "M42"),
        ("M31 LRGB", "M31"),
        ("NGC7000 HaRGB", "NGC7000"),
        ("M 42 SHO", "M 42"),
        ("M31 final", "M31"),
        ("M42 HaRGB final", "M42"),
        ("Veil RGB", "Veil"),
        ("RGB", "RGB"),  # un token solo non si tocca
        ("   ", ""),
        ("", ""),
        (None, None),
    ],
)
def test_object_name_cleanup(raw, expected):
    assert clean_object_name(raw) == expected


def test_object_name_rejects_non_strings():
    with pytest.raises(AttributeError):
        clean_object_name(31)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("N.I.N.A. 3.1.2.9001 (x64)", "N.I.N.A."),
        ("ZWO ASIAIR Plus", "ASIAIR"),
        ("Voyager 2.3", "Voyager"),
        ("Sequence Generator Pro 4.4", "Sequence Generator Pro"),
        ("SGPro", "Sequence Generator Pro"),
        # tutto il resto resta com'e' scritto, in software_raw: non e' supportato
        # software-ok: e' la lista dei NEGATIVI -- una regola sui nomi senza i nomi
        # che non deve prendere e' un test a meta', e questa e' la sua casa
        ("Siril 1.2.0", None),  # software-ok
        ("MaxIm DL Version 6.20", None),  # software-ok
        ("SharpCap v4.0.8208.0, 32 bit", None),  # software-ok
        ("QualcosaDiIgnoto 1.0", None),
        (None, None),
        ("", None),
    ],
)
def test_software(raw, expected):
    assert normalize_software(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Esprit 100ED", "esprit 100ed"),
        ("ESPRIT  100ED", "esprit 100ed"),
        ("   esprit 100ed   ", "esprit 100ed"),
        ("ZWO\tASI2600MM \t Pro", "zwo asi2600mm pro"),
        (None, ""),
        ("", ""),
        ("   \t  ", ""),
        ("ASI-2600MM Pro", "asi-2600mm pro"),
        ("  Caméra Ñoño  100  ", "caméra ñoño 100"),
        ("ASCOM.ToupTek.AAF", "ascom touptek aaf"),
        ("ZWO Focuser (1)", "zwo focuser"),
        ("Cam (2) X", "cam (2) x"),
        ("ATR2600M(USB2.0)", "atr2600m(usb2 0)"),
        ("Askar 103Apo", "askar 103apo"),
    ],
)
def test_header_value(raw, expected):
    assert normalize_header_value(raw) == expected


def test_header_value_is_idempotent_and_keeps_distinct_things_distinct():
    v = normalize_header_value("ASCOM ToupTek FilterWheel")
    assert normalize_header_value(v) == v
    assert (
        len(
            {
                normalize_header_value(x)
                for x in ["ZWO Focuser", "Gemini Focuser Pro", "ASCOM ToupTek AAF"]
            }
        )
        == 3
    )
