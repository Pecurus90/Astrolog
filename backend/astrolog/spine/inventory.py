"""L'**attrezzatura** in lettura: i pezzi che possiedi, e quanto ti sono serviti.

Le righe le scrive la spina leggendo gli header (`normalize`), le schede chi le corregge
nell'Attrezzatura (`gear`), e quanto e' servito ognuno chi lavora le pose (`gear_usage`): qui si
leggono tutte insieme, e **non si calcola niente** (Marco, 22/9/2026: una lettura non calcola mai).

Vincoli non ovvi:

* **Le ore che l'app non puo' sapere arrivano `None`, non zero**, e chi legge lo dichiara a
  schermo. Lo decide chi scrive (`gear_usage`). Un pezzo nato a meta' giro non ha ancora la sua
  riga, e arriva con `counted` falso: "non ancora contato" non e' "non si puo' sapere".
* **"Nessun filtro" non e' un filtro che possiedi**: e' la riga con cui l'app segna una posa senza
  vetro davanti, e in un elenco di cose tue sarebbe la prima voce di qualcosa che non hai.
"""

import json

from . import gear
from . import rigs as corredi

_USO = """u.frames, u.integration_s, u.untimed, u.nights, u.scale_arcsec_px, u.width_deg,
       u.height_deg, u.objects_json"""

_STRUMENTI = f"""
SELECT i.*, {_USO}
FROM instruments i
LEFT JOIN gear_usage u ON u.subject = 'instrument' AND u.subject_id = i.id
ORDER BY i.kind, i.name
"""  # noqa: S608 - frammento costante di questo file

# L'ordine e' quello che chi conta ha scritto (`position`, il piu' usato in cima); una riga non
# ancora contata va in fondo.
_CORREDI = f"""
SELECT g.id, g.focal_mm, o.name AS optics, c.name AS camera, {_USO}
FROM rigs g LEFT JOIN instruments o ON o.id = g.optics_id
            LEFT JOIN instruments c ON c.id = g.camera_id
LEFT JOIN gear_usage u ON u.subject = 'rig' AND u.subject_id = g.id
ORDER BY u.position IS NULL, u.position, g.id
"""  # noqa: S608 - frammento costante di questo file

_FILTRI = f"""
SELECT x.*, {_USO}
FROM filters x
LEFT JOIN gear_usage u ON u.subject = 'filter' AND u.subject_id = x.id
WHERE x.is_none = 0
ORDER BY u.position IS NULL, u.position, x.name
"""  # noqa: S608 - frammento costante di questo file

_BANDE = "SELECT filter_id, band, width_nm FROM filter_bands ORDER BY filter_id, band"


def instruments(conn):
    """I pezzi, per genere e per nome, con la loro scheda, quanto sono serviti e cosa ci hai
    ripreso."""
    # Colore e pixel di una camera li scrive l'utente **fra le dichiarazioni**, non nella colonna,
    # che e' dei file: letta la sola colonna, la pagina mostrerebbe cio' che i file dicono anche
    # dopo che l'utente ha detto un'altra cosa.
    dichiarato = gear.camera_specs(conn)
    return [
        {**_riga(r), **dichiarato.get(r["id"], {}), "no_hours": _senza_ore(r)}
        for r in conn.execute(_STRUMENTI).fetchall()
    ]


def _senza_ore(r):
    """Perche' un pezzo contato non ha ore: una montatura senza pose non e' "i file tacciono", e'
    che nessun corredo la porta ancora -- anche dove altre montature ce l'hanno."""
    if r["objects_json"] is None:
        return None  # non ancora contato: lo dice `counted`
    if r["kind"] == "mount" and not r["frames"]:
        return "no_rig"
    return "files_silent" if r["frames"] is None else None


def rigs(conn):
    """I corredi: com'e' fatto ognuno, quanto e' servito, cosa ci hai ripreso e quanto cielo
    inquadra davvero."""
    nomi, montature = corredi.rig_names(conn), corredi.rig_mounts(conn)
    return [
        {
            **_riga(r),
            "name": nomi.get(corredi.decl_key(r)),
            "mount_id": montature.get(corredi.decl_key(r)),
        }
        for r in conn.execute(_CORREDI).fetchall()
    ]


def filters(conn):
    """I filtri posseduti, con la banda che lasciano passare, quanto sono serviti e cosa ci hai
    ripreso."""
    bande = {}
    for r in conn.execute(_BANDE):
        bande.setdefault(r["filter_id"], []).append({"band": r["band"], "width_nm": r["width_nm"]})
    return [{**_riga(r), "bands": bande.get(r["id"], [])} for r in conn.execute(_FILTRI).fetchall()]


def _riga(r):
    """La riga letta, con gli oggetti ripresi e se chi conta l'ha gia' contata."""
    riga = {k: r[k] for k in r.keys() if k != "objects_json"}  # noqa: SIM118 - Row itera i valori
    riga["counted"] = r["objects_json"] is not None
    riga["objects"] = json.loads(r["objects_json"] or "[]")
    return riga
