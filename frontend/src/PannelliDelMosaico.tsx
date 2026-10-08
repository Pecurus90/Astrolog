import { senzaTempo } from "./RigaDellArchivio"
import type { components } from "./api/schema"
import { numero, ore, t } from "./i18n"

type Pannello = components["schemas"]["ArchivePanel"]

/**
 * I pannelli di un mosaico, sotto la sua carta (disegno v31, `.as-pannelli`): una riga per
 * pannello, col numero, l'oggetto, i frame e le ore.
 *
 * - **Il numero dice quale pannello**: il punto del cielo non si scrive (Marco, 8/10/2026, come
 *   nella tavola).
 * - **Un pannello senza oggetto lo dice** con una parola, non con un vuoto.
 * - **L'ordine e' quello del backend**, dal pannello a cui e' andato piu' tempo.
 */
export function PannelliDelMosaico({ pannelli }: { pannelli: Pannello[] }) {
  if (pannelli.length === 0) return null
  return (
    <ol className="as-pannelli" aria-label={t("archive.panels")}>
      {/* L'indice come chiave: l'elenco non si riordina qui, e due pannelli di corredi diversi
          possono avere lo stesso centro. */}
      {pannelli.map((p, i) => (
        <li key={i}>
          <span className="as-pannelli__n">{i + 1}</span>
          {p.object !== null ? (
            <span className="as-pannelli__ogg">{p.object}</span>
          ) : (
            <span className="as-pannelli__nessuno">{t("archive.panel.noObject")}</span>
          )}
          <span className="as-pannelli__cifre">
            {p.integration_s > 0
              ? t("filters.legend.timed", {
                  n: numero(p.frames),
                  h: ore(p.integration_s),
                })
              : t("filters.legend.untimed", { n: numero(p.frames) })}
            {p.integration_s > 0 && p.untimed > 0 && ` ${senzaTempo(p.untimed)}`}
          </span>
        </li>
      ))}
    </ol>
  )
}
