import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { type KeyboardEvent, type ReactNode, useEffect, useId, useRef, useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { AzioniDelVuoto, Vuoto } from "./Vuoto"
import { parola } from "./CartaDelParametro"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { useColonnaStretta } from "./colonna"
import { giraIlFuoco, useRiquadro } from "./riquadro"
import { type Chiave, fa, giorno, orario, t } from "./i18n"
import { CapoDellaNotte, CapoDellaTendenza, NotaDellaTendenza, SchedaDellaNotte, TendenzaDellaNotte, VoceDellaNotte, idDellaCarta, nomeDellaNotte, quando } from "./NotteDelMeteo"
import { Semaforo } from "./Semaforo"

type Meteo = components["schemas"]["WeatherOut"]
type Notte = Meteo["nights"][number]
type Codice = Notte["measures"][number]["code"]
type Esito = components["schemas"]["WeatherRefreshOut"]["status"]
type Richiesta = NonNullable<Meteo["last_request"]>
// l'ultima richiesta andata storta: da quando, e come
type Tace = { at: Richiesta["at"]; status: Exclude<Richiesta["status"], "ok"> }

/** La previsione del sito di casa: la leggono il Meteo e la Dashboard. */
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

/** Cio' che la pagina dice prima della previsione: che arriva, che non e' arrivata, o che senza un
 *  sito di casa non arrivera'. Lo dicono il Meteo e la Dashboard; il Meteo ha il suo senza sito. */
export function PrimaDellaPrevisione({ meteo, senzaSito }: { meteo: ReturnType<typeof usePrevisione>; senzaSito?: ReactNode }) {
  return (
    <>
      {meteo.isPending && <p>{t("weather.loading")}</p>}
      {meteo.error && <Avviso esito="allarme">{meteo.error.message}</Avviso>}
      {meteo.data?.site === null && (senzaSito ?? (
        <Vuoto titolo="weather.noSite.title" perche="weather.noSite.why" sotto={1}>
          <AzioniDelVuoto>
            <Bottone a="/impostazioni/sito">{t("weather.noSite.how")}</Bottone>
          </AzioniDelVuoto>
        </Vuoto>
      ))}
    </>
  )
}

/** Senza sito, come la tavola meteo-stati: la testa dice solo Meteo, l'avviso chiede il sito. */
function SenzaSito() {
  return (
    <div className="as-meteo">
      <header className="as-meteo__testa">
        <div className="as-meteo__dice">
          <p className="as-soprattitolo">{t("nav.weather")}</p>
        </div>
      </header>
      <Avviso esito="attesa" pagina titolo={t("weather.noSite.title")}
        azioni={<Bottone verso="primario" a="/impostazioni/sito">{t("weather.noSite.how")}</Bottone>}>
        {t("weather.noSite.why")}
      </Avviso>
    </div>
  )
}

/**
 * Il **Meteo** nel disegno v27/v28 (forma C, una notte alla volta): in testa il sito, quando e'
 * arrivata la previsione, il modello e *Aggiorna*; sotto la fila delle sette notti, le prime tre
 * ora per ora e le altre in tendenza, e la scheda della notte scelta.
 *
 * - **Qui non si calcola niente**: verdetto, giudizi, ore serene, ordine e scale arrivano scritti
 *   per ogni modello, e cambiare modello e' leggere un'altra riga.
 * - **Un servizio che tace non toglie niente**: resta la previsione di prima con la sua ora.
 * - **Il telefono ha un markup suo** (foglio v37, classi `as-tel-`): sotto la soglia della colonna
 *   il verdetto va in testa e apre gli altri fattori, le misure sono carte piccole. I dati sono
 *   gli stessi.
 */
export function Meteo() {
  const cache = useQueryClient()
  const meteo = usePrevisione()
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
  const [stretta, misura] = useColonnaStretta()
  // la notte scelta e, sul telefono, la carta aperta: una notte nuova richiude la carta
  const [scelta, setScelta] = useState(0)
  const [carta, setCarta] = useState<Codice | null>(null)
  const aperta = detto?.nights[scelta] ?? detto?.nights[0]
  // senza notti il telefono ha la testa degli stati, come il desktop (tavola meteo-stati v37)
  const telefono = stretta && aperta !== undefined
  const r = detto?.last_request
  const tace: Tace | null = r && r.status !== "ok" ? { at: r.at, status: r.status } : null
  const senzaPrevisione = detto?.fetched_at === null || detto?.nights.length === 0
  const scegliNotte = (i: number) => {
    setScelta(i)
    setCarta(null)
  }

  // gli stessi comandi nelle due teste, larga e telefono; se il servizio tace e la previsione vale
  // ancora, Aggiorna sta solo nella riga che lo dice
  const comandi = {
    aggiorna: tace && !senzaPrevisione ? undefined : () => aggiorna.mutate(),
    occupato: aggiorna.isPending,
    scegli: (m: string) => {
      setCarta(null)
      modello.mutate(m)
    },
    cambiando: modello.isPending,
  }

  return (
    <div className="as-pagina" ref={misura}>
      <PrimaDellaPrevisione meteo={meteo} senzaSito={<SenzaSito />} />
      {detto?.site && detto.missing === "no_timezone" && (
        <div className="as-meteo">
          <Testa {...comandi} aggiorna={undefined} detto={detto} />
          <Avviso esito="allarme" pagina titolo={t("weather.noTimezone")}
            azioni={<Bottone verso="primario" a="/impostazioni/sito">{t("weather.noTimezone.how")}</Bottone>} />
        </div>
      )}
      {detto?.site && detto.missing === null && (
        <div className={telefono ? "as-meteo as-tel-meteo" : "as-meteo"}>
          {telefono ? (
            <TestaDelTelefono key={aperta?.night} {...comandi} detto={detto} notte={aperta} prima={aperta === detto.nights[0]} apriCarta={setCarta} />
          ) : (
            <Testa {...comandi} detto={detto} />
          )}
          {aggiorna.error && <Avviso esito="allarme">{aggiorna.error.message}</Avviso>}
          {(aggiorna.data === "no_site" || aggiorna.data === "no_timezone") && (
            <Avviso esito="attesa" pagina>{t(`weather.status.${aggiorna.data}`)}</Avviso>
          )}
          {tace && (
            <RichiestaSenzaRisposta detto={detto} tace={tace} senzaPrevisione={senzaPrevisione} aggiorna={() => aggiorna.mutate()} occupato={aggiorna.isPending} />
          )}
          {modello.error && <Avviso esito="allarme">{modello.error.message}</Avviso>}
          <SeeingCheTace seeing={detto.seeing} aggiorna={() => aggiorna.mutate()} occupato={aggiorna.isPending} />
          {/* un servizio che tace senza previsione l'ha gia' detto, con l'allarme */}
          {!tace && detto.fetched_at === null && (
            <Avviso esito="attesa" pagina titolo={t("weather.never")}>
              {t("weather.never.how")}
            </Avviso>
          )}
          {!tace && detto.fetched_at !== null && detto.nights.length === 0 && <Avviso esito="attesa" pagina titolo={t("weather.noNights")} />}
          {detto.nights.length > 0 && (
            <Notti detto={detto} aperta={aperta} scegli={scegliNotte} telefono={telefono ? { aperta: carta, apri: setCarta } : undefined} />
          )}
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
  /** Senza: niente Aggiorna in testa (sito senza fuso, o servizio che tace con la previsione buona). */
  aggiorna: (() => void) | undefined
  occupato: boolean
  scegli: (m: string) => void
  cambiando: boolean
}) {
  return (
    <header className="as-meteo__testa">
      <div className="as-meteo__dice">
        <p className="as-soprattitolo">{t("weather.head.where", { sito: detto.site ?? "" })}</p>
        <Arrivo detto={detto} />
      </div>
      {aggiorna && (
        <Bottone onClick={aggiorna} disabled={occupato}>
          {occupato ? t("weather.refreshing") : t("weather.refresh")}
        </Bottone>
      )}
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

/** Da quando e' la previsione, e il seeing che ha un'eta' sua. Senza previsione la riga resta
 *  vuota: non c'e' ancora un'ora da dire del sito. */
function Arrivo({ detto }: { detto: Meteo }) {
  const seeing = detto.sources.find((f) => f.source === "meteoblue")
  return (
    <p className="as-meteo__arrivo">
      {detto.fetched_at !== null && [
        t("weather.head.arrived", { giorno: giorno(detto.fetched_at), ora: orario(detto.fetched_at), fa: fa(detto.fetched_at) }),
        seeing ? t("weather.head.seeing", { giorno: giorno(seeing.fetched_at), ora: orario(seeing.fetched_at), fa: fa(seeing.fetched_at) }) : null,
        t("weather.head.siteTime"),
      ]
        .filter(Boolean)
        .join(" \u00b7 ")}
    </p>
  )
}

// cio' che pesa senza una carta da aprire: la Luna. Le raffiche aprono quella del vento, dove
// stanno (tavola meteo-telefono v37).
const SENZA_CARTA: readonly Codice[] = ["moon"]
const cartaDi = (c: Codice): Codice => (c === "gust" ? "wind" : c)

/**
 * La testa sul telefono (`as-tel-testa`): il verdetto della notte scelta e il modello; sotto, da
 * quando e' la previsione e *Aggiorna*. Toccato, il verdetto di una notte piena apre gli altri
 * fattori in un riquadro sopra la pagina; una misura li chiude e apre la sua carta.
 */
function TestaDelTelefono({ detto, notte: n, prima, apriCarta, aggiorna, occupato, scegli, cambiando }: {
  detto: Meteo; notte: Notte | undefined; prima: boolean; apriCarta: (c: Codice) => void
  aggiorna: (() => void) | undefined; occupato: boolean; scegli: (m: string) => void; cambiando: boolean
}) {
  const [aperti, setAperti] = useState(false)
  const id = useId()
  const verdetto = useRef<HTMLDivElement>(null)
  const riquadro = useRef<HTMLDivElement>(null)
  const siApre = n !== undefined && !n.trend && n.window !== null
  const pesano = n?.measures.filter((m) => m.weighs) ?? []
  const chiudi = (fuoco: HTMLElement | null) => {
    setAperti(false)
    fuoco?.focus()
  }
  useRiquadro(aperti, [verdetto, riquadro], (esc) => chiudi(esc ? verdetto.current : null))
  // aperto, il fuoco entra: sulla prima misura, o sul riquadro se niente pesa
  useEffect(() => {
    if (aperti) (riquadro.current?.querySelector("button") ?? riquadro.current)?.focus()
  }, [aperti])
  const giro = (ev: KeyboardEvent<HTMLDivElement>) => {
    if (ev.key === "Tab") giraIlFuoco(ev)
  }
  const tocca = () => (aperti ? chiudi(verdetto.current) : setAperti(true))
  const tasto = (ev: KeyboardEvent<HTMLDivElement>) => {
    if (ev.key !== "Enter" && ev.key !== " ") return
    ev.preventDefault()
    tocca()
  }
  const tocco = siApre
    ? { role: "button", tabIndex: 0, "aria-expanded": aperti, "aria-controls": id, onClick: tocca, onKeyDown: tasto }
    : {}
  return (
    <>
      <div className="as-tel-testa">
        {n && (
          <div className="as-tel-verdetti" ref={verdetto} {...tocco}>
            <div className="as-tel-verdetto">
              {n.trend ? (
                <CapoDellaTendenza notte={n} />
              ) : (
                <CapoDellaNotte notte={n} prima={prima} segno={siApre && <span className="as-tel-pesa-segno">{t("weather.weighs.short")}</span>} />
              )}
            </div>
          </div>
        )}
        <MenuDelModello detto={detto} scegli={scegli} cambiando={cambiando} />
        {n && siApre && (
          <div className="as-tel-pesanti" id={id} ref={riquadro} tabIndex={-1} role="dialog" aria-label={t("weather.weighs.short")} hidden={!aperti} onKeyDown={giro}>
            <ul className="as-tel-pesano" aria-label={t("weather.weighs")}>
              <li>{t("weather.weighs")}</li>
              {pesano.length === 0 && <li>{t("weather.weighs.none")}</li>}
              {pesano.map((m) => {
                const dentro = (
                  <>
                    {m.level && <Semaforo livello={m.level}>{parola(m.code, m.level)}</Semaforo>}
                    <span>
                      <b>{t(`weather.measure.${m.code}` as Chiave)}</b> {quando(m)}
                    </span>
                  </>
                )
                return (
                  <li key={m.code}>
                    {SENZA_CARTA.includes(m.code) ? (
                      <span className="as-tel-pesa">{dentro}</span>
                    ) : (
                      <button className="as-tel-pesa" type="button" onClick={() => {
                        apriCarta(cartaDi(m.code))
                        // la carta piccola c'e' gia': il fuoco va li', non si perde nel riquadro chiuso
                        chiudi(document.querySelector(`[aria-controls="${idDellaCarta(n.night, cartaDi(m.code))}"]`))
                      }}>
                        {dentro}
                      </button>
                    )}
                  </li>
                )
              })}
            </ul>
          </div>
        )}
      </div>
      <div className="as-tel-arrivo">
        <Arrivo detto={detto} />
        {aggiorna && (
          <Bottone onClick={aggiorna} disabled={occupato}>
            {occupato ? t("weather.refreshing") : t("weather.refresh")}
          </Bottone>
        )}
      </div>
    </>
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
function Notti({ detto, aperta, scegli, telefono }: {
  detto: Meteo; aperta: Notte | undefined; scegli: (i: number) => void
  telefono: { aperta: Codice | null; apri: (c: Codice | null) => void } | undefined
}) {
  const voce = (n: Notte, i: number) => (
    <button key={n.night} type="button" role="tab" id={`voce-${n.night}`} aria-selected={n === aperta}
      aria-controls={`notte-${n.night}`} onClick={() => scegli(i)}
      className={n.trend ? "as-voce-notte as-voce-notte--tendenza" : "as-voce-notte"}>
      <VoceDellaNotte notte={n} telefono={telefono !== undefined} />
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
            telefono ? <NotaDellaTendenza /> : <TendenzaDellaNotte notte={aperta} />
          ) : (
            <SchedaDellaNotte key={aperta.night} notte={aperta} prima={aperta === detto.nights[0]} scale={detto.scales} seeing={detto.seeing}
              telefono={telefono} />
          )}
        </section>
      )}
    </>
  )
}

/** Il servizio che tace (tavola meteo-stati v37). Con la previsione che vale ancora, lo stato piu'
 *  frequente, la pagina resta intera e una riga d'attesa dice da quando non risponde, con Aggiorna
 *  tenue; senza una previsione valida e' un allarme, e Aggiorna e' l'azione. */
function RichiestaSenzaRisposta({ detto, tace, senzaPrevisione, aggiorna, occupato }: {
  detto: Meteo; tace: Tace; senzaPrevisione: boolean; aggiorna: () => void; occupato: boolean
}) {
  const { status } = tace
  if (senzaPrevisione || detto.fetched_at === null) {
    return (
      <Avviso esito="allarme" pagina titolo={t(`weather.silent.${status}.none`, { ora: orario(tace.at) })}
        azioni={<Bottone verso="primario" onClick={aggiorna} disabled={occupato}>{t("weather.refresh")}</Bottone>} />
    )
  }
  return (
    <Avviso esito="attesa" titolo={t(`weather.silent.${status}`, { ora: orario(tace.at), prima: orario(detto.fetched_at) })}
      azioni={<Bottone verso="tenue" onClick={aggiorna} disabled={occupato}>{t("weather.refresh")}</Bottone>} />
  )
}

/** Meteoblue che tace o risponde storto: resta il seeing di prima, con la sua eta' in testa. Il
 *  seeing che manca del tutto lo dice la sua carta. */
function SeeingCheTace({ seeing, aggiorna, occupato }: { seeing: Meteo["seeing"]; aggiorna: () => void; occupato: boolean }) {
  // senza un seeing di prima non c'e' niente che resti: lo dice la sua carta
  if (seeing.source === null) return null
  if (seeing.meteoblue !== "unreachable" && seeing.meteoblue !== "bad_answer") return null
  return (
    <Avviso esito="attesa" titolo={t(`weather.seeing.why.${seeing.meteoblue}`)}
      azioni={<Bottone verso="tenue" onClick={aggiorna} disabled={occupato}>{t("weather.refresh")}</Bottone>} />
  )
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
