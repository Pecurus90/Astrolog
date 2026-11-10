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

- [da dare] Pagine fra 700 e 1000 px: alla v77 la testa del Telaio ci sta da 700 px, ma il
  contenuto no: sotto i 1000 px alcune carte escono dalla colonna, per esempio la Luna nella
  Dashboard (lo dice Design stesso nella consegna v77). Ogni pagina dentro la colonna a ogni
  larghezza da 700 a 1440, senza scorrimento di lato, come la testa.

## Date, da controllare alla consegna

Nessuna.

## Fatte

Le 14 voci date il 10/11 sono fatte nella v77 (brief archiviato in
`handoff/design/docs/archivio/brief-porting-v76.md`).

- Resta per il porting, non per Design: le etichette degli assi di Statistiche 446 e 449 usano
  `toFixed(1)` col punto; nell'app i numeri li formatta il frontend con la virgola.
- Risposta a Design (v68): le quattro vie del cielo del sito sono quelle dell'app (Dalle misure =
  `frames`, Bortle a mano = `scale`, SQM a mano = `measured`, Dalla mappa = `service`; `sito.md`
  74-76); il servizio e' quello della mappa della luce artificiale.
