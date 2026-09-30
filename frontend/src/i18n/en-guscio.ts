/** I testi del **guscio**: il nome dell'app e le voci della barra.
 *
 * File suo perche' non appartengono a nessuna pagina: vivono in `Layout.tsx`, che le pagine le
 * contiene. Toglierle da `en.ts` gli ha dato aria -- ogni file di testi nuovo gli costa due righe,
 * e il tetto e' vicino -- ma il tetto non era sfondato: e' un riordino, non una riparazione. Le
 * voci ci sono **tutte**, anche quelle delle pagine che non esistono ancora: la barra ne mostra
 * solo quelle nate (`docs/domini/navigazione.md`).
 */
export const enGuscio = {
  "app.title": "AstroLog",
  "app.loading": "one moment...",
  "nav.label": "Pages",
  "nav.unknown": "Unknown page",
  "notFound.title": "This page does not exist",
  "notFound.why":
    "The address does not lead to any page of the app: maybe it is mistyped, or it comes from a page that no longer exists.",
  "notFound.home": "Back to Home",
  "nav.group.guarda": "Browse",
  "nav.group.sistema": "Organise",
  "nav.group.pianifica": "Plan",
  "nav.home": "Home",
  "nav.archive": "Archive",
  "nav.nights": "Nights",
  "nav.gear": "Equipment",
  "nav.stats": "Statistics",
  "nav.review": "To confirm",
  "nav.diagnostics": "Diagnostics",
  "nav.planner": "Planner",
  "nav.projects": "Projects",
  "nav.sky": "Sky chart",
  "nav.weather": "Weather",
  "nav.settings": "Settings",
}
