"""Quale, fra gli oggetti nel campo, e' il soggetto.

Portato da `old/backend/astrolog/catalogs/propose.py` coi suoi pesi, che sono tarati su casi
veri e non scelti a naso. Puro: niente database.

**Il fatto da cui parte tutto** (`old/backend/astrolog/catalogs/propose.py:8-12`, misurato su
bersagli reali): per
cinque bersagli su sei **il candidato piu' vicino al centro e' quello sbagliato** -- dentro
M 31 il piu' vicino e' la nana M 32, su M 101 e' la sua regione HII NGC 5447, sulla Rosetta e'
Ced 76. Il soggetto e' l'oggetto grande e luminoso che **contiene** il puntamento. Per questo si
pesa invece di prendere il primo per scarto crescente.

Vincoli non ovvi, ognuno pagato con una misura:

* **Il metro del punteggio e' il raggio dell'oggetto**, non la tolleranza di accettazione.
  Quando era quella, valeva esattamente un grado per il 95% del catalogo, e il contenimento
  usciva identico per una galassia di 2 primi e una nebulosa di 50: la "separazione scalata
  sulla dimensione" non avveniva, e codice e intento divergevano.
* **La magnitudine si moltiplica per la centratura, non si somma.** Un premio di luminosita'
  indipendente dalla geometria fa vincere l'oggetto brillante che nella foto quasi non c'e'.
* **La centratura entra come addendo solo col campo noto.** Senza campo vale 0,5 per tutti, e
  la stessa costante per tutti non cambia l'ordine ma **comprime i rapporti** -- e la guardia
  dell'ambiguita' ragiona su un rapporto.
* **Il pavimento e' l'errore del solver, non quello del GoTo.** `old/` aveva due gradini
  perche' il 94,5% delle sue pose non era risolto; qui `identify` gira dopo il solver.
"""

import math

from ..catalog import designation
from ..units import radius_deg
from .identify_geometry import reach_deg

# I pesi, fonte unica (`old/backend/astrolog/catalogs/propose.py:33-44`). La magnitudine pesa
# un filo piu' del contenimento: e' il segnale che ribalta il clutter debole -- le nebulosette senza
# magnitudine, piu' vicine ma minori.
W_CONTAINMENT = 1.0
W_MAGNITUDE = 1.4
W_SIZE = 0.6
W_CATALOG = 1.0
W_CENTERING = 1.2

# Il pavimento del metro: sotto l'errore del solver non si pretende di distinguere due
# candidati. E' il gradino "risolto" di `old/` (`SLOP_SOLVED_DEG`), non quello GoTo: qui una
# posa o ha il cielo misurato o non ce l'ha affatto.
SEP_FLOOR_DEG = 0.05
# Oltre, il metro non cresce piu': un oggetto enorme non deve "contenere" mezza costellazione.
SCALE_CAP_DEG = 3.0

# I cataloghi curati e famosi battono gli oscuri. Normalizzata 0..1
# (`old/backend/astrolog/catalogs/propose.py:52-57`).
CATALOG_PRIORITY = {
    "M": 1.0, "C": 0.9, "NGC": 0.7, "IC": 0.55,
    "Sh2": 0.4, "LBN": 0.3, "LDN": 0.3, "vdB": 0.3, "Ced": 0.3,
    "B": 0.3, "Abell": 0.3, "RCW": 0.3,
}  # fmt: skip
CATALOG_PRIORITY_DEFAULT = 0.2

# Ambiguita': il secondo ha un punteggio competitivo **ed** e' un oggetto davvero distinto dal
# primo, non qualcosa che gli sta dentro.
AMBIGUOUS_SCORE_RATIO = 0.6
# Il pavimento quando nessuno dei due ha una dimensione: e' la soglia fissa che aveva `old/`
# (`old/backend/astrolog/catalogs/propose.py:71-72`), tarata perche' M 81 e M 82 (0,61 gradi)
# contendano e la nebulosa Rosetta col suo ammasso (0,28) no.
AMBIGUOUS_SEPARATION_DEG = 0.4


def _magnitude_term(magnitude):
    """0..1: piu' luminoso, piu' alto. Assente vale 0 -- il clutter senza magnitudine non
    prende premio, ed e' proprio quello che affolla i campi."""
    if magnitude is None:
        return 0.0
    return (12.0 - min(12.0, max(3.0, magnitude))) / 9.0


def _size_term(size_major_arcmin):
    """0..1 sul logaritmo della dimensione: un primo vale 0, 316 primi valgono 1."""
    if size_major_arcmin is None:
        return 0.0
    return min(1.0, math.log10(max(size_major_arcmin, 1.0)) / 2.5)


def catalog_priority(name):
    """La priorita' del catalogo da cui viene la sigla principale della voce."""
    parsed = designation.parse(name)
    return (
        CATALOG_PRIORITY.get(parsed[0], CATALOG_PRIORITY_DEFAULT)
        if parsed
        else (CATALOG_PRIORITY_DEFAULT)
    )


def ranking_scale_deg(size_major_arcmin):
    """Il metro con cui si normalizza lo scarto: il **raggio dell'oggetto**, fra il pavimento
    e il tetto. Non e' una tolleranza di accettazione -- quella direbbe "dentro o fuori", qui
    serve l'opposto: un metro che **distingua** i candidati fra loro."""
    return min(SCALE_CAP_DEG, max(radius_deg(size_major_arcmin), SEP_FLOOR_DEG))


def centering_term(separation_deg, fov_radius_deg, size_major_arcmin=None):
    """Quanto il candidato e' **presente** nella foto: 1 col centro sul centro, 0 quando
    oggetto e campo non si toccano piu'. Campo ignoto vale 0,5, cioe' neutro.

    Il metro e' `identify_geometry.reach_deg`, quello di `overlaps_frame` (che dove il raggio
    non si sa si astiene apposta). Sul solo campo, un oggetto piu'
    grande dell'inquadratura -- cioe' **ogni pannello di mosaico** -- prendeva 0 e con esso
    perdeva tutto il premio di luminosita'."""
    if fov_radius_deg is None or fov_radius_deg <= 0:
        return 0.5
    return max(0.0, 1.0 - separation_deg / reach_deg(fov_radius_deg, size_major_arcmin))


def score_candidate(entry, fov_radius_deg=None):
    """Il punteggio di una voce di catalogo nel campo. Alto = piu' probabile soggetto.

    `entry` e' cio' che torna `catalog.lookup.in_cone`: porta `sep_deg`, `size_major_arcmin`,
    `magnitude` e `name`."""
    sep = entry["sep_deg"]
    size = entry.get("size_major_arcmin")
    sep_norm = min(1.0, sep / ranking_scale_deg(size))
    centering = centering_term(sep, fov_radius_deg, size)
    known_field = fov_radius_deg is not None and fov_radius_deg > 0
    return (
        W_CONTAINMENT * (1.0 - sep_norm)
        + (W_CENTERING * centering if known_field else 0.0)
        + W_MAGNITUDE * _magnitude_term(entry.get("magnitude")) * centering
        + W_SIZE * _size_term(size)
        + W_CATALOG * catalog_priority(entry.get("name"))
    )


def _is_inside(first, second, separation_deg, fov_radius_deg=None):
    """Uno dei due sta **dentro** l'altro? Allora non contendono: sono lo stesso soggetto.

    `old/` approssimava questa domanda con una soglia fissa di 0,4 gradi. Sui valori veri del
    nostro catalogo quella soglia sbaglia: M 32 dista **0,4039** dal centro di M 31, cioe'
    quattro millesimi di grado oltre la riga, e finirebbe a conferma ogni volta -- mentre e'
    una nana **dentro** M 31, che nelle sue pose c'e' sempre. Il raggio risponde alla stessa
    domanda meglio, e viene dal catalogo invece che da una taratura: M 81 e M 82 (0,61 contro
    un raggio di 0,18) restano due bersagli che contendono, la nebulosa Rosetta e il suo
    ammasso (0,28 contro 0,67) restano lo stesso soggetto.

    E si guarda il raggio **maggiore dei due**, perche' la domanda non ha un verso: su pose
    vere di NGC 7023 il soggetto sta dentro LDN 1174, la nube oscura che l'avvolge, e col solo
    raggio del primo (0,0833 contro 0,1001) andavano a conferma tutte e quaranta.

    **Ma il contenimento vale solo fra vicini rispetto all'inquadratura**, e questo e' il verso
    in cui si sceglie di sbagliare. Un oggetto grande contiene tutto cio' che gli cade dentro,
    e "gli appartiene" e' un'altra domanda -- la relazione pezzo/adiacenza, che il criterio
    geometrico non distingue e che sta in coda. Sul solo contenimento, 44 coppie del catalogo
    si dichiaravano lo stesso soggetto a piu' di un grado di distanza (NGC 1977 contro M 42,
    M 107 dentro una nube di otto gradi): meglio chiedere una volta di piu' che agganciare in
    silenzio il bersaglio sbagliato. Il metro e' il raggio della foto, non una taratura, e sulle
    543 coppie di bersagli veri si chiede 70 volte -- 88 col solo raggio del primo, 29 senza
    questa riga."""
    sizes = [x.get("size_major_arcmin") for x in (first, second)]
    largest = max((s for s in sizes if s and s > 0), default=None)
    # senza campo non si pretende, come `overlaps_frame`: non si scarta per un dato che manca
    # a noi. Ma dove il campo c'e' vale anche sul ramo della soglia fissa, o le 6.254 voci
    # senza dimensione avrebbero una scorciatoia per saltarlo -- e sono il clutter dei campi
    # stretti, cioe' proprio dove il vincolo serve.
    near_in_frame = fov_radius_deg is None or separation_deg <= fov_radius_deg
    if not largest:
        return separation_deg < AMBIGUOUS_SEPARATION_DEG and near_in_frame
    return separation_deg <= radius_deg(largest) and near_in_frame


def is_ambiguous(first, second, *, separation_deg, fov_radius_deg=None):
    """Il secondo contende davvero? Serve **tutte e due** le condizioni: un punteggio
    competitivo, e un oggetto distinto dal primo. Solo il punteggio manderebbe a conferma la
    nebulosa e il suo ammasso, che sono lo stesso soggetto."""
    if second is None or separation_deg is None:
        return False
    if _is_inside(first, second, separation_deg, fov_radius_deg):
        return False
    # il punteggio non scende mai sotto la priorita' del catalogo piu' oscuro (0,2): non c'e'
    # nessuna divisione per zero da guardare
    best = score_candidate(first, fov_radius_deg)
    return score_candidate(second, fov_radius_deg) >= AMBIGUOUS_SCORE_RATIO * best
