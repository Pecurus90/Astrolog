/**
 * I testi della pagina **Notti**: le notti passate, una riga ciascuna.
 *
 * File suo per la stessa ragione del primo avvio: `it.ts` e' al tetto di righe, e si spezza per
 * area.
 */
export const itNotti = {
  "nights.title": "Notti",
  "nights.failed": "non sono riuscito a leggere le notti",
  "nights.all": "Tutte le notti",
  "nights.gone": "Questa notte non c'e' piu' nell'archivio.",
  "nights.more": "Mostra altre",
  // La riga: quanti frame, e con che filtri. Le ore le scrive `TempoDellePose`, lo stesso pezzo
  // dell'Archivio, o due pagine direbbero le stesse ore in due modi.
  "nights.frames": "{n} frame",
  "nights.frames.one": "1 frame",
  "nights.at": "da {sito}",
  // La data e il giorno della settimana, che a schermo stanno insieme: l'ordine e il segno in
  // mezzo cambiano da lingua a lingua, quindi vivono qui e non nel componente.
  "nights.when": "{data} -- {giorno}",
  "nights.noFilter": "senza filtro dichiarato",
  // Il nome della fase lo danno le chiavi che usa gia' la barra: qui si aggiunge solo quanto era
  // illuminata.
  "nights.moon": "{fase}, {pct}%",
  // Il cielo vero di quella notte, dall'archivio: le tre classi del verdetto dette come si dice
  // un cielo passato, coi nomi delle classi in okta (FEW, SCT, BKN/OVC dei METAR).
  "nights.weather.go": "poco nuvoloso (nuvole al {pct}%).",
  "nights.weather.marginal": "parzialmente nuvoloso (nuvole al {pct}%).",
  "nights.weather.nogo": "molto nuvoloso (nuvole al {pct}%).",
  "nights.weather.waiting": "il meteo di quella notte non e' ancora arrivato",
  "nights.weather.unknown": "il sito non ha un fuso orario: il meteo di quella notte non si puo' sapere",
  "nights.weather.none": "l'archivio del meteo non dice com'era il cielo quella notte",
  // In cima: cosa tiene l'archivio intero. Non segue quello che si sta guardando, ed e' la
  // risposta alla domanda che ci si fa aprendo la pagina.
  "nights.totals": "{notti} notti in archivio",
  "nights.totals.frames": "{n} frame in tutto",
  "nights.totals.frames.one": "1 frame in tutto",
  // I frame che nessuna notte ha raccolto, raggruppati per **dove si risponde**. Un numero, non
  // un allarme. Il terzo gruppo non manda da nessuna parte apposta: a una posa che non dice
  // quando e' stata ripresa non c'e' risposta che rimedi.
  "nights.waiting.review": "{n} frame aspettano una tua risposta: senza, restano fuori da ogni notte.",
  "nights.waiting.review.one": "1 frame aspetta una tua risposta: senza, resta fuori da ogni notte.",
  "nights.waiting.where": "Vai a Da confermare",
  "nights.waiting.site":
    "{n} frame aspettano di sapere da dove osservavi: una notte e' una data piu' un luogo.",
  "nights.waiting.site.one":
    "1 frame aspetta di sapere da dove osservavi: una notte e' una data piu' un luogo.",
  "nights.waiting.never":
    "{n} frame non dicono quando sono stati ripresi, quindi nessuna notte puo' raccoglierli.",
  "nights.waiting.never.one":
    "1 frame non dice quando e' stato ripreso, quindi nessuna notte puo' raccoglierlo.",
  // Mentre la spina lavora. Chi apre la pagina a meta' corsa vedrebbe tre notti e crederebbe di
  // averne tre.
  "nights.reading":
    "Sto ancora leggendo l'archivio: {n} frame devono ancora trovare la loro notte.",
  "nights.reading.one": "Sto ancora leggendo l'archivio: 1 frame deve ancora trovare la sua notte.",
  // I quattro modi di non avere notti, che sono quattro risposte diverse: mandare l'utente a
  // sistemare la cosa sbagliata e' peggio che non dirgli niente.
  "nights.empty.noFrames": "Nessuna notte, per ora",
  "nights.empty.noFrames.why":
    "Le notti si ricostruiscono dagli header dei tuoi FITS: appena una cartella e' stata letta, ogni notte compare qui con le sue ore e i suoi frame.",
  "nights.empty.noFrames.how": "Aggiungi una cartella",
  "nights.empty.noSite": "Non so da dove osservavi",
  "nights.empty.noSite.why":
    "Una notte e' una data piu' un luogo: senza sapere dov'eri, l'app non sa in che fuso comincia e finisce la tua nottata, e le notti non nascono.",
  "nights.empty.noSite.how": "Dichiara il tuo sito",
  "nights.empty.notYet": "Le notti stanno arrivando",
  "nights.empty.notYet.why":
    "L'app sta ancora guardando i tuoi frame: una notte compare qui quando sa cosa hai ripreso e da dove.",
  "nights.empty.waiting": "Nessuna notte: l'app ti sta aspettando",
  "nights.empty.waiting.why":
    "I tuoi frame ci sono, ma restano fuori finche' non rispondi alle domande che l'app ti ha preparato.",
}
