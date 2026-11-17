import type { components } from "./api/schema"
import type { Chiave } from "./i18n"

/**
 * La **scheda di uno strumento**: i suoi campi e il nome di ogni genere. **Quali campi** chiedere
 * non si decide qui: li manda l'API per genere (`cards`), perche' si scrive anche il primo pezzo di
 * un genere che non possiedi. I moduli che li disegnano sono `ModuloDelPezzo` e `NuovoPezzo`.
 */

export type CampoScheda = components["schemas"]["GearList"]["cards"][string][number]

/** Come si chiama **un** pezzo di ogni genere -- al singolare: e' il nome di una cosa sola, non
 *  del gruppo che la pagina Attrezzatura intitola. Un `Record` sul tipo generato: un genere nuovo
 *  nello schema fa fallire la compilazione invece di sparire in silenzio. */
export const GENERE: Record<components["schemas"]["InstrumentOnPage"]["kind"], Chiave> = {
  optics: "review.kind.optics",
  camera: "review.kind.camera",
  mount: "review.kind.mount",
  reducer: "review.kind.reducer",
  filter_wheel: "review.kind.filter_wheel",
  guide_scope: "review.kind.guide_scope",
  guide_camera: "review.kind.guide_camera",
  focuser: "review.kind.focuser",
  oag: "review.kind.oag",
  spacer: "review.kind.spacer",
}
