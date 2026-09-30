import { useQuery } from "@tanstack/react-query"

import { api } from "./api/client"
import { t } from "./i18n"

/**
 * Le preferenze dell'utente, lette una volta: le chiede l'app all'avvio, per sapere se c'e' il primo
 * avvio da fare, e le rilegge chi mostra una preferenza. Una lettura sola, sotto la stessa chiave,
 * cosi' chi scrive aggiorna tutti insieme.
 */
export function usePreferenze() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/settings")
      if (error) throw new Error(t("settings.failed"))
      return data
    },
  })
}
