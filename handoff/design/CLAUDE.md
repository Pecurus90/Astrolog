# AstroLog — come si lavora in questo progetto

Leggere all'inizio di ogni conversazione, insieme a `docs/DECISIONI.md`
(cosa si e' deciso e perche') e `docs/CHANGELOG.md` (cosa e' cambiato).

## Dove siamo

Il linguaggio «bento» e' su tutte le pagine. Desktop e telefono sono allineati alle stesse regole (v56, 25 ottobre 2026): vedi DECISIONI v54–v56.42. Il Planner del Sistema solare e degli Eventi e' nella forma nuova (v57) e i transiti hanno la mappa (v58), da approvare; le altre proposte sono in DECISIONI v58, «Prossimi». Pulizia e consegna per Claude Code fatte (v58.5–v58.6, 26/10): `docs/per-claude-code-porting.md`, `COMPONENTI.md` coi due Planner nuovi, `Sistema` aggiornato. Prossimo: il porting di Claude Code.

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
