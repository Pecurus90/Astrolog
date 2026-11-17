import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createContext, useContext } from "react"

import { motivo } from "./api/motivo"
import type { components } from "./api/schema"
import { type Chiave, t } from "./i18n"

/**
 * La scrittura dei moduli dell'Attrezzatura e il perche' di un rifiuto. La usano i gesti che fanno
 * nascere qualcosa e quelli che correggono una riga; il modulo e' `componenti/Modulo`.
 *
 * **Un rifiuto si legge**: il backend manda un codice, qui diventa una frase -- un nome che possiedi
 * gia' non e' un errore dell'app, e' una cosa che devi sapere.
 */

/** What a gear write answers: how many frames went back to be read again. */
export type Scritto = Pick<components["schemas"]["GearWritten"], "requeued">

/** Who shows "{n} frame da rielaborare": the Gear page; elsewhere nobody. */
export const Rielaborati = createContext<(frame: number) => void>(() => undefined)

const RIFIUTI: Record<string, Chiave> = {
  name_taken: "gear.write.nameTaken",
  worker_busy: "gear.write.busy",
  merge_refused: "gear.write.mergeRefused",
  not_found: "gear.write.notFound",
  rig_exists: "gear.write.rigExists",
  wrong_kind: "gear.write.wrongKind",
  spelling_taken: "gear.write.spellingTaken",
}

/** Manda la scrittura, rilegge la pagina e chiude. La pagina si rilegge **dall'API**: cio' che si
 *  vede dopo e' cio' che il backend ha scritto davvero, non cio' che abbiamo mandato. */
export function useScrittura(manda: () => Promise<Scritto | undefined>, onFatto: () => void) {
  const coda = useQueryClient()
  const rielabora = useContext(Rielaborati)
  return useMutation({
    mutationFn: manda,
    onSuccess: async (scritto) => {
      // frames whose sky changed: the page says how many (board v82 `rielab`)
      if (scritto?.requeued) rielabora(scritto.requeued)
      // Anche `review`: una camera scritta senza pixel **alza** il conto delle domande aperte, e
      // quel numero sta nella barra di sinistra. Senza questa riga resterebbe fermo finche' non
      // si cambia pagina.
      await Promise.all([
        coda.invalidateQueries({ queryKey: ["gear"] }),
        coda.invalidateQueries({ queryKey: ["review"] }),
      ])
      onFatto()
    },
  })
}

/** The refusal in words, for the delivery's Modulo; null without one. */
export function rifiutoDetto(errore: unknown): string | null {
  return errore ? t(motivo(errore, RIFIUTI, "gear.write.failed")) : null
}
