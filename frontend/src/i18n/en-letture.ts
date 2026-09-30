/** I testi delle **letture**: le scansioni passate, e cosa e' rimasto fuori.
 *
 * File suo perche' sono tanti -- un esito, un motivo per cui una corsa si e' fermata, un motivo
 * per ogni file non letto e per ogni file saltato -- e sono quasi tutti **traduzioni di codici**
 * che il backend manda: chi va a correggerne uno non deve scorrere i testi di tutta la pagina.
 */
export const enLetture = {
  "settings.readings.title": "What I read, and when",
  "settings.readings.what":
    "Of every time I read your folders, what came in, what stayed out and why stays written down. It answers the question that comes after a scan: did it work?",
  "settings.readings.failed": "I can't read the readings.",
  "settings.readings.none": "No readings yet",
  "settings.readings.none.why":
    "A reading is born when the app reads your folders. Add at least one folder next door, then press Scan at the top: the first one will appear here.",
  "settings.readings.running": "reading right now",
  "settings.readings.more": "Show earlier readings",
  "settings.readings.ok": "read in full",
  "settings.readings.stopped": "stopped by you",
  "settings.readings.aborted": "stopped",
  "settings.readings.error": "fault",
  "settings.readings.why.root_unreachable": "the folder stopped answering",
  "settings.readings.why.internal_error": "a fault in the app: the trace is in the log",
  "settings.readings.why.database_error": "a fault in the archive: the trace is in the log",
  "settings.readings.found": "{n} files looked at",
  "settings.readings.found.one": "1 file looked at",
  "settings.readings.new": "{n} new",
  "settings.readings.new.one": "1 new",
  "settings.readings.unchanged": "{n} already in the archive",
  "settings.readings.duplicates": "{n} duplicates",
  "settings.readings.duplicates.one": "1 duplicate",
  "settings.readings.missing": "{n} gone from the disk",
  "settings.readings.missing.one": "1 gone from the disk",
  "settings.readings.skipped": "{n} skipped",
  "settings.readings.skipped.one": "1 skipped",
  "settings.readings.errors": "{n} not read",
  "settings.readings.errors.one": "1 not read",
  "settings.readings.online_only": "{n} online only",
  "settings.readings.leftOut": "what stayed out",
  "settings.readings.skip.calibration": "{n} calibration (dark, flat, bias)",
  "settings.readings.skip.stack": "{n} stacks of several shots",
  "settings.readings.skip.stack.one": "1 stack of several shots",
  "settings.readings.skip.still_writing": "{n} still being written",
  "settings.readings.error.file_unreadable": "the system did not open it",
  "settings.readings.error.header_unreadable": "not a FITS, or its header is broken",
  "settings.readings.error.name_not_utf8": "its name has characters I cannot write",
  "settings.readings.error.internal_error": "a fault in the app: the trace is in the log",
  "settings.readings.files": "The files I did not read",
  "settings.readings.filesGone":
    "This reading no longer keeps the list of files it did not read: the latest one of each folder does, and -- if that one stopped halfway -- so does the last one that made it to the end.",
  "settings.readings.filesFailed": "I can't read the list of files not read.",
  "settings.readings.filesMore": "Show more files",
  "settings.readings.unreadable_dirs": "could not be read",
  "settings.readings.hidden_dirs": "hidden, and I left them alone",
  "settings.readings.linked_dirs": "reached through a link: I did not follow it",
}
