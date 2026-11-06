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
