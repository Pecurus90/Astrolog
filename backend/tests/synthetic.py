"""L'archivio di prova sintetico: una dozzina di FITS veri con gli header dei quattro
software supportati, piu' i casi che rompono le assunzioni. E' IL dataset di collaudo del
dominio, mai la copia dell'archivio di Marco.

Vincolo non ovvio: i profili N.I.N.A. e ASIAIR ricalcano header veri (`tests/header/`); i
profili Voyager e SGP ricalcano la forma nota, perche' in casa non c'e' un loro header vero
(la coda lo dice: quando arrivera' entra prima della correzione che lo fa passare). Nessuna
chiave inventata: solo grafie diverse di chiavi che i quattro scrivono davvero.
"""

import sys

from conftest import write_fits

NINA = {
    "SWCREATE": "N.I.N.A. 3.1.2.9001 (x64)",
    "IMAGETYP": "LIGHT",
    "TELESCOP": "Askar 103Apo",
    "INSTRUME": "ATR2600M(USB2.0)",
    "FOCALLEN": 560.0,
    "XPIXSZ": 3.76,
    "XBINNING": 1,
    # come nell'header vero (`tests/header/nina.txt`): N.I.N.A. nomina ruota e focheggiatore
    "FWHEEL": "ASCOM ToupTek FilterWheel",
    "FOCNAME": "ASCOM ToupTek AAF",
}
ASIAIR = {
    "CREATOR": "ZWO ASIAIR Plus",
    "IMAGETYP": "Light",
    "TELESCOP": "EQMod Mount",  # l'ASIAIR scrive la MONTATURA, non l'ottica
    "INSTRUME": "Canon EOS 700D",
    "FOCALLEN": 560.0,
    "XPIXSZ": 4.29,
    "XBINNING": 1,  # l'header vero dell'ASIAIR porta tutti e due (tests/header/asiair.txt)
    "CCDXBIN": 1,
    "BAYERPAT": "RGGB",
    "GUIDECAM": "ZWO ASI120MM-S",  # l'ASIAIR la scrive su ogni posa (3 header veri su 3)
}
VOYAGER = {
    "SWCREATE": "Voyager",
    "IMAGETYP": "LIGHT",
    "TELESCOP": "TS 130 APO",
    "INSTRUME": "ASI2600MM Pro",
    "FOCALLEN": 910.0,
    "XPIXSZ": 3.76,
}
SGP = {
    "SWCREATE": "Sequence Generator Pro v4.4.0.1348",
    "IMAGETYP": "LIGHT",
    "TELESCOP": "RC8",
    "INSTRUME": "QHY268M",
    "FOCALLEN": 1624.0,
    "XPIXSZ": 3.76,
}

# Un light riscritto da un software di elaborazione, nella forma DIFFICILE: la chiave di chi
# ha acquisito resta (chi elabora non la cancella), e si aggiunge quella di chi ha scritto il
# file. Il software non distingue piu' i due gemelli: lo fa il marchio di riscrittura.
REWRITTEN = {"PROGRAM": "Elaborazione 1.9"}

# (file, profilo, filtro, oggetto, esposizione, data, cambi al profilo). Il commento sopra
# ogni gruppo dice quale assunzione quel gruppo rompe.
FRAMES = [
    # N.I.N.A. mono: le lettere sole della ruota, banda nota (L R) e ignota (H O)
    ("nina/L_001.fits", NINA, "L", "M 31", 120.0, "2024-10-31T21:00:00.100", {"FOCALLEN": 561.0}),
    ("nina/R_001.fits", NINA, "R", "M 31", 120.0, "2024-10-31T21:02:00.100", {}),
    ("nina/H_001.fits", NINA, "H", "NGC 6888", 300.0, "2024-07-14T22:10:00.000", {}),
    ("nina/O_001.fits", NINA, "O", "NGC 6888", 300.0, "2024-07-14T22:15:00.000", {}),
    # la stessa camera scritta senza il suffisso della porta: un pezzo solo, due grafie
    (
        "nina/L_002.fits",
        NINA,
        "L",
        "M 31",
        120.0,
        "2024-11-01T20:00:00.000",
        {"INSTRUME": "ATR2600M"},
    ),
    # la focale che oscilla di un millimetro (il primo frame del gruppo porta 561): un
    # corredo solo, e la sua focale e' la mediana 560, non la prima letta
    ("nina/L_003.fits", NINA, "L", "M 31", 120.0, "2024-11-01T20:05:00.000", {}),
    ("nina/L_004.fits", NINA, "L", "M 31", 120.0, "2024-11-01T20:10:00.000", {"FOCALLEN": 559.0}),
    # mono che dichiara "nessun filtro" e non ha matrice di Bayer: non si assume niente
    ("nina/none_001.fits", NINA, "none", "M 42", 60.0, "2024-12-20T23:00:00.000", {}),
    # ASIAIR a colori: nessun filtro nell'header e nessun oggetto
    ("asiair/Light_001.fits", ASIAIR, None, None, 180.0, "2024-03-12T21:30:00", {}),
    # un SECONDO nome di montatura, dallo stesso software: una regola scritta sul nome invece
    # che sul software passerebbe con `EQMod Mount` da solo e cadrebbe qui. I due nomi sono veri,
    # e vengono da due utenti diversi (`tests/header/asiair_am3.txt`).
    (
        "asiair/Light_002.fits",
        ASIAIR,
        None,
        None,
        180.0,
        "2024-03-12T21:33:00",
        {"TELESCOP": "ZWO AM3"},
    ),
    # camera a colori con un duo-banda avvitato davanti: il filtro c'e' e vale
    ("asiair/Light_003.fits", ASIAIR, "L-eXtreme", "IC 1396", 300.0, "2024-08-02T22:00:00", {}),
    # Voyager e SGP: altre grafie, altra attrezzatura, i sette decimali di SGP sulla data
    ("voyager/ha_001.fits", VOYAGER, "Ha 3nm", "Sh2 155", 600.0, "2024-09-19T21:00:00.500", {}),
    ("sgp/red_001.fits", SGP, "Red", "M 51", 240.0, "2024-04-05T22:12:33.1234567", {}),
    # la copia riscritta accanto al grezzo: stessa data, stessa camera, stessa esposizione
    ("nina/L_001_c.fits", NINA, "L", "M 31", 120.0, "2024-10-31T21:00:00.100", REWRITTEN),
]


def build_archive(root):
    """Scrive l'archivio sotto `root` e torna la lista dei percorsi, in ordine."""
    paths = []
    for name, profile, filt, obj, exposure, date, changes in FRAMES:
        header = {
            **profile,
            "FILTER": filt,
            "OBJECT": obj,
            "EXPTIME": exposure,
            "DATE-OBS": date,
            **changes,
        }
        header = {k: v for k, v in header.items() if v is not None}
        paths.append(write_fits(root / name, header))
    return paths


if __name__ == "__main__":  # per il collaudo dal vivo: python tests/synthetic.py <cartella>
    from pathlib import Path

    out = Path(sys.argv[1])
    sys.stdout.write(f"{len(build_archive(out))} frame sintetici in {out}\n")
