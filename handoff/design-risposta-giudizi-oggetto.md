# Per Claude Design -- giudizi relativi oltre la notte: le risposte

Da Claude Code, 18/10/2026. Risposta a «giudizi relativi oltre la notte». Decisioni di Marco,
scritte in `docs/adr/0022-misure-dei-frame.md`. Le regole generali restano: un giudizio per
misura, mai d'insieme, mai uno scarto.

## 1. Il frame contro l'oggetto: sì

- **Su quali frame**: quelli dello stesso oggetto e filtro, di tutte le notti. Minimo **10**,
  come per la notte (N.I.N.A.). Sotto, il giudizio tace: «meno di 10 frame dell'oggetto in
  questo filtro».
- **SNR**: «**SNR basso per l'oggetto**» sotto mediana − 2 MAD. È la stessa regola del
  SubframeSelector di PixInsight, che si usa proprio su tutti i frame di un oggetto. <!-- software-ok -->
- **HFD**: «**HFD alta per l'oggetto**» oltre mediana + 2 MAD. Non «fuoco peggiore»: il +5 % di
  N.I.N.A. vale dentro una sessione dopo l'autofocus. Fra notti diverse la HFD cambia col
  seeing, e «fuoco» sarebbe falso.
- **Due giudizi distinti**, «… per la notte» e «… per l'oggetto», uno accanto all'altro, mai
  uniti. Un frame può essere nella norma per la sua notte e basso per l'oggetto: si vedono
  tutti e due.

## 2. HFD contro l'archivio: solo il numero

Nessun giudizio. Accanto alla HFD di una notte o di una produzione: «**mediana del corredo:
2.6 px**» (stesso corredo e stesso filtro, tutti gli oggetti). È un confronto contro la
propria storia: chi ha sempre fuoco cattivo risulterebbe «normale». La qualità assoluta la dà
la FWHM in ″.

## 3. SNR fra oggetti diversi: no

Confermato. La PSF SNR dipende da campo, numero di stelle, filtro e posa. Si giudica solo dentro
la notte e dentro l'oggetto.

## 4. Massa d'aria: «oggetto basso»

- «**oggetto basso**» con massa d'aria sopra **2**, cioè sotto 30° (fonte: AAVSO, che lo usa
  anche come limite predefinito della sua rete di telescopi).
- Solo la parola, nessuno scarto.
- Tace se mancano il sito o le coordinate dell'oggetto.

## 5. «Non giudicabile su questo corredo»

Accanto, la prima volta: «**Limite del corredo 3.9″: due pixel da 1.94″.**» Il numero è
F = il maggiore fra 2 × scala e la diffrazione. «Risolve» non va bene: è il campionamento, non
il potere risolutivo.

## Riassunto per il disegno

| misura | per il frame, nella notte | per il frame, nell'oggetto | per notte e produzione |
|---|---|---|---|
| FWHM | giudizio assoluto in ″ | giudizio assoluto in ″ | giudizio assoluto sulla mediana |
| HFD | «fuoco peggiore» (+5 %) | «HFD alta per l'oggetto» (+2 MAD) | numero + «mediana del corredo» |
| SNR | «SNR basso per la notte» | «SNR basso per l'oggetto» | numero |
| Massa d'aria | «oggetto basso» sopra 2 | — | numero |
