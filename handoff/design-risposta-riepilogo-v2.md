# Per Claude Design -- Riepilogo v2: backfocus, giudizi e misure aggiornate

Da Claude Code, 18/10/2026. Risposta a "misure dei frame: backfocus e giudizi". Decisioni di
Marco, verificate su 62 frame veri di 7 corredi contro PixInsight; dettaglio in <!-- software-ok -->
`docs/adr/0022-misure-dei-frame.md`. Sostituisce la parte 2 di `design-attrezzatura-v2-e-misure.md`
dove le due dicono cose diverse. Le parole dei giudizi sono proposte: Marco le approva sulla tavola.

## 1. Backfocus dai frame: no

Marco: non si disegna. Da un frame solo il verso (corto o lungo) non è affidabile: la direzione
dell'allungamento si inverte passando il fuoco, le fonti si contraddicono, e gli strumenti seri lo
misurano con curve di fuoco su più frame. Restano tilt e curvatura. Niente frecce per angolo.

## 2. Giudizi: sì, misura per misura

- Marco li accetta. Valgono per **frame, notte (mediana) e produzione (mediana)**.
- **Nessun giudizio d'insieme** dell'oggetto o della notte: pesare misure diverse non ha fonte.
- **Nessuno scarto**: il giudizio informa, non toglie frame.
- Ogni soglia ha una fonte pubblica (o è una scelta di Marco, detta così). Dove manca il dato,
  il giudizio tace e dice perché.

| misura | giudizio | soglie | da dove |
|---|---|---|---|
| **FWHM** (in ″) | **eccellente / buono / nella media / scarso / pessimo** | sotto 2″ / 2-3″ / 3-4″ / 4-5″ / oltre 5″ | consenso dei forum (32 casi) |
| | **al limite del corredo** | sotto F = il maggiore fra 2 × scala e la diffrazione; i bordi sotto F salgono a F | due pixel per stella |
| | **non giudicabile su questo corredo** | quando F supera 3″ (es. 60/300 a 2,59″/px) | |
| **Eccentricità** | **rotonde / — / allungate** | fino a 0,45 / 0,45-0,71 solo il numero / oltre 0,71 | 0,45 dai forum; 0,71 ESO |
| **Fuoco** (HFD) | **fuoco peggiore** | HFD oltre +5 % sulle migliori della stessa notte e filtro | N.I.N.A. |
| **Tilt** | **buono / incerto / non adatto** | fino al 10 % / 10-20 % / oltre 20 % | ASTAP |
| **SNR** | **SNR basso per la notte** | sotto mediana − 2 MAD dei frame della stessa notte, oggetto e filtro | regola del SubframeSelector |
| **Luminosità del cielo** | **come il Bortle del sito / più chiaro del Bortle del sito** | tabella SQM ↔ Bortle; L, senza filtro e a colori | ASTAP (ClearDarkSky) |

SNR e fuoco si giudicano solo sul frame (contro la sua notte), e solo con almeno 10 frame della
stessa notte, oggetto e filtro (N.I.N.A.); sotto, tacciono. Per notte e produzione solo il numero.

**Senza giudizio**: curvatura di campo, gradiente del fondo (Marco), stelle, stelle sature, fondo,
rumore, massa d'aria, direzione dell'allungamento.

**Quando manca un dato**:
- frame senza scala del cielo: niente FWHM in ″, niente giudizio della FWHM;
- corredo senza apertura: F senza la diffrazione (solo 2 × scala);
- notte con meno di 10 frame dello stesso oggetto e filtro: niente giudizi "per la notte";
- luminosità del cielo senza Bortle del sito: niente giudizio.

## 3. Misure aggiornate (cambiano rispetto alla brief di prima)

- **FWHM e HFD sempre in due unità**, ″ e px, una accanto all'altra: "2.2″ · 1.6 px". Il
  giudizio usa i ″, il campionamento i px.
- **FWHM vera** (Marco): circa il 14 % sotto i numeri di PixInsight sulle stelle piccole, perché <!-- software-ok -->
  PixInsight le legge più grandi del vero. Una riga di spiegazione accanto, la prima volta. <!-- software-ok -->
- **Campionamento**, a parte e senza voto: sotto 1,5 px "sottocampionata (grave)", 1,5-2 px
  "sottocampionata", 2-3 px "ideale", oltre 3 px "sovracampionata".
- **SNR** è ora la PSF SNR di PixInsight: un numero grande (anche centinaia o migliaia). Si <!-- software-ok -->
  confronta solo dentro la stessa notte, mai fra camere.
- **Tilt** calcolato come ASTAP: (angolo peggiore − migliore) / HFD mediana, in %.
- **Tilt e curvatura** tacciono sulle camere a colori con stelle sotto ~1,2 superpixel.
- **Stelle**: il numero lo dà ASTAP sul frame intero.
- **Luminosità del cielo (SQM)**, identica ad ASTAP (scarto 0,003 mag):
  - solo frame **L, senza filtro e camere a colori**; R, G, B e filtri stretti mai. Niente
    catalogo V50: togliete "manca il catalogo V50" e la riga sul V50 nel passo di ASTAP;
  - **curva della notte** nelle Notti: un punto per frame, lungo la notte, con l'altezza della
    Luna sullo stesso asse del tempo. Due avvertenze: "nessun frame L o a colori in questa notte"
    quando manca; "il valore cambia anche con la direzione del cielo" accanto alla curva;
  - mono senza bias della camera: il numero con "senza bias"; **camere a colori senza bias:
    niente SQM**, con "serve il bias della camera" e il rimando al campo "Bias (ADU)" in
    Attrezzatura.

## 4. Già nel disegno: confermato

- Direzione dell'allungamento solo da 0,40; "sottocampionata" sotto 2 px.
- Grafico "Frame per frame": due misure, la prima piena e la seconda tratteggiata; "per valore"
  ordina sulla prima.

## 5. Esempio: Askar 103 + ATR2600M, 1,385″/px, OIII

F = max(2 × 1,385; 1,13) = 2,77″.

- FWHM 1.9″ · 1.4 px → **al limite del corredo**, sottocampionata
- FWHM 2.9″ · 2.1 px → **buono**, ideale
- FWHM 3.6″ · 2.6 px → **nella media**
- eccentricità 0,52 → solo il numero; 0,76 → **allungate**, in AR
- tilt 8 % → **buono**

CHANGELOG e DECISIONI come al solito.
