"""Il pixel di una camera ricavato dal CIELO, quando i file non lo dicono (Marco, 23/9/2026).

Per ogni posa risolta: scala misurata per focale del corredo diviso il binning; la camera prende la
mediana. Lo scrive chi cambia cio' da cui dipende -- `normalize` (le pose cambiano corredo), `solve`
(arriva la scala), la risposta "sono file di calibrazione" (il cielo si stacca) -- e la pagina lo
legge e basta. Le query sono qui e non nello store di uno stadio, perche' la chiamano in tre.

Vincolo non ovvio: quello dei file o dell'utente vince sempre in pagina, e questo non prova niente
per un'unione (`api/lookalike.py`): un riduttore che la focale dell'header non conta lo sposta.
"""

from ..units import hundredths, median, pixel_um_from_scale

# Per ogni camera, cio' che il cielo ha misurato sulle sue pose risolte, con la focale del corredo e
# il binning. Ogni camera c'e', anche senza pose risolte, perche' possa dimenticare il pixel che ne
# aveva ricavato. Le copie riscritte non votano: non sono un'altra posa.
_SKY_VOTES = """
SELECT i.id AS camera_id, w.scale_arcsec_px, r.focal_mm, f.binning
FROM instruments i
LEFT JOIN rigs r ON r.camera_id = i.id
LEFT JOIN frames f ON f.rig_id = r.id AND f.copy_of IS NULL
LEFT JOIN frame_wcs w ON w.frame_id = f.id
WHERE i.kind = 'camera'
"""


def write(conn):
    """Scrive su ogni camera la mediana dei pixel che le sue pose risolte fanno ricavare, al
    centesimo di micron -- come i costruttori lo dichiarano: le cifre dopo sarebbero rumore della
    misura -- o niente, se non ce n'e'."""
    pixels = {}
    for r in conn.execute(_SKY_VOTES):
        uno = pixel_um_from_scale(r["scale_arcsec_px"], r["focal_mm"], r["binning"])
        pixels.setdefault(r["camera_id"], []).append(uno)
    for camera_id, valori in pixels.items():
        mezzo = median(valori)
        pixel = hundredths(mezzo)
        conn.execute(
            "UPDATE instruments SET pixel_from_sky_um = ?"
            " WHERE id = ? AND pixel_from_sky_um IS NOT ?",
            (pixel, camera_id, pixel),
        )
