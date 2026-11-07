# Per Claude Design -- la coda

Ogni richiesta per Design entra qui nel momento in cui nasce, mai solo in chat (Marco, 6/11/2026).
All'avvio di ogni sessione `tools/stato.py` conta le voci e dice se in `handoff/design/` c'e' una
consegna nuova.

**Come si usa.** Marco incolla a Design le voci `[da dare]` e dice «dato»: diventano `[data]`.
Quando la consegna nuova arriva in `handoff/design/`, Claude Code controlla ogni voce `[data]`
sulle tavole: `[fatta vN]` se c'e', di nuovo `[da dare]` con cio' che manca se no. Le voci fatte
escono alla consegna dopo. Il testo lungo di un brief sta nel suo file accanto (`design-v59.md`).

Consegna controllata: v73 (7/11, scaricata dal progetto di Design, non ancora in `handoff/design/`:
entra con la correzione di queste voci).

## Da dare

Dal 7/11 (voci nate prima della v73, non ancora date):
- [da dare] Foglio (`astrolog.css`): `@keyframes skPulse` vive solo negli helmet; il foglio lo nomina
  (righe 866, 931, 1398, 2059, 2209, 2288) ma non lo definisce. Portato alla lettera, lo scheletro e
  i tondi di MisureFrame e Attrezzatura restano fermi: serve la regola nel foglio.
- [da dare] Misure dei frame, tessera Curvatura (Marco, 7/11): non piu' una % ma l'aberrazione
  fuori asse di ASTAP, in px (e in ″ con la scala): HFD delle stelle oltre il 75% verso gli
  angoli meno HFD del centro, col segno. Senza giudizio: ASTAP non da' soglie. Oggi in %
  (MisureFrame 176, 193, 340, 358). La tessera Tilt resta in % col giudizio 10 / 20 %.
- [da dare] Misure dei frame, tessera Gradiente (Marco, 7/11): niente % del fondo (MisureFrame 243,
  357), nessuna fonte pubblica la definisce. Restano le unita' di rumore e il lato chiaro.
- [da dare] Misure dei frame, dettaglio: FWHMTilt e FWHMCurvature di Image Analysis sono rapporti
  senza unita' (ImageAnalysis eq. 26-27), non px: si scrivono come numeri puri (oggi «Tilt ·
  curvatura» in px, MisureFrame 358).
- [da dare] Impostazioni › Selezione dei frame: accanto alla partenza una fonte pubblica, non un
  ADR interno all'app (oggi «ADR 0039», `soglie.js` 148-151): «Rousseeuw & Croux 1993» per i 2,5
  rispetto al gruppo, e cosi' per ogni soglia della sezione.

Dal controllo della v73 (7/11):
- [da dare] Parole che il glossario vieta, a schermo: «ore serene» (Notti 208, anche il testo
  corto), «ore buone» (Meteo stati 39, 45): sono «ore di posa» o «ore visibili»; «uscite» per le
  notti (Statistiche 481, 503, 546): «notti»; «voto» (Meteo 188): «verdetto»; percentuali con lo
  spazio («96 %», «fino al 25 %»: Dashboard 342-344, 360, 596; CalendarioNotti 58; Striscia 55):
  attaccate, «96%» (glossario, Marco 19/10; il brief v59 sbagliava a scrivere «25 %»).
- [da dare] Virgola decimale anche in Statistiche: `RW` fa `String(v)` e i `toFixed` arrivano col
  punto (Statistiche 416, 443, 450, 471-472, 503, 512, 524, 533). Passare da `AL.virg`.
- [da dare] Impostazioni, Luna: accanto al 25 % la fonte e' ING come per il 65 («regola di ING:
  buio sotto 0,25»), non «regola diffusa fra chi riprende» (Impostazioni 605, `soglie.js` 17; ADR
  0034 riga 31 la cita per entrambi). Accanto allo 0° niente nome di persona («Marco, 24/10/2026»,
  Impostazioni 607, `soglie.js` 19): «dall'orizzonte, quando sorge».
- [da dare] Impostazioni, via «SQM a mano»: accetta da 7 a 23 come l'app («Un numero da 7 a 23»),
  non da 16 a 22,5 (Impostazioni 497, 510; `docs/domini/sito.md` 77): un centro citta' a 15,x oggi
  la pagina lo rifiuta e l'app lo prende.
- [da dare] Impostazioni, via «Dalla mappa»: «le misure dei frame, quando bastano, propongono di
  correggerlo», non «lo correggono» (Impostazioni 512): l'app propone, l'utente sceglie («Usa»).
- [da dare] Servizi, carta «Servizio del cielo» (SezioneServizi 84): il link oggi e' vuoto. Il
  servizio e' lightpollutionmap.info (World Atlas della luce artificiale): nome e link, e come si
  ha la chiave (gratuita, chiesta con una email all'autore, 500 richieste al giorno).
- [da dare] Piano della notte, Ricerca senza chiavi: «Serve la chiave AAVSO/TNS in Impostazioni ›
  Servizi», con il rimando cliccabile (Piano della notte 654).
- [da dare] Archivio: manca lo stato di errore della pagina con «AstroLog non risponde, riprova»
  (c'e' in Notti, Meteo, Riepilogo); restano stili fissi da portare in classi del foglio (Archivio
  22, 34, 52, 56-58, 68-75).
- [da dare] Statistiche, Bortle misurato: il buco fra i mesi si conta in giro sui 12 (dicembre
  tocca gennaio, `sito.md` 222-223), oggi in linea (Statistiche 454). Con poche misure la frase
  e' quella decisa (Marco 24/10, `sito.md` 245-246): «Servono notti in almeno 4 mesi, senza buchi
  di oltre 3: finora {n} notti in {m} mesi.» (oggi «Ancora poche misure...», Statistiche 455).
- [da dare] Selezione dei frame: testi che danno per scontato il NAS («sul NAS e' in sola
  lettura», «Erano sul NAS», «sono sul NAS, dove il cestino non c'e'»: Selezione 446, 455, 652):
  «la cartella», «il disco» o il suo nome. Primo avvio 86: il percorso di esempio di ASTAP senza
  `\` di Windows, o uno per sistema.
- [da dare] Dati d'esempio incoerenti: Dashboard 364 raffiche 28 km/h con verdetto «buona» (la
  soglia e' 25); Dashboard 603 la Luna «sale fino a 68° alle 07:30», fuori dal buio 20:48-05:48.

## Date, da controllare alla consegna

- [data] Brief v59, punto 12, Telaio e Sistema. [fatta v73]
- [data] Brief v59, punti 0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11 [fatti v73], salvo le voci «Dal
  controllo della v73» qui sopra.
- [data] Brief v59, punto 4, Archivio e Riepilogo: Riepilogo fatto v73; Archivio sopra.
- [data] La scala di Bortle di ASTAP (`design-bortle-astap.md`, 23/10): fatta v73 (`soglie.js` 91).

## Fatte

- Selezione dei frame: «esclusi» e non «saltati» per i file della scansione (v73: «saltato» resta
  solo per i passi del Primo avvio, come il glossario).
- Selezione dei frame: eccentricita' di partenza 2,5 rispetto al setup, spenta come prima (v73).
- Risposta a Design (v68, porting 96): le quattro vie del cielo del sito sono quelle dell'app
  (Dalle misure = `frames`, Bortle a mano = `scale`, SQM a mano = `measured`, Dalla mappa =
  `service`; `sito.md` 74-76); il servizio e' quello della mappa della luce artificiale.
