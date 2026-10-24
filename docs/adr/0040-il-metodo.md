# 0040 -- Il metodo: sette regole tenute da macchine, congelato fino al 21/11/2026

**Stato:** accettata, 24/10/2026 (Marco). Supera in parte ADR 0001, 0015, 0025, 0027, 0028, 0030,
0033 nella parte di metodo. Fonti e misure: `reports/Impostare Claude Code per AstroLog.md`.

## Contesto

Audit del 24/10: 164 push rossi di fila dal 21/10, Nightly mai verde in 29 notti, 5 Issue
`difetto` aperte, 7 avvisi Dependabot, sette posti che dicono "cosa si fa ora". Sette ADR di metodo
in 25 giorni; 34% dei commit solo documenti (tetto 25%, ADR 0027). Rispettate le regole che una
macchina blocca (comando, commit); ignorate quelle che chiedono di guardare dopo (CI, notte, Issue,
misure). CLAUDE.md e' contesto, un hook e' deterministico (guida di Claude Code, *Best practices*).

## Decisione

| # | Regola | Macchina |
|---|---|---|
| 1 | **Una lista sola**: si lavora sul primo passo aperto di `docs/piano.json`; l'agente lo spunta e basta | `tools/piano.py` lo stampa all'avvio; al commit rifiuta ogni modifica che non sia una spunta senza messaggio `docs(piano):` (`plan:` non e' un tipo Conventional Commits) |
| 2 | **Prima il rosso**: CI, Nightly, Issue `difetto`/`sicurezza`, avviso di sicurezza vengono prima di ogni passo | SessionStart `tools/stato.py`; Stop hook; controllo in sottofondo dopo il push; Issue `nightly-rosso` aperta dalla Nightly |
| 3 | **Fatto = provato**: un passo e' fatto quando il commit che lo spunta e' verde su GitHub, non in locale | SessionStart guarda la CI del commit della spunta; rossa, il passo torna in testa |
| 4 | **Uno scrive, gli altri leggono**: in parallelo solo `esploratore` (2-4, con obiettivo, formato e confini) e `revisore` (uno, due su diff grandi) | Strumenti dei sotto-agenti: `esploratore` e `revisore` non scrivono |
| 5 | **A Marco solo il prodotto** (gusto, parole, rischio, schermate), a scelta multipla, consigliata in cima | `ask.py`; registro delle domande, contato il 21/11 |
| 6 | **Un difetto si ripara subito** con `/ripara`, o Issue `bloccato` col motivo | SessionStart conta le Issue e la loro eta'; con CI rossa lo Stop lascia chiudere solo se una Issue `bloccato` nomina il run |
| 7 | **Metodo congelato fino al 21/11/2026**; le proposte vanno in Issue `metodo` | `guard.py` chiede la conferma di Marco prima di ogni modifica a `CLAUDE.md` e `.claude/` |

La 5 resta in parte giudizio (domanda tecnica o di prodotto), come "test visto rosso" e "la
consigliata e' la piu' corretta": nessuna macchina li vede.

- **Soglie tecniche, metodo, ordine interno di un passo**: li decide l'agente e li dice in una riga.
  Una soglia che diverge dalla convenzione: vince la convenzione, a Marco si dice cosa cambia a
  schermo; nessuna convenzione: sceglie l'agente fra gli usi trovati (supera ADR 0028,
  *Convenzioni*).
- **Piano** solo se il passo tocca piu' file o l'approccio e' incerto; se il diff si dice in una
  frase, niente piano. Verifica del piano: **un verificatore** con le tre domande (logica,
  fattibilita', attacco), solo se il piano tocca una convenzione o piu' di un dominio.
- **Revisione**: un giro, piu' al massimo una verifica (ADR 0015). Un revisore, due su diff grandi
  con domande diverse; vale anche per il passo del cuore della pipeline (supera ADR 0030, tappa 5).
- **Aggiornare una dipendenza gia' presente non e' una dipendenza nuova**: niente domanda a Marco.
  Dependabot fonde da solo patch e minor a controlli obbligatori verdi, correzioni di sicurezza
  comprese (Marco, 24/10); le maggiori restano difetti. Una dipendenza nuova resta rischio di Marco.
- **Mutazione**: la Nightly fallisce solo se il punteggio peggiora rispetto a un riferimento
  salvato; notte rossa = Issue `nightly-rosso` (supera ADR 0001, "rapporto, non blocco").
- **Rito**: all'avvio lavoro non committato = si chiede; rosso = il lavoro e' quello; altrimenti
  primo passo aperto, ricetta invocata con `/nome`. Alla fine commit, push, spunta con lo sha,
  riassunto che apre con "cosa funziona ora e prima no". `/clear` fra un passo e l'altro.
- **CLAUDE.md sotto 100 righe**: tre principi, comandi, trappole di Windows, rimando al piano, una
  riga "lo controlla X" per regola. Regole d'area in `.claude/rules/` con `paths`. La provenienza
  delle regole sta qui, non accanto a ogni regola in CLAUDE.md.

### Si toglie

| Cosa | Perche' |
|---|---|
| `verificatore-disegno`, `collaudatore`, modo `pagina` dalla tabella dei ruoli | Non esistono; una sessione fresca prova a lanciarli. `collaudatore` al passo 29 |
| ADR 0025: `tools/contratti.py`, riga **Supera** obbligatoria, `verificatore-disegno` | Promesse senza uso; la consegna di Design si controlla con la lista di `/porta-tavola` |
| ADR 0028: `/salute`, `/audit`, `/smista`, audit settimanale via Action | `/salute` = SessionStart; `/audit` = `/rivedi`; `/smista` = regola 6. claude-code-action: secondo autore e costo |
| Misure di ADR 0015 (due settimane) e 0025 (`fix:` per fetta) | Mai fatte; una misura sola il 21/11 |
| `PARTENZA.md`, `fase4-registro.md`, `astap-piano.md`, `stato-di-oggi.md` come guide | Contenuto in `piano.json`; fuori dal repo niente dice "prossimo" |
| "Quando Marco corregge, nello stesso turno uno strumento" | Motore dei cambi di metodo; ora Issue `metodo` |
| Timbri "(Marco, data)" in CLAUDE.md | Provenienza qui |
| Permessi `Workflow(esegui)`, `Bash(curl *)`, `PowerShell(Remove-Item *)` | Morto da ADR 0015; larghi |
| Brief risposti in `handoff/` | Promessa di ADR 0027 mai mantenuta |

## Congelamento e misura

Fino a sabato 21/11/2026 il metodo non cambia; quel giorno si leggono cinque numeri, calcolati da
script, e si decide cosa togliere (non aggiungere):

1. ore di CI rossa su `main` per settimana: nessun rosso oltre un push o 2 ore (`gh run list`);
2. notti verdi di fila; eta' delle Issue `difetto`/`sicurezza`: nessuna oltre 2 giorni (Linear);
3. passi chiusi per settimana col commit verde: in salita, nessuno spuntato e riaperto;
4. domande tecniche a Marco: zero (registro di `ask.py`);
5. commit su CLAUDE.md e `.claude/` dopo la fase 0: zero; commit solo documenti sotto il 25%.

## Ordine

Prima la fase 0, le basi, una alla volta (ordine di Marco dopo il rapporto, 24/10/2026: le basi
prima dei problemi): case dei documenti -> riconciliazione delle decisioni ->
CLAUDE.md potato sotto 100 righe -> una lista `docs/piano.json` (`tools/piano.py`, `piano.md`
tolto con tetto 0) -> hook (SessionStart, Stop, dopo il push, Issue notturna, registro domande) ->
Dependabot. Poi i problemi uno per uno, nell'ordine di `piano.json`.

Gia' fatto: CI verde di nuovo dal commit `ca6b2f61`; case dei documenti controllate al commit
(`tools/tetti.py`, `HOUSES`).

## Conseguenze

- ADR 0001, 0015, 0025, 0027, 0028, 0030, 0033 portano in testa "superata in parte da ADR 0040"
  con le parti; il corpo non si riscrive.
- `tools/tetti.py`: CLAUDE.md 100, `docs/piano.md` 0 quando nasce `piano.json`.
- Rischi accettati: lo Stop scatta a ogni risposta (voluto, si misura); un `docs(piano):` si puo'
  inventare (il controllo lo rende visibile); GitHub puo' saltare una Nightly (oltre 36 ore = rosso).
