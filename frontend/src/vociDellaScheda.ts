import type { components } from "./api/schema"
import { alPiu, numero, t } from "./i18n"

type Pezzo = components["schemas"]["InstrumentOnPage"]

/** One entry of a piece's card: the words, and whether the app derived it ("(calcolato)"). */
export interface Voce {
  v: string
  calc: boolean
}

/**
 * La **scheda di un pezzo in una riga** (tavola v82 `specs`): una voce solo se c'e' il valore, con
 * le parole dell'app. Le voci ricavate (potere risolutore, sensore in mm, pixel dal cielo) le
 * manda gia' fatte l'API in `numbers` e `pixel_from_sky_um`: qui si scrivono e basta.
 */
export function vociDellaScheda(p: Pezzo): Voce[] {
  const voci: Voce[] = []
  const sp = (v: string, calc = false) => voci.push({ v, calc })
  // [T] board `vir`: the value as written, no fixed decimals
  const n = (x: number) => numero(x)
  if (p.optical_design) sp(t(`gear.design.${p.optical_design}`))
  if (p.sensor) sp(t("gear.spec.sensor", { nome: p.sensor }))
  if (p.aperture_mm !== null) sp(t("gear.aperture", { mm: n(p.aperture_mm) }))
  if (p.focal_mm !== null) sp(t("gear.focalNative", { mm: numero(p.focal_mm) }))
  const dawes = p.numbers.dawes?.value
  if (dawes != null) sp(t("gear.spec.resolving", { n: alPiu(dawes, 2) }), true)
  if (p.image_circle_mm !== null) sp(t("gear.spec.circle", { mm: n(p.image_circle_mm) }))
  if (p.required_backfocus_mm !== null) {
    const mm = n(p.required_backfocus_mm)
    const tol = p.backfocus_tolerance_mm
    sp(
      tol === null ? t("gear.backfocus", { mm }) : t("gear.spec.backfocusTol", { mm, tol: n(tol) }),
    )
  }
  if (p.width_px !== null && p.height_px !== null) {
    sp(t("gear.spec.pixels", { larghezza: numero(p.width_px), altezza: numero(p.height_px) }))
  }
  if (p.camera_type) sp(t(p.camera_type === "mono" ? "gear.camera.mono" : "gear.camera.color"))
  if (p.pixel_size_um !== null) sp(t("gear.pixel", { um: n(p.pixel_size_um) }))
  else if (p.pixel_from_sky_um !== null) {
    sp(t("gear.pixel", { um: n(p.pixel_from_sky_um) }), true)
  }
  const sensore = p.numbers.sensor_size
  if (sensore?.width != null && sensore.height != null) {
    const lati = { larghezza: alPiu(sensore.width, 1), altezza: alPiu(sensore.height, 1) }
    sp(t("gear.n.sensor.value", lati), true)
  }
  if (p.adc_bits !== null) sp(t("gear.spec.adc", { n: numero(p.adc_bits) }))
  for (const b of p.biases) {
    if (b.bias_adu === null) continue
    const adu = numero(b.bias_adu)
    sp(
      p.biases.length === 1 || b.offset === null
        ? t("gear.spec.bias", { n: adu })
        : t("gear.spec.biasAt", { n: adu, o: numero(b.offset) }),
    )
  }
  if (p.cooled) {
    sp(
      p.cooling_c === null ? t("gear.spec.cooled") : t("gear.spec.cooledBy", { c: n(p.cooling_c) }),
    )
  }
  if (p.payload_kg !== null) sp(t("gear.spec.payloadCw", { kg: n(p.payload_kg) }))
  if (p.payload_no_cw_kg !== null) sp(t("gear.spec.payloadNoCw", { kg: n(p.payload_no_cw_kg) }))
  if (p.slots !== null) sp(t("gear.slots", { n: numero(p.slots) }))
  if (p.filter_size) {
    const misura = t(`gear.size.${p.filter_size}`)
    sp(p.kind === "filter_wheel" ? t("gear.spec.wheelSize", { misura }) : misura)
  }
  if (p.reducer_factor !== null) {
    const fattore = n(p.reducer_factor)
    sp(t(p.reducer_factor > 1 ? "gear.spec.barlow" : "gear.reducerFactor", { fattore }))
  }
  if (p.step_um !== null) sp(t("gear.spec.step", { um: n(p.step_um) }))
  if (p.total_steps !== null) sp(t("gear.spec.steps", { n: numero(p.total_steps) }))
  if (p.thickness_mm !== null) sp(t("gear.spec.thickness", { mm: n(p.thickness_mm) }))
  if (p.prism_mm !== null) sp(t("gear.spec.prism", { mm: n(p.prism_mm) }))
  if (p.weight_kg !== null) sp(t("gear.weight", { kg: n(p.weight_kg) }))
  return voci
}

/** The first entries of a piece in the rig's card: at most three, never the weight (`chi`, 326). */
export function inBreve(p: Pezzo): string {
  const peso = p.weight_kg === null ? null : t("gear.weight", { kg: alPiu(p.weight_kg, 2) })
  return vociDellaScheda(p)
    .filter((x) => x.v !== peso)
    .slice(0, 3)
    .map((x) => x.v)
    .join(" · ") // glifo-ok: board separator
}
