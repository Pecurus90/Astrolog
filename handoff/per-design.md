# Per Claude Design -- la coda

Ogni richiesta per Design entra qui nel momento in cui nasce, mai solo in chat (Marco, 6/11/2026).
All'avvio di ogni sessione `tools/stato.py` conta le voci e dice se in `handoff/design/` c'e' una
consegna nuova.

**Come si usa.** Marco incolla a Design le voci `[da dare]` e dice «dato»: diventano `[data]`.
Quando la consegna nuova arriva in `handoff/design/`, Claude Code controlla ogni voce `[data]`
sulle tavole: `[fatta vN]` se c'e', di nuovo `[da dare]` con cio' che manca se no. Le voci fatte
escono alla consegna dopo. Il testo lungo di un brief sta nel suo file accanto (`design-v59.md`).

Consegna controllata: b19a233a

## Da dare

- [da dare] Foglio (`astrolog.css`): `@keyframes skPulse` vive solo nell'helmet di
  `componenti/Scheletro.dc.html`; il foglio lo nomina (righe 864, 929, 1378, 2037, 2187, 2266) ma
  non lo definisce. Portato alla lettera, lo scheletro e i tondi di MisureFrame e Attrezzatura
  restano fermi: serve la regola nel foglio.
- [da dare] Misure dei frame, tessera Curvatura (Marco, 7/11): non piu' una % ma l'aberrazione
  fuori asse di ASTAP, in px (e in ″ con la scala): HFD delle stelle oltre il 75% verso gli
  angoli meno HFD del centro. Senza giudizio: ASTAP non da' soglie. La tessera Tilt resta in %
  col giudizio 10 / 20 %.
- [da dare] Misure dei frame, tessera Gradiente (Marco, 7/11): niente % del fondo, nessuna fonte
  pubblica la definisce. Restano le unita' di rumore e il lato chiaro come angolo sul cielo.
- [da dare] Misure dei frame, dettaglio: FWHMTilt e FWHMCurvature di Image Analysis sono rapporti
  senza unita' (ImageAnalysis eq. 26-27), non px: si scrivono come numeri puri.

- [da dare] Selezione dei frame (v63), parole: i file che la scansione non legge si chiamano
  «esclusi», non «saltati»: e' gia' la parola del glossario, che vieta «saltati» e «scartati» per
  loro (Marco, 6/11). La Selezione tiene «Scarta / Tieni / da scartare / scartate» (approvate).
- [da dare] Impostazioni, sezione «Selezione dei frame» (v63): la fonte accanto alla partenza e'
  una fonte pubblica, non un numero di ADR interno all'app: «Rousseeuw & Croux 1993» per i 2,5
  rispetto al gruppo, e cosi' per ogni soglia della sezione.
- [da dare] Selezione dei frame (v63), eccentricita': il brief 2.2 cambia solo il numero iniziale
  (2,5 rispetto al setup al posto di 0,6). Se prima era accesa di partenza resta accesa; spegnerla
  cambia cio' che l'app scarta, e quella e' una scelta di Marco.

## Date, da controllare alla consegna

- [data] Brief v59, punto 0, per tutte le pagine (`design-v59.md`, 6/11).
- [data] Brief v59, punto 1, Misure dei frame. Design: fatto in v62, con «frame non confrontabili»
  (camera, guadagno, tempo di posa) e la virgola in una casa sola (`tema.js`).
- [data] Brief v59, punto 2, Selezione dei frame. Design: fatto in v63 (casa delle regole: A).
- [data] Brief v59, punto 3, Da confermare.
- [data] Brief v59, punto 4, Archivio e Riepilogo.
- [data] Brief v59, punto 5, Notti.
- [data] Brief v59, punto 6, Dashboard. Design: fatto in v61.
- [data] Brief v59, punto 7, Meteo. Design: fatto in v61.
- [data] Brief v59, punto 8, Planner, Piano della notte, Progetti.
- [data] Brief v59, punto 9, Impostazioni e Primo avvio.
- [data] Brief v59, punto 10, Attrezzatura.
- [data] Brief v59, punto 11, Statistiche.
- [data] Brief v59, punto 12, Telaio e Sistema.
- [data] La scala di Bortle di ASTAP nel commento del foglio (`design-bortle-astap.md`, 23/10).

## Fatte

Nessuna ancora: l'ultima consegna nel repo e' la v58.6 (26/10), che il brief v59 ha controllato.
