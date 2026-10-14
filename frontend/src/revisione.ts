import { useQuery } from "@tanstack/react-query"

import { api } from "./api/client"
import { t } from "./i18n"

/** Le domande da confermare: il conto lo leggono la barra e la Dashboard. */
export function useRevisione() {
  return useQuery({
    queryKey: ["review"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/review")
      if (error) throw new Error(t("review.failed"))
      return data
    },
  })
}
