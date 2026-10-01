# 0001 -- Il metodo passa a strumenti standard

**Stato:** accettata, 30/9/2026

## Contesto

Il metodo di lavoro era fatto di strumenti su misura: un cancello da 240 secondi prima di ogni
commit (mutazione compresa), un marker d'audit, cinque hook, quattordici skill, un disegno generato,
un tetto di 300 righe per file. Misurato: la prosa nel backend pesava 1,35 volte il codice, 79
file stavano fra 280 e 300 righe, le revisioni bocciavano frasi dei documenti invece di difetti.

## Decisione

- I controlli sono **pre-commit** (veloci al commit, completi al push) e la **CI** su tre sistemi,
  con gli stessi comandi. La mutazione gira **di notte** (`mutmut`) ed e' un rapporto, non un
  blocco: su tutto il backend i mutanti sopravvissuti ci sono sempre, e un job sempre rosso non
  dice niente. mutmut non gira su Windows, quindi gira solo in CI. Tutto il backend in un job
  solo sfora il limite di 5 ore: si divide in quattro job paralleli (`api`, `spine` in due, il
  resto), e il resto si calcola da `tools/mutation_shards.py`, cosi' un modulo nuovo non resta
  fuori; un gruppo che resta senza moduli ferma il job. Il rapporto di ogni job tiene
  solo i mutanti del suo gruppo, compresi i "not checked": un job tagliato a meta' lo dice; se
  nel rapporto il gruppo non ha nessun mutante (i nomi non si leggono piu'), il job fallisce
  invece di sembrare pulito. Un mutante che nessun gruppo prende fa fallire il job del resto,
  che lo elenca.
  Finche' non la si vede finire, non conta come macchina.
- Il limite e' sulle **funzioni** (ruff `C901`, `PLR0912/0913/0915`), non sui file: il file ha
  un tetto largo a 1000 righe (pylint). Chi supera oggi porta un `noqa`: e' il debito da togliere.
- **Commenti**: al massimo due righe, in inglese, solo il perche' che il codice non mostra. La docstring di una rotta API fa eccezione: e' il contratto OpenAPI (skill `rotta-api`).
- Il lavoro gira dal comando `/esegui` e dal Workflow `esegui`: revisione fino a vuoto, audit
  che esegue, controlli. Marco decide il prodotto e da' l'ok al commit.
- Plugin del progetto (`.claude/settings.json`): `pr-review-toolkit` per la revisione,
  `security-guidance` che avvisa su una modifica che apre un buco di sicurezza.
- Le decisioni stanno qui, una per file.

## Conseguenze

- Le regole di dominio del vecchio cancello sono passate in pre-commit come espressioni
  (`pygrep`): software fuori dai quattro, DDL fuori dallo schema, commento CSS chiuso da una glob,
  caratteri incollati nel codice di prodotto e nei testi dell'app (i test ne sono esenti: li' sono
  dati), caratteri di controllo in ogni file di codice, import da `old/`. Ognuna ha i suoi casi in
  `tools/test_precommit_rules.py`, che fallisce se una regola ne e' senza. Il messaggio di commit: al
  commit `conventional-pre-commit` (il formato) e `tools/commit_msg.py` (una riga ASCII, che
  scarta le righe `#` del modello dell'editor -- quindi una seconda riga `-m "#..."` passa); in CI,
  sui commit di una pull request, gli stessi due sul messaggio salvato, con `--final`, che non
  scarta niente (merge e bot esclusi: scrivono i loro). Restano anche
  import-linter, il contrasto dei colori, le ruote.
- I segreti: gitleaks al commit guarda lo staging; in CI un passo scansiona ogni file tracciato
  fuori da `old/`.
- Saltare gli hook di git (`--no-verify`, `-n`, `SKIP=`, `core.hooksPath`): a Claude sono vietate
  le forme comuni (`.claude/settings.json`), non tutte, e a una persona no. La rete e' la CI, che
  rifa' tutti i controlli sul codice; il messaggio di un commit spinto direttamente su `main`
  invece non ha rete.
- **Senza macchina, da ora** -- li tiene il Workflow `esegui`, che non salta i passi:
  - commenti corti: revisore e `comment-analyzer`;
  - l'audit: `auditore`;
  - un test sparito senza dirlo: `pr-test-analyzer` e il revisore;
  - le prove promesse nei contratti di `docs/domini/`: l'audit *promesse*;
  - rimandi fra documenti, percorsi citati, voci della coda citate col numero, un file in `docs/`
    fuori da `coda.md`, `guida-utente.md`, `domini/` e `adr/`: il revisore;
  - i percorsi di Windows con una barra mangiata in TS/JS e l'`except` muto dentro un `try`
    lungo (ruff prende `pass` e `continue`, `S110`/`S112`): il revisore.
- **Senza nessuno, e si accetta:**
  - il tetto di durata dei controlli;
  - i percorsi da non mettere mai in staging (DB, immagini dell'utente, `settings.local.json`):
    resta `.gitignore`, che `git add -f` scavalca;
  - l'avviso quando si tocca `old/docs/intervista-requisiti.md`, e i segnali d'apertura (lavoro
    in volo, voci di memoria senza casa): restano le regole in `CLAUDE.md`;
  - la chat in italiano: resta la regola in `CLAUDE.md`.
