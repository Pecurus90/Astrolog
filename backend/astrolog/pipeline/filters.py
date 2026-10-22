"""Written filter name to filter, exact (ADR 0031): standard list, user answers, user filters.
Unmatched name asked once; answer holds for every scan after."""

import sqlite3
from enum import StrEnum

from ..db.transaction import transaction


class Band(StrEnum):
    L = "l"
    R = "r"
    G = "g"
    B = "b"
    HA = "ha"
    HB = "hb"
    OIII = "oiii"
    SII = "sii"
    UVIR = "uvir"


class StandardFilter(StrEnum):
    L = "l"
    R = "r"
    G = "g"
    B = "b"
    HA = "ha"
    OIII = "oiii"
    SII = "sii"
    HB = "hb"
    HA_OIII = "ha_oiii"
    SII_OIII = "sii_oiii"
    UVIR = "uvir"  # luminance on mono, colour with UV/IR on colour camera: read later by camera
    NONE = "none"

    @property
    def bands(self) -> tuple[Band, ...]:
        return _BANDS[self]


_BANDS = {
    StandardFilter.L: (Band.L,),
    StandardFilter.R: (Band.R,),
    StandardFilter.G: (Band.G,),
    StandardFilter.B: (Band.B,),
    StandardFilter.HA: (Band.HA,),
    StandardFilter.OIII: (Band.OIII,),
    StandardFilter.SII: (Band.SII,),
    StandardFilter.HB: (Band.HB,),
    StandardFilter.HA_OIII: (Band.HA, Band.OIII),
    StandardFilter.SII_OIII: (Band.SII, Band.OIII),
    StandardFilter.UVIR: (Band.UVIR,),
    StandardFilter.NONE: (),
}

# Written forms, normalized (filter_key). ASCII only: FITS header has no Greek alpha, beta.
# Duals: no common form, reached by answer only. Others asked (O3, S2, Hb, Lum: no source).
FORMS = {
    "l": StandardFilter.L,  # LRGB: Chroma LRGB sets, Astronomik L-RGB
    "r": StandardFilter.R,
    "g": StandardFilter.G,
    "b": StandardFilter.B,
    "luminance": StandardFilter.L,  # LRGB spelled out; Astronomik L-2 "Luminanz"
    "red": StandardFilter.R,
    "green": StandardFilter.G,
    "blue": StandardFilter.B,
    "ha": StandardFilter.HA,  # Chroma, Baader product names
    "h-alpha": StandardFilter.HA,
    "oiii": StandardFilter.OIII,
    "o iii": StandardFilter.OIII,  # Chroma
    "sii": StandardFilter.SII,
    "s ii": StandardFilter.SII,  # Chroma
    "h-beta": StandardFilter.HB,  # Chroma
    "h": StandardFilter.HA,  # H, O, S: map decision 10, every camera
    "o": StandardFilter.OIII,
    "s": StandardFilter.SII,
    "uv/ir-cut": StandardFilter.UVIR,  # Baader UV/IR-Cut
    "none": StandardFilter.NONE,  # chosen by the owner with the list
    "no filter": StandardFilter.NONE,
}


def filter_key(written: str) -> str:
    """No case, no blanks at ends, inner blanks one: 'Ha  7nm' is 'ha 7nm'."""
    return " ".join(written.casefold().split())


def resolve(conn: sqlite3.Connection, written: str) -> None:
    """Writes what written name is: standard, then user filter's own name, then answer; none:
    to ask. Name of your filter always means that filter, whatever came first."""
    key = filter_key(written)
    standard, name = FORMS.get(key), None
    if standard is None:
        name = _filter_named(conn, key)
    if standard is None and name is None:
        row = conn.execute(
            "SELECT standard, filter_name FROM pipeline_filter_answers WHERE written_key = ?",
            (key,),
        ).fetchone()
        if row is not None:
            standard, name = row["standard"], row["filter_name"]
    conn.execute(
        "INSERT OR REPLACE INTO pipeline_filter_spellings (written, key, standard, filter_name)"
        " VALUES (?, ?, ?, ?)",
        (written, key, standard, name),
    )


def answer(
    conn: sqlite3.Connection,
    written: str,
    target: StandardFilter | str,
    bands: dict[Band, float | None] | None = None,
) -> None:
    """Written name is `target`: standard, or user filter by name, born here with its bands
    (width nm, None: not said). Every spelling of same key, or of filter name, follows."""
    key = filter_key(written)
    if not key or key in FORMS:
        raise ValueError(f"{written!r}: standard spelling or empty, never answered")
    own = _filter_named(conn, key)
    if own is not None and (isinstance(target, StandardFilter) or target.strip() != own):
        raise ValueError(f"{written!r}: name of your filter {own!r}, it means that filter")
    with transaction(conn):
        name_key = key  # new filter: spellings of its own name follow too
        if isinstance(target, StandardFilter):
            conn.execute(
                "INSERT OR REPLACE INTO pipeline_filter_answers (written_key, standard)"
                " VALUES (?, ?)",
                (key, target),
            )
        else:
            name = _user_filter(conn, target, bands)
            name_key = filter_key(name)
            conn.execute(
                "INSERT OR REPLACE INTO pipeline_filter_answers (written_key, filter_name)"
                " VALUES (?, ?)",
                (key, name),
            )
        spellings = conn.execute(
            "SELECT written FROM pipeline_filter_spellings WHERE key IN (?, ?)", (key, name_key)
        ).fetchall()
        for row in spellings:
            resolve(conn, row["written"])


def _user_filter(
    conn: sqlite3.Connection, name: str, bands: dict[Band, float | None] | None
) -> str:
    """Existing by exact name, or new: never named as standard form, never two on one key."""
    name = name.strip()
    if conn.execute("SELECT 1 FROM pipeline_filters WHERE name = ?", (name,)).fetchone():
        return name
    key = filter_key(name)
    if not key or key in FORMS or not bands:
        raise ValueError(f"{name!r}: new filter needs own name and its bands")
    if _filter_named(conn, key) is not None:
        raise ValueError(f"{name!r}: another filter has this name")
    conn.execute("INSERT INTO pipeline_filters (name) VALUES (?)", (name,))
    conn.executemany(
        "INSERT INTO pipeline_filter_bands (filter_name, band, width_nm) VALUES (?, ?, ?)",
        [(name, band, width) for band, width in bands.items()],
    )
    return name


def _filter_named(conn: sqlite3.Connection, key: str) -> str | None:
    """User filter whose name has this key. Key from name every time: rename never stale."""
    for row in conn.execute("SELECT name FROM pipeline_filters"):
        if filter_key(row["name"]) == key:
            return str(row["name"])
    return None
