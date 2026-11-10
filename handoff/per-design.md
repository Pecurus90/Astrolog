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
- [da dare] Sito dal nome lungo (collaudo v77, 10/11; prova con «Osservatorio del Monte Generoso,
  terrazza nord sopra la funicolare»): la tavola scorre di lato. Telaio desktop: la pastiglia
  Stanotte (`.al-c-telaio__riga-7`, `flex: none`, `nowrap`) allarga la testa a ogni larghezza (a
  1440 pagina 1661/1440). Telaio telefono: il sito sotto il titolo (`.al-c-telaio__riga-12`,
  secondo span, `nowrap`) passa sotto Da confermare e Cerca (414/390). Notti: il sito nella
  striscia (`.al-c-striscia__testo-4`, `nowrap`) sborda a 960 e 760; sul telefono la pillola del
  sito nella carta della notte va a capo su cinque righe. Un nome di sito puo' essere lungo:
  puntini col nome intero nel `title`, come le pillole della testa del Riepilogo alla v77.
- [da dare] Errori della tavola v77 trovati nel collaudo: il Telaio sborda di pochi px da solo a
  1280 (testa 1207/1184), 960, 760 e 700 (il tondo chiaro/scuro `tondo-3` non entra nelle fasce);
  l'Archivio da' in console `<path> attribute d: "{{ v.d }}"` e `"{{ q.ic }}"`; in `Riepilogo
  stati` uno schermo ha `data-screen-label` alto 0 e non si cattura.

- [da dare] Icona di AstroLog per la scheda del browser (Issue #56, Marco 10/11): oggi l'app
  usa il marchio della testa del telaio (anello e punto, `frontend/src/icona.svg`, colore del
  testo chiaro o scuro). Un'icona disegnata per 16 e 32 px, SVG, che regga sulle schede chiare e
  scure.

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
