import { useQuery } from "@tanstack/react-query"
import { useRef, useState } from "react"
import { Link } from "react-router"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { CartaDellaDashboard } from "./CartaDelParametro"
import { type Destra, ScalaDellaMisura } from "./CieloDelleNubi"
import { PrimaDellaPrevisione, usePrevisione } from "./Meteo"
import { OreSerene, oreDellaVoce, verdetto } from "./NotteDelMeteo"
import { Semaforo } from "./Semaforo"
import { Disco, useStanotte } from "./Stanotte"
import { AzioniDelVuoto, VuotoDellaSezione } from "./Vuoto"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, durata, fa, giorno, giornoEMese, giornoENumero, numero, oraDelSito, orario, t } from "./i18n"
import { useRevisione } from "./revisione"

type Meteo = components["schemas"]["WeatherOut"]
type Notte = Meteo["nights"][number]
type Luna = components["schemas"]["MoonOut"]
type NotteDellArchivio = components["schemas"]["Night"]

/** Le sei carte del meteo, sempre al loro posto (Marco, 12/10/2026, `handoff/design-dashboard.md`). */
const SEI: readonly Destra[] = ["cloud", "seeing", "jet", "wind", "condensation", "aerosol"]

const conMaiuscola = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

/**
 * La **Dashboard** sul disegno v37 (`pagine/dashboard.html` del progetto Design): stanotte in
 * testa con la Luna, le sei carte del meteo della notte che aprono sotto il loro grafico, le
 * prossime tre notti, cio' che resta da riprendere. I progetti ancora non esistono: lo dice.
 *
 * - **Qui non si calcola niente**: verdetto, ore serene, giudizi e conti arrivano scritti, dalle
 *   stesse query del Meteo, di Stanotte e della barra.
 * - Mancano ancora il dettaglio della Luna, la volta e l'anno (`docs/coda.md`).
 */
export function Dashboard() {
  const meteo = usePrevisione()
  const detto = meteo.data
  return (
    <div className="as-pagina">
      <PrimaDellaPrevisione meteo={meteo} />
      <div className="as-dashboard">
        {detto?.site && <Stanotte detto={detto} sito={detto.site} />}
        {detto?.site && <Prossime detto={detto} />}
        <div className="as-dashboard__coppia">
          <DaRiprendere />
        </div>
      </div>
    </div>
  )
}

/** La testa di stanotte, il vuoto dei progetti e il meteo della notte. */
function Stanotte({ detto, sito }: { detto: Meteo; sito: string }) {
  const luna = useStanotte().data?.moon ?? null
  const stanotte = detto.nights[0]
  return (
    <section className="as-dashboard__stanotte" aria-labelledby="dash-titolo">
      <div className="as-dashboard__testa">
        <div className="as-dashboard__dice">
          <p className="as-soprattitolo" id="dash-titolo">{t("dashboard.tonight", { sito })}</p>
          {stanotte && (
            <div className="as-dashboard__verdetto">
              {stanotte.window !== null && (
                <p className="as-dashboard__grande">
                  <OreSerene cielo={stanotte} />
                </p>
              )}
              <Semaforo livello={stanotte.verdict} grande>{verdetto(stanotte)}</Semaforo>
            </div>
          )}
        </div>
        {luna && <LunaInTesta luna={luna} />}
      </div>
      <VuotoDellaSezione testo="dashboard.projects.none">
        <AzioniDelVuoto>
          <Bottone verso="primario" a="/progetti">{t("dashboard.projects.create")}</Bottone>
        </AzioniDelVuoto>
      </VuotoDellaSezione>
      {stanotte && stanotte.window !== null && stanotte.measures.length > 0 && <MeteoDellaNotte detto={detto} notte={stanotte} />}
      <p className="as-dashboard__rimando">
        <Link to="/meteo">{t("nav.weather")}</Link>
      </p>
    </section>
  )
}

/** La Luna accanto al verdetto: fase, luce, quando sorge e quando tramonta. */
function LunaInTesta({ luna }: { luna: Luna }) {
  const sorge = luna.rise === null ? t("tonight.rise.never") : t("dashboard.moon.rise", { ora: oraDelSito(luna.rise) })
  const tramonta = luna.set === null ? t("tonight.set.never") : t("dashboard.moon.set", { ora: oraDelSito(luna.set) })
  return (
    <div className="as-dashboard__luna">
      <div className="as-luna">
        <Disco luna={luna} className="as-luna__faccia--testa" />
        <span>
          <b>{`${t(`moon.${luna.phase_key}`)}, ${t("tonight.illuminated", { pct: luna.illumination_pct })}`}</b>
          {`${sorge} \u00b7 ${tramonta}`}
        </span>
      </div>
    </div>
  )
}

/** L'eta' della previsione, come nella testa del Meteo. */
function Aggiornato({ detto }: { detto: Meteo }) {
  if (detto.fetched_at === null) return null
  return (
    <span className="as-dashboard__aggiornato">
      {t("weather.head.arrived", { giorno: giorno(detto.fetched_at), ora: orario(detto.fetched_at), fa: fa(detto.fetched_at) })}
    </span>
  )
}

/** Le sei carte in fila e, sotto, il grafico di quella aperta: una alla volta. */
function MeteoDellaNotte({ detto, notte: n }: { detto: Meteo; notte: Notte }) {
  const [aperta, setAperta] = useState<Destra | null>(null)
  const carte = useRef<Partial<Record<Destra, HTMLButtonElement | null>>>({})
  const ore = n.hours.filter((o) => o.shown)
  const misure = SEI.flatMap((codice) => n.measures.filter((m) => m.code === codice).map((m) => ({ codice, m })))
  const chiudi = (codice: Destra) => {
    setAperta(null)
    carte.current[codice]?.focus()
  }
  return (
    <>
      <div className="as-dashboard__sopra-meteo as-dashboard__meteo-capo">
        <p className="as-soprattitolo as-dashboard__meteo-titolo">{t("dashboard.weather.title")}</p>
        <Aggiornato detto={detto} />
      </div>
      <div className="as-dashboard__meteo">
        <div className="as-parametri as-parametri--fila">
          {misure.map(({ codice, m }) => (
            <CartaDellaDashboard key={codice} misura={m} notte={n} ore={ore} scala={detto.scales.find((s) => s.code === codice)}
              aperta={aperta === codice} governa={`dash-m-${codice}`} apri={() => setAperta(aperta === codice ? null : codice)}
              ref={(b) => { carte.current[codice] = b }} />
          ))}
        </div>
        {misure.map(({ codice }) => {
          const nome = t(`weather.measure.${codice}` as Chiave)
          return (
            <div key={codice} className="as-pannello" id={`dash-m-${codice}`} hidden={aperta !== codice}>
              <div className="as-pannello__capo">
                <p className="as-pannello__nome">{t("dashboard.weather.panel", { nome })}</p>
                <Bottone verso="nudo" piccolo onClick={() => chiudi(codice)}>{t("frame.close.word")}</Bottone>
              </div>
              {aperta === codice && <ScalaDellaMisura notte={n} ore={ore} scale={detto.scales} codice={codice} />}
            </div>
          )
        })}
      </div>
    </>
  )
}

/** Le tre notti dopo stanotte, come nella fila del Meteo: il giorno, le ore serene, il semaforo. */
function Prossime({ detto }: { detto: Meteo }) {
  const notti = detto.nights.slice(1, 4)
  if (notti.length === 0) return null
  return (
    <section className="as-dashboard__prossime" aria-labelledby="dash-giorni">
      <div className="as-dashboard__meteo-capo">
        <p className="as-soprattitolo as-dashboard__meteo-titolo" id="dash-giorni">{t("dashboard.nights.title")}</p>
        <Aggiornato detto={detto} />
      </div>
      <div className="as-dashboard__meteo">
        <div className="as-serate">
          {notti.map((n) => (
            <Link key={n.night} className="as-serata" to="/meteo" aria-label={t("dashboard.nights.label", { giorno: giornoENumero(n.night) })}>
              {/* il posto dell'icona del cielo: aspetta, con le parole del cielo, la scelta di Marco */}
              <span aria-hidden="true" />
              <p>
                {/* dalla quarta notte la previsione e' una tendenza, e lo dice (Marco, 26/9 e 14/10/2026) */}
                <b>{n.trend ? `${conMaiuscola(giornoENumero(n.night))} \u00b7 ${t("weather.night.trend")}` : conMaiuscola(giornoENumero(n.night))}</b>
                <span>{oreDellaVoce(n)}</span>
              </p>
              <Semaforo livello={n.verdict}>{verdetto(n)}</Semaforo>
            </Link>
          ))}
        </div>
      </div>
    </section>
  )
}

/** Cio' che resta da fare: le domande da confermare e l'ultima notte ripresa. Vuoto, non c'e'; c'e'
 *  anche senza sito, perche' l'archivio non dipende dal sito. */
function DaRiprendere() {
  const revisione = useRevisione()
  const daConfermare = revisione.data?.to_confirm ?? 0
  const ultima = useQuery({
    queryKey: ["nights", "ultima"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/nights", { params: { query: { limit: 1 } } })
      if (error) throw new Error(t("nights.failed"))
      return data.items[0] ?? null
    },
  }).data
  if (daConfermare === 0 && !ultima && !revisione.error) return null
  return (
    <section className="as-dashboard__lavoro" aria-labelledby="dash-lavoro">
      <p className="as-soprattitolo" id="dash-lavoro">{t("dashboard.work.title")}</p>
      {/* uno zero su un archivio che non ha risposto sarebbe una bugia tranquillizzante */}
      {revisione.error && <Avviso esito="allarme">{revisione.error.message}</Avviso>}
      {daConfermare > 0 && (
        <div className="as-riga">
          <span className="as-riga__segno as-riga__segno--attesa" aria-hidden="true" />
          <span>
            <b>{t("frame.count", { n: numero(daConfermare) })}</b>
          </span>
          <Bottone verso="primario" piccolo a="/da-confermare">{t("dashboard.work.answer")}</Bottone>
        </div>
      )}
      {ultima && (
        <Link className="as-riga" to={`/notti?notte=${ultima.id}`}>
          <span className="as-riga__segno" aria-hidden="true" />
          <span>
            <b>{conMaiuscola(giornoEMese(ultima.night_date))}</b>
            {comeEAndata(ultima)}
          </span>
          <span className="as-riga__freccia" aria-hidden="true">{"\u2192"}</span>
        </Link>
      )}
    </section>
  )
}

/** "4 h 12 min su M 31 e altri 2, 180 frame": il tempo e i frame della notte, l'oggetto con piu'
 *  tempo (il backend li manda in quell'ordine) e quanti altri. */
function comeEAndata(n: NotteDellArchivio): string {
  const valori = { durata: durata(n.integration_s) ?? "", frame: numero(n.frames) }
  const primo = n.objects[0]?.name
  if (!primo) return t("dashboard.work.night.bare", valori)
  const altri = n.objects.length - 1
  if (altri === 0) return t("dashboard.work.night", { ...valori, oggetto: primo })
  return t("dashboard.work.night.more", { ...valori, oggetto: primo, n: numero(altri) })
}
