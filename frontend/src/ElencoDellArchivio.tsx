import { Costellazione, Filtri, Mosaico, Nome, NonSiSa, Tipo, oreDi, senzaTempo } from "./RigaDellArchivio"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"

type Riga = components["schemas"]["ArchiveObject"]

/**
 * L'Archivio **a colonne** (disegno v31): il caso "confronto". Chi ha piu' ore, chi ha piu' frame.
 *
 * - **Le celle che non sanno lo dicono** con una parola e col tondo tratteggiato dell'ignoto, mai
 *   con un trattino (`handoff/design-archivio.md`).
 * - **Sotto i 720 px il foglio impila ogni riga**: le classi `as-archivio__col-*` dicono al foglio
 *   quale cella e' quale, e senza di loro sul telefono resterebbe una colonna di numeri.
 * - **I numeri stanno in `as-tabella__num`**, incolonnati a destra: due righe si confrontano a
 *   occhio solo se le cifre stanno una sopra l'altra.
 */
export function ElencoDellArchivio({ righe }: { righe: Riga[] }) {
  return (
    <div className="as-archivio__guscio">
      <table className="as-tabella as-archivio__tabella">
        <caption className="as-solo-lettori">{t("archive.table.caption")}</caption>
        <thead>
          <tr>
            <th scope="col">{t("archive.column.object")}</th>
            <th scope="col">{t("archive.column.type")}</th>
            <th scope="col">{t("archive.column.constellation")}</th>
            <th scope="col" className="as-tabella__num">
              {t("archive.column.frames")}
            </th>
            <th scope="col" className="as-tabella__num">
              {t("archive.column.time")}
            </th>
            <th scope="col">{t("archive.column.filters")}</th>
            <th scope="col">{t("archive.column.labels")}</th>
          </tr>
        </thead>
        <tbody>
          {righe.map((riga) => (
            <UnaRiga key={riga.key} riga={riga} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

function UnaRiga({ riga }: { riga: Riga }) {
  const ore = oreDi(riga.integration_s)
  return (
    <tr>
      <td>
        <Nome riga={riga} inRiga />
      </td>
      <td className="as-archivio__col-tipo">
        <Tipo riga={riga} />
      </td>
      <td className="as-archivio__col-cost">
        <Costellazione riga={riga} />
      </td>
      <td className="as-tabella__num as-archivio__col-frame">{numero(riga.frames)}</td>
      <td className="as-tabella__num as-archivio__col-ore">
        {/* mai "0 h": senza durata nei file si dicono i frame "senza tempo" */}
        {ore ?? <span className="as-archivio__ore--parole">{senzaTempo(riga.untimed)}</span>}
        {ore !== null && riga.untimed > 0 && (
          <span className="as-archivio__senza">{senzaTempo(riga.untimed)}</span>
        )}
      </td>
      <td className="as-archivio__col-filtri">
        {riga.filters.length > 0 ? <Filtri riga={riga} /> : <NonSiSa>{t("archive.unknown")}</NonSiSa>}
      </td>
      {/* Un oggetto senza segni non e' un dato che non si sa: e' vuoto davvero, e si tace. */}
      <td className="as-archivio__col-mosaico">
        <Mosaico riga={riga} />
      </td>
    </tr>
  )
}
