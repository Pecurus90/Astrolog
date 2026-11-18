import { useQuery } from "@tanstack/react-query"
import { useEffect } from "react"

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

// Round not written yet for a new site: ask again soon, the board's scuro meanwhile
const SENZA_ORA_MS = 60_000
// past the change by a breath, so the server's clock is past it too
const DOPO_IL_CAMBIO_MS = 1_000

/**
 * Automatico (tavola v82): the API says the mode in force and `until` when it changes; the
 * settings are read again then. Mounted once, by the app.
 */
export function useCambioDelTema() {
  const preferenze = usePreferenze()
  const dati = preferenze.data
  const automatico = dati?.values.theme_mode === "automatico"
  const quando = dati?.theme_now?.until ?? null
  const senzaOra = automatico && dati?.theme_site != null && dati.theme_now == null
  const { refetch } = preferenze
  useEffect(() => {
    if (!automatico) return
    let timer: ReturnType<typeof setTimeout> | undefined
    let spento = false
    const arma = (fino: string | null, senza: boolean) => {
      const attesa = fino
        ? Math.max(0, Date.parse(fino) - Date.now()) + DOPO_IL_CAMBIO_MS
        : senza
          ? SENZA_ORA_MS
          : null
      if (attesa === null) return
      timer = setTimeout(() => {
        void refetch().then(({ data }) => {
          // same answer again (round late, clock ahead): the effect does not rerun, re-arm here
          const ancora = data?.values.theme_mode === "automatico"
          const poi = data?.theme_now?.until ?? null
          const vuota = data?.theme_site != null && data.theme_now == null
          if (!spento && ancora && poi === fino && vuota === senza) arma(poi, vuota)
        })
      }, attesa)
    }
    arma(quando, senzaOra)
    return () => {
      spento = true
      clearTimeout(timer)
    }
  }, [automatico, quando, senzaOra, refetch])
}
