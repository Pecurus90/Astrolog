/** I testi delle **letture**: le scansioni passate, e cosa e' rimasto fuori.
 *
 * File suo perche' sono tanti -- un esito, un motivo per cui una corsa si e' fermata, un motivo
 * per ogni file non letto e per ogni file saltato -- e sono quasi tutti **traduzioni di codici**
 * che il backend manda: chi va a correggerne uno non deve scorrere i testi di tutta la pagina.
 */
export const itLetture = {
  "settings.readings.title": "Cronologia delle scansioni",
  "settings.readings.what":
    "Per ogni scansione: file letti, file esclusi e motivo.",
  "settings.readings.failed": "Scansioni non disponibili.",
  "settings.readings.none": "Nessuna scansione",
  "settings.readings.none.why":
    "Aggiungi una cartella e avvia la scansione.",
  "settings.readings.running": "in corso",
  "settings.readings.more": "Mostra le scansioni precedenti",
  // L'esito di una corsa, tradotto: il codice non arriva mai a schermo.
  "settings.readings.ok": "completata",
  "settings.readings.stopped": "interrotta dall'utente",
  "settings.readings.aborted": "interrotta",
  "settings.readings.error": "errore",
  // Perche' si e' fermata. `stop_requested` non compare: lo dice gia' "fermata da te".
  "settings.readings.why.root_unreachable": "cartella non raggiungibile",
  "settings.readings.why.internal_error": "errore interno: dettagli nel log",
  "settings.readings.why.database_error": "errore del database: dettagli nel log",
  // I numeri della ricevuta. Si mostrano **solo quelli sopra zero** tranne i nuovi: "0 nuovi" e'
  // la risposta alla domanda che si sta facendo chi guarda, gli altri zeri sono rumore.
  "settings.readings.found": "{n} file esaminati",
  "settings.readings.found.one": "1 file esaminato",
  "settings.readings.new": "{n} nuovi",
  "settings.readings.new.one": "1 nuovo",
  "settings.readings.unchanged": "{n} gi\u00e0 in archivio",
  "settings.readings.duplicates": "{n} duplicati",
  "settings.readings.duplicates.one": "1 duplicato",
  "settings.readings.missing": "{n} non pi\u00f9 su disco",
  "settings.readings.missing.one": "1 non pi\u00f9 su disco",
  "settings.readings.skipped": "{n} esclusi",
  "settings.readings.skipped.one": "1 escluso",
  "settings.readings.errors": "{n} non leggibili",
  "settings.readings.errors.one": "1 non leggibile",
  "settings.readings.online_only": "{n} solo online",
  "settings.readings.leftOut": "File esclusi",
  // Perche' un file e' stato saltato: e' una scelta dell'app, non un guasto.
  "settings.readings.skip.calibration": "{n} di calibrazione (dark, flat, bias)",
  "settings.readings.skip.stack": "{n} immagini integrate (stack)",
  "settings.readings.skip.stack.one": "1 immagine integrata (stack)",
  "settings.readings.skip.still_writing": "{n} ancora in scrittura",
  // Perche' un file non si e' potuto leggere: qui invece qualcosa non ha funzionato.
  "settings.readings.error.file_unreadable": "file non apribile",
  "settings.readings.error.header_unreadable": "non \u00e8 un FITS o header non valido",
  "settings.readings.error.name_not_utf8": "nome del file non valido (non UTF-8)",
  "settings.readings.error.internal_error": "errore interno: dettagli nel log",
  "settings.readings.files": "File non leggibili",
  "settings.readings.filesGone":
    "L'elenco dei file non leggibili \u00e8 conservato solo per l'ultima scansione di ogni cartella.",
  "settings.readings.filesFailed": "Elenco dei file non disponibile.",
  "settings.readings.filesMore": "Mostra altri file",
  // Le cartelle lasciate fuori, ognuna col suo perche'.
  "settings.readings.unreadable_dirs": "non leggibile",
  "settings.readings.hidden_dirs": "nascosta, ignorata",
  "settings.readings.linked_dirs": "collegamento simbolico, non seguito",
}
