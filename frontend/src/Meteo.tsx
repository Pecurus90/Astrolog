import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { AzioniDelVuoto, Vuoto } from "./Vuoto"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, giorno, orario, t } from "./i18n"
import { UnaNotte } from "./NotteDelMeteo"

type Meteo = components["schemas"]["WeatherOut"]
type Esito = components["schemas"]["WeatherRefreshOut"]["status"]

/**
 * Il **Meteo**: le prossime notti del sito di casa, col verdetto, le ore utili e cosa pesa.
 *
 * - **Qui non si calcola niente**: verdetto, fattori e ore utili arrivano scritti per ogni
 *   modello, e cambiare modello e' leggere un'altra riga.
 * - **Nuda, non incompleta** (`docs/domini/meteo.md`, *Niente grafica*): i dati in righe e
 *   tabelle; i grafici arrivano col design.
 * - **Un servizio che tace non toglie niente**: resta la previsione di prima con la sua ora.
 * - Le notti le disegna `NotteDelMeteo.tsx`.
 */
export function Meteo() {
  const cache = useQueryClient()
  const meteo = useQuery({
    queryKey: ["weather"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/weather")
      if (error) throw new Error(t("weather.failed"))
      return data
    },
  })
  const aggiorna = useMutation({
    mutationFn: async (): Promise<Esito> => {
      const { data, error } = await api.POST("/api/v1/weather/refresh")
      if (error) throw new Error(t("weather.refresh.failed"))
      return data.status
    },
    // anche Stanotte, che dice la notte in corso dalla stessa previsione
    onSuccess: () => Promise.all(["weather", "tonight"].map((q) => cache.invalidateQueries({ queryKey: [q] }))),
  })
  const modello = useMutation({
    mutationFn: async (scelto: string) => {
      const { error } = await api.PATCH("/api/v1/settings", { body: { values: { weather_model: scelto } } })
      if (error) throw new Error(t("weather.model.failed"))
    },
    onSuccess: () => Promise.all(["weather", "tonight"].map((q) => cache.invalidateQueries({ queryKey: [q] }))),
  })
  const detto = meteo.data

  return (
    <div className="as-pagina">
      {meteo.isPending && <p>{t("weather.loading")}</p>}
      {meteo.error && <Avviso esito="allarme">{meteo.error.message}</Avviso>}
      {detto && detto.site === null && (
        <Vuoto titolo="weather.noSite.title" perche="weather.noSite.why" sotto={1}>
          <AzioniDelVuoto>
            <Bottone a="/impostazioni/sito">{t("weather.noSite.how")}</Bottone>
          </AzioniDelVuoto>
        </Vuoto>
      )}
      {detto?.site && detto.missing === "no_timezone" && <p>{t("weather.noTimezone")}</p>}
      {detto?.site && detto.missing === null && (
        <>
          <p>
            {t("weather.site", { sito: detto.site })}{" "}
            {detto.fetched_at
              ? t("weather.fetched", { giorno: giorno(detto.fetched_at), ora: orario(detto.fetched_at) })
              : t("weather.never")}
          </p>
          <Bottone onClick={() => aggiorna.mutate()} disabled={aggiorna.isPending}>
            {aggiorna.isPending ? t("weather.refreshing") : t("weather.refresh")}
          </Bottone>
          {aggiorna.error && <Avviso esito="allarme">{aggiorna.error.message}</Avviso>}
          {aggiorna.data && aggiorna.data !== "ok" && (
            <Avviso esito="attesa">{t(`weather.status.${aggiorna.data}`)}</Avviso>
          )}
          <DaDoveIlSeeing seeing={detto.seeing} />
          <Modelli detto={detto} scegli={(m) => modello.mutate(m)} occupato={modello.isPending} />
          {modello.error && <Avviso esito="allarme">{modello.error.message}</Avviso>}
          {detto.fetched_at && detto.nights.length === 0 && <p>{t("weather.noNights")}</p>}
          {detto.nights.map((n) => (
            <UnaNotte key={n.night} notte={n} piene={detto.full_nights} />
          ))}
          <p>
            <a href="https://open-meteo.com/">{t("weather.attribution")}</a>
          </p>
          {detto.sources.map((f) => (
            <Citazione key={f.source} fonte={f.source} arrivata={f.fetched_at} />
          ))}
        </>
      )}
    </div>
  )
}

/** Lo switch del modello: una scelta sola fra quelli che la previsione chiede. */
function Modelli({ detto, scegli, occupato }: { detto: Meteo; scegli: (m: string) => void; occupato: boolean }) {
  return (
    <fieldset>
      <legend>{t("weather.model")}</legend>
      {detto.models.map((m) => (
        <label key={m}>
          <input
            type="radio"
            name="weather-model"
            value={m}
            checked={detto.model === m}
            disabled={occupato}
            onChange={() => scegli(m)}
          />{" "}
          {t(`weather.model.${m}` as Chiave)}
        </label>
      ))}
    </fieldset>
  )
}

/** Come si cita una fonte del cielo, per nome: una fonte che la pagina non conosce non si cita con
 *  le parole di un'altra. */
function Citazione({ fonte, arrivata }: { fonte: string; arrivata: string }) {
  if (fonte === "7timer")
    return (
      <p>
        <a href="https://www.7timer.info/">{t("weather.attribution.7timer")}</a>
      </p>
    )
  if (fonte === "meteoblue")
    return (
      <p>
        <a href="https://www.meteoblue.com/">{t("weather.attribution.meteoblue")}</a>
      </p>
    )
  if (fonte === "cams") return <p>{t("weather.attribution.cams", { anno: arrivata.slice(0, 4) })}</p>
  return null
}

/** Da dove viene il seeing, e -- quando c'e' la chiave e Meteoblue non l'ha dato -- perche'. */
function DaDoveIlSeeing({ seeing }: { seeing: Meteo["seeing"] }) {
  if (seeing.source === null) return null
  const perche = seeing.meteoblue && seeing.meteoblue !== "ok" ? (`weather.seeing.why.${seeing.meteoblue}` as const) : null
  return (
    <p>
      {t(seeing.source === "meteoblue" ? "weather.seeing.meteoblue" : "weather.seeing.7timer")}{" "}
      {perche && t(perche)}
    </p>
  )
}
