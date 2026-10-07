"""I filtri in un ordine solo, in tutta l'app (Marco, 7/10/2026): L, R, G, B, Ha, OIII, SII, poi i
filtri a colori, poi gli altri riconosciuti per banda, poi gli sconosciuti, "senza filtro" ultimo.
A pari banda, per nome. Supera "dal piu' usato": la stessa pastiglia sta sempre allo stesso posto.
"""

from astrolog.api import review_page
from astrolog.clock import now_iso
from astrolog.spine import archive, counts, filters_used, inventory
from astrolog.vocab.filters import DISPLAY_ORDER, Passband

# Nate in disordine, e le ore crescono verso la fine dell'ordine giusto: "dal piu' usato" darebbe
# l'ordine rovesciato, l'alfabeto un terzo ordine ancora.
FILTRI = [
    ("Zeta ignoto", "UNKNOWN"),
    ("L-eNhance", "DUO_HAOIII"),
    ("Sii 3nm", "SII"),
    ("Ha 7nm", "HA"),
    ("A colori", "OSC"),
    ("Blu", "B"),
    ("Oiii 3nm", "OIII"),
    ("Ha 3nm", "HA"),
    ("Rosso", "R"),
    ("Lum", "L"),
]
ATTESO = [
    "Lum",
    "Rosso",
    "Blu",
    "Ha 3nm",
    "Ha 7nm",
    "Oiii 3nm",
    "Sii 3nm",
    "A colori",
    "L-eNhance",
    "Zeta ignoto",
]


def banco(conn):
    """Un oggetto ripreso con tutti i filtri; il tempo cresce col posto nell'ordine giusto."""
    oggetto = conn.execute(
        "INSERT INTO objects(identity_confidence, created_at) VALUES('high', ?)", (now_iso(),)
    ).lastrowid
    conn.execute(
        "INSERT INTO object_names(object_id, name, origin, is_primary)"
        " VALUES(?, 'Campo', 'user', 1)",
        (oggetto,),
    )
    ids = {}
    for nome, banda in FILTRI:
        ids[nome] = conn.execute(
            "INSERT INTO filters(name, passband, created_at) VALUES(?, ?, ?)",
            (nome, banda, now_iso()),
        ).lastrowid
    ids["Nessun filtro"] = conn.execute(
        "INSERT INTO filters(name, passband, is_none, created_at) VALUES('Nessun filtro', 'NONE',"
        " 1, ?)",
        (now_iso(),),
    ).lastrowid
    for secondi, nome in enumerate(["Nessun filtro", *reversed(ATTESO)], start=1):
        conn.execute(
            "INSERT INTO frames(frame_hash, image_type, header_json, created_at, object_id,"
            " filter_id, exposure_s) VALUES(?, 'light', '[]', ?, ?, ?, ?)",
            (f"h-{nome}", now_iso(), oggetto, ids[nome], 60.0 / secondi),
        )
    return oggetto


def test_every_band_has_one_place_and_no_filter_is_last():
    assert sorted(DISPLAY_ORDER) == sorted(Passband)
    assert len(set(DISPLAY_ORDER)) == len(DISPLAY_ORDER)
    assert DISPLAY_ORDER[:7] == tuple(
        Passband(b) for b in ("L", "R", "G", "B", "HA", "OIII", "SII")
    )
    assert DISPLAY_ORDER[7:10] == (Passband.OSC, Passband.OSC_LP, Passband.OSC_UVIR)
    assert DISPLAY_ORDER[-2:] == (Passband.UNKNOWN, Passband.NO_FILTER)


def test_a_night_or_an_object_lists_its_filters_in_the_one_order(conn):
    """Le Notti e le righe dell'Archivio chiedono alla stessa casa."""
    oggetto = banco(conn)

    usati = filters_used.of(conn, counts.Subject.OBJECT, [oggetto])[oggetto]

    assert [f["name"] for f in usati] == [*ATTESO, "Nessun filtro"]


def test_the_archive_dropdown_offers_the_filters_in_the_one_order(conn):
    banco(conn)

    assert archive.choices(conn)["filters"] == [*ATTESO, "Nessun filtro"]


def test_the_gear_page_lists_your_filters_in_the_one_order(conn):
    """Anche i filtri gia' contati: la posizione del contatore vale per i corredi, non per loro."""
    banco(conn)
    for posto, (fid,) in enumerate(conn.execute("SELECT id FROM filters ORDER BY id DESC")):
        conn.execute(
            "INSERT INTO gear_usage(subject, subject_id, frames, objects_json, position)"
            " VALUES('filter', ?, 1, '[]', ?)",
            (fid, posto),
        )

    assert [f["name"] for f in inventory.filters(conn)] == ATTESO


def test_da_confermare_offers_your_filters_in_the_one_order(conn):
    """Uno dei miei: gli sconosciuti e "senza filtro" non si scelgono (`gear.filter_target`)."""
    banco(conn)

    assert [f.name for f in review_page.filter_choices(conn)] == ATTESO[:-1]
