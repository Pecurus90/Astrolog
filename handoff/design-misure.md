# Per Claude Design -- le misure dei frame

Da Claude Code, 18/10/2026. Decisione in `docs/adr/0022-misure-dei-frame.md`. L'app non ha
ancora queste misure, salvo HFD e stelle: arrivano col backend, dopo il disegno. Le parole dei
nomi sono proposte: Marco le approva sulla tavola.

## 1. Cosa misura l'app, per ogni frame

L'app misura e basta: **nessun voto, nessuno scarto, nessun "frame buono/cattivo"** (Marco). Una
misura si mostra col suo numero; l'unico confronto è con altri numeri.

| misura | unità a schermo | nota |
|---|---|---|
| FWHM | " (secondi d'arco) | senza scala del cielo resta in px e non si confronta fra corredi |
| FWHM allo zenit | " | accanto alla FWHM; come se l'oggetto fosse allo zenit |
| HFD | " | anche allo zenit |
| Stelle | numero | |
| Eccentricità | da 0 a 1 | 0 = stelle rotonde |
| Direzione dell'allungamento | "in AR" / "in Dec" | accanto all'eccentricità |
| SNR | numero | |
| Fondo cielo | ADU, col rumore | confrontabile solo con la stessa camera, guadagno e posa: la tavola lo dice |
| Gradiente del fondo | % e lato ("più chiaro verso est") | |
| Tilt | % | differenza fra l'angolo peggiore e il migliore, sulla HFD al centro |
| Curvatura di campo | % | media degli angoli contro il centro |
| Stelle sature | numero | |

Luminosità del cielo (mag/arcsec², come un SQM): in valutazione, non disegnatela ancora.

Tilt e curvatura si possono mostrare anche come i cinque numeri (quattro angoli e centro) su un
rettangolo del sensore.

## 2. Dove si vedono

- **Notti**: per ogni oggetto e filtro della notte, la mediana di ogni misura. Più un grafico
  della FWHM lungo la notte, frame per frame, con l'altezza dell'oggetto sullo stesso asse del
  tempo.
- **Archivio**: per ogni produzione (oggetto + ottica + camera), mediana e intervallo
  (quartili) di FWHM, eccentricità, SNR.
- **Statistiche**: brief a parte, più avanti.
- La scheda dell'oggetto no, per ora (Marco).

## 3. Gli stati

- **Non ancora misurato**: il frame aspetta la misura. "misura in corso" come per la scansione.
- **Non misurabile**: troppe poche stelle (nuvole, frame di prova). Il numero tace e la riga
  dice perché.
- **Senza scala del cielo** (frame non risolto): FWHM e HFD in px, niente valori allo zenit.
- **Senza sito o senza coordinate dell'oggetto**: niente valori allo zenit.
- **Mediana**: solo sui frame misurati; accanto, quanti ("su 112 di 120 frame").

## 4. Esempio: "Notte in quota" (Askar FRA400 + ZWO ASI2600MM Pro, 1,94 "/px)

Un frame di M 31 in L, oggetto a 35° (massa d'aria 1,74):

- FWHM 3,7", allo zenit 2,7"
- HFD 5,0", allo zenit 3,6"
- stelle 1240, sature 18
- eccentricità 0,42, in AR
- SNR 34
- fondo 812 ADU ± 21, gradiente 6 %, più chiaro verso est
- HFD angoli 2,5 / 2,7 / 2,9 / 2,6 px, centro 2,4 px: tilt 17 %, curvatura 11 %

Valore allo zenit = valore / massa d'aria^0,6 (ESO: il seeing scala con la massa d'aria alla
3/5).

## 5. Cosa vi chiedo

1. Le misure nella riga di un oggetto delle Notti, e il grafico FWHM + altezza.
2. Le misure della produzione nell'Archivio.
3. Il rettangolo del sensore per tilt e curvatura.
4. Gli stati del §3.

CHANGELOG e DECISIONI come al solito.
