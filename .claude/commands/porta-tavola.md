---
description: Ricetta portare una tavola - una pagina di Claude Design nell'app. Lista fissa contro la consegna, poi backend, pagina, collaudo, Marco a schermo.
argument-hint: [pagina, es. Archivio]
---

**Lavoro:** $ARGUMENTS

Regole comuni in ADR 0015, 0025 (il giro della fetta) e 0040. La consegna sta in
`handoff/design/` (istruzioni: `docs/per-claude-code-porting.md`).

**Chi vince** (Marco, 27/10/2026). La tavola e' la specifica, aspetto e funzioni; il codice si
adegua. In ordine:
1. una decisione di Marco **piu' recente** della tavola (data in ADR, contratto o `docs/piano.json`
   contro la data della voce in `handoff/design/docs/DECISIONI.md`) vince sulla tavola, senza
   chiedere; se cambia la tavola, brief a Design;
2. la tavola e DECISIONI vincono su un contratto `docs/domini/` piu' vecchio: il contratto si
   riscrive nello stesso diff;
3. cio' che non si puo' fare (principio 1: soglie da convenzioni pubbliche, dati che l'app non ha)
   resta fuori: si dice a Marco cosa cambia a schermo.

Cio' che la tavola o DECISIONI riportano **non si chiede**. A Marco solo cio' che la tavola non
dice: testi e soglie nuovi, a scelta multipla. Questa regola supera, per le pagine con una tavola,
"la pagina nasce semplice" di `componente-che-formatta`.

Passi:

1. **Tavola congelata**: versione = ultima voce di `handoff/design/docs/CHANGELOG.md`, scritta nel
   piano. Durante la fetta `handoff/design/` non si muove; una consegna nuova riapre il punto 2.
2. **Lista fissa contro la consegna**, voce per voce, ognuna con esito e prova `file:riga`. Un
   `esploratore` per la pagina e la sua tavola `stati`; i conti e i confronti li rifa' la sessione
   principale. Esiti: *ok*; *a Design* (brief in `handoff/`); *contratto da riscrivere*; *fuori*
   (regola 3 sopra).
   1. **Versione**: la pagina e i suoi componenti sono nella versione del punto 1; dove
      `COMPONENTI.md` e' piu' vecchio della pagina, vale la pagina.
   2. **Stati**: pieno, vuoto, caricamento (`Scheletro`), errore (`Avviso`), "non so", da chi non
      e' Marco; dalla tavola `stati` o da `?stato=`. Uno stato che manca va a Design.
   3. **Telefono**: `?formato=telefono` esiste; bersagli da 44 px; cio' che il telefono nasconde
      lo nasconde il foglio, non il codice: l'API da' gli stessi dati ai due formati.
   4. **Parole**: ogni testo contro il glossario (`tools/glossario.py`) e le decisioni sulle
      parole; italiano, numeri all'italiana, nessuna sigla di codice.
   5. **Numeri e soglie**: ogni numero fisso o soglia della tavola e di `soglie.js` contro ADR,
      contratto e `docs/registro.md`, con la fonte; si applica "Chi vince".
   6. **Unita'**: px contro arcosecondi, gradi, ore, percentuali, fuso del sito; la notte da
      mezzogiorno a mezzogiorno.
   7. **Calcoli**: ogni funzione di `soglie.js`, `dati*.js`, `catalogo.js` usata dalla pagina
      diventa un campo dall'API, con la rotta (esistente o da fare). Il componente non calcola.
   8. **Componenti**: ogni `dc-import` della pagina esiste in `pagine/componenti/` e nell'app (o
      si porta qui); parametri `modo` e `accento`.
   9. **Classi**: ogni classe usata esiste nel foglio della consegna; stile inline solo dove
      `per-claude-code-porting.md` lo ammette.
   10. **Colore mai da solo**: ogni stato ha parola e segno.
   11. **Simulato**: dati, "adesso" fisso, esportazioni che dicono "fatto": tutto con la sua
       sorgente vera nell'app, o *fuori*.
   12. **Per altri utenti**: nomi di filtri, setup, cartelle, siti della tavola sono dati di
       prova, mai regole (skill `per-altri-utenti`).
   13. **Aperte**: voci di DECISIONI "da approvare", "Prossimi", Issue che nominano la pagina:
       nessuna si porta come decisa.
3. **Piano corto** dai rilievi: backend (campi del punto 2.7), pagina, contratti da riscrivere,
   brief a Design. Un brief aperto che cambia cio' che si porta ferma la fetta finche' Design
   risponde; il resto va avanti.
4. **Backend** come `/costruisci`: test visti rossi, logica, rotta, tipi TS generati.
5. **Pagina**: la tavola in React coi componenti comuni e le classi del foglio, ogni testo da
   `t()`, nessun calcolo, ogni stato della voce 2.2 (skill `componente-che-formatta`,
   `testi-per-pagina`).
6. **Workflow `costruisci`** con `surface` e in `task` la lista del punto 2; esiti come in
   `/costruisci`.
7. **Collaudo** pagina contro tavola, desktop e telefono, ogni stato: agente `collaudatore`
   (dentro il workflow, coi suoi criteri e le catture di `tools/cattura.py`); le differenze le
   ripara chi ha scritto, una verifica.
8. **Differenze** (Marco, 8/11): ogni esito *fuori*, *contratto da riscrivere*, *a Design* e ogni
   scelta diversa dalla tavola va in `handoff/differenze-dalle-tavole.md`, sezione della pagina:
   cosa dice la tavola, cosa fa l'app, perche'. Nello stesso commit.
9. **Riassunto** come in `/costruisci`, con le differenze nuove; poi **Marco guarda a schermo**.
10. **Traduzione** (`traduttore`) a pagina finita, guida utente, commit e push come in
   `/costruisci`. Fatto quando la CI su GitHub e' verde.
