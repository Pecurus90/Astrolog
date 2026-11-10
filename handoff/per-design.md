# Per Claude Design -- la coda

Ogni richiesta per Design entra qui nel momento in cui nasce, mai solo in chat (Marco, 6/11/2026).
All'avvio di ogni sessione `tools/stato.py` conta le voci e dice se in `handoff/design/` c'e' una
consegna nuova.

**Come si usa.** Marco incolla a Design le voci `[da dare]` e dice «dato»: diventano `[data]`.
Quando la consegna nuova arriva in `handoff/design/`, Claude Code controlla ogni voce `[data]`
sulle tavole: `[fatta vN]` se c'e', di nuovo `[da dare]` con cio' che manca se no. Le voci fatte
escono alla consegna dopo. Il testo lungo di un brief sta nel suo file accanto (`design-v59.md`).

Consegna controllata: 94e305ae (v76, 7/11), in `handoff/design/` al posto della v75.

## Da dare

Dal controllo della v76 (7/11), file e righe di `handoff/design/pagine/`:
- [da dare] Meteo: la carta del Vento dice «raffiche fino a 13 km/h» (`picco`, 276, 284, 291 e i
  giorni 305-318), la carta delle Raffiche ne mostra il massimo derivato (vento x 1,5, 334): nella
  prima notte 20 km/h. Un numero solo: il `picco` del Vento dalla stessa serie delle Raffiche.
- [da dare] Telaio, helmet (10): `alPulse` e `alHalo` ora sono nel foglio (astrolog.css 553-554)
  ma restano anche nell'helmet: via dall'helmet, una casa sola.

Dal porting delle Notti (passo 33, 7/11):
- [da dare] Notti, fonte del sito (231): un terzo caso, il sito scelto rispondendo in Da
  confermare: «· dalla tua risposta in Da confermare» (Marco, 7/11). Oggi la tavola decide la fonte
  dal nome del sito (`/casa/i`): la fonte la manda l'app, tre valori.
- [da dare] Notti, cielo (205, `SZ`): lo storico del meteo non ha l'aerosol, quindi ogni notte
  passata dice «· senza aerosol» accanto alle ore di posa (ADR 0034, DECISIONI v60). Nella tavola `SZ`
  e' vuoto: mostrarlo. L'app oggi lo scrive solo nella protagonista: nelle righe di «A confronto»
  la riga del cielo si sovrapponeva; dire se e dove ci sta nelle righe.

Dal porting di «Tutto della notte» (passo 33, 8/11), `componenti/`:
- [da dare] Riepilogo (97-98, tabella `L`) e FinestraRiepilogo (36, `D`): le misure del formato
  (titolo 44/30, ore 64/48, padding 28/20, gap 16/12, bersagli 34/44, velo e pannello) sono
  inline. Come l'Archivio alla v75: radice con `data-formato`, le misure in classi del foglio;
  inline solo i dati.
- [da dare] Riepilogo, frecce ‹ › spente (149): solo opacita' .35. Dire lo stato anche col
  segno (`aria-disabled`, cursore, nessuna azione), come «Carica altre» nelle Notti.
- [da dare] MisureFrame: il frame che non si misura (altro programma, riscritto, rotto, `.fz`)
  non compare ne' nei grafici ne' nel frame, senza parole; conta solo in «su 112 di 120» (Marco,
  8/11). Testo «Senza scala del cielo» diverso fra MisureFrame 361 e Misure dei frame 162: uno.
- [da dare] MisureFrame, giudizi che l'app non da' (principio 1, ADR 0039): pillole della FWHM
  (3/4/5″, «consenso dei forum»: nessuna convenzione pubblica), eccentricita' 0,45/0,71, oggetto
  basso a massa d'aria 2. Restano i numeri; i giudizi relativi al gruppo e al setup (SNR basso,
  fuoco, HFD alta, «stelle allungate» del Setup) arrivano al passo 40. Togliere dalla tavola o
  segnarli «dopo».
- [da dare] Archivio, elenco (DECISIONI 1634): il tocco sulla riga apre la finestra dell'oggetto,
  ma la tabella non ha una classe che stenda il comando sulla riga, come `as-carta-oggetto__apri`
  sulla carta; oggi apre il nome. Fuori catalogo (Riepilogo 157): «si muove nel cielo» non vale
  per ogni oggetto senza catalogo, toglierlo. Produzioni (dati.js): la linguetta e' ottica,
  camera e ore, non anno e sito. Riepilogo, stati caricamento, errore e non trovato: nessuna x,
  e sul telefono la finestra e' a pagina intera; testa del telefono con due siti dai nomi lunghi:
  pillole e x vanno a capo.
- [da dare] Notti, la parola accanto al numero grande (221, `bigL`): «ore» anche coi minuti
  («10 min ore», `AL.ore` in tema.js 51) e doppia con le ore («4 h 18 ore»). Marco 10/11:
  «integrazione», come la finestra della notte e dell'oggetto.

Dal porting del telaio (passo 33, 10/11), `componenti/Telaio.dc.html`:
- [da dare] Telaio, finestre strette: la cornice ha min-width 1440, ma fra 700 e 1440 px
  (portatili 1280 e 1366, finestra non a tutto schermo) la testa non ci sta: a 1280 l'ingranaggio
  esce di 53 px. Marco 10/11: versioni scalate della testa, senza scorrimento di lato (per
  esempio Cerca solo con la lente, pillole e margini piu' stretti), una per fascia fino a 700.
- [da dare] Telaio telefono, Da confermare nella testa senza conto: largo 42 px (padding 0 12px,
  icona 18), sotto i 44 dei bersagli del telefono.

## Date, da controllare alla consegna

Nessuna.

## Fatte

- [fatta v76] Le undici voci del secondo controllo della v75: Gradiente della Selezione in unita'
  di rumore; virgola e spazio sottile negli ultimi numeri (Statistiche, Progetti, Piano della
  notte, Attrezzatura, Planner «22 080»); pillola della Luna dalla curva; raffiche sotto 25 nella
  notte buona; «Dalla mappa» senza chiave si sceglie ma non da' cielo, detto in SezioneServizi;
  «Unisci a» con frame da rielaborare; Curvatura con la regola del 75%; ASTAP
  `/opt/astap/astap_cli` ovunque; cartella d'esempio `Condivisa/Astro`; Cerca senza Carta del
  cielo; `alPulse` e `alHalo` nel foglio.

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
