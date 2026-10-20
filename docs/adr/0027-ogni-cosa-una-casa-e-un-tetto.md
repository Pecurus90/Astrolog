# 0027 -- Ogni cosa una casa e un tetto: piano, idee, Issue; niente coda

**Stato:** accettata, 20/10/2026 (Marco). Proposta completa e fonti:
https://claude.ai/artifact/UF76BGLvpxVWmgzXt98yDR

## Contesto

`docs/coda.md` a 1.278 righe: 520 di piano con circa 50 voci "fatto", 168 di difetti parcheggiati,
251 di requisiti delle pagine, 290 di debito scritto a mano, 23 di idee di Marco. 126 commit su 267
dal 3/9 sono solo documenti. Le convenzioni: zero bug policy (Linear, Redgate), niente backlog
(Shape Up, "Bets, not backlogs"), WIP limitato (Kanban), ADR corti e immutabili (Nygard), difetti
nelle Issue (GitHub), CLAUDE.md sotto 200 righe e regole ai controlli (guida di Claude Code).

## Decisione

- **Un difetto trovato si ripara subito** (`/ripara`). Bloccato da fuori (un file, una risposta
  di Marco, un utente Voyager): Issue di GitHub con etichetta `bloccato` e il motivo.
- **`docs/piano.md`**: Ora (una cosa), Dopo (in ordine), Piu' avanti. Niente voci "fatto": la
  storia e' git, dal primo rilascio anche `CHANGELOG.md` (Keep a Changelog).
- **`docs/idee.md`**: le idee di Marco, una riga con la data. A ogni tappa del piano si rilegge:
  si fa, resta o si cancella; ferma da tre tappe si cancella.
- **Debito tecnico**: nessuna lista; lo contano i controlli e si chiude quando si tocca il codice.
- **Brief a Design** in `handoff/` solo finche' aperti; risposti si cancellano.
- **Tetti controllati al commit**: piano 80 righe, idee 60, ADR 100, contratto di dominio 400,
  CLAUDE.md 200. Proposti, non convenzioni (tranne CLAUDE.md): si correggono dopo la prova.
- Un documento cambia nel commit del codice che lo riguarda; commit di soli documenti per un ADR o
  un brief. Obiettivo: sotto un quarto dei commit.

Ordine: i difetti del punto 1 del check di salute, poi lo smontaggio della coda e i tetti, poi il
porting.

## Conseguenze

- `docs/coda.md` sparisce; fino ad allora non cresce (`tools/tetti.py`).
- La spina (`docs/domini/spina.md`, 1.072 righe) si divide per stadio; gli ADR sopra 100 righe si
  riducono alla decisione, il dettaglio va nel contratto.
- CLAUDE.md, ricette e skill si aggiornano alle case nuove nello stesso lavoro.
