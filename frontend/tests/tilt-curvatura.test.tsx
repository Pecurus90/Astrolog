// @vitest-environment jsdom
/**
 * *Tilt e curvatura di campo* (`src/TiltCurvatura.tsx`) montato da solo: il sensore grande
 * della scelta e quelli piccoli per filtro, cerchi ed etichette al decimale della tavola.
 */
import { cleanup, render, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { t } from "../src/i18n"
import type { Misure, Scelta } from "../src/MisureDati"
import { TiltCurvatura } from "../src/TiltCurvatura"

afterEach(cleanup)

const stat = (key: string, median: number | null, extra: Record<string, unknown> = {}) => ({
  key,
  unit: "px",
  group: "stars_shape",
  measured: 3,
  median,
  q1: null,
  q3: null,
  low: null,
  high: null,
  trend: null,
  verdict: null,
  silent: null,
  ...extra,
})

// le misure in piu' prima: la prima di una chiave vince
const sensore = (angoli: number[], centro: number | null, extra: unknown[] = []) => [
  ...extra,
  ...angoli.map((v, i) => stat(`hfd_corner_${i + 1}_px`, v)),
  stat("hfd_centre_px", centro),
  stat("hfd_px", 3, { measured: 5 }),
  stat("hfd_tilt_pct", 14, { verdict: "marginal" }),
  stat("off_axis_px", 0.25),
]

const set = (filter: string | null, measures: unknown[], frames = 6) => ({
  group: null,
  filter,
  frames,
  pending: 0,
  differs: [],
  measures,
})

const MISURE = {
  groups: [],
  filters: [
    { name: "Ha", passband: "HA", frames: 4 },
    { name: "OIII", passband: "OIII", frames: 2 },
    { name: "SII", passband: "SII", frames: 2 },
  ],
  sets: [
    set(null, sensore([3.1, 3.2, 3.3, 3.6], 3, [stat("off_axis_arcsec", 0.5)])),
    set("Ha", sensore([1.5, 3, 3, 3], 3, [stat("hfd_tilt_pct", 20, { verdict: "go" })]), 4),
    set("OIII", sensore([3, 3, 3], 3), 2),
    set("SII", sensore([3, 3, 3, 3], 3), 2),
  ],
  series: [],
} as unknown as Misure

function monta(scelta: Scelta = { gruppo: null, filtro: null }, misure: Misure = MISURE) {
  render(<TiltCurvatura misure={misure} scelta={scelta} />)
  return screen.getByRole("region", { name: t("sensor.title") })
}

const cerchi = (svg: Element) =>
  [...svg.querySelectorAll("circle")].map((c) => [
    c.getAttribute("cx"),
    c.getAttribute("cy"),
    c.getAttribute("r"),
    c.getAttribute("class"),
  ])

const C = "al-c-misure-frame__cerchio"
const MAX = `${C} ${C}--max`

describe("il sensore grande", () => {
  it("i quattro angoli e il centro, il raggio che cresce con la HFD, il piu' alto acceso", () => {
    const sezione = monta()
    const svg = within(sezione).getByRole("img")
    expect(svg.getAttribute("aria-label")).toBe(
      t("sensor.label", {
        a: "3,1 px / 3,2 px / 3,3 px / 3,6 px",
        c: "3,0 px",
        t: "14%",
        k: "+0,25 px · +0,5″",
      }),
    )
    expect(svg.getAttribute("viewBox")).toBe("0 0 300 200")
    expect(cerchi(svg)).toEqual([
      ["70.0", "143.0", "11.3", C],
      ["230.0", "143.0", "13.7", C],
      ["230.0", "50.0", "16.0", C],
      ["70.0", "50.0", "23.0", MAX],
      ["150.0", "96.0", "9.0", C],
    ])
    const etichette = [...sezione.querySelectorAll<HTMLElement>(".al-c-misure-frame__strato-4")]
    expect(etichette.map((e) => [e.textContent, e.style.left, e.style.top])).toEqual([
      ["3,1 px", "23.3%", "60.3%"],
      ["3,2 px", "76.7%", "59.2%"],
      ["3,3 px", "76.7%", "39%"],
      ["3,6 px", "23.3%", "42.5%"],
      ["3,0 px", "50%", "58.5%"],
    ])
    expect(etichette[3]?.className).toBe(
      "al-c-misure-frame__strato-4 al-c-misure-frame__strato-4--max",
    )
  })

  it("in testa la scelta e i frame misurati; tilt col giudizio, curvatura in px e secondi d'arco", () => {
    const sezione = monta()
    expect(sezione.textContent).toContain(
      `${t("sensor.all")} · ${t("measures.of", { m: "5", n: "6" })}`,
    )
    const [tilt, curv] = sezione.querySelectorAll(".al-c-misure-frame__griglia-1 > div")
    expect(tilt?.textContent).toBe(`Tilt14%! ${t("measures.tilt.marginal")}`)
    expect(curv?.textContent).toBe("Curvature+0,25 px · +0,5″")
  })

  it("col filtro scelto la testa lo nomina", () => {
    const sezione = monta({ gruppo: null, filtro: "Ha" })
    expect(sezione.textContent).toContain(`Ha · ${t("measures.of", { m: "5", n: "4" })}`)
  })

  it("senza centro, o senza un angolo, il sensore non c'e' e lo dice", () => {
    const senza = {
      ...MISURE,
      sets: [set(null, sensore([3, 3, 3, 3], null)), ...MISURE.sets.slice(1)],
    } as unknown as Misure
    const sezione = monta({ gruppo: null, filtro: null }, senza)
    expect(within(sezione).queryByRole("img")).toBeNull()
    expect(sezione.textContent).toContain(t("measures.none"))
    cleanup()
    const angolo = monta({ gruppo: null, filtro: "OIII" })
    expect(within(angolo).queryByRole("img")).toBeNull()
  })
})

describe("i sensori per filtro", () => {
  it("uno per filtro che li ha, piccolo, col suo tilt e il suo giudizio", () => {
    const sezione = monta()
    const piccoli = [...sezione.querySelectorAll(".al-c-misure-frame__colonna-19")]
    expect(piccoli.map((p) => p.querySelector(".al-c-misure-frame__riga-38")?.textContent)).toEqual(
      ["Ha", "SII"],
    )
    const [ha, sii] = piccoli
    expect(ha?.querySelector(".al-c-misure-frame__testo-20")?.textContent).toBe(
      "Tilt 20% · Curvature +0,25 px",
    )
    expect(ha?.textContent).toContain(t("measures.tilt.go"))
    expect(sii?.textContent).toContain(t("measures.tilt.marginal"))
    const svg = ha?.querySelector("svg") as SVGElement
    expect(svg.getAttribute("viewBox")).toBe("0 0 150 100")
    expect(svg.getAttribute("aria-hidden")).toBe("true")
    // sotto la HFD del centro il raggio si ferma a 2
    expect(cerchi(svg)).toEqual([
      ["35.0", "71.5", "2.0", C],
      ["115.0", "71.5", "4.0", MAX],
      ["115.0", "25.0", "4.0", MAX],
      ["35.0", "25.0", "4.0", MAX],
      ["75.0", "48.0", "4.0", C],
    ])
    expect(ha?.querySelector<HTMLElement>(".al-c-misure-frame__tondo-1")?.style.background).toBe(
      "var(--filtro-ha)",
    )
    expect(sezione.querySelectorAll(".al-c-misure-frame__strato-4")).toHaveLength(5)
  })

  it("un tilt senza giudizio non porta pillola", () => {
    const muto = {
      ...MISURE,
      sets: [
        MISURE.sets[0],
        set("Ha", sensore([3, 3, 3, 3], 3, [stat("hfd_tilt_pct", 5, { verdict: null })])),
      ],
    } as unknown as Misure
    const sezione = monta({ gruppo: null, filtro: null }, muto)
    const ha = sezione.querySelector(".al-c-misure-frame__colonna-19")
    expect(ha?.querySelector(".al-c-misure-frame__testo-20")?.textContent).toBe(
      "Tilt 5% · Curvature +0,25 px",
    )
    expect(ha?.querySelector(".al-c-misure-frame__riga-37")?.textContent).toBe("")
  })
})
