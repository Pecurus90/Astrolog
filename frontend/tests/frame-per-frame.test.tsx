// @vitest-environment jsdom
/**
 * *Frame per frame* (`src/FramePerFrame.tsx`) montato da solo: i comandi della vista, i grafici
 * per filtro, l'asse, il riquadro del frame sotto il dito, la finestra e la legenda.
 */
import { cleanup, fireEvent, render, screen } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { FramePerFrame } from "../src/FramePerFrame"
import { t } from "../src/i18n"
import type { FrameMisurato, Misure, Scelta } from "../src/MisureDati"

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

// jsdom non misura: il grafico largo quanto il suo viewBox, a partire da zero.
beforeEach(() => {
  vi.spyOn(Element.prototype, "getBoundingClientRect").mockReturnValue({
    left: 0,
    top: 0,
    width: 1000,
    height: 220,
    right: 1000,
    bottom: 220,
    x: 0,
    y: 0,
    toJSON: () => ({}),
  })
})

const stat = (key: string, low: number, high: number, median: number | null = low) => ({
  key,
  unit: "px",
  group: "stars_shape",
  measured: 2,
  median,
  q1: low,
  q3: high,
  low,
  high,
  trend: null,
  verdict: null,
  silent: null,
})

const MISURE_HA = [
  stat("fwhm_arcsec", 2, 3, 2.5),
  stat("fwhm_zenith_arcsec", 1.5, 2.5, 1.8),
  stat("eccentricity", 0.4, 0.5, 0.45),
  stat("sqm", 20, 21, 20.5),
  stat("background_adu", 800, 900, 850),
]

const insieme = (
  filter: string | null,
  measures = MISURE_HA,
  differs: string[] = [],
  group: string | null = null,
) => ({
  group,
  filter,
  frames: 4,
  pending: 0,
  differs,
  measures,
})

const frame = (
  frame_id: number,
  state: string,
  group: string | null,
  filter: string,
  values: Record<string, number>,
): FrameMisurato =>
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

const SERIE = [
  frame(1, "measured", "a", "Ha", {
    fwhm_arcsec: 2.0,
    fwhm_zenith_arcsec: 1.6,
    eccentricity: 0.4,
    airmass: 1.23,
    moon_altitude_deg: 20,
  }),
  frame(2, "estimated", "a", "Ha", { fwhm_arcsec: 3.0, eccentricity: 0.5, moon_altitude_deg: -5 }),
  frame(3, "too_few_stars", "b", "Ha", {}),
  frame(4, "pending", "b", "Ha", {}),
  frame(5, "measured", "b", "OIII", { fwhm_arcsec: 2.5, eccentricity: 0.3 }),
]

const MISURE = {
  night_id: 7,
  timezone: "Europe/Rome",
  frames: 5,
  pending: 1,
  groups: [
    { key: "a", name: "M 51", night_date: null, frames: 2, pending: 0 },
    { key: "b", name: "M 101", night_date: null, frames: 3, pending: 1 },
  ],
  filters: [
    { name: "Ha", passband: "HA", frames: 4 },
    { name: "OIII", passband: "OIII", frames: 1 },
  ],
  sets: [
    insieme(null),
    insieme("Ha"),
    insieme("OIII", [stat("fwhm_arcsec", 2.5, 2.5)]),
    insieme(null, MISURE_HA, [], "a"),
    insieme("Ha", MISURE_HA, [], "a"),
  ],
  series: SERIE,
} as unknown as Misure

const TUTTI: Scelta = { gruppo: null, filtro: null }

function monta(
  misure: Misure = MISURE,
  met = ["fwhm", "eccentricity"],
  scelta: Scelta = TUTTI,
  sel: number | null = null,
) {
  const onSel = vi.fn()
  const vista = render(
    <FramePerFrame
      misure={misure}
      scelta={scelta}
      met={met}
      sel={sel}
      onSel={onSel}
      formato="desktop"
    />,
  )
  return { onSel, ...vista }
}

const grafico = (nome: string) => screen.getByRole("img", { name: nome })
const sullAsse = (c: HTMLElement) =>
  [...c.querySelectorAll<HTMLElement>(".al-c-misure-frame__strato-1")].map((s) => s.textContent)

describe("un grafico per filtro", () => {
  it("il primo filtro della notte, con le mediane e l'asse delle due misure", () => {
    const { container } = monta()
    expect(grafico("Ha: FWHM e Eccentricity di 4 frame")).toBeTruthy()
    expect(screen.queryByRole("img", { name: /^OIII/ })).toBeNull()
    expect(container.textContent).toContain("FWHM 2,5″")
    expect(container.textContent).toContain("Eccentricity 0,45")
    // 10%, 50% e 90% della scala col 15% d'aria: FWHM 1,85-3,15, Eccentricity 0,385-0,515
    expect(sullAsse(container)).toEqual(["2,0", "2,5", "3,0", "0,40", "0,45", "0,50"])
    const [primo, , , quarto] = container.querySelectorAll<HTMLElement>(
      ".al-c-misure-frame__strato-1",
    )
    expect(primo?.style.left).toBe("3.8%")
    expect(primo?.style.top).toBe("88.09%")
    expect(primo?.style.transform).toBe("translate(-100%, -50%)")
    expect(quarto?.style.left).toBe("96.2%")
    expect(quarto?.style.transform).toBe("translate(0px, -50%)")
  })

  it("le barre: stimata, accesa sul frame aperto, tratteggiata la seconda misura", () => {
    const { container } = monta(MISURE, ["fwhm", "eccentricity"], TUTTI, 1)
    const barre = [...container.querySelectorAll("rect.al-c-misure-frame__barra")]
    expect(barre.map((r) => r.getAttribute("class"))).toEqual([
      "al-c-misure-frame__barra al-c-misure-frame__barra--accesa",
      "al-c-misure-frame__barra al-c-misure-frame__barra--stimata",
    ])
    expect(container.querySelectorAll("rect.al-c-misure-frame__tratto-2")).toHaveLength(2)
    expect(container.querySelector(".al-c-misure-frame__tratto-6")).toBeNull()
  })

  it("una misura sola: niente seconda scala, l'asse finisce piu' a destra", () => {
    const { container } = monta(MISURE, ["fwhm"])
    expect(grafico("Ha: FWHM di 4 frame")).toBeTruthy()
    expect(sullAsse(container)).toEqual(["2,0", "2,5", "3,0"])
    const asse = container.querySelector("line.al-c-misure-frame__tratto-1")
    expect(asse?.getAttribute("x2")).toBe("992")
  })

  it("i nomi degli oggetti sotto l'asse, dove ne comincia uno", () => {
    const { container } = monta()
    const nomi = [...container.querySelectorAll<HTMLElement>(".al-c-misure-frame__strato-2")]
    expect(nomi.map((n) => n.textContent)).toEqual(["M 51", "M 101"])
    expect(nomi[1]?.style.left).toBe("calc(45.6%)")
    // fra due oggetti, il separatore tratteggiato
    expect(container.querySelectorAll("line.al-c-misure-frame__tratto-2")).toHaveLength(1)
  })

  it("un nome che non ci sta salta", () => {
    const lungo = {
      ...MISURE,
      groups: [
        { key: "a", name: "Nebulosa Nord America e Pellicano", night_date: null, frames: 1 },
        { key: "b", name: "M 101", night_date: null, frames: 3 },
      ],
      series: [
        frame(1, "measured", "a", "Ha", { fwhm_arcsec: 2 }),
        ...Array.from({ length: 30 }, (_, i) =>
          frame(i + 2, "measured", "b", "Ha", { fwhm_arcsec: 2 }),
        ),
      ],
    } as unknown as Misure
    const { container } = monta(lungo)
    const nomi = [...container.querySelectorAll(".al-c-misure-frame__strato-2")]
    expect(nomi.map((n) => n.textContent)).toEqual(["Nebulosa Nord America e Pellicano"])
  })

  it("il filtro scelto sopra decide il grafico; un altro filtro se ne aggiunge, l'ultimo resta", () => {
    monta(MISURE, ["fwhm", "eccentricity"], { gruppo: null, filtro: "OIII" })
    expect(grafico("OIII: FWHM e Eccentricity di 1 frame")).toBeTruthy()
    fireEvent.click(screen.getByRole("link", { name: /Ha/ }))
    expect(grafico("Ha: FWHM e Eccentricity di 4 frame")).toBeTruthy()
    expect(grafico("OIII: FWHM e Eccentricity di 1 frame")).toBeTruthy()
    fireEvent.click(screen.getByRole("link", { name: /OIII/ }))
    expect(screen.queryByRole("img", { name: /^OIII/ })).toBeNull()
    fireEvent.click(screen.getByRole("link", { name: /Ha/ }))
    expect(grafico("Ha: FWHM e Eccentricity di 4 frame")).toBeTruthy()
  })

  it("nel gruppo scelto, solo i suoi frame e i suoi filtri", () => {
    monta(MISURE, ["fwhm"], { gruppo: "a", filtro: null })
    expect(screen.getByRole("link", { name: /Ha/ })).toBeTruthy()
    expect(screen.queryByRole("link", { name: /OIII/ })).toBeNull()
    expect(grafico("Ha: FWHM di 2 frame")).toBeTruthy()
  })
})

describe("i comandi della vista", () => {
  it("a linee i tracciati al posto delle barre, e il cerchio sul frame aperto", () => {
    const { container } = monta(MISURE, ["fwhm", "eccentricity"], TUTTI, 1)
    const barre = screen.getByRole("radio", { name: t("chart.view.barre") })
    const linee = screen.getByRole("radio", { name: t("chart.view.linee") })
    expect(barre.getAttribute("aria-checked")).toBe("true")
    expect(linee.getAttribute("aria-checked")).toBe("false")
    expect(container.querySelector(".al-c-misure-frame__tratto-5")).toBeNull()
    fireEvent.click(linee)
    expect(linee.getAttribute("aria-checked")).toBe("true")
    expect(container.querySelectorAll("rect.al-c-misure-frame__barra")).toHaveLength(0)
    const tracciati = [...container.querySelectorAll("path.al-c-misure-frame__tratto-5")]
    expect(tracciati).toHaveLength(2)
    expect(tracciati[0]?.getAttribute("d")).toMatch(/^M158\.0 [\d.]+L386\.0 [\d.]+$/)
    expect(container.querySelector("circle.al-c-misure-frame__tratto-6")).toBeTruthy()
    expect(container.querySelector(".al-c-misure-frame__pillola-1--linea-1")).toBeTruthy()
    expect(container.querySelector(".al-c-misure-frame__pillola-1--linea-2")).toBeTruthy()
    fireEvent.click(barre)
    expect(container.querySelector(".al-c-misure-frame__pillola-1--barra-1")).toBeTruthy()
    expect(container.querySelector(".al-c-misure-frame__pillola-1--barra-2")).toBeTruthy()
  })

  it("per valore: solo i misurati, dal piu' basso, senza oggetti sotto l'asse", () => {
    const { container } = monta()
    expect(container.textContent).not.toContain(t("chart.low"))
    fireEvent.change(screen.getByRole("combobox", { name: t("chart.order") }), {
      target: { value: "val" },
    })
    expect(grafico("Ha: FWHM e Eccentricity di 2 frame")).toBeTruthy()
    expect(container.textContent).toContain(t("chart.low"))
    expect(container.textContent).toContain(t("chart.high", { m: "FWHM" }))
    expect(container.querySelectorAll(".al-c-misure-frame__strato-2")).toHaveLength(0)
    fireEvent.change(screen.getByRole("combobox", { name: t("chart.order") }), {
      target: { value: "ora" },
    })
    expect(grafico("Ha: FWHM e Eccentricity di 4 frame")).toBeTruthy()
  })

  it("per valore l'ordine e' quello del valore, non della ripresa", () => {
    const misure = {
      ...MISURE,
      series: [
        frame(1, "measured", "a", "Ha", { fwhm_arcsec: 2.9 }),
        frame(2, "measured", "a", "Ha", { fwhm_arcsec: 2.1 }),
      ],
    } as unknown as Misure
    const { container } = monta(misure, ["fwhm"], TUTTI, 1)
    fireEvent.change(screen.getByRole("combobox", { name: t("chart.order") }), {
      target: { value: "val" },
    })
    const barre = [...container.querySelectorAll("rect.al-c-misure-frame__barra")]
    // il frame 1, acceso, ora sta a destra
    expect(barre.map((r) => r.getAttribute("class"))).toEqual([
      "al-c-misure-frame__barra",
      "al-c-misure-frame__barra al-c-misure-frame__barra--accesa",
    ])
  })

  it("allo zenit FWHM cambia colonna e nome, l'altra misura resta", () => {
    const { container } = monta()
    const valore = screen.getByRole("combobox", { name: t("chart.value") })
    fireEvent.change(valore, { target: { value: "z" } })
    expect(container.textContent).toContain(`FWHM${t("chart.at.zenith")}`)
    expect(container.textContent).not.toContain(`Eccentricity${t("chart.at.zenith")}`)
    expect(container.textContent).toContain("FWHM 1,8″")
    fireEvent.change(screen.getByRole("combobox", { name: t("chart.value") }), {
      target: { value: "m" },
    })
    expect(container.textContent).not.toContain(t("chart.at.zenith"))
  })

  it("senza zenit nelle misure scelte, niente scelta del valore", () => {
    monta(MISURE, ["eccentricity", "sqm"])
    expect(screen.queryByRole("combobox", { name: t("chart.value") })).toBeNull()
  })

  it("la Luna si accende e si spegne, con la sua chiave e la sua linea", () => {
    const { container } = monta()
    const luna = screen.getByRole("switch", { name: t("chart.moon.on") })
    expect(container.textContent).not.toContain(t("chart.moon.key"))
    fireEvent.click(luna)
    expect(container.textContent).toContain(t("chart.moon.key"))
    const linea = container.querySelector("path[stroke-dasharray='1 4']")
    expect(linea?.getAttribute("d")).toBe("M158.0 169.1L386.0 214.0")
    fireEvent.click(screen.getByRole("switch", { name: t("chart.moon.off") }))
    expect(container.textContent).not.toContain(t("chart.moon.key"))
  })

  it("per valore la Luna non c'e'", () => {
    monta()
    fireEvent.change(screen.getByRole("combobox", { name: t("chart.order") }), {
      target: { value: "val" },
    })
    expect(screen.queryByRole("switch")).toBeNull()
  })
})

describe("la nota accanto al filtro", () => {
  it("l'SQM dice che cambia con la direzione, o che non c'e'", () => {
    const { container } = monta(MISURE, ["sqm"])
    expect(container.textContent).toContain(t("chart.sqm.direction"))
    cleanup()
    const senza = {
      ...MISURE,
      sets: [insieme(null), insieme("Ha", [stat("sqm", 20, 21, null)])],
    } as unknown as Misure
    const altro = monta(senza, ["sqm"])
    expect(altro.container.textContent).toContain(t("measures.none"))
  })

  it("fondo e rumore fra setup diversi non si confrontano; solo la posa, al secondo", () => {
    const camera = {
      ...MISURE,
      sets: [insieme(null), insieme("Ha", MISURE_HA, ["camera"])],
    } as unknown as Misure
    const { container } = monta(camera, ["background"])
    expect(container.textContent).toContain(t("chart.not.comparable", { r: "camera" }))
    cleanup()
    const posa = {
      ...MISURE,
      sets: [insieme(null), insieme("Ha", MISURE_HA, ["exposure"])],
    } as unknown as Misure
    const altro = monta(posa, ["noise"])
    expect(altro.container.textContent).toContain(
      t("chart.not.comparable.rate", { r: "tempo di posa" }),
    )
    cleanup()
    // coi valori dall'API, le parole della tavola (MisureFrame 312): «tempo di posa (300 s e 180 s)»
    const coi = {
      ...MISURE,
      sets: [
        insieme(null),
        { ...insieme("Ha", MISURE_HA, ["exposure"]), differs_values: { exposure: [300, 180] } },
      ],
    } as unknown as Misure
    const terzo = monta(coi, ["noise"])
    expect(terzo.container.textContent).toContain(
      "frame non confrontabili, tempo di posa (300 s e 180 s): fondo e rumore non si confrontano fra loro; il fondo al secondo sì",
    )
    cleanup()
    const fwhm = monta(camera, ["fwhm"])
    expect(fwhm.container.querySelector(".al-c-misure-frame__testo-2")).toBeNull()
  })
})

describe("il frame sotto il dito", () => {
  const sopra = (clientX: number) => {
    const area = screen.getAllByRole("img")[0]?.parentElement as HTMLElement
    fireEvent.mouseMove(area, { clientX })
    return area
  }

  it("il riquadro dice frame, oggetto, ora e misure; un tocco lo apre", () => {
    const { onSel } = monta()
    const area = sopra(158)
    const riquadro = screen.getByRole("tooltip")
    expect(riquadro.textContent).toContain(t("shot.title", { i: "1", n: "4", f: "Ha" }))
    expect(riquadro.textContent).toContain("M 51 · 23:00")
    expect(riquadro.textContent).toContain("FWHM2,0″")
    expect(riquadro.textContent).toContain("Eccentricity0,40")
    expect(riquadro.textContent).toContain("Airmass1,23")
    expect(riquadro.style.left).toBe("15.8%")
    expect(riquadro.style.transform).toBe("translateX(12px)")
    fireEvent.click(area, { clientX: 158 })
    expect(onSel).toHaveBeenCalledWith(1)
    fireEvent.mouseLeave(area)
    expect(screen.queryByRole("tooltip")).toBeNull()
  })

  it("oltre il 60% della larghezza il riquadro passa a sinistra", () => {
    monta()
    sopra(841)
    const riquadro = screen.getByRole("tooltip")
    expect(riquadro.textContent).toContain(t("shot.title", { i: "4", n: "4", f: "Ha" }))
    expect(riquadro.textContent).toContain(t("measures.pending"))
    expect(riquadro.style.transform).toBe("translateX(calc(-100% - 12px))")
  })

  it("un frame con troppo poche stelle lo dice; fuori dall'asse si prende il piu' vicino", () => {
    monta()
    sopra(613)
    expect(screen.getByRole("tooltip").textContent).toContain(t("shot.few"))
    sopra(5000)
    expect(screen.getByRole("tooltip").textContent).toContain(t("measures.pending"))
    sopra(-50)
    expect(screen.getByRole("tooltip").textContent).toContain("Frame 1 di 4")
  })

  it("col dito: il primo tocco sceglie il frame", () => {
    monta()
    const area = grafico("Ha: FWHM e Eccentricity di 4 frame").parentElement as HTMLElement
    fireEvent.touchStart(area, { touches: [{ clientX: 386 }] })
    expect(screen.getByRole("tooltip").textContent).toContain("Frame 2 di 4")
  })

  it("con la Luna accesa, la sua altezza; sotto l'orizzonte a parole", () => {
    monta()
    fireEvent.click(screen.getByRole("switch", { name: t("chart.moon.on") }))
    sopra(158)
    expect(screen.getByRole("tooltip").textContent).toContain("Moon Altitude20°")
    sopra(386)
    expect(screen.getByRole("tooltip").textContent).toContain(
      `Moon Altitude${t("chart.moon.below")}`,
    )
  })

  it("l'airmass gia' in grafico non si ripete", () => {
    monta(MISURE, ["airmass"])
    sopra(158)
    const riquadro = screen.getByRole("tooltip")
    expect(riquadro.textContent?.match(/Airmass/g)).toHaveLength(1)
  })
})

describe("la legenda", () => {
  it("i segni che ci sono: forma stimata, troppo poche stelle, in corso", () => {
    const { container } = monta()
    const legenda = container.querySelector(".al-c-misure-frame__riga-26") as HTMLElement
    expect(legenda.textContent).toContain(t("chart.caption"))
    expect(legenda.textContent).toContain(t("chart.estimated"))
    expect(legenda.textContent).toContain(t("shot.few"))
    expect(legenda.textContent).toContain(t("measures.pending"))
    const segni = [...legenda.querySelectorAll("path")].map((p) => [
      p.getAttribute("class"),
      p.getAttribute("d"),
    ])
    expect(segni).toEqual([
      ["al-c-misure-frame__chiave--accento", "M6 1h6v8h-6z"],
      ["al-c-misure-frame__chiave--tenue", "M6 2l6 6m0 -6l-6 6"],
      ["al-c-misure-frame__chiave--tenue", "M7 5a2 2 0 1 0 4 0a2 2 0 1 0 -4 0"],
    ])
    fireEvent.click(screen.getByRole("radio", { name: t("chart.view.linee") }))
    expect(legenda.querySelector("path")?.getAttribute("d")).toBe(
      "M9 5m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0",
    )
  })

  it("nel gruppo scelto, solo i segni dei suoi frame", () => {
    const { container } = monta(MISURE, ["fwhm"], { gruppo: "a", filtro: null })
    const legenda = container.querySelector(".al-c-misure-frame__riga-26") as HTMLElement
    expect(legenda.textContent).toContain(t("chart.estimated"))
    expect(legenda.textContent).not.toContain(t("shot.few"))
    expect(legenda.textContent).not.toContain(t("measures.pending"))
  })
})

describe("la finestra dei frame", () => {
  const molti = (n: number, gruppo: (i: number) => string | null) =>
    ({
      ...MISURE,
      series: Array.from({ length: n }, (_, i) =>
        frame(i + 1, "measured", gruppo(i), "Ha", { fwhm_arcsec: 2 + (i % 3) / 2 }),
      ),
    }) as unknown as Misure

  it("› e ‹ spostano di mezza finestra, il cursore segue", () => {
    monta(molti(400, () => "a"))
    const tratto = screen.getByRole("slider", { name: t("chart.window.label") })
    expect(tratto.getAttribute("aria-valuetext")).toBe("frame 1–182 di 400")
    expect(tratto.getAttribute("aria-valuenow")).toBe("1")
    expect(tratto.getAttribute("aria-valuemax")).toBe("400")
    const [, dopo] = screen.getAllByRole("button", { name: t("shot.next") })
    fireEvent.click(dopo ?? screen.getByRole("button", { name: t("shot.next") }))
    expect(tratto.getAttribute("aria-valuetext")).toBe("frame 92–273 di 400")
    fireEvent.click(screen.getByRole("button", { name: t("shot.prev") }))
    expect(tratto.getAttribute("aria-valuetext")).toBe("frame 1–182 di 400")
    const cursore = tratto.querySelector<HTMLElement>(".al-c-misure-frame__strato-3")
    expect(cursore?.style.width).toBe("45.5%")
  })

  it("trascinando, la finestra si centra dove sta il dito; senza tasto non si muove", () => {
    monta(molti(400, () => "a"))
    const tratto = screen.getByRole("slider", { name: t("chart.window.label") })
    fireEvent.pointerDown(tratto, { clientX: 500 })
    expect(tratto.getAttribute("aria-valuetext")).toBe("frame 110–291 di 400")
    fireEvent.pointerMove(tratto, { clientX: 0, buttons: 0 })
    expect(tratto.getAttribute("aria-valuetext")).toBe("frame 110–291 di 400")
    fireEvent.pointerMove(tratto, { clientX: 1000, buttons: 1 })
    expect(tratto.getAttribute("aria-valuetext")).toBe("frame 219–400 di 400")
  })

  it("un bottone per oggetto porta al suo primo frame", () => {
    monta(molti(400, (i) => (i < 300 ? "a" : "b")))
    const tratto = screen.getByRole("slider", { name: t("chart.window.label") })
    fireEvent.click(screen.getByRole("button", { name: "M 101" }))
    expect(tratto.getAttribute("aria-valuetext")).toBe("frame 219–400 di 400")
    fireEvent.click(screen.getByRole("button", { name: "M 51" }))
    expect(tratto.getAttribute("aria-valuetext")).toBe("frame 1–182 di 400")
  })

  it("un oggetto solo: niente bottoni", () => {
    monta(molti(400, () => "a"))
    expect(screen.queryByRole("button", { name: "M 51" })).toBeNull()
  })
})
