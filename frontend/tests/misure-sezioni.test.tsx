// @vitest-environment jsdom
/**
 * Le tre sezioni delle misure (`src/MisureSezioni.tsx`) montate da sole: *Il frame* con le sue
 * tessere e le sue note, *A confronto* sulla scala comune, la tabella *Per filtro*.
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { t } from "../src/i18n"
import type { EsitoDelGruppo, FrameMisurato, Misure, Scelta } from "../src/MisureDati"
import { AConfronto, IlFrame, PerFiltro } from "../src/MisureSezioni"

afterEach(cleanup)

const RUMORE = t("measure.unit.noise")
const TUTTI: Scelta = { gruppo: null, filtro: null }

const frame = (
  frame_id: number,
  state: string,
  values: Record<string, number>,
  extra: Partial<FrameMisurato> = {},
): FrameMisurato =>
  ({
    frame_id,
    start: "2024-05-18T23:00:00+02:00",
    group: "a",
    filter: "Ha",
    state,
    tilt_level: null,
    sampling: null,
    angle_axis: null,
    values,
    ...extra,
  }) as FrameMisurato

const PIENO = frame(
  1,
  "measured",
  {
    fwhm_arcsec: 2.44,
    fwhm_px: 1.26,
    fwhm_zenith_arcsec: 2.1,
    hfd_arcsec: 3.1,
    hfd_px: 1.6,
    stars: 950,
    saturated: 21,
    eccentricity: 0.42,
    snr: 35.6,
    background_adu: 900.2,
    noise_adu: 12.4,
    airmass: 1.23,
    altitude_deg: 54.4,
    gradient_noise: 1.23,
    hfd_tilt_pct: 14.4,
    off_axis_px: 0.25,
    off_axis_arcsec: 0.49,
    fwhm_tilt: 0.123,
    fwhm_curvature: 0.456,
    sqm: 21.34,
  },
  { sampling: "ideal", angle_axis: "ra", tilt_level: "marginal" },
)

const conSerie = (series: FrameMisurato[]) =>
  ({
    groups: [{ key: "a", name: "M 51", night_date: null, frames: 2, pending: 0 }],
    filters: [{ name: "Ha", passband: "HA", frames: 2 }],
    sets: [],
    series,
  }) as unknown as Misure

function ilFrame(
  series: FrameMisurato[],
  sel: number | null = null,
  tipo: "notte" | "oggetto" = "notte",
) {
  const onSel = vi.fn()
  render(<IlFrame misure={conSerie(series)} scelta={TUTTI} sel={sel} onSel={onSel} tipo={tipo} />)
  const sezione = screen.getByRole("region", { name: t("shot.section") })
  const tessere = [...sezione.querySelectorAll(".al-c-misure-frame__colonna-8")].map(
    (x) => x.textContent,
  )
  return { onSel, sezione, tessere }
}

describe("il frame", () => {
  it("le tessere di un frame misurato, ognuna col suo sotto", () => {
    const { sezione, tessere } = ilFrame([PIENO])
    expect(within(sezione).getByRole("heading").textContent).toBe("Frame 1 di 1 · Ha")
    expect(sezione.textContent).toContain("M 51 · 23:00 · Altitude 54° · Airmass 1,23")
    expect(tessere.slice(0, 8)).toEqual([
      `FWHM2,4″ · 1,3 px${t("measures.sampling.ideal")}`,
      "HFD3,1″ · 1,6 px",
      `Stars950${t("measures.saturated", { n: "21" })}`,
      `Eccentricity0,42${t("measures.axis.ra")}`,
      `SNR36${t("shot.snr.sub")}`,
      `Background900 ADU${t("shot.noise", { n: "12" })}`,
      "Airmass1,23Altitude 54°",
      `Gradient1,2 ${RUMORE}`,
    ])
    expect(tessere[8]).toContain(`Tilt14%${t("shot.tilt.sub")}`)
    expect(tessere[8]).toContain(t("measures.tilt.marginal"))
    expect(tessere.slice(9)).toEqual([
      `Curvature+0,25 px · +0,5″${t("shot.curvature.sub")}`,
      `Tilt · Curvature (FWHM)0,12 · 0,46${t("shot.fwhm.field.sub")}`,
      `SQMSQM 21,3${t("measures.sqm.unit")}`,
    ])
    // scala e sito ci sono: nessuna nota
    expect(sezione.querySelector(".al-c-misure-frame__riga-32")).toBeNull()
    const grande = sezione.querySelector(".al-c-misure-frame__testo-13--grande")
    expect(grande?.textContent).toBe("2,4″ · 1,3 px")
  })

  it("lo SQM col giudizio sul Bortle del sito, o 'senza Bortle del sito' (tavola 358)", () => {
    const giudicato = { ...PIENO, sky_verdict: "brighter" } as FrameMisurato
    const notte = (site_bortle: number | null) =>
      ({ ...conSerie([giudicato]), site_bortle }) as unknown as Misure
    const monta = (m: Misure) => {
      render(<IlFrame misure={m} scelta={TUTTI} sel={null} onSel={vi.fn()} tipo="notte" />)
      const s = screen.getByRole("region", { name: t("shot.section") })
      return [...s.querySelectorAll(".al-c-misure-frame__colonna-8")].at(-1)?.textContent
    }
    // la pillola d'avviso porta il suo segno davanti al testo
    expect(monta(notte(4))).toBe(
      `SQMSQM 21,3${t("measures.sqm.unit")}! ${t("measures.sky.brighter")}`,
    )
    cleanup()
    expect(monta(notte(null))).toBe(
      `SQMSQM 21,3${t("measures.sqm.unit.noSite")}! ${t("measures.sky.brighter")}`,
    )
  })

  it("il gradiente dice verso dove il cielo e' piu' chiaro (tavola 357)", () => {
    const { tessere } = ilFrame([{ ...PIENO, gradient_side: "E" } as FrameMisurato])
    expect(tessere[7]).toBe(`Gradient1,2 ${RUMORE}più chiaro verso est`)
  })

  it("un frame con poco: le quattro tessere fisse, in pixel senza scala, e la sua nota", () => {
    const { sezione, tessere } = ilFrame([frame(1, "measured", { fwhm_px: 1.24 })])
    expect(tessere).toEqual(["FWHM1,2 px", "HFD—", "Stars—", "Background—"])
    expect(sezione.textContent).toContain(t("shot.no.scale"))
    expect(sezione.textContent).toContain("M 51 · 23:00")
    expect(sezione.textContent).not.toContain("Altitude")
  })

  it("con la scala e senza sito, la nota del sito; la curvatura senza secondi d'arco", () => {
    const { sezione, tessere } = ilFrame([
      frame(1, "measured", { fwhm_arcsec: 2, fwhm_px: 1, off_axis_px: -0.3 }),
    ])
    expect(sezione.textContent).toContain(t("shot.no.site"))
    expect(tessere).toContain(`Curvature−0,30 px${t("shot.curvature.sub")}`)
  })

  it("una forma stimata lo dice in nota e sulle tessere della forma", () => {
    const { sezione, tessere } = ilFrame([
      frame(1, "estimated", { fwhm_px: 1.24, eccentricity: 0.5 }, { sampling: "ideal" }),
    ])
    expect(sezione.textContent).toContain(t("shot.estimated.note"))
    expect(sezione.textContent).not.toContain(t("shot.no.scale"))
    expect(tessere[0]).toBe(`FWHM1,2 px${t("shot.estimated")}`)
    expect(tessere[3]).toBe(`Eccentricity0,50${t("shot.estimated")}`)
  })

  it("nell'oggetto l'SNR si confronta anche fra le notti; lo stesso frame senza giudizio del tilt", () => {
    const { tessere } = ilFrame(
      [frame(1, "measured", { snr: 30, hfd_tilt_pct: 10 })],
      null,
      "oggetto",
    )
    expect(tessere).toContain(`SNR30${t("shot.snr.sub.object")}`)
    expect(tessere).toContain(`Tilt10%${t("shot.tilt.sub")}`)
  })

  it("in corso o con troppo poche stelle: niente tessere, la riga che lo dice", () => {
    const { sezione, tessere } = ilFrame([frame(1, "pending", {}), frame(2, "too_few_stars", {})])
    expect(tessere).toEqual([])
    expect(sezione.querySelector(".al-c-misure-frame__riga-30")?.textContent).toBe(
      t("measures.pending"),
    )
    cleanup()
    const poche = ilFrame([frame(2, "too_few_stars", {})])
    expect(poche.sezione.querySelector(".al-c-misure-frame__riga-31")?.textContent).toBe(
      `?${t("shot.few")}`,
    )
    expect(poche.sezione.querySelector(".al-c-misure-frame__riga-30")).toBeNull()
  })

  it("‹ e › girano in tondo; con un frame solo sono spenti", () => {
    const { onSel, sezione } = ilFrame(
      [frame(1, "measured", {}), frame(2, "measured", {}), frame(3, "measured", {})],
      1,
    )
    fireEvent.click(within(sezione).getByRole("button", { name: t("shot.prev") }))
    expect(onSel).toHaveBeenLastCalledWith(3)
    fireEvent.click(within(sezione).getByRole("button", { name: t("shot.next") }))
    expect(onSel).toHaveBeenLastCalledWith(2)
    cleanup()
    const uno = ilFrame([frame(1, "measured", {})])
    expect(within(uno.sezione).getByRole("button", { name: t("shot.prev") })).toHaveProperty(
      "disabled",
      true,
    )
    expect(within(uno.sezione).getByRole("button", { name: t("shot.next") })).toHaveProperty(
      "disabled",
      true,
    )
  })

  it("nessun frame lo dice; un gruppo senza nome si chiama con la chiave", () => {
    const vuoto = ilFrame([])
    expect(within(vuoto.sezione).getByRole("heading").textContent).toBe(t("shot.none"))
    cleanup()
    const ignoto = ilFrame([frame(1, "measured", {}, { group: "zz", start: null } as never)])
    expect(ignoto.sezione.querySelector(".al-c-misure-frame__testo-4")?.textContent).toBe("zz")
  })
})

const stat = (key: string, extra: Record<string, unknown> = {}) => ({
  key,
  unit: "arcsec",
  group: "stars_shape",
  measured: 3,
  median: null,
  q1: null,
  q3: null,
  low: null,
  high: null,
  trend: null,
  verdict: null,
  silent: null,
  ...extra,
})

const set = (group: string | null, filter: string | null, measures: unknown[], frames = 4) => ({
  group,
  filter,
  frames,
  pending: 0,
  differs: [],
  measures,
})

const CONFRONTO = {
  groups: [
    { key: "a", name: "M 51", night_date: null, frames: 4, pending: 0 },
    { key: "b", name: null, night_date: null, frames: 2, pending: 0 },
  ],
  filters: [
    { name: "Ha", passband: "HA", frames: 4 },
    { name: "OIII", passband: "OIII", frames: 2 },
  ],
  sets: [
    set(null, null, [stat("fwhm_arcsec", { low: 2, high: 4, median: 3 })]),
    set("a", null, [stat("fwhm_arcsec", { median: 2.5, q1: 2.2, q3: 2.8 })]),
    set("b", null, [stat("fwhm_arcsec", { median: 3, q1: null, q3: 3.2, measured: 1 })], 2),
    set("a", "Ha", []),
    set("b", "Ha", []),
    set("b", "OIII", []),
  ],
  series: [],
} as unknown as Misure

function confronto(
  misure: Misure = CONFRONTO,
  scelta: Scelta = TUTTI,
  tipo: "notte" | "oggetto" = "notte",
  esiti?: ReadonlyMap<string, EsitoDelGruppo>,
) {
  const onMisura = vi.fn()
  const onOggetto = vi.fn()
  render(
    <AConfronto
      misure={misure}
      scelta={scelta}
      misura="fwhm"
      scelte={["fwhm", "snr", "kept"]}
      onMisura={onMisura}
      onOggetto={onOggetto}
      tipo={tipo}
      esiti={esiti}
    />,
  )
  return { onMisura, onOggetto }
}

describe("a confronto", () => {
  it("una riga per gruppo sulla scala comune: nome, frame misurati, quartili e mediana", () => {
    confronto()
    const sezione = screen.getByRole("region", { name: t("compare.objects") })
    const [a, b] = within(sezione).getAllByRole("link")
    expect(a?.textContent).toBe(`M 51${t("measures.of", { m: "3", n: "4" })}2,5″`)
    expect(b?.textContent).toBe(`b${t("measures.of", { m: "1", n: "2" })}3,0″`)
    const banda = a?.querySelector<HTMLElement>(".al-quartili__banda")
    expect([banda?.style.left, banda?.style.width]).toEqual(["10%", "30%"])
    expect(a?.querySelector<HTMLElement>(".al-quartili__mediana")?.style.left).toBe("25%")
    // senza primo quartile la riga non disegna la banda
    const senza = b?.querySelector<HTMLElement>(".al-quartili__banda")
    expect([senza?.style.left, senza?.style.width]).toEqual(["0%", "0%"])
    expect(b?.querySelector<HTMLElement>(".al-quartili__mediana")?.style.left).toBe("-10%")
    const tinte = [...(b?.querySelectorAll<HTMLElement>(".al-c-misure-frame__tondo-10") ?? [])]
    expect(tinte.map((x) => x.style.background)).toEqual(["var(--filtro-ha)", "var(--filtro-oiii)"])
    expect(sezione.querySelector(".al-c-misure-frame__riga-35")?.textContent).toBe(
      `2,0″${t("compare.scale")}4,0″`,
    )
  })

  it("toccata una riga la sceglie, ritoccata la toglie; la misura cambia dal menu", () => {
    const primo = confronto()
    fireEvent.click(screen.getAllByRole("link")[0] as HTMLElement)
    expect(primo.onOggetto).toHaveBeenLastCalledWith("a")
    fireEvent.change(screen.getByRole("combobox", { name: t("compare.measure") }), {
      target: { value: "snr" },
    })
    expect(primo.onMisura).toHaveBeenLastCalledWith("snr")
    const voci = within(screen.getByRole("combobox")).getAllByRole("option")
    expect(voci.map((o) => o.textContent)).toEqual(["FWHM", "SNR", "HFD Stars"])
    cleanup()
    const scelto = confronto(CONFRONTO, { gruppo: "a", filtro: null })
    const [a, b] = screen.getAllByRole("link")
    expect(a?.getAttribute("aria-pressed")).toBe("true")
    expect(b?.getAttribute("aria-pressed")).toBe("false")
    fireEvent.click(a as HTMLElement)
    expect(scelto.onOggetto).toHaveBeenLastCalledWith(null)
  })

  it("le notti di un oggetto, con l'esito accanto", () => {
    const esiti = new Map([["a", { esito: 2 as const, testo: "da rifare", segno: "!" }]])
    confronto(CONFRONTO, TUTTI, "oggetto", esiti)
    const sezione = screen.getByRole("region", { name: t("compare.nights") })
    expect(within(sezione).getAllByRole("link")[0]?.textContent).toContain("da rifare")
  })

  it("senza scala la FWHM passa ai pixel; senza estremi la scala va da 0 a 1", () => {
    const px = {
      ...CONFRONTO,
      sets: [
        set(null, null, [stat("fwhm_px")]),
        set("a", null, [stat("fwhm_px", { median: 1.5, q1: 1, q3: 2 })]),
      ],
    } as unknown as Misure
    confronto(px)
    const [a] = screen.getAllByRole("link")
    expect(a?.textContent).toContain("1,5 px")
    const banda = a?.querySelector<HTMLElement>(".al-quartili__banda")
    expect([banda?.style.left, banda?.style.width]).toEqual(["100%", "100%"])
    expect(
      screen.getByRole("region").querySelector(".al-c-misure-frame__riga-35")?.textContent,
    ).toBe(`—${t("compare.scale")}—`)
  })

  it("col filtro scelto, la scala e le righe di quel filtro", () => {
    const filtrato = {
      ...CONFRONTO,
      sets: [
        set(null, "Ha", [stat("fwhm_arcsec", { low: 1, high: 3, median: 2 })]),
        set("a", "Ha", [stat("fwhm_arcsec", { median: 1.2, q1: 1.1, q3: 1.3 })]),
        ...CONFRONTO.sets,
      ],
    } as unknown as Misure
    confronto(filtrato, { gruppo: null, filtro: "Ha" })
    expect(screen.getAllByRole("link")[0]?.textContent).toContain("1,2″")
  })
})

describe("per filtro", () => {
  const TABELLA = {
    groups: [],
    filters: [
      { name: "Ha", passband: "HA", frames: 4 },
      { name: "OIII", passband: "OIII", frames: 2 },
    ],
    sets: [
      set(null, "Ha", [
        stat("fwhm_arcsec", { median: 2.44 }),
        stat("fwhm_px", { median: 1.2, verdict: "under", measured: 3 }),
        stat("hfd_px", { median: 1.6, measured: 3 }),
        stat("background_adu", { median: 900 }),
        stat("noise_adu", { median: 12.4 }),
        stat("hfd_tilt_pct", { median: 14, verdict: "nogo" }),
        stat("sqm", { median: 21.3, sky_verdict: "as_site" }),
        stat("kept", { median: 120 }),
      ]),
      set(
        null,
        "OIII",
        [stat("hfd_px", { median: 2, measured: 1 }), stat("noise_adu", { median: 5 })],
        2,
      ),
    ],
    series: [],
  } as unknown as Misure

  function tabella(scelta: Scelta = TUTTI, altra: string | null = null) {
    const onFiltro = vi.fn()
    render(<PerFiltro misure={TABELLA} scelta={scelta} altra={altra} onFiltro={onFiltro} />)
    const t0 = screen.getByRole("table", { name: t("perfilter.table") })
    const righe = within(t0).getAllByRole("row")
    return { onFiltro, t0, righe }
  }

  it("le intestazioni della tavola, piu' l'altra misura scelta", () => {
    const { t0 } = tabella(TUTTI, "kept")
    expect(
      within(t0)
        .getAllByRole("columnheader")
        .map((c) => c.textContent),
    ).toEqual([
      t("perfilter.head.filter"),
      "FWHM",
      "HFD",
      "Eccentricity",
      "SNR",
      "Background",
      "Tilt",
      "Curvature",
      "SQM",
      "HFD Stars",
    ])
    expect(t0.style.minWidth).toBe("748px")
    expect(t0.style.gridTemplateColumns).toBe(
      "minmax(92px, 1.1fr) minmax(84px, 1.3fr) minmax(64px, 1fr) minmax(64px, 1fr) minmax(64px, 1fr) minmax(64px, 1fr) minmax(64px, 1fr) minmax(64px, 1fr) minmax(84px, 1.3fr) minmax(64px, 1fr)",
    )
    cleanup()
    expect(tabella().t0.style.minWidth).toBe("676px")
  })

  it("una riga per filtro: frame misurati, mediane, campionamento, rumore e tilt", () => {
    const { righe } = tabella(TUTTI, "kept")
    const celle = within(righe[1] as HTMLElement)
      .getAllByRole("cell")
      .map((c) => c.textContent)
    expect(celle[0]).toBe(`Ha${t("perfilter.frames", { m: "3", n: "4" })}`)
    expect(celle[1]).toBe(`2,4″${t("measures.sampling.under")}`)
    expect(celle[2]).toBe("1,6 px")
    expect(celle[3]).toBe("—")
    expect(celle[5]).toBe(`900 ADU${t("perfilter.noise", { n: "12" })}`)
    expect(celle[6]).toContain("14%")
    expect(celle[6]).toContain(t("measures.tilt.nogo"))
    expect(celle[8]).toBe(`SQM 21,3✓ ${t("measures.sky.asSite")}`)
    expect(celle[9]).toBe("120")
    const oiii = within(righe[2] as HTMLElement)
      .getAllByRole("cell")
      .map((c) => c.textContent)
    expect(oiii[0]).toBe(`OIII${t("perfilter.frames", { m: "1", n: "2" })}`)
    // rumore senza fondo: niente sotto
    expect(oiii[5]).toBe("—")
    expect(oiii[1]).toBe("—")
  })

  it("toccata una riga sceglie il filtro, ritoccata lo toglie", () => {
    const { onFiltro, righe } = tabella()
    fireEvent.click(righe[2] as HTMLElement)
    expect(onFiltro).toHaveBeenLastCalledWith("OIII")
    cleanup()
    const scelta = tabella({ gruppo: null, filtro: "Ha" })
    expect(scelta.righe[1]?.getAttribute("aria-pressed")).toBe("true")
    expect(scelta.righe[2]?.getAttribute("aria-pressed")).toBe("false")
    fireEvent.click(scelta.righe[1] as HTMLElement)
    expect(scelta.onFiltro).toHaveBeenLastCalledWith(null)
  })
})
