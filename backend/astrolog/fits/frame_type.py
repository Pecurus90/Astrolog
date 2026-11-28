"""The words of `frames.image_type`, and the two signs of a rewritten file the spine reads from a
saved header: the calibration mark and the programs named. The type itself: `pipeline/card.py`."""

import re
from collections.abc import Callable, Iterator
from enum import StrEnum

from .header_keys import ACQUISITION_KEYS, WRITER_KEYS, HeaderLike, text


class FrameType(StrEnum):
    LIGHT = "light"
    DARK = "dark"
    FLAT = "flat"
    BIAS = "bias"
    DARK_FLAT = "dark_flat"
    STACK = "stack"
    # The type the header did not state: one word, looked for by the typeless question and spine.
    UNKNOWN = "unknown"


SEPARATORS_RE = re.compile(r"[\s_\-]+", re.ASCII)

# CALSTAT is letters (B bias, D dark, F flat); CALIBRAT is a FITS logical, where `F` means false.
# *FITS File Header Definitions*, Diffraction Limited (MaxIm DL help). software-ok: the source
CALIBRATION_LETTERS = "bdf"
YES_WORDS = frozenset({"t", "true", "yes", "y"})


def _as_flag(value: str | None, word_rule: Callable[[str], bool]) -> bool:
    """A number or a missing key is a flag; a word goes to the key's own rule. It arrives as
    `text`, with wrapping quotes removed: otherwise `'T'` and `'F'` swap answers."""
    if value is None:
        return False
    try:
        return bool(float(value))
    except ValueError:
        return word_rule(value.casefold())


def _calibration_letters(word: str) -> bool:
    """Closed alphabet: true only for convention letters alone (spaces, `-`, `_`; not `BDX`, not
    `B,D,F`) or a logical yes. A letter found anywhere would read `uncalibrated` as calibrated."""
    if word in YES_WORDS:
        return True
    letters = SEPARATORS_RE.sub("", word)
    return bool(letters) and all(c in CALIBRATION_LETTERS for c in letters)


def says_calibrated(header: HeaderLike) -> bool:
    """A wrong mark is worse than none: it would pass a real frame off as a copy. The other half of
    the rewrite mark, two programs named together, needs vocab and lives in `spine/rewrite`."""
    # CALIBRAT is a yes/no and nothing else: `F` is the FITS false, not the flat letter.
    return _as_flag(text(header.get("CALSTAT")), _calibration_letters) or _as_flag(
        text(header.get("CALIBRAT")), YES_WORDS.__contains__
    )


def program_names(header: HeaderLike) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Every program named, as (acquired by, written by). Whether two spellings are one program
    (`SGPro 4.4`, `Sequence Generator Pro v4.4`) is for vocab to say."""
    return tuple(_named(header, ACQUISITION_KEYS)), tuple(_named(header, WRITER_KEYS))


def _named(header: HeaderLike, keys: tuple[str, ...]) -> Iterator[str]:
    return (n for n in (text(header.get(k)) for k in keys) if n)
