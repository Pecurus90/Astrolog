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

**Nessun voto e nessuno scarto**: l'app misura e basta (Marco, confermato; ADR 0013). Medie e
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
