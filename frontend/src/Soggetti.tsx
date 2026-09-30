import type { components } from "./api/schema"
import { numero, t } from "./i18n"

type Soggetti = components["schemas"]["Subjects"]

// Quanti oggetti si nominano: oltre si dice quanti altri, perche' una camera copre anni di notti.
const PRIMI = 3

/**
 * **Cosa hai ripreso** in un gruppo di pose, accanto alla domanda: per rispondere senza andare a
 * memoria. Una riga sola, uguale in tutte le sezioni che chiedono per gruppo.
 *
 * - Gli oggetti arrivano gia' in ordine dall'API; qui si nominano i primi e si conta il resto.
 * - I due vuoti restano due frasi: "non ha trovato niente" e "non ha ancora guardato o non e'
 *   riuscito" non sono la stessa cosa, e un vuoto a zero non si scrive.
 */
export function Soggetti({ soggetti }: { soggetti: Soggetti }) {
  const { found, not_found, not_yet } = soggetti
  const pose = (n: number) => t("review.frames", { n: numero(n) })
  const parti: string[] = []
  if (found.length > 0) {
    const nominati = found
      .slice(0, PRIMI)
      .map((s) => t("review.subjects.item", { nome: s.name, pose: pose(s.frames) }))
      .join(", ")
    const altri = found.length - PRIMI
    const oggetti = altri > 0 ? `${nominati} ${t("review.subjects.more", { n: numero(altri) })}` : nominati
    parti.push(t("review.subjects", { oggetti }))
  }
  if (not_found > 0) parti.push(t("review.subjects.notFound", { pose: pose(not_found) }))
  if (not_yet > 0) parti.push(t("review.subjects.notYet", { pose: pose(not_yet) }))
  return <span>{parti.join("; ")}</span>
}
