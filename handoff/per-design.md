# Per Claude Design -- la coda

Ogni richiesta per Design entra qui nel momento in cui nasce, mai solo in chat (Marco, 6/11/2026).
All'avvio di ogni sessione `tools/stato.py` conta le voci e dice se in `handoff/design/` c'e' una
consegna nuova.

**Come si usa.** Marco incolla a Design le voci `[data]` e dice «dato»: diventano `[data]`.
Quando la consegna nuova arriva in `handoff/design/`, Claude Code controlla ogni voce `[data]`
sulle tavole: `[fatta vN]` se c'e', di nuovo `[data]` con cio' che manca se no. Le voci fatte
escono alla consegna dopo. Il testo lungo di un brief sta nel suo file accanto (`design-v59.md`).

Consegna controllata: 3c2a77a4 (v78, 10/11), in `handoff/design/` al posto della v77.

## Da dare

- [da dare] Pillola del sito nella carta della notte, telefono (resto della v78, lo dice Design):
  con un nome lungo la fonte («dalle coordinate nei frame») sparisce, resta solo nel `title`, che
  sul telefono non si vede. La fonte deve restare leggibile a ogni lunghezza del nome.
- [da dare] Striscia delle notti sul desktop stretto (resto della v78): nelle carte da 150 px
  «1 h 50 di banda larga» va a capo su due righe.
- [da dare] Impostazioni, Primo avvio e Sistema fra 700 e 1440 px (resto della v78: Design non le
  ha misurate). Claude Code le misura nell'app e porta qui cio' che sborda.
- [da dare] Notti fra 700 e 999 px (collaudo v78, 10/11): il calendario delle notti
  (`.al-notti__colonna-4`) resta largo 4/12 (244 px a 860) con due terzi vuoti a destra, mentre la
  carta della notte prende la riga intera. Anche il calendario sulla riga intera, o accanto a
  qualcosa.
- [da dare] Sito dal nome lungo, i posti che la v78 non ha toccato (collaudo v78 nell'app con
  «Osservatorio del Monte Generoso, terrazza nord sopra la funicolare»): nella testa di Tutto della
  notte, sotto il titolo, il nome va a capo su due righe a 390 e a 700; in Cerca sul telefono la
  riga «Siti · …» va a capo. Il `?sito=` della tavola non arriva al Riepilogo ne' all'aiuto di Cerca.
- [da dare] Errori delle tavole v78 (collaudo 10/11): `Notti.dc.html` da' «TypeError: Cannot read
  properties of undefined (reading 'q')» in componentDidUpdate dopo Tutto della notte, Esc, Cerca;
  `componenti/Telaio.dc.html` da' quattro `<path> attribute d` coi segnaposto
  `{{ m.altroChev }}`, `{{ m.modeIcon }}`, `{{ vb.az.d }}`, `{{ b.d }}` (la v78 li ha tolti solo
  nell'Archivio); `componenti/Telaio.dc.html?formato=telefono` a 390 resta desktop e scorre di 153 px.

- [da dare] Icona di AstroLog per la scheda del browser (Issue #56, Marco 10/11): oggi l'app
  usa il marchio della testa del telaio (anello e punto, `frontend/src/icona.svg`, colore del
  testo chiaro o scuro). Un'icona disegnata per 16 e 32 px, SVG, che regga sulle schede chiare e
  scure.

## Date, da controllare alla consegna

Nessuna.

## Fatte

Le tre voci date il 10/11 sono fatte nella v78, controllate nell'app e sulle tavole il 10/11 (a
700, 760, 860, 960, 1000, 1100, 1280, 1440 e 390 nessuno scorrimento di lato, nemmeno con la barra
vera): pagine fra 700 e 1000 px, sito dal nome lungo, errori della tavola v77 (lo schermo alto 0
di `Riepilogo stati` non ricontrollato: pagina non ancora portata). I resti sono in «Da dare».

Le 14 voci date il 10/11 sono fatte nella v77 (brief archiviato in
`handoff/design/docs/archivio/brief-porting-v76.md`).

- Resta per il porting, non per Design: le etichette degli assi di Statistiche 446 e 449 usano
  `toFixed(1)` col punto; nell'app i numeri li formatta il frontend con la virgola.
- Risposta a Design (v68): le quattro vie del cielo del sito sono quelle dell'app (Dalle misure =
  `frames`, Bortle a mano = `scale`, SQM a mano = `measured`, Dalla mappa = `service`; `sito.md`
  74-76); il servizio e' quello della mappa della luce artificiale.
