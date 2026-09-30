/** I testi del **riconoscitore**: cosa cambia senza, dove si prende, e dove dirgli che sta.
 *
 * File suo perche' li usano in due -- il primo avvio, che li mostra **solo** a chi ASTAP non ce
 * l'ha, e la sezione *Il riconoscitore* delle Impostazioni, dove si guarda e si corregge sempre.
 * Erano sotto `wizard.solver.*`, che fuori dal primo avvio sarebbe stato un nome che mente.
 */
export const enSolver = {
  "solver.withoutTitle": "What changes without it",
  "solver.without":
    "Without it, the app catalogues your files, tidies up the names and counts the hours, but it will not be able to tell you what you imaged. You can install it later on.",
  "solver.whereGroup": "where to get it",
  "solver.haveItGroup": "if you already have it",
  "solver.noDownload": "The app downloads nothing and installs nothing: the address is written here so that you can go there, when you want.",
  "solver.pathHelp": "The path goes all the way to the program, not to the folder holding it.",
  "solver.checkNow": "The check is immediate, here: you do not find out at the end of a scan that the path was wrong.",
  "solver.placeholder": "C:\\Program Files\\astap\\astap_cli.exe",
  "solver.foundTitle": "Found",
  "solver.download": "Download ASTAP from the author's site",
  "solver.label": "If you already have it, where it is",
  "solver.use": "Use this one",
  "solver.found": "Found it. The app will recognise what you imaged.",
  "solver.foundNoDatabase":
    "Found it. It is still missing its star database: until that is there, it recognises nothing.",
  "solver.alsoTheDatabase":
    "It also needs its star database, a separate download: without it, ASTAP starts and recognises nothing. Once you have installed it, Settings tells you whether the app finds it.",
  "solver.notThere":
    "ASTAP is not there. Check the path: it must end with the program (it is called astap_cli), not with the folder you installed it in.",
  "solver.databaseHere": "star database: {quali}",
  "solver.databaseTitle": "The star database is missing",
  "solver.databaseWhy":
    "ASTAP is there, but on its own it recognises nothing: it needs a catalogue of stars to compare with what you framed, and that is a separate download. Without it, the reading stops at the first shot.",
  "solver.databaseGet": "Download the star database",
  "solver.databaseWhich":
    "If you don't know which one, take the D80: it is the most complete, about 1.25 GB. It goes in the same folder as the program.",
}
