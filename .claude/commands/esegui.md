---
description: Sceglie la ricetta giusta per il lavoro (costruisci, ripara, rifattorizza, riordina, rivedi, documenti) e la segue.
argument-hint: [cosa vuoi]
---

**Lavoro:** $ARGUMENTS

Vale `CLAUDE.md`. Prima si dice il tipo in una riga, poi si segue la sua ricetta (ADR 0015):

- funzionalita' nuova o comportamento che cambia: `.claude/commands/costruisci.md`;
- difetto: `.claude/commands/ripara.md`;
- stesso comportamento, codice diverso: `.claude/commands/rifattorizza.md`;
- togliere, accorpare, spostare: `.claude/commands/riordina.md`;
- rivedere un'area senza correggere: `.claude/commands/rivedi.md`;
- documenti e decisioni: li scrivo io, nessuna revisione sulle parole; un comportamento promesso
  in un contratto ha il suo test. Commit `docs:`.

Un lavoro misto si divide: prima la parte che fissa il comportamento, poi il resto.
