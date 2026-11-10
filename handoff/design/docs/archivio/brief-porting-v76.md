# Brief per Claude Design: correzioni alla v76 (AstroLog, 10/11/2026)

Da Claude Code, durante il porting della consegna v76 (Notti, Tutto della notte, finestra dell'oggetto, telaio). Chiuso nella v77: voce per voce in `docs/per-claude-code-porting.md`, sezione v77, e in DECISIONI v77.

## Telaio (componenti/Telaio.dc.html)

1. Finestre strette. La cornice ha min-width: 1440, ma fra 700 e 1440 px la testa non ci sta (portatili da 1280 e 1366 px, finestra non a tutto schermo). A 1280 px l'ingranaggio esce di 53 px. Marco (10/11) chiede versioni scalate della testa, senza scorrimento di lato: per esempio Cerca solo con la lente, pillole e margini più stretti. Una versione per ogni fascia, fino ai 700 px, dove parte il telefono.
2. Telefono, Da confermare nella testa senza conto: largo 42 px (padding 0 12px, icona 18), sotto i 44 px dei bersagli del telefono.
3. Helmet (riga 10): alPulse e alHalo sono già nel foglio (astrolog.css 553-554) ma restano anche nell'helmet. Una casa sola.

## Meteo

4. La carta del Vento dice «raffiche fino a 13 km/h» (picco, righe 276, 284, 291 e i giorni 305-318); la carta delle Raffiche mostra un massimo derivato (vento × 1,5, riga 334), 20 km/h nella prima notte. Un numero solo: il picco del Vento dalla stessa serie delle Raffiche.

## Notti

5. Fonte del sito (riga 231): serve un terzo caso, il sito scelto rispondendo in Da confermare, «· dalla tua risposta in Da confermare» (Marco, 7/11). Oggi la tavola decide la fonte dal nome del sito (/casa/i). La fonte la manda l'app, con tre valori possibili.
6. Cielo (riga 205, SZ): lo storico del meteo non ha l'aerosol, quindi ogni notte passata dice «· senza aerosol» accanto alle ore di posa. Nella tavola SZ è vuoto: va mostrato. Va anche detto se e dove ci sta nelle righe di «A confronto»: lì la riga del cielo si sovrapponeva.
7. La parola accanto al numero grande (riga 221, bigL): dice «ore» anche coi minuti («10 min ore») e ripete l'unità con le ore («4 h 18 ore»). Marco (10/11) vuole «integrazione», come nella finestra della notte e dell'oggetto.

## Tutto della notte / Riepilogo / MisureFrame

8. Riepilogo (righe 97-98, tabella L) e FinestraRiepilogo (riga 36, D): misure del formato inline. Come l'Archivio alla v75: radice con data-formato, misure in classi del foglio, inline solo i dati.
9. Riepilogo, frecce ‹ › spente (riga 149): lo stato spento è solo l'opacità .35. Va detto anche col segno (aria-disabled, il cursore, nessuna azione), come «Carica altre» nelle Notti.
10. MisureFrame, frame che non si misura (di un altro programma, riscritto, rotto o in .fz): né nei grafici né nel frame, senza parole; conta solo in «su 112 di 120» (Marco, 8/11). «Senza scala del cielo» diverso fra MisureFrame (riga 361) e Misure dei frame (riga 162): ne serve uno solo.
11. MisureFrame, giudizi che l'app non dà: pillole della FWHM (3/4/5″, «consenso dei forum»), eccentricità 0,45/0,71, «oggetto basso» a massa d'aria 2. I numeri restano. I giudizi del gruppo e del setup (SNR basso, fuoco, HFD alta, «stelle allungate» del Setup) arrivano più avanti: tolti o segnati «dopo».

## Archivio / finestra dell'oggetto

12. Elenco (DECISIONI riga 1634): il tocco sulla riga deve aprire la finestra dell'oggetto, ma la tabella non ha una classe che stenda il comando su tutta la riga, come as-carta-oggetto__apri sulla carta. Oggi si apre solo dal nome.
13. Fuori catalogo (Riepilogo riga 157): «si muove nel cielo» non vale per ogni oggetto senza catalogo.
14. Produzioni (dati.js): la linguetta deve dire ottica, camera e ore, non anno e sito.
15. Riepilogo, stati di caricamento, errore e non trovato: manca la x per chiudere; sul telefono la finestra va a pagina intera.
16. Testa del telefono con due siti dai nomi lunghi: pillole e x vanno a capo.
