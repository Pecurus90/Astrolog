"""Il Sole: quanto e' alto lungo la notte, e **le fasce del cielo** che ne escono.

Le fasce arrivano a chi disegna **gia' fatte**, e il perche' sta nel contratto
(`docs/domini/effemeridi.md`, voce *"Le fasce arrivano gia' divise"*).

Vincoli non ovvi:

* **Le fasce si leggono dalle altezze, non dagli attraversamenti.** Cosi' i casi estremi escono
  da soli, e ognuno per quello che e': dove il Sole non tramonta la finestra e' tutta giorno, una
  fascia sola; dove non sorge, invece, i crepuscoli ci sono quasi sempre lo stesso -- alle
  Svalbard a gennaio il cielo risale fino al nautico a mezzogiorno -- e una fascia sola la si vede
  solo dove il Sole resta sotto i diciotto gradi per tutta la finestra.
* **Un confine si interpola** fra i due campioni che lo racchiudono, come in `grid`: il passo
  decide quanto e' fitta la ricerca, non di quanto si sbaglia.

Le quattro soglie e la loro fonte stanno in `ephemeris/__init__.py`.
"""

from . import ASTRO_DEG, CIVIL_DEG, GRID_STEP_MIN, NAUTICAL_DEG, RISESET_DEG, corpi
from .grid import night_grid

# Le cinque fasce, **dalla piu' chiara alla piu' scura**, ognuna col pavimento che la tiene su:
# sopra `RISESET_DEG` e' giorno, sotto `ASTRO_DEG` e' buio. L'ordine e' quello che serve a
# trovare in che fascia cade un'altezza, e la sequenza dei nomi e' il vocabolario che esce di qui.
FASCE = (
    ("day", RISESET_DEG),
    ("civil", CIVIL_DEG),
    ("nautical", NAUTICAL_DEG),
    ("astronomical", ASTRO_DEG),
)
BUIO = "dark"


def altitudes(istanti, latitude, longitude):
    """L'altezza del Sole sull'orizzonte, in gradi, per ognuno degli istanti dati."""
    return corpi.altezze("sun", istanti, latitude, longitude)


def night_bands(inizio, latitude, longitude, hours):
    """Le fasce del cielo di una notte intera, **nel fuso da cui e' stata chiesta**.

    E' il gemello di `moon.night_track`, e fa lo stesso giro: la griglia, le altezze, la
    derivazione, e gli istanti riportati nell'ora che l'utente leggera'."""
    istanti = night_grid(inizio, hours=hours, step_min=GRID_STEP_MIN)
    fasce = sky_bands(istanti, altitudes(istanti, latitude, longitude))
    return [
        {
            **f,
            "starts_at": f["starts_at"].astimezone(inizio.tzinfo),
            "ends_at": f["ends_at"].astimezone(inizio.tzinfo),
        }
        for f in fasce
    ]


def sky_at(istanti, latitude, longitude):
    """In che fascia del cielo cade ognuno degli istanti dati. Chi vuole sapere solo questo -- il
    cielo di un'ora -- non paga la notte campionata minuto per minuto di `night_bands`."""
    return [_fascia(a) for a in altitudes(istanti, latitude, longitude)]


def sky_bands(istanti, altezze):
    """Le fasce del cielo lungo la finestra: `[{"starts_at", "ends_at", "kind"}]`, attaccate e
    senza buchi.

    La prima comincia col primo istante e l'ultima finisce con l'ultimo, sempre: una notte che
    comincia gia' al buio non ha un inizio da inventare, e un buio che non finisce si misura fino
    al bordo -- contarlo per zero direbbe "nessun buio" su una notte buia ventitre ore, ed e' il
    difetto che nel progetto di prima e' uscito per ultimo."""
    if len(istanti) < 2:
        return []
    fasce = []
    inizio, quale = istanti[0], _fascia(altezze[0])
    for i in range(len(istanti) - 1):
        for confine, dopo in _confini(istanti[i], istanti[i + 1], altezze[i], altezze[i + 1]):
            fasce.append({"starts_at": inizio, "ends_at": confine, "kind": quale})
            inizio, quale = confine, dopo
    fasce.append({"starts_at": inizio, "ends_at": istanti[-1], "kind": quale})
    return fasce


def _fascia(altezza):
    """In che fascia cade un'altezza."""
    for nome, pavimento in FASCE:
        if altezza > pavimento:
            return nome
    return BUIO


def _confini(t0, t1, a0, a1):
    """I confini fra due campioni: quali soglie attraversano, e in che istante.

    Sono **piu' d'uno** quando un passo scavalca una fascia intera: non capita con la griglia
    vera, dove il Sole scende di meno di un grado ogni tre minuti, ma una regola che vale solo a
    passo fitto non e' una regola. Escono in ordine di attraversamento, che scendendo e' l'ordine
    delle soglie e salendo e' il suo rovescio."""
    scendendo = a1 < a0
    soglie = [s for _, s in FASCE if min(a0, a1) <= s < max(a0, a1)]
    for soglia in sorted(soglie, reverse=scendendo):
        # la frazione di intervallo a cui l'altezza tocca la soglia; il denominatore non e' zero
        # perche' la soglia sta **dentro** i due estremi
        quota = (soglia - a0) / (a1 - a0)
        yield t0 + (t1 - t0) * quota, _fascia(soglia if scendendo else soglia + _UN_FILO)


# Una soglia e' il **pavimento** della fascia sopra: chi ci sta esattamente appartiene a quella
# sotto (`_fascia` confronta con `>`). Salendo, il confine porta nella fascia di sopra, e per
# chiederlo a `_fascia` bisogna scavalcare la soglia di un filo invece di riscrivere la scala.
_UN_FILO = 1e-9
