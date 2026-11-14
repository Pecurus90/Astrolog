/**
 * Il treno ottico di un setup (tavola v82, `treno` 447-548): esploso in vista isometrica, a linee,
 * in millimetri, le linee nascoste coperte dal fondo. Schema non in scala.
 *
 * Non e' derivazione di dati: quali pezzi porta il setup lo dice il backend (`pieces`);
 * qui i loro numeri diventano tracciati SVG, come in `disegnoDellaLuna.ts`.
 */

export type Ruolo =
  | "optics"
  | "focuser"
  | "reducer"
  | "oag"
  | "spacer"
  | "filter_wheel"
  | "camera"
  | "guide_scope"
  | "guide_camera"

/** Un pezzo del treno con i campi della scheda che il disegno legge; `null` se non scritti. */
export interface Pezzo {
  id: number
  nome: string
  ruolo: Ruolo
  schema?: string | null
  apertura?: number | null
  focale?: number | null
  spessore?: number | null
  posizioni?: number | null
  aColori?: boolean
}

export interface Treno {
  ott: Pezzo
  foc?: Pezzo | undefined
  rid?: Pezzo | undefined
  oag?: Pezzo | undefined
  dist: Pezzo[]
  ruota?: Pezzo | undefined
  cam?: Pezzo | undefined
  gs?: Pezzo | undefined
  camG?: Pezzo | undefined
}

export interface Tratto {
  d: string
  pieno: boolean
  opacita: number
}

export interface Gruppo {
  pezzo: Pezzo
  tratti: Tratto[]
  profondita: number
  riquadro: [number, number, number, number]
}

export interface Etichetta {
  pezzo: Pezzo
  numero: number
  su: boolean
  /** Centro del pezzo, dove parte il filo; `x` dove sta la pillola, spinta di lato. */
  cx: number
  x: number
  larghezza: number
  filo: string
  punto: [number, number]
}

export interface Disegno {
  vista: { x: number; y: number; w: number; h: number }
  asse: string
  /** Dal fondo al davanti: chi viene dopo copre chi viene prima. */
  gruppi: Gruppo[]
  su: Etichetta[]
  giu: Etichetta[]
  /** Nell'ordine dei numeri della legenda del telefono. */
  legenda: Etichetta[]
  /** La larghezza massima del disegno, alto 400 px (300 sul telefono). */
  larghezzaMassima: number
  /** Pillole col numero e legenda: sul telefono, o quando i nomi di una riga non entrano. */
  coiNumeri: boolean
}

type Punto = [number, number]

const C = 0.70711
const Q = 0.40825
const N = 56
const E = 30 // mm between two pieces, along the axis
const PI = Math.PI
const ALTO: readonly Ruolo[] = ["focuser", "guide_scope", "guide_camera"]

const P = (x: number, y: number, z: number): Punto => [(x + z) * C, -(x + 2 * y - z) * Q]

const tracciato = (pts: Punto[], chiuso = false) =>
  pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join("") +
  (chiuso ? "Z" : "")

function inviluppo(pts: Punto[]): Punto[] {
  const p = pts.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1])
  const cr = (k: Punto, a: Punto, b: Punto) =>
    (a[0] - k[0]) * (b[1] - k[1]) - (a[1] - k[1]) * (b[0] - k[0])
  const lo: Punto[] = []
  const up: Punto[] = []
  for (const q of p) {
    while (lo.length >= 2 && cr(lo[lo.length - 2]!, lo[lo.length - 1]!, q) <= 0) lo.pop()
    lo.push(q)
  }
  for (let i = p.length - 1; i >= 0; i--) {
    const q = p[i]!
    while (up.length >= 2 && cr(up[up.length - 2]!, up[up.length - 1]!, q) <= 0) up.pop()
    up.push(q)
  }
  return lo.slice(0, -1).concat(up.slice(0, -1))
}

type Asse = "x" | "y"

/** Il quaderno del disegno: gruppi, tratti e ingombri, come le funzioni della tavola. */
class Quaderno {
  gruppi: Gruppo[] = []
  B: [number, number, number, number] = [1e9, 1e9, -1e9, -1e9]
  private g: Gruppo | null = null

  grp(pezzo: Pezzo, x: number, y: number, z: number) {
    this.g = { pezzo, tratti: [], profondita: -x + y + z, riquadro: [1e9, 1e9, -1e9, -1e9] }
    this.gruppi.push(this.g)
  }

  private bb(pts: Punto[]) {
    const g = this.g!
    for (const [u, v] of pts) {
      this.B = [
        Math.min(this.B[0], u),
        Math.min(this.B[1], v),
        Math.max(this.B[2], u),
        Math.max(this.B[3], v),
      ]
      g.riquadro = [
        Math.min(g.riquadro[0], u),
        Math.min(g.riquadro[1], v),
        Math.max(g.riquadro[2], u),
        Math.max(g.riquadro[3], v),
      ]
    }
  }

  add(d: string, pieno: boolean, opacita = 1) {
    this.g!.tratti.push({ d, pieno, opacita })
  }

  private pt(ax: Asse, s: number, a: number, b: number, c: Punto): Punto {
    return ax === "x" ? P(s, c[0] + a, c[1] + b) : P(c[0] + a, s, c[1] + b)
  }

  private anello(ax: Asse, s: number, r: number, c: Punto): Punto[] {
    const out: Punto[] = []
    for (let i = 0; i <= N; i++) {
      const a = (i / N) * PI * 2
      out.push(this.pt(ax, s, r * Math.cos(a), r * Math.sin(a), c))
    }
    return out
  }

  // the visible half of a ring on the surface: its normal looks at the viewer, d = (-1, 1, 1)
  arco(ax: Asse, s: number, r: number, c: Punto, op = 0.55) {
    const a0 = ax === "x" ? -PI / 4 : PI / 4
    const out: Punto[] = []
    for (let i = 0; i <= N / 2; i++) {
      const a = a0 + (i / (N / 2)) * PI
      out.push(this.pt(ax, s, r * Math.cos(a), r * Math.sin(a), c))
    }
    this.add(tracciato(out), false, op)
  }

  cyl(ax: Asse, s0: number, len: number, r: number, c: Punto = [0, 0]) {
    const e0 = this.anello(ax, s0, r, c)
    const e1 = this.anello(ax, s0 + len, r, c)
    this.add(tracciato(inviluppo(e0.concat(e1)), true), true)
    this.add(tracciato(ax === "x" ? e0 : e1, true), false)
    this.bb(e0.concat(e1))
  }

  faccia(ax: Asse, s: number, r: number, c: Punto, op = 0.6) {
    this.add(tracciato(this.anello(ax, s, r, c), true), false, op)
  }

  box(x: number, y: number, z: number, dx: number, dy: number, dz: number) {
    const p = (a: number, b: number, k: number) => P(x + a * dx, y + b * dy, z + k * dz)
    const f: Punto[][] = [
      [p(0, 0, 0), p(0, 1, 0), p(0, 1, 1), p(0, 0, 1)],
      [p(0, 1, 0), p(1, 1, 0), p(1, 1, 1), p(0, 1, 1)],
      [p(0, 0, 1), p(0, 1, 1), p(1, 1, 1), p(1, 0, 1)],
    ]
    f.forEach((q) => this.add(tracciato(q, true), true))
    this.bb(f.flat())
  }
}

/** I pezzi nell'ordine dei numeri (tavola `pezziTreno`, 446). */
export function pezziDelTreno(T: Treno): Pezzo[] {
  return [T.ott, T.foc, T.rid, T.oag, ...T.dist, T.ruota, T.cam, T.gs, T.camG].filter(
    (p): p is Pezzo => p !== undefined,
  )
}

interface Voce {
  q: Pezzo
  len: number
  r: number
  rid?: boolean
  oag?: boolean
  cam?: boolean
  off?: number
}

interface Ottica {
  L: number
  R: number
  rf: number
  dew: number
  Lt: number
  xf: number
  SC: boolean
  NW: boolean
}

// optics, from the back to the front; unknown design draws as a refractor (board default)
function ottica(K: Quaderno, ott: Pezzo): Ottica {
  const sch = ott.schema ?? ""
  const SC = sch === "sct" || sch === "maksutov"
  const RC = sch === "rc"
  const NW = sch === "newtonian"
  const rifrattore = !SC && !RC && !NW
  const ap = ott.apertura || 80
  const fo = ott.focale || 500
  const R = (ap + (SC ? 26 : 22)) / 2
  const L = SC ? ap * 2.1 : NW ? fo * 0.92 : RC ? ap * 2.2 : fo * 0.78
  const rf = ap > 80 ? 32 : 26
  const dew = rifrattore ? Math.min(ap * 1.3, L * 0.32) : 0
  const Lt = L - dew
  K.grp(ott, L / 2, 0, 0)
  K.box(dew + Lt * 0.15, -R - 16, -16, Lt * 0.7, 10, 32)
  let xf: number
  if (SC) {
    K.cyl("x", L + 40, 30, 30)
    K.cyl("x", L, 40, R * 0.86)
    xf = L + 70
  } else if (NW) xf = 0
  else {
    K.cyl("x", dew + Lt + 70, 36, rf - 6)
    K.cyl("x", dew + Lt, 70, rf)
    K.arco("x", dew + Lt + 70 + 12, rf - 6, [0, 0], 0.4)
    xf = dew + Lt + 106
  }
  K.cyl("x", dew, Lt, R)
  for (const f of [0.28, 0.66]) {
    const x = dew + Lt * f
    K.box(x, -R - 6, -7, 14, 6, 14)
    K.arco("x", x, R + 3, [0, 0], 0.9)
    K.arco("x", x + 14, R + 3, [0, 0], 0.9)
  }
  const fr = dew ? R + 6 : R
  if (dew) K.cyl("x", 0, dew, fr)
  K.faccia("x", 0, fr * 0.84, [0, 0])
  if (!SC && !NW) K.faccia("x", 0, fr * 0.7, [0, 0], 0.35)
  if (!rifrattore) K.faccia("x", 0, fr * 0.3, [0, 0], 0.9)
  if (NW || RC) {
    K.add(tracciato([P(0, fr * 0.84, 0), P(0, -fr * 0.84, 0)]), false, 0.6)
    K.add(tracciato([P(0, 0, fr * 0.84), P(0, 0, -fr * 0.84)]), false, 0.6)
  }
  if (NW) K.cyl("y", R - 4, 60, rf, [L * 0.16, 0])
  return { L, R, rf, dew, Lt, xf, SC, NW }
}

function voci(T: Treno, SC: boolean): Voce[] {
  const v: Voce[] = []
  if (T.rid) v.push({ q: T.rid, len: 40, r: SC ? 50 : 36, rid: true })
  if (T.oag) v.push({ q: T.oag, len: Math.max(12, T.oag.spessore || 16), r: 45, oag: true })
  for (const q of T.dist) v.push({ q, len: Math.max(4, q.spessore || 5), r: 30 })
  if (T.ruota) {
    const rw = (T.ruota.posizioni || 7) > 5 ? 92 : 80
    v.push({ q: T.ruota, len: Math.max(16, T.ruota.spessore || 20), r: rw, off: rw - 52 })
  }
  if (T.cam) v.push({ q: T.cam, len: 100, r: T.cam.aColori ? 39 : 45, cam: true })
  return v
}

type CameraDellOag = { x: number; y: number; lato?: boolean } | null

// the train in exploded view, along the axis; a Newtonian's goes up from its focuser
function esploso(K: Quaderno, items: Voce[], o: Ottica): CameraDellOag {
  let oagCam: CameraDellOag = null
  if (!o.NW) {
    let x = o.xf + E
    for (const it of items) {
      K.grp(it.q, x + it.len / 2, it.off || 0, 0)
      if (it.cam) {
        const k = it.len * 0.42
        K.cyl("x", x + k, it.len - k, it.r - 2)
        for (let d = k + 8; d < it.len - 4; d += 7) K.arco("x", x + d, it.r - 2, [0, 0], 0.45)
        K.cyl("x", x, k, it.r)
        K.faccia("x", x, it.r * 0.45, [0, 0], 0.4)
      } else if (it.oag) {
        K.cyl("y", it.r - 6, 62, 11, [x + it.len / 2, 0])
        K.cyl("x", x, it.len, it.r)
        K.faccia("x", x, it.r * 0.55, [0, 0], 0.4)
        oagCam = { x: x + it.len / 2, y: it.r + 62 + 22 }
      } else {
        K.cyl("x", x, it.len, it.r, [it.off || 0, 0])
        if (it.rid) for (const d of [12, 20, 28]) K.arco("x", x + d, it.r, [0, 0], 0.4)
        if (it.off) K.faccia("x", x, 18, [0, 0], 0.4)
      }
      x += it.len + E
    }
    return oagCam
  }
  let y = o.R + 56 + E
  const fx = o.L * 0.16
  for (const it of items) {
    K.grp(it.q, fx, y + it.len / 2, 0)
    if (it.oag) {
      K.cyl("x", fx - it.r - 56, 62, 11, [y + it.len / 2, 0])
      K.cyl("y", y, it.len, it.r, [fx, 0])
      oagCam = { x: fx - it.r - 62 - 22 - 44, y: y + it.len / 2, lato: true }
    } else K.cyl("y", y, it.len, it.r, [fx + (it.off || 0), 0])
    y += it.len + E
  }
  return oagCam
}

// focuser, guide scope on top with its camera, or the guide camera on the OAG's prism
function sopra(K: Quaderno, T: Treno, o: Ottica, oagCam: CameraDellOag) {
  const { L, R, rf, dew, Lt, SC, NW } = o
  if (T.foc) {
    const m = SC ? [L + 4, R * 0.86] : NW ? [L * 0.16 + rf + 6, R + 6] : [dew + Lt + 12, rf]
    K.grp(T.foc, m[0]! + 25, m[1]! + 30, 0)
    K.box(m[0]!, m[1]! + 10, -22, 48, 40, 44)
  }
  if (T.gs) {
    const rg = ((T.gs.apertura || 30) + 12) / 2
    const lg = (T.gs.focale || 120) * 1.15
    const xg = dew + Lt * 0.4
    const yg = R + 30 + rg
    if (T.camG) {
      K.grp(T.camG, xg + lg + E + 22, yg, 0)
      K.cyl("x", xg + lg + E, 44, 18, [yg, 0])
    }
    K.grp(T.gs, xg + lg / 2, yg, 0)
    for (const f of [0.18, 0.68]) K.box(xg + lg * f, R + 2, -6, 12, yg - rg - R, 12)
    K.cyl("x", xg, lg, rg, [yg, 0])
    for (const f of [0.18, 0.68]) {
      const x = xg + lg * f
      K.arco("x", x, rg + 2, [yg, 0], 0.9)
      K.arco("x", x + 12, rg + 2, [yg, 0], 0.9)
    }
    K.faccia("x", xg, rg * 0.8, [yg, 0])
  } else if (T.camG && oagCam) {
    K.grp(T.camG, oagCam.x, oagCam.y, 0)
    if (oagCam.lato) K.cyl("x", oagCam.x, 44, 18, [oagCam.y, 0])
    else K.cyl("y", oagCam.y, 44, 18, [oagCam.x, 0])
  }
}

/** La pillola larga quanto il nome, in unita' del disegno; sul telefono il solo numero. */
const PILLOLA_PX = (nome: string, telefono: boolean) => (telefono ? 30 : nome.length * 7.9 + 30)

// labels side by side, never touching: pushed right, then back left from the drawing's edge
function spingi(arr: Etichetta[], maxX: number, sc: number) {
  for (let i = 1; i < arr.length; i++) {
    arr[i]!.x = Math.max(
      arr[i]!.cx,
      arr[i - 1]!.x + (arr[i - 1]!.larghezza + arr[i]!.larghezza) / 2 + 6 * sc,
    )
  }
  const ultima = arr[arr.length - 1]
  const over = ultima ? ultima.x + ultima.larghezza / 2 - maxX : 0
  if (over > 0) {
    ultima!.x -= over
    for (let i = arr.length - 2; i >= 0; i--) {
      arr[i]!.x = Math.min(
        arr[i]!.x,
        arr[i + 1]!.x - (arr[i]!.larghezza + arr[i + 1]!.larghezza) / 2 - 6 * sc,
      )
    }
  }
}

function etichette(
  T: Treno,
  K: Quaderno,
  vy: number,
  H: number,
  larghezzaPx: number,
  coiNumeri: boolean,
) {
  const B = K.B
  const numeri = new Map(pezziDelTreno(T).map((q, k) => [q.id, k + 1]))
  const sc = (B[2] - B[0] + 48) / larghezzaPx
  let alterna = 0
  const tutte: Etichetta[] = K.gruppi
    .map((g) => ({ g, cx: (g.riquadro[0] + g.riquadro[2]) / 2 }))
    .sort((a, b) => a.cx - b.cx)
    .map(({ g, cx }) => {
      const su = ALTO.includes(g.pezzo.ruolo) ? true : alterna++ % 2 === 1
      const ay = su ? g.riquadro[1] : g.riquadro[3]
      return {
        pezzo: g.pezzo,
        numero: numeri.get(g.pezzo.id) ?? 0,
        su,
        cx,
        x: cx,
        larghezza: PILLOLA_PX(g.pezzo.nome, coiNumeri) * sc,
        filo: "",
        punto: [cx, ay] as Punto,
      }
    })
  const su = tutte.filter((l) => l.su)
  const giu = tutte.filter((l) => !l.su)
  for (const a of [su, giu]) spingi(a, B[2] + 24, sc)
  for (const l of tutte) {
    const ay = l.punto[1]
    const ey = l.su ? vy : vy + H
    l.filo = `M${l.cx} ${ay}L${l.cx} ${l.su ? ay - 14 : ay + 14}L${l.x} ${ey}`
  }
  return { su, giu, legenda: tutte.slice().sort((a, b) => a.numero - b.numero) }
}

// names that don't fit in a row push the first pill out of the box on the left (Marco, 14/11)
const entrano = (pillole: Etichetta[], sinistra: number) =>
  pillole.every((l) => l.x - l.larghezza / 2 >= sinistra)

/**
 * Il disegno del treno. `larghezzaPx` e' quella misurata del riquadro (tavola `trW`): le pillole
 * si spingono di lato in pixel veri; senza misura vale 800 (330 sul telefono).
 */
export function disegnoDelTreno(
  T: Treno,
  larghezzaPx: number | undefined,
  telefono: boolean,
): Disegno {
  const K = new Quaderno()
  const o = ottica(K, T.ott)
  const items = voci(T, o.SC)
  const oagCam = esploso(K, items, o)
  sopra(K, T, o, oagCam)
  const fine = o.NW ? o.L : o.xf + items.reduce((s, it) => s + it.len + E, 0)
  const asse = tracciato([P(-40, 0, 0), P(fine + 60, 0, 0)])
  const B = K.B
  const pad = 24
  const padV = 46
  const w = B[2] - B[0] + pad * 2
  const h = B[3] - B[1] + padV * 2
  const vista = { x: B[0] - pad, y: B[1] - padV, w, h }
  const px = larghezzaPx || (telefono ? 330 : 800)
  let coiNumeri = telefono
  let pillole = etichette(T, K, vista.y, h, px, coiNumeri)
  if (!coiNumeri && !entrano([...pillole.su, ...pillole.giu], vista.x)) {
    coiNumeri = true
    pillole = etichette(T, K, vista.y, h, px, coiNumeri)
  }
  const { su, giu, legenda } = pillole
  const gruppi = K.gruppi.slice().sort((a, b) => a.profondita - b.profondita)
  const larghezzaMassima = Math.round(((telefono ? 300 : 400) * w) / h)
  return { vista, asse, gruppi, su, giu, legenda, larghezzaMassima, coiNumeri }
}
