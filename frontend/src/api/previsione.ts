import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { t } from "../i18n"
import { api } from "./client"
import type { components } from "./schema"

type Esito = components["schemas"]["WeatherRefreshOut"]["status"]

/** La previsione del sito predefinito: la leggono il Meteo e la Dashboard. Fuori dalla pagina Meteo,
 *  o la Dashboard se la scaricherebbe tutta. */
export function usePrevisione() {
  return useQuery({
    queryKey: ["weather"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/weather")
      if (error) throw new Error(t("weather.failed"))
      return data
    },
  })
}

/** Rilegge la previsione e Stanotte, che dice la notte in corso dalla stessa previsione. */
export function useRileggi() {
  const cache = useQueryClient()
  return () =>
    Promise.all(["weather", "tonight"].map((q) => cache.invalidateQueries({ queryKey: [q] })))
}

/** Aggiorna: chiede la previsione subito e rilegge. Lo usano il Meteo e la Dashboard. */
export function useAggiorna() {
  const rileggi = useRileggi()
  return useMutation({
    mutationFn: async (): Promise<Esito> => {
      const { data, error } = await api.POST("/api/v1/weather/refresh")
      if (error) throw new Error(t("weather.refresh.failed"))
      return data.status
    },
    onSuccess: rileggi,
  })
}
