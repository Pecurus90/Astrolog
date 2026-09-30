/** I testi di **Impostazioni**. File suo: `it.ts` e' al tetto di righe, e si spezza per area. */
export const itImpostazioni = {
  "settings.sections": "Sezioni delle impostazioni",
  "settings.folders": "Cartelle",
  "settings.solver": "Il riconoscitore",
  "settings.solver.title": "Il riconoscitore del cielo",
  "settings.solver.what":
    "E' ASTAP che guarda le stelle inquadrate e dice dove punta ogni ripresa. Qui vedi se l'app lo trova, e dove.",
  "settings.solver.here": "trovato",
  "settings.solver.none": "Non trovo ASTAP su questo computer.",
  "settings.solver.declaredNotThere": "Il percorso che hai scritto non porta a nessun programma:",
  "settings.solver.from.declared": "perche' gliel'hai detto tu",
  "settings.solver.from.env": "da chi ha avviato l'app (ASTROLOG_ASTAP)",
  "settings.solver.from.path": "cercandolo fra i programmi di sistema",
  "settings.solver.from.known_place": "dove si installa di solito",
  "settings.solver.search": "Cercalo tu",
  "settings.solver.searchedFound": "Ne ho trovato uno",
  "settings.solver.searchedNothing": "Ho guardato fra i programmi di sistema e dove ASTAP si installa di solito: non c'e'.",
  "settings.solver.adopt": "Usa quello che hai trovato",
  "settings.solver.failed": "Non riesco a sapere dove sta il riconoscitore.",
  "settings.solver.searchFailed": "Non sono riuscito a cercarlo.",
  "settings.site": "Il sito",
  "settings.readings": "Le letture",
  "settings.services": "Servizi",
  "settings.services.title": "I servizi",
  "settings.services.what": "Le chiavi personali dei servizi che l'app interroga. Senza, l'app funziona lo stesso.",

  "settings.folders.title": "Le cartelle che leggo",
  "settings.folders.what":
    "Le leggo tutte, sottocartelle comprese. Nessun file viene spostato ne' modificato.",
  "settings.folders.reachable": "si raggiunge",
  "settings.folders.unreachable": "non si raggiunge",
  "settings.folders.frames": "{n} frame in archivio",
  "settings.folders.frames.one": "1 frame in archivio",
  "settings.folders.frames.kept": "{n} frame gia' letti restano in archivio",
  "settings.folders.frames.kept.one": "1 frame gia' letto resta in archivio",
  "settings.folders.since": "aggiunta il {quando}",
  "settings.folders.remove": "Togli",
  "settings.folders.keeps":
    "Togliere una cartella non cancella niente: smetto di leggerla, e i frame che ne sono gia' entrati restano in archivio con la loro storia.",
  "settings.folders.failed": "Non riesco a leggere l'elenco delle cartelle.",

  "settings.folders.add.title": "Aggiungi una cartella",
  "settings.folders.add.what": "Scrivi il percorso come lo vedi nel tuo computer.",
  // Sul NAS il disco del computer non esiste: si sceglie da quello che il NAS espone.
  "settings.folders.add.what.nas": "Scegli fra le cartelle che il NAS espone: il disco del tuo computer, da qui dentro, non si vede.",
  "settings.folders.label": "Percorso",
  "settings.folders.look": "Guarda cosa c'e' dentro",
  "settings.folders.add": "Aggiungi",
  "settings.folders.lookFailed": "Non sono riuscito a guardare dentro quella cartella.",
  "settings.folders.addFailed": "Non sono riuscito ad aggiungere quella cartella.",
  "settings.folders.removeFailed": "Non sono riuscito a togliere quella cartella.",
  "settings.folders.foundTitle": "Trovata",
  "settings.folders.found": "Ci sono {n} file da leggere.",
  "settings.folders.found.one": "C'e' 1 file da leggere.",
  // Il conteggio si e' fermato al suo tetto di tempo: e' un pavimento, non un totale.
  "settings.folders.atLeastTitle": "Almeno questi",
  "settings.folders.atLeast": "Ne ho contati {n} e ho smesso di contare: ce ne sono almeno tanti.",
  "settings.folders.unreachableTitle": "Non la raggiungo",
  "settings.folders.unreachableHelp":
    "Il disco potrebbe essere scollegato, o il percorso sbagliato. Finche' non la raggiungo non posso aggiungerla.",

  "settings.folders.none": "Non leggo nessuna cartella",
  "settings.folders.none.why":
    "Finche' non ne indichi una, l'archivio resta vuoto: non c'e' niente da cui leggere.",
  "settings.folders.none.safe":
    "Nessun file viene spostato ne' modificato: si leggono e si contano.",

  "settings.folders.confirm": "Smetto di leggere {percorso}?",
  "settings.folders.confirm.what":
    "Non cancello niente. Quello che e' gia' entrato in archivio resta dov'e', con le sue notti e le sue ore.",
  "settings.folders.confirm.frames": "frame restano in archivio",
  "settings.folders.confirm.files": "i file sul disco non vengono toccati",
  "settings.folders.confirm.stop":
    "smetto di guardare questa cartella: i file nuovi non entrano piu'",
  "settings.folders.cancel": "Annulla",
  "settings.folders.stop": "Smetti di leggerla",

  "settings.site.title": "I tuoi siti",
  "settings.site.what":
    "Le notti e l'altezza degli oggetti si calcolano dal sito di casa. Gli altri servono alle uscite.",
  "settings.site.home": "di casa",
  "settings.site.makeHome": "Rendi di casa",
  "settings.site.makeHomeOne": "Rendi di casa {nome}",
  "settings.site.fix": "Correggi",
  "settings.site.fixOne": "Correggi {nome}",
  "settings.site.remove": "Togli",
  "settings.site.removeOne": "Togli {nome}",
  "settings.site.removeIt": "Togli il sito",
  "settings.site.add": "Aggiungi un sito",
  "settings.site.cancel": "Annulla",
  "settings.site.save": "Salva",
  "settings.site.keeps":
    "Senza il cielo il sito funziona lo stesso: quello che manca e' il confronto fra una notte e l'altra quando cambi posto.",
  "settings.site.failed": "Non riesco a leggere i tuoi siti.",
  "settings.site.saveFailed": "Non sono riuscito a salvare il sito.",
  "settings.site.homeFailed": "Non sono riuscito a cambiare il sito di casa.",
  "settings.site.removeFailed": "Non sono riuscito a togliere il sito.",
  "settings.site.add.title": "Aggiungi un sito",
  "settings.site.add.what": "Cerca il posto per nome, oppure scrivi le coordinate.",
  "settings.site.fix.title": "Correggi il sito",
  "settings.site.fix.what":
    "Il cielo cambia: un lampione nuovo, un quartiere che spegne di notte. Qui si corregge senza rifare niente.",
  "settings.site.confirm": "Tolgo {nome}?",
  "settings.site.confirm.what":
    "I frame ripresi da li' restano in archivio. Quello che si perde e' il posto da cui l'app calcola le notti.",
  "settings.site.hasNightsTitle": "Questo sito tiene delle notti",
  "settings.site.hasNights":
    "{n} notti sono legate a questo sito: finche' ci sono, non si puo' togliere. Se il posto e' sbagliato, correggilo invece di toglierlo.",
  "settings.site.hasNights.one":
    "1 notte e' legata a questo sito: finche' c'e', non si puo' togliere. Se il posto e' sbagliato, correggilo invece di toglierlo.",
  "settings.site.noHomeTitle": "Nessun sito e' quello di casa",
  "settings.site.noHome":
    "Finche' non ne scegli uno, le notti non si calcolano e la barra non sa da dove osservi. Premi Rendi di casa su quello giusto.",
  "settings.site.none": "Nessun sito dichiarato",
  "settings.site.none.why":
    "Catalogo lo stesso tutto quello che hai ripreso. Quello che non posso fare e' dividere le riprese in notti: senza un posto non so quando comincia e quando finisce il buio.",
  "settings.site.none.enough": "Bastano nome e coordinate. Il cielo si dichiara dopo, o mai.",
}
