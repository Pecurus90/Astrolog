/**
 * I testi della pagina **Notti**: le notti passate, una carta ciascuna (disegno v29, il registro).
 *
 * File suo per la stessa ragione del primo avvio: `it.ts` e' al tetto di righe, e si spezza per
 * area.
 */
export const itNotti = {
  "nights.title": "Notti",
  "nights.failed": "Non sono riuscito a leggere le notti",
  "nights.retry": "Riprova",
  "nights.loading": "Sto leggendo le notti",
  "nights.all": "\u2190 Tutte le notti",
  "nights.all.short": "Tutte le notti",
  "nights.gone": "Questa notte non c'e' piu' nell'archivio",
  "nights.gone.why": "I suoi frame sono stati tolti o spostati.",
  "nights.more": "Mostra altre",
  "nights.shown": "{n} notti di {di}",
  // In testa: cosa tiene l'archivio intero. Non segue quello che si sta guardando, ed e' la
  // risposta alla domanda che ci si fa aprendo la pagina. Mai "0 ore": i frame senza durata si
  // contano a parte.
  "nights.totals.title": "tutto l'archivio",
  "nights.totals.nights": "notti",
  "nights.totals.frames": "frame",
  "nights.totals.hours": "ore",
  "nights.totals.hours.one": "ora",
  "nights.totals.untimed": "senza tempo",
  "nights.totals.copies": "Le copie riscritte non si contano.",
  // I frame che nessuna notte ha raccolto, una riga per **dove si risponde**. Il terzo gruppo non
  // ha un'azione apposta: a un frame che non dice quando e' stato ripreso nessuna risposta rimedia.
  "nights.waiting.review": "{n} frame aspettano una tua risposta",
  "nights.waiting.review.one": "1 frame aspetta una tua risposta",
  "nights.waiting.review.why": "Finche' non rispondi non entrano in nessuna notte.",
  "nights.waiting.where": "Vai a Da confermare",
  "nights.waiting.site": "{n} frame aspettano il sito",
  "nights.waiting.site.one": "1 frame aspetta il sito",
  "nights.waiting.site.why": "Vengono da una cartella che non dice da dove osservavi.",
  "nights.waiting.site.how": "Apri le Impostazioni",
  "nights.waiting.never": "{n} frame senza data",
  "nights.waiting.never.one": "1 frame senza data",
  "nights.waiting.never.why": "Nel file non c'e' la data: non possono stare in nessuna notte.",
  // Mentre la spina lavora. Chi apre la pagina a meta' corsa vedrebbe tre notti e crederebbe di
  // averne tre.
  "nights.reading": "Sto ancora leggendo l'archivio: {n} frame devono ancora trovare la loro notte",
  "nights.reading.one": "Sto ancora leggendo l'archivio: 1 frame deve ancora trovare la sua notte",
  "nights.reading.why": "Le notti si aggiungono da sole. Non serve fare niente.",
  // I quattro modi di non avere notti, che sono quattro risposte diverse: mandare l'utente a
  // sistemare la cosa sbagliata e' peggio che non dirgli niente.
  "nights.empty.noFrames": "Nessuna notte, per ora",
  "nights.empty.noFrames.why": "Le notti nascono dai frame delle cartelle che mi fai leggere.",
  "nights.empty.noFrames.how": "Aggiungi una cartella",
  "nights.empty.noSite": "Non so da dove osservavi",
  "nights.empty.noSite.why":
    "Ho letto i tuoi frame, ma senza il sito non so a che notte appartengono: una notte e' una data piu' un sito.",
  "nights.empty.noSite.how": "Dichiara il tuo sito",
  "nights.empty.notYet": "Le notti stanno arrivando",
  "nights.empty.notYet.why":
    "Sto leggendo l'archivio: le notti arrivano man mano che i frame trovano la loro. Non serve fare niente.",
  "nights.empty.waiting": "Nessuna notte: l'app ti sta aspettando",
  "nights.empty.waiting.why": "I tuoi frame aspettano una tua risposta: finche' non rispondi non entrano in nessuna notte.",
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
  "nights.untimed": "{n} senza tempo",
  "nights.frames": "{n} frame",
  "nights.frames.one": "1 frame",
  "nights.object.untimed": "senza tempo",
  "nights.objects.more": "e {n} altri",
  "nights.objects.more.one": "e 1 altro",
  // Il cielo vero di quella notte, dall'archivio: le tre classi del verdetto dette come si dice
  // un cielo passato, coi nomi delle classi in okta (FEW, SCT, BKN/OVC dei METAR).
  "nights.weather.go": "poco nuvoloso, in media {pct}%",
  "nights.weather.marginal": "parzialmente nuvoloso, in media {pct}%",
  "nights.weather.nogo": "molto nuvoloso, in media {pct}%",
  // Due attese diverse: la notte giovane sa quando il meteo arriva; quella vecchia aspetta solo il
  // servizio, e una data sarebbe una promessa gia' rotta.
  "nights.weather.arrives": "il meteo arriva il {data}",
  "nights.weather.arrives.why": "L'archivio del meteo e' definitivo solo qualche giorno dopo la notte.",
  "nights.weather.waiting": "il meteo non e' ancora arrivato",
  "nights.weather.waiting.why": "Il servizio del meteo non ha ancora risposto per questa notte.",
  "nights.weather.unknown": "non si puo' sapere",
  "nights.weather.unknown.why": "Il sito non ha un fuso riconoscibile: senza, la notte non ha ore.",
  "nights.weather.none": "L'archivio del meteo non dice com'era il cielo quella notte.",
  // La barra dei filtri (FiltriUsati): la legenda dice frame e ore, o "senza tempo".
  "filters.legend.timed": "{n} \u00b7 {h} h",
  "filters.legend.untimed": "{n} \u00b7 senza tempo",
  "filters.none": "senza filtro dichiarato",
  "filters.bar": "Filtri: {filtri}",
}
