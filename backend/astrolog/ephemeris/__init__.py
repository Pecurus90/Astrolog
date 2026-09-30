"""Le effemeridi: cosa fa il cielo da un posto e in un momento. **Offline, sempre.**

Portato da `old/backend/astrolog/ephemeris/`, un pezzo per volta: qui ci sono la Luna e il **Sole**
-- del Sole quello che serve a dire dov'e' il buio (il contratto e' `docs/domini/effemeridi.md`).
I pianeti e la visibilita' di un oggetto restano nella cava finche' non serve una schermata.

**Importare questo package disinnesca la rete di astropy**, ed e' l'unica ragione per cui esiste
un `__init__` con del codice dentro:

* `iers.conf.auto_download = False` e `iers.conf.auto_max_age = None` **lavorano insieme**, e
  l'ordine dell'una senza l'altra e' peggio di niente. Misurato simulando la macchina senza rete,
  su una data del 2027: col solo `auto_download = False` astropy **solleva**, e il suo stesso
  messaggio indica `auto_max_age = None` come rimedio; con tutte e due passa. La prima smette di
  uscire di casa, la seconda accetta i dati **impacchettati** con astropy anche quando sono
  vecchi -- cosa che serve proprio perche' si e' smesso di scaricarne di nuovi. La precisione
  persa e' molto sotto il secondo: per sorgere, tramontare e fase non si vede. L'app gira su un
  NAS in una casa senza rete e su un portatile in montagna: una effemeride che scarica non e'
  lenta, e' rotta.
* `solar_system_ephemeris.set("builtin")` -- il modello incorporato, nessun file da scaricare.
  Sole ad arcosecondi, Luna a decine: per dire quanta luce fa stanotte e' avanzato.

E' un effetto all'import, ed e' deliberato: l'assetto vale per tutto cio' che ci sta dentro, e
lasciarlo a chi chiama vorrebbe dire dimenticarlo nel punto dove nessuno guarda. E' idempotente.
"""

from astropy.coordinates import solar_system_ephemeris
from astropy.utils import iers

# Niente rete: ne' adesso ne' quando qualcuno chiedera' una data del 2030.
iers.conf.auto_download = False
iers.conf.auto_max_age = None
solar_system_ephemeris.set("builtin")

# L'altezza a cui un corpo si dice sorto o tramontato: **0,833 gradi sotto l'orizzonte**, cioe'
# 50 minuti d'arco. E' la somma di due cose -- la rifrazione dell'aria vicino all'orizzonte (34')
# e il raggio apparente del disco (16') -- ed e' la convenzione degli almanacchi, dal Nautical
# Almanac in giu', per il Sole come per la Luna. Due numeri diversi qui vorrebbero dire due orari
# che nessuno puo' confrontare con un'altra fonte.
# **Vale anche per la Luna, ed e' misurato**: l'USNO per lei usa una formula sua, con dentro la
# parallasse, ma le nostre altezze sono topocentriche e il numero torna. Il confronto sta in
# `test_rise_and_set_match_the_usno_tables_within_a_minute`, con dentro le date, le coordinate e i
# valori delle tavole: e' li' che si rifa', non qui.
RISESET_DEG = -0.833

# Le tre soglie del crepuscolo: l'altezza **geometrica del centro del Sole** sotto l'orizzonte a
# cui finisce ognuno. Sono le definizioni dell'USNO (<https://aa.usno.navy.mil/faq/RST_defs>),
# verificate alla fonte il 20/9/2026 e non ricopiate dal progetto di prima, dove le stesse soglie
# non citavano niente. In parole: dopo il civile serve la luce artificiale per stare fuori; dopo il
# nautico l'orizzonte in mare non si distingue piu'; dopo l'astronomico la luce del Sole diffusa e'
# meno di quella delle stelle -- ed e' quello il buio di chi fotografa il cielo.
CIVIL_DEG = -6.0
NAUTICAL_DEG = -12.0
ASTRO_DEG = -18.0

# Il passo con cui si campiona il cielo per cercare gli attraversamenti. Tre minuti: l'istante poi
# si **interpola**, quindi il passo non e' l'errore -- decide solo quanto fitta e' la ricerca.
GRID_STEP_MIN = 3

# Il passo della curva che si manda a chi la disegna: molto piu' largo di quello del conto, perche'
# sono due mestieri diversi. Quindici minuti fanno una novantina di punti per notte, che a schermo
# e' gia' una curva liscia (misurata: 5,5 KB di risposta): il passo del conto ne farebbe 481, cinque
# volte tanti, per una differenza che nessuno vede.
# **Deve restare un multiplo di `GRID_STEP_MIN`**, o "ogni quindici
# minuti" diventa un arrotondamento e i punti si spostano.
TRACK_STEP_MIN = 15

# Quanto lontano dall'equatore celeste arriva la Luna. E' un **limite superiore**, e deve restare
# tale: serve a dire quanto in alto la Luna puo' salire da un posto, e un numero anche solo un po'
# troppo piccolo farebbe un tetto che taglia la curva invece di contenerla.
#
# Sommare le due inclinazioni medie -- obliquita' dell'eclittica (23,44) piu' orbita lunare (5,14)
# -- da' 28,58, ed e' il conto che gira: **non basta**. L'inclinazione dell'orbita oscilla, e al
# lunistizio maggiore la declinazione va oltre: misurata qui, ora per ora dal 2024 al 2026, arriva
# a **28,72**. Con 28,58 il tetto restava sopra la Luna solo grazie alla parallasse, cioe' per
# fortuna. Si arrotonda per eccesso al decimo, perche' l'errore da una parte taglia il disegno e
# dall'altra costa qualche grado di tela.
MAX_DECLINATION_DEG = 28.8

# A quanti gradi per volta sale il bordo alto del grafico della notte. Viene dal disegno: una
# scala che finisse sul numero esatto cambierebbe di un grado fra due siti vicini, e le tacche non
# cadrebbero mai tonde.
CEILING_STEP_DEG = 15
