# Per Claude Design -- Dashboard: le aggiunte

Decise da Marco il 12 ottobre 2026, dopo il confronto con gli strumenti che gli astrofotografi
usano (Astrospheric, Clear Outside, Target Scheduler di N.I.N.A., Voyager, Telescopius).
**La disposizione della pagina non cambia.** La tabella dei progetti prende colonne. Valgono per
desktop, telefono, stati e Atlante. Le aggiunte del Meteo (visibilita', carte uscite, il conto
delle carte) stanno ora nel contratto `docs/domini/meteo.md`; la regola della Luna del calendario
in `docs/domini/effemeridi.md`.

Un testo segnato *(provvisorio)* resta col filo tratteggiato: Marco lo conferma dopo averlo visto.

## 1. Dashboard

1. **Telefono, le sei carte del meteo.** A quattro per riga lasciano due posti vuoti: vanno a tre
   per riga, due file piene.

2. **La tabella dei progetti prende colonne.** Oggi: oggetto, ore, verso l'obiettivo, sopra 30°
   stanotte. Diventa:

   | colonna | esempio | cosa dice |
   |---|---|---|
   | oggetto | IC 1396 · Banda stretta | come oggi |
   | ore | 14 h 20 di 20 h | come oggi, con la barra |
   | per filtro | Hα 6 h 10 · OIII 5 h · SII 3 h 10 | le ore di ogni filtro, una barretta per filtro *(provvisorio)* |
   | utili stanotte | 5 ore | le ore di buio sereno in cui l'oggetto sta sopra 30°; prende il posto di «sopra 30° stanotte» *(provvisorio)* |
   | transito | 01:20 | l'ora in cui passa al meridiano *(provvisorio)* |
   | dalla Luna | 74° | la distanza dalla Luna stanotte, solo il numero: nessun semaforo *(provvisorio)* |
   | finestra | ancora 6 settimane | per quanto resta riprendibile *(provvisorio)* |

   Per un mosaico, sotto «per filtro» una riga in piu': *pannello 1: 6 h · pannello 2: 5 h 45*
   *(provvisorio)*.
   Un progetto che stanotte non ha ore utili dice «nessuna» in quella colonna, senza colore
   d'allarme: non e' un guasto.

3. **L'ordine della tabella.** Accanto al titolo un segmentato a due voci: *per ore* (oggi) e
   *meglio stanotte* *(provvisorio)*, che mette in cima chi ha piu' ore utili stanotte. Il titolo
   «progetti in corso · per ore» diventa «progetti in corso».

4. **Telefono.** La riga di riepilogo «Progetti in corso» dice il migliore di stanotte invece del
   piu' avanti: *IC 1396 · 5 ore utili stanotte* *(provvisorio)*. La tabella intera sta nella
   pagina Progetti, come oggi.

5. **L'ultima notte, in «da riprendere».** Sotto «4 h 12 su IC 1396, 126 frame» una riga:
   *FWHM media 2,8″* *(provvisorio)*. L'app la mostrera' quando misurera' i frame.

## 2. Cio' che non cambia

La volta, il dettaglio della Luna, le sei carte del meteo con i loro grafici, le prossime tre
notti, l'anno. I testi della Dashboard stanno in `frontend/src/i18n/it-dashboard.ts`.

## 3. Cosa dire a parte

- se le sette colonne della tabella dei progetti reggono a 1440 e a 1024, e cosa hai fatto dove
  non reggono;
- ogni testo che non regge nella forma: non riscriverlo, segnalalo.
