# 0012 -- Il disegno delle pagine viene da Claude Design e si porta alla lettera

**Stato:** accettata, 29/9/2026; in vigore.

## Contesto

Le pagine sono nate prima del loro disegno e sono state vestite dopo, con un foglio di stile
consegnato da Claude Design e mattoni nostri. Marco ridisegna tutte le pagine con Claude Design.

## Decisione

- **Le pagine si rifanno tutte col disegno nuovo.** Finche' non arriva, si lavora sul backend; le
  cose che toccano solo lo schermo aspettano il porting della pagina (Issue #20).
- **Il foglio della consegna si porta alla lettera** e non si corregge da noi: le correzioni
  tornano **alla fonte**, perche' una versione successiva cancellerebbe le nostre.
- **La consegna si verifica punto per punto**: completezza contro il brief, contrasto
  **misurato** coi token e non dichiarato.
- **I token in una casa sola** (colori, spazi, raggi, tipografia); **i mattoni quando due pagine
  vere li chiedono**, mai a tavolino.
- **Niente modalita' a luce rossa.** Resta la regola che ne era la conseguenza: **il colore da
  solo non dice mai niente** (WCAG 2.2, criterio 1.4.1 *Use of Color*, livello A); un segno grafico arriva a 3:1 sul suo fondo
  (1.4.11 *Non-text Contrast*) e un testo vivo a 4,5:1 (1.4.3 *Contrast (Minimum)*), livello AA.
  La scala di Bortle va da freddo a caldo, non da chiaro a scuro: sul fondo scuro il nero puro
  fa 1,07:1 e la classe 1, il cielo migliore, sparirebbe.

## Conseguenze

- Le guardie sul foglio (`tools/controlli_*.py`) giudicano il contenuto della consegna, e un
  numero nostro scritto nel foglio si tiene fermo con una guardia.
- Il frontend non entra nel refactor del backend.
