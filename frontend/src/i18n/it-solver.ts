/** I testi del **riconoscitore**: cosa cambia senza, dove si prende, e dove dirgli che sta.
 *
 * File suo perche' li usano in due -- il primo avvio, che li mostra **solo** a chi ASTAP non ce
 * l'ha, e la sezione *Il riconoscitore* delle Impostazioni, dove si guarda e si corregge sempre.
 * Erano sotto `wizard.solver.*`, che fuori dal primo avvio sarebbe stato un nome che mente.
 */
export const itSolver = {
  "solver.withoutTitle": "Cosa cambia senza",
  "solver.without": "Senza, l'app cataloga i tuoi file, mette in ordine i nomi e conta le ore, ma non sapra' dirti cosa hai ripreso. Puoi installarlo anche piu' avanti.",
  "solver.whereGroup": "dove si prende",
  "solver.haveItGroup": "se ce l'hai gia'",
  "solver.noDownload": "L'app non scarica e non installa niente: l'indirizzo e' scritto qui perche' tu possa andarci, quando vuoi.",
  "solver.pathHelp": "Il percorso va fino al programma, non alla cartella che lo contiene.",
  "solver.checkNow": "Il controllo e' subito, qui: non si scopre a scansione finita che il percorso era sbagliato.",
  // La barra rovescia si raddoppia: in una stringa di questo linguaggio `\a` non e' una barra
  // seguita da una `a`, e il segnaposto usciva a schermo come `C:Program Filesastap...`.
  "solver.placeholder": "C:\\Program Files\\astap\\astap_cli.exe",
  "solver.foundTitle": "Trovato",
  "solver.download": "Scarica ASTAP dal sito dell'autore",
  "solver.label": "Se ce l'hai gia', dove sta",
  "solver.use": "Usa questo",
  "solver.found": "Trovato. L'app riconoscera' cosa hai ripreso.",
  "solver.foundNoDatabase":
    "Trovato. Gli manca ancora il catalogo stellare: finche' non c'e', non riconosce niente.",
  "solver.alsoTheDatabase":
    "Serve anche il suo catalogo stellare, che si scarica a parte: senza, ASTAP parte e non riconosce niente. Quando l'avrai installato, in Impostazioni vedi se l'app lo trova.",
  "solver.notThere": "Li' non c'e' ASTAP. Controlla il percorso: deve finire col programma (si chiama astap_cli), non con la cartella dove l'hai installato.",
  "solver.databaseHere": "catalogo stellare: {quali}",
  "solver.databaseTitle": "Manca il catalogo stellare",
  "solver.databaseWhy":
    "ASTAP c'e', ma da solo non riconosce niente: gli serve un catalogo di stelle con cui confrontare quello che hai inquadrato, e si scarica a parte. Senza, la lettura si ferma alla prima posa.",
  "solver.databaseGet": "Scarica il catalogo stellare",
  // Il consigliato e la sua misura vengono dal sito dell'autore, non a memoria: "The D05 is the
  // smallest. The D80 is the largest. Using the D80 has no drawback accept it is larger, about
  // 1.25 gbyte" (hnsky.org/astap.htm). Dove va lo dice la stessa pagina: "as long as all files
  // are in the same directory".
  "solver.databaseWhich":
    "Se non sai quale, prendi il D80: e' il piu' completo, circa 1,25 GB. Va messo nella stessa cartella del programma.",
}
