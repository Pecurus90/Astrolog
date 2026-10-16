import { useQuery } from "@tanstack/react-query"
import { Fragment, type ReactNode, useContext, useRef, useState } from "react"
import { Link } from "react-router"

import { Avanza, Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import type { SegnoDellaMisura } from "./Icons"
import { CartaDelTelefono, CartaDellaDashboard } from "./CartaDelParametro"
import { type Destra, ScalaDellaMisura } from "./CieloDelleNubi"
import { useStato } from "./Scansiona"
import { PrimaDellaPrevisione, senzaPrevisioneIn, silenzio, useAggiorna, usePrevisione } from "./Meteo"
import { OreSerene, oreDellaVoce, verdetto } from "./NotteDelMeteo"
import { Semaforo } from "./Semaforo"
import { ApriStanotte, Disco, useStanotte } from "./Stanotte"
import { Volta } from "./Volta"
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
 * - Mancano ancora il dettaglio della Luna e l'anno (`docs/coda.md`).
 */
export function Dashboard() {
  const meteo = usePrevisione()
  const detto = meteo.data
  const [telefono, misura] = useColonnaStretta()
  // senza una cartella e senza un frame non c'e' archivio: la prima azione e' scegliere la cartella.
  // Le cartelle tolte lasciano i loro frame, e un archivio con le sue notti non e' vuoto.
  const cartelle = useQuanteCartelle().data
  const archivio = useArchivio().data
  const archivioVuoto = cartelle?.total === 0 && archivio?.totals.frames === 0
  const sito = detto?.site ?? null
  // la prima scansione al lavoro: i conti crescono ancora, e la pagina lo dice
  const scan = useStato().data?.scan
  const lettura = scan?.first && scan.state === "running" && scan.last_event ? { ...scan.last_event, manca: scan.remaining_s ?? null } : null
  // il meteo che non risponde senza una previsione che valga: la notte e le prossime non si dicono
  const giu = detto ? silenzio(detto) !== null && senzaPrevisioneIn(detto) : false
  return (
    <div className="as-pagina" ref={misura}>
      <PrimaDellaPrevisione meteo={meteo} senzaSito={false} />
      <div className={telefono ? "as-dashboard as-tel-dash" : "as-dashboard"}>
        {detto && sito === null && <PerCominciare archivioVuoto={archivioVuoto} />}
        {sito && archivioVuoto && <ArchivioVuoto />}
        {detto && sito && (
          <Stanotte detto={detto} sito={sito} telefono={telefono}
            giu={giu ? { quando: detto.fetched_at, ogni: detto.retry_s, primario: !archivioVuoto } : null}
            progetti={!archivioVuoto} />
        )}
        {detto && sito && !giu && <Prossime detto={detto} telefono={telefono} />}
        {lettura && <PrimaLettura lettura={lettura} />}
        {sito && archivioVuoto && <Seguito />}
        {sito && !archivioVuoto && !telefono && (
          <div className="as-dashboard__coppia">
            <Progetti />
            <DaRiprendere finora={lettura !== null} />
          </div>
        )}
      </div>
    </div>
  )
}

/** L'archivio in una riga: l'ultima notte e i totali (`limit=1`). */
function useArchivio() {
  return useQuery({
    queryKey: ["nights", "ultima"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/nights", { params: { query: { limit: 1 } } })
      if (error) throw new Error(t("nights.failed"))
      return data
    },
  })
}

/** Le cartelle d'archivio scelte: la stessa query delle Impostazioni. */
function useQuanteCartelle() {
  return useQuery({
    queryKey: ["folders"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/folders")
      if (error) throw new Error(t("settings.folders.failed"))
      return data
    },
  })
}

/** Senza sito non si calcola niente (tavola dashboard-stati v37): due passi in fila, il sito aperto
 *  e l'archivio dopo, spento finche' il primo non e' fatto. Con l'archivio gia' scelto, uno. */
function PerCominciare({ archivioVuoto }: { archivioVuoto: boolean }) {
  return (
    <section className="as-dashboard__inizio" aria-labelledby="dash-inizio">
      <p className="as-soprattitolo" id="dash-inizio">{t("dashboard.start.kicker")}</p>
      {archivioVuoto && <p className="as-dashboard__inizio-titolo">{t("dashboard.start.title")}</p>}
      <div className="as-dashboard__passi">
        <Avviso esito="ora" segno={numero(1)} pagina titolo={t("dashboard.start.site.title")}
          azioni={<Bottone verso="primario" a="/impostazioni/sito">{t("dashboard.start.site.how")}</Bottone>}>
          {t("dashboard.start.site.text")}
        </Avviso>
        {archivioVuoto && (
          <Avviso esito="dopo" segno={numero(2)} pagina titolo={t("dashboard.start.archive.title")}>
            {t("dashboard.start.archive.text")}
          </Avviso>
        )}
      </div>
      <p className="as-dashboard__dopo">{t("dashboard.start.after")}</p>
    </section>
  )
}

/** L'archivio senza cartelle: in testa alla pagina, con la sua azione, la prima. */
function ArchivioVuoto() {
  return (
    <Avviso esito="attesa" pagina titolo={t("dashboard.archive.empty.title")}
      azioni={<Bottone verso="primario" a="/impostazioni/cartelle">{t("dashboard.archive.empty.how")}</Bottone>}>
      {t("dashboard.archive.empty.text")}
    </Avviso>
  )
}

/** Al posto di progetti, lavoro e anno quando l'archivio non c'e' ancora: una frase sola. */
function Seguito() {
  return (
    <section className="as-dashboard__seguito" aria-labelledby="dash-seguito">
      <p className="as-soprattitolo" id="dash-seguito">{t("dashboard.later.title")}</p>
      <div className="as-vuoto as-vuoto--sezione">
        <p className="as-vuoto__testo">{t("dashboard.later.text")}</p>
      </div>
    </section>
  )
}

/** Il meteo che non risponde senza una previsione che valga: da quando, ogni quanto riprova. */
type Giu = { quando: string | null; ogni: number; primario: boolean }

/** La testa di stanotte e il meteo della notte; sul telefono anche la cosa da fare adesso. Col
 *  meteo giu' la testa dice il buio calcolato, e un allarme prende il posto delle carte. */
function Stanotte({ detto, sito, telefono, giu, progetti }: {
  detto: Meteo; sito: string; telefono: boolean; giu: Giu | null; progetti: boolean
}) {
  const notte = useStanotte().data
  const luna = notte?.moon ?? null
  const apriStanotte = useContext(ApriStanotte)
  const stanotte = giu ? undefined : detto.nights[0]
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
          {/* il buio e' calcolo, non previsione: c'e' anche col meteo giu' (tavola dashboard-stati-meteo) */}
          {giu && notte?.dark_s != null && (
            <div className="as-dashboard__verdetto">
              {/* d'estate a nord il buio astronomico non arriva: lo dice la parola, non "0 s" */}
              {notte.dark_s > 0 ? (
                <p className="as-dashboard__grande">
                  <b>{durata(notte.dark_s)}</b> {t("weather.clear.trend")}
                </p>
              ) : (
                <span className="as-meteo__parola">{t("weather.verdict.noNight")}</span>
              )}
              <Semaforo livello={null} grande>{t("weather.verdict.unknown")}</Semaforo>
            </div>
          )}
        </div>
        {luna && <LunaInTesta luna={luna} />}
      </div>
      {/* sul telefono la cosa da fare adesso e' il primario della pagina: senza progetti, crearne uno */}
      {telefono && progetti && <VuotoDeiProgetti />}
      {notte && (
        <Volta stanotte={notte} telefono={telefono}
          nubi={stanotte ? stanotte.hours.filter((o) => o.shown) : []}
          coperta={stanotte !== undefined && stanotte.window !== null && stanotte.usable_hours === 0} />
      )}
      {giu && <MeteoGiu giu={giu} />}
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

/** L'allarme del meteo giu': da quando non risponde, ogni quanto riprova da solo, e Riprova ora
 *  (tenue quando il primario della pagina e' un altro). */
function MeteoGiu({ giu }: { giu: Giu }) {
  const riprova = useAggiorna()
  const ogni = numero(Math.round(giu.ogni / 60))
  return (
    <Avviso esito="allarme" pagina titolo={t("dashboard.weather.down.title")}
      azioni={<Bottone verso={giu.primario ? "primario" : "tenue"} onClick={() => riprova.mutate()} disabled={riprova.isPending}>{t("dashboard.weather.down.how")}</Bottone>}>
      {giu.quando
        ? t("dashboard.weather.down.text", { giorno: giorno(giu.quando), ora: orario(giu.quando), fa: fa(giu.quando), minuti: ogni })
        : t("dashboard.weather.down.text.never", { minuti: ogni })}
    </Avviso>
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
        {/* senza le nuvole misurate nessun segno: un cielo disegnato sarebbe inventato */}
        {n.sky_word || pioveDalle(n) ? (
          <svg className="as-icona-meteo" viewBox="0 0 20 20" aria-hidden="true">
            <use href={`#i-${segnoDelCielo(n)}`} />
          </svg>
        ) : (
          <span aria-hidden="true" />
        )}
        <p>
          {/* dalla quarta notte la previsione e' una tendenza, e lo dice (Marco, 26/9 e 14/10/2026) */}
          <b>{n.trend ? `${conMaiuscola(giornoENumero(n.night))} \u00b7 ${t("weather.night.trend")}` : conMaiuscola(giornoENumero(n.night))}</b>
          <span>{oreDellaVoce(n)}</span>
          {n.sky_word && <span>{cieloInParole(n)}</span>}
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

/** Il segno del cielo di una notte (tavola v37): la pioggia vince sulle nuvole. */
function segnoDelCielo(n: Notte): SegnoDellaMisura {
  if (pioveDalle(n)) return "m-pioggia"
  if (n.sky_word === "clear") return "m-sereno"
  return n.sky_word === "scattered" ? "m-velato" : "nuvola"
}

/** L'ora in cui comincia la pioggia che non si puo', se c'e'. */
const pioveDalle = (n: Notte) => n.measures.find((m) => m.code === "rain" && m.level === "nogo")?.since ?? null

/** "Coperto, pioggia dalle 17", "Sereno \u00b7 3 h di buio senza Luna": le parole del cielo
 *  (okta WMO, scritte dal backend), la pioggia e le ore di buio con la Luna giu'. */
function cieloInParole(n: Notte): string {
  const pioggia = pioveDalle(n)
  const cielo = `${t(`weather.sky.word.${n.sky_word ?? "clear"}`)}${pioggia ? t("dashboard.nights.rain", { ora: oraDelSito(pioggia).slice(0, 2) }) : ""}`
  const senzaLuna = n.moonless_dark_hours ? t("dashboard.nights.moonless", { durata: durata(n.moonless_dark_hours * 3600) ?? "" }) : null
  return senzaLuna ? `${cielo} \u00b7 ${senzaLuna}` : cielo
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

/** La prima scansione al lavoro (tavola dashboard-stati-lettura v37): quanti file su quanti, quanto
 *  manca al ritmo finora (lo stima il backend; nel primo minuto tace), e che non serve fare niente. */
function PrimaLettura({ lettura: l }: { lettura: { current: number; total: number; manca: number | null } }) {
  const valori = { fatti: numero(l.current), su: numero(l.total) }
  return (
    <Avviso esito="lavoro" pagina titolo={t("dashboard.scan.title")}
      sotto={<Avanza pct={l.total ? Math.round((l.current / l.total) * 100) : 0} nome={t("dashboard.scan.bar")} />}>
      {l.manca === null ? t("dashboard.scan.text.noEta", valori) : t("dashboard.scan.text", { ...valori, quanto: durata(l.manca) ?? "" })}
    </Avviso>
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
function DaRiprendere({ finora }: { finora: boolean }) {
  const revisione = useRevisione()
  const daConfermare = revisione.data?.to_confirm ?? 0
  const archivio = useArchivio().data
  const ultima = archivio?.items[0] ?? null
  // i frame che non stanno in nessuna notte (tavola dashboard-stati-coperta): durante la prima
  // scansione non sono ancora contati
  const fuori = finora ? 0 : archivio?.waiting_frames ?? 0
  const fuoriDaiConti = fuori > 0 ? t("dashboard.work.outside", { n: numero(fuori) }) : null
  if (!finora && daConfermare === 0 && !fuori && !ultima && !revisione.error) return null
  return (
    <section className="as-dashboard__lavoro" aria-labelledby="dash-lavoro">
      <p className="as-soprattitolo" id="dash-lavoro">{t("dashboard.work.title")}</p>
      {/* uno zero su un archivio che non ha risposto sarebbe una bugia tranquillizzante */}
      {revisione.error && <Avviso esito="allarme">{revisione.error.message}</Avviso>}
      {/* durante la prima scansione i casi da confermare non sono ancora contati */}
      {finora && (
        <div className="as-riga">
          <span className="as-riga__segno as-riga__segno--attesa" aria-hidden="true" />
          <span>
            <b>{t("dashboard.work.toConfirm")}</b>
            {t("dashboard.work.toConfirm.later")}
          </span>
        </div>
      )}
      {!finora && daConfermare > 0 && (
        <div className="as-riga">
          <span className="as-riga__segno as-riga__segno--attesa" aria-hidden="true" />
          <span>
            <b>{t("frame.count", { n: numero(daConfermare) })}</b>
            {fuoriDaiConti}
          </span>
          {/* il primario della pagina e' Crea un progetto: Rispondi scende a tenue */}
          <Bottone verso="tenue" piccolo a="/da-confermare">{t("dashboard.work.answer")}</Bottone>
        </div>
      )}
      {/* niente da confermare: si risponde altrove (sito, data), e Notti dice dove */}
      {!finora && daConfermare === 0 && fuoriDaiConti && (
        <Link className="as-riga" to="/notti">
          <span className="as-riga__segno as-riga__segno--attesa" aria-hidden="true" />
          <span>
            <b>{fuoriDaiConti}</b>
          </span>
          <span className="as-riga__freccia" aria-hidden="true">{"\u2192"}</span>
        </Link>
      )}
      {ultima && (
        <Link className="as-riga" to={`/notti?notte=${ultima.id}`}>
          <span className="as-riga__segno" aria-hidden="true" />
          <span>
            <b>{conMaiuscola(giornoEMese(ultima.night_date))}</b>
            {finora ? t("dashboard.work.night.sofar") : comeEAndata(ultima)}
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
