// @vitest-environment jsdom
/**
 * *Le misure dei frame* (`src/MisureDeiFrame.tsx`) montate da sole: le tessere con valore, sotto
 * e giudizio, la scelta delle due misure dei grafici, il filtro, l'oggetto isolato e l'altra
 * misura che la finestra ricorda.
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it } from "vitest"

import { t } from "../src/i18n"
import type { Misure } from "../src/MisureDati"
import { MisureDeiFrame } from "../src/MisureDeiFrame"

const RICORDA = "astrolog.misure.altra"

beforeEach(() => localStorage.clear())
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
  silent: median === null ? "no_value" : null,
  ...extra,
})

const TUTTE = [
  stat("fwhm_arcsec", 2.44, { trend: [1, 2, 3] }),
  stat("fwhm_px", 1.2, { verdict: "over" }),
  stat("fwhm_zenith_arcsec", 2.0),
  stat("hfd_arcsec", null),
  stat("hfd_px", 1.6, { measured: 3, q1: 1.5, q3: 1.7, trend: [3, 1] }),
  stat("stars", 950, { q1: 900, q3: 1000 }),
  stat("saturated", 20.6),
  stat("eccentricity", null, { silent: "measuring" }),
  stat("snr", 36),
  stat("background_adu", 900),
  stat("noise_adu", 12),
  stat("hfd_tilt_pct", 14, { verdict: "nogo" }),
  stat("off_axis_px", 0.25),
  stat("off_axis_arcsec", 0.5),
  stat("sqm", 21.3),
  stat("airmass", 1.2, { q1: 1.1, q3: 1.3 }),
  stat("kept", 120),
]

const set = (
  group: string | null,
  filter: string | null,
  frames: number,
  measures: unknown[] = TUTTE,
  extra: Record<string, unknown> = {},
) => ({ group, filter, frames, pending: 0, differs: [], measures, ...extra })

const MISURE = {
  night_id: 7,
  timezone: "Europe/Rome",
  frames: 6,
  pending: 0,
  groups: [{ key: "a", name: "M 51", night_date: null, frames: 6, pending: 0 }],
  filters: [{ name: "Ha", passband: "HA", frames: 4 }],
  sets: [
    set(null, null, 6),
    set("a", null, 6),
    set(null, "Ha", 4, [stat("hfd_px", 1.5, { measured: 2 })], { pending: 2 }),
    set("a", "Ha", 4),
  ],
  series: [],
} as unknown as Misure

function monta(misure: Misure = MISURE, tipo: "notte" | "oggetto" = "notte") {
  render(<MisureDeiFrame misure={misure} formato="desktop" tipo={tipo} />)
  return screen.getByRole("region", { name: t("measures.title") })
}

const tessera = (sezione: HTMLElement, nome: string) =>
  within(sezione)
    .getAllByRole("button")
    .find(
      (b) => b.querySelector(".al-c-misure-frame__blocco-2")?.textContent === nome,
    ) as HTMLElement

const parti = (b: HTMLElement) =>
  [
    ".al-c-misure-frame__testo-5",
    ".al-c-misure-frame__testo-6",
    ".al-c-misure-frame__blocco-3",
  ].map((c) => b.querySelector(c)?.textContent ?? null)

describe("le tessere", () => {
  it("valore, sotto e campionamento di ognuna, dall'API", () => {
    const s = monta()
    expect(parti(tessera(s, "FWHM"))).toEqual([
      "2,4″ · 1,2 px",
      t("measures.zenith", { v: "2,0″" }),
      t("measures.sampling.over"),
    ])
    expect(parti(tessera(s, "HFD"))).toEqual(["1,6 px", "1,5 px – 1,7 px", null])
    expect(parti(tessera(s, "Stars"))).toEqual([
      "950",
      `${t("measures.saturated", { n: "21" })} · 900 – 1000`,
      null,
    ])
    expect(parti(tessera(s, "Eccentricity"))).toEqual(["—", t("measures.pending"), null])
    expect(parti(tessera(s, "Gradient"))).toEqual(["—", null, null])
    expect(parti(tessera(s, "Curvature"))).toEqual(["+0,25 px · +0,5″", null, null])
    expect(parti(tessera(s, "SQM"))).toEqual(["SQM 21,3", t("measures.sqm.unit"), null])
    expect(parti(tessera(s, "Airmass"))).toEqual(["1,20", "1,10 – 1,30", null])
    expect(tessera(s, "Tilt").textContent).toContain(t("measures.tilt.nogo"))
  })

  it("una misura senza valore dice perche'; le stelle senza quartili non dicono le sature", () => {
    const poche = {
      ...MISURE,
      sets: [set(null, null, 6, [stat("stars", 10), stat("saturated", 3), stat("sqm", null)])],
    } as unknown as Misure
    const s = monta(poche)
    expect(parti(tessera(s, "Stars"))).toEqual(["10", null, null])
    expect(parti(tessera(s, "SQM"))).toEqual(["—", t("measures.none"), null])
    expect(parti(tessera(s, "FWHM"))).toEqual(["—", null, null])
  })

  it("lo SQM col giudizio sul Bortle del sito; per filtro niente giudizio (MisureFrame 242)", () => {
    const con = (extra: Record<string, unknown>) =>
      ({
        ...MISURE,
        sets: [set(null, null, 6, [stat("sqm", 20.9, { sky_verdict: "brighter", ...extra })])],
      }) as unknown as Misure
    expect(tessera(monta(con({})), "SQM").textContent).toContain(t("measures.sky.brighter"))
    cleanup()
    // per filtro l'API manda il giudizio nullo (MisureFrame 242, `!multi`)
    expect(
      tessera(monta(con({ per_filter: true, sky_verdict: null })), "SQM").textContent,
    ).not.toContain(t("measures.sky.brighter"))
  })

  it("lo SQM che manca all'insieme dice perche' con le parole della tavola (MisureFrame 236)", () => {
    const senza = (silent: string) =>
      ({
        ...MISURE,
        sets: [set(null, null, 6, [stat("sqm", null, { silent })])],
      }) as unknown as Misure
    expect(parti(tessera(monta(senza("sqm_not_this_filter")), "SQM"))[1]).toBe(
      "nessun frame L o a colori in questa notte",
    )
    cleanup()
    expect(parti(tessera(monta(senza("sqm_not_this_filter"), "oggetto"), "SQM"))[1]).toBe(
      "nessun frame L o a colori",
    )
    cleanup()
    expect(parti(tessera(monta(senza("needs_camera_bias")), "SQM"))[1]).toBe(
      "serve il bias della camera · Bias (ADU) in Attrezzatura",
    )
  })

  it("per filtro o fra setup diversi, la tessera lo dice al posto del valore", () => {
    const misto = {
      ...MISURE,
      sets: [
        set(
          null,
          null,
          6,
          [stat("background_adu", 900, { per_filter: true }), stat("noise_adu", 12)],
          {
            differs: ["camera", "gain"],
          },
        ),
      ],
    } as unknown as Misure
    const s = monta(misto)
    expect(parti(tessera(s, "Background"))).toEqual([
      t("measures.per.filter"),
      t("measures.per.filter.why"),
      null,
    ])
    expect(parti(tessera(s, "Noise"))).toEqual([
      t("measures.not.comparable"),
      t("measures.not.comparable.why", { r: "camera e guadagno" }),
      null,
    ])
    expect(parti(tessera(s, "SNR"))[0]).toBe("—")
  })

  it("la riga della notte sotto la tessera, piena per la prima misura scelta", () => {
    const s = monta()
    const fwhm = tessera(s, "FWHM").querySelector("path")
    expect(fwhm?.getAttribute("d")).toBe("M0.0 27.0L50.0 15.0L100.0 3.0")
    expect(fwhm?.getAttribute("class")).toBe(
      "al-c-misure-frame__spark al-c-misure-frame__spark--prima",
    )
    expect(tessera(s, "HFD").querySelector("path")?.getAttribute("class")).toBe(
      "al-c-misure-frame__spark ",
    )
    expect(tessera(s, "Stars").querySelector("svg")).toBeNull()
  })
})

describe("le due misure dei grafici", () => {
  const premute = (s: HTMLElement) =>
    within(s)
      .getAllByRole("button")
      .filter((b) => b.getAttribute("aria-pressed") === "true")
      .map((b) => b.querySelector(".al-c-misure-frame__blocco-2")?.textContent)

  it("la notte parte da FWHM ed Eccentricity, l'oggetto da FWHM e SNR", () => {
    const s = monta()
    expect(premute(s)).toEqual(["FWHM", "Eccentricity"])
    expect(tessera(s, "FWHM").className).toBe(
      "al-c-misure-frame__colonna-3 al-c-misure-frame__colonna-3--prima",
    )
    expect(tessera(s, "Eccentricity").className).toBe(
      "al-c-misure-frame__colonna-3 al-c-misure-frame__colonna-3--seconda",
    )
    expect(tessera(s, "SNR").className).toBe("al-c-misure-frame__colonna-3 ")
    cleanup()
    expect(premute(monta(MISURE, "oggetto"))).toEqual(["FWHM", "SNR"])
  })

  it("una terza misura spinge fuori la piu' vecchia; si toglie, ma non l'ultima", () => {
    const s = monta()
    fireEvent.click(tessera(s, "SNR"))
    expect(premute(s)).toEqual(["Eccentricity", "SNR"])
    expect(tessera(s, "SNR").className).toContain("--seconda")
    fireEvent.click(tessera(s, "Eccentricity"))
    expect(premute(s)).toEqual(["SNR"])
    fireEvent.click(tessera(s, "SNR"))
    expect(premute(s)).toEqual(["SNR"])
    expect(screen.getByRole("img", { name: /^Ha: SNR di/ })).toBeTruthy()
  })

  it("a confronto segue le misure scelte, e la sua scelta vale finche' resta fra quelle", () => {
    monta()
    const confronto = screen.getByRole("region", { name: t("compare.objects") })
    const menu = within(confronto).getByRole("combobox")
    expect((menu as HTMLSelectElement).value).toBe("fwhm")
    fireEvent.change(menu, { target: { value: "eccentricity" } })
    expect((within(confronto).getByRole("combobox") as HTMLSelectElement).value).toBe(
      "eccentricity",
    )
    fireEvent.click(tessera(screen.getByRole("region", { name: t("measures.title") }), "SNR"))
    fireEvent.click(
      tessera(screen.getByRole("region", { name: t("measures.title") }), "Eccentricity"),
    )
    expect((within(confronto).getByRole("combobox") as HTMLSelectElement).value).toBe("snr")
  })
})

describe("filtro, oggetto e altra misura", () => {
  it("il filtro scelto cambia l'insieme, i frame misurati e la nota delle misure in corso", () => {
    const s = monta()
    const tutti = within(s).getByRole("radio", { name: new RegExp(t("measures.all")) })
    expect(tutti.getAttribute("aria-checked")).toBe("true")
    expect(tutti.textContent).toContain("6")
    expect(s.textContent).toContain(t("measures.of", { m: "3", n: "6" }))
    expect(s.querySelector(".al-c-misure-frame__riga-5")).toBeNull()
    const ha = within(s).getByRole("radio", { name: /Ha/ })
    expect(ha.textContent).toContain("4")
    fireEvent.click(ha)
    expect(s.textContent).toContain(t("measures.of", { m: "2", n: "4" }))
    expect(s.querySelector(".al-c-misure-frame__riga-5")?.textContent).toBe(t("measures.pending"))
    fireEvent.click(within(s).getByRole("radio", { name: new RegExp(t("measures.all")) }))
    expect(s.textContent).toContain(t("measures.of", { m: "3", n: "6" }))
  })

  it("l'oggetto isolato da A confronto ha il suo bottone, che lo libera", () => {
    monta()
    const confronto = screen.getByRole("region", { name: t("compare.objects") })
    fireEvent.click(within(confronto).getByText("M 51"))
    const solo = screen.getByRole("button", { name: t("measures.only", { n: "M 51" }) })
    fireEvent.click(solo)
    expect(screen.queryByRole("button", { name: t("measures.only", { n: "M 51" }) })).toBeNull()
  })

  it("l'altra misura diventa una tessera, entra nei grafici e si ricorda; tolta, se ne va", () => {
    const s = monta()
    const menu = within(s).getByRole("combobox", { name: t("measures.other") })
    expect(within(menu).getAllByRole("option")[0]?.textContent).toBe(t("measures.other.pick"))
    fireEvent.change(menu, { target: { value: "kept" } })
    expect(localStorage.getItem(RICORDA)).toBe("kept")
    expect(parti(tessera(s, "HFD Stars"))[0]).toBe("120")
    expect(tessera(s, "HFD Stars").getAttribute("aria-pressed")).toBe("true")
    expect(tessera(s, "FWHM").getAttribute("aria-pressed")).toBe("false")
    const dopo = within(s).getByRole("combobox", { name: t("measures.other") })
    expect(within(dopo).getAllByRole("option")[0]?.textContent).toBe(t("measures.other.none"))
    const colonne = within(screen.getByRole("table")).getAllByRole("columnheader")
    expect(colonne.at(-1)?.textContent).toBe("HFD Stars")
    fireEvent.change(dopo, { target: { value: "psf_snr" } })
    expect(tessera(s, "HFD Stars")).toBeUndefined()
    expect(tessera(s, "PSF SNR").getAttribute("aria-pressed")).toBe("true")
    fireEvent.change(within(s).getByRole("combobox", { name: t("measures.other") }), {
      target: { value: "" },
    })
    expect(localStorage.getItem(RICORDA)).toBeNull()
    expect(tessera(s, "PSF SNR")).toBeUndefined()
    expect(screen.getByRole("img", { name: /^Ha: Eccentricity di/ })).toBeTruthy()
  })

  it("tolta l'unica misura scelta, i grafici tornano alla FWHM", () => {
    const s = monta()
    fireEvent.change(within(s).getByRole("combobox", { name: t("measures.other") }), {
      target: { value: "kept" },
    })
    fireEvent.click(tessera(s, "Eccentricity"))
    fireEvent.change(within(s).getByRole("combobox", { name: t("measures.other") }), {
      target: { value: "" },
    })
    expect(screen.getByRole("img", { name: /^Ha: FWHM di/ })).toBeTruthy()
  })

  it("il lato del pilastro dice i lati dai conti dell'API e non entra nei grafici (tavola 248)", () => {
    const misure = {
      ...MISURE,
      sets: [
        set(null, null, 6, TUTTE, { pier_side: { east: 2, west: 1 } }),
        ...MISURE.sets.slice(1),
      ],
    } as unknown as Misure
    const s = monta(misure)
    fireEvent.change(within(s).getByRole("combobox", { name: t("measures.other") }), {
      target: { value: "pier_side" },
    })
    expect(parti(tessera(s, "Pier Side"))).toEqual(["est e ovest", "a ovest 1 di 3 frame", null])
    expect(tessera(s, "Pier Side").getAttribute("aria-pressed")).toBe("false")
    fireEvent.click(tessera(s, "Pier Side"))
    expect(tessera(s, "Pier Side").getAttribute("aria-pressed")).toBe("false")
    expect(screen.getByRole("img", { name: /^Ha: FWHM e Eccentricity/ })).toBeTruthy()
    const riga = within(screen.getByRole("table")).getAllByRole("row")[1]
    expect(within(riga!).getAllByRole("cell").at(-1)?.textContent).toBe("—")
  })

  it("all'apertura riprende l'altra misura ricordata", () => {
    localStorage.setItem(RICORDA, "kept")
    const s = monta()
    expect(parti(tessera(s, "HFD Stars"))[0]).toBe("120")
    expect(tessera(s, "HFD Stars").getAttribute("aria-pressed")).toBe("false")
  })
})
