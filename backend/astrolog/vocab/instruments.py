"""The kinds of instrument: the words of the `instruments.kind` CHECK, in its order."""

from enum import StrEnum


# One member per kind: a rule elsewhere names it instead of repeating the string.
class InstrumentKind(StrEnum):
    OPTICS = "optics"
    CAMERA = "camera"
    MOUNT = "mount"
    REDUCER = "reducer"
    FILTER_WHEEL = "filter_wheel"
    GUIDE_SCOPE = "guide_scope"
    GUIDE_CAMERA = "guide_camera"
    FOCUSER = "focuser"
    OAG = "oag"
    SPACER = "spacer"


# The words of the `instruments.optical_design` CHECK (ADR 0021).
class OpticalDesign(StrEnum):
    REFRACTOR = "refractor"
    NEWTONIAN = "newtonian"
    SCT = "sct"
    RC = "rc"
    MAKSUTOV = "maksutov"
    CAMERA_LENS = "camera_lens"
    OTHER = "other"


# The words of the `filter_size` CHECKs, wheel and filter alike (ADR 0021).
class FilterSize(StrEnum):
    INCH_1_25 = "1.25in"
    MM_31 = "31mm"
    MM_36 = "36mm"
    INCH_2 = "2in"
    MM_50_SQUARE = "50mm_square"
