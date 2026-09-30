"""La Luna: quanto e' illuminata, che fase e', quando sorge e tramonta, quanto sale stanotte, con
che curva ci arriva, e quanto potrebbe salire al massimo da quel posto.

Vincoli non ovvi:

* **La fase e' geocentrica, il sorgere e' topocentrico**, e non e' una svista. Quanto e'
  illuminata la Luna si vede uguale da tutta la Terra -- calcolarla dal sito la farebbe ballare
  di pochissimo e senza motivo, e due utenti che guardano la stessa luna leggerebbero due numeri
  diversi. L'ora in cui sorge invece dipende da dove sei, ed e' tutto il punto.
* **Un istante senza fuso si rifiuta.** `astropy` lo leggerebbe come UTC in silenzio: su un sito
  in Arizona la notte sarebbe quella sbagliata di mezza giornata, e nessuno se ne accorgerebbe.
  E' la stessa regola dell'archivio (`astrolog.clock`), applicata al cielo.
* **Chi non sorge non ha un orario.** Sopra il circolo polare la Luna puo' restare sopra o sotto
  l'orizzonte per giorni: li' si torna `None`, che a schermo diventa una frase, non un'ora finta.
* **I quattro nomi "esatti" -- nuova, primo quarto, piena, ultimo quarto -- coprono dodici
  gradi ciascuno**, sei per lato del loro centro: "luna piena" e' una parola, non un istante, e
  chiamarla piena solo all'istante esatto vorrebbe dire non dirlo mai. Gli altri quattro --
  crescente, gibbosa crescente, gibbosa calante, calante -- si prendono quel che resta, cioe'
  settantotto gradi a testa. `_BANDA_DEG` e' la **semi**-ampiezza dei primi quattro, ed e' da li'
  che si ricava quanta luce puo' avere ogni fase.

Nota sui tipi: le dichiarazioni di `astropy` danno per possibilmente assente ogni angolo di una
coordinata (`.lon`, `.alt`) e per "vettore di qualcosa" il suo valore in gradi, perche' la stessa
chiamata sa lavorare su un istante solo o su mille. Dove qui si sa che e' uno, si converte a
numero e si disarma l'avviso **sul posto e per nome** -- la stessa forma che usa
`fits/header_coords.py`, che chiede ad astropy le stesse cose.
"""

import math

from astropy.coordinates import (
    GeocentricMeanEcliptic,
    get_body,
    get_sun,
)
from astropy.time import Time

from . import (
    CEILING_STEP_DEG,
    GRID_STEP_MIN,
    MAX_DECLINATION_DEG,
    RISESET_DEG,
    TRACK_STEP_MIN,
    corpi,
)
from .grid import first_crossing, night_grid

# Le otto fasi, nell'ordine del mese lunare. E' anche l'elenco chiuso di cio' che questo modulo
# puo' rispondere: chi mostra la fase scrive i suoi testi da qui.
PHASES = (
    "new",
    "waxing_crescent",
    "first_quarter",
    "waxing_gibbous",
    "full",
    "waning_gibbous",
    "last_quarter",
    "waning_crescent",
)

# Quanto ci si puo' allontanare dal centro di nuovo/quarti/piena continuando a chiamarli cosi':
# la fetta di cerchio che ne esce e' larga **il doppio**, dodici gradi.
_BANDA_DEG = 6.0


def phase_name(scarto_deg):
    """La fase dalla differenza di longitudine eclittica fra Luna e Sole: 0 nuova, 90 primo
    quarto, 180 piena, 270 ultimo quarto.

    E' pubblica perche' e' **la regola**, e una regola si prova dove sta: provarla solo passando
    dal cielo vorrebbe dire campionare un mese vero per scoprire che una banda non scatta mai."""
    d = scarto_deg % 360
    if d < _BANDA_DEG or d > 360 - _BANDA_DEG:
        return "new"
    for centro, nome in ((90, "first_quarter"), (180, "full"), (270, "last_quarter")):
        if abs(d - centro) < _BANDA_DEG:
            return nome
    if d < 90:
        return "waxing_crescent"
    if d < 180:
        return "waxing_gibbous"
    if d < 270:
        return "waning_gibbous"
    return "waning_crescent"


def _longitudini_eclittiche(corpo, eclittica):
    """Le longitudini eclittiche di un corpo, in gradi: una per istante chiesto."""
    return corpi.convertito(corpo, eclittica).lon.deg  # pyright: ignore[reportOptionalMemberAccess]


def phase(istante):
    """Che luna fa in quel momento: `{"phase_key", "illumination_pct"}`.

    E' **geocentrica**: la stessa da ogni posto della Terra, e per questo non chiede un sito."""
    return phases([istante])[0]


def phases(istanti):
    """Che luna faceva in ognuno di quegli istanti, **in una chiamata sola**.

    Chi ha una pagina di notti chiede cento fasi insieme, e cento chiamate costerebbero cento
    volte tanto: quanto, lo misura `test_asking_the_phases_together_is_worth_it`. `phase` passa
    di qui, o le due strade direbbero due lune per la stessa notte.

    Un elenco vuoto torna vuoto senza chiedere niente: `Time([])` in astropy non e' una lista
    vuota, e' un errore, e il caso si chiude qui invece che in ogni chiamante."""
    if not istanti:
        return []
    quando = Time([corpi.quando(i) for i in istanti])
    sole = get_sun(quando)
    luna = get_body("moon", quando)
    eclittica = GeocentricMeanEcliptic(obstime=quando)
    scarti = _longitudini_eclittiche(luna, eclittica) - _longitudini_eclittiche(  # pyright: ignore[reportOperatorIssue]
        sole, eclittica
    )
    elongazioni = sole.separation(luna).deg  # pyright: ignore[reportArgumentType]
    return [
        {
            "phase_key": phase_name(float(scarto)),
            # La frazione illuminata dall'elongazione: 0 quando Luna e Sole stanno dalla stessa
            # parte, 1 quando sono opposti.
            "illumination_pct": round((1 - math.cos(math.radians(float(elongazione)))) / 2 * 100),
        }
        for scarto, elongazione in zip(scarti, elongazioni, strict=True)  # pyright: ignore[reportArgumentType]
    ]


def altitudes(istanti, latitude, longitude):
    """L'altezza della Luna sull'orizzonte, in gradi, per ognuno degli istanti dati."""
    return corpi.altezze("moon", istanti, latitude, longitude)


def lit_side(phase_key, latitude):
    """Da che parte si vede il lembo illuminato: `"left"` o `"right"`.

    Cresce a destra e cala a sinistra -- ma **dall'emisfero sud si vede al contrario**, perche' la
    Luna sta dalla parte opposta del cielo e la si guarda capovolta. Senza questa riga, meta' del
    mondo vedrebbe ogni fase specchiata, e da qui non se ne accorgerebbe nessuno."""
    cresce = phase_key in ("waxing_crescent", "first_quarter", "waxing_gibbous")
    return "right" if cresce != (latitude < 0) else "left"


def sky_ceiling(latitude):
    """Il tetto del sito: quanto in alto la Luna puo' arrivare da quella latitudine, **mai di
    piu'**, in gradi e salito al multiplo di quindici.

    E' il bordo alto del grafico della notte. Dipende **solo da dove sei**, non da stanotte, ed e'
    per questo che serve: la stessa scala vale tutte le notti di quel posto, quindi due notti si
    confrontano a occhio invece di diventare la stessa gobba.

    **Sopra i novanta non si va**, e non e' un dettaglio: alle latitudini sotto la declinazione
    massima della Luna lei passa allo zenit, e li' il tetto e' novanta e basta. La formula senza
    quel limite -- novanta meno la latitudine piu' la declinazione -- alle Canarie da' 90,5 e a
    Singapore 117, che salito alla tacca fa 120 contro i 90 che servono: **un terzo piu' alto del
    necessario**, poco piu' di un quinto di tela vuota per sempre, e un difetto che a
    quarantacinque gradi non si vede mai."""
    quanto_ci_manca = max(0.0, abs(latitude) - MAX_DECLINATION_DEG)
    return math.ceil((90 - quanto_ci_manca) / CEILING_STEP_DEG) * CEILING_STEP_DEG


def night_track(inizio, latitude, longitude, hours):
    """Tutto cio' che si sa della Luna in una notte, da **un campionamento solo**.

    Torna `{"rise", "set", "highest", "track"}`: i due attraversamenti, il punto piu' alto, e la
    curva dell'altezza. Stanno insieme perche' vengono tutti dalla stessa griglia, e chiederla due
    volte vorrebbe dire pagare due volte l'unica cosa cara che c'e' qui.

    `hours` non ha un valore di riserva: quanto dura una notte lo sa chi la conosce, e la notte
    del cambio d'ora non dura ventiquattro ore. Scritto qui un ventiquattro di comodo, il giorno
    che il chiamante lo calcola bene questo mentirebbe in silenzio.

    `rise` e `set` sono istanti con fuso, oppure `None` se quell'attraversamento non c'e' nella
    finestra. **`None` vuol dire "non in questa notte", non "mai".** Sopra il circolo polare e' il
    caso ovvio, ma capita anche a latitudini normali: la Luna torna ogni giorno circa cinquanta
    minuti piu' tardi, quindi un paio di notti al mese uno dei due attraversamenti cade fuori
    dalla finestra. Misurato a Vicenza: due notti su trenta. Chi mostra questi numeri scrive "non
    tramonta stanotte", non "non tramonta".

    **I due istanti sono indipendenti**, ognuno il primo del suo verso: per meta' mese il
    tramonto viene **prima** del sorgere (misurato: tredici notti su trenta), ed e' giusto --
    e' la Luna di ieri che cala prima che sorga quella di stanotte.

    **`highest` c'e' sempre**, anche quando non ci sono orari: una Luna che non sorge sale lo
    stesso, sotto l'orizzonte, e quanto poco sale e' cio' che chi osserva vuole sapere. E' il
    massimo **dentro la finestra**, che non e' sempre una culminazione vera: puo' cadere sul
    bordo, se la Luna sta ancora salendo quando la notte finisce."""
    istanti = night_grid(inizio, hours=hours, step_min=GRID_STEP_MIN)
    alte = altitudes(istanti, latitude, longitude)

    # Il conto sta in UTC, la risposta torna **nel fuso da cui e' stata chiesta**: e' l'ora che
    # l'utente leggera', e il passaggio la fa `astimezone`, che l'ora legale la sa.
    def nel_fuso(quando):
        return quando.astimezone(inizio.tzinfo) if quando else None

    def punto(i):
        return {"at": nel_fuso(istanti[i]), "altitude_deg": round(alte[i], 1)}

    # L'ultimo campione ci va comunque: con una finestra che non e' un multiplo del passo della
    # curva il salto lo scavalca, e il grafico chiuderebbe prima della fine della notte. Si uniscono
    # come **insieme** invece che con un `if`, cosi' quando il salto ci arriva gia' non nasce un
    # doppione -- che a schermo sarebbe un segmento lungo zero, cioe' niente da vedere e un punto
    # in piu' nel conto.
    passo = TRACK_STEP_MIN // GRID_STEP_MIN
    quali = sorted({*range(0, len(istanti), passo), len(istanti) - 1})

    return {
        "rise": nel_fuso(first_crossing(istanti, alte, RISESET_DEG, "up")),
        "set": nel_fuso(first_crossing(istanti, alte, RISESET_DEG, "down")),
        "highest": punto(alte.index(max(alte))),
        "track": [punto(i) for i in quali],
    }
