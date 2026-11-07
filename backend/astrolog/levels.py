"""A measure's word, the weather's and a frame's alike (glossario.md, `level`): one home under the
weather and the pipeline, which do not know each other."""

from enum import StrEnum


class Verdict(StrEnum):
    GO = "go"
    MARGINAL = "marginal"
    NOGO = "nogo"
