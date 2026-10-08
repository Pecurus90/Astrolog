/**
 * I testi del **piede della barra**: da dove osservi, e che luna fa.
 *
 * File suo per la stessa ragione del primo avvio: `it.ts` e' al tetto di righe, e si spezza per
 * area.
 */
export const itStanotte = {
  "tonight.title": "Stanotte",
  "tonight.at": "Stanotte a {sito}",
  "tonight.site": "sito",
  "tonight.moon": "luna",
  "tonight.weather": "meteo",
  "tonight.sites.manage": "Gestisci i siti",
  "tonight.sites.failed": "Cambio del sito non riuscito.",
  "tonight.sites.unread": "Siti non disponibili.",
  "tonight.sky": "Bortle {n}",
  // Il sito c'e' ma non gli e' mai stata data una classe di cielo: non e' un guasto, e' una cosa
  // che manca.
  "tonight.sky.none": "Bortle non indicato",
  // La rampa di nove bande e' un disegno: chi ascolta sente questa frase al suo posto.
  "tonight.sky.label": "Bortle {n} su 9, sito {sito}",
  "tonight.sky.none.label": "Bortle non indicato per {sito}",
  "tonight.nosite": "Nessun sito selezionato.",
  "tonight.nosite.how": "Seleziona sito",
  "tonight.loading": "Caricamento\u2026",
  "tonight.failed": "Dati di stanotte non disponibili.",
  "tonight.notimezone": "Fuso orario del sito non riconosciuto: Luna non calcolabile.",
  "tonight.illuminated": "illuminata al {pct}%",
  // Il grafico in barra non ha assi ne' etichette: questa frase e' il suo dato, per chi non lo
  // vede. E' anche l'unico posto in barra dove il numero di quanto sale compare -- a schermo sta
  // nel pannello, per decisione del disegno.
  // Si aggiunge al nome del grafico: per chi non vede la tela il buio e' **il dato** che le fasce
  // mostrano, e senza questa frase resterebbe solo un colore. E' **buio** e non "buio pieno": in
  // questo stesso piede "buio pieno" e' gia' la classe 1 di Bortle (`sky.low`), che e' quanto e'
  // scuro il posto, non quando e' scuro stanotte.
  "tonight.weather.none": "Previsione non disponibile. Dettagli nella pagina Meteo.",
  "tonight.weather.open": "Apri il Meteo",
  // In barra c'e' il verbo e l'ora, e basta: quanto sale lo mostra il grafico, e il numero si
  // legge nel pannello. Decisione del disegno, dichiarata nel foglio.
  "tonight.rise": "sorge",
  "tonight.set": "tramonta",
  "tonight.rise.never": "non sorge",
  "tonight.set.never": "non tramonta",
  // --- Il pannello. Si apre dalla striscia, e dice cio' che in 227px non ci sta. Il bottone che
  // lo apre **non ha un nome suo**: il suo nome e' cio' che ci sta dentro -- fase, percentuale,
  // grafico e orari -- e un'etichetta lo coprirebbe togliendo quei dati a chi ascolta.
  // I tre riquadri. Il terzo e' **quanto** sale, che e' il numero che decide la notte: una piena
  // che resta bassa disturba meno di una mezza che passa allo zenit. Si dice **"sale fino a"** e
  // non "culmina": il punto piu' alto e' il massimo dentro la finestra della notte, e una notte su
  // quindici cade sul bordo invece che su una culminazione vera (`docs/domini/effemeridi.md`).
  // La legenda e' scritta: un colore da solo non dice niente (WCAG 1.4.1).
  // La rampa delle cinque fasce, nominata dai suoi due estremi: dentro c'e' il crepuscolo, e il
  // buio e' l'ultima. Le fasce che una notte non ha non si nominano, perche' non si vedono.
  // Le scritte dentro il grafico: il tetto del sito in alto a sinistra, e la riga dello zero.
  "moon.new": "Luna nuova",
  "moon.waxing_crescent": "Crescente",
  "moon.first_quarter": "Primo quarto",
  "moon.waxing_gibbous": "Gibbosa crescente",
  "moon.full": "Luna piena",
  "moon.waning_gibbous": "Gibbosa calante",
  "moon.last_quarter": "Ultimo quarto",
  "moon.waning_crescent": "Calante",
}
