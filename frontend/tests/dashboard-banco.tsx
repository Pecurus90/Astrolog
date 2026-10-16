/**
 * Il banco della **Dashboard**: la notte con le sei misure, la Luna, l'ultima notte dell'archivio e
 * il gesto con cui si arriva alla pagina. Lo usano la pagina (`dashboard.test.tsx`) e gli stati
 * (`dashboard-stati.test.tsx`).
 */
import { STANOTTE, colonna, disegna } from "./banco"
import { NOTTE as DEL_METEO, TENDENZA, meteo, misura } from "./meteo-banco"

// le sei misure della Dashboard: il banco del Meteo non ha jet stream e condensa con un valore
export const NOTTE = {
  ...DEL_METEO,
  measures: [
    ...DEL_METEO.measures,
    misura("jet", { level: "go", value: 96, axis_max: 200 }),
    misura("condensation", { level: "go", value: 8, axis_min: -5, axis_max: 15 }),
  ],
}

export const STANOTTE_CON_LUNA = {
  "/api/v1/tonight": {
    stato: 200,
    corpo: {
      night: "2026-09-26",
      site: null,
      moon: {
        phase_key: "waning_gibbous", illumination_pct: 62, rise: "2026-09-26T23:40:00+02:00", set: "2026-09-27T15:17:00+02:00",
        lit_side: "left", highest: null, track: [], ceiling_deg: 90,
      },
      sky_bands: [],
      dark_s: 31380,
      weather: null,
    },
  },
}

export const NOTTE_ARCHIVIO = {
  id: 7, night_date: "2026-09-19", site: "Casa", site_source: "header", frames: 180, integration_s: 15120, untimed: 0,
  objects: [
    { key: "m31", name: "M 31", frames: 120, integration_s: 9000, untimed: 0, bar_pct: 100 },
    { key: "m33", name: "M 33", frames: 40, integration_s: 4000, untimed: 0, bar_pct: 44 },
    { key: "m45", name: "M 45", frames: 20, integration_s: 2120, untimed: 0, bar_pct: 24 },
  ],
  filters: [], moon: null, weather: { verdict: null, cloud_total_pct: null, usable_hours: null, window: null, window_hours: null, state: "unknown", arrives_on: null },
}

export function notti(items: unknown[], fuori = 0) {
  return {
    "/api/v1/nights": {
      stato: 200,
      corpo: {
        items, total: items.length, limit: 1, offset: 0, totals: { nights: items.length, frames: 0, integration_s: 0, untimed: 0 },
        waiting: fuori ? [{ answer_at: "review", frames: fuori }] : [], waiting_frames: fuori, still_reading: 0, reading_done_pct: null,
      },
    },
  }
}

/** Le cartelle d'archivio scelte: quante, e basta, perche' la Dashboard guarda solo se ce n'e'. */
export function cartelle(total: number) {
  return { "/api/v1/folders": { stato: 200, corpo: { items: [], total, limit: 50, offset: 0 } } }
}

export const PROSSIME = [
  { ...NOTTE, night: "2026-09-27", verdict: "nogo", usable_hours: 0, usable_since: null, usable_until: null },
  { ...NOTTE, night: "2026-09-28", verdict: "go", usable_hours: 8, usable_since: "2026-09-28T21:00:00+02:00", usable_until: "2026-09-29T05:00:00+02:00" },
  { ...TENDENZA, night: "2026-09-29", window_hours: 9 },
]

/** La Dashboard montata. `previsione` cambia la risposta del meteo, `altre` aggiunge o sostituisce
 *  rotte, `larga` misura la colonna (il telefono e' sotto i 900). */
export async function montaDashboard({ previsione = {}, altre = {}, larga }: {
  previsione?: Record<string, unknown>; altre?: Record<string, unknown>; larga?: number | undefined
} = {}) {
  meteo(
    { fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE, ...PROSSIME], ...previsione },
    {
      ...STANOTTE, ...STANOTTE_CON_LUNA, ...notti([NOTTE_ARCHIVIO]), ...cartelle(1),
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 32 } }, ...altre,
    } as never,
  )
  // dopo `meteo`: il banco non deve togliere la misura della colonna
  if (larga !== undefined) colonna(larga)
  return disegna()
}
