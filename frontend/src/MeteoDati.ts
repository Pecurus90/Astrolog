import type { components } from "./api/schema"
import type { CellaMeteo } from "./componenti/CardMeteo"
import type { Esito } from "./componenti/Pillola"
import type { NotteStriscia } from "./componenti/Striscia"
import { bandeDellaPosa, ESITO, esitoDellaNotte, orePosa } from "./DashboardDati"
import {
  type Chiave,
  fa,
  giornoBreve,
  giornoENumero,
  maiuscola,
  numero,
  oraDelSito,
  orario,
  t,
  unDecimale,
  valoreEUnita,
} from "./i18n"

/**
 * The Weather page's words (board v82), from what `/weather` wrote: here a sentence is chosen and
 * a number written, never a number made. The Dashboard shares the cards' lines.
 */

export type Meteo = components["schemas"]["WeatherOut"]
export type Notte = Meteo["nights"][number]
export type Misura = Notte["measures"][number]
export type Ora = Notte["hours"][number]
export type Scala = Meteo["scales"][number]
export type Codice = Misura["code"]
type Livello = NonNullable<Misura["level"]>
type Finestra = NonNullable<Notte["window"]>
export type Campo =
  | "cloud_total_pct"
  | "cloud_low_pct"
  | "precip_mm"
  | "wind_kmh"
  | "dew_spread_c"
  | "seeing_arcsec"
  | "wind_250hpa_kmh"
  | "aerosol_optical_depth"
  | "temperature_c"
  | "visibility_km"
  | "dust_ugm3"
  | "wind_700hpa_kmh"

// How each card shows a measure: the hour's field, the unit and the line under the value.
export type Forma = { campo: Campo; unita?: Chiave; sotto?: Chiave }
export const FORME: Partial<Record<Codice, Forma>> = {
  cloud: { campo: "cloud_total_pct", unita: "weather.unit.pct", sotto: "weather.card.mean" },
  cloud_low: { campo: "cloud_low_pct", unita: "weather.unit.pct", sotto: "weather.card.mean" },
  rain: { campo: "precip_mm", unita: "weather.unit.mm", sotto: "weather.card.total" },
  wind: { campo: "wind_kmh", unita: "weather.unit.kmh", sotto: "weather.card.wind" },
  condensation: {
    campo: "dew_spread_c",
    unita: "weather.unit.celsius",
    sotto: "weather.card.condensation",
  },
  seeing: { campo: "seeing_arcsec", unita: "weather.unit.arcsec", sotto: "weather.card.seeing" },
  jet: { campo: "wind_250hpa_kmh", unita: "weather.unit.kmh", sotto: "weather.card.jet" },
  aerosol: { campo: "aerosol_optical_depth", sotto: "weather.card.aerosol" },
  visibility: { campo: "visibility_km", unita: "weather.unit.km", sotto: "weather.card.lowest" },
  temperature: { campo: "temperature_c", unita: "weather.unit.celsius" },
  dust: { campo: "dust_ugm3", unita: "weather.unit.dust", sotto: "weather.card.mean" },
  wind_700: { campo: "wind_700hpa_kmh", unita: "weather.unit.kmh" },
}

/** The cards, always in their place (contract, Marco 13/10/2026; board v82 `ORDER`). */
export const CARTE: readonly Codice[] = [
  "cloud",
  "cloud_low",
  "condensation",
  "rain",
  "visibility",
  "wind",
  "seeing",
  "jet",
  "aerosol",
]
export const ALTRE: readonly Codice[] = ["temperature", "dust", "wind_700"]

/** How high a value sits on the scale the backend wrote, 0 (floor) to 1 (top). */
export function quota(
  m: Pick<Misura, "axis_min" | "axis_max" | "axis_curve"> | undefined,
  v: number,
): number {
  const basso = m?.axis_min ?? 0
  const alto = m?.axis_max ?? 1
  const lineare = (v - basso) / (alto - basso || 1)
  return m?.axis_curve === "sqrt" ? Math.sqrt(Math.min(1, Math.max(0, lineare))) : lineare
}

/** A judgement's word: Moon and aerosol have their own, the others the verdict's. */
export function parola(code: Codice, livello: Livello): string {
  if (code === "moon" || code === "aerosol") return t(`weather.word.${code}.${livello}` as Chiave)
  return t(`weather.word.${livello}`)
}

/** Visibility from 10 km on is said in whole kilometres. */
export function tondo(code: Codice, v: number): number {
  return code === "visibility" && v >= 10 ? Math.round(v) : v
}

/** A value with its unit, or the word that says the service did not give it. */
/** A card's number as written: the condensation's spread and threshold always to the tenth. */
export function cifre(code: Codice, v: number): string {
  return code === "condensation" ? unDecimale(v) : numero(tondo(code, v))
}

export function conUnita(code: Codice, v: number | null): string {
  if (v === null) return t("weather.card.unknown")
  const u = FORME[code]?.unita
  return u ? valoreEUnita(cifre(code, v), t(u)) : cifre(code, v)
}

/** The line under the value: what the number says, and over which hours. */
export function sotto(m: Misura, n: Notte): string {
  if (m.code === "seeing" && m.known_until && m.known_hours < (n.window_hours ?? 0)) {
    return t("weather.card.seeing.part", { a: oraDelSito(m.known_until) })
  }
  if (m.code === "temperature") {
    const rugiada = n.measures.find((x) => x.code === "dew_point")?.value
    return rugiada == null
      ? t("weather.card.temperatureNoDew")
      : t("weather.card.temperature", { r: numero(rugiada) })
  }
  if (m.code === "wind_700") {
    if (n.wind_700hpa_tenths === null) return t("weather.card.wind700.nobase")
    if (n.wind_700hpa_tenths === 0) return t("weather.card.wind700.zero")
    if (n.wind_700hpa_tenths === 10) return t("weather.card.wind700.ten")
    return t("weather.card.wind700", { n: numero(n.wind_700hpa_tenths) })
  }
  const forma = FORME[m.code]
  const riga = forma?.sotto ? t(forma.sotto) : ""
  if (m.code === "condensation" && n.elevation_known === false) {
    return [riga, t("weather.card.dewNoElevation")].join(" \u00b7 ")
  }
  return riga
}

/** The peak with its hours, or what the card says in its place. */
export function picco(m: Misura, n: Notte): string {
  // no hour given: "never below" or "no rain" would be an invented fact
  if (m.known_hours === 0) return ""
  if (m.code === "wind") {
    const raffica = n.measures.find((x) => x.code === "gust")
    if (!raffica || raffica.peak === null || !raffica.peak_at || !raffica.peak_until) return ""
    return t("weather.card.gusts", {
      v: numero(raffica.peak),
      da: oraDelSito(raffica.peak_at),
      a: oraDelSito(raffica.peak_until),
    })
  }
  if (m.code === "condensation") {
    // each hour has its own threshold (Beysens): the one of the first dew hour, or the highest
    const prima = m.spans[0]
    const soglia = prima
      ? n.hours.find((o) => o.at === prima.since)?.dew_threshold_c
      : n.dew_threshold_top_c
    if (soglia == null) return ""
    return prima
      ? t("weather.card.dewSince", {
          s: cifre("condensation", soglia),
          da: oraDelSito(prima.since),
        })
      : t("weather.card.dewNever", { s: cifre("condensation", soglia) })
  }
  if (m.code === "rain" && !m.peak) return t("weather.card.noRain")
  if (m.code === "visibility") {
    const nebbia = m.spans.find((s) => s.level === "nogo")
    return nebbia
      ? t("weather.card.fogSince", { da: oraDelSito(nebbia.since) })
      : t("weather.card.noFog")
  }
  if (m.peak === null || !m.peak_at || !m.peak_until) return ""
  const detto = t("weather.card.peak", {
    v: conUnita(m.code, m.peak),
    da: oraDelSito(m.peak_at),
    a: oraDelSito(m.peak_until),
  })
  if (m.code === "seeing" && m.known_until && m.known_hours < (n.window_hours ?? 0)) {
    return `${detto} \u00b7 ${t("weather.card.missingSince", { da: oraDelSito(m.known_until) })}`
  }
  return detto
}

/** The hours the page draws. */
export const disegnate = (n: Notte): Ora[] => n.hours.filter((o) => o.shown)

const NEL_BUIO: Record<Finestra, readonly Ora["sky"][]> = {
  dark: ["dark"],
  nautical: ["dark", "astronomical"],
  sun_down: ["dark", "astronomical", "nautical", "civil"],
}

/** Whether an hour is one the verdict judged: the dark, or the night's window without it. */
export function nelBuio(o: Ora, n: Notte): boolean {
  return n.window !== null && NEL_BUIO[n.window].includes(o.sky)
}

/** "dalle 21:00 alle 23:00, 2 ore", runs joined; "tutta la notte" when they cover the window. */
export function intervalli(
  tratti: { since: string; until: string; hours: number }[],
  n: Notte,
): string {
  const ore = tratti.reduce((k, s) => k + s.hours, 0)
  if (!tratti.length) return ""
  if (n.window_hours !== null && ore >= n.window_hours) return t("meteo.when.all")
  const pezzi = tratti.map((s) =>
    t("meteo.when.span", { da: oraDelSito(s.since), a: oraDelSito(s.until) }),
  )
  return t(ore === 1 ? "meteo.when.one" : "meteo.when", {
    tratti: pezzi.join(t("meteo.when.and")),
    n: numero(ore),
  })
}

/** The hours that carry the measure's word for the night. */
export function quandoDellaMisura(m: Misura, n: Notte): string {
  if (m.level === null) return ""
  const suoi = m.spans.filter((s) => s.level === m.level)
  if (suoi.length) return intervalli(suoi, n)
  if (m.since && m.until) return intervalli([{ since: m.since, until: m.until, hours: m.hours }], n)
  return t("meteo.when.all")
}

/** The pill of a measure: its word, or the bounds a value with no word sits between. */
export function giudizioDi(
  m: Misura,
  scala: Scala | undefined,
): {
  esito: 0 | 1 | 2 | "mancante" | "neutra"
  parola: string
} {
  if (m.level) return { esito: ESITO[m.level], parola: parola(m.code, m.level) }
  const limiti = (scala?.steps ?? []).map((p) => p.bound).sort((a, b) => a - b)
  const [da, a] = [limiti[0], limiti[limiti.length - 1]]
  if (m.value === null || da === undefined || a === undefined || da === a) {
    return { esito: "mancante", parola: t("weather.card.unknownWord") }
  }
  return {
    esito: "neutra",
    parola: t("dashboard.weather.between", { da: numero(da), a: numero(a) }),
  }
}

/** "Notte di mercoled\u00ec 30 \u00b7 stanotte", "\u00b7 tendenza" from the fourth. */
export function nomeDellaNotte(n: Notte, prima: boolean): string {
  const nome = t("weather.night.name", { giorno: giornoENumero(n.night) })
  if (prima) return `${nome} \u00b7 ${t("weather.night.tonight")}`
  return n.trend ? `${nome} \u00b7 ${t("weather.night.trend")}` : nome
}

/** The day the "Come va" card names: "stanotte", or "domenica 4". */
export const giornoDellaNotte = (n: Notte, prima: boolean): string =>
  prima ? t("weather.night.tonight") : giornoENumero(n.night)

const accordo = (n: Notte): string => {
  const a = n.agreement
  const d = n.verdict ? a[n.verdict] : a.unknown
  return t(d === 1 ? "dashboard.agreement.one" : "dashboard.agreement", {
    n: numero(d),
    su: numero(a.total),
  })
}

export type Protagonista = {
  top: string
  valore: string
  pillola: { esito: Esito; testo: string } | null
  ripresa: { tipo: "larga" | "stretta" | "mista"; testo: string } | null
  sotto: string
  grande: boolean
  grafico: boolean
}

/** The big number of the night (board `hv`): Ore di posa, or the dark of a trend night. */
export function protagonista(n: Notte, prima: boolean): Protagonista {
  const nome = nomeDellaNotte(n, prima)
  const conTop = (label: string) =>
    `${maiuscola(label)} \u00b7 ${nome.charAt(0).toLowerCase()}${nome.slice(1)}`
  const pillola = n.verdict ? { esito: ESITO[n.verdict], testo: esitoDellaNotte(n).testo } : null
  if (n.window === null) {
    return {
      top: nome,
      valore: t("weather.verdict.noNight"),
      pillola: null,
      ripresa: null,
      sotto: t("weather.window.none"),
      grande: false,
      grafico: false,
    }
  }
  if (n.trend) {
    // sky_word and cloud_total_pct are null together (verdict.sky_word)
    const nubi =
      n.sky_word && n.cloud_total_pct != null
        ? t("meteo.trend.sky", {
            cielo: t(`weather.sky.word.${n.sky_word}`),
            pct: numero(Math.round(n.cloud_total_pct)),
          })
        : t("meteo.trend.skyNone")
    return {
      top: conTop(t("meteo.night.label.trend")),
      valore: t("meteo.hours", { n: numero(Math.round(n.dark_hours)) }),
      pillola,
      ripresa: ripresaLuna(n),
      sotto: `${nubi} \u00b7 ${accordo(n)}. ${t("weather.trend.note")}`,
      grande: true,
      grafico: true,
    }
  }
  if (!n.verdict) {
    return {
      top: nome,
      valore: t("weather.verdict.unknown"),
      pillola: null,
      ripresa: null,
      sotto: t("weather.verdict.none"),
      grande: false,
      grafico: true,
    }
  }
  const posa = n.exposure_hours ?? 0
  const bande =
    bandeDellaPosa(n) || (posa >= 0.05 ? t("meteo.exposure.allBroad") : t("meteo.exposure.none"))
  const parti = [
    bande,
    accordo(n),
    ...(n.without_aerosol ? [t("dashboard.transparency.noAerosol")] : []),
  ]
  return {
    top: conTop(t(`meteo.night.label.${n.window}`)),
    valore: orePosa(posa),
    pillola,
    ripresa: ripresaLuna(n),
    sotto: parti.join(" \u00b7 "),
    grande: true,
    grafico: true,
  }
}

/** The night's Moon for broadband (board `lunaNotte`): "Luna al 62% dalle 23:40 \u00b7 banda larga
 *  fino alle 23:40", and its short form for the strip. From the Moon measure the backend wrote. */
export function lunaDellaNotte(
  n: Notte,
): { tipo: "larga" | "stretta" | "mista"; testo: string; breve: string } | null {
  const m = n.measures.find((x) => x.code === "moon")
  if (!m || !m.level || m.known_hours === 0 || !m.known_since || !m.known_until) return null
  const pct = numero(Math.round(m.value ?? 0))
  const da = oraDelSito(m.known_since)
  const a = oraDelSito(m.known_until)
  const tutta = m.known_from_start && m.known_to_end
  const quando = tutta
    ? t("meteo.when.all")
    : m.known_from_start
      ? t("meteo.moon.until", { a })
      : m.known_to_end
        ? t("meteo.moon.from", { da })
        : t("meteo.moon.between", { da, a })
  const libera = t(m.level === "nogo" ? "meteo.moon.free.broad" : "meteo.moon.free.dark")
  // the strip's tile has room for the hour alone, as the board's `breve` ("fino alle 23")
  const resto = (ore: { da: string; a: string }) =>
    tutta
      ? ""
      : m.known_from_start
        ? t("meteo.moon.rest.after", { libera, a: ore.a })
        : m.known_to_end
          ? t("meteo.moon.rest.before", { libera, da: ore.da })
          : t("meteo.moon.rest.around", { libera, ...ore })
  const luna = t("meteo.moon", { pct, quando })
  const tipo = m.level !== "nogo" ? "larga" : tutta ? "stretta" : "mista"
  const lungo = resto({ da, a })
  return {
    tipo,
    testo: lungo && m.level !== "go" ? `${luna} \u00b7 ${lungo}` : luna,
    breve:
      m.level !== "nogo" || tutta
        ? t("meteo.moon.short", { pct })
        : resto({ da: da.slice(0, 2), a: a.slice(0, 2) }),
  }
}

const ripresaLuna = (n: Notte): Protagonista["ripresa"] => {
  const r = lunaDellaNotte(n)
  return r ? { tipo: r.tipo, testo: r.testo } : null
}

const ripresaDi = (n: Notte): Pick<NotteStriscia, "rip"> => {
  const r = lunaDellaNotte(n)
  return r ? { rip: { tipo: r.tipo, testo: r.breve } } : {}
}

/** A night's tile in the strip (board `tiles`). */
export function tessera(n: Notte, prima: boolean, sel: boolean, on: () => void): NotteStriscia {
  const es = n.verdict ? ESITO[n.verdict] : ("mancante" as const)
  const posa = n.exposure_hours ?? 0
  const ore = n.trend
    ? t("meteo.strip.dark", { n: numero(Math.round(n.dark_hours)) })
    : !n.verdict
      ? "?"
      : posa < 0.05
        ? t("meteo.strip.none")
        : orePosa(posa)
  const larga = n.broadband_exposure_hours ?? 0
  const stretta = n.narrowband_exposure_hours ?? 0
  const range = n.trend
    ? n.sky_word
      ? `${t(`weather.sky.word.${n.sky_word}`)} \u00b7 ${numero(Math.round(n.cloud_total_pct ?? 0))}%`
      : ""
    : larga >= 0.05 && stretta >= 0.05
      ? t("meteo.strip.split", { larga: unDecimale(larga), stretta: unDecimale(stretta) })
      : n.usable_since && n.usable_until
        ? `${oraDelSito(n.usable_since).slice(0, 2)}\u2013${oraDelSito(n.usable_until).slice(0, 2)}`
        : n.sky_word
          ? t(`weather.sky.word.${n.sky_word}`).toLowerCase()
          : ""
  const cloud = n.measures.find((m) => m.code === "cloud")
  const celle: CellaMeteo[] = disegnate(n).map((o) => {
    const v = o.cloud_total_pct
    return {
      h: v === null ? 100 : 20 + v * 0.8,
      esito: v === null || !nelBuio(o, n) || !o.levels.cloud ? null : ESITO[o.levels.cloud],
    }
  })
  const tag = prima ? t("weather.night.tonight") : ""
  return {
    day: giornoENumero(n.night, true),
    tag,
    tagS: n.trend ? t("weather.night.trend") : tag,
    tend: n.trend,
    sel,
    esito: es,
    ...(n.verdict ? {} : { pillT: t("weather.card.unknownWord") }),
    ...ripresaDi(n),
    hours: ore,
    range,
    cells: cloud ? celle : [],
    on,
  }
}

/** "Previsione Open-Meteo del 30 settembre, 18:05 (2 ore fa) \u00b7 Seeing Meteoblue del ... \u00b7 ora
 *  locale del sito", and its short phone form "Open-Meteo 2 ore fa \u00b7 Meteoblue 14 ore fa". */
export function arrivo(m: Meteo): { lungo: string; corto: string } {
  if (m.fetched_at === null) return { lungo: "", corto: "" }
  const seeing = m.sources.find((f) => f.source === "meteoblue")
  const quando = (at: string) => ({ giorno: giornoBreve(at), ora: orario(at), fa: fa(at) })
  const parti = [
    t("meteo.arrived", quando(m.fetched_at)),
    ...(seeing ? [t("meteo.arrived.seeing", quando(seeing.fetched_at))] : []),
    t("weather.head.siteTime"),
  ]
  const corti = [
    t("meteo.arrived.short", { fa: fa(m.fetched_at) }),
    ...(seeing ? [t("meteo.arrived.seeing.short", { fa: fa(seeing.fetched_at) })] : []),
  ]
  return { lungo: parti.join(" \u00b7 "), corto: corti.join(" \u00b7 ") }
}

/** No forecast worth reading: never arrived, or without nights. */
export const senzaPrevisione = (m: Meteo): boolean => m.fetched_at === null || m.nights.length === 0

/** The page notice where there is nothing to show (board `av`). */
export type AvvisoDiPagina = {
  segno: "!" | "?"
  titolo: string
  testo?: string | undefined
  azione?: { l: string; a?: string; aggiorna?: boolean }
}

export function avvisoDellaPagina(m: Meteo): AvvisoDiPagina | null {
  if (m.site === null) {
    return {
      segno: "?",
      titolo: t("weather.noSite.title"),
      testo: t("weather.noSite.why"),
      azione: { l: t("weather.noSite.how"), a: "/impostazioni/siti" },
    }
  }
  if (m.missing === "no_timezone") {
    return {
      segno: "!",
      titolo: t("weather.noTimezone"),
      azione: { l: t("weather.noTimezone.how"), a: "/impostazioni/siti" },
    }
  }
  const r = m.last_request
  if (r && r.status !== "ok" && senzaPrevisione(m)) {
    return {
      segno: "!",
      titolo: t(`weather.silent.${r.status}.none`, { ora: orario(r.at) }),
      testo: m.fetched_at ? t("meteo.stale.gone") : undefined,
      azione: { l: t("weather.refresh"), aggiorna: true },
    }
  }
  if (m.fetched_at === null) {
    return { segno: "?", titolo: t("weather.never"), testo: t("weather.never.how") }
  }
  if (m.nights.length === 0) {
    return { segno: "?", titolo: t("weather.noNights"), testo: t("meteo.noNights.how") }
  }
  return null
}

/** The row under the head when the last request failed but the forecast still holds. */
export function rigaDelServizio(m: Meteo): string | null {
  const r = m.last_request
  if (!r || r.status === "ok" || senzaPrevisione(m) || m.fetched_at === null) return null
  return t(`weather.silent.${r.status}`, { ora: orario(r.at), prima: orario(m.fetched_at) })
}

/** The night's edges for the facts: "20:48\u201305:48" of the judged window, from the sky bands. */
export function buioDellaNotte(n: Notte): string | null {
  const dentro = (n.sky_bands ?? []).filter((b) =>
    n.window === "dark"
      ? b.kind === "dark"
      : n.window === "nautical"
        ? b.kind === "dark" || b.kind === "astronomical"
        : b.kind !== "day",
  )
  const a = dentro[0]
  const b = dentro[dentro.length - 1]
  return a && b ? `${oraDelSito(a.starts_at)}\u2013${oraDelSito(b.ends_at)}` : null
}

/** The hour's word on a measure: the backend's level, or neutral where the measure has none. */
export function livelloDellOra(o: Ora, code: Codice): Livello | null {
  return code in o.levels ? (o.levels[code as keyof Ora["levels"]] ?? null) : null
}
