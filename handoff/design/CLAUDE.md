# AstroLog — come si lavora in questo progetto

Leggere all'inizio di ogni conversazione, insieme a `docs/DECISIONI.md`
(cosa si e' deciso e perche') e `docs/CHANGELOG.md` (cosa e' cambiato).

## Dove siamo

Il linguaggio «bento» e' su tutte le pagine. Desktop e telefono sono allineati alle stesse regole (v56, 25 ottobre 2026): vedi DECISIONI v54–v56.42. Il Planner del Sistema solare e degli Eventi e' nella forma nuova (v57) e i transiti hanno la mappa (v58), da approvare; le altre proposte sono in DECISIONI v58, «Prossimi». Pulizia e consegna per Claude Code fatte (v58.5–v58.6, 26/10): `docs/per-claude-code-porting.md`, `COMPONENTI.md` coi due Planner nuovi, `Sistema` aggiornato. Ritocchi dopo l'inventario (v59, 27/10): Luna 25 / 65 / 0°, Ore di posa, Elimina pezzo, Progetti finiti in Da confermare; da approvare. Brief del 6/11 prima del porting (intero in `docs/archivio/brief-porting-v59.md`, fasi in DECISIONI v60): fatte le fasi 1–4, cioe' punto 0 (v60), Dashboard e Meteo (v61), Misure dei frame (v62), Selezione dei frame (v63), Archivio e Riepilogo (v64), Notti (v65), Da confermare e Attrezzatura (v66–v67), Impostazioni e Primo avvio (v68), Statistiche (v69), Telaio e Sistema (v70), tutte da approvare. Fase 5 fatta (7/11): Planner (v71), Progetti (v72), Piano della notte (v73), da approvare. Esportazione per Claude Code fatta (v74, 7/11): pacchetto dell'intero progetto. Da confermare con Claude Code (v68): le quattro vie del cielo del sito e il servizio del cielo. Statistiche (tastiera) e la pastiglia Stanotte sul telefono sono andate in verifica il 7/11. Le 15 voci del controllo della v73 corrette (v75, 7/11; risposta v68 chiusa: servizio del cielo lightpollutionmap.info), da approvare; Secondo controllo, 11 voci corrette (v76, 7/11), da approvare; pacchetto `consegna/astrolog-v76.zip`. Correzioni dal porting della v76, 16 voci (v77, 10/11): telaio a fasce da 700 a 1440, Raffiche, Notti, Riepilogo, MisureFrame, Archivio; da approvare. Collaudo della v77, 3 voci (v78, 10/11): pagine dentro la colonna da 700 a 1440, sito lungo coi puntini, Telaio senza sbordi; da approvare; pacchetto `consegna/astrolog-v78.zip`. Collaudo della v78, 7 voci (v79, 10/11): fonte del sito fuori dalla pillola, striscia da 176 px, Sistema e calendario delle Notti fra 700 e 999, sito lungo in Tutto della notte e Cerca, errori delle icone e di Cerca, icona della scheda; da approvare; pacchetto `consegna/astrolog-v79.zip`. Collaudo e porting della v79, 3 voci (v80, 11/11): errori delle icone di Cerca e Telaio, Archivio come l'app (ricerca sulle sigle, catalogo latino e inglese, senza Sole, Sistema solare e Aggiungi oggetto), Dashboard Il 2026 e Filtri coi tre stati dell'anno e il taglio a sei righe; da approvare; pacchetto `consegna/astrolog-v80.zip`. Dopo la v80 (v81, 11/11): segnaposto SVG come `sc-camel-*` in tutte le tavole, nomi comuni e costellazioni da `catalogo.js` (`ALnome`), stato dei filtri oltre cinque; da approvare; pacchetto `consegna/astrolog-v81.zip`. Tutto IAU e console pulita (v82, 11/11): stelle coi nomi IAU, «Pleiades», le 58 tavole aperte da sole senza errori; da approvare; pacchetto `consegna/astrolog-v82.zip`.

Nel progetto resta solo l'essenziale: niente tavole di prova, catture o caricamenti; nessun codice spento. Le prove si fanno e si cancellano nella stessa conversazione.

## Il metodo

1. **Prima le schermate, poi i mattoni.** Si disegna una schermata intera nel
   linguaggio nuovo; quando convince, se ne ricavano token, telaio e mattoni.
2. **Un brief prima di ogni schermata**, cinque righe: a cosa serve, che dati
   mostra, gli stati difficili, la cosa piu' importante, cosa NON c'e'. Si parte
   dalla pagina vera e dal suo «stati».
3. **Una pagina per schermata**, desktop e telefono; leggera abbastanza da
   lasciarsi catturare.
4. **Il giro di lavoro.** Disegno → catturo desktop e telefono → mi critico da
   solo e correggo → solo allora mostro.
5. **Cambiare la forma, non solo la pelle.**
6. **Varianti quando la direzione non e' chiara**: due o tre, l'utente sceglie.
7. **Controlli a ogni passo**: contrasto in entrambi i modi e coi cinque
   accenti; carte che non escono dalla colonna; bersagli sotto 44 px sul telefono.
8. **Una conversazione per fase.** Ogni decisione nuova si scrive in
   DECISIONI.md nel momento in cui si prende.
9. **Modifiche piccole restano piccole.**

## Regole fisse del linguaggio nuovo

- Carte bento a angoli grandi, un numero protagonista per carta, pillole per
  le scelte, freccia ↗ solo dove si apre un dettaglio.
- Temi: modo chiaro / scuro (poi automatico) × cinque accenti. I colori con un
  significato (esiti, filtri, pianeti, Luna) non cambiano col tema.
- Il colore non e' mai da solo: ogni stato ha anche la parola e un segno.
- Navigazione: barra in alto; "Altro" per le pagine meno usate.
- I dati simulati si dichiarano come tali.
- Italiano, niente sigle di codice a schermo; numeri all'italiana.
- Si risponde in italiano, breve e diretto.
