"""Le notti di una serie oraria di un servizio: da mezzogiorno a mezzogiorno nel fuso del sito, e
quali ore di ognuna la serie porta. Lo usano la previsione dei modelli, le fonti del cielo in
quota e lo storico.

Vincolo non ovvio: **intera o no dipende dalla fonte**. Un modello ora per ora scrive una notte
solo se ne ha tutte le ore; una fonte che non campiona ogni ora (7Timer) non l'avrebbe mai, e la
sua notte entra con le ore che ha.
"""

from datetime import UTC, date, timedelta

from ..clock import night_window
from ..ephemeris import sun


def covered(timezone, tempi, dalla, *, whole):
    """Le notti che la serie copre, da `dalla` (YYYY-MM-DD): `[(data, [(posto, istante)])]`, dove
    `posto` e' l'indice dell'ora nella serie. Con `whole` si ferma alla prima notte incompleta;
    senza, una notte entra se ha almeno un'ora, e ci sono solo le ore che la serie da'."""
    if not tempi:
        return []
    indice = {t: i for i, t in enumerate(tempi)}
    notti = []
    giorno = date.fromisoformat(dalla)
    while True:
        comincia, quante = night_window(giorno.isoformat(), timezone)
        istanti = [comincia.astimezone(UTC) + timedelta(hours=h) for h in range(round(quante))]
        coppie = [(indice[t], t) for t in istanti if t in indice]
        if whole and len(coppie) < len(istanti):
            return notti
        if not whole and istanti[0] > tempi[-1]:
            return notti
        if coppie:
            notti.append((giorno.isoformat(), coppie))
        giorno += timedelta(days=1)


def hours(serie, coppie, fuso, **per_istante):
    """Le ore di una notte come si scrivono: l'istante nel fuso del sito e i valori della serie.
    `per_istante` aggiunge un campo letto da una mappa per istante (il cielo, per la previsione)."""
    ore = []
    for i, istante in coppie:
        riga = {"at": istante.astimezone(fuso).isoformat()}
        riga.update({nome: mappa[istante] for nome, mappa in per_istante.items()})
        riga.update({nome: valori[i] for nome, valori in serie.items()})
        ore.append(riga)
    return ore


def empty(ore):
    """Nessuna ora porta un valore: una notte cosi' non si scrive."""
    return all(v is None for o in ore for k, v in o.items() if k not in ("at", "sky"))


def sky(latitude, longitude, notti):
    """In che cielo cade ogni ora delle notti date, in una chiamata sola: `{istante: fascia}`."""
    istanti = [t for _, coppie in notti for _, t in coppie]
    fasce = sun.sky_at(istanti, latitude, longitude)
    return {t: fasce[i] for i, t in enumerate(istanti)}
