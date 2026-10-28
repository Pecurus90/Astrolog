# Per Claude Design -- Statistiche, brief completa (v1.3)

## 0quater. Allineamento alle regole del 24/10/2026

La pagina e' ancora in lavorazione con Marco: questa brief resta finche' non c'e' un contratto.
Valgono sopra cio' che segue:
- **Bortle del sito** (ADR 0039, regola intera in `docs/domini/sito.md`): notti in almeno 4 mesi
  degli ultimi 12, nessun buco oltre 3 mesi, livello annuo da un fit armonico. Dati scarsi:
  **«Servono notti in almeno 4 mesi, senza buchi di oltre 3: finora {n} notti in {m} mesi.»**
  (Marco). Esce «Servono notti in 6 mesi diversi».
- **"Qualita' della notte" (0-100) diventa la Trasparenza** (ADR 0034): nuvole per aerosol, il
  seeing fuori dal voto. Le notti buone restano quelle da 70. La riga «qualita' senza seeing»
  cade; al suo posto, quando manca l'aerosol, una riga «senza aerosol» (testo da far approvare a
  Marco). Nel selettore, «Qualita' media della notte» diventa «Trasparenza media della notte»
  (da approvare).

## 0ter. Risposte alle domande della v31.6 (20/10/2026)

1. **«Confronta setup»: si'** (Marco), ma **in ″**, non in px. La FWHM in ″ e' il cielo piu'
   l'ottica, e si confronta fra setup diversi; in px dipende dalla scala di ciascuno. L'app ha
   la scala di ogni frame risolto (`frame_wcs.scale_arcsec_px`). Due setup scelti, sovrapposti sul
   giorno dell'anno, con le loro bande; il px resta nel valore al passaggio.
2. **Calendario in «Tutto»: un anno alla volta**, come avete fatto (Marco).
3. **Seeing nella griglia: tutte le notti col meteo**, come avete fatto: e' il cielo del sito,
   non delle tue uscite. Le misure dei frame restano sulle notti uscite. Scelta di metodo.
4. **Confronto allo stesso giorno**: si', come avete fatto (contratto: il cumulato letto alla
   stessa data). Con «Tutto» o un anno finito, l'anno intero.
5. Testi:
   - «Tutti i setup insieme: FWHM e HFD cambiano da un setup all'altro.» -> va bene, ma in ″ si
     confrontano: **«Tutti i setup insieme: in px FWHM e HFD cambiano da un setup all'altro.»**
   - «In px si confronta fra setup diversi; in ″ no» e' **al rovescio**. Diventa: **«FWHM
     mediana allo zenit. In ″ si confronta fra setup diversi; in px dipende dalla scala.»**
   - **Bortle**: sotto il numero solo «misurato su {n} notti» (come in Impostazioni); la regola
     intera al passaggio o al tocco della ⓘ (Marco).
6. **Dati**: oggi l'app **non ne manda nessuno** per le Statistiche: la pagina si costruisce
   dopo, e FWHM, HFD, eccentricita' e SQM arrivano con lo stadio `measure` (ADR 0022). L'elenco
   va bene cosi' com'e': lo prendiamo come contratto della rotta. Continuate coi dati di prova.

## 0bis. Correzione alla v31.1 (20/10/2026)

La v31.1 e' a posto. Una sola cosa cambia, scelta di Marco: **niente "setup con piu' ore" al
posto di «Tutti»**. Il setup lo sceglie l'utente dalla tendina in testa (sez. 1), e la griglia
segue: un setup, oppure **«Tutti» = tutti i setup insieme** (mediana su tutte le notti uscite),
per FWHM, HFD, stelle e fondo come per le altre misure. Sotto la griglia, con «Tutti» e piu' di
un setup: «Tutti i setup insieme: FWHM, stelle e fondo cambiano da un setup all'altro.» (testo
da approvare). Esce «il setup con piu' ore negli ultimi 12 mesi». Approvati gli altri testi
della v31.1 («nessuna uscita con {setup}», la riga della regola del Bortle).

## 0. Correzioni alla prima consegna (20/10/2026)

La pagina e' piaciuta molto a Marco. Si corregge e si aggiunge solo questo:

1. **Piu' misure nella griglia mesi x anni** (Marco). Il selettore della sez. 6 porta:
   - dal meteo: **Notti buone e uscite**, **Qualita' media della notte** (0-100), **Seeing**;
   - dai frame: **FWHM allo zenit**, **HFD allo zenit** (″ e px), **Eccentricita'**, **Stelle**
     (numero per posa), **Fondo cielo** (ADU), **SQM**;
   - **Ore integrate**.
   Mediana del mese. FWHM, HFD, stelle e fondo dipendono dal setup: con «Tutti» si mostra il
   setup con piu' ore, come avete gia' fatto per la FWHM (approvato), e la riga lo dice.
   Raggruppate il selettore in tre: «Cielo», «Frame», «Volumi».
2. **Bortle in sez. 9**: «misurato su {n} notti» segue la regola dell'ADR 0022, non la mediana di
   tutte le notti: la regola e la frase dei dati scarsi in 0quater.
3. **Approvati da Marco**: gradini del calendario a 2, 4 e 6 ore; FWHM del setup con piu' ore;
   «Cielo» diviso in SQM e Seeing; i vostri testi nuovi, con una correzione: «Scansiona ora» ->
   **«Scansiona»**, come nel resto dell'app.
4. Registrate le Statistiche nel CHANGELOG e una sezione nelle DECISIONI.

---

Da Claude Code, 20/10/2026. L'ultima pagina che manca: **Statistiche** (`/statistiche`), voce del
gruppo «Guarda» accanto ad Archivio, Notti, Progetti e Attrezzatura. Decisioni in
`docs/adr/0024-statistiche.md` (con le fonti), qualita' della notte in
`docs/adr/0020-qualita-della-notte-da-0-a-100.md`, misure dei frame in
`docs/adr/0022-misure-dei-frame.md`. Le parole fra «» sono proposte: Marco le approva sulla
tavola. I numeri li manda l'app; la pagina non calcola niente.

**Cosa fa la pagina**: confronta nel tempo. Quanto esci, quanto sfrutti il cielo che hai, come
cambiano le stagioni, i filtri, i setup e la qualita' dei tuoi frame. Glossario: «Statistiche»,
mai «analitica», «report», «grafici».

## 1. In testa

- Titolo «Statistiche».
- **Anno**: pillole degli anni con frame, l'ultimo acceso; una voce «Tutto».
- **Confronta con**: di partenza l'anno prima; «nessuno» per toglierlo.
- **Sito**: tendina, di partenza il sito di casa. Le notti buone sono di un posto.
- **Setup**: «Tutti» di partenza, o uno (setup = ottica + camera, + riduttore).

## 2. L'anno in un colpo

- **Numero grande: notti buone sfruttate.** «18 su 31 notti buone» (buona = qualita' della notte
  da 70, la stessa del Meteo). Sotto in piccolo l'anno di confronto: «l'anno scorso 14 su 27».
  Riga d'aiuto: «Notti con qualita' da 70 al sito, e in quante sei uscito.»
- Accanto quattro celle col delta sull'anno di confronto: **notti uscite**, **ore integrate**,
  **frame**, **resa del buio** («62 %»; aiuto: «Ore integrate sulle ore di buio delle notti in cui
  sei uscito.»).
- Le notti prima dell'app non hanno il seeing: la qualita' si calcola senza, e una riga lo dice:
  «Notti prima del {data}: qualita' senza seeing.»

## 3. Calendario delle notti

Griglia dell'anno, settimane in colonna, giorni in riga, mesi scritti sopra.
- Quadretto pieno, **piu' scuro con piu' ore integrate** (scala sequenziale, 4-5 gradini).
- **Contorno** sulle notti buone in cui non sei uscito: le notti perse.
- Vuoto chiaro: nessuna uscita, notte non buona.
- Il colore non e' l'unico segno (WCAG 1.4.1): al passaggio o al tocco «sab 12 ott · 5 h 20 ·
  qualita' 84» oppure «notte buona, non sei uscito».
- Legenda sotto: «meno ore … piu' ore» e «notte buona persa».

## 4. Volumi nell'anno

- Barre per notte (ore integrate), in «Tutto» per mese.
- **Cumulato**: linea dell'anno e linea dell'anno di confronto, sovrapposte sul **giorno
  dell'anno** (asse da gennaio a dicembre senza anno). Il punto di oggi dice «al {giorno}:
  {ore} h · l'anno scorso {ore} h».
- Cambio di setup: un segno verticale sottile sulla serie con il nome.

## 5. Capacita': la qualita' dei frame

Una misura alla volta, da un selettore: **FWHM allo zenit** (arcsec e px, sempre le due
unita'), **HFD allo zenit**, **eccentricita'**. Niente SNR (fra notti diverse non si
confronta).
- Un punto per notte x setup, con la **banda dei quartili** (sotto 4 misure niente banda, solo
  il punto).
- Linea di tendenza: mediana mobile su 7 notti, spezzata dove passano piu' di 26 giorni senza
  notti.
- Due anni sovrapposti sul giorno dell'anno: il progresso si legge come **banda che si
  stringe**.
- Riga sotto: «Allo zenit: valore diviso per la massa d'aria alla 0,6 (ESO).» e, se ce ne sono,
  «{n} frame senza massa d'aria esclusi.»
- Prima che l'app misuri i frame: «Le misure dei frame non ci sono ancora.»

## 6. Stagioni: mesi x anni

Una griglia: righe gli anni, colonne i 12 mesi; sotto la riga **media** e le **quattro stagioni
meteorologiche** (inverno dic-gen-feb, primavera mar-apr-mag, estate giu-lug-ago, autunno
set-ott-nov; l'inverno porta il dicembre dell'anno prima). Ogni casella col numero e un colore
sequenziale. Selettore della misura:
- **Notti buone e uscite** («9 · 6»: buone, uscite);
- **Ore integrate**;
- **FWHM mediana allo zenit** (arcsec);
- **Cielo**: SQM mediano (mag/arcsec²) e seeing mediano (″).
Casella senza dato: vuota con un trattino, al passaggio il perche' («nessuna uscita», «seeing non
archiviato prima del {data}»). Si legge «ottobre e' sempre il mio mese migliore» in un colpo.

## 7. Per filtro

Ore integrate per filtro nell'anno, **barre impilate per mese**; il filtro con piu' ore in basso,
il totale scritto sopra ogni barra. Accanto la tabellina: filtro, ore, frame, notti. Filtri dai
nomi dell'utente (L, R, G, B, Hα, OIII, SII, dual band…); colori del foglio per banda.

## 8. Per setup

Una riga per setup: **ore**, **frame**, **oggetti**, **FWHM mediana allo zenit** a parita' di
altezza, e su che tipo di oggetti ha lavorato di piu' (nebulose, galassie, ammassi). Niente
classifica: ordine per ore.

## 9. Cielo del sito

- **SQM** per mese e anno (mag/arcsec²), dai frame L o a colori. Due serie:
  **Luna sotto -5°** e **Luna su**.
- **Curva media per ora della notte**: SQM medio dalle 21 alle 05, per vedere quando il cielo e'
  piu' buio.
- Sotto il Bortle del sito, come in Impostazioni: «misurato su {n} notti».
- Riga: «Solo frame L o a colori: i filtri stretti non misurano il cielo.»

## 10. Stati (Tweaks)

Pieno (6 anni); primo anno (niente confronto, niente righe «l'anno scorso»); zero frame («Nessun
frame ancora: le statistiche nascono con la prima notte.» col rimando alla scansione); misure dei
frame non ancora calcolate (sez. 5 e 9 dicono perche', il resto c'e'); sito senza meteo storico
(«Meteo storico in arrivo» al posto delle notti buone); un setup solo (sez. 8 sparisce).

## 11. Telefono

Una colonna: in testa anno e numero grande; il calendario scorre in orizzontale dentro la sua
carta (la pagina no); la griglia mesi x anni diventa la scelta di un anno e 12 righe; i grafici a
tutta larghezza, il valore al tocco. Bersagli da 44 px.

## Fuori

- Scarto dei frame, classifiche fra oggetti, voto d'insieme.
- Correlazione fra qualita' dei frame e meteo.
- SNR nel tempo.
- Stima dello SQM per i filtri stretti.

CHANGELOG e DECISIONI come al solito.
