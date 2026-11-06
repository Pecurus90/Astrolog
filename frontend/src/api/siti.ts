import { useQuery } from "@tanstack/react-query"

import { t } from "../i18n"
import { api } from "./client"

/** I siti dichiarati: li leggono Stanotte e le Impostazioni, con la stessa chiave della cache. */
export function useSiti() {
  return useQuery({
    queryKey: ["sites"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/sites")
      if (error) throw new Error(t("settings.site.failed"))
      return data
    },
  })
}
