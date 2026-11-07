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

Dal secondo controllo della v75 (7/11), file e righe di `handoff/design/pagine/`:
- [da dare] Selezione dei frame: il Gradiente e' ancora in % (370, criteri 378, 476, formula 591):
  in unita' di rumore come nelle Misure (`grad/100*bg/rum`, MisureFrame 192).
- [da dare] Virgola decimale, i residui: Statistiche assi SQM (446, 449), Eccentricita' (393,
  412), ore con passo 2,5 (358, 365, 375, 525); Progetti 254-255 (eccentricita', SQM); Piano
  della notte 616, 649 (mag); Attrezzatura 427 («1.25″»). Migliaia con lo spazio sottile: Planner
  785 «22 080 oggetti», non «22.080» (glossario).
- [da dare] Dashboard 603: la pillola «sale fino a 64° alle 05:30» non torna con la curva della
  Luna della stessa carta (356, circa 57° a quell'ora): il numero della pillola dalla curva.
- [da dare] Meteo 334, 385: raffiche derivate «fino a 25 km/h» accanto al Vento «buona»; sotto 25
  o il giudizio coerente.
- [da dare] Impostazioni, via «Dalla mappa» senza chiave: SezioneServizi 84 dice che «resta
  spenta», Impostazioni 501, 507 la lascia scegliere. Una delle due.
- [da dare] Attrezzatura, «Unisci a» (188): l'unione sposta frame e il giro riparte
  (`docs/domini/attrezzatura.md` 112): anche qui l'avviso «frame da rielaborare».
- [da dare] Misure dei frame, tessera Curvatura (358): il testo nomina la regola, «HFD oltre il
  75% verso gli angoli meno HFD al centro».
- [da dare] Percorso di ASTAP d'esempio: placeholder `/opt/astap/astap_cli` (Primo avvio 86) e
  predefinito `Programmi/astap/astap_cli` (Primo avvio 138, Impostazioni 349, 430, 590,
  SezioneServizi 103): uno solo, non legato a Windows italiano.
- [da dare] Selezione dei frame: la cartella d'esempio `nas/astro` (275, 444, 455, 634) e «nas/astro
  risponde piano»: un nome generico.
- [da dare] Cerca (componenti/Cerca 84): «Carta del cielo» e' una pagina senza indirizzo; vive nel
  Planner, va tolta dalla ricerca.
- [da dare] Foglio: `alHalo` e `alPulse` (Telaio 126-127) solo nell'helmet del Telaio: nel foglio,
  come `skPulse`.

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
