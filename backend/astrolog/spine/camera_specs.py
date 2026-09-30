"""Cosa i FILE dicono della scheda di una camera: il pixel fisico e il colore, votati dalle pose.

E' il mestiere intero -- il voto e la scrittura --: `normalize` lo chiama prima del giro, per sapere
il colore con cui scegliere i filtri, e a fine giro, per scriverlo. Lo store e'
il suo, come per la meta' di `identify` che scrive l'oggetto: qui non c'e' un secondo stadio che
prende in prestito una query, c'e' una parte del lavoro di `normalize` che sta in un file suo.

Vincolo non ovvio: vince il valore piu' frequente e **a pari file nessuno** (Marco, 11/9/2026) --
fra due valori con lo stesso peso non si scegle a caso --, chi non porta un pixel fisico non vota, e
una camera rimasta senza pose che votano dimentica cio' che dicevano. Cio' che l'utente scrive sulla
scheda non passa di qui: sta fra le dichiarazioni e vince in lettura (`gear.camera_specs`).
"""

from collections import Counter

from ..units import most_frequent, physical_pixel_um
from . import declarations as decl
from . import normalize_store as store
from . import unfiltered


def ahead(conn, frame_ids, pending):
    """`{nome della camera: colore}` come lo votera' la fine della corsa, per chi la normalizza
    prima del giro: le pose in coda (`frame_ids`) votano con la camera che il giro dara' loro --
    `pending` sono le coppie `(camera, ha la matrice)` di quelle che non sono copie -- e le altre
    col corredo che hanno. Le pose senza matrice di una camera che cambia colore, e che non sono
    in coda, ci tornano: il loro filtro dipende da lui."""
    votes = {}
    for r in store.camera_votes(conn, leaving_out=frame_ids):
        votes.setdefault(r["camera"], Counter())[bool(r["color"])] += r["n"]
    for camera, bayer in pending:
        votes.setdefault(camera, Counter())[bayer] += 1
    colours = {camera: _colour(v) for camera, v in votes.items()}
    for camera_id, (nome, votato) in store.camera_colours(conn).items():
        if colours[nome] != votato and unfiltered.written_colour(conn, nome) is None:
            unfiltered.requeue(conn, camera_id)
    return colours


def from_files(conn, used=None):
    """Scrive su ogni camera il pixel fisico e il colore che i suoi file votano.

    Si rifa' alla fine di ogni giro che ha lavorato qualche posa, anche di una corsa fermata: cosi'
    il primo file che capita non decide per sempre. Un colore diverso da quello con cui le pose
    senza matrice di quella camera hanno scelto il filtro -- `used`, quello che `ahead` ha dato al
    giro, o quello scritto prima -- le rimette in coda; ma non se il colore l'ha scritto l'utente:
    li' il voto non sposta niente."""
    prima = store.camera_colours(conn)
    for camera_id, (colore, pixel) in _voted(store.camera_votes(conn)).items():
        store.set_camera_specs(conn, camera_id, colore, pixel)
        nome, votato = prima[camera_id]
        scelto = (used or {}).get(nome, votato)  # il colore con cui le pose hanno scelto
        if scelto != colore and unfiltered.written_colour(conn, nome) is None:
            unfiltered.requeue(conn, camera_id)


def _colour(votes):
    """Il colore che vince fra `{ha la matrice: file}`: a pari file nessuno."""
    return decl.CAMERA_COLOR if most_frequent(+votes) else None


def _voted(rows):
    """`{id della camera: (colore, pixel fisico)}` dalle righe di `normalize_store.camera_votes`."""
    votes = {}
    for r in rows:
        pixels, colours = votes.setdefault(r["camera_id"], (Counter(), Counter()))
        pixels[physical_pixel_um(r["pixel_size_um"], r["binning"])] += r["n"]
        colours[bool(r["color"])] += r["n"]
    out = {}
    for camera_id, (pixels, colours) in votes.items():
        pixels.pop(None, None)  # chi non dice un pixel fisico non vota
        out[camera_id] = (_colour(colours), most_frequent(pixels))
    return out
