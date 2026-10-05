---
description: Ricetta rifattorizzare - cambiare il codice senza cambiare cio' che fa. La prova di equivalenza decide, non un revisore.
argument-hint: [cosa si rifattorizza]
---

**Lavoro:** $ARGUMENTS

Regole comuni in ADR 0015. Passi:

1. **Prova prima**: `python -m pytest backend/tests/test_snapshot_comportamento.py` e
   `python tools/tipi.py --check` verdi. Se la parte toccata non e' coperta dalle snapshot o dai
   test, si aggiunge prima un test che la fissa, e si committa da solo.
2. **Modifica**: lotti piccoli; rinomine e spostamenti con uno strumento (rope, LibCST,
   ast-grep) quando ce n'e' uno, non a mano. Il lavoro meccanico va allo `sviluppatore`.
3. **Stessa prova dopo**: snapshot identiche, tipi identici, test non toccati, controlli verdi
   (`python -m pre_commit run --all-files --hook-stage manual`). Le snapshot non si aggiornano:
   se cambiano, il comportamento e' cambiato e il lotto si rifa'.
4. **Revisore: zero** se la prova copre tutto. Uno solo, se non la copre, con la domanda "cambia
   qualcosa che l'utente vede?".
5. Riassunto in una riga, commit e push automatici: `git commit -m "refactor: <una riga ASCII>"`.
