# AstroLog -- come si lavora

App **open source** per catalogare, analizzare e pianificare sessioni di astrofotografia: legge gli
header dei FITS, risolve ogni frame sul cielo, ricostruisce la cronologia. Backend Python (FastAPI,
SQLite), frontend React/TypeScript, nessun login. Il progetto di prima e' in `old/`, come cava:
solo in locale e nel repository privato `Astrolog-archivio` (porta dati personali).

Cosa fare: **una lista sola**, `docs/piano.json` (`python tools/piano.py`), dal primo passo aperto in giu' (ADR 0040).
Decisioni nei contratti `docs/domini/` e negli ADR `docs/adr/`. Il metodo e' **ADR 0040**, fermo
fino al 21/11/2026: un'idea di metodo va in una Issue `metodo`, non qui.

## Tre principi

1. **Si progetta per chi la usera', non per Marco.** Attrezzature, software, nomi e cartelle
   diversi; l'archivio di Marco verifica, non decide: un numero tarato su un archivio solo vale se
   si tara sui dati di ogni utente, se lo regge un argomento indipendente, o se diventa
   Impostazione; ogni taratura si prova su dati che non ha visto. Si regge a mani vuote. Bersagli: Windows, Mac, NAS (Docker), mobile per ultimo,
   quindi i dati escono dall'API gia' fatti e il layout non porta logica. **Soglie e formule da
   convenzioni pubbliche**, verificate su una fonte vera e citate accanto al numero (lo controlla
   `tools/registro.py`); se il codice diverge, vale la convenzione e si dice a Marco cosa cambia a
   schermo. Un software esterno ripreso si confronta con la sua documentazione.
2. **Marco decide il prodotto, non il codice.** A lui solo gusto, parole, rischio, dati suoi,
   schermate: a scelta multipla (che passi da una domanda a scelta lo controlla
   `.claude/hooks/ask.py`), la consigliata in cima col perche' in una riga, la piu' corretta e non
   la piu' corta, col suo costo. Soglie tecniche, metodo, ordine interno di un passo: li decido io
   e lo dico in una riga. Una decisione scritta in un contratto o in un ADR vale: se sembra
   sbagliata si porta a Marco, non si aggira; un numero tecnico smentito da una misura lo correggo
   io e lo dico. **Un difetto non e'
   una domanda**: si ripara subito con `/ripara`, o diventa Issue `bloccato` col motivo.
   Ogni resoconto apre con *cosa funziona ora e prima no*.
3. **Il database non conta finche' non si rilascia.** Si ricrea da `backend/astrolog/schema.sql`:
   niente migrazioni, niente backfill.

## Il giro di lavoro

- **Prima il rosso**: CI, Nightly, Issue `difetto`, avvisi di sicurezza vengono prima del passo
  del piano. **Fatto vuol dire verde su GitHub**, non in locale: dopo il push si guarda la CI.
- **Ogni modifica al codice passa da una ricetta** invocata col suo nome: `/costruisci`,
  `/ripara`, `/rifattorizza`, `/riordina`, `/rivedi`. Un giro di revisione, al massimo una
  verifica; blocca solo un rilievo con prova; cio' che resta aperto ferma il lavoro.
- **Uno scrive, gli altri leggono**: in parallelo solo `esploratore` (ricognizione) e `revisore`.
  Due agenti non scrivono mai insieme sugli stessi file, e nessuno lancia pre-commit mentre un
  altro scrive (mette da parte le modifiche non salvate).
- **Un lavoro alla volta**; `/clear` fra un passo e l'altro.

| Ruolo | Chi |
|---|---|
| Prodotto, risposte, sguardo finale a schermo | Marco |
| Tavole e componenti | Claude Design |
| Piano, logica di dominio, backend, coordinamento | sessione principale |
| Ricognizione in sola lettura | `esploratore` |
| Lavoro meccanico gia' deciso | `sviluppatore` |
| Revisione del diff | `revisore` |
| Audit che esegue e misura | `auditore` |
| Traduzione di una pagina finita | `traduttore` |

## Il codice

- **Controlli** in `.pre-commit-config.yaml`: veloci al commit, completi al push e in CI.
- **Limiti sulle funzioni** (ruff `C901`, `PLR0912/0913/0915`), file sotto 1000 righe.
- **Nomi e commenti in inglese** (i nomi del backend: `tools/nomi_inglesi.py`); italiano in
  documenti, testi dell'app e chat. Commenti caveman, al massimo 2 righe (`tools/commenti.py`). Prosa
  compressa nei documenti di lavoro; `docs/guida-utente.md` in italiano pieno.
- **Tipi**: funzione toccata esce annotata; `StrEnum` per insiemi chiusi, `dataclass` per righe.
- **Un fatto, una casa.** Derivazioni in Python; il frontend formatta e basta; tipi TS
  dall'OpenAPI. Si cerca prima se esiste. Un'astrazione alla seconda occorrenza.
- **Test prima, visti rossi.** **Una lettura non calcola.** **Le date portano il fuso**: la notte
  va da mezzogiorno a mezzogiorno nel fuso del sito.
- **Programmi verificati: N.I.N.A. e ASIAIR** (ADR 0029, 0033); SharpCap Pro solo per l'export <!-- software-ok -->
  del Sistema solare.
- **`old/` si porta, non si importa** (lo controlla un hook): un pezzo coi suoi test; si porta
  solo cio' che si usa. `old/docs/intervista-requisiti.md` si legge e non si tocca.

## Come mi comporto

- **Verifico sul reale prima di asserire**; una riparazione si prova facendo fare al programma la
  cosa che prima non faceva; dopo una modifica al backend lo si riavvia.
- **Un numero o un "sempre/nessuno" si conta** prima di scriverlo; un fatto corretto si corregge
  in tutte le sue case.
- **Una superficie si collauda nel browser** (skill `collaudo-dal-vivo`).
- **Prima la risposta, poi il lavoro.** Un testo o una frase nuovi si concordano prima del codice.
  Un'idea di Marco "per dopo" resta in `docs/idee.md` finche' non dice di farla. Se Marco aspetta
  qualcosa da dare ad altri (Design), quello viene prima.
- **La memoria non e' una casa**: cio' che vale sta nel repo; la memoria tiene il rimando.
- Quando compatti, conserva il passo del piano, i file toccati e i comandi di test.

## Regole ferme

- **Commit e push automatici** di un lavoro chiuso, verde e rivisto; si ferma solo per cio' che e'
  di Marco. Conventional Commits, una riga ASCII, niente `Co-Authored-By` (lo controllano i hook
  del messaggio in `.pre-commit-config.yaml`). Mai force push ne' storia riscritta: `git revert --no-commit <sha>`, poi
  `git commit -m "revert: ..."`.
- **Windows + Git Bash**: percorsi assoluti, mai `cd` in un comando composto, mai heredoc o script
  che scrivono file (lo blocca `.claude/hooks/guard.py`): si scrive con Edit/Write.
- **Uno script di sostituzioni** stampa le stringhe non trovate; dopo un generatore si guarda
  `git status`.
- **Regole o plugin cambiati: sessione nuova.**
- **Ogni documento nella sua casa** (lo controlla `tools/tetti.py`): domini, ADR, guida, idee,
  piano, registro generato, brief aperti in `handoff/`; lo schema in `schema.sql`.
