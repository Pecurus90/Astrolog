/**
 * I testi della pagina **Notti**: le notti passate, una carta ciascuna (disegno v29, il registro).
 *
 * File suo per la stessa ragione del primo avvio: `it.ts` e' al tetto di righe, e si spezza per
 * area.
 */
export const itNotti = {
  "nights.title": "Notti",
  "nights.failed": "Notti non disponibili",
  "nights.retry": "Riprova",
  "nights.loading": "Caricamento delle notti",
  "nights.all": "\u2190 Tutte le notti",
  "nights.all.short": "Tutte le notti",
  "nights.gone": "Notte non trovata",
  "nights.gone.why": "I frame sono stati rimossi o spostati.",
  "nights.more": "Carica altre",
  "nights.shown": "{n} notti di {di}",
  // In testa: cosa tiene l'archivio intero. Non segue quello che si sta guardando, ed e' la
  // risposta alla domanda che ci si fa aprendo la pagina. Mai "0 ore": i frame senza durata si
  // contano a parte.
  "nights.totals.title": "Totale archivio",
  "nights.totals.nights": "notti",
  "nights.totals.frames": "frame",
  "nights.totals.hours": "ore",
  "nights.totals.hours.one": "ora",
  "nights.totals.untimed": "senza durata",
  "nights.totals.copies": "Le copie calibrate non sono contate.",
  // I frame che nessuna notte ha raccolto, una riga per **dove si risponde**. Il terzo gruppo non
  // ha un'azione apposta: a un frame che non dice quando e' stato ripreso nessuna risposta rimedia.
  "nights.waiting.review": "{n} frame da confermare",
  "nights.waiting.review.one": "1 frame da confermare",
  "nights.waiting.review.why": "Non sono assegnati a una notte finch\u00e9 non vengono confermati.",
  "nights.waiting.where": "Apri Da confermare",
  "nights.waiting.site": "{n} frame senza sito",
  "nights.waiting.site.one": "1 frame senza sito",
  "nights.waiting.site.why": "La cartella di provenienza non ha un sito associato.",
  "nights.waiting.site.how": "Apri le Impostazioni",
  "nights.waiting.never": "{n} frame senza data",
  "nights.waiting.never.one": "1 frame senza data",
  "nights.waiting.never.why": "Data assente nel file: non assegnabili a una notte.",
  // Mentre la spina lavora. Chi apre la pagina a meta' corsa vedrebbe tre notti e crederebbe di
  // averne tre.
  "nights.reading": "Scansione in corso: {n} frame da assegnare",
  "nights.reading.one": "Scansione in corso: 1 frame da assegnare",
  "nights.reading.why": "Le notti si aggiornano automaticamente.",
  // I quattro modi di non avere notti, che sono quattro risposte diverse: mandare l'utente a
  // sistemare la cosa sbagliata e' peggio che non dirgli niente.
  "nights.empty.noFrames": "Nessuna notte",
  "nights.empty.noFrames.why": "Le notti vengono create dai frame delle cartelle aggiunte.",
  "nights.empty.noFrames.how": "Aggiungi cartella",
  "nights.empty.noSite": "Sito mancante",
  "nights.empty.noSite.why":
    "I frame sono stati letti, ma senza un sito non possono essere assegnati a una notte.",
  "nights.empty.noSite.how": "Aggiungi sito",
  "nights.empty.notYet": "Scansione in corso",
  "nights.empty.notYet.why":
    "Le notti compaiono man mano che i frame vengono letti.",
  "nights.empty.waiting": "Nessuna notte: frame da confermare",
  "nights.empty.waiting.why": "I frame non sono assegnati a una notte finch\u00e9 non vengono confermati.",
  // Le intestazioni delle cinque colonne, in maiuscoletto dal foglio.
  "nights.col.when": "notte e sito",
  "nights.col.done": "ore e frame",
  "nights.col.objects": "oggetti",
  "nights.col.filters": "filtri",
  "nights.col.sky": "luna e meteo",
  // La carta: il nome per chi ascolta dice data, giorno e sito; a schermo la data e il giorno
  // stanno insieme, e l'ordine e il segno in mezzo cambiano da lingua a lingua.
  "nights.card": "{data}, {giorno}, {sito}",
  "nights.weekday": "\u2014 {giorno}",
  "nights.hours": "{h} h",
  "nights.untimed": "{n} senza durata",
  "nights.frames": "{n} frame",
  "nights.frames.one": "1 frame",
  "nights.object.untimed": "senza durata",
  "nights.objects.more": "+ {n}",
  "nights.objects.more.one": "+ 1",
  // Il cielo vero di quella notte, dall'archivio: le tre classi del verdetto dette come si dice
  // un cielo passato, coi nomi delle classi in okta (FEW, SCT, BKN/OVC dei METAR).
  "nights.weather.go": "poco nuvoloso, in media {pct}%",
  "nights.weather.marginal": "parzialmente nuvoloso, in media {pct}%",
  "nights.weather.nogo": "molto nuvoloso, in media {pct}%",
  // Due attese diverse: la notte giovane sa quando il meteo arriva; quella vecchia aspetta solo il
  // servizio, e una data sarebbe una promessa gia' rotta.
  "nights.weather.arrives": "Meteo disponibile dal {data}",
  "nights.weather.arrives.why": "I dati meteo storici sono disponibili alcuni giorni dopo la notte.",
  "nights.weather.waiting": "Meteo non ancora disponibile",
  "nights.weather.waiting.why": "Il servizio meteo non ha ancora fornito i dati.",
  "nights.weather.unknown": "Non disponibile",
  "nights.weather.unknown.why": "Fuso orario del sito non riconosciuto.",
  "nights.weather.none": "Dati meteo non disponibili per questa notte.",
  // La barra dei filtri (FiltriUsati): la legenda dice frame e ore, o "senza tempo".
  "filters.legend.timed": "{n} \u00b7 {h} h",
  "filters.legend.untimed": "{n} \u00b7 senza durata",
  "filters.none": "Filtro non indicato",
  "filters.bar": "Filtri: {filtri}",
}
