import type { Prova } from "./Domanda"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"

type Soggetti = components["schemas"]["Subjects"]
type Soggetto = components["schemas"]["Subject"]
type Strumenti = components["schemas"]["FrameRig"]

// Quanti oggetti si nominano: oltre si dice quanti altri, perche' una camera copre anni di notti.
const PRIMI = 3

/** Gli oggetti nel campo, gia' in ordine dall'API: i primi per nome, poi quanti altri. */
function nominati(trovati: readonly Soggetto[]): string {
  const frames = (n: number) => t("review.frames", { n: numero(n) })
  const primi = trovati
    .slice(0, PRIMI)
    .map((s) => t("review.subjects.item", { nome: s.name, frame: frames(s.frames) }))
    .join(", ")
  const altri = trovati.length - PRIMI
  return altri > 0 ? `${primi} ${t("review.subjects.more", { n: numero(altri) })}` : primi
}

/** "Oggetti nel campo" da un elenco di oggetti; nessuna riga se l'elenco e' vuoto. */
export function provaDegliOggetti(trovati: readonly Soggetto[]): Prova[] {
  return trovati.length > 0 ? [{ nome: t("review.proof.inField"), righe: [nominati(trovati)] }] : []
}

/**
 * **Cosa hai ripreso** in un gruppo di frame, come righe delle prove: per rispondere senza andare
 * a memoria. I due vuoti restano due frasi: "non ha trovato niente" e "non ha ancora guardato"
 * non sono la stessa cosa. Uno zero non fa una riga.
 */
export function provaDeiSoggetti(soggetti: Soggetti): Prova[] {
  const { found, not_found, not_yet } = soggetti
  const frames = (n: number) => t("review.frames", { n: numero(n) })
  const aParte = [
    not_found > 0 && t("review.subjects.notFound", { frame: frames(not_found) }),
    not_yet > 0 && t("review.subjects.notYet", { frame: frames(not_yet) }),
  ].filter((x): x is string => typeof x === "string")
  return [
    ...provaDegliOggetti(found),
    ...(aParte.length > 0
      ? [{ nome: t("review.proof.others"), righe: [aParte.join(" \u00b7 ")] }]
      : []),
  ]
}

/** "Ottica e camera" dei frame: una riga per coppia, nell'ordine dell'API. */
export function provaDegliStrumenti(strumenti: readonly Strumenti[]): Prova[] {
  const righe = strumenti
    .map((s) => [s.optics, s.camera].filter(Boolean).join(" \u00b7 "))
    .filter(Boolean)
  return righe.length > 0 ? [{ nome: t("review.proof.rigs"), righe }] : []
}
