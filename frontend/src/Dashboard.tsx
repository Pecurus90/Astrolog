import { useQuery } from "@tanstack/react-query"
import { Fragment, type ReactNode, useContext, useRef, useState } from "react"
import { Link } from "react-router"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { CartaDelTelefono, CartaDellaDashboard } from "./CartaDelParametro"
import { type Destra, ScalaDellaMisura } from "./CieloDelleNubi"
import { PrimaDellaPrevisione, usePrevisione } from "./Meteo"
import { OreSerene, oreDellaVoce, verdetto } from "./NotteDelMeteo"
import { Semaforo } from "./Semaforo"
import { ApriStanotte, Disco, useStanotte } from "./Stanotte"
import { AzioniDelVuoto, VuotoDellaSezione } from "./Vuoto"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { useColonnaStretta } from "./colonna"
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
 * La **Dashboard** sul disegno v37 (`pagine/dashboard.html` e `dashboard-telefono.html` del
 * progetto Design): stanotte in testa con la Luna, le sei carte del meteo della notte che aprono
 * sotto il loro grafico, le prossime tre notti, i progetti e cio' che resta da riprendere.
 *
 * - **Qui non si calcola niente**: verdetto, ore serene, giudizi e conti arrivano scritti, dalle
 *   stesse query del Meteo, di Stanotte e della barra.
 * - **Il telefono ha un markup suo** (`as-tel-dash`): stanotte e la cosa da fare adesso, le carte
 *   piccole, le prossime notti in una riga sempre aperta; niente rimandi ad altre pagine, ci va la
 *   barra in basso.
 * - I progetti ancora non esistono: lo dice la loro sezione, e il suo e' il primario della pagina.
 * - Mancano ancora il dettaglio della Luna, la volta e l'anno (`docs/coda.md`).
 */
export function Dashboard() {
  const meteo = usePrevisione()
  const detto = meteo.data
  const [telefono, misura] = useColonnaStretta()
  return (
    <div className="as-pagina" ref={misura}>
      <PrimaDellaPrevisione meteo={meteo} />
      <div className={telefono ? "as-dashboard as-tel-dash" : "as-dashboard"}>
        {detto?.site && <Stanotte detto={detto} sito={detto.site} telefono={telefono} />}
        {detto?.site && <Prossime detto={detto} telefono={telefono} />}
        {!telefono && (
          <div className="as-dashboard__coppia">
            <Progetti />
            <DaRiprendere />
          </div>
        )}
      </div>
    </div>
  )
}

/** La testa di stanotte e il meteo della notte; sul telefono anche la cosa da fare adesso. */
function Stanotte({ detto, sito, telefono }: { detto: Meteo; sito: string; telefono: boolean }) {
  const luna = useStanotte().data?.moon ?? null
  const apriStanotte = useContext(ApriStanotte)
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
      {/* sul telefono la cosa da fare adesso e' il primario della pagina: senza progetti, crearne uno */}
      {telefono && <VuotoDeiProgetti />}
      {stanotte && stanotte.window !== null && stanotte.measures.length > 0 && <MeteoDellaNotte detto={detto} notte={stanotte} telefono={telefono} />}
      {!telefono && (
        <p className="as-dashboard__rimando">
          {apriStanotte && (
            <a href="#" role="button" onClick={(ev) => { ev.preventDefault(); apriStanotte() }}>{t("dashboard.tonight.full")}</a>
          )}
          <Link to="/meteo">{t("nav.weather")}</Link>
        </p>
      )}
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

/** Le sei carte e, sotto, il grafico di quella aperta: una alla volta. Sul desktop i grafici
 *  stanno sotto la fila; sul telefono ognuno sotto la sua carta piccola. */
function MeteoDellaNotte({ detto, notte: n, telefono }: { detto: Meteo; notte: Notte; telefono: boolean }) {
  const [aperta, setAperta] = useState<Destra | null>(null)
  const carte = useRef<Partial<Record<Destra, HTMLButtonElement | null>>>({})
  const ore = n.hours.filter((o) => o.shown)
  const misure = SEI.flatMap((codice) => n.measures.filter((m) => m.code === codice).map((m) => ({ codice, m })))
  const apri = (codice: Destra) => setAperta(aperta === codice ? null : codice)
  const chiudi = (codice: Destra) => {
    setAperta(null)
    // sul telefono la carta piccola si trova da cio' che governa: non porta un ref
    const carta = telefono ? document.querySelector<HTMLElement>(`[aria-controls="dash-t-${codice}"]`) : carte.current[codice]
    carta?.focus()
  }
  const pannello = (codice: Destra, fuori?: { id: string; hidden: boolean }) => (
    <div className="as-pannello" {...fuori}>
      <div className="as-pannello__capo">
        <p className="as-pannello__nome">{t("dashboard.weather.panel", { nome: t(`weather.measure.${codice}` as Chiave) })}</p>
        <Bottone verso="nudo" piccolo onClick={() => chiudi(codice)}>{t("frame.close.word")}</Bottone>
      </div>
      {aperta === codice && <ScalaDellaMisura notte={n} ore={ore} scale={detto.scales} codice={codice} telefono={telefono} />}
    </div>
  )
  return (
    <>
      <div className="as-dashboard__sopra-meteo as-dashboard__meteo-capo">
        <p className="as-soprattitolo as-dashboard__meteo-titolo">{t("dashboard.weather.title")}</p>
        <Aggiornato detto={detto} />
      </div>
      <div className="as-dashboard__meteo">
        {telefono ? (
          <div className="as-tel-carte">
            {misure.map(({ codice, m }) => (
              <Fragment key={codice}>
                <CartaDelTelefono misura={m} notte={n} ore={ore} scala={detto.scales.find((s) => s.code === codice)}
                  aperta={aperta === codice} governa={`dash-t-${codice}`} apri={() => apri(codice)} />
                <div className="as-tel-dettaglio" id={`dash-t-${codice}`} hidden={aperta !== codice}>{pannello(codice)}</div>
              </Fragment>
            ))}
          </div>
        ) : (
          <>
            <div className="as-parametri as-parametri--fila">
              {misure.map(({ codice, m }) => (
                <CartaDellaDashboard key={codice} misura={m} notte={n} ore={ore} scala={detto.scales.find((s) => s.code === codice)}
                  aperta={aperta === codice} governa={`dash-m-${codice}`} apri={() => apri(codice)}
                  ref={(b) => { carte.current[codice] = b }} />
              ))}
            </div>
            {misure.map(({ codice }) => (
              <Fragment key={codice}>{pannello(codice, { id: `dash-m-${codice}`, hidden: aperta !== codice })}</Fragment>
            ))}
          </>
        )}
      </div>
    </>
  )
}

/** Le tre notti dopo stanotte, come nella fila del Meteo: il giorno, le ore serene, il semaforo.
 *  Sul desktop portano al Meteo; sul telefono stanno in una riga sempre aperta, senza rimandi. */
function Prossime({ detto, telefono }: { detto: Meteo; telefono: boolean }) {
  const notti = detto.nights.slice(1, 4)
  if (notti.length === 0) return null
  const serata = (n: Notte) => {
    const dentro = (
      <>
        {/* il posto dell'icona del cielo: aspetta, con le parole del cielo, la scelta di Marco */}
        <span aria-hidden="true" />
        <p>
          {/* dalla quarta notte la previsione e' una tendenza, e lo dice (Marco, 26/9 e 14/10/2026) */}
          <b>{n.trend ? `${conMaiuscola(giornoENumero(n.night))} \u00b7 ${t("weather.night.trend")}` : conMaiuscola(giornoENumero(n.night))}</b>
          <span>{oreDellaVoce(n)}</span>
        </p>
        <Semaforo livello={n.verdict}>{verdetto(n)}</Semaforo>
      </>
    )
    return telefono ? (
      <article key={n.night} className="as-serata">{dentro}</article>
    ) : (
      <Link key={n.night} className="as-serata" to="/meteo" aria-label={t("dashboard.nights.label", { giorno: giornoENumero(n.night) })}>{dentro}</Link>
    )
  }
  const corpo = (
    <>
      <div className="as-dashboard__meteo-capo">
        <p className="as-soprattitolo as-dashboard__meteo-titolo" id="dash-giorni">{t("dashboard.nights.title")}</p>
        <Aggiornato detto={detto} />
      </div>
      <div className="as-dashboard__meteo">
        <div className="as-serate">{notti.map(serata)}</div>
      </div>
    </>
  )
  if (!telefono) return <section className="as-dashboard__prossime" aria-labelledby="dash-giorni">{corpo}</section>
  return (
    <ul className="as-tel-righe as-carta">
      <RigaAperta nome={t("dashboard.nights.short")}>{corpo}</RigaAperta>
    </ul>
  )
}

/** Una riga del telefono sempre aperta (`as-tel-sez--aperta`): il nome in testa, il corpo sotto. */
function RigaAperta({ nome, children }: { nome: string; children: ReactNode }) {
  return (
    <li className="as-tel-sez as-tel-sez--aperta">
      <h3 className="as-tel-sez__h">
        <span className="as-tel-apri as-tel-apri--fermo">
          <span className="as-tel-apri__nome">{nome}</span>
          <span className="as-tel-apri__dato" />
          <span className="as-tel-apri__sub" />
        </span>
      </h3>
      <div className="as-tel-corpo as-tel-corpo--fisso">{children}</div>
    </li>
  )
}

/** Il vuoto dei progetti: una frase e Crea un progetto, il primario della pagina. */
function VuotoDeiProgetti() {
  return (
    <VuotoDellaSezione testo="dashboard.projects.none">
      <AzioniDelVuoto>
        <Bottone verso="primario" a="/progetti">{t("dashboard.projects.create")}</Bottone>
      </AzioniDelVuoto>
    </VuotoDellaSezione>
  )
}

/** I progetti in corso: finche' non esistono, la sezione lo dice (tavola dashboard-stati-progetti). */
function Progetti() {
  return (
    <section className="as-dashboard__progetti" aria-labelledby="dash-progetti">
      {/* un div e non l'header della tavola: per chi ascolta sarebbe un secondo "banner" accanto alla barra */}
      <div className="as-dashboard__capo">
        <p className="as-soprattitolo" id="dash-progetti">{t("dashboard.projects.title")}</p>
      </div>
      <VuotoDeiProgetti />
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
          {/* il primario della pagina e' Crea un progetto: Rispondi scende a tenue */}
          <Bottone verso="tenue" piccolo a="/da-confermare">{t("dashboard.work.answer")}</Bottone>
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
