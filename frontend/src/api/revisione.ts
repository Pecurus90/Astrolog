import { useQuery } from "@tanstack/react-query"

import { t } from "../i18n"
import { api } from "./client"

/** Le domande da confermare: la pagina, e il conto nella barra e nella Dashboard. */
export function useRevisione() {
  return useQuery({
    queryKey: ["review"],
    // [T] who changes the answers says so (Applica, the end of a scan, the gear forms invalidate
    // it): moving between pages or back to the window need not read the whole page again
    staleTime: 5 * 60 * 1000,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/review")
      if (error) throw new Error(t("review.failed"))
      return data
    },
  })
}
