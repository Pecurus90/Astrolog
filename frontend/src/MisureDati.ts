/**
 * Le misure dei frame per lo schermo (tavola v76, `componenti/MisureFrame.dc.html`, `MET` e
 * `AMG`): nome e forma di ogni misura. Mediane, quartili, estremi e giudizi arrivano dall'API
 * (`GET /api/v1/nights/{id}/measures`); qui si scrivono e basta.
 */
import type { components } from "./api/schema"
import { varianteDi } from "./FiltriUsati"
import { type Chiave, decimali, numero, t } from "./i18n"

export type Misure = components["schemas"]["NightMeasures"]
export type Insieme = components["schemas"]["MeasureSet"]
export type Statistica = components["schemas"]["MeasureStat"]
export type FrameMisurato = components["schemas"]["MeasuredFrame"]

const intero = (v: number) => numero(Math.round(v))
const gradi = (v: number) => `${intero(v)}\u00B0`
const conSegno = (v: number, d: number) => `${v >= 0.005 ? "+" : ""}${decimali(v, d)}`

/** Come si scrive il valore di ogni misura, dalla tavola (`MET[k].fmt`, `AMG`). */
const FORMATI: Record<string, (v: number) => string> = {
  fwhm_arcsec: (v) => `${decimali(v, 1)}\u2033`,
  hfd_arcsec: (v) => `${decimali(v, 1)}\u2033`,
  fwhm_zenith_arcsec: (v) => `${decimali(v, 1)}\u2033`,
  fwhm_px: (v) => `${decimali(v, 1)} px`,
  hfd_px: (v) => `${decimali(v, 1)} px`,
  stars: intero,
  saturated: intero,
  snr: intero,
  psf_count: intero,
  kept: intero,
  shape_stars: intero,
  trails: intero,
  calibration_stars: intero,
  psf_snr: intero,
  psf_residual_sigma: (v) => decimali(v, 3),
  ceiling_adu: (v) => `${intero(v)} ADU`,
  sky_adu: (v) => `${intero(v)} ADU`,
  angle_deg: gradi,
  angle_pa_deg: gradi,
  gradient_angle_deg: gradi,
  eccentricity: (v) => decimali(v, 2),
  eccentricity_sigma: (v) => decimali(v, 2),
  elongation_coherence: (v) => decimali(v, 2),
  airmass: (v) => decimali(v, 2),
  background_adu: (v) => `${intero(v)} ADU`,
  noise_adu: (v) => `${intero(v)} ADU`,
  median_adu: (v) => `${intero(v)} ADU`,
  psf_flux_adu: intero,
  psf_mean_flux_adu: intero,
  sigma_adu: (v) => `${decimali(v, 1)} ADU`,
  mstar_adu: (v) => `${decimali(v, 1)} ADU`,
  nstar_adu: (v) => `${decimali(v, 1)} ADU`,
  gradient_noise: (v) => `${decimali(v, 1)} ${t("measure.unit.noise")}`,
  row_banding: (v) => `${decimali(v, 2)} ${t("measure.unit.noise")}`,
  column_banding: (v) => `${decimali(v, 2)} ${t("measure.unit.noise")}`,
  hfd_tilt_pct: (v) => `${intero(v)}%`,
  off_axis_px: (v) => `${conSegno(v, 2)} px`,
  off_axis_arcsec: (v) => `${conSegno(v, 1)}\u2033`,
  fwhm_tilt: (v) => decimali(v, 2),
  fwhm_curvature: (v) => decimali(v, 2),
  sqm: (v) => `SQM ${decimali(v, 1)}`,
  psf_residual: (v) => decimali(v, 3),
  fwhm_sigma_px: (v) => `${decimali(v, 2)} px`,
  psf_signal_weight: (v) => decimali(v, 2),
  sky_rate_adu_s: (v) => `${decimali(v, 2)} ADU/s`,
  entropy_bits: (v) => decimali(v, 2),
  noise_ratio: (v) => decimali(v, 3),
  elongation_angle_deg: gradi,
  gradient_pa_deg: gradi,
  azimuth_deg: gradi,
  altitude_deg: gradi,
  moon_altitude_deg: gradi,
  moon_separation_deg: gradi,
  sun_altitude_deg: gradi,
  hour_angle_h: (v) => `${conSegno(v, 1)} h`,
  zero_point_mag: (v) => `${decimali(v, 2)} mag`,
  moon_illumination: (v) => `${intero(v * 100)}%`,
}

/** Il valore di una misura per lo schermo, o la lineetta. */
export function scritto(chiave: string, v: number | null | undefined): string {
  if (v === null || v === undefined) return "\u2014"
  return (FORMATI[chiave] ?? ((x: number) => decimali(x, 2)))(v)
}

/** Una tessera: il suo nome, la misura che la regge e quella in pixel quando c'e' la scala. */
export interface Tessera {
  id: string
  nome: string
  chiave: string
  px?: string
}

// Names: the reference programs' technical terms, untranslated (misure.md).
export const TESSERE: Tessera[] = [
  { id: "fwhm", nome: "FWHM", chiave: "fwhm_arcsec", px: "fwhm_px" },
  { id: "hfd", nome: "HFD", chiave: "hfd_arcsec", px: "hfd_px" },
  { id: "stars", nome: "Stars", chiave: "stars" },
  { id: "eccentricity", nome: "Eccentricity", chiave: "eccentricity" },
  { id: "snr", nome: "SNR", chiave: "snr" },
  { id: "background", nome: "Background", chiave: "background_adu" },
  { id: "noise", nome: "Noise", chiave: "noise_adu" },
  { id: "gradient", nome: "Gradient", chiave: "gradient_noise" },
  { id: "tilt", nome: "Tilt", chiave: "hfd_tilt_pct" },
  { id: "curvature", nome: "Curvature", chiave: "off_axis_px" },
  { id: "sqm", nome: "SQM", chiave: "sqm" },
  { id: "airmass", nome: "Airmass", chiave: "airmass" },
]

// Le misure che dipendono da camera, guadagno e posa (tavola, `perF`, `mixPo`).
export const DAL_SETUP = new Set(["background_adu", "noise_adu"])

/** Le altre misure, a gruppi come la tavola (`AMG`), coi nomi tecnici come le tessere. */
export const ALTRE: { gruppo: Chiave; voci: { chiave: string; nome: string }[] }[] = [
  {
    gruppo: "measure.group.stars_shape",
    voci: [
      { chiave: "kept", nome: "HFD Stars" },
      { chiave: "shape_stars", nome: "Shape Stars" },
      { chiave: "psf_residual", nome: "PSF Residual" },
      { chiave: "psf_residual_sigma", nome: "PSF Residual Sigma" },
      { chiave: "fwhm_sigma_px", nome: "FWHM Sigma" },
      { chiave: "eccentricity_sigma", nome: "Eccentricity Sigma" },
      { chiave: "angle_deg", nome: "Angle" },
      { chiave: "angle_pa_deg", nome: "Angle PA" },
      { chiave: "elongation_angle_deg", nome: "Elongation Angle" },
      { chiave: "elongation_coherence", nome: "Elongation Coherence" },
      { chiave: "saturated", nome: "Saturated" },
    ],
  },
  {
    gruppo: "measure.group.signal",
    voci: [
      { chiave: "psf_snr", nome: "PSF SNR" },
      { chiave: "psf_signal_weight", nome: "PSF Signal Weight" },
      { chiave: "psf_flux_adu", nome: "PSF Flux" },
      { chiave: "psf_mean_flux_adu", nome: "PSF Mean Flux" },
      { chiave: "psf_count", nome: "PSF Count" },
    ],
  },
  {
    gruppo: "measure.group.background",
    voci: [
      { chiave: "sky_rate_adu_s", nome: "Sky Rate" },
      { chiave: "median_adu", nome: "Median" },
      { chiave: "sigma_adu", nome: "Sigma" },
      { chiave: "entropy_bits", nome: "Entropy" },
      { chiave: "noise_ratio", nome: "Noise Ratio" },
      { chiave: "mstar_adu", nome: "M*" },
      { chiave: "nstar_adu", nome: "N*" },
      { chiave: "ceiling_adu", nome: "Saturation Level" },
      { chiave: "row_banding", nome: "Row Banding" },
      { chiave: "column_banding", nome: "Column Banding" },
      { chiave: "gradient_angle_deg", nome: "Gradient Angle" },
      { chiave: "gradient_pa_deg", nome: "Gradient PA" },
      { chiave: "trails", nome: "Trails" },
    ],
  },
  {
    gruppo: "measure.group.sky",
    voci: [
      { chiave: "altitude_deg", nome: "Altitude" },
      { chiave: "azimuth_deg", nome: "Azimuth" },
      { chiave: "hour_angle_h", nome: "Hour Angle" },
      { chiave: "zero_point_mag", nome: "Zero Point" },
      { chiave: "calibration_stars", nome: "Calibration Stars" },
      { chiave: "sky_adu", nome: "Sky ADU" },
    ],
  },
  {
    gruppo: "measure.group.moon_sun",
    voci: [
      { chiave: "moon_altitude_deg", nome: "Moon Altitude" },
      { chiave: "moon_separation_deg", nome: "Moon Separation" },
      { chiave: "moon_illumination", nome: "Moon Illumination" },
      { chiave: "sun_altitude_deg", nome: "Sun Altitude" },
    ],
  },
]

const NOMI = new Map([
  ...TESSERE.map((x) => [x.id, x.nome] as const),
  ...ALTRE.flatMap((g) => g.voci.map((v) => [v.chiave, v.nome] as const)),
])

/** Il nome di una misura, tessera o altra. */
export function nomeDi(id: string): string {
  return NOMI.get(id) ?? id
}

/** La chiave della misura dietro una tessera o un'altra misura. */
export function chiaveDi(id: string): string {
  return TESSERE.find((x) => x.id === id)?.chiave ?? id
}

/** Come `chiaveDi`, ma FWHM e HFD senza scala nell'insieme passano ai pixel (tavola, `noScala`). */
export function chiaveIn(id: string, s: Insieme | undefined): string {
  const tessera = TESSERE.find((x) => x.id === id)
  if (tessera?.px && statistica(s, tessera.chiave)?.median == null) return tessera.px
  return chiaveDi(id)
}

/** L'insieme della notte per oggetto e filtro, `null` = tutti. */
export function insieme(
  m: Misure,
  oggetto: string | null,
  filtro: string | null,
): Insieme | undefined {
  return m.sets.find((s) => s.object_key === oggetto && s.filter === filtro)
}

export function statistica(s: Insieme | undefined, chiave: string): Statistica | undefined {
  return s?.measures.find((x) => x.key === chiave)
}

/** Il primo e il terzo quartile, col trattino lungo fra i due. */
export function quartili(chiave: string, s: Statistica | undefined): string {
  if (!s || s.q1 === null || s.q3 === null) return ""
  return `${scritto(chiave, s.q1)} \u2013 ${scritto(chiave, s.q3)}`
}

/** La riga sotto una tessera, dai 24 punti della notte: un disegno, non un conto (tavola, `spark`). */
export function linea(trend: number[] | null | undefined): string {
  if (!trend || trend.length < 2) return ""
  const basso = Math.min(...trend)
  const alto = Math.max(...trend)
  const r = alto - basso || 1
  const passo = 100 / (trend.length - 1)
  return trend
    .map(
      (b, i) =>
        `${i ? "L" : "M"}${(i * passo).toFixed(1)} ${(27 - ((b - basso) / r) * 24).toFixed(1)}`,
    )
    .join("")
}

/** Dove sta un valore sulla scala comune di *A confronto*, in %. */
export function posizione(v: number, basso: number, alto: number): string {
  return `${(((v - basso) / (alto - basso || 1)) * 100).toFixed(1)}%`
}

/** L'esito di un giudizio del tilt nella pillola. */
export const ESITO: Record<string, 0 | 1 | 2> = { go: 0, marginal: 1, nogo: 2 }

/** L'oggetto e il filtro scelti; `null`: tutti. */
export interface Scelta {
  oggetto: string | null
  filtro: string | null
}

/** I filtri che hanno frame nella scelta di oggetto, nell'ordine dell'app. */
export function filtriDi(m: Misure, oggetto: string | null): Misure["filters"] {
  return m.filters.filter((f) => insieme(m, oggetto, f.name))
}

/** Il colore del filtro, dal token della sua banda. */
export function tintaDi(passband: string | undefined): { fondo: string } {
  const variante = varianteDi(passband).split("--")[1] ?? "ignoto"
  return { fondo: `var(--filtro-${variante})` }
}

/** Cosa cambia fra i frame, a parole: "camera e guadagno". */
export function diversi(differs: Insieme["differs"]): string {
  const parole = differs.map((d) => t(`measures.differs.${d}`))
  if (parole.length < 2) return parole[0] ?? ""
  return t("measures.differs.and", { a: parole.slice(0, -1).join(", "), b: parole.at(-1) ?? "" })
}
