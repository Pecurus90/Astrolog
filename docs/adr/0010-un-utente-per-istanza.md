# 0010 -- Un utente per istanza, con piu' siti e piu' setup

**Stato:** accettata

## Contesto

Un astrofotografo riprende da piu' posti e con piu' setup. Due persone sotto lo stesso tetto
possono avere un NAS solo.

## Decisione

- **Un'istanza dell'app e' di un utente**, che puo' avere piu' siti e piu' setup.
- **Due persone sullo stesso NAS = due istanze**, con due cartelle dati.

## Conseguenze

- Nessun login e nessuna separazione per utente dentro il database (0002).
