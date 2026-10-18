# Per Claude Design -- Attrezzatura v2 e le misure dei frame

Da Claude Code, 18/10/2026. Una brief sola: le risposte su Attrezzatura v2 (controllata contro le
decisioni) e le misure dei frame, nuove. Decisioni in `docs/adr/0021-dati-completi-dell-attrezzatura.md`
e `docs/adr/0022-misure-dei-frame.md`. I testi qui sotto li ha approvati Marco.

# Parte 1 -- Attrezzatura v2

Campi, conti, frasi "manca …", avviso della guida, carico: tornano con le decisioni. Cosa cambia.

## 1. Difetti da correggere

- **Distanziali "(vuoto: dai file)"**: nessun file indica i distanziali. Etichetta: "Distanziali".
  "(vuoto: dai file)" resta solo sulle parti che i file possono dire.
- **"in esploso, a misura"**: le lunghezze del tubo e della camera e i diametri sono stimati, quindi
  non è a misura. Testo: "Schema non in scala. Seleziona uno strumento per aprirlo."
- **Numeri scientifici col punto** (regola dell'app, come nei programmi di ripresa): campionamento,
  scala di guida, FWHM, HFD, potere risolutore → "1.94″/px", "1.61″". Millimetri, chili e
  percentuali restano con la virgola.

## 2. Le vostre domande

1. **Schema ottico**: entra (Marco). Voci: rifrattore, Newton, Schmidt-Cassegrain,
   Ritchey-Chrétien, Maksutov, obiettivo fotografico, altro.
2. **Ordine del treno** (riduttore, guida fuori asse, distanziali, ruota, camera): va bene per il
   disegno. L'app non conosce l'ordine vero, che sceglie l'utente; i conti non ne dipendono.
3. **Backfocus**: niente tolleranza fissa (Marco). Campo nuovo **"Tolleranza del backfocus (mm)"**
   nella scheda di riduttore e ottica, dal produttore.
   - Con la tolleranza: "esatto", "+0,5 mm, in tolleranza", "corto di …", "lungo di …".
   - Senza: solo la differenza ("+0,5 mm"), senza pillola.
   - La tolleranza è quella del riduttore se c'è, altrimenti dell'ottica: la stessa regola del
     backfocus richiesto.
4. **Misure stimate del treno**: la stima basta, con la frase del §1.
5. **Meteo**: va bene. Le scale dei corredi arrivano dall'app, già calcolate.

## 3. Testi (approvati)

| nel disegno | diventa |
|---|---|
| I numeri del corredo | **Dati del corredo** |
| calcolati dalle schede dei pezzi | **Dalle schede tecniche degli strumenti.** |
| Il treno ottico | **Treno ottico** |
| in esploso, a misura; tocca un pezzo o il suo nome per aprirlo | **Schema non in scala. Seleziona uno strumento per aprirlo.** |
| ci sta / non ci sta | **copre il sensore / non copre il sensore** |
| nei limiti / fuori dai limiti | **nell'intervallo / fuori intervallo** |
| pari | **esatto** |

Restano: "Campionamento", "Schema ottico", "Guide fuori asse", "Distanziali", "entro il carico" /
"oltre il carico", "corto di …" / "lungo di …", le frasi "manca …". "Pezzo" non si usa: la parola
dell'app è "strumento".

## 4. Campi nuovi nel modulo

- Ottica: **Schema ottico**, **Tolleranza del backfocus (mm)**.
- Riduttore: **Tolleranza del backfocus (mm)**.
- Camera: **Bias (ADU)**, facoltativo (serve alla luminosità del cielo, parte 2).

# Parte 2 -- Le misure dei frame

L'app misura e basta: **nessun voto, nessuno scarto, nessun "frame buono/cattivo"** (Marco).
Oggi l'app ha solo HFD e stelle: il resto arriva col backend, dopo il disegno.

## 5. Cosa misura, per ogni frame

| misura | a schermo | nota |
|---|---|---|
| FWHM | ″ | senza scala del cielo in px, e non si confronta fra corredi |
| FWHM allo zenit | ″ | accanto alla FWHM |
| HFD | ″ | anche allo zenit |
| Stelle | numero | contate sul frame intero |
| Stelle sature | numero | |
| Eccentricità | da 0 a 1 | **"rotonde" fino a 0,45** (Marco); sopra, solo il numero |
| Direzione dell'allungamento | "in AR" / "in Dec" | accanto all'eccentricità |
| SNR | numero | |
| Fondo cielo | ADU, col rumore | si confronta solo con la stessa camera, guadagno e posa: la tavola lo dice |
| Gradiente del fondo | % e lato ("più chiaro verso est") | |
| Tilt | % | angolo peggiore meno migliore, sulla HFD al centro |
| Curvatura di campo | % | media degli angoli contro il centro |
| Luminosità del cielo | "SQM 19.2" o "R: 20.8" mag/arcsec² | sotto |

Tilt e curvatura si possono mostrare come cinque numeri (quattro angoli e centro) su un
rettangolo del sensore.

**Luminosità del cielo**:
- Con L, senza filtro e camere a colori si chiama SQM. Con R, G e B la banda davanti ("R: 20.8
  mag/arcsec²"): non è uno SQM.
- Con Hα, OIII e SII mai.
- Senza il bias della camera è una stima: accanto, "senza bias".
- R, G e B chiedono il catalogo V50 di ASTAP. Senza, la misura tace e dice "manca il catalogo
  V50"; il passo di ASTAP (primo avvio e Impostazioni) dice a cosa serve.
- Più alto il numero, più buio il cielo.

## 6. Dove si vedono

- **Notti**: per oggetto e filtro, la mediana di ogni misura; un grafico della FWHM lungo la
  notte, frame per frame, con l'altezza dell'oggetto sullo stesso asse del tempo.
- **Archivio**: per produzione (oggetto + ottica + camera), mediana e quartili di FWHM,
  eccentricità, SNR.
- **Statistiche**: brief a parte.
- La scheda dell'oggetto no, per ora (Marco).

## 7. Gli stati

- **Non ancora misurato**: "misura in corso".
- **Non misurabile**: "troppo poche stelle" (nuvole, frame di prova); il numero tace.
- **Forma stimata**: il fit non è riuscito, FWHM ed eccentricità sono stimate; la riga lo dice.
- **Senza scala del cielo** (frame non risolto): FWHM e HFD in px, niente zenit.
- **Senza sito o senza coordinate dell'oggetto**: niente zenit.
- **Mediane**: solo sui frame misurati, con quanti ("su 112 di 120 frame").

## 8. Esempio: "Notte in quota" (Askar FRA400 + ZWO ASI2600MM Pro, 1.94″/px)

Un frame di M 31 in L, oggetto a 35° (massa d'aria 1,74):

- FWHM 3.7″, allo zenit 2.7″; HFD 5.0″, allo zenit 3.6″
- stelle 1240, sature 18
- eccentricità 0,42, rotonde, in AR
- SNR 34
- fondo 812 ADU ± 21, gradiente 6 %, più chiaro verso est
- HFD angoli 2.5 / 2.7 / 2.9 / 2.6 px, centro 2.4 px: tilt 17 %, curvatura 11 %
- SQM 19.2

Valore allo zenit = valore / massa d'aria^0,6 (ESO: il seeing scala con la massa d'aria alla 3/5).

# Cosa vi chiedo

1. Attrezzatura v2 coi difetti del §1, i testi del §3 e i campi del §4.
2. Le misure nella riga di un oggetto delle Notti, col grafico FWHM + altezza.
3. Le misure della produzione nell'Archivio.
4. Il rettangolo del sensore per tilt e curvatura.
5. Gli stati del §7.
6. La luminosità del cielo con la sua banda, "senza bias", "manca il catalogo V50", e la riga sul
   V50 nel passo di ASTAP.

CHANGELOG e DECISIONI come al solito.
