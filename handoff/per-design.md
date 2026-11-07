# Per Claude Design -- la coda

Ogni richiesta per Design entra qui nel momento in cui nasce, mai solo in chat (Marco, 6/11/2026).
All'avvio di ogni sessione `tools/stato.py` conta le voci e dice se in `handoff/design/` c'e' una
consegna nuova.

**Come si usa.** Marco incolla a Design le voci `[da dare]` e dice «dato»: diventano `[data]`.
Quando la consegna nuova arriva in `handoff/design/`, Claude Code controlla ogni voce `[data]`
sulle tavole: `[fatta vN]` se c'e', di nuovo `[da dare]` con cio' che manca se no. Le voci fatte
escono alla consegna dopo. Il testo lungo di un brief sta nel suo file accanto (`design-v59.md`).

Consegna controllata: v75 (7/11), in `handoff/design/` al posto della v58.6.

## Da dare

Nessuna.

## Date, da controllare alla consegna

Nessuna.

## Fatte

- [fatta v73] Brief v59, punti 0-12 (`design-v59.md`), e la scala di Bortle di ASTAP
  (`design-bortle-astap.md`, `soglie.js` 91).
- [fatta v75] Le quindici voci del controllo della v73: `skPulse` nel foglio; Curvatura in px alla
  ASTAP senza giudizio; Gradiente senza % del fondo; FWHMTilt e FWHMCurvature numeri puri; fonte
  Rousseeuw & Croux 1993 nella Selezione; parole del glossario (ore serene, ore buone, uscite,
  voto, percentuali attaccate); virgola nelle Statistiche; ING accanto al 25 % e niente nome
  accanto allo 0°; SQM a mano da 7 a 23; «propongono di correggerlo»; carta del servizio del
  cielo con lightpollutionmap.info e la chiave; rimando a Impostazioni › Servizi nel Piano della
  notte; errore dell'Archivio dal Telaio; Bortle misurato col buco in giro sui 12 e la frase del
  24/10; testi della Selezione senza NAS; dati d'esempio di raffiche e Luna.
- Resta per il porting, non per Design: le etichette degli assi di Statistiche 446 e 449 usano
  `toFixed(1)` col punto; nell'app i numeri li formatta il frontend con la virgola.
- Risposta a Design (v68): le quattro vie del cielo del sito sono quelle dell'app (Dalle misure =
  `frames`, Bortle a mano = `scale`, SQM a mano = `measured`, Dalla mappa = `service`; `sito.md`
  74-76); il servizio e' quello della mappa della luce artificiale.
