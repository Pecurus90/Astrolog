"""Una frase che un ADR dichiara superata non torna nel contratto.

Un ADR scrive in testa `**Supera** in `docs/domini/x.md`: "frase"; "frase"`. Se il contratto
tiene ancora la frase, chi lo legge (una sessione, una brief per Design) riporta indietro una
decisione di Marco: e' successo col semaforo dalle sole nuvole, superato dall'ADR 0020.
"""

import re
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
RIGA = re.compile(r"^\*\*Supera\*\* in `([^`]+)`: (.+)$", re.MULTILINE)


def superate() -> list[tuple[str, str, str]]:
    """(adr, contratto, frase) per ogni frase dichiarata superata."""
    trovate = []
    for adr in sorted((RADICE / "docs" / "adr").glob("*.md")):
        for contratto, frasi in RIGA.findall(adr.read_text(encoding="utf-8")):
            trovate += [(adr.name, contratto, f) for f in re.findall(r'"([^"]+)"', frasi)]
    return trovate


def test_adr_0020_declares_what_it_supersedes():
    assert any(adr.startswith("0020") for adr, _, _ in superate())


def test_a_superseded_sentence_is_gone_from_its_contract():
    tornate = [
        f"{adr}: {contratto} dice ancora {frase!r}"
        for adr, contratto, frase in superate()
        # a removed document holds no sentence any more
        if (RADICE / contratto).exists()
        and frase.lower() in (RADICE / contratto).read_text(encoding="utf-8").lower()
    ]
    assert not tornate, tornate
