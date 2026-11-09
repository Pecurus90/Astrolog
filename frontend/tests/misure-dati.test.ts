/**
 * Le misure dei frame in parole e in geometria (`src/MisureDati.ts`, `src/FramePerFrameDati.ts`):
 * ogni formato, ogni scala e ogni barra di *Frame per frame* al decimale, come la tavola v76.
 */
import { describe, expect, it } from "vitest"

import {
  type Richiesta,
  chiaveGrafico,
  disegno,
  frameMostrato,
  geometria,
  haZenit,
  pc,
  scala,
  striscia,
  sullAsse,
} from "../src/FramePerFrameDati"
import { t } from "../src/i18n"
import {
  type FrameMisurato,
  type Insieme,
  type Misure,
  type Statistica,
  chiaveDi,
  chiaveIn,
  diversi,
  filtriDi,
  insieme,
  linea,
  medianeInTesta,
  nomeDelGruppo,
  nomeDi,
  posizione,
  quartili,
  scritto,
  tintaDi,
} from "../src/MisureDati"

const stat = (key: string, extra: Partial<Statistica> = {}): Statistica =>
  ({
    key,
    unit: "px",
    group: "stars_shape",
    measured: 2,
    median: null,
    q1: null,
    q3: null,
    low: null,
    high: null,
    trend: null,
    verdict: null,
    silent: null,
    ...extra,
  }) as Statistica

const set = (measures: Statistica[], group: string | null = null, filter: string | null = null) =>
  ({ group, filter, frames: 2, pending: 0, differs: [], measures }) as unknown as Insieme

const frame = (
  frame_id: number,
  state: string,
  values: Record<string, number>,
  group: string | null = "a",
  filter: string | null = "Ha",
) =>
  ({
    frame_id,
    start: "2024-05-18T23:00:00+02:00",
    group,
    filter,
    state,
    tilt_level: null,
    sampling: null,
    angle_axis: null,
    values,
  }) as FrameMisurato

const RUMORE = t("measure.unit.noise")

describe("ogni misura si scrive come la tavola", () => {
  const V = 12.3456
  const ATTESI: Record<string, string> = {
    fwhm_arcsec: "12,3″",
    hfd_arcsec: "12,3″",
    fwhm_zenith_arcsec: "12,3″",
    fwhm_px: "12,3 px",
    hfd_px: "12,3 px",
    stars: "12",
    saturated: "12",
    snr: "12",
    psf_count: "12",
    kept: "12",
    shape_stars: "12",
    trails: "12",
    calibration_stars: "12",
    psf_snr: "12",
    psf_residual_sigma: "12,346",
    ceiling_adu: "12 ADU",
    sky_adu: "12 ADU",
    angle_deg: "12°",
    angle_pa_deg: "12°",
    gradient_angle_deg: "12°",
    eccentricity: "12,35",
    eccentricity_sigma: "12,35",
    elongation_coherence: "12,35",
    airmass: "12,35",
    background_adu: "12 ADU",
    noise_adu: "12 ADU",
    median_adu: "12 ADU",
    psf_flux_adu: "12",
    psf_mean_flux_adu: "12",
    sigma_adu: "12,3 ADU",
    mstar_adu: "12,3 ADU",
    nstar_adu: "12,3 ADU",
    gradient_noise: `12,3 ${RUMORE}`,
    row_banding: `12,35 ${RUMORE}`,
    column_banding: `12,35 ${RUMORE}`,
    hfd_tilt_pct: "12%",
    off_axis_px: "+12,35 px",
    off_axis_arcsec: "+12,3″",
    fwhm_tilt: "12,35",
    fwhm_curvature: "12,35",
    sqm: "SQM 12,3",
    psf_residual: "12,346",
    fwhm_sigma_px: "12,35 px",
    psf_signal_weight: "12,35",
    sky_rate_adu_s: "12,35 ADU/s",
    entropy_bits: "12,35",
    noise_ratio: "12,346",
    elongation_angle_deg: "12°",
    gradient_pa_deg: "12°",
    azimuth_deg: "12°",
    altitude_deg: "12°",
    moon_altitude_deg: "12°",
    moon_separation_deg: "12°",
    sun_altitude_deg: "12°",
    hour_angle_h: "+12,3 h",
    zero_point_mag: "12,35 mag",
    sconosciuta: "12,35",
  }

  it.each(Object.entries(ATTESI))("%s", (chiave, atteso) => {
    expect(scritto(chiave, V)).toBe(atteso)
  })

  it("l'illuminazione della Luna da frazione a percento, senza valore la lineetta", () => {
    expect(scritto("moon_illumination", 0.456)).toBe("46%")
    expect(scritto("snr", null)).toBe("—")
    expect(scritto("snr", undefined)).toBe("—")
  })

  it("il segno piu' solo da mezzo centesimo in su; i negativi col loro meno", () => {
    expect(scritto("off_axis_px", 0.004)).toBe("0,00 px")
    expect(scritto("off_axis_px", 0)).toBe("0,00 px")
    expect(scritto("hour_angle_h", -1.24)).toBe("−1,2 h")
  })
})

describe("nomi, chiavi e insiemi", () => {
  const ARC = set([stat("fwhm_arcsec", { median: 2 }), stat("fwhm_zenith_arcsec", { median: 1.8 })])
  const PX = set([stat("fwhm_px", { median: 1.2 }), stat("hfd_zenith_arcsec", { median: null })])

  it("il nome tecnico di tessere e altre misure, la chiave quando non ce l'ha", () => {
    expect(nomeDi("fwhm")).toBe("FWHM")
    expect(nomeDi("kept")).toBe("HFD Stars")
    expect(nomeDi("ignota")).toBe("ignota")
    expect(chiaveDi("tilt")).toBe("hfd_tilt_pct")
    expect(chiaveDi("kept")).toBe("kept")
  })

  it("FWHM e HFD senza scala nell'insieme passano ai pixel", () => {
    expect(chiaveIn("fwhm", ARC)).toBe("fwhm_arcsec")
    expect(chiaveIn("fwhm", PX)).toBe("fwhm_px")
    expect(chiaveIn("hfd", undefined)).toBe("hfd_px")
    expect(chiaveIn("snr", PX)).toBe("snr")
  })

  it("allo zenit FWHM e HFD cambiano colonna, solo se l'insieme ha la mediana", () => {
    expect(chiaveGrafico("fwhm", ARC, false)).toBe("fwhm_arcsec")
    expect(chiaveGrafico("fwhm", ARC, true)).toBe("fwhm_zenith_arcsec")
    expect(chiaveGrafico("fwhm", PX, true)).toBe("fwhm_px")
    expect(chiaveGrafico("snr", ARC, true)).toBe("snr")
    expect(chiaveGrafico("hfd", set([stat("hfd_arcsec", { median: 3 })]), true)).toBe(
      "hfd_zenith_arcsec",
    )
    expect(haZenit("fwhm", ARC)).toBe(true)
    expect(haZenit("fwhm", PX)).toBe(false)
    expect(
      haZenit("hfd", set([stat("hfd_arcsec", { median: 3 }), stat("hfd_zenith_arcsec")])),
    ).toBe(false)
    expect(haZenit("snr", ARC)).toBe(false)
  })

  const MISURE = {
    night_id: 7,
    timezone: "Europe/Rome",
    frames: 2,
    pending: 0,
    groups: [],
    filters: [
      { name: "Ha", passband: "HA", frames: 2 },
      { name: "OIII", passband: "OIII", frames: 1 },
    ],
    sets: [set([], null, null), set([], "a", "Ha"), set([], null, "Ha"), set([], null, "OIII")],
    series: [],
  } as unknown as Misure

  it("l'insieme per gruppo e filtro, e i filtri che il gruppo ha", () => {
    expect(insieme(MISURE, "a", "Ha")?.group).toBe("a")
    expect(insieme(MISURE, "a", null)).toBeUndefined()
    expect(filtriDi(MISURE, "a").map((f) => f.name)).toEqual(["Ha"])
    expect(filtriDi(MISURE, null).map((f) => f.name)).toEqual(["Ha", "OIII"])
  })

  it("il gruppo si chiama col nome, poi con la data della notte, poi con la chiave", () => {
    const g = { key: "m-51", name: "M 51", night_date: null, frames: 1, pending: 0 }
    expect(nomeDelGruppo(g)).toBe("M 51")
    expect(nomeDelGruppo({ ...g, name: null, night_date: "2026-09-16" })).toBe(
      "Mercoledì 16 settembre",
    )
    expect(nomeDelGruppo({ ...g, name: null })).toBe("m-51")
  })

  it("il colore del filtro dal token della sua banda, ignoto senza banda", () => {
    expect(tintaDi("HA").fondo).toBe("var(--filtro-ha)")
    expect(tintaDi(undefined).fondo).toBe("var(--filtro-ignoto)")
  })

  it("cosa cambia fra i frame, a parole", () => {
    expect(diversi([])).toBe("")
    expect(diversi(["camera"])).toBe("camera")
    expect(diversi(["camera", "gain"])).toBe("camera e guadagno")
    expect(diversi(["camera", "gain", "exposure"])).toBe("camera, guadagno e tempo di posa")
  })
})

describe("quartili, linee e posizioni", () => {
  it("i quartili col trattino lungo, niente senza uno dei due", () => {
    expect(quartili("fwhm_px", stat("fwhm_px", { q1: 1.1, q3: 1.3 }))).toBe("1,1 px – 1,3 px")
    expect(quartili("fwhm_px", stat("fwhm_px", { q1: null, q3: 1.3 }))).toBe("")
    expect(quartili("fwhm_px", stat("fwhm_px", { q1: 1.1, q3: null }))).toBe("")
    expect(quartili("fwhm_px", undefined)).toBe("")
  })

  it("la riga sotto la tessera dai punti della notte", () => {
    expect(linea(null)).toBe("")
    expect(linea([1])).toBe("")
    expect(linea([0, 10, 5])).toBe("M0.0 27.0L50.0 3.0L100.0 15.0")
    expect(linea([2, 2])).toBe("M0.0 27.0L100.0 27.0")
  })

  it("dove sta un valore sulla scala comune", () => {
    expect(posizione(5, 0, 10)).toBe("50.0%")
    expect(posizione(7, 2, 12)).toBe("50.0%")
    expect(posizione(5, 5, 5)).toBe("0.0%")
  })
})

describe("FWHM e SNR in testa", () => {
  const notte = (measures: Statistica[], extra: Record<string, unknown> = {}) =>
    ({ sets: [set(measures)], ...extra }) as unknown as Misure

  it("i puntini finche' le misure non arrivano", () => {
    expect(medianeInTesta(undefined)).toEqual([
      { v: "…", l: t("window.fwhm") },
      { v: "…", l: t("window.snr") },
    ])
  })

  it("la FWHM in secondi d'arco, in pixel solo senza scala", () => {
    const arc = notte([stat("fwhm_arcsec", { median: 2.44 }), stat("snr", { median: 35.6 })])
    expect(medianeInTesta(arc).map((x) => x.v)).toEqual(["2,4″", "36"])
    const px = notte([stat("fwhm_px", { median: 1.24 })])
    expect(medianeInTesta(px).map((x) => x.v)).toEqual(["1,2 px", "—"])
  })

  it("con piu' produzioni insieme ne' l'SNR ne' i pixel", () => {
    const misto = notte([stat("fwhm_px", { median: 1.24 }), stat("snr", { median: 30 })], {
      one_production: false,
    })
    expect(medianeInTesta(misto)).toEqual([{ v: "—", l: t("window.fwhm") }])
    const una = notte([stat("snr", { median: 30 })], { one_production: true })
    expect(medianeInTesta(una).map((x) => x.v)).toEqual(["—", "30"])
  })
})

describe("il frame mostrato", () => {
  const SERIE = [
    frame(1, "too_few_stars", {}, "a", "Ha"),
    frame(2, "measured", {}, "a", "OIII"),
    frame(3, "estimated", {}, "b", "Ha"),
  ]
  const m = { series: SERIE } as unknown as Misure
  const ids = (x: { vista: FrameMisurato[] }) => x.vista.map((f) => f.frame_id)

  it("lo scelto, o il primo misurato, o il primo", () => {
    expect(frameMostrato(m, { gruppo: null, filtro: null }, null).f?.frame_id).toBe(2)
    expect(frameMostrato(m, { gruppo: null, filtro: null }, 3).f?.frame_id).toBe(3)
    expect(frameMostrato(m, { gruppo: null, filtro: null }, 99).f?.frame_id).toBe(2)
    expect(frameMostrato(m, { gruppo: "a", filtro: "Ha" }, null).f?.frame_id).toBe(1)
    expect(frameMostrato(m, { gruppo: "c", filtro: null }, null).f).toBeUndefined()
  })

  it("la vista segue gruppo e filtro", () => {
    expect(ids(frameMostrato(m, { gruppo: null, filtro: null }, null))).toEqual([1, 2, 3])
    expect(ids(frameMostrato(m, { gruppo: "a", filtro: null }, null))).toEqual([1, 2])
    const ha = frameMostrato(m, { gruppo: null, filtro: "Ha" }, null)
    expect(ids(ha)).toEqual([1, 3])
    expect(ha.f?.frame_id).toBe(3)
  })
})

describe("geometria e scale", () => {
  it("desktop e telefono, con e senza seconda scala", () => {
    expect(geometria(false, true)).toEqual({
      W: 1000,
      x0: 44,
      x1: 956,
      H: 220,
      top: 12,
      bot: 214,
      passo: 5,
    })
    expect(geometria(true, false)).toEqual({
      W: 360,
      x0: 30,
      x1: 352,
      H: 170,
      top: 12,
      bot: 164,
      passo: 4,
    })
    expect(geometria(false, false).x1).toBe(992)
    expect(geometria(true, true).x1).toBe(330)
  })

  const conLimiti = (key: string, low: number, high: number) => set([stat(key, { low, high })])

  it("gli estremi dell'API col 15% d'aria, mai sotto zero se non ci si va", () => {
    const [lo, hi] = scala([conLimiti("snr", 10, 30), undefined], "snr") ?? [NaN, NaN]
    expect(lo).toBeCloseTo(7)
    expect(hi).toBeCloseTo(33)
    const due = scala([conLimiti("snr", 10, 30), conLimiti("snr", 5, 20)], "snr") ?? []
    expect(due[0]).toBeCloseTo(1.25)
    expect(due[1]).toBeCloseTo(33.75)
    expect(scala([conLimiti("snr", 0, 10)], "snr")).toEqual([0, 11.5])
    const neg = scala([conLimiti("off_axis_px", -2, 2)], "off_axis_px") ?? []
    expect(neg[0]).toBeCloseTo(-2.6)
    expect(neg[1]).toBeCloseTo(2.6)
  })

  it("senza ampiezza mezza unita' d'aria; l'eccentricita' si ferma a 1", () => {
    expect(scala([conLimiti("snr", 4, 4)], "snr")).toEqual([3.5, 4.5])
    const ecc = scala([conLimiti("eccentricity", 0.2, 0.9)], "eccentricity") ?? []
    expect(ecc[0]).toBeCloseTo(0.095)
    expect(ecc[1]).toBe(1)
  })

  it("niente scala senza estremi", () => {
    expect(scala([], "snr")).toBeNull()
    expect(scala([set([stat("snr")])], "snr")).toBeNull()
    expect(scala([conLimiti("snr", 1, 2)], "stars")).toBeNull()
  })

  it("sull'asse le tessere senza unita', le altre misure con la loro", () => {
    expect(sullAsse("stars", 950.6)).toBe("951")
    expect(sullAsse("snr", 35.5)).toBe("36")
    expect(sullAsse("background_adu", 912.4)).toBe("912")
    expect(sullAsse("noise_adu", 12.6)).toBe("13")
    expect(sullAsse("hfd_tilt_pct", 14.4)).toBe("14")
    expect(sullAsse("eccentricity", 0.4234)).toBe("0,42")
    expect(sullAsse("airmass", 1.237)).toBe("1,24")
    expect(sullAsse("fwhm_arcsec", 2.44)).toBe("2,4")
    expect(sullAsse("fwhm_px", 1.26)).toBe("1,3")
    expect(sullAsse("fwhm_zenith_arcsec", 2.06)).toBe("2,1")
    expect(sullAsse("sqm", 21.34)).toBe("21,3")
    expect(sullAsse("sky_adu", 900.2)).toBe("900 ADU")
    expect(sullAsse("psf_snr", 5.4)).toBe("5")
  })

  it("le percentuali sul disegno", () => {
    expect(pc(25, 200)).toBe("12.50%")
  })
})

describe("il disegno dei frame", () => {
  const G = geometria(false, true)
  const TRE = [
    frame(1, "measured", { a: 5, b: 50, moon_altitude_deg: 45 }, "a"),
    frame(2, "too_few_stars", { moon_altitude_deg: -10 }, "a"),
    frame(3, "estimated", { a: 10 }, "b"),
  ]
  const richiesta = (extra: Partial<Richiesta> = {}): Richiesta => ({
    frames: TRE,
    chiavi: ["a", "b"],
    scale: [
      [0, 10],
      [0, 100],
    ],
    g: G,
    inizio: 0,
    linee: false,
    luna: true,
    acceso: 1,
    ...extra,
  })

  it("barre, linee, Luna, separatori e segni, al decimale", () => {
    const d = disegno(richiesta())
    expect(d.finestra).toBe(false)
    expect(d.inizio).toBe(0)
    expect(d.slot).toBe(304)
    expect(d.vis.map((f) => f.frame_id)).toEqual([1, 2, 3])
    expect(d.sep).toEqual(["652.0"])
    expect(d.dL).toBe("M196.0 113.0L500.0 214.0")
    expect([d.hx, d.hy]).toEqual([196, 113])
    expect(d.A).toEqual([
      { x: "189.0", y: "113.0", w: "14.0", h: "101.0", r: "7.0", stimata: false, accesa: true },
      { x: "797.0", y: "12.0", w: "14.0", h: "202.0", r: "7.0", stimata: true, accesa: false },
    ])
    expect(d.dA).toBe("M196.0 113.0L804.0 12.0")
    expect(d.B).toEqual([
      {
        x: "188.3",
        y: "113.0",
        w: "15.5",
        h: "101.0",
        r: "7.8",
        sol: false,
        d: "M187.3 113.0H204.8",
      },
    ])
    expect(d.dB).toBe("M196.0 113.0")
    expect(d.segni).toEqual(["M497 206l6 6m0 -6l-6 6"])
  })

  it("un frame in corso ha il cerchietto; senza Luna niente linea; nessuno acceso", () => {
    const d = disegno(
      richiesta({
        frames: [frame(1, "pending", { moon_altitude_deg: 10 })],
        luna: false,
        acceso: null,
      }),
    )
    expect(d.segni).toEqual(["M498 210a2 2 0 1 0 4 0a2 2 0 1 0 -4 0"])
    expect(d.dL).toBe("")
    expect([d.hx, d.hy]).toEqual([null, null])
  })

  it("la Luna si interrompe dove un frame non ha la sua altezza", () => {
    const frames = [
      frame(1, "measured", { moon_altitude_deg: 90 }),
      frame(2, "measured", {}),
      frame(3, "measured", { moon_altitude_deg: 0 }),
    ]
    expect(disegno(richiesta({ frames })).dL).toBe("M196.0 12.0M804.0 214.0")
  })

  it("a linee niente barre, ma i tracciati restano", () => {
    const d = disegno(richiesta({ linee: true }))
    expect(d.A).toEqual([])
    expect(d.B).toEqual([])
    expect(d.dA).toBe("M196.0 113.0L804.0 12.0")
    expect(d.dB).toBe("M196.0 113.0")
  })

  it("senza misura o senza scala il frame non ha barre", () => {
    expect(disegno(richiesta({ chiavi: [] })).A).toEqual([])
    expect(disegno(richiesta({ scale: [] })).dA).toBe("")
    const una = disegno(richiesta({ chiavi: ["a"], scale: [[0, 10]] }))
    expect(una.A).toHaveLength(2)
    expect(una.B).toEqual([])
    expect(disegno(richiesta({ scale: [[0, 10]] })).dB).toBe("")
  })

  it("una scala senza ampiezza non divide per zero", () => {
    const d = disegno(richiesta({ frames: [frame(1, "measured", { a: 6 })], scale: [[5, 5]] }))
    expect(d.dA).toBe("M500.0 12.0")
  })

  it("niente frame: un posto solo", () => {
    expect(disegno(richiesta({ frames: [] })).slot).toBe(912)
  })

  const molti = (n: number) =>
    Array.from({ length: n }, (_, i) => frame(i + 1, "measured", { a: 1, b: 1 }))

  it("oltre cinque px per barra, la finestra dal suo inizio, tenuta dentro i frame", () => {
    const d = disegno(richiesta({ frames: molti(200), inizio: 50 }))
    expect(d.finestra).toBe(true)
    expect(d.inizio).toBe(18)
    expect(d.vis).toHaveLength(182)
    expect(d.vis[0]?.frame_id).toBe(19)
    expect(disegno(richiesta({ frames: molti(200), inizio: -5 })).inizio).toBe(0)
    expect(disegno(richiesta({ frames: molti(200), inizio: 7 })).vis[0]?.frame_id).toBe(8)
    const pieno = disegno(richiesta({ frames: molti(182), inizio: 7 }))
    expect(pieno.finestra).toBe(false)
    expect(pieno.inizio).toBe(0)
    expect(pieno.B[0]?.sol).toBe(true)
  })
})

describe("la striscia sotto la finestra", () => {
  it("una riga per frame misurato, sui cento della larghezza", () => {
    const frames = [
      frame(1, "measured", { a: 5 }),
      frame(2, "too_few_stars", { a: 5 }),
      frame(3, "estimated", { a: 10 }),
      frame(4, "measured", {}),
    ]
    expect(striscia(frames, "a", [0, 10])).toBe("M0.00 22V12.0M50.00 22V2.0")
    expect(striscia([frame(1, "measured", { a: 3 })], "a", [3, 3])).toBe("M0.00 22V22.0")
  })
})
