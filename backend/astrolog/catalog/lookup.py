"""Le domande che si fanno al catalogo: **che oggetto e' questa sigla**, **cosa c'e' in questo
pezzo di cielo**, e **questa voce esiste** (con cosa dice).

Le prime due sono quelle su cui `identify` e' costruito. La terza e' nata con la parola
dell'utente: quando dichiara che una posa e' un'altra voce, quella voce va presa per nome
proprio -- non e' fra i candidati del cielo, che dicevano un'altra cosa.

Vincolo non ovvio: la ricerca per cono passa dal **versore**. Un cerchio sul cielo diventa un
riquadro su `x, y, z` -- che l'indice sa fare -- e poi si misura davvero col prodotto scalare:
il riquadro sgrossa, il coseno decide. Filtrare sulle coordinate sferiche costringerebbe a
ricordarsi ogni volta che l'ascensione retta a 0 gradi torna a 360, e due oggetti vicini
possono avere coordinate 0,5 e 359,5.
"""

import math

from .. import units
from . import designation
from .load import unit_vector

_FIELDS = (
    "slug, name, common_name, ra_deg, dec_deg, constellation, type_code, kinds_json,"
    " size_major_arcmin, size_minor_arcmin, position_angle_deg, magnitude, magnitude_band,"
    " surface_brightness, distance_ly, opacity"
)


def by_designation(conn, raw):
    """La voce che porta quella sigla, o `None`. Un nome che il catalogo non conosce e' la
    norma, non un guasto: si fotografano anche cose che non hanno una voce.

    Porta anche `is_primary`, cioe' se la sigla cercata e' quella con cui la voce si chiama o
    un suo altro nome: `NGC 224` e `M 31` sono lo stesso oggetto, ma chi identifica dal solo
    nome dice `historic_name` invece di `exact_name`, e senza questo campo non potrebbe."""
    key = designation.key(raw)
    if key is None:
        return None
    fields = ", ".join("e." + f.strip() for f in _FIELDS.split(","))
    row = conn.execute(
        f"SELECT {fields}, n.is_primary FROM catalog_entries e"  # noqa: S608 - colonne costanti di questo file
        " JOIN catalog_names n ON n.slug = e.slug WHERE n.key = ?",
        (key,),
    ).fetchone()
    return dict(row) if row else None


def by_slug(conn, slug):
    """La voce con quello slug, o `None`. Lo slug e' la chiave del catalogo: chi arriva qui lo
    ha gia' in mano (una dichiarazione dell'utente, un oggetto dell'archivio) e vuole i campi."""
    fields = ", ".join(f.strip() for f in _FIELDS.split(","))
    row = conn.execute(
        f"SELECT {fields} FROM catalog_entries WHERE slug = ?",  # noqa: S608 - colonne costanti di questo file
        (slug,),
    ).fetchone()
    return dict(row) if row else None


def in_cone(conn, ra_deg, dec_deg, radius_deg):
    """Le voci entro `radius_deg` dal punto dato, dalla piu' vicina, ognuna col suo
    `sep_deg`: chi sceglie il soggetto ha bisogno dello scarto, non solo dell'elenco."""
    radius_deg = min(max(radius_deg, 0.0), 180.0)  # oltre mezzo cielo il cono e' tutto il cielo
    cx, cy, cz = unit_vector(ra_deg, dec_deg)
    # La corda che sottende l'angolo: e' il lato del riquadro che sgrossa la ricerca.
    chord = 2 * math.sin(math.radians(radius_deg) / 2)
    min_cos = math.cos(math.radians(radius_deg))

    out = []
    for row in conn.execute(
        f"SELECT {_FIELDS}, x, y, z FROM catalog_entries"  # noqa: S608 - colonne costanti di questo file
        " WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ? AND z BETWEEN ? AND ?",
        (cx - chord, cx + chord, cy - chord, cy + chord, cz - chord, cz + chord),
    ):
        entry = dict(row)
        cos_sep = entry.pop("x") * cx + entry.pop("y") * cy + entry.pop("z") * cz
        if cos_sep < min_cos:
            continue  # dentro il riquadro ma fuori dal cerchio: gli angoli del quadrato
        entry["sep_deg"] = units.separation_deg_from_cosine(cos_sep)
        out.append(entry)
    return sorted(out, key=lambda e: e["sep_deg"])
