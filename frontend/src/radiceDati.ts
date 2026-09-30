/**
 * **Dove l'app vede i dati**: la radice del container sul NAS, niente sul computer.
 *
 * Sta in una casa sola perche' la stessa risposta decide due cose lontane fra loro -- se il passo
 * delle cartelle si sfoglia o si scrive, e quale riga ne spiega il perche' in cima alla carta --
 * e la stessa domanda scritta in due componenti sarebbe la stessa verita' in due posti.
 *
 * Vincoli non ovvi:
 *
 * - **Non cambia finche' l'app gira** (e' la forma dei percorsi del processo), quindi si chiede
 *   una volta e non si rilegge a ogni ritorno sul passo o sulla finestra.
 * - **Mentre non si sa, si risponde "computer"**: e' la strada che funziona sempre -- il percorso
 *   si scrive a mano -- mentre sfogliare senza radice non porterebbe da nessuna parte.
 */
import { useQuery } from "@tanstack/react-query"

import { api } from "./api/client"
import { t } from "./i18n"

export function useRadiceDati(): string | null {
  const dove = useQuery({
    queryKey: ["path-info"],
    staleTime: Infinity,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/folders/path-info")
      if (error) throw new Error(t("wizard.folders.lookFailed"))
      return data
    },
  })
  return dove.data?.data_root ?? null
}
