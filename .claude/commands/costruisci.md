---
description: Ricetta costruire - una funzionalita' nuova dal piano al commit. Una revisione, una verifica delle correzioni, un audit che esegue, controlli.
argument-hint: [cosa vuoi]
---

**Lavoro:** $ARGUMENTS

Regole comuni in ADR 0015. Passi:

Metodo di Marco (23/10/2026) per ogni funzionalita' nuova: ricognizione, domande, piano, verifica
indipendente del piano, piano riscritto, poi il codice.

1. **Ricognizione larga**, agenti in parallelo, uno per fonte: codice di oggi e `old/`, documenti
   e decisioni, documentazione del software esterno, convenzioni e metodi standard online (fonte
   accanto a ogni fatto), misura sul vero (copie, mai l'archivio). Cosa esiste e si riusa.
2. **Domande a Marco** solo se la risposta dipende da lui: a scelta multipla, consigliata in cima.
3. **Piano scritto, punto per punto**, con le decisioni di Marco; entra nella mappa del lavoro.
4. **Verifica del piano** da agenti a contesto fresco, modelli diversi: logica (progetta prima
   senza il piano, poi confronta), fattibilita' (esegue e misura), attacco e coerenza con ADR e
   contratti. Ognuno cerca anche convenzioni e metodi standard online: conferma o smentisce.
5. **Piano riscritto** coi rilievi; cio' che e' di Marco torna al punto 2. Ogni punto poi ha:
   Contesto / Obiettivo / Fuori perimetro / Prova finale / `mode` (`logica` = scrivo io;
   `meccanico` = `sviluppatore`) e `surface` se cambia cio' che si vede.
4. **Se `logica`, costruisco io**: test visti rossi, codice, documenti nello stesso diff (guida
   utente, contratto in `docs/domini/`, ADR, schema). File nuovi: `git add -N`.
5. **Workflow `costruisci`** con `args: {task, plan, mode, surface, answers}`. Esiti:
   - `done`: al punto 6.
   - `question`: a Marco come al punto 3, poi si rilancia con la risposta in `answers`.
   - `stopped`, `checks_failing`, `failed`: si dice a Marco cosa resta aperto e dove. Niente commit.
6. **Riassunto**, cinque righe: apre con *cosa funziona ora e prima no*; poi rilievi corretti,
   rifiutati (col perche') e `parked`, elencati una volta.
7. Se `surface`: **Marco guarda la fetta a schermo** prima del commit.
8. **Commit e push automatici**: `git status`, `git add <file uno per uno>`,
   `git commit -m "feat: <una riga ASCII>"`, `git push origin main`.
