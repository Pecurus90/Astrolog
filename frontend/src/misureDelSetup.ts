import type { Formato } from "./componenti/Tema"
import type { components } from "./api/schema"
import { t } from "./i18n"

type Corredo = components["schemas"]["RigOnPage"]

// [T] Attrezzatura.dc.html `L` (210-213): the rig detail's measures per format
export const MISURE_DETTAGLIO = {
  desktop: {
    stacco: "16px",
    angolo: "28px",
    dentro: "28px",
    titolo: "30px",
    grande: "64px",
    medio: "40px",
    bottone: "40px",
    griglia: "repeat(12,minmax(0,1fr))",
    otto: "span 8",
    quattro: "span 4",
    testa: "minmax(0,1fr) minmax(0,1.1fr)",
    parti: "repeat(4,minmax(0,1fr))",
    alta: "160px",
    anello: "140px",
  },
  telefono: {
    stacco: "12px",
    angolo: "24px",
    dentro: "20px",
    titolo: "24px",
    grande: "48px",
    medio: "34px",
    bottone: "44px",
    griglia: "minmax(0,1fr)",
    otto: "1 / -1",
    quattro: "1 / -1",
    testa: "minmax(0,1fr)",
    parti: "repeat(2,minmax(0,1fr))",
    alta: "140px",
    anello: "140px",
  },
} as const satisfies Record<Formato, Record<string, string>>

/** Optics and camera in full, "ottica non indicata" for the missing one (board `defC`). */
export function coppiaDelSetup(r: Corredo): string {
  return t("gear.rig.pair", {
    ottica: r.optics ?? t("gear.rig.noOptics"),
    camera: r.camera ?? t("gear.rig.noCamera"),
  })
}

/** The name the detail gives a rig: yours, else optics and camera in full (board `nomeC`). */
export function nomeDelSetup(r: Corredo): string {
  return r.name ?? coppiaDelSetup(r)
}
