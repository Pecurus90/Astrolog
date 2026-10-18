# 0022 -- Le misure dei frame: tutte, attestate, nel database, senza voto

**Stato:** accettata, 18/10/2026 (Marco).

## Contesto

`measure` e' nel grafo degli stadi e non ha ancora un corpo. Oggi un frame porta solo HFD e
stelle, che ASTAP da' mentre risolve (`frame_metrics`, `source = 'astap'`). Marco vuole i dati
completi nel database, per confrontare notti, corredi e siti, misurati "come PixInsight o <!-- software-ok -->
Siril": veloci, ma corretti. Lo stack resta quello di ADR 0007: `sep` con numpy e scipy. <!-- software-ok -->

Ricerca del 18/10/2026 sul codice di Siril (`f518f2cf`), N.I.N.A. (`4742afae`), ASTAP (mirror <!-- software-ok -->
`CanardConfit/ASTAP@c2b4aa6a`) e sulla documentazione di PixInsight (ImageWeighting, <!-- software-ok -->
pixinsight.com/doc/docs/ImageWeighting). Il codice di PCL (PixInsight) non si porta: la sua <!-- software-ok -->
licenza lo vieta per la generazione automatica di codice. AstroLog e' GPL-3.

## Decisione

### Dove si misura

Cinque zone da 1024 px (centro e quattro angoli), piu' il fondo sul frame intero ridotto 4×4. Le
zone si leggono dal file senza caricarlo tutto (FITS non compresso). Il progetto vecchio guardava
solo i 2048 px al centro (`old/backend/astrolog/quality/analyzer.py`) e gli angoli non li vedeva.
Misura sul portatile, frame sintetico 6248×4176 px: frame intero 1,01 s, cinque zone 0,08 s
senza fit; col fit e la lettura del file 0,4-0,9 s (confronto sotto). Si rimisura su arm64
(ADR 0007).

### Il metodo

1. **Fondo e rumore**: `sep.Background` per zona. Rumore = 1,4826 × MAD dei pixel di fondo, la
   regola di ASTAP, N.I.N.A. e del rumore N* di PixInsight (1,4826 = 1/Φ⁻¹(3/4), Rousseeuw e <!-- software-ok -->
   Croux, JASA 88:1273, 1993). Il rumore MRS di PixInsight (Starck e Murtagh 1998) resta fuori. <!-- software-ok -->
2. **Stelle**: `sep.extract` a 5σ, soglia predefinita di Siril. Si tengono solo: non fuse e non <!-- software-ok -->
   tagliate dal bordo (`flag` 0), picco sotto il 90 % della saturazione, lontane dal bordo piu'
   di 3 HFD, senza vicine entro 3 FWHM, b/a sopra 0,5 (rotondita' minima predefinita di Siril). <!-- software-ok -->
3. **HFD**: diametro che contiene meta' del flusso, `sep.flux_radius` con frazione 0,5, su tutte
   le stelle tenute. **Sostituisce la HFD di ASTAP**, che e' il raggio medio Σf·r/Σf e per una
   stella gaussiana viene il 6,4 % piu' alta (conto: σ√(π/2) contro σ√(2 ln 2)).
4. **FWHM, eccentricita', angolo**: fit di una PSF di Moffat ellittica (Levenberg-Marquardt,
   `scipy.optimize.least_squares`) sulle 10-15 stelle migliori di ogni zona, come PixInsight e <!-- software-ok -->
   Siril. FWHM = 2α√(2^(1/β) − 1), con α = √(αx·αy); eccentricita' = √(1 − (b/a)²), la <!-- software-ok -->
   definizione di PixInsight. Prova su stelle di Moffat sintetiche di FWHM nota: errore 0 %; i <!-- software-ok -->
   momenti di `sep` sbagliano dal +14 al +44 % e servono solo a contare e a orientare. Se il fit
   non converge: momenti di `sep`, e la misura lo dice.
5. **SNR**: per stella SNR = F / √(F/g + n·σ²), la formula CCD (Merline e Howell) che usano
   Siril e ASTAP; g dall'header (`EGAIN`), senza g in ADU. Per il frame, la mediana. <!-- software-ok -->
6. **Aggregazione**: mediana per zona e per frame; dispersione 1,4826 × MAD.
7. **Camere a colori**: si misura sul superpixel 2×2 del grezzo (un pixel per quadrato Bayer), e
   le misure tornano in pixel del sensore. Sul grezzo il motivo Bayer passa per rumore e scarta
   quasi tutte le stelle (prova sotto).
8. **Pixel caldi**: i light non sono calibrati, e in banda stretta la maggior parte dei
   rilevamenti erano pixel caldi (HFD 0,9 px, prova su cinque frame Hα/OIII di Marco). Le stelle
   si cercano su una copia filtrata con mediana 3×3; HFD e fit si misurano sul frame grezzo.
9. **Poche stelle**: sotto un minimo di stelle tenute per zona si ripiega sul frame intero; sotto
   il minimo anche li', la misura tace e dice "troppo poche stelle". Il minimo si fissa alla
   costruzione con una prova, come le altre costanti.

**Confronto misurato** (18/10/2026, 12 frame sintetici 6248×4176 a verita' nota: Moffat β 2,5 e
4,5, gaussiane, FWHM 2,5/4/6 px, eccentricita' 0,5, tilt; piu' due frame veri di Marco, una L
mono e una OSC Canon). Errore medio in valore assoluto:

| metodo | FWHM | HFD | eccentricita' | tempo a frame |
|---|---|---|---|---|
| progetto vecchio (photutils, centro 2048 px) | 9,4 % (max 25) | 6,5 % (max 17) | 0,23 | 1,13 s |
| questo metodo (5 zone, fit di Moffat) | 1,7 % (max 4,7) | 2,8 % (max 7) | 0,11 | 0,56 s (0,38-0,91) |
| ASTAP `-analyse` | -- | 11,5 % (max 19) | -- | 0,3 s |

Con 40 stelle (nuvole) il vecchio dava una HFD sbagliata del 516 % invece di tacere. Su stelle
rotonde l'eccentricita' non va a zero (questo metodo 0,10-0,17, il vecchio 0,25-0,31): vicino a 0
amplifica il rumore (b/a 0,99 da' gia' 0,14). A schermo si mostra il numero; una soglia di
"rotonde" senza fonte non si mette; quella che si mette e' sotto. Il tempo, con la lettura del file, e' 0,4-0,9 s e cresce
con la FWHM.

HFD e FWHM si salvano tutte e due: il loro rapporto dipende dalla forma della stella (β) e
nessuna delle due si ricava dall'altra.

### Verifica contro PixInsight e contro stelle iniettate (18/10/2026) <!-- software-ok -->

SubframeSelector di PixInsight 1.9.5 lanciato senza finestra (`PixInsight.exe --automation-mode <!-- software-ok -->
-n --force-exit -r=<script>`) su sei frame veri di Marco (una L, quattro Hα, una OIII), piu' 200
stelle di forma nota iniettate per configurazione su fondi veri (L, Hα con nebulosa, OIII, OSC):

- **FWHM sul frame**: entro il 5 % da PixInsight (L +7 %); contro la verita' iniettata da −1 a <!-- software-ok -->
  +8 %. Il +8 % sotto i 2 px viene dall'integrazione sul pixel e lo ha anche PixInsight. La <!-- software-ok -->
  mediana delle sole cinque zone invece si scosta del +17-18 % sui campi non piatti (quattro zone
  su cinque sono angoli): **il valore del frame si prende su stelle sparse in tutto il campo**
  (una griglia 3×3, poche stelle per casella), le cinque zone restano per tilt e curvatura.
- **FWHM sotto 2 px**: sottocampionata, +5-12 % sistematico (anche in PixInsight). A schermo il <!-- software-ok -->
  segno "sottocampionata": 2 px per FWHM e' il criterio di Nyquist.
- **Eccentricita'**: entro ±0,05 da PixInsight; 0,5 iniettata torna 0,48-0,51. Una stella rotonda <!-- software-ok -->
  col rumore vero legge 0,16-0,30 (PixInsight 0,18-0,23): sotto ~0,3 il numero non distingue una <!-- software-ok -->
  stella rotonda, e la soglia "rotonde" a 0,45 ci sta sopra.
- **Angolo**: senza bias (≤2°), ma ha senso solo con eccentricita' da 0,4 in su: sotto, la
  direzione tace.
- **HFD**: +2-14 % su L e OSC, **+20-30 % con nebulosa diffusa** (lo fa anche ASTAP), perche' il
  fondo a maglie di `sep` non segue la nebulosa. Con un fondo ad anello locale attorno a ogni
  stella il bias sparisce (Hα +23 % → −1 %): **la HFD usa il fondo ad anello**.
- **Rumore**: coincide con PixInsight entro l'1-2 %. <!-- software-ok -->
- **Stelle**: il numero dipende dalla soglia (−7…+37 % contro PixInsight): si legge come <!-- software-ok -->
  indicatore, non come assoluto.
- **SNR**: nessun riferimento esterno (le definizioni di PixInsight sono altre, il guadagno non <!-- software-ok -->
  era nell'header): non verificato. A schermo si confronta solo con la stessa camera.
- **OSC**: valido solo sul superpixel 2×2; PixInsight sul grezzo non fa da riferimento. <!-- software-ok -->
- **Progetto vecchio**: FWHM +22-30 % contro PixInsight, HFD per stella inaffidabile sulle stelle <!-- software-ok -->
  deboli (sottrae una mediana globale e taglia sotto zero).

Script e risultati nello scratchpad della sessione (`valida/`), non nel repository: la prova che
resta e' quella che nasce coi test del backend, su frame sintetici a verita' nota.

### Verifica larga (18/10/2026, 45 light)

45 light veri, mai master ne' stack: ATR2600M mono (L, R, G, B, Hα, OIII, SII), Poseidon-C Pro
su tre telescopi, ASI2600MC Duo, ASI294MC Pro, Canon 700D; scale da 0,51 a 2,85 "/px; casi
difficili (fuori fuoco, mosso, nuvole, cometa). Riferimento PixInsight SubframeSelector (sulle <!-- software-ok -->
camere a colori sulla copia a superpixel), piu' 200 stelle iniettate su 13 frame veri e frame
sintetici a PSF nota. Sui 40 frame normali:

| misura | contro il riferimento: mediana / P90 | verdetto |
|---|---|---|
| FWHM | −1,9 % / 8,8 % (PixInsight); sui sintetici +1…8 %, PixInsight −7…+10 % | si pubblica | <!-- software-ok -->
| eccentricita' | −0,02 / 0,07 | si pubblica; sotto ~0,3 sono stelle rotonde |
| HFD | verita' +0…11 %; ASTAP +8…27 % | si pubblica, fondo ad anello come **media** a oggetti mascherati |
| direzione | errore 5-10° a 1σ, senza bias | solo da eccentricita' 0,4 |
| stelle | +8 % / 55 %, stessa classifica (ρ 0,98) | indicatore relativo |
| stelle sature | giusto solo col tetto letto dall'istogramma | tetto da `DATAMAX`, o dall'istogramma (la Canon satura a 61212) |
| fondo | 0,0 % / 0,3 % | si pubblica |
| rumore | +1,1 % / 2,5 % a piena risoluzione; +8 % / 17 % sul frame ridotto | a piena risoluzione |
| gradiente | 0,0 / 0,7 punti contro un piano indipendente; direzione 1,7° | si pubblica |
| tilt, curvatura | mono e reflex ρ 0,99, P90 23 e 9 punti; camere a colori sottocampionate P90 49 | mono e reflex; a colori sotto ~1,2 superpixel tace |
| SNR | nessuna correlazione con PixInsight (ρ −0,34 / 0,29) | **da ridefinire**: si prende la PSF SNR documentata da PixInsight e si riverifica | <!-- software-ok -->

Correzioni portate nel metodo: media dell'anello (la mediana, coi pixel caldi, gonfiava la HFD
del 15-24 % in banda stretta); tetto di saturazione dall'istogramma; rumore a piena risoluzione;
fit con eccentricita' ≥ 0,99 o stelle a ciambella (fuori fuoco) = forma non misurabile, resta la
HFD; camere a colori sotto ~1,2 superpixel di FWHM misurate sul canale verde a piena risoluzione.

**Tempo** (portatile, un processo): mono 26 MP 4,5 s (P90 5,8), a colori 26 MP 2,1 s, Canon 1,4 s.
Il grosso e' il filtro mediano contro i pixel caldi (1,9 s sui 26 MP). Sul miscuglio
dell'archivio di Marco circa 3,7 s a frame, 11 ore per 11.000 frame su un processo; in
parallelo meno, non misurato. Il filtro si accelera prima di costruire.

### SNR e velocita' (18/10/2026)

- **SNR = PSF SNR della documentazione di PixInsight** (ImageWeighting, eq. 7, 18-19; solo la <!-- software-ok -->
  documentazione, non il codice): c3·(Σ flussi)² / (c4·σ²), con c3 = 1,350e-7, c4 = 4,987e6, il
  flusso di ogni stella rilevata dentro l'ellisse a un decimo del massimo della sua PSF, fondo
  dall'anello locale, σ il nostro rumore. Sui 45 frame segue PixInsight: ρ 0,97, rapporto 1,04 <!-- software-ok -->
  (P10-P90 0,98-1,13). Il vecchio SNR mediano per stella non lo seguiva (ρ −0,11). Dipende da
  campo, scala, densita' stellare e da come si presenta il dato: si confronta solo dentro la
  stessa sessione e produzione, mai fra camere.
- **Filtro contro i pixel caldi**: mediana 3×3 esatta scritta in numpy (terne verticali
  ordinate una volta, poi med3 di massimo dei minimi, mediana delle mediane, minimo dei massimi),
  identica bit per bit a `scipy.ndimage.median_filter` su quattro frame e 24 volte piu' veloce
  (1,87 → 0,08 s sui 26 MP). Mono 26 MP da 4,6 a 2,75 s a frame, a colori 1,78 s, Canon 1,07 s.
  Le scorciatoie (maschera dei pixel caldi, rilevamento sul grezzo, binning) cambiavano il numero
  di stelle del 9-67 % e sono scartate.
- **11.000 frame** (miscuglio di Marco): 7,2 ore su un processo, 4,1 su due, 2,5 su quattro
  (misurato su 8 frame: ×1,75 con 2, ×2,92 con 4). Senza ASTAP e da SSD.

### I giudizi (Marco, 18/10/2026)

L'app giudica misura per misura, per frame, per notte (mediana) e per produzione (mediana).
Nessun voto d'insieme (pesare misure diverse fra loro non ha fonte) e nessun frame scartato: il
giudizio informa. Dove manca il dato che serve, il giudizio tace.

- **Tilt**: la formula di ASTAP, (angolo peggiore − migliore) / HFD mediana; fino al 10 % buono,
  10-20 % incerto, oltre non adatto ("Any tilt equal or less than 10% of the range is a good
  value", hnsky.org/astap.htm; Siril mette il limite al 10 %). <!-- software-ok -->
- **Eccentricita'**: fino a 0,45 "rotonde", 0,45-0,6 incerto, oltre 0,6 "allungate" (Marco).
  ESO FORS2 tiene solo frame con ellitticita' sotto 0,3, cioe' eccentricita' ~0,71
  (eso.org/qc/FORS2/qc/imagequality/imagequality.html): 0,6 non e' largo.
- **Fuoco**: un frame la cui HFD supera del 15 % la mediana dei migliori della stessa notte e
  filtro e' "fuoco peggiore" (Marco; SGP usa 15 % come esempio per rifare l'autofocus,
  N.I.N.A. 5 % come predefinito).
- **Luminosita' del cielo** contro il Bortle del sito: la tabella SQM ↔ Bortle di Wikipedia
  (en.wikipedia.org/wiki/Bortle_scale, fonte secondaria). Solo per L e senza filtro.
- **Gradiente e SNR**: solo rispetto alla sessione (stessa notte, oggetto, filtro): segnato il
  frame oltre mediana ± 2 MAD, come i tutorial del SubframeSelector. Per notte e produzione solo
  il numero.
- **FWHM**, rispetto allo stesso corredo (ottica, camera, focale) e filtro, due volte (Marco):
  rispetto alla notte e rispetto allo storico. Nessuna convenzione amatoriale giudica la FWHM
  contro il limite teorico del corredo (ricerca del 18/10/2026); i programmi che scelgono i frame
  la confrontano con lo stesso corredo.
  - **ottimo**: entro il +5 % dalla migliore del riferimento (il 10° percentile, non il record:
    Marco). +5 % e' il predefinito di N.I.N.A. per rifare l'autofocus
    (`AutofocusAfterHFRIncreaseTrigger.cs`, `Default = 5`).
  - **scarso**: oltre mediana + 2 MAD del riferimento: "FWHMSigma < 2", la regola del
    SubframeSelector di PixInsight piu' ripetuta (pixinsight.com/forum, threads/subframeselector-question.5939). <!-- software-ok -->
  - **buono**: in mezzo.
  - Quanti frame servono perche' il riferimento valga: nessuna fonte, da decidere con Marco.
  - **Campionamento** a parte, senza voto sul frame: FWHM sotto 1,5 px sottocampionamento grave
    (Howell et al. 1996, AJ 112, 1302; Stan Moore; manuale di CCDInspector), sotto 2 px
    sottocampionata, 2-3 px ideale (AAVSO, Astronomy Tools; 2,5-3 "excellent match" per
    Diffraction Limited, diffractionlimited.com/matching-camera-optics), sopra 3 px
    sovracampionata. Come voto del frame non funziona: sull'Askar di Marco i frame migliori (sotto
    3") stanno sotto 2,2 px.
- **Senza giudizio**: curvatura di campo (Marco), stelle, fondo, rumore, massa d'aria.
- **Backfocus dai frame: no** (Marco). Da un frame solo il verso non e' affidabile: la direzione
  dell'allungamento si inverte passando il fuoco (telescope-optics.net/astigmatism1.htm), le
  fonti si contraddicono, e gli strumenti seri lo misurano con curve di fuoco su piu' frame
  (Hocus Focus per N.I.N.A.).

### Le misure, e cosa si scrive

Si scrivono una volta, quando `measure` passa; nessuna lettura le ricalcola.

- **FWHM**, **HFD**: in pixel; a schermo in secondi d'arco (× scala misurata). Senza scala restano
  in pixel e non entrano nei confronti fra corredi.
- **Stelle**: quelle che ASTAP conta sul frame intero nella passata `-analyse` del solver (Marco):
  le cinque zone sono il 20 % del sensore, e contare noi sul frame ridotto conta i pixel caldi.
- **Eccentricita'**, **direzione dell'allungamento**: l'angolo mediano del fit (media circolare di
  2θ pesata per l'eccentricita'), girato con la rotazione della soluzione del cielo: "in AR" o "in
  Dec", la piu' vicina. A schermo "rotonde" fino a 0,45 (Marco): "0.45 must be about the threshold
  where the human eye/brain can distinguish between a circle and an ellipse"
  (stargazerslounge.com/topic/258551-how-round-are-round-stars, forum); le guide danno 0,42, asse
  corto al 91 % (astrohobby.ca/2022/02/26/star-eccentricity-and-guiding-accuracy). Nessuno
  scarto: sopra 0,45 resta il numero.

**Perche' non ASTAP per tilt e forma** (Marco l'ha chiesto, 18/10/2026): `astap_cli` 2025.11 non
ha il tilt (sta solo nella finestra grafica); `-extract` da' la HFD stella per stella ma scrive il
CSV accanto al FITS anche con `-o` (provato su una copia), e su una cartella di rete in sola
lettura fallisce; la sua HFD e' il raggio medio, alta del 6-19 % (confronto sopra); FWHM,
eccentricita' e angolo non li da'. ASTAP resta per la soluzione e il numero di stelle.
- **SNR**.
- **Fondo cielo** (ADU) e **rumore**. Confrontabile solo con la stessa camera, guadagno e posa.
- **Gradiente del fondo**: sul frame ridotto, (massimo − minimo) / mediana in %, e il lato piu'
  chiaro in direzione del cielo.
- **Tilt**: la HFD nei quattro angoli e al centro. A schermo, angolo peggiore meno migliore, in %
  della HFD al centro. Nessuna fonte da' un metodo standard ne' una soglia: solo numeri.
- **Curvatura di campo**: mediana degli angoli contro il centro, in %.
- **Stelle sature**: picco sopra il 90 % della saturazione (`DATAMAX`, o il massimo del tipo di
  dato).

Nuove rispetto al progetto vecchio: tilt, curvatura, direzione, gradiente, stelle sature (Marco).

### Allo zenit

FWHM e HFD anche allo zenit: valore / massa d'aria^0,6. "The seeing varies with the airmass to
the power of 3/5th" (ESO, eso.org/gen-fac/pubs/astclim/lasilla/seeing). Massa d'aria dell'oggetto
all'ora del frame, dalle effemeridi del sito; senza sito o coordinate, niente valore allo zenit.
Eccentricita' e SNR no: la prima misura inseguimento e ottiche, non l'aria.

### Luminosita' del cielo (mag/arcsec²)

Misura del 18/10/2026: l'opzione `-sqm` c'e' solo nell'`astap.exe` grafico (non nel CLI che usa
l'app, ne' sul NAS) e si blocca su un frame OSC. Quindi un metodo nostro:

- SQM = ZP − 2,5·log10((fondo − bias) / scala²) + estinzione, con ZP il punto zero dalle stelle
  del frame abbinate al catalogo e l'estinzione 0,2811·massa d'aria − 0,28 come ASTAP. Sulla
  stessa L mono di Marco da' 19,15, come `astap.exe -sqm`.
- **Catalogo**: i file di ASTAP sul disco, letti da noi (formato documentato su hnsky.org). D80
  porta Gaia BP: vale per L, senza filtro e OSC (raw, mai debayerizzato).
- **R, G, B ognuno nella sua banda** (Marco): stelle tarate nella banda del filtro col catalogo V50
  (V e colore BP−RP) e le trasformazioni pubblicate da Gaia, da verificare e citare alla
  costruzione. A schermo "R: 20,8 mag/arcsec²", non uno SQM. Senza V50 tace e dice perche'.
  Non esiste un coefficiente fisso fra bande: dipende dal colore del cielo (cielo buio a La Palma:
  B 22,7, V 21,9, R 21,0; Benn e Ellison 1998).
- Filtri stretti (Hα, OIII, SII): mai.
- **Bias**: campo facoltativo "Bias (ADU)" della camera (si aggiunge ad ADR 0021). Senza, si stima
  e la misura porta scritto "senza bias" (Marco).
- Errore atteso ±0,1-0,2 mag: stima, non misura.

### Il resto

**Nessun voto d'insieme e nessuno scarto** (Marco, confermato; ADR 0013): i giudizi misura per
misura sono sopra, e informano soltanto. Medie e
mediane solo sui frame misurati.

**Dove si vedono**: Notti, Archivio, Statistiche. La scheda dell'oggetto no, per ora (Marco).

## Conseguenze

- `frame_metrics` si allarga (HFD per zona, direzione, gradiente, sature, massa d'aria, SQM e la
  sua banda, i segni "senza bias" e "fit non riuscito"); schema ricreato.
- La HFD di ASTAP smette di finire in `frame_metrics`; la passata `-analyse` resta per il numero
  di stelle.
- Le stelle misurate per zona hanno un tetto: in banda stretta, con molte stelle, il fit e la HFD
  arrivavano a 3,1 s a frame.
- `measure` legge i pixel dopo `solve`, in sola lettura: niente file accanto ai FITS.
- Un lettore dei cataloghi di ASTAP (D80, V50), coi suoi test.
- Il fondo in ADU non si confronta fra camere diverse: a schermo lo si dice.
