/**
 * Il banco del **Meteo**: le notti di prova e i gesti con cui si arriva alla pagina.
 *
 * Sta qui perche' lo usano la pagina larga (`meteo.test.tsx`) e quella del telefono
 * (`meteo-telefono.test.tsx`): due copie di un banco un giorno raccontano due previsioni.
 */
import { fireEvent, screen } from "@testing-library/react"

import { SALUTE, SPINA, STANOTTE, type Voce, disegna, impostazioni, rispondi } from "./banco"

export const MODELLI = ["best_match", "ecmwf_ifs025", "icon_seamless", "gfs_seamless"]

export const GIUDIZI = {
  cloud: "go", cloud_low: "go", rain: "go", gust: "go", wind: "go", condensation: "go",
  jet: "go", seeing: null, aerosol: null, moon: null, visibility: "go",
}

export function ora(at: string, sky: string, campi: Record<string, unknown> = {}) {
  return {
    at,
    sky,
    cloud_total_pct: 0,
    cloud_low_pct: 0,
    cloud_mid_pct: 0,
    cloud_high_pct: 0,
    temperature_c: 12,
    humidity_pct: 60,
    dew_point_c: 4,
    wind_kmh: 5,
    wind_gust_kmh: 10,
    precip_mm: 0,
    visibility_km: 12,
    wind_700hpa_kmh: 30,
    wind_250hpa_kmh: 120,
    seeing_arcsec: null,
    aerosol_optical_depth: 0.12,
    dust_ugm3: null,
    moon_pct: null,
    dew_spread_c: 8,
    levels: GIUDIZI,
    shown: true,
    ...campi,
  }
}

export function misura(code: string, campi: Record<string, unknown> = {}) {
  return {
    code, level: null, weighs: false, value: null, peak: null, peak_at: null, peak_until: null,
    spans: [], axis_min: 0, axis_max: 100, axis_curve: "linear", since: null, until: null, hours: 0, known_hours: 3,
    known_since: null, known_until: null, known_from_start: false, known_to_end: false, ...campi,
  }
}

export const NOTTE = {
  night: "2026-09-26",
  trend: false,
  agreement: { go: 1, marginal: 3, nogo: 0, unknown: 0, total: 4 },
  wind_700hpa_kmh: 42,
  wind_700hpa_tenths: 8,
  verdict: "marginal",
  cloud_total_pct: 40,
  usable_hours: 3,
  usable_since: "2026-09-26T23:00:00+02:00",
  usable_until: "2026-09-27T02:00:00+02:00",
  window: "dark",
  window_hours: 8,
  shown_from: "2026-09-26T19:00:00+02:00",
  shown_until: "2026-09-26T23:00:00+02:00",
  measures: [
    misura("cloud", { level: "marginal", value: 40, peak: 80, peak_at: "2026-09-26T22:00:00+02:00", peak_until: "2026-09-26T23:00:00+02:00" }),
    misura("cloud_low", { level: "go", value: 5 }),
    misura("wind", {
      level: "nogo",
      weighs: true,
      value: 20,
      axis_max: 45,
      spans: [
        { level: "marginal", since: "2026-09-26T20:00:00+02:00", until: "2026-09-26T21:00:00+02:00", hours: 1 },
        { level: "nogo", since: "2026-09-26T21:00:00+02:00", until: "2026-09-26T23:00:00+02:00", hours: 2 },
      ],
      since: "2026-09-26T21:00:00+02:00",
      until: "2026-09-26T23:00:00+02:00",
      hours: 2,
    }),
    misura("gust", { level: "go", peak: 35, peak_at: "2026-09-26T22:00:00+02:00", peak_until: "2026-09-26T23:00:00+02:00" }),
    misura("rain", { level: "go", value: 0, peak: 0, axis_max: 1.5 }),
    misura("seeing", { known_hours: 0 }),
    misura("aerosol", { level: "go", value: 0.05, axis_max: 0.2 }),
    misura("temperature", { value: 5, axis_min: 4, axis_max: 12 }),
    misura("dew_point", { value: 4 }),
    misura("visibility", { level: "go", value: 12, peak: 12, axis_max: 12 }),
    misura("dust", { value: 2, axis_max: 4 }),
    misura("wind_700", { value: 42 }),
  ],
  hours: [
    ora("2026-09-26T12:00:00+02:00", "day", { shown: false }),
    ora("2026-09-26T19:00:00+02:00", "civil"),
    ora("2026-09-26T22:00:00+02:00", "dark", { wind_kmh: null, wind_gust_kmh: 35 }),
    ora("2026-09-26T23:00:00+02:00", "dark"),
  ],
}

export const TENDENZA = {
  ...NOTTE,
  night: "2026-09-29",
  trend: true,
  usable_hours: null,
  usable_since: null,
  usable_until: null,
  verdict: "go",
  agreement: { go: 2, marginal: 1, nogo: 1, unknown: 0, total: 4 },
  measures: [],
  hours: [],
}

/** La previsione del banco; `altre` aggiunge rotte o sostituisce quelle di qui. */
export function meteo(corpo: Record<string, unknown>, altre: Record<string, Voce> = {}) {
  rispondi({
    ...STANOTTE,
    "/api/v1/weather": {
      stato: 200,
      corpo: {
        site: "Casa",
        missing: null,
        model: "best_match",
        models: MODELLI,
        fetched_at: null,
        last_request: null,
        full_nights: 3,
        retry_s: 900,
        seeing: { key: false, source: null, meteoblue: null },
        sources: [{ source: "cams", fetched_at: "2026-09-25T15:00:00.000Z" }],
        scales: [
          { code: "wind", steps: [{ level: "nogo", bound: 29, strict: false }, { level: "marginal", bound: 20, strict: false }], lower_is_worse: false },
          { code: "condensation", steps: [{ level: "marginal", bound: 3, strict: true }], lower_is_worse: true },
        ],
        nights: [],
        ...corpo,
      },
    },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...SPINA,
    ...altre,
  })
}

/** Dalla barra, come l'utente: prova anche che la voce sia accesa. */
export async function apriMeteo() {
  const reso = await disegna()
  fireEvent.click(await screen.findByRole("link", { name: /meteo/i }))
  await screen.findByRole("heading", { level: 1, name: /meteo/i })
  return reso
}

export const conNotti = (...notti: unknown[]) => meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: notti })
export const scheda = () => screen.findByRole("tabpanel")

export function carta(nome: RegExp) {
  const titolo = screen.getAllByRole("heading", { level: 3 }).find((h) => nome.test(h.textContent ?? ""))
  return titolo?.closest("article") as HTMLElement
}
