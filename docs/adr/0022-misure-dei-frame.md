# 0022 -- Le misure dei frame: tutte, attestate, nel database, senza voto

**Stato:** accettata, 18/10/2026 (Marco); superata in parte da ADR 0033 (stelle da `measure`), 0037 (SNR, zone, tilt) e 0039 (Qn, eccentricita', oggetto basso, Bortle del sito). Ridotta il 26/10/2026: il metodo costruito, le misure sul vero e i testi stanno in `docs/domini/misure.md`.

## Contesto

Marco vuole i dati completi nel database, per confrontare notti, setup e siti, misurati "come
PixInsight o Siril": veloci, ma corretti. Stack di ADR 0007: `sep` con numpy e scipy. Ricerca <!-- software-ok -->
del 18/10/2026 sul codice di Siril, N.I.N.A., ASTAP e sulla documentazione di PixInsight <!-- software-ok -->
(ImageWeighting); il codice di PCL non si porta (licenza). Verifiche del 18/10/2026: 12 frame
sintetici a verita' nota, SubframeSelector di PixInsight su sei frame veri e 200 stelle iniettate, <!-- software-ok -->
45 light di sette setup, 62 frame per l'ottimizzazione; script fuori dal repository, la prova
che resta nasce coi test.

## Decisione

**Il metodo** (dettagli e scarti costruiti in `domini/misure.md`):

1. Fondo `sep.Background`; rumore 1,4826 x MAD a piena risoluzione (Rousseeuw e Croux, JASA
   88:1273, 1993); coincide con PixInsight entro l'1-2%. <!-- software-ok -->
2. Stelle con `sep.extract` a 5 sigma (Siril) su una copia filtrata con mediana 3x3 esatta (il <!-- software-ok -->
   conteggio, dal passo 25.15, e' quello del SubframeSelector: ADR 0033 D1, `misure.md`): in <!-- software-ok -->
   banda stretta la maggior parte dei rilevamenti sul grezzo erano pixel caldi. Tenute: intere,
   picco sotto il 90% della saturazione, lontane dal bordo e dalle vicine piu' di 3 FWHM; b/a
   sopra 0,5 solo per l'HFD: la forma le prende tutte, se no un frame mosso non ne ha (25.1).
3. **HFD**: diametro col meta' flusso, fondo ad anello locale (con la nebulosa il fondo a maglie
   dava +20-30%). Sostituisce la HFD di ASTAP, il raggio medio, alta del 6-27%.
4. **FWHM, eccentricita', angolo**: fit di Moffat ellittico (Levenberg-Marquardt) integrato sul
   pixel, 60 stelle per casella di una griglia 3x3 lungo tutta la classifica di flusso; FWHM =
   2a sqrt(2^(1/b) - 1), eccentricita' sqrt(1 - (b/a)^2) (PixInsight). Fit che non converge: <!-- software-ok -->
   momenti di `sep`, detto. Eccentricita' >= 0,99 o stella a ciambella: forma non misurabile.
   Angolo solo da eccentricita' 0,4, girato col cielo: "in AR" o "in Dec". Il 25.1 scrive
   l'angolo sui pixel; il giro col cielo arriva al 25.2 con la scala risolta (stesso incontro fra
   measure e solve).
5. **SNR**: PSF SNR della documentazione di PixInsight (ImageWeighting, eq. 7, 18-19), c3 = <!-- software-ok -->
   1,350e-7, c4 = 4,987e6; sui 45 frame rho 0,97 con PixInsight. Mai fra camere o oggetti. <!-- software-ok -->
6. **Camere a colori** (Marco, 26/10/2026, passo 24.06; prima: superpixel 2x2) come WBPP: debayer
   VNG a piena risoluzione (Chang, Cheung e Pan 1999, il VNGThread di PixInsight portato), poi <!-- software-ok -->
   tutto sull'intensita' HSI (min + max) / 2, il piano su cui misura il SubframeSelector; pattern
   da `BAYERPAT` con `XBAYROFF`/`YBAYROFF`, come l'Auto del Debayer. Il rumore come lo dice WBPP:
   per piano R, G, B del mosaico, poi (min + max) / 2. Il superpixel allargava le
   stelle piccole: Canon 700D HFD 6,94 px contro 3,97 di ASTAP, con VNG 3,20.
7. **Altre misure**: fondo e rumore in ADU (solo stessa camera, guadagno, posa); gradiente sul
   frame ridotto, (max - min) / mediana, col lato piu' chiaro; tilt e curvatura dalla HFD in
   cinque zone (quattro angoli e centro); stelle sature (`DATAMAX` o il tetto dall'istogramma);
   FWHM e HFD anche allo zenit, valore / X^0,6 (ESO, "seeing varies with the airmass to the power
   of 3/5th"), con sito e coordinate.
8. **SQM**: il metodo di ASTAP portato (MPL-2.0, nei crediti; `-sqm` c'e' solo nell'eseguibile
   grafico): ZP = 21 + 2,5 log10 della media pesata per SNR di flusso / 10^((21 - BP)/2,5), scarto
   a 1,5 sigma, flusso col fondo dall'anello; cielo = moda dell'istogramma; SQM = ZP - 2,5
   log10((cielo - bias)/scala^2) + 0,2811 X - 0,28, X di Pickering 2002. Catalogo D80 (Gaia BP);
   solo mono col filtro L e a colori (Marco, 28/10/2026: un mono senza filtro scritto tace; a
   colori superpixel, media dei quattro). Verificato contro `astap.exe -sqm` su 48 frame mono:
   mediana 0,003 mag, massimo 0,028 (`misure.md`). Mono senza bias: "senza bias" (0,03-0,18 mag); a colori solo col bias della camera
   (ADR 0021): senza, fino a 0,9 mag. `OFFSET` non e' il bias in ADU, ma lo sceglie: il bias si
   dichiara per camera e offset (Marco, 28/10/2026). Costruito al passo 25.3: `misure.md`.
9. Il Bortle del sito dalle misure: l'app propone, l'utente sceglie (`domini/sito.md`).

**I giudizi** (Marco, 18/10/2026): misura per misura, per frame, notte e produzione (mediana);
nessun voto d'insieme e nessuno scarto (lo sceglie l'utente, ADR 0032); dove manca il dato, tace.

- **FWHM in secondi d'arco**, fasce dal consenso dei forum (32 casi, 18/10/2026): sotto 2"
  eccellente ("Below 2 is advanced imager in great skies", cloudynights.com/forums/topic/644278),
  2-3" buono, 3-4" nella media ("3.0 to 3.5 arcsec is normal", AAVSO), 4-5" scarso ("4 arcsec
  is poor", AAVSO), oltre pessimo. **Limite del setup** F = max(2 x scala, 1,029 lambda/D) ("the
  realistic minimum FWHM is 2 pixels", AstroBin 10757): sotto F "al limite del setup"; F oltre
  3" "non giudicabile su questo setup", col perche' ("Limite del setup 3.9″: due pixel da 1.94″.").
  Usare F per alzare i bordi e' una scelta di Marco. Lo schema solo relativo e' scartato.
- **Campionamento**, senza voto: sotto 1,5 px grave (Howell et al. 1996), sotto 2 px
  sottocampionata, 2-3 ideale (AAVSO; Diffraction Limited), sopra 3 sovracampionata.
- **Fuoco**: HFD oltre il 5% del 10° percentile della notte e filtro, "fuoco peggiore" (N.I.N.A.,
  `AutofocusAfterHFRIncreaseTrigger.cs`, Default = 5); minimo 10 frame per i giudizi della notte.
- **Per l'oggetto** (minimo 10 frame, tutte le notti): "SNR basso per l'oggetto", "HFD alta per
  l'oggetto" oltre la soglia relativa (mediana +-2,5 Qn, ADR 0039); "SNR basso per la notte".
- **Tilt**: (peggiore - migliore) / HFD mediana, fino al 10% buono, 10-20 incerto, oltre non
  adatto (hnsky.org/astap.htm; Siril al 10%). <!-- software-ok -->
- **Eccentricita'** relativa al setup, avviso "stelle allungate" (ADR 0039).
- **Oggetto basso**: sotto 30 gradi esteso, 45 stelle (ADR 0039).
- **SQM contro il Bortle del sito**: la tabella di ASTAP (`domini/sito.md`, ADR 0035).
- Solo il numero: gradiente, curvatura, stelle, fondo, rumore, massa d'aria, HFD contro il setup.
- **Backfocus dai frame: no** (Marco): da un frame il verso non e' affidabile.

**Unita'**: FWHM e HFD sempre in secondi d'arco e pixel; il giudizio usa i secondi, il
campionamento i pixel. **Dove**: Notti, Archivio, Statistiche, Selezione dei frame; la scheda
dell'oggetto no (Marco).

## Conseguenze

- Le misure si scrivono una volta, quando `measure` passa, in `pipeline_measures`; nessuna
  lettura le ricalcola. `frame_metrics` della pipeline vecchia e' uscita col passo 25.
- La passata `-analyse` esce (ADR 0033, D1); il tilt non viene da ASTAP: `astap_cli` non lo ha, e
  `-extract` scrive un CSV accanto al FITS anche con `-o`.
- `measure` legge i pixel in sola lettura, niente file accanto ai FITS.
- Un lettore dei cataloghi di ASTAP (D80), coi suoi test, col passo 25.3.
- Il fondo in ADU non si confronta fra camere diverse: a schermo lo si dice.
