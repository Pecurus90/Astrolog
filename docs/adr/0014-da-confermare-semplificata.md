# 0014 -- Da confermare semplificata: meno famiglie di domande, chiavi che non si spostano

**Stato:** accettata, 5/10/2026

## Contesto

Da confermare ha dieci famiglie di domande (`ReviewOut`, `api/models_review.py`), ognuna con un
suo modo di raggruppare i frame e un suo codice di scrittura. Tre chiedono l'attrezzatura
(senza camera, senza ottica, senza filtro), due l'oggetto (Oggetti, Senza nome); le risposte di
senza camera e senza nome hanno la notte nella chiave, e cambiare il fuso di casa le divide e le
riunisce (`spine/home_nights.py`). Una lettura critica del disegno (`docs/coda.md`, *Semplificare
e completare la spina*) ha trovato che lo stesso risultato si ottiene con meno.

## Decisione

- **S1 -- Una domanda sull'attrezzatura.** Senza camera, senza ottica e senza filtro diventano
  una domanda sola per **firma dell'header** (grafia di camera e telescopio, focale, dimensioni
  del sensore), che risponde corredo e filtro insieme. Si accetta di perdere il caso raro della
  stessa firma con attrezzature diverse in notti diverse.
- **S2 -- Chiavi che non si spostano.** Le risposte non portano la notte nella chiave: si
  agganciano alla firma dell'header o ai frame fissati al momento della risposta. Sparisce il
  lavoro di `home_nights` sul fuso di casa; si accetta di perdere parte del "vale anche per i
  frame futuri di quella notte".
- **S3 -- Una scheda per gruppo di frame per l'oggetto**, coi candidati del cielo (anche zero), al
  posto di Oggetti e Senza nome.
- **S4 -- Applica conferma solo cio' a cui si e' risposto**, e un oggetto che il cielo riconosce
  con certezza non si chiede. Si perde l'avviso degli oggetti nuovi (`ReviewSeen`).

## Conseguenze

- Si fanno **prima della fase 2 del refactor**: riscrivono i moduli delle domande (`rigless`,
  `unnamed`, `unfiltered`, `rig_optics`, `night_rig`, `home_nights`, `object_answer` e le loro
  rotte), che la fase 2 altrimenti pulirebbe per poi buttare.
- Cambiano i contratti in `docs/domini/spina.md` e la guida (`docs/guida-utente.md`), nello
  stesso diff di ciascuna; il database si ricrea (`schema.sql`, nessuna migrazione).
- Diventa possibile il backup delle risposte (M5), agganciato a chiavi che non cambiano.
- La pagina si ridisegna col disegno nuovo ([ADR 0012](0012-il-disegno-viene-da-claude-design.md)):
  il backend manda le domande nuove, lo schermo le veste quando arriva il disegno.
