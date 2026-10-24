---
description: Ricetta costruire - una funzionalita' nuova dal piano al commit. Una revisione, una verifica delle correzioni, un audit che esegue, controlli.
argument-hint: [cosa vuoi]
---

**Lavoro:** $ARGUMENTS

Regole comuni in ADR 0015 e ADR 0040. Passi:

1. **Ricognizione**: da 2 a 4 `esploratore` in parallelo, ognuno con obiettivo, formato e confini
   scritti (codice e `old/`, decisioni, documentazione esterna, convenzioni con la fonte). Le
   misure sul vero le fa la sessione principale, su copie. Cosa esiste e si riusa.
2. **Domande a Marco** solo di prodotto: a scelta multipla, consigliata in cima.
3. **Piano scritto** solo se il lavoro tocca piu' file o l'approccio e' incerto: se il diff si dice
   in una frase, niente piano. Ogni punto: Contesto / Obiettivo / Fuori perimetro / Prova finale /
   `mode` (`logica` = scrivo io; `meccanico` = `sviluppatore`) e `surface` se cambia lo schermo.
4. **Un verificatore** a contesto fresco, con tre domande (logica, fattibilita', attacco), solo se
   il piano tocca una convenzione o piu' di un dominio. Piano riscritto coi rilievi.
5. **Se `logica`, costruisco io**: test visti rossi, codice, documenti nello stesso diff (guida
   utente, contratto in `docs/domini/`, ADR, schema). File nuovi: `git add -N`.
6. **Workflow `costruisci`** con `args: {task, plan, mode, surface, answers}`. Esiti:
   - `done`: al punto 7.
   - `question`: a Marco come al punto 2, poi si rilancia con la risposta in `answers`.
   - `stopped`, `checks_failing`, `failed`: si dice a Marco cosa resta aperto e dove. Niente commit.
7. **Riassunto**, cinque righe: apre con *cosa funziona ora e prima no*; poi rilievi corretti,
   rifiutati (col perche') e `parked`, elencati una volta.
8. Se `surface`: **Marco guarda la fetta a schermo** prima del commit.
9. **Commit e push automatici**: `git status`, `git add <file uno per uno>`,
   `git commit -m "feat: <una riga ASCII>"`, `git push origin main`. **Fatto quando la CI su
   GitHub e' verde**: si segue con `gh run watch`; se fallisce, il lavoro non e' chiuso.
