---
name: schema-unico
description: Usa quando tocchi backend/astrolog/schema.sql, aggiungi una tabella o una colonna, o stai per scrivere una migrazione, un ALTER TABLE o un backfill. Dice che lo schema e' uno, che non esistono migrazioni fino al rilascio, e che ogni tabella dichiara se e' dichiarato o derivato.
---

# Uno schema, niente migrazioni

**`backend/astrolog/schema.sql` e' l'unica verita' del database.** Si cambia il file, si
lancia `tools/reset_db.py`, il DB rinasce. Pre-commit blocca `CREATE`/`ALTER`/`DROP
TABLE` in un `.py` di `backend/astrolog`: se stai per scriverne uno, stai per aprire una seconda casa. Un'eccezione
legittima si marca `# ddl-ok: <perche'>` sulla riga: una `CREATE TEMP TABLE` di appoggio -- che vive nella connessione,
sparisce con lei e non e' una casa (`db/idlist.py`, gli id di una `WHERE ... IN` quando sono
decine di migliaia). Una `CREATE TABLE` vera resta vietata: quella sta in `schema.sql`.

**Fino al rilascio non esistono migrazioni, backfill, ne' compatibilita' col DB di ieri**
(principio 3). Se ti viene da scrivere "aggiungo la colonna se manca", fermati: cambia lo
schema e ricrea. Le migrazioni nasceranno alla versione 1.0, e solo allora.

**Ogni tabella dice se e' dichiarato o derivato**, in un commento in testa alla `CREATE`:

- **derivato** -- l'app lo ricava dai FITS o dal catalogo e lo puo' ricalcolare: frame,
  geometria risolta, sessioni, raggruppamenti, metriche;
- **dichiarato** -- l'utente lo ha *detto* e non si perde mai: nomi dati agli oggetti,
  correzioni a filtri e strumenti, siti, piani. E' cio' che si esporta e rientra su un DB
  nuovo. Una tabella che mescola i due sta sbagliando forma.

**Ogni colonna ha il suo perche' accanto**, in una riga: e' l'unico posto dove il perche'
controintuitivo di un vincolo sopravvive. Un `CHECK` protegge un invariante che il codice
non puo' garantire da solo; un vincolo che il codice gia' garantisce e' rumore.

**Le chiavi sono stabili.** Cio' che il dichiarato riferisce (un oggetto, un corredo) ha
una chiave che non cambia quando il derivato si ricalcola: altrimenti il reimport delle
dichiarazioni non ritrova a cosa agganciarsi.

**SQLite ha quattro condizioni, e sono nel contratto della spina**: `STRICT` sulle tabelle;
WAL; **un solo scrittore** (il worker: chi risolve o misura in un altro processo restituisce
i risultati al worker, non li scrive); e il file **mai su una condivisione di rete** (SMB,
NFS): il locking li' corrompe. Sul NAS il DB sta sul volume locale del container, i FITS
sulla condivisione.

**La geometria sul cielo ha un indice deciso una volta**: R\*Tree a tre dimensioni sul
vettore unitario (x, y, z) del centro -- niente salto a RA 0/360, niente problema ai poli;
la ricerca a cono e' un box piu' un prodotto scalare. Il footprint di un frame sono i suoi
quattro angoli, nello stesso indice.

**I test creano il DB da `schema.sql`**, in un file temporaneo, via la fixture comune
(`test-sulla-logica`). Se un test ha bisogno di uno schema diverso, il problema e' lo
schema.
