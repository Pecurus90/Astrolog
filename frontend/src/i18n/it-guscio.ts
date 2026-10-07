/** I testi del **guscio**: il nome dell'app e le voci della barra.
 *
 * File suo perche' non appartengono a nessuna pagina: vivono in `Layout.tsx`, che le pagine le
 * contiene. Toglierle da `it.ts` gli ha dato aria -- ogni file di testi nuovo gli costa due righe,
 * e il tetto e' vicino -- ma il tetto non era sfondato: e' un riordino, non una riparazione. Le
 * voci ci sono **tutte**, anche quelle delle pagine che non esistono ancora: la barra ne mostra
 * solo quelle nate (`docs/domini/navigazione.md`).
 *
 * `app.title` porta lo stesso valore in ogni lingua: e' il nome del prodotto, cioe' identita' che
 * non si traduce. Vive nel dizionario lo stesso, perche' una sola regola -- ogni testo passa da
 * `t()` -- e' piu' facile da tenere di una regola con un'eccezione.
 */
export const itGuscio = {
  "app.title": "AstroLog",
  "app.loading": "un momento...",
  "nav.label": "Le pagine",
  "nav.unknown": "Pagina sconosciuta",
  "notFound.title": "Questa pagina non c'e'",
  "notFound.why":
    "L'indirizzo non porta a nessuna pagina dell'app: forse e' scritto male, o viene da una pagina che non c'e' piu'.",
  "notFound.home": "Torna alla Dashboard",
  "soon.title": "{pagina} sta arrivando",
  "soon.why": "Questa pagina non c'e' ancora: la voce resta qui, al suo posto, e si accende quando la pagina e' pronta.",
  "frame.skip": "Vai al contenuto",
  "frame.more": "Altro",
  "frame.more.count": "dentro: {n} casi da confermare",
  "frame.count": "{n} casi da confermare",
  "frame.close": "Chiudi",
  "frame.close.word": "chiudi",
  "nav.home": "Dashboard",
  "nav.archive": "Archivio",
  "nav.nights": "Notti",
  "nav.gear": "Attrezzatura",
  "nav.stats": "Statistiche",
  "nav.review": "Da confermare",
  "nav.planner": "Planner",
  "nav.projects": "Progetti",
  "nav.sky": "Carta del cielo",
  "nav.weather": "Meteo",
  "nav.settings": "Impostazioni",
}
