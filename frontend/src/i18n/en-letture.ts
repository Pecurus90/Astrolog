/** Texts of **Settings > Scans** (board v82, `SezioneServizi`): past scans, what went in, what was
 * left out and why.
 *
 * Its own file because most of them are **translations of codes** sent by the backend (`GET /scans`).
 */
export const enLetture = {
  "settings.scans.intro":
    "Past scans, the most recent on top: how long it took, what went in, what was left out and why.", // glifo-ok: board text
  "settings.scans.failed": "Scans not available.",
  "settings.scans.none": "No scans yet",
  "settings.scans.none.how": "Add a folder in “Folders and scan” and start the first one.", // glifo-ok: board text
  "settings.scans.when": "{giorno}, {ora}",
  "settings.scans.now": "now",
  "settings.scans.more": "Show earlier scans",
  "settings.scans.completed": "completed",
  "settings.scans.stopped": "stopped by hand",
  "settings.scans.blocked": "blocked",
  "settings.scans.running": "running",
  "settings.scans.running.pct": "running · {pct}%", // glifo-ok: board text
  "settings.scans.folders": "Folders",
  "settings.scans.entered": "Went in",
  "settings.scans.entered.n": "frames: {n}",
  "settings.scans.entered.read": "{letti} files read out of {su}",
  "settings.scans.leftOut": "Left out",
  "settings.scans.unread": "Unreadable · {n}", // glifo-ok: board text
  "settings.scans.unread.all": "Show all {n}",
  "settings.scans.unread.gone":
    "The list of unreadable files is kept only for the latest scan of each folder.", // glifo-ok: board text
  "settings.scans.unread.failed": "File list not available.",
  "settings.scans.reason": "Reason",
  "settings.scans.stop": "Stop",
  "settings.scans.retry": "Try again",
  "settings.scans.why.root_unreachable":
    "The folder {cartella} is not responding: reading not completed. Check the drive and try again; it resumes where it stopped.",
  "settings.scans.why.internal_error": "Internal error while reading {cartella}: details in the log.",
  "settings.scans.why.database_error": "The database did not respond while reading {cartella}: details in the log.",
  "settings.scans.why.left_open":
    "AstroLog closed while reading {cartella}. Try again; it resumes where it stopped.", // glifo-ok: board text
  "settings.scans.out.unchanged": "{n} already in the archive", // glifo-ok: board text
  "settings.scans.out.duplicates": "{n} duplicates",
  "settings.scans.out.duplicates.one": "1 duplicate",
  "settings.scans.out.calibration": "{n} calibration (dark, flat, bias)",
  "settings.scans.out.rewritten": "{n} processed by another program (calibrated or stacked)",
  "settings.scans.out.rewritten.one": "1 processed by another program (calibrated or stacked)",
  "settings.scans.out.not_supported": "{n} from an unsupported program",
  "settings.scans.out.not_supported.one": "1 from an unsupported program",
  "settings.scans.out.still_writing": "{n} still being written",
  "settings.scans.out.online_only": "{n} online only, not downloaded",
  "settings.scans.out.online_only.one": "1 online only, not downloaded",
  "settings.scans.dir.unreadable": "{percorso}: folder not readable",
  "settings.scans.dir.hidden": "{percorso}: hidden folder, ignored",
  "settings.scans.file.file_unreadable": "file cannot be opened",
  "settings.scans.file.header_unreadable": "not a FITS file or the header is damaged", // glifo-ok: board text
  "settings.scans.file.name_not_utf8": "invalid file name (not UTF-8)",
  "settings.scans.file.internal_error": "internal error: details in the log",
}
