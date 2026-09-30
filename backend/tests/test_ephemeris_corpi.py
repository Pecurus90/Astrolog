"""Dove sta un corpo del cielo: le regole di `ephemeris/corpi.py`, che Luna e Sole dividono.

Le prove del conto vero stanno nei due file dei corpi; qui c'e' cio' che vale per tutti e due.
"""

import pytest

from astrolog.ephemeris import corpi


def test_a_conversion_that_does_not_happen_is_said_not_ignored():
    """Se astropy non converte, il conto dopo lavorerebbe **su niente** senza accorgersene.

    E' una riga dei vincoli non ovvi di `corpi.py`, e finche' non c'era questa prova nessuno la
    teneva: togliendo il `raise` restava tutto verde. Astropy dichiara che la conversione puo'
    tornare `None`, quindi qui si finge proprio quello."""

    class NonConverte:
        def transform_to(self, _sistema):
            return None

    with pytest.raises(RuntimeError, match="non ha convertito"):
        corpi.convertito(NonConverte(), object())
