# Per Claude Design -- la coda

Ogni richiesta per Design entra qui nel momento in cui nasce, mai solo in chat (Marco, 6/11/2026).
All'avvio di ogni sessione `tools/stato.py` conta le voci e dice se in `handoff/design/` c'e' una
consegna nuova.

**Come si usa.** Marco incolla a Design le voci `[data]` e dice «dato»: diventano `[data]`.
Quando la consegna nuova arriva in `handoff/design/`, Claude Code controlla ogni voce `[data]`
sulle tavole: `[fatta vN]` se c'e', di nuovo `[data]` con cio' che manca se no. Le voci fatte
escono alla consegna dopo. Il testo lungo di un brief sta nel suo file accanto (`design-v59.md`).

Consegna controllata: 16f37b9a (v77, 10/11), in `handoff/design/` al posto della v76.

## Da dare

- [da dare] Pillola del sito nella carta della notte, telefono (resto della v78, lo dice Design):
  con un nome lungo la fonte («dalle coordinate nei frame») sparisce, resta solo nel `title`, che
  sul telefono non si vede. La fonte deve restare leggibile a ogni lunghezza del nome.
- [da dare] Striscia delle notti sul desktop stretto (resto della v78): nelle carte da 150 px
  «1 h 50 di banda larga» va a capo su due righe.
- [da dare] Impostazioni, Primo avvio e Sistema fra 700 e 1440 px (resto della v78: Design non le
  ha misurate). Claude Code le misura nell'app e porta qui cio' che sborda.

- [da dare] Icona di AstroLog per la scheda del browser (Issue #56, Marco 10/11): oggi l'app
  usa il marchio della testa del telaio (anello e punto, `frontend/src/icona.svg`, colore del
  testo chiaro o scuro). Un'icona disegnata per 16 e 32 px, SVG, che regga sulle schede chiare e
  scure.

## Date, da controllare alla consegna

Arrivata la v78 (3c2a77a4, 10/11) con le tre voci date: da controllare sulle tavole.

- [data] Pagine fra 700 e 1000 px: ogni pagina dentro la colonna da 700 a 1440, senza
  scorrimento di lato (v78: carte una sotto l'altra sotto 1000, `data-col` su Carta).
- [data] Sito dal nome lungo: puntini col nome intero nel `title` nella pastiglia Stanotte, nel
  sito sotto il titolo del telefono, nella striscia e nella pillola della notte (v78, prova con
  `?sito=`).
- [data] Errori della tavola v77: Telaio che sborda di pochi px a 1280, 960, 760 e 700; Archivio
  coi `<path>` `{{ v.d }}` e `{{ q.ic }}` in console; in `Riepilogo stati` uno schermo alto 0
  (Design ne ha trovati due con la stessa etichetta, non uno alto 0: da ricontrollare).

## Fatte

Le 14 voci date il 10/11 sono fatte nella v77 (brief archiviato in
`handoff/design/docs/archivio/brief-porting-v76.md`).

- Resta per il porting, non per Design: le etichette degli assi di Statistiche 446 e 449 usano
  `toFixed(1)` col punto; nell'app i numeri li formatta il frontend con la virgola.
- Risposta a Design (v68): le quattro vie del cielo del sito sono quelle dell'app (Dalle misure =
  `frames`, Bortle a mano = `scale`, SQM a mano = `measured`, Dalla mappa = `service`; `sito.md`
  74-76); il servizio e' quello della mappa della luce artificiale.
