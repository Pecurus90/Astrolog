/** I testi di **Impostazioni > Scansioni** (tavola v82, `SezioneServizi`): le scansioni passate,
 * cosa e' entrato, cosa e' rimasto fuori e perche'.
 *
 * File suo perche' sono quasi tutti **traduzioni di codici** che il backend manda (`GET /scans`):
 * chi va a correggerne uno non deve scorrere i testi di tutta la pagina.
 */
export const itLetture = {
  "settings.scans.intro":
    "Le scansioni passate, la più recente in alto: quanto è durata, cosa è entrato, cosa è rimasto fuori e perché.", // glifo-ok: testo della tavola
  "settings.scans.failed": "Scansioni non disponibili.",
  "settings.scans.none": "Nessuna scansione ancora",
  "settings.scans.none.how": "Aggiungi una cartella in «Cartelle e scansione» e avvia la prima.", // glifo-ok: testo della tavola
  "settings.scans.when": "{giorno}, {ora}",
  "settings.scans.now": "adesso",
  "settings.scans.more": "Mostra le scansioni precedenti",
  // L'esito di un gesto, tradotto: il codice non arriva mai a schermo.
  "settings.scans.completed": "completata",
  "settings.scans.stopped": "interrotta a mano",
  "settings.scans.blocked": "bloccata",
  "settings.scans.running": "in corso",
  "settings.scans.running.pct": "in corso · {pct}%", // glifo-ok: testo della tavola
  "settings.scans.folders": "Cartelle",
  "settings.scans.entered": "Entrati",
  "settings.scans.entered.n": "{n} frame",
  "settings.scans.entered.read": "{letti} file letti su {su}",
  "settings.scans.leftOut": "Rimasti fuori",
  "settings.scans.unread": "Non leggibili · {n}", // glifo-ok: testo della tavola
  "settings.scans.unread.all": "Mostra tutti i {n}",
  "settings.scans.unread.gone":
    "L'elenco dei file non leggibili è conservato solo per l'ultima scansione di ogni cartella.", // glifo-ok: testo della tavola
  "settings.scans.unread.failed": "Elenco dei file non disponibile.",
  "settings.scans.reason": "Motivo",
  "settings.scans.stop": "Interrompi",
  "settings.scans.retry": "Riprova",
  // Perche' si e' bloccata; `{cartella}` e' il percorso.
  "settings.scans.why.root_unreachable":
    "La cartella {cartella} non risponde: lettura non completata. Controlla il disco e riprova; riparte da dove si era fermata.",
  "settings.scans.why.internal_error": "Errore interno durante la lettura di {cartella}: dettagli nel log.",
  "settings.scans.why.database_error": "Il database non ha risposto durante la lettura di {cartella}: dettagli nel log.",
  "settings.scans.why.left_open":
    "AstroLog si è chiuso durante la lettura di {cartella}. Riprova; riparte da dove si era fermata.", // glifo-ok: testo della tavola
  // I file trovati che non sono entrati, col perche'.
  "settings.scans.out.unchanged": "{n} già in archivio", // glifo-ok: testo della tavola
  "settings.scans.out.duplicates": "{n} duplicati",
  "settings.scans.out.duplicates.one": "1 duplicato",
  "settings.scans.out.calibration": "{n} di calibrazione (dark, flat, bias)",
  "settings.scans.out.rewritten": "{n} elaborati da un altro programma (calibrati o integrati)",
  "settings.scans.out.rewritten.one": "1 elaborato da un altro programma (calibrato o integrato)",
  "settings.scans.out.not_supported": "{n} di un programma non supportato",
  "settings.scans.out.not_supported.one": "1 di un programma non supportato",
  "settings.scans.out.still_writing": "{n} ancora in scrittura",
  "settings.scans.out.online_only": "{n} solo online, non scaricati",
  "settings.scans.out.online_only.one": "1 solo online, non scaricato",
  // Le cartelle lasciate fuori, ognuna col suo perche'.
  "settings.scans.dir.unreadable": "{percorso}: cartella non leggibile",
  "settings.scans.dir.hidden": "{percorso}: cartella nascosta, ignorata",
  // Perche' un file non si e' potuto leggere.
  "settings.scans.file.file_unreadable": "file non apribile",
  "settings.scans.file.header_unreadable": "non è un FITS o l'intestazione è rovinata", // glifo-ok: testo della tavola
  "settings.scans.file.name_not_utf8": "nome del file non valido (non UTF-8)",
  "settings.scans.file.internal_error": "errore interno: dettagli nel log",
}
