import { Prova, Riga } from "./Riga"
import { TempoDellePose } from "./TempoDellePose"
import type { components } from "./api/schema"
import { cielo, t } from "./i18n"

type Pannello = components["schemas"]["ArchivePanel"]

/**
 * I pannelli di un mosaico, dentro la sua carta: **chiusi di suo**, e si aprono con un clic.
 *
 * - **La forma e' quella dei mosaici proposti** (`SezioneMosaici.tsx`): una riga per pannello, col
 *   nome, i frame, il tempo e il punto del cielo. Il punto dice QUALE pannello: due inquadrature
 *   dello stesso oggetto sarebbero due righe con lo stesso nome.
 * - **Un pannello senza oggetto lo dice** con una parola, non con un vuoto: le sue pose non sono
 *   legate a nessun oggetto, e una riga senza nome non si legge. Un oggetto fuori catalogo ha un
 *   nome, e si scrive quello.
 * - **L'ordine e' quello del backend**, dal pannello a cui e' andato piu' tempo.
 */
export function PannelliDelMosaico({ pannelli }: { pannelli: Pannello[] }) {
  if (pannelli.length === 0) return null
  return (
    <details className="as-carta__piede as-carta__piede--prosa">
      <summary>{t("archive.panels.open")}</summary>
      <ul className="as-elenco">
        {/* L'indice come chiave: l'elenco non si riordina qui, e due pannelli di corredi diversi
            possono avere lo stesso centro. */}
        {pannelli.map((p, i) => (
          <li key={i}>
            <Riga
              nome={p.object ?? t("archive.panel.noObject")}
              nomeDiCatalogo={p.object !== null}
              frames={p.frames}
              dettagli={
                <>
                  <TempoDellePose secondi={p.integration_s} senzaTempo={p.untimed} />{" "}
                  <Prova>{t("review.mosaics.where", { dove: cielo(p.ra_deg, p.dec_deg) })}</Prova>
                </>
              }
            />
          </li>
        ))}
      </ul>
    </details>
  )
}
