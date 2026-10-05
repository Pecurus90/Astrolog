---
description: Ricetta costruire - una funzionalita' nuova dal piano al commit. Una revisione, una verifica delle correzioni, un audit che esegue, controlli.
argument-hint: [cosa vuoi]
---

**Lavoro:** $ARGUMENTS

Regole comuni in ADR 0015. Passi:

1. **Ricognizione.** Grep, o `esploratore` se serve leggere molto. Cosa esiste e si riusa.
2. **Piano in cinque righe**: Contesto / Obiettivo / Fuori perimetro / Prova finale / `mode`
   (`logica` = scrivo io; `meccanico` = `sviluppatore`) e `surface` se cambia cio' che si vede.
3. **Domande a Marco** solo se la risposta dipende da lui: a scelta multipla, consigliata in cima.
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
