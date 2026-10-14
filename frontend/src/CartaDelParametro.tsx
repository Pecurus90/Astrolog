import { type KeyboardEvent, type PointerEvent, type ReactNode, useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import type { SegnoDellaMisura } from "./Icons"
import type { components } from "./api/schema"
import { type Chiave, numero, oraDelSito, t } from "./i18n"
import { Semaforo } from "./Semaforo"

type Notte = components["schemas"]["WeatherNightOut"]
type Misura = components["schemas"]["WeatherMeasureOut"]
type Ora = components["schemas"]["WeatherHourOut"]
type Scala = components["schemas"]["WeatherScaleOut"]
type Seeing = components["schemas"]["WeatherSeeingOut"]
type Codice = Misura["code"]
type Campo = "cloud_total_pct" | "cloud_low_pct" | "precip_mm" | "wind_kmh" | "dew_spread_c"
  | "seeing_arcsec" | "wind_250hpa_kmh" | "aerosol_optical_depth" | "temperature_c" | "visibility_km"
  | "dust_ugm3" | "wind_700hpa_kmh"

// Come il disegno (v27) mostra ogni carta: il campo dell'ora, l'unita', la riga sotto il valore e
// se il grafico e' a barre (le misure con soglia) o a linea (le neutre). Presentazione: i numeri
// e i giudizi arrivano scritti dal backend.
type Forma = { campo: Campo; unita?: Chiave; sotto?: Chiave; barre: boolean; piccola?: boolean }
const FORME: Partial<Record<Codice, Forma>> = {
  cloud: { campo: "cloud_total_pct", unita: "weather.unit.pct", sotto: "weather.card.mean", barre: true },
  cloud_low: { campo: "cloud_low_pct", unita: "weather.unit.pct", sotto: "weather.card.mean", barre: true },
  rain: { campo: "precip_mm", unita: "weather.unit.mm", sotto: "weather.card.total", barre: true },
  wind: { campo: "wind_kmh", unita: "weather.unit.kmh", sotto: "weather.card.wind", barre: true },
  condensation: { campo: "dew_spread_c", unita: "weather.unit.celsius", sotto: "weather.card.condensation", barre: true },
  seeing: { campo: "seeing_arcsec", unita: "weather.unit.arcsec", sotto: "weather.card.seeing", barre: true },
  jet: { campo: "wind_250hpa_kmh", unita: "weather.unit.kmh", sotto: "weather.card.jet", barre: true },
  aerosol: { campo: "aerosol_optical_depth", sotto: "weather.card.aerosol", barre: true },
  visibility: { campo: "visibility_km", unita: "weather.unit.km", sotto: "weather.card.lowest", barre: true },
  temperature: { campo: "temperature_c", unita: "weather.unit.celsius", barre: false, piccola: true },
  dust: { campo: "dust_ugm3", unita: "weather.unit.dust", sotto: "weather.card.mean", barre: false, piccola: true },
  wind_700: { campo: "wind_700hpa_kmh", unita: "weather.unit.kmh", barre: false, piccola: true },
}

/** Quanto sale un valore sulla scala che il backend ha scritto, da 0 (il fondo) a 1 (la cima). La
 *  visibilita' ha la cima ferma e cresce con la radice: oltre la cima un valore resta in cima. */
export function quota(m: Pick<Misura, "axis_min" | "axis_max" | "axis_curve"> | undefined, v: number): number {
  const basso = m?.axis_min ?? 0
  const alto = m?.axis_max ?? 1
  const lineare = (v - basso) / (alto - basso || 1)
  return m?.axis_curve === "sqrt" ? Math.sqrt(Math.min(1, Math.max(0, lineare))) : lineare
}

/** Le carte grandi e piccole, ognuna sempre al suo posto: l'ordine d'importanza del backend vale
 *  per gli altri fattori, non per le carte. */
export const CARTE_GRANDI: readonly Codice[] = ["cloud", "cloud_low", "condensation", "rain", "visibility", "wind", "seeing", "jet", "aerosol"]
export const CARTE_PICCOLE: readonly Codice[] = ["temperature", "dust", "wind_700"]

/** Le misure di un gruppo di carte, nell'ordine del gruppo. */
export function alPosto(misure: readonly Misura[], posti: readonly Codice[]): Misura[] {
  return posti.flatMap((codice) => misure.filter((m) => m.code === codice))
}

const TINTE = {
  go: "as-parametro__tinta--buona",
  marginal: "as-parametro__tinta--incerta",
  nogo: "as-parametro__tinta--niente",
  neutro: "as-parametro__tinta--neutro",
} as const

/** La parola di un giudizio: Luna e aerosol hanno le loro, le altre quelle del verdetto. */
export function parola(code: Codice, livello: NonNullable<Misura["level"]>): string {
  if (code === "moon" || code === "aerosol") return t(`weather.word.${code}.${livello}` as Chiave)
  return t(`weather.word.${livello}`)
}

/** Un valore con la sua unita', o la parola che dice che il servizio non lo da'. */
function conUnita(v: number | null, unita?: Chiave) {
  if (v === null) return t("weather.card.unknown")
  return unita ? `${numero(v)} ${t(unita)}` : numero(v)
}

/**
 * Una carta del Meteo (`as-parametro`): il valore della notte, la riga che dice cos'e', il
 * giudizio con le sue ore, le barrette ora per ora dal crepuscolo all'alba e il picco. Tutti i
 * numeri arrivano scritti: qui si sceglie solo dove disegnarli.
 *
 * Una carta si porta a un'ora: il filo sul cielo le porta tutte (`oraDelCielo`), il tocco o le
 * frecce sulle sue barrette porta lei sola e ce la lascia ("x notte" la riporta alla notte).
 */
export function CartaDelParametro({
  misura: m,
  notte: n,
  ore,
  scala,
  seeing,
  oraDelCielo = null,
}: {
  misura: Misura
  notte: Notte
  ore: Ora[]
  scala?: Scala | undefined
  seeing: Seeing
  oraDelCielo?: number | null
}) {
  const forma = FORME[m.code]
  if (!forma) return null
  const nome = t(`weather.measure.${m.code}` as Chiave)
  if (m.code === "seeing" && m.known_hours === 0 && (!seeing.key || seeing.meteoblue === "refused")) {
    return <SeeingSenzaChiave nome={nome} rifiutata={seeing.key} />
  }
  // le piccole del desktop non hanno l'avviso nella tavola: restano carte, col "Non disponibile"
  if (m.known_hours === 0 && !forma.piccola) {
    return (
      <CartaDellAvviso nome={nome}>
        <Avviso esito="ignoto" titolo={t("weather.card.unknown")} />
      </CartaDellAvviso>
    )
  }
  return <Carta misura={m} notte={n} ore={ore} scala={scala} forma={forma} nome={nome} oraDelCielo={oraDelCielo} />
}

// il segno di ogni misura sulla carta piccola del telefono (tavole v37)
const SEGNI: Partial<Record<Codice, SegnoDellaMisura>> = {
  cloud: "nuvola", cloud_low: "nuvola", condensation: "m-goccia", rain: "m-pioggia", visibility: "m-velato", wind: "m-vento",
  seeing: "m-seeing", jet: "m-getto", aerosol: "m-occhio", temperature: "m-termometro", dust: "m-velato", wind_700: "m-vento",
}

/**
 * La carta piccola del telefono (`as-tel-carta`): il segno, il nome, il valore della notte, le
 * barrette e la parola sola. E' un bottone: apre la carta intera della sua misura (`governa`).
 */
export function CartaDelTelefono({ misura: m, notte: n, ore, scala, aperta, governa, apri }: {
  misura: Misura; notte: Notte; ore: Ora[]; scala?: Scala | undefined; aperta: boolean; governa: string; apri: () => void
}) {
  const forma = FORME[m.code]
  if (!forma) return null
  return (
    <button className="as-tel-carta" type="button" aria-expanded={aperta} aria-controls={governa} onClick={apri}>
      <span className="as-tel-carta__capo">
        <svg className="as-tel-carta__segno" viewBox="0 0 20 20" aria-hidden="true">
          <use href={`#i-${SEGNI[m.code] ?? "nuvola"}`} />
        </svg>
        <span className="as-tel-carta__nome">{t(`weather.measure.${m.code}` as Chiave)}</span>
      </span>
      {/* senza valore niente numero ne' barrette: il semaforo spento lo dice (Design, v37.1) */}
      {m.value === null ? (
        <Semaforo livello={null}>{t("weather.card.unknownWord")}</Semaforo>
      ) : (
        <>
          <span className="as-tel-carta__valore">
            <b>{numero(tondo(m.code, m.value))}</b>
            {forma.unita ? t(forma.unita) : ""}
          </span>
          <span className="as-tel-carta__barre" aria-hidden="true">
            <Grafico misura={m} notte={n} ore={ore} forma={forma} scala={scala} ora={null} dove="piccola" />
          </span>
          {m.level !== null && m.code !== "cloud" && m.known_hours > 0 && <Semaforo livello={m.level}>{parola(m.code, m.level)}</Semaforo>}
        </>
      )}
    </button>
  )
}

function Carta({ misura: m, notte: n, ore, scala, forma, nome, oraDelCielo }: {
  misura: Misura; notte: Notte; ore: Ora[]; scala: Scala | undefined; forma: Forma; nome: string; oraDelCielo: number | null
}) {
  const [fissa, setFissa] = useState<number | null>(null)
  const [sopra, setSopra] = useState<number | null>(null)
  const ora = fissa ?? sopra ?? oraDelCielo
  const qui = ora === null ? undefined : ore[ora]
  const unita = forma.unita ? t(forma.unita) : ""
  const sottoNotte = sotto(m, n, forma)
  const valoreNotte = m.value === null ? t("weather.card.unknown") : numero(tondo(m.code, m.value))
  const livello = qui && m.code in qui.levels ? qui.levels[m.code as keyof Ora["levels"]] : null
  const oraDa = (ev: PointerEvent<HTMLDivElement>) => {
    const q = ev.currentTarget.getBoundingClientRect()
    return Math.min(ore.length - 1, Math.max(0, Math.floor(((ev.clientX - q.left) / q.width) * ore.length)))
  }
  const tasto = (ev: KeyboardEvent<HTMLDivElement>) => {
    const nuova = oraDalTasto(ev.key, ora, ore.length - 1)
    if (nuova === undefined) return
    ev.preventDefault()
    setFissa(nuova)
  }
  const valoreQui = qui ? alValore(qui, forma) : null
  const sottoQui = qui ? sottoAllOra(qui, m) : ""
  return (
    <article className={forma.piccola ? "as-parametro as-parametro--piccolo" : "as-parametro"} data-a-ora={fissa === null ? undefined : ""}>
      <h3 className="as-parametro__nome">{nome}</h3>
      <p className="as-parametro__valore">
        <b>{qui ? (valoreQui === null ? t("weather.card.unknown") : numero(tondo(m.code, valoreQui))) : valoreNotte}</b>
        {(qui ? valoreQui : m.value) !== null && <span className={m.code === "seeing" ? "as-parametro__segno" : undefined}>{unita}</span>}
      </p>
      <p className="as-parametro__sotto">
        <span>{qui ? sottoQui : sottoNotte}</span>
        <button className="as-parametro__torna" type="button" hidden={fissa === null} aria-label={t("weather.card.backLabel")}
          onClick={() => setFissa(null)}>
          {t("weather.card.back")}
        </button>
      </p>
      {qui
        ? livello !== null && (
            <div className="as-parametro__sem">
              <Semaforo livello={livello}>{parola(m.code, livello)}</Semaforo>
            </div>
          )
        : m.level !== null && m.code !== "cloud" && m.known_hours > 0 && (
            <div className="as-parametro__sem">
              <Semaforo livello={m.level}>{giudizio(m)}</Semaforo>
            </div>
          )}
      <div className="as-parametro__grafico" data-meteo-carta-piano="" tabIndex={0} role="slider" aria-label={t("weather.card.hours", { nome })}
        aria-valuemin={0} aria-valuemax={ore.length - 1} aria-valuenow={ora ?? undefined}
        aria-valuetext={qui
          ? t("weather.card.valueAt", { ora: oraDelSito(qui.at), v: valoreQui === null ? t("weather.card.unknown") : `${numero(tondo(m.code, valoreQui))} ${unita}` })
          : t("weather.card.valueNight", { v: `${valoreNotte} ${unita}`, sotto: sottoNotte })}
        onPointerDown={(ev) => {
          const i = oraDa(ev)
          setFissa(fissa === i ? null : i)
        }}
        onPointerMove={(ev) => { if (ev.pointerType === "mouse") setSopra(oraDa(ev)) }}
        onPointerLeave={() => setSopra(null)}
        onKeyDown={tasto}>
        <Grafico misura={m} notte={n} ore={ore} forma={forma} scala={scala} ora={ora} />
        <Asse ore={ore} />
      </div>
      {!forma.piccola && <p className="as-parametro__picco">{picco(m, n, forma, scala)}</p>}
    </article>
  )
}

/** L'ora che un tasto sceglie su un grafico ora per ora: le frecce si spostano (dalla notte
 *  partono dal bordo), Inizio e Fine vanno ai capi, Esc torna alla notte (`null`); un altro tasto
 *  non sceglie niente (`undefined`). La usano le carte e il cielo. */
export function oraDalTasto(tasto: string, ora: number | null, ultima: number): number | null | undefined {
  if (tasto === "Escape") return null
  const avanti = ora === null ? 0 : Math.min(ultima, ora + 1)
  const indietro = ora === null ? ultima : Math.max(0, ora - 1)
  return ({ ArrowRight: avanti, ArrowUp: avanti, ArrowLeft: indietro, ArrowDown: indietro, Home: 0, End: ultima } as Record<string, number>)[tasto]
}

/** La visibilita' da 10 km in su si dice a chilometri interi, sotto con un decimale. */
export function tondo(code: Codice, v: number): number {
  return code === "visibility" && v >= 10 ? Math.round(v) : v
}

/** Il valore di un'ora sulla carta: il campo che la carta disegna. */
function alValore(o: Ora, forma: Forma): number | null {
  return o[forma.campo]
}

/** La riga sotto il valore a un'ora: l'ora, e cio' che la carta porta accanto. */
function sottoAllOra(o: Ora, m: Misura): string {
  const ora = oraDelSito(o.at)
  if (m.code === "temperature" && o.dew_point_c !== null) return t("weather.card.atDew", { ora, r: numero(o.dew_point_c) })
  if (m.code === "wind" && o.wind_gust_kmh !== null) return t("weather.card.atGust", { ora, r: numero(o.wind_gust_kmh) })
  return t("weather.card.at", { ora })
}

/** La carta di una misura senza ore: un avviso al posto di numero e grafico (tavola meteo-stati). */
function CartaDellAvviso({ nome, children }: { nome: string; children: ReactNode }) {
  return (
    <article className="as-parametro as-parametro--avviso">
      <h3 className="as-parametro__nome">{nome}</h3>
      {children}
    </article>
  )
}

function SeeingSenzaChiave({ nome, rifiutata }: { nome: string; rifiutata: boolean }) {
  return (
    <CartaDellAvviso nome={nome}>
      <Avviso
        esito={rifiutata ? "allarme" : "attesa"}
        titolo={t(rifiutata ? "weather.card.seeing.refused" : "weather.card.seeing.none")}
        azioni={<Bottone a="/impostazioni/servizi">{t("weather.card.seeing.how")}</Bottone>}
      />
    </CartaDellAvviso>
  )
}

/** La riga sotto il valore: cosa dice il numero, e su quali ore. */
function sotto(m: Misura, n: Notte, forma: Forma): string {
  if (m.code === "seeing" && m.known_until && m.known_hours < (n.window_hours ?? 0)) {
    return t("weather.card.seeing.part", { a: oraDelSito(m.known_until) })
  }
  if (m.code === "temperature") {
    const rugiada = n.measures.find((x) => x.code === "dew_point")?.value
    return t("weather.card.temperature", { r: rugiada == null ? t("weather.card.unknown") : numero(rugiada) })
  }
  if (m.code === "wind_700") {
    if (n.wind_700hpa_tenths === null) return t("weather.card.wind700.nobase")
    if (n.wind_700hpa_tenths === 0) return t("weather.card.wind700.zero")
    if (n.wind_700hpa_tenths === 10) return t("weather.card.wind700.ten")
    return t("weather.card.wind700", { n: numero(n.wind_700hpa_tenths) })
  }
  return forma.sotto ? t(forma.sotto) : ""
}

/** "incerta dalle 22, niente dalle 01", o "buona tutta la notte". */
function giudizio(m: Misura): string {
  if (m.level === null) return ""
  if (m.spans.length === 0) return t("weather.card.allNight", { parola: parola(m.code, m.level) })
  return m.spans.map((s) => t("weather.card.since", { parola: parola(m.code, s.level), da: oraDelSito(s.since) })).join(", ")
}

/** Il picco con le sue ore, o cio' che la carta dice al suo posto. */
function picco(m: Misura, n: Notte, forma: Forma, scala: Scala | undefined): string {
  // nessuna ora data: "mai sotto" o "nessuna pioggia" sarebbero un fatto inventato
  if (m.known_hours === 0) return ""
  if (m.code === "wind") {
    const raffica = n.measures.find((x) => x.code === "gust")
    if (!raffica || raffica.peak === null || !raffica.peak_at || !raffica.peak_until) return ""
    return t("weather.card.gusts", { v: numero(raffica.peak), da: oraDelSito(raffica.peak_at), a: oraDelSito(raffica.peak_until) })
  }
  if (m.code === "condensation") {
    const soglia = numero(scala?.steps[0]?.bound ?? 0)
    const sotto = m.spans.find((s) => s.level === "nogo")
    return sotto ? t("weather.card.dewSince", { s: soglia, da: oraDelSito(sotto.since) }) : t("weather.card.dewNever", { s: soglia })
  }
  if (m.code === "rain" && !m.peak) return t("weather.card.noRain")
  if (m.code === "visibility") {
    const nebbia = m.spans.find((s) => s.level === "nogo")
    return nebbia ? t("weather.card.fogSince", { da: oraDelSito(nebbia.since) }) : t("weather.card.noFog")
  }
  if (m.peak === null || !m.peak_at || !m.peak_until) return ""
  const detto = t("weather.card.peak", { v: conUnita(m.peak, forma.unita), da: oraDelSito(m.peak_at), a: oraDelSito(m.peak_until) })
  if (m.code === "seeing" && m.known_until && m.known_hours < (n.window_hours ?? 0)) {
    return `${detto} \u00b7 ${t("weather.card.missingSince", { da: oraDelSito(m.known_until) })}`
  }
  return detto
}

const LARGO = 240
const ALTO = 64

/** Le barrette o le linee della carta, ora per ora, sulla scala che il backend ha scritto. */
function Grafico({ misura: m, notte: n, ore, forma, scala, ora, dove = "carta" }: {
  misura: Misura; notte: Notte; ore: Ora[]; forma: Forma; scala?: Scala | undefined; ora: number | null; dove?: "carta" | "piccola"
}) {
  // la stessa misura si disegna due volte sul telefono (carta piccola e carta aperta): due id
  const id = `${dove}-${n.night}-${m.code}`
  const passo = LARGO / (ore.length || 1)
  const basso = m.axis_min ?? 0
  const alto = m.axis_max ?? 1
  const y = (v: number) => ALTO - 2 - quota(m, v) * (ALTO - 6)
  return (
    <svg className="as-parametro__tela" viewBox={`0 0 ${LARGO} ${ALTO}`} preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <pattern id={`${id}-t`} width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="5" className="as-parametro__tratto" />
        </pattern>
      </defs>
      {ore.map((o, i) =>
        o.sky === "dark" ? null : <rect key={o.at} className="as-parametro__giorno" x={i * passo} y={0} width={passo} height={ALTO} />,
      )}
      {forma.barre &&
        scala?.steps
          .filter((s) => s.bound > basso && s.bound < alto)
          .map((s) => <line key={s.bound} className="as-parametro__soglia" x1={0} x2={LARGO} y1={y(s.bound)} y2={y(s.bound)} />)}
      {forma.barre ? <Barre misura={m} ore={ore} campo={forma.campo} passo={passo} y={y} id={id} ora={ora} /> : <Linee misura={m} ore={ore} campo={forma.campo} passo={passo} y={y} />}
      {ora !== null && <line className="as-parametro__mira" x1={(ora + 0.5) * passo} x2={(ora + 0.5) * passo} y1={0} y2={ALTO} />}
    </svg>
  )
}

type Disegno = { misura: Misura; ore: Ora[]; campo: Campo; passo: number; y: (v: number) => number }

function Barre({ misura: m, ore, campo, passo, y, id, ora }: Disegno & { id: string; ora: number | null }) {
  const base = y(m.axis_min ?? 0)
  return (
    <>
      {ore.map((o, i) => {
        const v = o[campo]
        const x = i * passo + passo * 0.14
        if (v === null) return <rect key={o.at} x={x} y={2} width={passo * 0.72} height={ALTO - 4} fill={`url(#${id}-t)`} />
        const livello = m.code in o.levels ? o.levels[m.code as keyof Ora["levels"]] : null
        const cima = y(v)
        return (
          <rect key={o.at} data-spento={ora !== null && ora !== i ? "" : undefined}
            className={["as-parametro__barra", TINTE[livello ?? "neutro"], o.sky === "dark" ? "" : "as-parametro__barra--chiaro"].filter(Boolean).join(" ")} x={x} y={base - cima < 1.5 ? base - 1.5 : cima}
            width={passo * 0.72} height={base - cima < 1.5 ? 1.5 : base - cima} rx={1.5} />
        )
      })}
      {m.code === "wind" &&
        ore.map((o, i) =>
          o.wind_gust_kmh === null ? null : (
            <line key={`r-${o.at}`} className={`as-parametro__raffica ${TINTE[o.levels.gust ?? "neutro"]}`}
              x1={i * passo + passo * 0.14} x2={i * passo + passo * 0.86} y1={y(o.wind_gust_kmh)} y2={y(o.wind_gust_kmh)} />
          ),
        )}
    </>
  )
}

/** Una linea per serie, spezzata dove il servizio non da' il valore; temperatura e rugiada
 *  insieme, con le ore di condensa segnate dove si toccano. */
function Linee({ misura: m, ore, campo, passo, y }: Disegno) {
  const serie: Campo[] = m.code === "temperature" ? [campo, "dew_point_c" as Campo] : [campo]
  return (
    <>
      {m.code === "temperature" &&
        ore.map((o, i) =>
          o.levels.condensation === "nogo" ? <rect key={`c-${o.at}`} className="as-parametro__tocca" x={i * passo} y={0} width={passo + 0.3} height={ALTO} /> : null,
        )}
      {serie.flatMap((c, k) =>
        tratti(ore, c).map((tratto) => (
          <polyline key={`${c}-${tratto[0]}`} className={k ? "as-parametro__linea as-parametro__linea--due" : "as-parametro__linea"}
            points={tratto.map((i) => `${(i + 0.5) * passo},${y(ore[i]?.[c] as number)}`).join(" ")} />
        )),
      )}
    </>
  )
}

/** Le ore con un valore, a tratti: un'ora che manca chiude il tratto e il prossimo riparte. */
function tratti(ore: Ora[], c: Campo): number[][] {
  const fatti: number[][] = []
  let corrente: number[] = []
  ore.forEach((o, i) => {
    if (o[c] === null) {
      if (corrente.length) fatti.push(corrente)
      corrente = []
    } else corrente.push(i)
  })
  if (corrente.length) fatti.push(corrente)
  return fatti
}

/** Tre ore sotto il grafico: la prima, quella in mezzo, l'ultima. */
function Asse({ ore }: { ore: Ora[] }) {
  const scelte = [0, (ore.length - 1) >> 1, ore.length - 1].filter((i, k, a) => i >= 0 && a.indexOf(i) === k)
  return (
    <p className="as-parametro__asse" aria-hidden="true">
      {scelte.map((i) => (
        <span key={i} style={{ left: `${((i + 0.5) / ore.length) * 100}%` }}>
          {oraDelSito(ore[i]?.at ?? "")}
        </span>
      ))}
    </p>
  )
}
