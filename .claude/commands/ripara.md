---
description: Ricetta riparare - un difetto dal sintomo al commit. Test che lo riproduce visto rosso, correzione minima, un revisore.
argument-hint: [il difetto]
---

**Difetto:** $ARGUMENTS

Regole comuni in ADR 0015. Passi:

1. **Riproduci**: un test che mostra il difetto, visto rosso. Senza test rosso non si corregge.
2. **Causa**: lo strato dove nasce il difetto, non dove si vede.
3. **Correzione minima** li'. Niente meccanismi, file o dipendenze nuovi: se servono, e' una
   domanda a Marco.
4. Test verde, nessun altro test cambiato; `python -m pre_commit run --files <file toccati>`.
5. **Un `revisore`**, una domanda: la causa e' quella giusta? e' cambiato altro? Solo rilievi
   bloccanti con prova. Un bloccante: una correzione, una verifica; ancora aperto, ci si ferma.
6. Se il difetto si vedeva a schermo: collaudo (skill `collaudo-dal-vivo`), poi Marco guarda.
7. **Riassunto** in tre righe (cosa funziona ora e prima no, la causa, il test), poi commit e
   push automatici: `git commit -m "fix: <una riga ASCII>"`, `git push origin main`.
