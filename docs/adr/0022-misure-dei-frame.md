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

### Ottimizzazione su 62 frame (18/10/2026)

Sette corredi, anche due da ASIAIR (Newton ~1000 mm + ASI2600MC, rifrattore 335 mm + ASI294MC).

- **Stelle per il fit**: 60 per casella della griglia 3×3, prese su tutta la classifica di
  flusso, non le piu' luminose. Le stelle luminose sono piu' rotonde (anche in PixInsight: 0,49 <!-- software-ok -->
  sopra SNR 160 contro 0,55 fra 40 e 80), e PixInsight fa la media su tutte le stelle rilevate <!-- software-ok -->
  (verificato rifacendo le sue fit stella per stella). Stella per stella misuriamo come lui:
  scarto mediano 0,000 su 22.900 stelle. Fit di Moffat a lotti in numpy (540 stelle in 0,4 s).
- **Eccentricita'**: dal fit campionato al centro del pixel, media sulle stelle con SNR ≥ 20.
  Contro PixInsight P90 0,020 (prima 0,074), peggiore 0,036; giudizio diverso a 0,45 in 1 frame <!-- software-ok -->
  su 57 (prima 9), a 0,6 in 3 (prima 8); sulla mediana della notte nessuno. Sotto 1,6 px sia
  PixInsight sia noi leggono 0,6 come 0,55. <!-- software-ok -->
- **FWHM vera** (Marco): fit di Moffat integrato sul pixel, mediana. Contro la verita' iniettata
  P90 1,4 % (PixInsight 19 %, il metodo di prima 20 %). Esce ~14 % sotto PixInsight, perche' <!-- software-ok -->
  PixInsight legge le stelle sottocampionate piu' grandi del vero (+13 % sotto 2 px, +24 % a <!-- software-ok -->
  1 px). Conseguenza dichiarata: le fasce dei forum vengono da programmi con quello stesso
  errore, quindi sui corredi sottocampionati il giudizio dell'app e' un po' piu' generoso di
  quello che darebbe chi misura con PixInsight. A schermo il numero non torna con PixInsight: <!-- software-ok -->
  la guida lo spiega.
- **Tempo**: mono 26 MP ~3,1 s a frame (P90 4,4), a colori 1,2 s, Canon 0,8 s.

### I giudizi (Marco, 18/10/2026)

L'app giudica misura per misura, per frame, per notte (mediana) e per produzione (mediana).
Nessun voto d'insieme (pesare misure diverse fra loro non ha fonte) e nessun frame scartato: il
giudizio informa. Dove manca il dato che serve, il giudizio tace.

- **Tilt**: la formula di ASTAP, (angolo peggiore − migliore) / HFD mediana; fino al 10 % buono,
  10-20 % incerto, oltre non adatto ("Any tilt equal or less than 10% of the range is a good
  value", hnsky.org/astap.htm; Siril mette il limite al 10 %). <!-- software-ok -->
- **Eccentricita'**: fino a 0,45 "rotonde"; oltre 0,71 "allungate"; in mezzo solo il numero
  (Marco). 0,71 e' il limite ESO: FORS2 tiene solo frame con ellitticita' sotto 0,3, cioe'
  eccentricita' ~0,71 (eso.org/qc/FORS2/qc/imagequality/imagequality.html).
- **Fuoco**: un frame la cui HFD supera del 5 % il 10° percentile della stessa notte e filtro e'
  "fuoco peggiore" (Marco): 5 % e' il predefinito di N.I.N.A. per rifare l'autofocus
  (`AutofocusAfterHFRIncreaseTrigger.cs`).
- **Minimo per i giudizi "per la notte"** (fuoco, SNR): 10 frame della stessa notte, oggetto e
  filtro; sotto, tacciono (Marco). 10 e' il `SampleSize` predefinito dello stesso trigger di
  N.I.N.A.
- **Luminosita' del cielo** contro il Bortle del sito: la tabella SQM ↔ Bortle di ASTAP
  (`bortle()`, da ClearDarkSky: Bortle 5 = 19,50-20,49, 6 = 18,94-19,50), la stessa del
  programma da cui viene il metodo (Marco). Solo per L, senza filtro e camere a colori.
- **SNR**: solo rispetto alla sessione (stessa notte, oggetto, filtro): "SNR basso per la notte"
  sotto mediana − 2 MAD, come i tutorial del SubframeSelector. Per notte e produzione solo il
  numero.
- **Gradiente**: solo il numero (Marco): nessuna fonte lo giudica, e la regola dei 2 MAD i
  tutorial la usano per FWHM e SNR.
- **FWHM e HFD a schermo sempre in due unita'**: secondi d'arco e pixel, uno accanto all'altro
  (Marco, 18/10/2026). Il SubframeSelector di PixInsight mostra i pixel finche' non gli si da' <!-- software-ok -->
  la scala: chi confronta i numeri deve ritrovare gli stessi. Il giudizio usa i secondi d'arco, il
  campionamento i pixel. <!-- software-ok -->
- **FWHM: giudizio assoluto in secondi d'arco** (Marco, 18/10/2026). Uno schema solo relativo
  (contro lo storico dello stesso corredo) e' scartato: chi ha sempre guida o fuoco cattivi
  risulterebbe "buono". Le fasce vengono dal consenso dei forum (32 casi verificati su Cloudy
  Nights, Stargazers Lounge, AstroBin, IceInSpace, webastro, AAVSO; ricerca del 18/10/2026):
  - sotto 2" **eccellente** ("Below 2 is advanced imager in great skies", cloudynights.com/forums/topic/644278);
  - 2-3" **buono** (il taglio a 3" e' il piu' comune);
  - 3-4" **nella media** ("3.0 to 3.5 arcsec is normal", archive.aavso.org/fwhm-expectations-larger-aperture-instruments);
  - 4-5" **scarso** ("4 arcsec is poor", stessa pagina AAVSO);
  - oltre 5" **pessimo**.
  - **Limite del corredo** F = max(2 × scala, 1,029·λ/D): sotto due pixel e sotto la
    diffrazione il corredo non registra stelle ("the realistic minimum FWHM is 2 pixels",
    AstroBin, topic 10757; lo ripetono altri). Una FWHM sotto F e' "al limite del corredo", non
    "eccellente"; ogni bordo sotto F sale a F. Sull'Askar di Marco (1,385"/px) F = 2,77": buono
    2,77-3", e il suo scarto oltre 3" e' "tengo buono ed eccellente". Se F supera i 3" (es. 60/300
    a 2,59"/px, F = 5,2") la FWHM non distingue una notte buona da una media: "non giudicabile su
    questo corredo". Usare F per alzare i bordi e' una scelta (Marco), non una convenzione.
  - Resta, come dato in piu', il confronto con la notte:
  +5 % sul migliore e' il predefinito di N.I.N.A. per rifare l'autofocus
  (`AutofocusAfterHFRIncreaseTrigger.cs`, `Default = 5`); "FWHMSigma < 2" la regola del
  SubframeSelector di PixInsight piu' ripetuta (pixinsight.com/forum, threads/subframeselector-question.5939). <!-- software-ok -->
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

- **Il metodo di ASTAP, portato** (sorgente MPL-2.0, github.com/han-k59/astap; MPL e' compatibile
  con la GPL-3 di AstroLog, e va nei crediti): ZP = 21 + 2,5·log10 della media pesata per SNR di
  flusso/10^((21 − BP)/2,5), con lo scarto a 1,5σ; flusso nel quadrato della stella col fondo
  dall'anello; cielo = moda dell'istogramma; SQM = ZP − 2,5·log10((cielo − bias)/scala²) +
  0,2811·X − 0,28, X di Pickering 2002 dall'altezza ricalcolata. Tutto per posa, in ADU.
- **Verifica** (18/10/2026, 18 frame mono L di Marco, 7 notti, altezze 31-82°): contro
  `astap.exe -sqm` scarto mediano 0,003 mag, massimo 0,007 (l'arrotondamento di ASTAP); stesso
  punto zero e stesse stelle di calibrazione. Tempo 0,5-0,9 s a frame, da vettorializzare.
- **Catalogo**: lettore nostro dei file .1476 di ASTAP (numpy, coi suoi test). D80 porta Gaia BP:
  vale per L, senza filtro e camere a colori (superpixel 2×2, media dei quattro; i mono binnati
  2×2 restano entro +0,035 da ASTAP).
- **B e G** col catalogo V50 di ASTAP (1,0 GB, lo scarica l'utente come il D80: porta V e il
  colore delle stelle), con le relazioni di Gaia DR3 (Riello et al. 2021, A&A 649, A3, tab. C.2).
  A schermo "B: 20,8 mag/arcsec²", non uno SQM. Senza V50 tace e dice "manca il catalogo V50".
- **R: dopo** (Marco): serve G, BP e RP di Gaia per ogni stella, che nessun catalogo di ASTAP
  porta; resta fra le idee (VizieR con cache, o un estratto nostro).
- Filtri stretti (Hα, OIII, SII): mai.
- **Bias**: campo facoltativo "Bias (ADU)" della camera (ADR 0021). Senza, si mostra lo stesso con
  "senza bias" (Marco), anche sulle camere a colori. Peso misurato: sulle mono 0,03-0,18 mag, su
  una ASI2600MC fino a 0,9 mag. `OFFSET` non e' un ADU uguale per tutte le camere e non si usa.

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
