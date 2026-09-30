/**
 * I testi inglesi della pagina **Notti**: una **traduzione**, non una sorgente. Si scrive in
 * `it-notti.ts` e si porta qui, con le stesse chiavi e gli stessi segnaposto.
 */
export const enNotti = {
  "nights.title": "Nights",
  "nights.failed": "could not read the nights",
  "nights.more": "Show more",
  "nights.frames": "{n} frames",
  "nights.frames.one": "1 frame",
  "nights.at": "from {sito}",
  "nights.when": "{data} -- {giorno}",
  "nights.noFilter": "no filter declared",
  "nights.moon": "{fase}, {pct}%",
  "nights.weather.go": "few clouds (clouds at {pct}%).",
  "nights.weather.marginal": "partly cloudy (clouds at {pct}%).",
  "nights.weather.nogo": "mostly cloudy (clouds at {pct}%).",
  "nights.weather.waiting": "the weather for that night has not arrived yet",
  "nights.weather.unknown": "the site has no time zone: the weather for that night cannot be known",
  "nights.weather.none": "the weather archive does not say what the sky was like that night",
  "nights.totals": "{notti} nights in the archive",
  "nights.totals.frames": "{n} frames in all",
  "nights.totals.frames.one": "1 frame in all",
  "nights.waiting.review":
    "{n} frames are waiting for your answer: without it, they stay out of every night.",
  "nights.waiting.review.one": "1 frame is waiting for your answer: without it, it stays out of every night.",
  "nights.waiting.where": "Go to To confirm",
  "nights.waiting.site":
    "{n} frames are waiting to know where you were observing from: a night is a date plus a place.",
  "nights.waiting.site.one":
    "1 frame is waiting to know where you were observing from: a night is a date plus a place.",
  "nights.waiting.never":
    "{n} frames do not say when they were taken, so no night can collect them.",
  "nights.waiting.never.one":
    "1 frame does not say when it was taken, so no night can collect it.",
  "nights.reading": "I am still reading the archive: {n} frames have yet to find their night.",
  "nights.reading.one": "I am still reading the archive: 1 frame has yet to find its night.",
  "nights.empty.noFrames": "No nights yet",
  "nights.empty.noFrames.why":
    "Nights are rebuilt from the headers of your FITS files: as soon as a folder has been read, every night shows up here with its hours and its frames.",
  "nights.empty.noFrames.how": "Add a folder",
  "nights.empty.noSite": "I don't know where you were observing from",
  "nights.empty.noSite.why":
    "A night is a date plus a place: without knowing where you were, the app cannot tell which time zone your night starts and ends in, and no night is ever born.",
  "nights.empty.noSite.how": "Declare your site",
  "nights.empty.notYet": "The nights are on their way",
  "nights.empty.notYet.why":
    "The app is still looking at your frames: a night shows up here once it knows what you imaged and from where.",
  "nights.empty.waiting": "No nights: the app is waiting for you",
  "nights.empty.waiting.why":
    "Your frames are there, but they stay out until you answer the questions the app has ready for you.",
}
