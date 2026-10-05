---
description: Ricetta revisione - rivedere un'area o prepararsi a un rilascio. Uno o due revisori con domande strette, ogni rilievo con prova; nessuna correzione nello stesso giro.
argument-hint: [area da rivedere]
---

**Area:** $ARGUMENTS

Regole comuni in ADR 0015. Passi:

1. **Perimetro dichiarato**: file o cartelle, e cosa resta fuori.
2. **Uno o due revisori** in parallelo, con domande diverse e strette (es. bug logici;
   sicurezza). Solo rilievi bloccanti, ognuno con prova: un comando, un test che fallisce, un
   controesempio preciso.
3. **Un verificatore** separato (`auditore`) prova i bloccanti eseguendo. Cio' che non riproduce
   cade.
4. **Nessuna correzione qui.** I bloccanti confermati vanno a Marco in una lista: quali si
   riparano subito (ognuno con `/ripara`) e quali vanno in `docs/coda.md`.
