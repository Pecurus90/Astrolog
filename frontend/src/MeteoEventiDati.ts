import { type Chiave, gradi, numero, oraDelSito, t } from "./i18n"
import { conUnita, disegnate, type Notte } from "./MeteoDati"

/**
 * The night's story in words (board v82 `pesa.ev`, Meteo.dc.html:460-499): the backend wrote
 * each event, its minute and its numbers; here a sentence is chosen, never an event made.
 */

export type Evento = Notte["events"][number]

/** How the dot beside the time looks: the verdict's word, the unknown, the Sun, the Moon, a ring. */
export type Punto = "go" | "marginal" | "nogo" | "ignoto" | "sole" | "luna" | "anello"

export type RigaDellEvento = {
  /** Unique within the night: the minute and the kind, with the planet. */
  chiave: string
  ora: string
  nome: string
  sotto: string
  punto: Punto
  /** A verdict event: the big dot and the bold name. */
  esito: boolean
  contano: boolean
  aria: string
}

// the board writes gusts whole (MS dec: 0), as the Wind card says its gusts; condensation keeps its tenth
const intero = (v: number | null): number | null => (v === null ? null : Math.round(v))

const pianeta = (e: Evento): string =>
  e.body ? t(`dashboard.chart.planet.${e.body}` as Chiave) : ""

function nome(e: Evento): string {
  const v = e.value ?? 0
  switch (e.kind) {
    case "verdict":
      return t(`meteo.event.verdict.${e.level ?? "nogo"}` as Chiave)
    case "clouds_over":
    case "clouds_under":
      return t(`meteo.event.${e.kind}` as Chiave, { b: numero(e.bound ?? 0) })
    case "condensation":
      return t("meteo.event.condensation", { b: conUnita("condensation", e.bound) })
    case "gust_peak":
      // gusts are wind: the same km/h, and the gust has no card of its own
      return t("meteo.event.gust_peak", { v: conUnita("wind", intero(e.value)) })
    case "moon_above":
    case "moon_below":
      return t(`meteo.event.${e.kind}` as Chiave, { g: gradi(v) })
    case "planet_rise":
    case "planet_set":
    case "planet_top":
      return t(`meteo.event.${e.kind}` as Chiave, { p: pianeta(e) })
    default:
      return t(`meteo.event.${e.kind}` as Chiave)
  }
}

function sotto(e: Evento): string {
  const v = e.value ?? 0
  switch (e.kind) {
    case "dark_start":
      return e.until ? t("meteo.event.dark_start.sub", { ora: oraDelSito(e.until) }) : ""
    case "verdict":
      return t(e.level === "go" ? "meteo.event.verdict.go.sub" : "meteo.event.verdict.sub", {
        v: numero(Math.round(v)),
      })
    case "sky_unknown":
      return e.until ? t("meteo.event.sky_unknown.sub", { ora: oraDelSito(e.until) }) : ""
    case "clouds_over":
    case "clouds_under":
      return t("meteo.event.clouds.sub", { v: numero(Math.round(v)) })
    case "rain_start":
      return t("meteo.event.rain_start.sub", { v: conUnita("rain", e.value) })
    case "condensation":
      return t("meteo.event.condensation.sub", { v: conUnita("condensation", e.value) })
    case "gust_peak":
      return t("meteo.event.gust_peak.sub")
    case "seeing_best":
      return t("meteo.event.seeing_best.sub", { v: conUnita("seeing", e.value) })
    case "moon_rise":
      return e.value == null ? "" : t("meteo.event.moon_rise.sub", { v: numero(Math.round(v)) })
    case "moon_above":
    case "moon_below":
      return t(`meteo.event.${e.kind}.${e.level === "nogo" ? "nogo" : "marginal"}` as Chiave)
    case "planet_top":
      return t("meteo.event.planet_top.sub", { g: gradi(v) })
    default:
      return ""
  }
}

function punto(e: Evento): Punto {
  if (e.kind === "sky_unknown") return "ignoto"
  if (e.group === "verdict") return e.level ?? "ignoto"
  if (e.group === "sun") return "sole"
  return e.group === "moon" ? "luna" : "anello"
}

export function rigaDellEvento(e: Evento): RigaDellEvento {
  const ora = oraDelSito(e.at)
  const n = nome(e)
  const s = sotto(e)
  return {
    chiave: `${e.at}${e.kind}${e.body ?? ""}`,
    ora,
    nome: n,
    sotto: s,
    punto: punto(e),
    esito: e.group === "verdict",
    contano: e.key_moment,
    aria: [ora, n, s].filter(Boolean).join(", "),
  }
}

/** The drawn hour holding the event, for the chart's thread: the last one starting by then. */
export function oraDellEvento(n: Notte, at: string): number | null {
  const quando = Date.parse(at)
  let trovata: number | null = null
  disegnate(n).forEach((o, i) => {
    if (Date.parse(o.at) <= quando) trovata = i
  })
  return trovata
}
