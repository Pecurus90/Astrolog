"""L'archivio grande del budget di prestazioni (passo 6.15): 10.000 frame finti ma con gli header
di N.I.N.A. e ASIAIR, tre siti, trenta oggetti, ~500 notti in tre anni. Si costruisce con gli
stadi veri dell'app, fuori dall'app; solo il cielo si scrive dall'header invece di chiederlo ad
ASTAP (10.000 lanci sarebbero dieci minuti, e la suite non lancia ASTAP).

Seminato: due costruzioni danno lo stesso archivio, quindi la stessa misura.
"""

import datetime as dt
import random

from astrolog.db.connect import connect
from astrolog.spine import stages, typeless_folders
from astrolog.spine.group import group_frames
from astrolog.spine.identify import identify_frames
from astrolog.spine.normalize import normalize_frames
from astrolog.spine.stages import StageName
from conftest import scan, sky_solved, write_fits
from synthetic import ASIAIR, NINA

FRAMES = 10_000
PER_NIGHT = 20
OBJECTS = [
    ("M 31", 10.6848, 41.2691),
    ("M 33", 23.4621, 30.6599),
    ("M 42", 83.8221, -5.3911),
    ("M 45", 56.75, 24.1167),
    ("M 51", 202.4696, 47.1952),
    ("M 81", 148.8882, 69.0653),
    ("M 101", 210.8023, 54.3489),
    ("M 27", 299.9016, 22.7211),
    ("M 57", 283.3963, 33.0292),
    ("M 13", 250.4235, 36.4613),
    ("NGC 7000", 314.75, 44.3333),
    ("IC 1396", 324.725, 57.4833),
    ("NGC 6888", 303.0417, 38.35),
    ("NGC 7023", 315.4, 68.1667),
    ("IC 434", 85.2458, -2.4583),
    ("NGC 2244", 97.9792, 4.9417),
    ("M 8", 270.925, -24.3833),
    ("M 16", 274.7, -13.8167),
    ("M 20", 270.675, -22.9717),
    ("NGC 6960", 311.4292, 30.7167),
    ("M 63", 198.9554, 42.0293),
    ("M 106", 184.7396, 47.3039),
    ("NGC 891", 35.6392, 42.3492),
    ("IC 5070", 312.75, 44.3667),
    ("NGC 281", 13.1958, 56.6167),
    ("M 97", 168.6988, 55.019),
    ("NGC 4565", 189.0866, 25.9877),
    ("M 64", 194.1825, 21.6827),
    ("NGC 7635", 350.2, 61.2),
    ("M 1", 83.6331, 22.0145),
]
SITES = [
    ("Casa", 45.0, 12.0, 120.0, "Europe/Rome", 1),
    ("Monte", 46.0, 11.0, 1500.0, "Europe/Rome", 0),
    ("Deserto", 33.0, -112.0, 400.0, "America/Phoenix", 0),
]
SETUPS = [
    {**NINA, "INSTRUME": "ATR2600M(USB2.0)", "FOCALLEN": 560.0, "XPIXSZ": 3.76},
    {**NINA, "TELESCOP": "RC8", "INSTRUME": "ASI2600MM Pro", "FOCALLEN": 1624.0, "XPIXSZ": 3.76},
    {**ASIAIR, "INSTRUME": "ZWO ASI2600MC Duo", "FOCALLEN": 1004.0, "XPIXSZ": 3.76},
]
MONO = ["L", "R", "G", "B", "Ha", "OIII", "SII"]
SHAPE = (16, 24)


def write_archive(root, frames=FRAMES):
    """I frame sul disco; torna quanti."""
    rnd = random.Random(42)
    nights = frames // PER_NIGHT
    start = dt.datetime(2023, 1, 1, 20, 0, tzinfo=dt.UTC)
    n = 0
    for day in sorted(rnd.sample(range(1100), nights)):
        name, ra, dec = rnd.choice(OBJECTS)
        site = rnd.choice(SITES)
        setup = rnd.choice(SETUPS)
        t = start + dt.timedelta(days=day, hours=rnd.uniform(0, 3) + (7 if site[2] < 0 else 0))
        for k in range(PER_NIGHT):
            band = None if setup is SETUPS[2] else MONO[k * len(MONO) // PER_NIGHT]
            exposure = 300.0 if band in ("Ha", "OIII", "SII") else 120.0
            header = {
                **setup,
                "EXPTIME": exposure,
                "DATE-OBS": t.strftime("%Y-%m-%dT%H:%M:%S"),
                "RA": ra + rnd.uniform(-0.05, 0.05),
                "DEC": dec + rnd.uniform(-0.05, 0.05),
                "OBJECT": name,
                "SITELAT": site[1],
                "SITELONG": site[2],
                "SITEELEV": site[3],
                **({"FILTER": band} if band else {}),
            }
            day_dir = t.strftime("%Y-%m-%d")
            write_fits(root / name.replace(" ", "") / day_dir / f"f{n:05d}.fits", header, SHAPE)
            t += dt.timedelta(seconds=exposure + 5)
            n += 1
    return n


def build(db_path, root):
    """Scansione, normalizzazione, cielo dall'header, identificazione, notti: l'archivio come
    la pagina lo legge dopo una scansione finita."""
    conn = connect(db_path)
    try:
        for name, lat, lon, elev, tz, home in SITES:
            conn.execute(
                "INSERT INTO sites(name, latitude, longitude, elevation_m, elevation_source,"
                " timezone, is_default, created_at) VALUES(?, ?, ?, ?, 'declared', ?, ?, 'now')",
                (name, lat, lon, elev, tz, home),
            )
        scan(conn, root)
        list(normalize_frames(conn))
        _sky_from_header(conn)
        typeless_folders.write(conn)
        list(identify_frames(conn))
        list(group_frames(conn))
    finally:
        conn.close()


def _sky_from_header(conn):
    ready = set(stages.ready(conn, StageName.SOLVE))
    rows = conn.execute("SELECT id, ra_hint_deg, dec_hint_deg FROM frames").fetchall()
    for frame_id, ra, dec in rows:
        if frame_id in ready and ra is not None:
            sky_solved(conn, frame_id, ra=ra, dec=dec)
