# 0015 -- Una ricetta per tipo di lavoro, una revisione sola

**Stato:** accettata, 5/10/2026. Sostituisce il giro di revisione di ADR 0001.

## Contesto

Il Workflow `esegui` rivedeva con cinque agenti "finche' un giro non trova difetti", uguale per
ogni lavoro. Misurato: 10-16 giri e 2-6 milioni di token per un lotto piccolo, quasi tutti su
parole dei commenti; dentro i giri il correttore aggiungeva meccanismi (un thread pool, un
lockfile rigenerato, il Workflow da 150 a 821 righe). Un revisore LLM e' un sensore rumoroso: un
giro "pulito" non arriva per costruzione. Fonti e misure: `reports/Metodo di lavoro con agenti.md`
(locale, fuori dal repo).

## Decisione

Quattro regole valgono per ogni ricetta:

- **Un giro di revisione**, piu' al massimo una verifica ristretta alle correzioni. Cio' che resta
  aperto ferma il lavoro e va nel riassunto; niente secondo ciclo.
- **Blocca solo un rilievo con prova**: comportamento sbagliato, sicurezza, perdita di dati,
  contratto o richiesta violati, test tolto o indebolito; la prova e' un comando, un test rosso o
  un controesempio preciso. Il resto si elenca una volta e non riapre il lavoro.
- **Il correttore puo' rifiutare** col perche', e non aggiunge dipendenze, file o meccanismi:
  se servono, e' una domanda a Marco.
- **Una regola che una macchina sa controllare sta in una macchina**, non in un prompt:
  commenti (`tools/commenti.py`, ruff `ERA001`), test tolti (`tools/guardia_test.py`), file
  protetti e dipendenze (`.claude/hooks/guard.py`), equivalenza (snapshot syrupy, tipi generati).

Ricette, in `.claude/commands/` (`/esegui` sceglie):

| Tipo | Comando | Revisori | Si ferma quando |
|---|---|---|---|
| Costruire | `/costruisci`, Workflow `costruisci` | 1 + audit `promesse` (+ `collaudo` se cambia lo schermo) | controlli verdi dopo un giro e una verifica |
| Riparare | `/ripara` | 1 | test del difetto verde, nient'altro cambiato |
| Rifattorizzare | `/rifattorizza` | 0, 1 se la prova non copre | snapshot e tipi identici |
| Togliere, riorganizzare | `/riordina` | 0-1, sulla regola | strumenti e controlli verdi |
| Rivedere | `/rivedi` | 1-2 + un verificatore | un passaggio; i bloccanti diventano `/ripara` |
| Documenti | -- | 0 | rimandi validi, promessa nuova col suo test |

I momenti di Marco sono quattro: cosa si fa (all'inizio, a scelta multipla), cio' che vede (a
schermo, se cambia), il rischio (una dipendenza o un meccanismo nuovo), il riassunto. Commit e
push restano automatici.

Il lavoro sul metodo (Workflow, comandi, agenti) non passa per il proprio giro: si scrive corto,
si prova su un compito vero, si misura.

## Conseguenze

- Tolti `.claude/workflows/esegui.js` e `tools/solo_prosa.py`, coi loro test (dichiarati in
  `tools/test_tolti.txt`). I revisori di `pr-review-toolkit` escono dal giro; il plugin resta
  installato per chi lo chiama a mano.
- Per due settimane si registrano token, minuti e difetti per tipo di lavoro, da confrontare coi
  numeri del giro vecchio. Se una ricetta lascia passare difetti, si aggiunge una macchina, non
  un revisore.
