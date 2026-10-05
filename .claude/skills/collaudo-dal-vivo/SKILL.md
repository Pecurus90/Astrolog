---
name: collaudo-dal-vivo
description: Usa quando una fetta tocca una superficie (una pagina, un modale, un controllo) e devi collaudarla davvero prima di dichiararla fatta, o quando devi misurare un CSS. Dice come si avvia l'app per il collaudo, con quale DB, cosa si guarda nel browser, e come si misura senza farsi ingannare.
---

# Collaudo dal vivo

**Una superficie mai aperta non e' fatta.** Leggere il codice trova cio' che il codice dice;
guidare l'app trova cio' che fa. Il collaudo e' un passo delle ricette (`/costruisci`, `/ripara`), non
un'abitudine.

**Come si avvia.** Isolata: `npm --prefix frontend run build`, poi `python -m astrolog` con
`ASTROLOG_PORT` libera e `ASTROLOG_DATA_DIR` in una cartella temporanea (`tools/dev.py` e' per
Marco: avvia il backend sulla porta 8765 con la sua cartella dati, cioe' il suo DB). Le regole:

- **mai sull'archivio vero di Marco.** Si usa una **copia di collaudo** del DB (o un DB
  ricreato da `schema.sql` su un archivio di prova). I FITS originali non si toccano mai,
  nemmeno in lettura se il collaudo puo' scrivere accanto a loro.
- **il backend che gira ha il codice di quando e' partito.** Dopo una modifica al backend
  si riavvia, altrimenti si collauda il vecchio. Il frontend di sviluppo si ricarica da
  solo; il backend no.
- **si collauda in un browser vero**, con gli strumenti che ci sono, e si chiude cio' che
  si e' aperto.

**Cosa si guarda.**

- **il contenuto, non i pulsanti**: che i numeri siano quelli attesi, che le celle che
  tacciono dicano perche', che uno stato vuoto sia lo stato giusto (primo avvio, zero
  frame, nessun sito) e non un guasto;
- **la console**: zero errori e zero chiavi di traduzione grezze a schermo;
- **le tre forme del dato**: pieno, vuoto, "non so". Se una non si puo' provare
  sull'archivio di collaudo, si prova cambiando un dato **sulla copia** e poi si rimette
  com'era -- e lo si dice nel resoconto;
- **da chi non e' Marco**: un nome di filtro diverso, un header senza `RA`, un percorso
  con spazi. Se l'archivio di collaudo non li ha, e' un collaudo a meta', e va detto.

**Ingrandire prima di dire "rotto".** Uno screenshot intero non basta per un numero da
11 px: si ingrandisce la regione e si legge davvero.

**Misurare il CSS senza farsi ingannare.** Ridimensionare la finestra dallo strumento di
automazione **non e' affidabile**: dice "fatto" e non cambia niente. Una container query
si misura **restringendo il contenitore** (uno stile inline sul suo genitore); una media
query si misura **iniettando le regole** del ramo stretto senza l'involucro `@media`. E si
legge il **valore calcolato** (`getComputedStyle`), non il sorgente: il sorgente dice cosa
si voleva, il calcolato dice cosa c'e'.

**Cosa si riporta.** Cosa funziona ora e prima no, con la prova (uno screenshot ingrandito,
un valore letto); cosa non si e' potuto provare, e perche'.
