/**
 * Le Notti in parole: cio' che l'API manda, scritto come la tavola v76. Si formatta e basta:
 * esiti, ore di posa, ripresa e conti arrivano gia' fatti (`docs/domini/notti.md`).
 */
import type { components } from "./api/schema"
import type { PezzoFiltro } from "./componenti/BarraFiltri"
import type { EsitoNotte } from "./componenti/CalendarioNotti"
import type { TipoRipresa } from "./componenti/Ripresa"
import {
  type Chiave,
  dataLunga,
  giornoENumero,
  notte as dataBreve,
  numero,
  oreEMinuti,
  t,
  unDecimale,
} from "./i18n"

export type Notte = components["schemas"]["Night"]
export type Elenco = components["schemas"]["NightList"]
export type Mese = components["schemas"]["NightMonth"]

// Quanti oggetti per notte si nominano: gli altri si contano ("e 2 altri").
const OGGETTI_IN_VISTA = 3

const ESITI: Record<string, EsitoNotte> = { go: 0, marginal: 1, nogo: 2 }
const PAROLE: Record<EsitoNotte, Chiave> = {
  0: "ui.outcome.good",
  1: "ui.outcome.uncertain",
  2: "ui.outcome.unsuitable",
  [-1]: "nights.sky.silent",
}
const SEGNI: Record<EsitoNotte, string> = { 0: "\u2713", 1: "!", 2: "\u2715", [-1]: "?" }

export function esitoDi(verdetto: string | null | undefined): EsitoNotte {
  return verdetto ? (ESITI[verdetto] ?? -1) : -1
}

export const segnoDi = (e: EsitoNotte): string => SEGNI[e]
export const parolaDi = (e: EsitoNotte): string => t(PAROLE[e])

export const titoloDi = (n: Notte): string => dataLunga(n.night_date)

/** \u00ABmer 30\u00BB: il giorno breve della striscia. */
export const giornoBreve = (n: Notte): string => giornoENumero(n.night_date, true)

const FONTI: Record<Notte["site_from"], Chiave> = {
  frames: "nights.site.frames",
  home: "nights.site.home",
  answer: "nights.site.answer",
}
export const fonteDelSito = (n: Notte): string => t(FONTI[n.site_from])

/** Le ore di una notte, o null se nessun frame dice quanto e' durato. */
export const oreDi = (secondi: number): string | null => (secondi > 0 ? oreEMinuti(secondi) : null)

export interface Cielo {
  esito: EsitoNotte
  pillola: string
  titolo: string
  sotto: string
  corto: string
  striscia: string
  /** Una tacca per ora di buio, piene quante le ore di posa. */
  tacche: { tutte: number; piene: number } | null
  modificaSito: boolean
}

function conAerosol(testo: string, senza: boolean): string {
  return senza ? `${testo} \u00B7 ${t("nights.sky.noAerosol")}` : testo
}

/** Il cielo di una notte passata: verdetto dalla Trasparenza, nuvole in classi okta. */
export function cielo(n: Notte): Cielo {
  const m = n.weather
  const e = esitoDi(m.verdict)
  if (m.state === "unknown") {
    return {
      esito: -1,
      pillola: t("nights.sky.unknown"),
      titolo: t("nights.sky.unknown.title"),
      sotto: t("nights.sky.unknown.why"),
      corto: t("nights.sky.unknown.short"),
      striscia: t("nights.sky.unknown.strip"),
      tacche: null,
      modificaSito: true,
    }
  }
  if (m.state === "waiting" || e === -1 || m.exposure_hours == null) {
    const arriva = m.state === "waiting" && m.arrives_on ? dataBreve(m.arrives_on) : null
    return arriva
      ? {
          esito: -1,
          pillola: t("nights.sky.arriving"),
          titolo: t("nights.sky.arriving.title", { data: arriva }),
          sotto: t("nights.sky.arriving.why"),
          corto: t("nights.sky.arriving.short", { data: arriva }),
          striscia: t("nights.sky.arriving.strip"),
          tacche: null,
          modificaSito: false,
        }
      : {
          esito: -1,
          pillola: t("nights.sky.silent"),
          titolo: t("nights.sky.silent.title"),
          sotto: t("nights.sky.silent.why"),
          corto: t("nights.sky.silent.short"),
          striscia: t("nights.sky.silent"),
          tacche: null,
          modificaSito: false,
        }
  }
  const nuvole = m.sky_word
    ? t("nights.sky.mean", {
        cielo: t(`weather.sky.word.${m.sky_word}`),
        pct: numero(Math.round(m.cloud_total_pct ?? 0)),
      })
    : ""
  const posa = unDecimale(m.exposure_hours)
  const buio = numero(Math.round(m.dark_hours))
  const senzaBuio = m.window === "sun_down"
  const sotto = senzaBuio
    ? t("nights.sky.sunDown", { n: buio })
    : t("nights.sky.exposure", { h: posa, b: buio })
  const corto = senzaBuio
    ? t("nights.sky.sunDown.short", { n: buio })
    : t("nights.sky.exposure.short", { h: posa, b: buio })
  return {
    esito: e,
    pillola: parolaDi(e),
    titolo: nuvole,
    sotto: conAerosol(sotto, m.without_aerosol),
    corto,
    striscia: parolaDi(e),
    tacche: senzaBuio
      ? null
      : { tutte: Math.round(m.dark_hours), piene: Math.round(m.exposure_hours) },
    modificaSito: false,
  }
}

const TIPI: Record<NonNullable<Notte["shooting"]>["kind"], TipoRipresa> = {
  broadband: "larga",
  narrowband: "stretta",
  mixed: "mista",
}

/** Cosa lasciava la Luna: il segno e le ore di banda larga, o \u00ABsolo banda stretta\u00BB. */
export function ripresa(n: Notte): { tipo: TipoRipresa; testo: string } | null {
  const r = n.shooting
  if (!r) return null
  const testo =
    r.broadband_hours > 0
      ? t("nights.shooting.broad", { h: oreEMinuti(r.broadband_hours * 3600) })
      : t("nights.shooting.narrow")
  return { tipo: TIPI[r.kind], testo }
}

export interface LunaDellaNotte {
  pct: number
  lato: "destra" | "sinistra"
  titolo: string
  testo: string
}

export function luna(n: Notte): LunaDellaNotte | null {
  const l = n.moon
  if (!l) return null
  return {
    pct: l.illumination_pct,
    lato: l.lit_side === "right" ? "destra" : "sinistra",
    titolo: t(`moon.${l.phase_key}`),
    testo: t("nights.moon.lit", { pct: l.illumination_pct }),
  }
}

export interface OggettoDellaNotte {
  nome: string
  ore: string
  larghezza: string
}

export function oggetti(n: Notte): { primi: OggettoDellaNotte[]; altri: string | null } {
  const primi = n.objects.slice(0, OGGETTI_IN_VISTA).map((o) => ({
    nome: o.name ?? o.key,
    ore: oreDi(o.integration_s) ?? t("nights.untimed"),
    larghezza: `${o.bar_pct}%`,
  }))
  const resto = n.objects.length - primi.length
  return { primi, altri: resto > 0 ? t("nights.objects.more", { n: resto }) : null }
}

/** I nomi degli oggetti in fila, per la riga dell'elenco. */
export function oggettiInFila(n: Notte): string {
  const { primi, altri } = oggetti(n)
  return [primi.map((o) => o.nome).join(" \u00B7 "), altri].filter(Boolean).join(" ")
}

export function filtri(n: Notte): PezzoFiltro[] {
  // frame senza filtro nell'header: un pezzo tratteggiato, non una barra muta (tavola, `ignoto`)
  if (!n.filters.length && n.frames > 0) {
    return [
      {
        banda: "UNKNOWN",
        nome: t("filters.none"),
        frame: n.frames,
        secondi: n.integration_s > 0 ? n.integration_s : null,
        peso: 1,
      },
    ]
  }
  return n.filters.map((f) => ({
    banda: f.passband,
    nome: f.name,
    frame: f.frames,
    secondi: f.integration_s > 0 ? f.integration_s : null,
    // una notte senza tempo pesa coi frame, un minuto l'uno (tavola, BarraFiltri)
    peso: f.integration_s > 0 ? f.integration_s : f.frames * 60,
  }))
}

/** Il numero grande della protagonista e la riga sotto. */
export function numeri(n: Notte): { grande: string; parola: string; sotto: string } {
  const ore = oreDi(n.integration_s)
  if (ore === null) {
    return {
      grande: t("nights.frames", { n: n.frames }),
      parola: t("nights.untimed"),
      sotto: t("nights.notime"),
    }
  }
  const frame = t("nights.frames", { n: n.frames })
  return {
    grande: ore,
    parola: t("nights.hours"),
    sotto: n.untimed ? `${frame} \u00B7 ${t("nights.frames.untimed", { n: n.untimed })}` : frame,
  }
}

/** \u00AB2 notti \u00B7 5 h 10\u00BB, o \u00ABnessuna notte\u00BB. */
export function sommaDelMese(notti: number, secondi: number): string {
  if (!notti) return t("nights.month.none")
  const quante = t("nights.month.nights", { n: notti })
  const ore = oreDi(secondi)
  return ore ? `${quante} \u00B7 ${ore}` : quante
}
