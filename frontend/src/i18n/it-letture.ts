/** I testi delle **letture**: le scansioni passate, e cosa e' rimasto fuori.
 *
 * File suo perche' sono tanti -- un esito, un motivo per cui una corsa si e' fermata, un motivo
 * per ogni file non letto e per ogni file saltato -- e sono quasi tutti **traduzioni di codici**
 * che il backend manda: chi va a correggerne uno non deve scorrere i testi di tutta la pagina.
 */
export const itLetture = {
  "settings.readings.title": "Cosa ho letto, e quando",
  "settings.readings.what":
    "Di ogni volta che ho letto le tue cartelle resta scritto cosa e' entrato, cosa e' rimasto fuori e perche'. Serve a rispondere alla domanda che viene dopo una scansione: ha funzionato?",
  "settings.readings.failed": "Non riesco a leggere le letture.",
  "settings.readings.none": "Nessuna lettura, per ora",
  "settings.readings.none.why":
    "Una lettura nasce quando l'app legge le tue cartelle. Indica almeno una cartella qui accanto, poi premi Scansiona in alto: la prima comparira' qui.",
  "settings.readings.running": "sta leggendo adesso",
  "settings.readings.more": "Mostra le letture precedenti",
  // L'esito di una corsa, tradotto: il codice non arriva mai a schermo.
  "settings.readings.ok": "letta tutta",
  "settings.readings.stopped": "fermata da te",
  "settings.readings.aborted": "fermata",
  "settings.readings.error": "guasto",
  // Perche' si e' fermata. `stop_requested` non compare: lo dice gia' "fermata da te".
  "settings.readings.why.root_unreachable": "la cartella non rispondeva piu'",
  "settings.readings.why.internal_error": "un guasto dell'app: la traccia e' nel diario",
  "settings.readings.why.database_error": "un guasto dell'archivio: la traccia e' nel diario",
  // I numeri della ricevuta. Si mostrano **solo quelli sopra zero** tranne i nuovi: "0 nuovi" e'
  // la risposta alla domanda che si sta facendo chi guarda, gli altri zeri sono rumore.
  "settings.readings.found": "{n} file guardati",
  "settings.readings.found.one": "1 file guardato",
  "settings.readings.new": "{n} nuovi",
  "settings.readings.new.one": "1 nuovo",
  "settings.readings.unchanged": "{n} gia' in archivio",
  "settings.readings.duplicates": "{n} doppioni",
  "settings.readings.duplicates.one": "1 doppione",
  "settings.readings.missing": "{n} spariti dal disco",
  "settings.readings.missing.one": "1 sparito dal disco",
  "settings.readings.skipped": "{n} saltati",
  "settings.readings.skipped.one": "1 saltato",
  "settings.readings.errors": "{n} non letti",
  "settings.readings.errors.one": "1 non letto",
  "settings.readings.online_only": "{n} solo online",
  "settings.readings.leftOut": "cosa e' rimasto fuori",
  // Perche' un file e' stato saltato: e' una scelta dell'app, non un guasto.
  "settings.readings.skip.calibration": "{n} di calibrazione (dark, flat, bias)",
  "settings.readings.skip.stack": "{n} somme di piu' pose",
  "settings.readings.skip.stack.one": "1 somma di piu' pose",
  "settings.readings.skip.still_writing": "{n} ancora in scrittura",
  // Perche' un file non si e' potuto leggere: qui invece qualcosa non ha funzionato.
  "settings.readings.error.file_unreadable": "il sistema non l'ha aperto",
  "settings.readings.error.header_unreadable": "non e' un FITS, o il suo header e' rotto",
  "settings.readings.error.name_not_utf8": "il suo nome ha caratteri che non so scrivere",
  "settings.readings.error.internal_error": "un guasto dell'app: la traccia e' nel diario",
  "settings.readings.files": "I file che non ho letto",
  "settings.readings.filesGone":
    "Questa lettura non tiene piu' l'elenco dei file non letti: lo tiene l'ultima di ogni cartella, e -- se quella si e' fermata a meta' -- anche l'ultima arrivata in fondo.",
  "settings.readings.filesFailed": "Non riesco a leggere l'elenco dei file non letti.",
  "settings.readings.filesMore": "Mostra altri file",
  // Le cartelle lasciate fuori, ognuna col suo perche'.
  "settings.readings.unreadable_dirs": "non si sono potute leggere",
  "settings.readings.hidden_dirs": "nascoste, e le ho lasciate stare",
  "settings.readings.linked_dirs": "raggiunte da un collegamento: non l'ho seguito",
}
