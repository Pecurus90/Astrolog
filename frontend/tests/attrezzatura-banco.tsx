/**
 * Il banco della pagina **Attrezzatura**: le righe di fabbrica che manda l'API e la strada con cui
 * l'utente ci arriva. Lo usano le prove della pagina e quelle dei gesti che scrivono qualcosa.
 */
import { fireEvent, screen, within } from "@testing-library/react"

import { SALUTE, SCHEDE, SPINA, STANOTTE, disegna, impostazioni, rispondi } from "./banco"

export const OTTICA = {
  id: 1,
  no_hours: null as string | null,
  kind: "optics",
  name: "TS 130 APO",
  brand: null,
  model: null,
  camera_type: null,
  pixel_size_um: null,
  pixel_from_sky_um: null,
  aperture_mm: 130,
  focal_mm: 910,
  reducer_factor: null,
  weight_kg: null,
  payload_kg: null,
  slots: null,
  optical_design: null as string | null,
  sensor: null,
  width_px: null,
  height_px: null,
  adc_bits: null,
  cooled: null,
  cooling_c: null,
  image_circle_mm: null,
  required_backfocus_mm: null,
  backfocus_tolerance_mm: null,
  thickness_mm: null,
  prism_mm: null,
  filter_size: null,
  step_um: null,
  total_steps: null,
  payload_no_cw_kg: null,
  numbers: {} as Record<string, unknown>,
  in_rigs: [] as { rig_id: number; frames: number; chosen: boolean }[],
  from_files: [] as string[],
  delete_refused: null as { code: string; frames: number; rigs: number[] } | null,
  rig_for_mount: null as number | null,
  biases: [] as { offset: number | null; bias_adu: number | null; frames: number }[],
  bar_pct: 100,
  notes: null,
  detected: true,
  mergeable_into: [] as number[],
  frames: 120,
  integration_s: 36000,
  untimed: 0,
  nights: 7,
  objects: [{ key: "m-31", name: "M 31", frames: 120, integration_s: 36000 }],
  counted: true,
}

export const MONTATURA = {
  ...OTTICA,
  id: 2,
  kind: "mount",
  name: "EQ6-R",
  no_hours: "no_rig",
  aperture_mm: null,
  focal_mm: null,
  payload_kg: 20,
  frames: null,
  integration_s: null,
  untimed: null,
  nights: null,
  objects: [],
}

const manca = (kind: string, field: string | null) => ({ missing: { kind, field } })

/** I conti di un setup come li scrive il backend: tre fatti, sei con cio' che manca. */
export const NUMERI = {
  focal_ratio: { value: 7, missing: null },
  sampling: { value: 0.85, seeing_from: 1.7, seeing_to: 2.4, missing: null },
  field: { width: 4.4, height: 2.99, missing: null },
  sensor_size: { width: null, height: null, ...manca("camera", "width_px") },
  coverage: { diagonal_mm: null, circle_mm: null, covers: null, ...manca("optics", "image_circle_mm") },
  guide_scale: { value: null, in_range: null, range_from: null, range_to: null, guide: null, guide_name: null, ...manca("guide", null) },
  guide_ratio: { value: null, ...manca("guide", null) },
  backfocus: { train_mm: 55.5, required_mm: 55, required_by: "optics", difference_mm: 0.5, tolerance_mm: 1, verdict: "in_tolerance", missing: null },
  load: { percent: null, within: null, weight_kg: null, payload_kg: null, ...manca("mount", null) },
}

export const CORREDO = {
  id: 10,
  name: "Il grande",
  optics_id: 1,
  camera_id: null as number | null,
  numbers: null as Record<string, unknown> | null,
  optics: "TS 130 APO",
  camera: "ASI2600MM",
  focal_mm: 910,
  frames: 120,
  integration_s: 36000,
  untimed: 0,
  nights: 7,
  objects: [{ key: "m-31", name: "M 31", frames: 120, integration_s: 36000 }],
  counted: true,
  scale_arcsec_px: 0.85,
  width_deg: 1.5,
  height_deg: 1,
  parts: [] as {
    kind: string
    id: number | null
    name: string
    frames: number
    chosen: boolean
    passband?: string | null
    ring_from?: number | null
    ring_to?: number | null
  }[],
  bar_pct: 100,
  title: "Il grande",
  // ottica e camera ci sono, le altre otto parti da indicare
  slots: ["optics", "camera", "reducer", "filter_wheel", "spacer", "mount", "focuser", "guide", "guide_camera", "software"].map(
    (kind, i) => ({ kind, filled: i < 2 }),
  ),
  slots_missing: 8,
}

export const FILTRO = {
  id: 3,
  name: "Ha",
  brand: null,
  model: null,
  passband: "HA",
  bands: [{ band: "HA", width_nm: 3 }],
  filter_size: null as string | null,
  thickness_mm: null as number | null,
  mounted: null as boolean | null,
  fast_optics: null as boolean | null,
  in_rigs: [] as { rig_id: number; frames: number; chosen: boolean }[],
  delete_refused: null as { code: string; frames: number; rigs: number[] } | null,
  bar_pct: 100,
  frames: 60,
  integration_s: 18000,
  untimed: 0,
  nights: 4,
  objects: [{ key: "m-42", name: "M 42", frames: 60, integration_s: 18000 }],
  counted: true,
  mergeable_into: [] as number[],
}

export function attrezzatura(corpo: Record<string, unknown> = {}, porte: Record<string, unknown> = {}) {
  rispondi({
    ...STANOTTE,
    "/api/v1/gear": {
      stato: 200,
      corpo: {
        instruments: [OTTICA, MONTATURA],
        rigs: [CORREDO],
        filters: [FILTRO],
        cards: SCHEDE,
        moon_deg: 0.527,
        fields: [],
        moon_pct: null,
        brands: [] as string[],
        ...corpo,
      },
    },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...SPINA,
    // last: a test's answer wins over the bench's (the scan running, a write)
    ...(porte as Parameters<typeof rispondi>[0]),
  })
}

/** Sceglie un gruppo dall'indice (tavola v82: il dettaglio mostra solo cio' che scegli) e torna il
 *  suo elenco. `lista` serve dove il nome del gruppo e' contenuto in quello della pillola. */
export async function vedi(gruppo: RegExp, lista: RegExp = gruppo) {
  const indice = await screen.findByRole("navigation", { name: /indice dell'attrezzatura/i })
  fireEvent.click(within(indice).getByRole("link", { name: gruppo }))
  return screen.findByRole("list", { name: lista })
}

/** Le sezioni del dettaglio di un setup (tavola v82): la carta col nome, le Parti, il Campo. */
export const parti = () => screen.findByRole("region", { name: /^parti$/i })
export const campo = () => screen.findByRole("region", { name: /^campo$/i })
export const carta = (nome: RegExp = /il grande/i) => screen.findByRole("region", { name: nome })
/** Una parte, per genere: la riga con i suoi pezzi e il suo «Seleziona». */
export async function parte(genere: string): Promise<HTMLElement> {
  const riga = (await parti()).querySelector(`[data-parte="${genere}"]`)
  if (!(riga instanceof HTMLElement)) throw new Error(`nessuna parte ${genere}`)
  return riga
}

/** Apre l'app e va su Attrezzatura **dal menu Altro**: e' la strada dell'utente, e prova anche
 *  che la voce ci sia -- una pagina raggiungibile solo scrivendo l'indirizzo non esiste. */
export async function apriAttrezzatura() {
  const reso = await disegna()
  fireEvent.click(await screen.findByRole("link", { name: "Altro" }))
  fireEvent.click(await screen.findByRole("menuitem", { name: /^attrezzatura/i }))
  await screen.findByRole("heading", { name: /attrezzatura/i })
  return reso
}
