import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { AzioniDelVuoto, Vuoto } from "./Vuoto"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, fa, giorno, orario, t } from "./i18n"
import { SchedaDellaNotte, TendenzaDellaNotte, VoceDellaNotte, nomeDellaNotte } from "./NotteDelMeteo"

type Meteo = components["schemas"]["WeatherOut"]
type Esito = components["schemas"]["WeatherRefreshOut"]["status"]

/**
 * Il **Meteo** nel disegno v27/v28 (forma C, una notte alla volta): in testa il sito, quando e'
 * arrivata la previsione, il modello e *Aggiorna*; sotto la fila delle sette notti, le prime tre
 * ora per ora e le altre in tendenza, e la scheda della notte scelta.
 *
 * - **Qui non si calcola niente**: verdetto, giudizi, ore serene, ordine e scale arrivano scritti
 *   per ogni modello, e cambiare modello e' leggere un'altra riga.
 * - **Un servizio che tace non toglie niente**: resta la previsione di prima con la sua ora.
 * - Il telefono vede gli stessi controlli: il foglio mostra il segmentato o il menu secondo la
 *   larghezza, la pagina li scrive tutti e due.
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
  const rileggi = () => Promise.all(["weather", "tonight"].map((q) => cache.invalidateQueries({ queryKey: [q] })))
  const aggiorna = useMutation({
    mutationFn: async (): Promise<Esito> => {
      const { data, error } = await api.POST("/api/v1/weather/refresh")
      if (error) throw new Error(t("weather.refresh.failed"))
      return data.status
    },
    // anche Stanotte, che dice la notte in corso dalla stessa previsione
    onSuccess: rileggi,
  })
  const modello = useMutation({
    mutationFn: async (scelto: string) => {
      const { error } = await api.PATCH("/api/v1/settings", { body: { values: { weather_model: scelto } } })
      if (error) throw new Error(t("weather.model.failed"))
    },
    onSuccess: rileggi,
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
      {detto?.site && detto.missing === "no_timezone" && (
        <Avviso esito="allarme" pagina azioni={<Bottone a="/impostazioni/sito">{t("weather.noTimezone.how")}</Bottone>}>
          {t("weather.noTimezone")}
        </Avviso>
      )}
      {detto?.site && detto.missing === null && (
        <div className="as-meteo">
          <Testa
            detto={detto}
            aggiorna={() => aggiorna.mutate()}
            occupato={aggiorna.isPending}
            scegli={(m) => modello.mutate(m)}
            cambiando={modello.isPending}
          />
          {aggiorna.error && <Avviso esito="allarme">{aggiorna.error.message}</Avviso>}
          {aggiorna.data && aggiorna.data !== "ok" && (
            <Avviso esito="attesa" pagina>{t(`weather.status.${aggiorna.data}`)}</Avviso>
          )}
          {modello.error && <Avviso esito="allarme">{modello.error.message}</Avviso>}
          <SeeingCheTace seeing={detto.seeing} />
          {detto.fetched_at === null && (
            <Avviso esito="attesa" pagina titolo={t("weather.never")}>
              {t("weather.never.how")}
            </Avviso>
          )}
          {detto.fetched_at !== null && detto.nights.length === 0 && <p>{t("weather.noNights")}</p>}
          {detto.nights.length > 0 && <Notti detto={detto} />}
          {detto.fetched_at !== null && <Fonti detto={detto} />}
        </div>
      )}
    </div>
  )
}

/** La testa: dove, da quanto e' arrivata la previsione (e il seeing, che ha un'eta' sua), il
 *  modello e il pulsante. */
function Testa({
  detto,
  aggiorna,
  occupato,
  scegli,
  cambiando,
}: {
  detto: Meteo
  aggiorna: () => void
  occupato: boolean
  scegli: (m: string) => void
  cambiando: boolean
}) {
  const seeing = detto.sources.find((f) => f.source === "meteoblue")
  return (
    <header className="as-meteo__testa">
      <div className="as-meteo__dice">
        <p className="as-soprattitolo">{t("weather.head.where", { sito: detto.site ?? "" })}</p>
        <p className="as-meteo__arrivo">
          {[
            detto.fetched_at === null
              ? null
              : t("weather.head.arrived", { giorno: giorno(detto.fetched_at), ora: orario(detto.fetched_at), fa: fa(detto.fetched_at) }),
            seeing ? t("weather.head.seeing", { giorno: giorno(seeing.fetched_at), ora: orario(seeing.fetched_at), fa: fa(seeing.fetched_at) }) : null,
            t("weather.head.siteTime"),
          ]
            .filter(Boolean)
            .join(" \u00b7 ")}
        </p>
      </div>
      <Bottone onClick={aggiorna} disabled={occupato}>
        {occupato ? t("weather.refreshing") : t("weather.refresh")}
      </Bottone>
      <div className="as-meteo__modello">
        <span className="as-meteo__solo-largo" id="meteo-modello">
          {t("weather.model")}
        </span>
        <div className="as-segmentato as-meteo__solo-largo" role="group" aria-labelledby="meteo-modello">
          {detto.models.map((m) => (
            <button key={m} type="button" className="as-segmentato__voce" aria-pressed={m === detto.model}
              disabled={cambiando} onClick={() => scegli(m)}>
              {t(`weather.model.${m}` as Chiave)}
            </button>
          ))}
        </div>
        <MenuDelModello detto={detto} scegli={scegli} cambiando={cambiando} />
      </div>
    </header>
  )
}

/** Sul telefono il modello si sceglie da un elenco: ogni voce dice cos'e'. */
function MenuDelModello({ detto, scegli, cambiando }: { detto: Meteo; scegli: (m: string) => void; cambiando: boolean }) {
  const [aperto, setAperto] = useState(false)
  return (
    <div className="as-menu as-menu--telefono">
      <button className="as-menu__apri" type="button" aria-expanded={aperto} onClick={() => setAperto(!aperto)}>
        <span>{t("weather.model")}</span>
        <b>{t(`weather.model.${detto.model}` as Chiave)}</b>
        <i aria-hidden="true">{"\u25be"}</i>
      </button>
      <ul className="as-menu__voci as-menu__voci--elenco" role="menu" hidden={!aperto}>
        {detto.models.map((m) => (
          <li key={m}>
            <button className="as-menu__voce" type="button" role="menuitemradio" aria-checked={m === detto.model} disabled={cambiando}
              onClick={() => {
                setAperto(false)
                scegli(m)
              }}>
              <span className="as-menu__nome">{t(`weather.model.${m}` as Chiave)}</span>
              <span className="as-menu__dove">{t(`weather.model.${m}.what` as Chiave)}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

/** La fila delle notti e la scheda di quella scelta: una sola aperta alla volta. */
function Notti({ detto }: { detto: Meteo }) {
  const [scelta, setScelta] = useState(0)
  const aperta = detto.nights[scelta] ?? detto.nights[0]
  const voce = (n: Meteo["nights"][number], i: number) => (
    <button key={n.night} type="button" role="tab" id={`voce-${n.night}`} aria-selected={n === aperta}
      aria-controls={`notte-${n.night}`} onClick={() => setScelta(i)}
      className={n.trend ? "as-voce-notte as-voce-notte--tendenza" : "as-voce-notte"}>
      <VoceDellaNotte notte={n} />
    </button>
  )
  const piene = detto.nights.flatMap((n, i) => (n.trend ? [] : [voce(n, i)]))
  const tendenza = detto.nights.flatMap((n, i) => (n.trend ? [voce(n, i)] : []))
  return (
    <>
      <div className="as-notti" role="tablist" aria-label={t("weather.nights")}>
        <div className="as-notti__gruppo">
          <p>{t("weather.nights.hourly")}</p>
          <div className="as-notti__voci">{piene}</div>
        </div>
        {tendenza.length > 0 && (
          <div className="as-notti__gruppo">
            <p>{t("weather.nights.trend")}</p>
            <div className="as-notti__voci">{tendenza}</div>
          </div>
        )}
      </div>
      {aperta && (
        <section id={`notte-${aperta.night}`} role="tabpanel" aria-labelledby={`voce-${aperta.night}`}
          aria-label={nomeDellaNotte(aperta, aperta === detto.nights[0])}
          className={aperta.trend ? "as-meteo__scheda as-meteo__tendenza" : "as-meteo__scheda"}>
          {aperta.trend ? (
            <TendenzaDellaNotte notte={aperta} />
          ) : (
            <SchedaDellaNotte notte={aperta} prima={aperta === detto.nights[0]} scale={detto.scales} seeing={detto.seeing} />
          )}
        </section>
      )}
    </>
  )
}

/** Meteoblue che tace o risponde storto: resta il seeing di prima, con la sua eta' in testa. Il
 *  seeing che manca del tutto lo dice la sua carta. */
function SeeingCheTace({ seeing }: { seeing: Meteo["seeing"] }) {
  // senza un seeing di prima non c'e' niente che resti: lo dice la sua carta
  if (seeing.source === null) return null
  if (seeing.meteoblue !== "unreachable" && seeing.meteoblue !== "bad_answer") return null
  return <Avviso esito="attesa" pagina>{t(`weather.seeing.why.${seeing.meteoblue}`)}</Avviso>
}

/** Le fonti, con le parole che i servizi chiedono; una fonte che non ha scritto niente non si
 *  cita, e una che la pagina non conosce nemmeno. */
function Fonti({ detto }: { detto: Meteo }) {
  const cams = detto.sources.find((f) => f.source === "cams")
  return (
    <ul className="as-meteo__fonti">
      <li>
        {t("weather.sources.forecast")} <a href="https://open-meteo.com/">{t("weather.attribution")}</a>
      </li>
      {detto.sources.some((f) => f.source === "meteoblue") && (
        <li>
          <a href="https://www.meteoblue.com/">{t("weather.attribution.meteoblue")}</a>
        </li>
      )}
      {cams && <li>{t("weather.attribution.cams", { anno: cams.fetched_at.slice(0, 4) })}</li>}
    </ul>
  )
}
