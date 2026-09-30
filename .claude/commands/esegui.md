---
description: Porta un lavoro dal piano al riassunto finale senza fermarsi - piano e domande, costruzione con i documenti, poi il Workflow esegui (revisione fino a vuoto, audit eseguendo, controlli verdi). Il commit lo fa dopo l'ok di Marco.
argument-hint: [cosa vuoi]
---

**Lavoro:** $ARGUMENTS

Vale `CLAUDE.md`. Il giro e' questo, e non si salta un passo.

1. **Ricognizione.** `esploratore` (o grep diretto se sai gia' dove): cosa esiste e si riusa,
   cosa e' nuovo, cosa rischia. Se viene da `docs/coda.md`, ri-misura lo stato.
2. **Piano in cinque righe** -- Contesto / Obiettivo / Lavoro / Vincoli / Fatto quando -- con
   `mode`: `meccanico` (potare, tipizzare: serve giudizio, lo `sviluppatore` su Opus),
   `spostamento` (spostare file, rinominare, aggiornare import: lo `sviluppatore` su Sonnet) o
   `logica` (dominio: lo scrivo io), e `surface` se cambia cio' che l'utente vede.
3. **Domande a Marco, solo se servono, prima di scrivere codice**: quando la risposta dipende da
   lui (gusto, dati suoi, rischio che accetta). A video, a scelta multipla, la consigliata in cima
   -- la piu' corretta, anche se costa piu' lavoro, e si dice quanto. Un difetto non e' una
   domanda: si ripara. Il piano si mostra a Marco solo se cambia cio' che vede.
4. **Se `logica`, costruisco io**: test visti rossi, codice, e i documenti nello stesso diff --
   `docs/guida-utente.md` se cambia cio' che l'utente vede, il contratto in `docs/domini/`,
   `docs/coda.md` (chiuso -> sparisce, debito nuovo -> Parcheggio), un ADR in `docs/adr/` per una
   decisione nuova, `backend/astrolog/schema.sql`. Una pagina finita -> il `traduttore`. Ogni
   file nuovo: `git add -N <file>`, senno' revisione e controlli non lo vedono.
5. **Workflow `esegui`** con `args: {task, plan, mode, surface, answers, history}`. In
   `meccanico` e `spostamento` costruisce lo `sviluppatore`, documenti compresi. Poi, a cicli: revisione
   (revisore + pr-review-toolkit) finche' un giro torna vuoto, audit (`auditore`, una domanda
   alla volta, eseguendo), tutti i controlli; se l'audit o i controlli fanno correggere, si torna
   alla revisione. Esiti:
   - `done`: al punto 6.
   - `question`: la domanda va a Marco come al punto 3; si rilancia aggiungendo la risposta ad
     `answers` e passando la `history` restituita (il lavoro fatto resta nel diff).
   - `failed`, `not_dry`, `audit_failing`, `checks_failing`: si dice a Marco cosa si e' fermato e
     dove. Niente commit.
6. **Riassunto a Marco**, cinque righe, aprendo con *cosa funziona ora e prima no*: poi l'esito
   della revisione (giri, rilievi scartati e perche'), dell'audit, dei controlli. Ogni cosa tolta
   si spiega in una riga.
7. **Dopo l'ok di Marco:** `git status` (un'altra sessione puo' aver messo in staging),
   `git add <file uno per uno>`, `git commit -m "<tipo>: <una riga ASCII>"` (Conventional
   Commits: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`), `git push origin main`.
