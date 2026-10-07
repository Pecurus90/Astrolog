/**
 * I testi del **primo avvio**, italiani.
 *
 * Stanno in un file loro perche' sono un terzo di tutto il dizionario: il primo avvio e' la
 * schermata che parla di piu' -- ogni passo dice cosa chiede e perche' -- e chi va a correggere
 * una di quelle frasi non deve scorrere i testi di tutte le altre pagine per trovarla.
 */
export const itWizard = {
  "wizard.passo": "Passo {n} di {tot}",
  "wizard.name.why": "Serve a salutarti nella barra in alto, e a intestare le tue statistiche.",
  "wizard.name.placeholder": "Come vuoi essere chiamato",
  "wizard.site.searchGroup": "cerca il posto per nome",
  "wizard.site.manualWhy": "Sempre aperta, non solo quando la ricerca fallisce: un sito buio puo' non avere rete, ed e' proprio dove si osserva.",
  "wizard.site.failedTitle": "Non ho potuto salvare il sito",
  "wizard.folders.intro": "Scrivi il percorso di una cartella: la leggo tutta, sottocartelle comprese. Puoi indicarne piu' di una.",
  "wizard.folders.introNas": "L'app gira dentro un container: il percorso che vede lei non e' quello che vedi tu, e non si puo' indovinare. Sfoglia le cartelle e dimmi quale usare.",
  "wizard.folders.open": "Apri",
  // Il nome per chi ascolta e per chi comanda a voce: venti cartelle in elenco sono venti
  // bottoni che si chiamano tutti "Apri", e "clicca Notti" non trova niente. Comincia con la
  // parola che si vede, cosi' chi la pronuncia la ritrova.
  "wizard.folders.openOne": "Apri {nome}",
  "wizard.folders.pathHelp": "E' il percorso come lo vede il container, non come lo vedi tu dal computer.",
  "wizard.folders.foundTitle": "Dentro c'e' roba da leggere",
  "wizard.folders.atLeastTitle": "Il numero e' un minimo, non un totale",
  "wizard.folders.unreachableTitle": "Questa cartella non si raggiunge",
  "wizard.folders.unreachableHelp": "Finche' la cartella non risponde non c'e' niente da registrare. Correggi il percorso, o collega il disco e riprova.",
  "wizard.folders.browseFailedTitle": "Non riesco a leggere l'elenco",
  "wizard.folders.here": "Sei in",
  "wizard.solver.intro": "Sul computer non trovo ASTAP, il programma che riconosce il cielo dalle stelle inquadrate. Non e' un guasto: e' una cosa da fare, e si puo' fare anche dopo.",
  "wizard.solver.state": "non trovato",
  "wizard.solver.state.noDatabase": "senza catalogo",
  "wizard.solver.introNoDatabase":
    "ASTAP c'e', ma gli manca il catalogo stellare: senza, non riconosce niente. Non e' un guasto: e' un download a parte, e si puo' fare anche dopo.",
  "wizard.savedFailedTitle": "Non ho potuto salvare",
  "wizard.title": "Primo avvio",
  "wizard.step.name": "Come ti chiami",
  "wizard.steps": "I passi del primo avvio",
  // Le due parole che il segno del binario non puo' dire: e' `aria-hidden`, perche' chi
  // ascolta sentirebbe "spunta" invece di "fatto".
  "wizard.step.done": "- fatto",
  "wizard.step.here": "- sei qui",
  "wizard.step.site": "Da dove osservi",
  "wizard.step.solver": "Il riconoscitore",
  "wizard.step.folders": "Dove stanno i file",
  "wizard.step.services": "Il seeing per la planetaria",
  "wizard.services.why": "Se hai una chiave Meteoblue, il seeing arriva ora per ora e per sette notti. Non e' obbligatoria: senza, il seeing non c'e' e il resto del meteo funziona uguale. Puoi saltare e metterla dopo nelle Impostazioni.",
  "wizard.skip": "Salta per ora",
  "wizard.next": "Avanti",
  "wizard.back": "Indietro",
  "wizard.reassure": "Puoi saltare: l'app cataloga e cerca lo stesso.",
  "wizard.done": "Fatto",
  "wizard.name.label": "Nome",
  "wizard.name.hint": "Per ora l'app lo conserva soltanto. Si puo' lasciare vuoto.",
  "wizard.site.why": "Senza un sito le notti non nascono: serve per le fasce della notte e per l'altezza degli oggetti. Puoi aggiungerne altri piu' avanti.",
  "wizard.site.failed": "il sito non si e' salvato",
  "wizard.site.manual": "Oppure scrivi le coordinate",
  "wizard.site.save": "Usa questo sito",
  "wizard.folders.choose": "Scegli una cartella",
  "wizard.folders.up": "Sali di una cartella",
  "wizard.folders.useThis": "Usa questa cartella",
  "wizard.folders.empty": "qui dentro non ci sono altre cartelle",
  "wizard.folders.backToRoot": "Torna alla cartella dei dati",
  "wizard.folders.browseFailed": "non si riesce a leggere l'elenco delle cartelle: scrivi il percorso",
  "wizard.folders.added": "Le cartelle che hai indicato",
  "wizard.folders.label": "Percorso della cartella",
  "wizard.folders.look": "Guarda",
  "wizard.folders.add": "Aggiungi la cartella",
  "wizard.folders.found": "{n} file FITS",
  "wizard.folders.found.one": "1 file FITS",
  "wizard.folders.atLeast": "Ne ho contati {n} e ho smesso di contare: ce ne sono almeno tanti.",
  "wizard.folders.lookFailed": "non si e' potuto guardare li'",
  "wizard.folders.failed": "la cartella non si e' registrata",
}
