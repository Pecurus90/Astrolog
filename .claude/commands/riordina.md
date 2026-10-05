---
description: Ricetta togliere o riorganizzare - codice morto, doppioni, file da accorpare o spostare. L'elenco lo fa uno strumento; si rivede la regola, non il diff.
argument-hint: [cosa si toglie o si sposta]
---

**Lavoro:** $ARGUMENTS

Regole comuni in ADR 0015. Passi:

1. **Elenco da strumento**: jscpd per i doppioni, grep degli usi, vulture o knip se installati.
   Cosa si toglie o si sposta, file per file, con il perche' in una riga.
2. Se sparisce qualcosa che l'utente vede: **domanda a Marco**. Altrimenti si procede.
3. **Spostamenti con strumento semantico** (rope, LibCST, ast-grep) o, se a mano, dallo
   `sviluppatore` in modo `spostamento`. Import aggiornati, nessun file lasciato a ponte.
4. Un test tolto si dichiara in `tools/test_tolti.txt` (`nome - motivo`): lo pretende
   `tools/guardia_test.py`.
5. **Prova**: snapshot e tipi identici, import-linter e controlli verdi
   (`python -m pre_commit run --all-files --hook-stage manual`).
6. **Revisore: zero o uno**, e guarda la regola o lo script di trasformazione, non le righe.
7. Riassunto (cosa e' sparito, in una riga per voce), commit e push automatici:
   `git commit -m "refactor: <una riga ASCII>"` o `chore:`.
