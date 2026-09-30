/**
 * Il banco della pagina **Attrezzatura**: le righe di fabbrica che manda l'API e la strada con cui
 * l'utente ci arriva. Lo usano le prove della pagina e quelle dei gesti che scrivono qualcosa.
 */
import { fireEvent, screen } from "@testing-library/react"

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
  backfocus_mm: null,
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

export const CORREDO = {
  id: 10,
  name: "Il grande",
  mount_id: null as number | null,
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
}

export const FILTRO = {
  id: 3,
  name: "Ha",
  brand: null,
  model: null,
  bands: [{ band: "HA", width_nm: 3 }],
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
    ...(porte as Parameters<typeof rispondi>[0]),
    ...STANOTTE,
    "/api/v1/gear": {
      stato: 200,
      corpo: {
        instruments: [OTTICA, MONTATURA],
        rigs: [CORREDO],
        filters: [FILTRO],
        cards: SCHEDE,
        ...corpo,
      },
    },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...SPINA,
  })
}

/** Apre l'app e va su Attrezzatura **dalla barra**: e' la strada dell'utente, e prova anche che
 *  la voce sia accesa -- una pagina raggiungibile solo scrivendo l'indirizzo non esiste. */
export async function apriAttrezzatura() {
  const reso = await disegna()
  fireEvent.click(await screen.findByRole("link", { name: /attrezzatura/i }))
  await screen.findByRole("heading", { name: /attrezzatura/i })
  return reso
}
