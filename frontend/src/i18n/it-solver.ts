/** I testi del **riconoscitore**: cosa cambia senza, dove si prende, e dove dirgli che sta.
 *
 * File suo perche' li usano in due -- il primo avvio, che li mostra **solo** a chi ASTAP non ce
 * l'ha, e la sezione *Il riconoscitore* delle Impostazioni, dove si guarda e si corregge sempre.
 * Erano sotto `wizard.solver.*`, che fuori dal primo avvio sarebbe stato un nome che mente.
 */
export const itSolver = {
  "solver.withoutTitle": "Senza ASTAP",
  "solver.without": "I file vengono catalogati e le ore contate, ma gli oggetti ripresi non vengono identificati.",
  "solver.whereGroup": "Download",
  "solver.haveItGroup": "Gi\u00e0 installato",
  "solver.noDownload": "L'app non scarica n\u00e9 installa ASTAP.",
  "solver.pathHelp": "Percorso del programma (astap_cli), non della cartella.",
  "solver.checkNow": "Il percorso viene verificato subito.",
  // La barra rovescia si raddoppia: in una stringa di questo linguaggio `\a` non e' una barra
  // seguita da una `a`, e il segnaposto usciva a schermo come `C:Program Filesastap...`.
  "solver.placeholder": "C:\\Program Files\\astap\\astap_cli.exe",
  "solver.foundTitle": "ASTAP trovato",
  "solver.download": "Scarica ASTAP dal sito dell'autore",
  "solver.label": "Percorso di ASTAP",
  "solver.use": "Verifica percorso",
  "solver.found": "Gli oggetti ripresi verranno identificati.",
  "solver.foundNoDatabase":
    "Catalogo stellare mancante: senza, gli oggetti non vengono identificati.",
  "solver.alsoTheDatabase":
    "Serve anche il catalogo stellare, che si scarica a parte.",
  "solver.notThere": "ASTAP non trovato in questo percorso. Il percorso deve terminare con il programma (astap_cli).",
  "solver.databaseHere": "catalogo stellare: {quali}",
  "solver.databaseTitle": "Catalogo stellare mancante",
  "solver.databaseWhy":
    "ASTAP richiede un catalogo stellare, che si scarica a parte. Senza catalogo gli oggetti non vengono identificati.",
  "solver.databaseGet": "Scarica il catalogo stellare",
  // Il consigliato e la sua misura vengono dal sito dell'autore, non a memoria: "The D05 is the
  // smallest. The D80 is the largest. Using the D80 has no drawback accept it is larger, about
  // 1.25 gbyte" (hnsky.org/astap.htm). Dove va lo dice la stessa pagina: "as long as all files
  // are in the same directory".
  "solver.databaseWhich":
    "Catalogo consigliato: D80 (circa 1,25 GB), nella stessa cartella di ASTAP.",
}
