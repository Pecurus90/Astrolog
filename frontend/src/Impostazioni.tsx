import { Link, useLocation } from "react-router"

import { ImpostazioniBackup } from "./Backup"
import { Cartelle } from "./ImpostazioniCartelle"
import { Letture } from "./ImpostazioniLetture"
import { Riconoscitore } from "./ImpostazioniRiconoscitore"
import { Servizi } from "./ImpostazioniServizi"
import { Sito } from "./ImpostazioniSito"
import { t } from "./i18n"
import { type Sezione, sezioniAperte } from "./pagine"

/**
 * Impostazioni: una pagina sola, con dentro le sue sezioni.
 *
 * - **Ogni sezione ha il suo indirizzo**, ed e' un indirizzo vero e non un'ancora: il tasto
 *   indietro funziona e il collegamento si manda.
 * - **Una sezione senza `elemento` non esiste**: non e' una rotta e non compare qui.
 * - L'indirizzo della pagina apre la **prima sezione aperta**.
 */
export const SEZIONI: readonly Sezione[] = [
  { a: "/impostazioni/cartelle", chiave: "settings.folders", elemento: <Cartelle /> },
  { a: "/impostazioni/sito", chiave: "settings.site", elemento: <Sito /> },
  { a: "/impostazioni/riconoscitore", chiave: "settings.solver", elemento: <Riconoscitore /> },
  { a: "/impostazioni/servizi", chiave: "settings.services", elemento: <Servizi /> },
  { a: "/impostazioni/letture", chiave: "settings.readings", elemento: <Letture /> },
  { a: "/impostazioni/backup", chiave: "settings.backup", elemento: <ImpostazioniBackup /> },
]

export function Impostazioni() {
  const dove = useLocation()
  const aperte = sezioniAperte(SEZIONI)
  const qui = aperte.find((s) => s.a === dove.pathname) ?? aperte[0]
  if (!qui) return null

  return (
    <div className="as-pagina">
      <div className="as-impostazioni">
        <nav className="as-impostazioni__lato as-sezioni" aria-label={t("settings.sections")}>
          {aperte.map((s) => (
            // `aria-current="true"`, non `"page"`: lo dichiara il foglio, ed e' anche cio' su cui
            // accende la voce.
            <Link
              aria-current={s.a === qui.a ? "true" : undefined}
              className="as-sezioni__voce"
              key={s.a}
              to={s.a}
            >
              {t(s.chiave)}
            </Link>
          ))}
        </nav>
        <div className="as-impostazioni__corpo">{qui.elemento}</div>
      </div>
    </div>
  )
}
