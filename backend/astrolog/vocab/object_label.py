"""Il nome dell'oggetto com'e' scritto nell'header, ripulito: spazi ai bordi e parole di
tavolozza in coda ("M42 RGB", "M31 LRGB final" -> "M42", "M31").

Vincolo non ovvio: le SIGLE (M, NGC, Caldwell, Sh2...) non si riconoscono qui con una
lista scritta a mano: le sa il catalogo, e le riconosce lo stadio identify (Marco,
2026-09-06). Qui non si inventa niente: un nome che non si riconosce resta com'e'.
"""

PALETTE_NOISE = frozenset(
    {"rgb", "lrgb", "hargb", "rgbha", "lrgbha", "sho", "hoo", "hso", "final", "crop", "reprocessed"}
)


def _strip_palette_suffix(s):
    tokens = s.split()
    if len(tokens) <= 1:
        return s
    removed = False
    while len(tokens) > 1 and tokens[-1].lower() in PALETTE_NOISE:
        tokens.pop()
        removed = True
    return " ".join(tokens) if removed else s


def clean_object_name(raw):
    """Il nome senza spazi ai bordi e senza le parole di tavolozza in coda. Un valore vuoto
    o None torna com'e'; un non-stringa solleva (non e' un nome)."""
    if not raw:
        return raw
    return _strip_palette_suffix(raw.strip())
