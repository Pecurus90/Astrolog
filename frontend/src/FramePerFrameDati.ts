/**
 * Il disegno di *Frame per frame* (tavola v76, `componenti/MisureFrame.dc.html` 265-305): una
 * barra per frame, la prima misura piena, la seconda tratteggiata con la sua scala. Solo
 * geometria: valori, estremi e mediane arrivano dall'API; qui si mettono sull'asse.
 */
import { decimali, numero } from "./i18n"
import {
  type FrameMisurato,
  type Insieme,
  type Misure,
  type Scelta,
  TESSERE,
  chiaveIn,
  scritto,
  statistica,
} from "./MisureDati"

export const MISURATO = new Set(["measured", "estimated"])

/** I frame della scelta e quello aperto in *Il frame*: lo scelto, o il primo misurato. */
export function frameMostrato(
  misure: Misure,
  scelta: Scelta,
  sel: number | null,
): { vista: FrameMisurato[]; f: FrameMisurato | undefined } {
  const vista = misure.series.filter(
    (f) =>
      (scelta.gruppo === null || f.group === scelta.gruppo) &&
      (scelta.filtro === null || f.filter === scelta.filtro),
  )
  const f =
    vista.find((x) => x.frame_id === sel) ?? vista.find((x) => MISURATO.has(x.state)) ?? vista[0]
  return { vista, f }
}

// FWHM e HFD allo zenit, quando la notte le ha (tavola, "Misurata").
const ZENIT: Record<string, string> = {
  fwhm_arcsec: "fwhm_zenith_arcsec",
  hfd_arcsec: "hfd_zenith_arcsec",
}

/** La colonna della misura nel grafico: con "allo zenit" FWHM e HFD passano alla loro. */
export function chiaveGrafico(id: string, set: Insieme | undefined, zenit: boolean): string {
  const k = chiaveIn(id, set)
  return zenit ? (ZENIT[k] ?? k) : k
}

/** La misura ha il suo valore allo zenit in questo insieme. */
export function haZenit(id: string, set: Insieme | undefined): boolean {
  const z = ZENIT[chiaveIn(id, set)]
  return z !== undefined && statistica(set, z)?.median != null
}

export interface Geometria {
  W: number
  x0: number
  x1: number
  H: number
  top: number
  bot: number
  passo: number // px per barra sotto cui scatta la finestra
}

/** Le misure del disegno, desktop e telefono (tavola 267, 272). */
export function geometria(tel: boolean, due: boolean): Geometria {
  const W = tel ? 360 : 1000
  const margine = tel ? 30 : 44
  const H = tel ? 170 : 220
  return {
    W,
    x0: margine,
    x1: W - (due ? margine : 8),
    H,
    top: 12,
    bot: H - 6,
    passo: tel ? 4 : 5,
  }
}

/** La scala di una misura sui filtri dei grafici: gli estremi dell'API, col 15% d'aria. */
export function scala(insiemi: (Insieme | undefined)[], chiave: string): [number, number] | null {
  const s = insiemi.map((x) => statistica(x, chiave)).filter((x) => x?.low != null)
  if (!s.length) return null
  const lo = Math.min(...s.map((x) => x?.low ?? 0))
  let hi = Math.max(...s.map((x) => x?.high ?? 0))
  const aria = (hi - lo) * 0.15 || 0.5
  hi += aria
  if (chiave === "eccentricity") hi = Math.min(1, hi)
  return [lo >= 0 ? Math.max(0, lo - aria) : lo - aria, hi]
}

const INTERI = new Set(["stars", "snr", "background_adu", "noise_adu", "hfd_tilt_pct"])
const DUE = new Set(["eccentricity", "airmass"])

const DELLE_TESSERE = new Set([
  ...TESSERE.flatMap((x) => [x.chiave, x.px ?? x.chiave]),
  ...Object.values(ZENIT),
])

/** Un numero sull'asse: le tessere senza unita' (tavola `fAx`), le altre misure con la loro. */
export function sullAsse(chiave: string, v: number): string {
  if (!DELLE_TESSERE.has(chiave)) return scritto(chiave, v)
  if (INTERI.has(chiave)) return numero(Math.round(v))
  return decimali(v, DUE.has(chiave) ? 2 : 1)
}

export interface Rettangolo {
  x: string
  y: string
  w: string
  h: string
  r: string
}

export interface Disegno {
  vis: FrameMisurato[]
  inizio: number
  finestra: boolean
  slot: number
  A: (Rettangolo & { stimata: boolean; accesa: boolean })[]
  B: (Rettangolo & { sol: boolean; d: string })[]
  dA: string
  dB: string
  dL: string
  segni: string[]
  sep: string[]
  hx: number | null
  hy: number | null
}

const n1 = (v: number) => v.toFixed(1)

function rettangolo(x: number, y: number, w: number, bot: number): Rettangolo {
  return { x: n1(x - w / 2), y: n1(y), w: n1(w), h: n1(Math.max(w, bot - y)), r: n1(w / 2) }
}

/** Il segno sotto l'asse di un frame senza misure: x poche stelle, cerchietto in corso. */
function segno(f: FrameMisurato, x: number, bot: number): string {
  return f.state === "too_few_stars"
    ? `M${x - 3} ${bot - 8}l6 6m0 -6l-6 6`
    : `M${x - 2} ${bot - 4}a2 2 0 1 0 4 0a2 2 0 1 0 -4 0`
}

export interface Richiesta {
  frames: FrameMisurato[]
  chiavi: string[]
  scale: [number, number][]
  g: Geometria
  inizio: number
  linee: boolean
  luna: boolean
  acceso: number | null
}

/** Barre, linee e segni dei frame in vista: oltre `passo` px per barra, una finestra. */
export function disegno(q: Richiesta): Disegno {
  const { g, chiavi, scale } = q
  const max = Math.floor((g.x1 - g.x0) / g.passo)
  const finestra = q.frames.length > max
  const inizio = finestra ? Math.max(0, Math.min(q.frames.length - max, q.inizio)) : 0
  const vis = finestra ? q.frames.slice(inizio, inizio + max) : q.frames
  const slot = (g.x1 - g.x0) / Math.max(1, vis.length)
  const bw = Math.max(1.5, Math.min(14, slot * 0.6))
  const ys = scale.map(
    ([lo, hi]) =>
      (v: number) =>
        g.bot - ((v - lo) / (hi - lo || 1)) * (g.bot - g.top),
  )
  const out: Disegno = {
    vis,
    inizio,
    finestra,
    slot,
    A: [],
    B: [],
    dA: "",
    dB: "",
    dL: "",
    segni: [],
    sep: [],
    hx: null,
    hy: null,
  }
  let lunaPrima = false
  vis.forEach((f, i) => {
    const x = g.x0 + slot * (i + 0.5)
    if (i && vis[i - 1]?.group !== f.group) out.sep.push(n1(g.x0 + slot * i))
    const lu = f.values.moon_altitude_deg
    // sotto l'orizzonte sull'asse, come la tavola (157); senza altezza la linea si interrompe
    if (q.luna && lu !== undefined) {
      const y = g.bot - (Math.max(0, lu) / 90) * (g.bot - g.top)
      out.dL += `${lunaPrima ? "L" : "M"}${n1(x)} ${n1(y)}`
    }
    lunaPrima = lu !== undefined
    if (!MISURATO.has(f.state)) {
      out.segni.push(segno(f, x, g.bot))
      return
    }
    const va = f.values[chiavi[0] ?? ""]
    const ya0 = ys[0]
    if (va === undefined || !ya0) return
    const ya = ya0(va)
    const acceso = f.frame_id === q.acceso
    if (acceso) [out.hx, out.hy] = [x, ya]
    if (!q.linee)
      out.A.push({
        ...rettangolo(x, ya, bw, g.bot),
        stimata: f.state === "estimated",
        accesa: acceso,
      })
    out.dA += `${out.dA ? "L" : "M"}${n1(x)} ${n1(ya)}`
    const vb = chiavi[1] === undefined ? undefined : f.values[chiavi[1]]
    const yb0 = ys[1]
    if (vb === undefined || !yb0) return
    const yb = yb0(vb)
    const w2 = bw + 1.5
    if (!q.linee)
      out.B.push({
        ...rettangolo(x, yb, w2, g.bot),
        sol: bw < 5,
        d: `M${n1(x - w2 / 2 - 1)} ${n1(yb)}H${n1(x + w2 / 2 + 1)}`,
      })
    out.dB += `${out.dB ? "L" : "M"}${n1(x)} ${n1(yb)}`
  })
  return out
}

/** La striscia di tutti i frame sotto la finestra: una riga per frame misurato, 0-100 per 0-24. */
export function striscia(frames: FrameMisurato[], chiave: string, s: [number, number]): string {
  const n = frames.length
  return frames
    .map((f, i) => {
      const v = MISURATO.has(f.state) ? f.values[chiave] : undefined
      if (v === undefined) return ""
      const y = 22 - ((v - s[0]) / (s[1] - s[0] || 1)) * 20
      return `M${((i / n) * 100).toFixed(2)} 22V${y.toFixed(1)}`
    })
    .join("")
}

/** Dove sta x sul disegno, in % della larghezza. */
export const pc = (v: number, d: number): string => `${((v / d) * 100).toFixed(2)}%`
