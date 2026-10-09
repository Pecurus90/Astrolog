/** I testi di **Impostazioni**. File suo: `it.ts` e' al tetto di righe, e si spezza per area. */
export const itImpostazioni = {
  "settings.sections": "Sezioni delle impostazioni",
  "settings.folders": "Cartelle",
  "settings.solver": "ASTAP",
  "settings.solver.title": "ASTAP",
  "settings.solver.what":
    "ASTAP identifica il campo inquadrato in ogni frame (plate solving).",
  "settings.solver.here": "trovato",
  "settings.solver.none": "ASTAP non trovato.",
  "settings.solver.declaredNotThere": "Percorso non valido:",
  "settings.solver.from.declared": "percorso inserito manualmente",
  "settings.solver.from.env": "variabile ASTROLOG_ASTAP",
  "settings.solver.from.path": "PATH di sistema",
  "settings.solver.from.known_place": "cartella di installazione predefinita",
  "settings.solver.search": "Cerca ASTAP",
  "settings.solver.searchedFound": "ASTAP trovato",
  "settings.solver.searchedNothing": "ASTAP non trovato nel PATH n\u00e9 nelle cartelle di installazione predefinite.",
  "settings.solver.adopt": "Usa questo percorso",
  "settings.solver.failed": "Percorso di ASTAP non disponibile.",
  "settings.solver.searchFailed": "Ricerca non riuscita.",
  "settings.site": "Siti",
  "settings.readings": "Scansioni",
  "settings.services": "Servizi",
  "settings.services.title": "Servizi",
  "settings.services.what": "Chiavi API dei servizi esterni. Facoltative.",

  "settings.folders.title": "Cartelle",
  "settings.folders.what":
    "Vengono lette anche le sottocartelle. I file non vengono spostati n\u00e9 modificati.",
  "settings.folders.reachable": "Raggiungibile",
  "settings.folders.unreachable": "Non raggiungibile",
  "settings.folders.frames": "{n} frame in archivio",
  "settings.folders.frames.one": "1 frame in archivio",
  "settings.folders.frames.kept": "{n} frame restano in archivio",
  "settings.folders.frames.kept.one": "1 frame resta in archivio",
  "settings.folders.since": "aggiunta il {quando}",
  "settings.folders.remove": "Rimuovi",
  "settings.folders.keeps":
    "Rimuovere una cartella non elimina file n\u00e9 frame gi\u00e0 in archivio.",
  "settings.folders.failed": "Cartelle non disponibili.",

  "settings.folders.add.title": "Aggiungi cartella",
  "settings.folders.add.what": "Inserisci il percorso della cartella.",
  // Sul NAS il disco del computer non esiste: si sceglie da quello che il NAS espone.
  "settings.folders.add.what.nas": "Seleziona una cartella fra quelle disponibili sul NAS.",
  "settings.folders.label": "Percorso",
  "settings.folders.look": "Verifica",
  "settings.folders.add": "Aggiungi",
  "settings.folders.lookFailed": "Verifica non riuscita.",
  "settings.folders.addFailed": "Aggiunta non riuscita.",
  "settings.folders.removeFailed": "Rimozione non riuscita.",
  "settings.folders.foundTitle": "File trovati",
  "settings.folders.found": "{n} file FITS",
  "settings.folders.found.one": "1 file FITS",
  // Il conteggio si e' fermato al suo tetto di tempo: e' un pavimento, non un totale.
  "settings.folders.atLeastTitle": "Conteggio parziale",
  "settings.folders.atLeast": "Conteggio interrotto a {n}: i file sono di pi\u00f9.",
  "settings.folders.unreachableTitle": "Cartella non raggiungibile",
  "settings.folders.unreachableHelp":
    "Controlla il percorso o collega il disco, poi riprova.",

  "settings.folders.none": "Nessuna cartella",
  "settings.folders.none.why":
    "Aggiungi una cartella per popolare l'archivio.",
  "settings.folders.none.safe":
    "I file non vengono spostati n\u00e9 modificati.",

  "settings.folders.confirm": "Rimuovere {percorso}?",
  "settings.folders.confirm.what":
    "Effetti della rimozione:",
  "settings.folders.confirm.frames": "frame restano in archivio",
  "settings.folders.confirm.files": "i file su disco non vengono modificati",
  "settings.folders.confirm.stop":
    "i nuovi file di questa cartella non vengono pi\u00f9 letti",
  "settings.folders.cancel": "Annulla",
  "settings.folders.stop": "Rimuovi cartella",

  // Chi ha spostato le foto (un altro disco, un'altra lettera, il NAS): stessa cartella, posto nuovo.
  "settings.folders.move": "Cambia percorso",
  "settings.folders.move.title": "Nuovo percorso di {percorso}",
  "settings.folders.move.what":
    "Indica il nuovo percorso. Viene verificato che contenga gli stessi file.",
  "settings.folders.move.label": "Nuovo percorso",
  "settings.folders.move.look": "Verifica",
  "folders.move.foundTitle": "Cartella gi\u00e0 registrata",
  "folders.move.found":
    "Corrisponde a {percorso}: stessi file. I dati associati vengono mantenuti.",
  "folders.move.here": "Usa questo percorso",
  "folders.move.notSame": "I file non corrispondono: percorso non modificato.",
  "folders.move.exists": "Percorso gi\u00e0 presente.",
  "folders.move.unreachable": "Percorso non raggiungibile.",
  "folders.move.failed": "Modifica del percorso non riuscita.",

  "settings.site.title": "Siti di osservazione",
  "settings.site.what":
    "Il sito predefinito \u00e8 usato per le notti, Stanotte e il Meteo.",
  "settings.site.home": "predefinito",
  "settings.site.makeHome": "Imposta come predefinito",
  "settings.site.makeHomeOne": "Imposta {nome} come predefinito",
  "settings.site.fix": "Modifica",
  "settings.site.fixOne": "Modifica {nome}",
  "settings.site.remove": "Rimuovi",
  "settings.site.removeOne": "Rimuovi {nome}",
  "settings.site.removeIt": "Rimuovi sito",
  "settings.site.add": "Aggiungi sito",
  "settings.site.cancel": "Annulla",
  "settings.site.save": "Salva",
  "settings.site.keeps":
    "La classe di Bortle \u00e8 facoltativa.",
  "settings.site.failed": "Siti non disponibili.",
  "settings.site.saveFailed": "Salvataggio non riuscito.",
  "settings.site.homeFailed": "Modifica del sito predefinito non riuscita.",
  "settings.site.removeFailed": "Rimozione non riuscita.",
  "settings.site.add.title": "Aggiungi sito",
  "settings.site.add.what": "Cerca per nome o inserisci le coordinate.",
  "settings.site.fix.title": "Modifica sito",
  "settings.site.fix.what":
    "Nome, coordinate e classe di Bortle.",
  "settings.site.confirm": "Rimuovere {nome}?",
  "settings.site.confirm.what":
    "I frame restano in archivio.",
  "settings.site.hasNightsTitle": "Sito in uso",
  "settings.site.hasNights":
    "{n} notti sono associate a questo sito: non pu\u00f2 essere rimosso.",
  "settings.site.hasNights.one":
    "1 notte \u00e8 associata a questo sito: non pu\u00f2 essere rimosso.",
  "settings.site.noHomeTitle": "Nessun sito predefinito",
  "settings.site.noHome":
    "Imposta un sito come predefinito per calcolare le notti.",
  "settings.site.none": "Nessun sito",
  "settings.site.none.why":
    "Senza un sito i frame vengono catalogati ma non divisi in notti.",
  "settings.site.none.enough": "Sono richiesti nome e coordinate.",
  "settings.backup": "Backup",
  "backup.title": "Backup",
  "backup.what":
    "Il backup contiene i dati inseriti (attrezzatura, oggetti, siti, preferenze). Non contiene i file FITS.",
  "backup.when": "Ultimo backup: {giorno}, {ora}",
  "backup.counts": "conferme {risposte}, siti {siti}, cartelle {cartelle}, strumenti e filtri {pezzi}",
  "backup.none": "Nessun backup.",
  "backup.unreadable": "File di backup non leggibile: verr\u00e0 ricreato.",
  "backup.export": "Esporta backup",
  "backup.import": "Importa backup",
  "backup.imported": "Backup importato. Scansione avviata.",
  "backup.notABackup": "File di backup non valido.",
  "backup.exportFailed": "Esportazione non riuscita.",
  "backup.importFailed": "Importazione non riuscita.",
  "backup.failed": "Stato del backup non disponibile.",
  "backup.restoreFailed": "Ripristino non riuscito.",
  "backup.count.answers": "Conferme",
  "backup.count.sites": "Siti",
  "backup.count.folders": "Cartelle",
  "backup.count.gear": "Strumenti e filtri",
  "backup.found.title": "Backup trovato",
  "backup.found.question": "Ripristinare i dati salvati? Le cartelle verranno rilette.",
  "backup.found.restore": "Ripristina",
  "backup.found.decline": "Inizia da zero",
}
