# 0022 -- Le misure dei frame: tutte, nel database, senza voto

**Stato:** accettata, 18/10/2026 (Marco).

## Contesto

`measure` e' nel grafo degli stadi e non ha ancora un corpo. Oggi un frame porta solo HFD e
stelle, che ASTAP da' mentre risolve (`frame_metrics`, `source = 'astap'`). Marco vuole i dati
completi nel database, per confrontare notti, corredi e siti. Lo stack resta quello di ADR 0007:
`sep` con numpy e scipy.

## Decisione

**Ogni frame light risolto porta queste misure**, sul frame intero (il progetto vecchio guardava
solo i 2048 px al centro, `old/backend/astrolog/quality/analyzer.py`, e gli angoli non li vedeva).
Si scrivono una volta, quando `measure` passa, e nessuna lettura le ricalcola. Le prime sei sono
quelle del progetto vecchio; tilt, curvatura, direzione, gradiente e stelle sature sono nuove
(Marco, 18/10/2026):

- **FWHM**: in pixel nel database; a schermo in secondi d'arco (× scala misurata). Senza scala
  resta in pixel e non entra nei confronti fra corredi.
- **HFD**: da ASTAP, come oggi.
- **Stelle**: da ASTAP, come oggi.
- **Eccentricita'** = √(1 − (b/a)²), con a e b i semiassi che `sep` misura su ogni stella. Si
  tiene la mediana delle stelle del frame. 0 vuol dire stelle rotonde.
- **Fondo cielo** (ADU) e il suo rumore: il fondo di `sep`. Vale per confronti con la stessa
  camera, guadagno e posa.
- **SNR** = mediana del picco delle stelle / rumore del fondo (progetto vecchio: guadagno e
  rumore di lettura non stanno in tutti gli header).
- **Tilt**: la HFD delle stelle in ognuno dei quattro angoli e al centro, cinque numeri.
  - A schermo, la differenza fra l'angolo peggiore e il migliore, in % della HFD al centro.
  - Nessuna fonte pubblica un modo standard di misurarlo, ne' una soglia. ASTAP confronta gli
    angoli col centro (dai forum, non dal manuale). Quindi solo numeri, senza giudizio.
- **Curvatura di campo**: la HFD media dei quattro angoli contro quella del centro, in %. Stessi
  cinque numeri del tilt.
- **Direzione dell'allungamento**: l'angolo mediano dell'asse lungo delle stelle (`sep`, theta),
  girato con la rotazione della soluzione del cielo: "in AR" o "in Dec", la piu' vicina. Si
  scrive sempre; la pagina la mostra accanto all'eccentricita', senza soglia.
- **Gradiente del fondo**: il fondo di `sep` su una griglia; (massimo − minimo) / mediana, in %, e
  da che lato e' piu' chiaro.
- **Stelle sature**: quante stelle hanno il picco al valore massimo del file (`DATAMAX` se c'e',
  altrimenti il massimo del tipo di dato).

**FWHM allo zenit**, accanto alla misurata: FWHM / massa d'aria^0,6. "The seeing varies with the
airmass to the power of 3/5th" (ESO, astroclimatologia di La Silla,
eso.org/gen-fac/pubs/astclim/lasilla/seeing). La massa d'aria e' quella dell'oggetto all'ora
del frame, dalle effemeridi del sito. Senza sito o senza coordinate, niente FWHM allo zenit.
Si riporta anche la HFD (come la HFR nel progetto vecchio, `old/docs/domini/statistiche.md`);
eccentricita' e SNR no: la prima misura inseguimento e ottiche, non l'aria.

**Luminosita' del cielo (mag/arcsec²)**: Marco la vuole; se ne misura prima fattibilita' e costo
(l'ASTAP da riga di comando 2025.11 non ha l'opzione SQM). Si decide con quella misura.

**Nessun voto e nessuno scarto**: l'app misura e basta (Marco, confermato; ADR 0013). Medie e
mediane si fanno solo sui frame misurati.

**Dove si vedono**: Notti, Archivio, Statistiche. La scheda dell'oggetto no, per ora (Marco).

## Conseguenze

- `frame_metrics` guadagna i cinque HFD del tilt, direzione, gradiente, stelle sature e la massa
  d'aria; schema ricreato.
- `measure` legge i pixel una seconda volta dopo `solve`, in sola lettura: niente file accanto ai
  FITS.
- Il tempo per frame si misura su arm64 prima di chiudere lo stack (ADR 0007).
- Il fondo cielo in ADU non si confronta fra camere diverse: a schermo lo si dice.
