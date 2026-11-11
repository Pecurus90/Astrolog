import type { components } from "./api/schema"
import type { TipoRipresa } from "./componenti/Ripresa"
import type { Esito } from "./componenti/Pillola"
import { type Chiave, numero, oraDelSito, oreEMinuti, t, unDecimale } from "./i18n"
import { buioDellaNotte, fraseDellaLuna } from "./Stanotte"

/**
 * The Dashboard's words (board v79), from what `/tonight` and `/weather` wrote: here a sentence
 * is chosen, never a number made. Each empty is a sentence, never a dash.
 */

export type Stanotte = components["schemas"]["TonightOut"]
export type Meteo = components["schemas"]["WeatherOut"]
export type NotteMeteo = Meteo["nights"][number]
export type Breve = components["schemas"]["WeatherBriefOut"]
type Livello = "go" | "marginal" | "nogo"

/** The outcome's index on the board: 0 good, 1 uncertain, 2 not suitable. */
export const ESITO: Record<Livello, 0 | 1 | 2> = { go: 0, marginal: 1, nogo: 2 }
const SEGNO = ["\u2713", "!", "\u2715"] as const
const PAROLA = [
  "ui.outcome.good",
  "ui.outcome.uncertain",
  "ui.outcome.unsuitable",
] as const satisfies readonly Chiave[]

/** The head's pill: sign, then "notte buona". */
export function pillolaDellaNotte(verdetto: Livello): { esito: 0 | 1 | 2; testo: string } {
  const e = ESITO[verdetto]
  return { esito: e, testo: t("dashboard.night.pill", { segno: SEGNO[e], parola: t(PAROLA[e]) }) }
}

/** "4,6 ore" or "Nessuna ora" (board `posaOre`: under 0,05 h nothing is written). */
export function orePosa(ore: number): string {
  return ore < 0.05
    ? t("dashboard.exposure.none")
    : t("dashboard.exposure.hours", { ore: unDecimale(ore) })
}

/** "3,1 in banda larga, 1,5 solo banda stretta", "solo banda stretta" or nothing (board `posaBande`). */
export function bandeDellaPosa(
  b: Pick<Breve, "exposure_hours" | "broadband_exposure_hours" | "narrowband_exposure_hours">,
): string {
  const tot = b.exposure_hours ?? 0
  const larga = b.broadband_exposure_hours ?? 0
  const stretta = b.narrowband_exposure_hours ?? 0
  if (larga >= 0.05 && stretta >= 0.05) {
    return t("dashboard.exposure.split", { larga: unDecimale(larga), stretta: unDecimale(stretta) })
  }
  return tot >= 0.05 && stretta >= 0.05 ? t("dashboard.exposure.narrow") : ""
}

/** The night's Moon in one line under the big number (board `lunaNotte`): kind and words. */
export function ripresaDiStanotte(s: Stanotte): { tipo: TipoRipresa; testo: string } | null {
  const su = s.moon_in_dark ?? null
  if (!su) return null
  const tipo: TipoRipresa =
    su.level !== "nogo" ? "larga" : su.from_start && su.to_end ? "stretta" : "mista"
  return { tipo, testo: fraseDellaLuna(s) }
}

/** The head's line under the number: bands, dark, Transparency, the models, the upper wind. */
export function sottoDellaNotte(s: Stanotte, w: Breve): string {
  const parti = [bandeDellaPosa(w), buioDellaNotte(s)]
  if (w.transparency != null)
    parti.push(t("dashboard.transparency.mean", { v: numero(Math.round(w.transparency)) }))
  if (w.without_aerosol) parti.push(t("dashboard.transparency.noAerosol"))
  if (w.verdict)
    parti.push(
      t("dashboard.agreement", {
        n: numero(w.agreement[w.verdict]),
        su: numero(w.agreement.total),
      }),
    )
  if (w.wind_700hpa_kmh != null) {
    const v = numero(w.wind_700hpa_kmh)
    parti.push(
      w.wind_700hpa_tenths == null
        ? t("dashboard.wind700.nobase", { v })
        : t("dashboard.wind700", { v, n: numero(w.wind_700hpa_tenths) }),
    )
  }
  return parti.filter(Boolean).join(" \u00b7 ")
}

/** A dark stretch's band words: "banda larga" or "solo banda stretta". */
export const nomeDellaBanda = (band: "broadband" | "narrowband"): string =>
  t(band === "broadband" ? "dashboard.band.broad" : "dashboard.band.narrow")

/** The two Moon tiles: hours of each band in the dark and their stretches. */
export function latiDellaRipresa(
  s: Stanotte,
): { tipo: TipoRipresa; nome: string; v: string; sotto: string }[] {
  const tratti = s.shooting ?? []
  const lato = (band: "broadband" | "narrowband", secondi: number | null | undefined) => {
    const suoi = tratti.filter((x) => x.band === band)
    return {
      tipo: (band === "broadband" ? "larga" : "stretta") as TipoRipresa,
      nome: nomeDellaBanda(band),
      v: secondi ? oreEMinuti(secondi) : t("dashboard.band.noHours"),
      sotto: suoi.length
        ? suoi
            .map((x) =>
              t("frame.tonight.stretch", { da: oraDelSito(x.starts_at), a: oraDelSito(x.ends_at) }),
            )
            .join(" \u00b7 ")
        : t("dashboard.band.noHours"),
    }
  }
  return [lato("broadband", s.broadband_dark_s), lato("narrowband", s.narrowband_dark_s)]
}

/** The next nights' shooting sign, from the exposure split the forecast wrote. */
export function ripresaDellaNotte(n: Breve): { tipo: TipoRipresa; testo: string } | null {
  const larga = n.broadband_exposure_hours
  const stretta = n.narrowband_exposure_hours
  if (larga == null || stretta == null || (n.exposure_hours ?? 0) < 0.05) return null
  if (stretta < 0.05) return { tipo: "larga", testo: t("dashboard.band.broadAll") }
  if (larga < 0.05) return { tipo: "stretta", testo: t("dashboard.band.narrow") }
  return {
    tipo: "mista",
    testo: t("dashboard.band.mixed", { larga: unDecimale(larga), stretta: unDecimale(stretta) }),
  }
}

/** The outcome pill of a forecast night, or "senza meteo". */
export function esitoDellaNotte(n: Breve): { esito: Esito; testo: string } {
  if (!n.verdict) return { esito: "mancante", testo: t("dashboard.night.noWeather") }
  const e = ESITO[n.verdict]
  return { esito: e, testo: t(PAROLA[e]) }
}

/** "8,4 ore di posa, 21-06", "nessuna ora di posa", "9 ore di buio, tendenza". */
export function oreDellaNotte(n: NotteMeteo): string {
  if (n.trend) return t("dashboard.next.trend", { ore: numero(n.dark_hours) })
  const ore = n.exposure_hours ?? 0
  if (ore < 0.05) return t("dashboard.next.none")
  const tra =
    n.usable_since && n.usable_until
      ? t("dashboard.next.span", {
          da: oraDelSito(n.usable_since).slice(0, 2),
          a: oraDelSito(n.usable_until).slice(0, 2),
        })
      : ""
  return `${t("dashboard.next.hours", { ore: unDecimale(ore) })}${tra}`
}

/** "Sereno, 4%", "Coperto, 96%, pioggia dalle 17". */
export function cieloDellaNotte(n: NotteMeteo): string {
  if (!n.sky_word) return t("dashboard.next.noClouds")
  const pioggia = n.measures.find((m) => m.code === "rain" && m.level === "nogo")?.since ?? null
  const pct =
    n.cloud_total_pct == null
      ? ""
      : t("dashboard.next.pct", { pct: numero(Math.round(n.cloud_total_pct)) })
  const piove = pioggia ? t("dashboard.nights.rain", { ora: oraDelSito(pioggia).slice(0, 2) }) : ""
  return `${t(`weather.sky.word.${n.sky_word}`)}${pct}${piove}`
}
