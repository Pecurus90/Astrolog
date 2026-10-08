/** I testi del **riconoscitore**: cosa cambia senza, dove si prende, e dove dirgli che sta.
 *
 * File suo perche' li usano in due -- il primo avvio, che li mostra **solo** a chi ASTAP non ce
 * l'ha, e la sezione *Il riconoscitore* delle Impostazioni, dove si guarda e si corregge sempre.
 * Erano sotto `wizard.solver.*`, che fuori dal primo avvio sarebbe stato un nome che mente.
 */
export const enSolver = {
  "solver.withoutTitle": "Without ASTAP",
  "solver.without": "Files are catalogued and hours are counted, but imaged objects are not identified.",
  "solver.whereGroup": "Download",
  "solver.haveItGroup": "Already installed",
  "solver.noDownload": "The app does not download or install ASTAP.",
  "solver.pathHelp": "Path of the program (astap_cli), not of the folder.",
  "solver.checkNow": "The path is checked immediately.",
  "solver.placeholder": "C:\\Program Files\\astap\\astap_cli.exe",
  "solver.foundTitle": "ASTAP found",
  "solver.download": "Download ASTAP from the author's site",
  "solver.label": "ASTAP path",
  "solver.use": "Check path",
  "solver.found": "Imaged objects will be identified.",
  "solver.foundNoDatabase":
    "Star catalog missing: without it, objects are not identified.",
  "solver.alsoTheDatabase":
    "The star catalog is also required. It is downloaded separately.",
  "solver.notThere":
    "ASTAP not found at this path. The path must end with the program (astap_cli).",
  "solver.databaseHere": "star catalog: {quali}",
  "solver.databaseTitle": "Star catalog missing",
  "solver.databaseWhy":
    "ASTAP requires a star catalog, which is downloaded separately. Without a catalog, objects are not identified.",
  "solver.databaseGet": "Download the star catalog",
  "solver.databaseWhich":
    "Recommended catalog: D80 (about 1.25 GB), in the same folder as ASTAP.",
}
