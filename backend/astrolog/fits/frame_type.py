"""Missing or unrecognised type -> `unknown`, never "assume light": those frames enter and are asked
about. A stack only from strong signals, never from exposure: a long light must not vanish."""

import re
from collections.abc import Callable, Iterator

from .header_keys import ACQUISITION_KEYS, WRITER_KEYS, HeaderLike, as_int, get, text

# Without separators, since spellings are compared without them (`_type_of_word`): Voyager's and
# SGP's spelling is unknown, and a spelling must not decide whether a calibration enters.
FRAME_TYPES = {
    "light": "light",
    "lightframe": "light",
    "science": "light",
    "scienceframe": "light",
    "object": "light",
    "objectframe": "light",
    "exposure": "light",
    "dark": "dark",
    "darkframe": "dark",
    "flat": "flat",
    "flatframe": "flat",
    "flatfield": "flat",
    "bias": "bias",
    "biasframe": "bias",
    "offset": "bias",
    "zero": "bias",
    "darkflat": "dark_flat",
    "flatdark": "dark_flat",
}

CALIBRATION_TYPES = frozenset({"dark", "flat", "bias", "dark_flat"})
# The type the header did not state: one word, looked for by the typeless question and the spine.
UNKNOWN = "unknown"

SEPARATORS_RE = re.compile(r"[\s_\-]+", re.ASCII)

STACK_COUNT_KEYS = ("STACKCNT", "NCOMBINE", "NIMAGES")
STACK_WORD_RE = re.compile(r"\b(?:master|integration|stack|stacked)\b", re.IGNORECASE | re.ASCII)
# Whoever does not count the summed frames lists them in HISTORY as numbered keys. CALSTAT and
# CALIBRAT stay out on purpose: calibrated is not summed.
STACK_SOURCE_RE = re.compile(r"\bSOURCE\d+\b", re.ASCII)

# CALSTAT is letters (B bias, D dark, F flat); CALIBRAT is a FITS logical, where `F` means false.
# *FITS File Header Definitions*, Diffraction Limited (MaxIm DL help). software-ok: the source
CALIBRATION_LETTERS = "bdf"
YES_WORDS = frozenset({"t", "true", "yes", "y"})


def is_stack(header: HeaderLike) -> bool:
    """A count key above one (a count of one is a single frame), a stack word in IMAGETYP or
    OBJECT, or the list of sources in HISTORY."""
    if any((as_int(header.get(k)) or 0) > 1 for k in STACK_COUNT_KEYS):
        return True
    for key in ("IMAGETYP", "OBJECT"):
        v = header.get(key)
        if isinstance(v, str) and STACK_WORD_RE.search(v):
            return True
    return any(STACK_SOURCE_RE.search(str(line)) for line in header.get("HISTORY", []))


def _type_of_word(value: str | None) -> str | None:
    """Compared without separators and in the singular: `Dark Frame`, `DARK-FRAME`, `darkframe`
    and `darks` are all a dark. The only reader of the vocabulary."""
    word = SEPARATORS_RE.sub("", (value or "").lower())
    for candidate in (word, word.removesuffix("es"), word.removesuffix("s")):
        if candidate in FRAME_TYPES:
            return FRAME_TYPES[candidate]
    return None


def _calibration_in_object(header: HeaderLike) -> str | None:
    """A calibration library may write `IMAGETYP = LIGHT` and `OBJECT = darkflat`. The whole field,
    never a substring: `Dark Nebula` and `Flaming Star` are real objects."""
    kind = _type_of_word(text(get(header, "object")))
    return kind if kind in CALIBRATION_TYPES else None


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


def image_type(header: HeaderLike) -> str:
    """`light | dark | flat | bias | dark_flat | stack | unknown`."""
    if is_stack(header):
        return "stack"
    calibration = _calibration_in_object(header)
    if calibration is not None:
        return calibration
    return _type_of_word(text(get(header, "image_type"))) or UNKNOWN
