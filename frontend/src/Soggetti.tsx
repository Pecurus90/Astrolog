import type { components } from "./api/schema"
import { numero, t } from "./i18n"

type Soggetti = components["schemas"]["Subjects"]

// Quanti oggetti si nominano: oltre si dice quanti altri, perche' una camera copre anni di notti.
const PRIMI = 3

/**
 * **Cosa hai ripreso** in un gruppo di frame, come righe della tabellina di una domanda: per
 * rispondere senza andare a memoria.
 *
 * - Gli oggetti arrivano gia' in ordine dall'API; qui si nominano i primi e si conta il resto.
 * - I due vuoti restano due frasi: "non ha trovato niente" e "non ha ancora guardato o non e'
 *   riuscito" non sono la stessa cosa. Uno zero non fa una riga.
 */
export function provaDeiSoggetti(soggetti: Soggetti): { nome: string; dato: string }[] {
  const { found, not_found, not_yet } = soggetti
  const pose = (n: number) => t("review.frames", { n: numero(n) })
  const righe: { nome: string; dato: string }[] = []
  if (found.length > 0) {
    const nominati = found
      .slice(0, PRIMI)
      .map((s) => t("review.subjects.item", { nome: s.name, pose: pose(s.frames) }))
      .join(", ")
    const altri = found.length - PRIMI
    righe.push({
      nome: t("review.proof.objects"),
      dato: altri > 0 ? `${nominati} ${t("review.subjects.more", { n: numero(altri) })}` : nominati,
    })
  }
  const aParte = [
    not_found > 0 && t("review.subjects.notFound", { pose: pose(not_found) }),
    not_yet > 0 && t("review.subjects.notYet", { pose: pose(not_yet) }),
  ].filter(Boolean)
  if (aParte.length > 0) righe.push({ nome: t("review.proof.others"), dato: aParte.join(" \u00b7 ") })
  return righe
}
