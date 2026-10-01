# 0008 -- Una pagina Diagnostica, nessuna telemetria

**Stato:** accettata

## Contesto

Chi usa l'app su attrezzature e archivi che non conosciamo deve poter dire cosa non va, senza che
l'app mandi niente da sola.

## Decisione

- **Nessuna telemetria, per costruzione**: le segnalazioni le fa l'utente, a mano.
- Una pagina **Diagnostica con un bottone "copia"**: versione, sistema, percorsi, cosa il solver
  non ha risolto e perche', gli ultimi errori del log, senza dati personali. Il log e' ruotato,
  accanto al database.

## Conseguenze

- La Diagnostica raccoglie anche i frame che uno stadio ha segnato `failed`, che oggi restano nel
  residuo (`backend/astrolog/spine/group.py`).
- La pagina nasce col pacchetto (`docs/coda.md`, *Nasce con*).
