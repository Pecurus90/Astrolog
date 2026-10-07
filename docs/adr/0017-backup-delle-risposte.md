# 0017 -- Il backup delle risposte: un file accanto al database, riscritto a ogni risposta

**Stato:** accettata, 7/10/2026 (Marco).

## Contesto

Cio' che l'utente dice all'app (attrezzatura, oggetti, tipi di file, siti, mosaici, preferenze)
sta nella sezione DICHIARATO di `schema.sql`, che "sopravvive ai reset, si esporta", ma niente lo
esportava: un database perso o ricreato voleva dire rispondere tutto da capo. Le dichiarazioni
sono gia' agganciate a chiavi stabili (impronta del frame, grafia dell'header, nomi, percorsi);
`instruments`, `filters`, `sites`, `folders` hanno id di riga da rilegare per nome.

## Decisione

- **Un file**, `risposte.json` accanto al database, scritto per intero e in modo atomico (file
  temporaneo, poi rinomina) dopo ogni scrittura dell'utente andata a buon fine: Applica,
  attrezzatura, impostazioni, chiave Meteoblue, siti, cartelle e spostamento di cartella. Una
  regola sola sugli indirizzi (`api/backup.is_user_write`, in un middleware), non una chiamata per
  rotta; mai dagli stadi della spina.
- **Import senza dipendenze nuove**: la pagina legge il file e ne manda il contenuto JSON.
- **Cosa contiene**, ognuno per la sua chiave stabile: `config` (le chiavi segrete si', perche' il
  database accanto le ha gia' in chiaro); `sites` per nome, con quota e cielo e la loro provenienza
  (cosi' il ripristino non chiede niente alla rete; il fuso si ricalcola dalle coordinate); `folders` per percorso, con nome, ritiro e un campione di riconoscimento (fino a 5
  coppie percorso relativo -> impronta); `instruments` scritti dall'utente (`detected = 0`) per
  (genere, nome); `filters` e bande per nome; `header_aliases`; tutte le `declarations`. Niente di
  derivato: frame, corredi, oggetti, notti, meteo, catalogo si rifanno dai file.
- **Ripristino proposto, mai automatico**: un database senza risposte (nuovo, o ricreato da
  `tools/reset_db.py` prima dell'avvio), con il file accanto, fa chiedere "Ho trovato le tue risposte del <data>: le rimetto?". Si rimette in quest'ordine:
  `config`, `sites`, `folders`, `instruments`, `filters`, `header_aliases`, `declarations`, poi i
  corredi dichiarati (`rigs.restore_declared`). La scansione rifa' il resto.
- **Cartelle su un'altra macchina**: la riga torna anche se il percorso non c'e', col suo campione
  (`folders.sample_json`); lo spostamento di M2 riconosce la cartella dal campione quando non ha
  ancora frame, cosi' "aggiungi la cartella nel posto nuovo" porta le risposte.
- **Esporta e Importa a mano** in Impostazioni, per un'altra macchina: lo stesso file **senza le
  chiavi segrete** (Marco) e senza `astap_path`: un percorso dichiarato vince sulla ricerca
  automatica, e sbagliato sull'altra macchina la ferma. L'importazione e' lo stesso ripristino.
- **Il file non va mai nella Diagnostica** (ADR 0008).

## Conseguenze

- Un reset o una reinstallazione non costano piu' le risposte; il file sopravvive a
  `tools/reset_db.py`, che cancella solo il database.
- Una risposta su un mosaico torna solo se la nuova lettura sceglie lo stesso frame piu' vecchio
  come chiave (date uguali): rischio dichiarato.
