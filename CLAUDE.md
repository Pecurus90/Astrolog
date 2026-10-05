# AstroLog -- come si lavora

App **open source** per catalogare, analizzare e pianificare sessioni di astrofotografia: si
punta alle cartelle dei FITS, l'app legge gli header, risolve ogni frame sul cielo e ricostruisce
una cronologia osservativa. Backend Python (FastAPI, SQLite), frontend React/TypeScript, nessun
login. Il progetto di prima e' in `old/`, come cava: solo in locale e nel repository privato
`Astrolog-archivio`, non in quello pubblico (porta dati personali).

Lo stato si legge dal codice e da [`docs/coda.md`](docs/coda.md); le decisioni stanno in
[`docs/adr/`](docs/adr/). Questo file dice solo come si lavora.

## Tre principi

1. **Si progetta per chi la usera', non per Marco.** Altri utenti avranno attrezzature, software,
   nomi e cartelle diversi: l'archivio di Marco e' un caso di prova, mai il metro. Si regge a mani
   vuote (primo avvio, zero frame). Tre bersagli: Windows, Mac, NAS (Docker) anche da tablet e
   telefono -- desktop prima, mobile alla fine, quindi i dati escono dall'API gia' fatti e il
   layout non porta logica. **Le soglie vengono da convenzioni pubbliche** (okta WMO, Nyquist,
   Beaufort), verificate su una fonte vera e citate accanto al numero, mai scritte a memoria.
2. **Marco non e' un programmatore: decide il prodotto, non il codice.** Si chiede solo cio' che
   dipende da lui (gusto, dati suoi, rischio che accetta). Quando serve: **a video, a scelta
   multipla, con la consigliata in cima e il perche' in una riga**. **La consigliata e' la piu'
   corretta, non la piu' corta**: se la strada giusta costa piu' lavoro, si consiglia quella e si
   dice quanto costa. Se la risposta non dipende da lui e una consigliata c'e', non si chiede: si
   prende quella. Cio' che dipende dal codice, da una misura o dal metodo lo decido io e lo dico in
   una riga. **Un difetto
   non e' una domanda**: si ripara e si dice. Ogni resoconto apre con *cosa funziona ora e prima
   no*.
3. **Il database non conta finche' non si rilascia.** Si ricrea da `backend/astrolog/schema.sql`
   quante volte serve: niente migrazioni, niente backfill.

## Il giro di lavoro

Una ricetta per tipo di lavoro (ADR 0015): `/costruisci`, `/ripara`, `/rifattorizza`,
`/riordina`, `/rivedi`; `/esegui` o le parole scelgono. Per tutte: un giro di revisione e al
massimo una verifica delle correzioni; blocca solo un rilievo con prova; il correttore puo'
rifiutare e non aggiunge dipendenze, file o meccanismi; cio' che resta aperto ferma il lavoro e
va nel riassunto. Una regola controllabile da una macchina sta in una macchina, non in un prompt.

| Ruolo | Chi | Modello |
|---|---|---|
| Prodotto, risposte, collaudo a schermo | Marco | -- |
| Piano, logica di dominio, coordinamento | sessione principale | Opus |
| Ricognizione in sola lettura | `esploratore` | Sonnet |
| Potare, tipizzare (serve giudizio) | `sviluppatore` | Opus |
| Spostare file, rinominare, aggiornare import | `sviluppatore`, modo `spostamento` | Sonnet |
| Revisione del diff, un giro | `revisore` | Opus |
| Audit che esegue e misura | `auditore` | Opus |
| Traduzione di una pagina finita | `traduttore` | Sonnet |

## Il codice

- **Controlli:** `.pre-commit-config.yaml` -- veloci al commit, completi al push e in CI
  (`python -m pre_commit run --all-files --hook-stage manual`). La mutazione gira di notte.
- **Limiti sulle funzioni, non sui file** (ruff `C901`, `PLR0912/0913/0915`; file sotto 1000
  righe). Un `noqa` su quelle regole e' debito: si toglie quando si tocca la funzione.
- **Nomi e commenti in inglese; italiano** nei documenti, nei testi dell'app e in chat.
- **Tipi:** una funzione che si tocca esce annotata; `StrEnum` per un insieme chiuso di stringhe,
  `dataclass` per una riga che viaggia fra funzioni invece di un `dict`.
- **Prosa compressa** nei commenti e nei documenti di lavoro (coda, ADR, contratti, comandi,
  agenti): frasi corte, niente riempitivi, solo il perche' che il codice non mostra. Tetto e
  divieti dei commenti li controlla `tools/commenti.py`. `docs/guida-utente.md` resta italiano pieno.
- **Un fatto, una casa.** Le derivazioni vivono in Python; il backend manda cio' che lo schermo
  mostra e il frontend formatta e basta; i tipi TS si generano dall'OpenAPI. Prima di scrivere
  una funzione si cerca se esiste. Un'astrazione o un file nuovo alla seconda occorrenza, mai
  alla prima.
- **Test prima del codice, visti rossi:** una regola, un test che si rompe se la regola si rompe.
- **Una lettura non calcola:** calcola chi scrive, e scrive il risultato.
- **Le date portano il fuso:** la notte va da mezzogiorno a mezzogiorno nel fuso del sito.
- **Software supportati: quattro** (N.I.N.A., ASIAIR, Voyager, SGP). Una decisione gia' in
  un contratto di `docs/domini/` o in un ADR vale: se sembra sbagliata si porta a Marco, non si aggira.
- **`old/` si porta, non si importa:** un pezzo si sposta coi suoi test; un vocabolario voce per
  voce, con Marco. `old/docs/intervista-requisiti.md` si legge e non si tocca.

## Come mi comporto

- **Verifico sul reale prima di asserire**: codice, DB, app che gira -- non i documenti. Una
  riparazione si prova facendo fare al programma la cosa che prima non faceva. Dopo una modifica
  al backend lo si riavvia prima di collaudare.
- **Un numero o un "sempre/nessuno" in prosa si conta** (grep, misura) prima di scriverlo, o non
  si scrive. Un fatto corretto si corregge in tutte le sue case, cercate col grep anche con le
  parole che legge l'utente.
- **Una superficie si collauda nel browser**, guardando il contenuto (skill `collaudo-dal-vivo`).
- **Quando Marco mi corregge su un modo di sbagliare**, nello stesso turno: prima uno strumento
  (test, hook, controllo di pre-commit), solo se non si puo' una riga qui.
- **Una fetta arriva a schermo**: parte da cio' che l'utente vedra' e ci arriva in un commit.
- **La memoria non e' una casa**: cio' che vale si scrive nel repo (qui, `docs/coda.md`, un ADR);
  la memoria tiene solo il rimando, e ogni voce dichiara la sua casa (`casa:`).

## Regole ferme

- **Commit e push automatici** (Marco, 5/10/2026): un lavoro chiuso coi controlli verdi e la
  sua revisione fatta si committa e si pubblica senza chiedere, col suo riassunto, e si passa
  al successivo. Si ferma e chiede solo per cio' che e' di Marco: prodotto, cio' che
  l'utente vede da collaudare, una dipendenza nuova, un controllo rosso che non si ripara.
  Messaggio Conventional Commits, una riga ASCII
  (`fix: ...`), niente `Co-Authored-By`. Mai force push, mai riscrivere la storia: si torna
  indietro con `git revert --no-commit <sha>` e poi `git commit -m "revert: ..."` (il messaggio
  che `git revert` scrive da solo non passa i controlli del messaggio).
- **Windows + Git Bash:** percorsi assoluti, mai `cd` in un comando composto, mai heredoc che
  scrive un file. Il testo si scrive con Edit/Write: negli script le barre rovesciate diventano
  caratteri di controllo o a capo veri, e i backtick li esegue la shell.
- **Uno script di sostituzioni afferma di aver trovato ogni stringa**, raccoglie i mancati e li
  stampa alla fine; dopo un generatore si guarda `git status`, non il suo output.
- **Un lavoro alla volta:** se all'apertura c'e' lavoro in volo, si chiede.
- **Regole o plugin cambiati: sessione nuova.** Gli agenti ricevono il CLAUDE.md letto all'avvio,
  e un plugin installato a sessione aperta non carica i suoi agenti.

## Dove va cosa

| se sto per... | casa |
|---|---|
| toccare un dominio | `docs/domini/<dominio>.md` |
| prendere una decisione che resta | `docs/adr/NNNN-titolo.md` |
| cambiare cio' che l'utente vede | `docs/guida-utente.md`, nello stesso intervento |
| parcheggiare un'idea o un debito | `docs/coda.md` |
| toccare lo schema | `backend/astrolog/schema.sql` |
