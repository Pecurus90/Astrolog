/** I testi delle **letture**: le scansioni passate, e cosa e' rimasto fuori.
 *
 * File suo perche' sono tanti -- un esito, un motivo per cui una corsa si e' fermata, un motivo
 * per ogni file non letto e per ogni file saltato -- e sono quasi tutti **traduzioni di codici**
 * che il backend manda: chi va a correggerne uno non deve scorrere i testi di tutta la pagina.
 */
export const enLetture = {
  "settings.readings.title": "Scan history",
  "settings.readings.what":
    "For each scan: files read, files excluded and why.",
  "settings.readings.failed": "Scans not available.",
  "settings.readings.none": "No scans",
  "settings.readings.none.why":
    "Add a folder and start the scan.",
  "settings.readings.running": "running",
  "settings.readings.more": "Show earlier scans",
  "settings.readings.ok": "completed",
  "settings.readings.stopped": "stopped by the user",
  "settings.readings.aborted": "stopped",
  "settings.readings.error": "error",
  "settings.readings.why.root_unreachable": "folder not reachable",
  "settings.readings.why.internal_error": "internal error: details in the log",
  "settings.readings.why.database_error": "database error: details in the log",
  "settings.readings.found": "{n} files examined",
  "settings.readings.found.one": "1 file examined",
  "settings.readings.new": "{n} new",
  "settings.readings.new.one": "1 new",
  "settings.readings.unchanged": "{n} already in the archive",
  "settings.readings.duplicates": "{n} duplicates",
  "settings.readings.duplicates.one": "1 duplicate",
  "settings.readings.missing": "{n} no longer on disk",
  "settings.readings.missing.one": "1 no longer on disk",
  "settings.readings.skipped": "{n} excluded",
  "settings.readings.skipped.one": "1 excluded",
  "settings.readings.errors": "{n} unreadable",
  "settings.readings.errors.one": "1 unreadable",
  "settings.readings.online_only": "{n} online only",
  "settings.readings.leftOut": "Excluded files",
  "settings.readings.skip.calibration": "{n} calibration (dark, flat, bias)",
  "settings.readings.skip.stack": "{n} stacked images",
  "settings.readings.skip.stack.one": "1 stacked image",
  "settings.readings.skip.still_writing": "{n} still being written",
  "settings.readings.error.file_unreadable": "file cannot be opened",
  "settings.readings.error.header_unreadable": "not a FITS file or invalid header",
  "settings.readings.error.name_not_utf8": "invalid file name (not UTF-8)",
  "settings.readings.error.internal_error": "internal error: details in the log",
  "settings.readings.files": "Unreadable files",
  "settings.readings.filesGone":
    "The list of unreadable files is kept only for the latest scan of each folder.",
  "settings.readings.filesFailed": "File list not available.",
  "settings.readings.filesMore": "Show more files",
  "settings.readings.unreadable_dirs": "unreadable",
  "settings.readings.hidden_dirs": "hidden, ignored",
  "settings.readings.linked_dirs": "symbolic link, not followed",
}
