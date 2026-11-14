/**
 * Il banco della **Dashboard** (tavola v79): stanotte a Cima Ekar con la Luna, i pianeti e il
 * buio diviso per banda, la previsione con le sei misure e le prossime notti, il calendario della
 * Luna e l'ultima notte dell'archivio. Lo usano la pagina (`dashboard.test.tsx`), gli stati
 * (`dashboard-stati.test.tsx`) e l'anno (`anno.test.tsx`).
 */
import { STANOTTE, disegna } from "./banco"
import { NOTTE as DEL_METEO, TENDENZA, meteo, misura, ora } from "./meteo-banco"

const H = (h: string) => `2026-09-30T${h}:00+02:00`
const D = (h: string) => `2026-10-01T${h}:00+02:00`

// le sei misure della Dashboard, con le ore della notte e la loro Trasparenza
export const NOTTE = {
  ...DEL_METEO,
  night: "2026-09-30",
  verdict: "go",
  agreement: { go: 3, marginal: 1, nogo: 0, unknown: 0, total: 4 },
  transparency: 78,
  exposure_hours: 4.6,
  broadband_exposure_hours: 3.1,
  narrowband_exposure_hours: 1.5,
  moonless_dark_hours: 3,
  sky_word: "clear",
  measures: [
    ...DEL_METEO.measures,
    misura("jet", { level: "go", value: 96, axis_max: 200 }),
    misura("condensation", { level: "go", value: 8, axis_min: -5, axis_max: 15 }),
  ],
  hours: [
    ora(H("12:00"), "day", { shown: false }),
    ora(H("19:00"), "civil", { transparency: 60 }),
    ora(H("21:00"), "dark", { transparency: 82 }),
    ora(H("23:00"), "dark", { transparency: 74 }),
  ],
}

const punto = (at: string, altitude_deg: number) => ({ at, altitude_deg })

export const STANOTTE_PIENA = {
  night: "2026-09-30",
  site: { name: "Cima Ekar", sky_sqm: 21.4, bortle: 4 },
  moon: {
    phase_key: "waning_gibbous", illumination_pct: 62, rise: H("23:40"), set: D("15:17"), rise_compass: "ENE",
    age_days: 21, distance_km: 371200, next_new: "2026-10-09", next_full: "2026-10-24", lit_side: "left",
    highest: punto(D("05:30"), 52), ceiling_deg: 75,
    track: [
      { ...punto(H("18:30"), -30), moonless_dark_left_s: 10000 },
      { ...punto(H("20:00"), -20), moonless_dark_left_s: 10000 },
      { ...punto(H("22:00"), -5), moonless_dark_left_s: 6000 },
      { ...punto(D("00:00"), 15), moonless_dark_left_s: 0 },
      { ...punto(D("02:00"), 35), moonless_dark_left_s: 0 },
      { ...punto(D("04:00"), 50), moonless_dark_left_s: 0 },
      { ...punto(D("06:00"), 52), moonless_dark_left_s: 0 },
      { ...punto(D("07:30"), 48), moonless_dark_left_s: 0 },
    ],
  },
  sky_bands: [
    { starts_at: H("12:00"), ends_at: H("19:11"), kind: "day" },
    { starts_at: H("19:11"), ends_at: H("19:41"), kind: "civil" },
    { starts_at: H("19:41"), ends_at: H("20:15"), kind: "nautical" },
    { starts_at: H("20:15"), ends_at: H("20:48"), kind: "astronomical" },
    { starts_at: H("20:48"), ends_at: D("05:48"), kind: "dark" },
    { starts_at: D("05:48"), ends_at: D("06:21"), kind: "astronomical" },
    { starts_at: D("06:21"), ends_at: D("06:55"), kind: "nautical" },
    { starts_at: D("06:55"), ends_at: D("07:25"), kind: "civil" },
    { starts_at: D("07:25"), ends_at: D("12:00"), kind: "day" },
  ],
  dark_s: 32400,
  chart: { starts_at: H("18:30"), ends_at: D("07:30"), dark_from: H("20:48"), dark_until: D("05:48") },
  planets: [
    { key: "saturn", track: [punto(H("20:00"), 20), punto(H("23:00"), 41), punto(D("03:00"), 10)], rise: null, set: D("04:10"), highest: punto(H("23:00"), 41) },
    { key: "jupiter", track: [punto(H("20:00"), -10), punto(D("03:00"), 30)], rise: H("23:05"), set: null, highest: punto(D("05:00"), 38) },
    { key: "mars", track: [punto(H("20:00"), -20), punto(D("05:00"), 20)], rise: D("01:10"), set: null, highest: punto(D("07:00"), 28) },
    { key: "venus", track: [punto(H("19:00"), 5), punto(H("20:00"), -5)], rise: null, set: H("19:40"), highest: punto(H("18:30"), 8) },
  ],
  moonless_dark: [{ starts_at: H("20:48"), ends_at: H("23:40") }],
  moon_in_dark: { level: "nogo", since: H("23:40"), until: D("05:48"), from_start: false, to_end: true },
  shooting: [
    { band: "broadband", starts_at: H("20:48"), ends_at: H("23:40"), seconds: 10320 },
    { band: "narrowband", starts_at: H("23:40"), ends_at: D("05:48"), seconds: 22080 },
  ],
  highest_planet: "saturn",
  broadband_dark_s: 10320,
  narrowband_dark_s: 22080,
  weather: {
    verdict: "go", cloud_total_pct: 16, usable_hours: 8, window: "dark", window_hours: 9, transparency: 78,
    exposure_hours: 4.6, broadband_exposure_hours: 3.1, narrowband_exposure_hours: 1.5, dark_hours: 9, without_aerosol: false,
    agreement: { go: 3, marginal: 1, nogo: 0, unknown: 0, total: 4 }, usable_since: H("21:00"), usable_until: D("05:00"),
    wind_700hpa_kmh: 15, wind_700hpa_tenths: 2, sky_word: "clear", moonless_dark_hours: 3,
  },
}

export const NOTTE_ARCHIVIO = {
  id: 7, night_date: "2026-09-19", site: "Casa", site_source: "header", frames: 180, integration_s: 15120, untimed: 0,
  objects: [
    { key: "m31", name: "M 31", frames: 120, integration_s: 9000, untimed: 0, bar_pct: 100 },
    { key: "m33", name: "M 33", frames: 40, integration_s: 4000, untimed: 0, bar_pct: 44 },
  ],
  filters: [], moon: null, weather: { verdict: null, cloud_total_pct: null, usable_hours: null, window: null, window_hours: null, state: "unknown", arrives_on: null },
}

export function notti(items: unknown[], fuori = 0) {
  return {
    "/api/v1/nights": {
      stato: 200,
      corpo: {
        items, total: items.length, limit: 1, offset: 0, totals: { nights: items.length, frames: items.length ? 180 : 0, integration_s: 0, untimed: 0, objects: 2 },
        waiting: fuori ? [{ answer_at: "site", frames: fuori }] : [], waiting_frames: fuori, still_reading: 0, reading_done_pct: null,
      },
    },
  }
}

/** Le cartelle d'archivio scelte: quante, e basta, perche' la Dashboard guarda solo se ce n'e'. */
export function cartelle(total: number) {
  return { "/api/v1/folders": { stato: 200, corpo: { items: [], total, limit: 50, offset: 0 } } }
}

/** Settembre e ottobre 2026 come il giro li scrive: il 19 settembre ripreso a Casa. */
export function calendario(vuoto = false) {
  const giorni = vuoto
    ? []
    : Array.from({ length: 61 }, (_, i) => {
        const d = new Date(Date.UTC(2026, 8, 1 + i)).toISOString().slice(0, 10)
        return {
          date: d, phase_key: "waxing_crescent", illumination_pct: 10, dark_s: 9 * 3600, moonless_dark_s: 4 * 3600, lit_side: "right",
          event: d === "2026-09-09" ? "new" : d === "2026-09-24" ? "full" : null,
          level: d < "2026-09-15" ? "go" : d < "2026-09-20" ? "marginal" : "nogo",
          shots: d === "2026-09-19" ? [{ night_id: 7, site: "Casa", objects: ["M 31", "M 33"], frames: 180, integration_s: 15120, untimed: 0 }] : [],
        }
      })
  return { "/api/v1/moon/calendar": { stato: 200, corpo: { today: "2026-09-30", good_pct: 25, limit_pct: 65, nights: giorni } } }
}

export const SCALA_DELLA_LUNA = {
  code: "moon",
  steps: [{ level: "nogo", bound: 65, strict: true }, { level: "marginal", bound: 25, strict: true }],
  lower_is_worse: false,
}

export const PROSSIME = [
  { ...NOTTE, night: "2026-10-01", verdict: "nogo", exposure_hours: 0, broadband_exposure_hours: 0, narrowband_exposure_hours: 0, sky_word: "overcast", cloud_total_pct: 96 },
  { ...NOTTE, night: "2026-10-02", verdict: "go", exposure_hours: 8.4, broadband_exposure_hours: 8.4, narrowband_exposure_hours: 0, cloud_total_pct: 4, usable_since: "2026-10-02T21:00:00+02:00", usable_until: "2026-10-03T06:00:00+02:00" },
  { ...TENDENZA, night: "2026-10-03", dark_hours: 9, sky_word: "scattered", cloud_total_pct: 38, transparency: 51 },
]

/** La Dashboard montata. `previsione` cambia la risposta del meteo, `stanotte` quella di stanotte,
 *  `altre` aggiunge o sostituisce rotte, `larga` misura la colonna (il telefono e' sotto i 700). */
export async function montaDashboard({ previsione = {}, stanotte = {}, altre = {}, larga }: {
  previsione?: Record<string, unknown>; stanotte?: Record<string, unknown>; altre?: Record<string, unknown>; larga?: number | undefined
} = {}) {
  meteo(
    { fetched_at: "2026-09-30T16:05:00.000Z", nights: [NOTTE, ...PROSSIME], scales: [SCALA_DELLA_LUNA], ...previsione },
    {
      ...STANOTTE,
      "/api/v1/tonight": { stato: 200, corpo: { ...STANOTTE_PIENA, ...stanotte } },
      ...notti([NOTTE_ARCHIVIO]), ...cartelle(1), ...calendario(),
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 32 } }, ...altre,
    } as never,
  )
  // il formato della consegna: sotto i 700 px il telefono, che si chiede dall'indirizzo
  if (larga !== undefined && larga < 700) window.history.pushState({}, "", "/?formato=telefono")
  return disegna()
}
