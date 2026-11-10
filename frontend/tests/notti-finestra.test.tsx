// @vitest-environment jsdom
/**
 * **Tutto della notte** (`src/TuttoDellaNotte.tsx`, `src/MisureDellaNotte.tsx`): la finestra che
 * il ↗ della protagonista apre sopra le Notti. Scrive cio' che l'API manda: la testa, i setup, gli
 * oggetti col catalogo, le tessere delle misure, il frame, il confronto e la tabella per filtro.
 */
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { t } from "../src/i18n"
import { distanza, estensione } from "../src/TuttoDellaNotte"
import { type Voce, pulisci } from "./banco"
import { DICIOTTO, apri, chieste, notte, pagina, rotte } from "./notti-banco"

afterEach(pulisci)

const stat = (key: string, unit: string, extra: Record<string, unknown> = {}) => ({
  key,
  unit,
  group: "stars_shape",
  measured: 2,
  median: null,
  q1: null,
  q3: null,
  low: null,
  high: null,
  trend: null,
  verdict: null,
  silent: "no_value",
  ...extra,
})

const val = (median: number, q1: number, q3: number, extra: Record<string, unknown> = {}) => ({
  median,
  q1,
  q3,
  low: q1 - 0.5,
  high: q3 + 0.5,
  silent: null,
  ...extra,
})

const MISURE_TUTTE = [
  stat("hfd_px", "px", val(1.6, 1.5, 1.7)),
  stat("fwhm_px", "px", val(1.2, 1.1, 1.3, { verdict: "under" })),
  stat("fwhm_arcsec", "arcsec", val(2.4, 2.2, 2.6)),
  stat("snr", "ratio", val(36, 30, 40)),
  stat("hfd_tilt_pct", "pct", val(14, 12, 16, { verdict: "marginal" })),
  stat("background_adu", "adu", val(900, 880, 920)),
  stat("eccentricity", "ratio"),
]

const insieme = (group: string | null, filter: string | null, frames = 2) => ({
  group,
  filter,
  frames,
  pending: 0,
  differs: [],
  measures: MISURE_TUTTE,
})

const MISURE = {
  night_id: 7,
  timezone: "Europe/Rome",
  frames: 2,
  pending: 0,
  groups: [{ key: "m-51", name: "M 51", night_date: null, frames: 2, pending: 0 }],
  filters: [{ name: "Ha", passband: "HA", frames: 2 }],
  sets: [insieme(null, null), insieme("m-51", null), insieme(null, "Ha"), insieme("m-51", "Ha")],
  series: [
    {
      frame_id: 1,
      start: "2024-05-18T23:00:00+02:00",
      group: "m-51",
      filter: "Ha",
      state: "measured",
      tilt_level: "go",
      sampling: "ideal",
      angle_axis: "ra",
      values: {
        fwhm_arcsec: 2.4,
        fwhm_px: 1.2,
        hfd_px: 1.6,
        stars: 1500,
        saturated: 21,
        eccentricity: 0.42,
        hfd_tilt_pct: 8,
      },
    },
    {
      frame_id: 2,
      start: "2024-05-18T23:05:00+02:00",
      group: "m-51",
      filter: "Ha",
      state: "too_few_stars",
      tilt_level: null,
      sampling: null,
      angle_axis: null,
      values: {},
    },
  ],
}

const DETTAGLIO = {
  night: DICIOTTO,
  first_start: "2024-05-18T23:00:00+02:00",
  last_end: "2024-05-19T01:30:00+02:00",
  rigs: [
    {
      id: 3,
      name: "Notte in quota",
      optics: "Askar FRA400",
      camera: "ZWO ASI2600MM Pro",
      focal_mm: 400,
      scale_arcsec_px: 1.94,
      width_deg: 3.4,
      height_deg: 2.2,
      parts: [
        { kind: "mount", id: 4, name: "EQ6-R Pro", frames: 3, chosen: false },
        { kind: "spacer", id: 5, name: "Distanziale 10 mm", frames: 3, chosen: false },
      ],
      frames: 3,
      integration_s: 10800,
      untimed: 0,
    },
  ],
  objects: [
    {
      key: "m-51",
      common_name: "Galassia Vortice",
      type_code: "GALAXY",
      constellation: "CVn",
      distance: { value: 23.0, unit: "million_ly" },
      extent_ly: 76000,
    },
  ],
}

const FINESTRA: Record<string, Voce> = {
  "/api/v1/nights/7/measures": { stato: 200, corpo: MISURE },
  "/api/v1/nights/7": { stato: 200, corpo: DETTAGLIO },
}

async function finestra(prima = FINESTRA) {
  await apri(rotte(pagina([DICIOTTO]), prima))
  const carta = await notte()
  fireEvent.click(within(carta).getByRole("link", { name: "Tutto della notte" }))
  return screen.findByRole("dialog", { name: "Tutto della notte" })
}

describe("la finestra della notte", () => {
  it("il ↗ della protagonista la apre: data, ore della ripresa nel fuso del sito, misure in testa", async () => {
    const d = await finestra()
    const testa = await within(d).findByRole("region", { name: "Riepilogo" })
    expect(within(testa).getByText("Sabato 18 maggio 2024")).toBeTruthy()
    expect(within(testa).getByText("Cima Ekar · dalle 23:00 alle 01:30")).toBeTruthy()
    expect(within(testa).getByText("3 h")).toBeTruthy()
    expect(await within(testa).findByText("2,4″")).toBeTruthy()
    expect(within(testa).getByText("36")).toBeTruthy()
  })

  it("il setup col suo nome e i pezzi, chiusi ai quattro della tavola", async () => {
    const d = await finestra()
    const setup = await within(d).findByRole("region", { name: "Setup" })
    expect(within(setup).getByText("Notte in quota")).toBeTruthy()
    expect(within(setup).getByText("Askar FRA400, 400 mm")).toBeTruthy()
    expect(within(setup).getByText("EQ6-R Pro")).toBeTruthy()
    expect(within(setup).getByText("3,4° × 2,2° · 1,94″/px")).toBeTruthy()
    // il distanziale prende in prestito l'icona del campo, non il suo posto fra i quattro
    expect(within(setup).queryByText("Distanziale 10 mm")).toBeNull()
    fireEvent.click(within(setup).getByRole("link", { name: /Tutti gli strumenti/ }))
    expect(within(setup).getByText("Distanziale 10 mm")).toBeTruthy()
  })

  it("piu' setup: in lettere fino a nove, poi in cifre", async () => {
    const rig = DETTAGLIO.rigs[0]
    for (const [n, nome] of [
      [3, "Tre setup"],
      [9, "Nove setup"],
      [10, "10 setup"],
    ] as const) {
      const rigs = Array.from({ length: n }, (_, i) => ({ ...rig, id: i + 1 }))
      const corpo = { ...DETTAGLIO, rigs }
      const d = await finestra({ ...FINESTRA, "/api/v1/nights/7": { stato: 200, corpo } })
      const setup = await within(d).findByRole("region", { name: "Setup" })
      expect(within(setup).getByText(nome)).toBeTruthy()
      pulisci()
    }
  })

  it("gli oggetti dicono tipo, costellazione, distanza ed estensione dal catalogo", async () => {
    const d = await finestra()
    const ogg = await within(d).findByRole("region", { name: "Gli oggetti" })
    expect(within(ogg).getByText("Galassia Vortice")).toBeTruthy()
    expect(within(ogg).getByText("23 milioni di anni luce")).toBeTruthy()
    // lo spazio sottile delle migliaia: la libreria lo normalizza in uno spazio
    expect(within(ogg).getByText("circa 76 000 anni luce")).toBeTruthy()
  })

  it("gli oggetti si chiamano col nome, non con la chiave, anche a confronto e isolati", async () => {
    const d = await finestra()
    const ogg = await within(d).findByRole("region", { name: "Gli oggetti" })
    expect(within(ogg).getByText("M 51")).toBeTruthy()
    expect(within(d).queryByText("m-51")).toBeNull()
    const confronto = await within(d).findByRole("region", { name: "Gli oggetti a confronto" })
    fireEvent.click(within(confronto).getByText("M 51"))
    expect(within(d).getByRole("button", { name: "solo M 51 ×" })).toBeTruthy()
  })

  it("il nome di un oggetto apre la sua finestra al posto di quella della notte", async () => {
    const d = await finestra()
    const ogg = await within(d).findByRole("region", { name: "Gli oggetti" })
    fireEvent.click(within(ogg).getByRole("link", { name: "M 51" }))
    expect(await screen.findByRole("dialog", { name: "Riepilogo: M 51" })).toBeTruthy()
    // una finestra sola: due insieme chiuderebbero insieme con lo stesso Esc
    expect(screen.queryByRole("dialog", { name: "Tutto della notte" })).toBeNull()
    expect(chieste("/api/v1/objects/m-51").length).toBeGreaterThan(0)
  })

  it("Esc la chiude", async () => {
    await finestra()
    fireEvent.keyDown(document, { key: "Escape" })
    expect(screen.queryByRole("dialog")).toBeNull()
  })

  it("una notte che non c'e' piu' lo dice", async () => {
    const d = await finestra({
      ...FINESTRA,
      "/api/v1/nights/7": { stato: 404, corpo: { detail: "night_not_found" } },
    })
    expect(await within(d).findByText("Notte non trovata")).toBeTruthy()
  })
})

describe("le misure della notte", () => {
  it("la tessera della FWHM in secondi d'arco e pixel, col campionamento della mediana", async () => {
    const d = await finestra()
    const tessera = (await within(d).findAllByRole("button", { name: /^FWHM/ }))[0]
    expect(tessera?.textContent).toContain("2,4″ · 1,2 px")
    expect(tessera?.textContent).toContain("sottocampionata")
  })

  it("una tessera senza valore dice perche', dall'API", async () => {
    const d = await finestra()
    const ecc = (await within(d).findAllByRole("button", { name: /^Eccentricity/ }))[0]
    expect(ecc?.textContent).toContain("non c’è per questi frame")
  })

  it("il tilt porta il giudizio della mediana scritto dall'API", async () => {
    const d = await finestra()
    const tilt = (await within(d).findAllByRole("button", { name: /^Tilt/ }))[0]
    expect(tilt?.textContent).toContain("14%")
    expect(tilt?.textContent).toContain("incerto")
  })

  it("il frame scelto e' il primo misurato; › va al successivo, che ha troppo poche stelle", async () => {
    const d = await finestra()
    const frame = await within(d).findByRole("region", { name: "Il frame" })
    expect(within(frame).getByRole("heading").textContent).toBe("Frame 1 di 2 · Ha")
    expect(within(frame).getByText("in AR")).toBeTruthy()
    fireEvent.click(within(frame).getByRole("button", { name: "Frame dopo" }))
    expect(within(frame).getByRole("heading").textContent).toBe("Frame 2 di 2 · Ha")
    expect(within(frame).getByText("troppo poche stelle")).toBeTruthy()
  })

  it("a confronto, senza scala, la FWHM passa ai pixel", async () => {
    const senza = MISURE_TUTTE.filter((s) => s.key !== "fwhm_arcsec")
    const corpo = { ...MISURE, sets: MISURE.sets.map((s) => ({ ...s, measures: senza })) }
    const d = await finestra({ ...FINESTRA, "/api/v1/nights/7/measures": { stato: 200, corpo } })
    const confronto = await within(d).findByRole("region", { name: "Gli oggetti a confronto" })
    expect(within(confronto).getByText("1,2 px")).toBeTruthy()
  })

  it("una riga per filtro sceglie quel filtro, e si toglie toccandola di nuovo", async () => {
    const d = await finestra()
    const tabella = await within(d).findByRole("table", { name: "Mediane per filtro" })
    const riga = within(tabella).getAllByRole("row")[1]
    if (!riga) throw new Error("manca la riga del filtro")
    fireEvent.click(riga)
    expect(riga.getAttribute("aria-pressed")).toBe("true")
    expect(within(d).getByRole("radio", { name: /Ha/ }).getAttribute("aria-checked")).toBe("true")
  })

  it("fondo di piu' filtri dice «per filtro» quando lo dice l'API", async () => {
    const misure = MISURE_TUTTE.map((s) =>
      s.key === "background_adu" ? { ...s, per_filter: true } : s,
    )
    const corpo = { ...MISURE, sets: MISURE.sets.map((s) => ({ ...s, measures: misure })) }
    const d = await finestra({ ...FINESTRA, "/api/v1/nights/7/measures": { stato: 200, corpo } })
    const fondo = (await within(d).findAllByRole("button", { name: /^Background/ }))[0]
    expect(fondo?.textContent).toContain("si confronta per filtro")
  })

  it("le altre misure hanno il nome tecnico dei programmi, anche quelle che la tavola non nomina", async () => {
    const d = await finestra()
    const menu = await within(d).findByRole("combobox", { name: "Altre misure" })
    const voci = within(menu)
      .getAllByRole("option")
      .map((o) => o.textContent)
    for (const nome of ["PSF Signal Weight", "PSF SNR", "Trails", "HFD Stars", "Altitude"])
      expect(voci).toContain(nome)
    expect(voci).not.toContain("Peso del segnale · PSF Signal Weight")
  })
})

const ANGOLI = [
  stat("hfd_corner_1_px", "px", val(3.1, 3.0, 3.2)),
  stat("hfd_corner_2_px", "px", val(3.2, 3.1, 3.3)),
  stat("hfd_corner_3_px", "px", val(3.3, 3.2, 3.4)),
  stat("hfd_corner_4_px", "px", val(3.4, 3.3, 3.5)),
  stat("hfd_centre_px", "px", val(3.0, 2.9, 3.1)),
  stat("off_axis_px", "px", val(0.25, 0.2, 0.3)),
]

function conMisure(misure: unknown[], series: unknown[] = MISURE.series): Record<string, Voce> {
  const corpo = { ...MISURE, series, sets: MISURE.sets.map((s) => ({ ...s, measures: misure })) }
  return { ...FINESTRA, "/api/v1/nights/7/measures": { stato: 200, corpo } }
}

describe("frame per frame e tilt e curvatura", () => {
  it("un grafico per filtro con le due misure scelte, e i segni dei frame senza misura", async () => {
    const d = await finestra()
    const grafici = await within(d).findByRole("region", { name: "I grafici" })
    expect(
      within(grafici).getByRole("img", { name: "Ha: FWHM e Eccentricity di 2 frame" }),
    ).toBeTruthy()
    expect(within(grafici).getAllByText("troppo poche stelle").length).toBeGreaterThan(0)
    // senza altezza della Luna e senza zenit, i loro comandi non ci sono
    expect(within(grafici).queryByRole("switch")).toBeNull()
    expect(within(grafici).queryByRole("combobox", { name: "Valore" })).toBeNull()
  })

  it("i frame senza filtro hanno pillola, riga per filtro e grafico col loro nome", async () => {
    const corpo = {
      ...MISURE,
      filters: [{ name: "__no_filter__", passband: "UNKNOWN", frames: 2 }],
      sets: [
        insieme(null, null),
        insieme("m-51", null),
        insieme(null, "__no_filter__"),
        insieme("m-51", "__no_filter__"),
      ],
      series: MISURE.series.map((f) => ({ ...f, filter: "__no_filter__" })),
    }
    const d = await finestra({ ...FINESTRA, "/api/v1/nights/7/measures": { stato: 200, corpo } })
    expect(await within(d).findByRole("radio", { name: /Filtro non indicato/ })).toBeTruthy()
    const tabella = within(d).getByRole("table", { name: "Mediane per filtro" })
    expect(within(tabella).getByText("Filtro non indicato")).toBeTruthy()
    const grafici = within(d).getByRole("region", { name: "I grafici" })
    expect(
      within(grafici).getByRole("img", {
        name: "Filtro non indicato: FWHM e Eccentricity di 2 frame",
      }),
    ).toBeTruthy()
    expect(within(d).queryByText("__no_filter__")).toBeNull()
  })

  it("con la Luna e lo zenit nei dati compaiono i loro comandi", async () => {
    const zenit = stat("fwhm_zenith_arcsec", "arcsec", val(2.0, 1.9, 2.1))
    const series = MISURE.series.map((f) => ({
      ...f,
      values: { ...f.values, moon_altitude_deg: 20 },
    }))
    const d = await finestra(conMisure([...MISURE_TUTTE, zenit], series))
    const grafici = await within(d).findByRole("region", { name: "I grafici" })
    expect(
      within(grafici).getByRole("switch", { name: "Accendi la Luna nei grafici" }),
    ).toBeTruthy()
    expect(within(grafici).getByRole("combobox", { name: "Valore" })).toBeTruthy()
  })

  it("oltre le barre che ci stanno, la finestra dei frame", async () => {
    const molti = Array.from({ length: 200 }, (_, i) => ({
      ...MISURE.series[0],
      frame_id: i + 1,
    })) as typeof MISURE.series
    const d = await finestra(conMisure(MISURE_TUTTE, molti))
    const grafici = await within(d).findByRole("region", { name: "I grafici" })
    const slider = within(grafici).getByRole("slider", { name: "Tratto dei frame in vista" })
    expect(slider.getAttribute("aria-valuetext")).toBe("frame 1–182 di 200")
  })

  it("nella finestra dei frame, l'oggetto senza chiave non si chiama come un filtro", async () => {
    const molti = Array.from({ length: 200 }, (_, i) => ({
      ...MISURE.series[0],
      frame_id: i + 1,
      group: i < 100 ? "m-51" : null,
    })) as unknown as typeof MISURE.series
    const d = await finestra(conMisure(MISURE_TUTTE, molti))
    const grafici = await within(d).findByRole("region", { name: "I grafici" })
    expect(within(grafici).getByRole("button", { name: "M 51" })).toBeTruthy()
    expect(
      within(grafici).getByRole("button", { name: "Nessun oggetto identificato" }),
    ).toBeTruthy()
    expect(within(grafici).queryByRole("button", { name: "Filtro non indicato" })).toBeNull()
  })

  it("il sensore dalle mediane degli angoli e del centro, col giudizio del tilt", async () => {
    const d = await finestra(conMisure([...MISURE_TUTTE, ...ANGOLI]))
    const sezione = await within(d).findByRole("region", { name: "Tilt e curvatura di campo" })
    const sensore = within(sezione).getByRole("img")
    expect(sensore.getAttribute("aria-label")).toBe(
      "HFD agli angoli 3,1 px / 3,2 px / 3,3 px / 3,4 px, al centro 3,0 px: tilt 14%, curvatura +0,25 px",
    )
    expect(sezione.textContent).toContain("incerto")
    expect(within(sezione).getByText("Tilt 14% · Curvature +0,25 px")).toBeTruthy()
  })

  it("senza le HFD degli angoli il sensore dice che non c'e'", async () => {
    const d = await finestra()
    const sezione = await within(d).findByRole("region", { name: "Tilt e curvatura di campo" })
    expect(within(sezione).queryByRole("img")).toBeNull()
    expect(within(sezione).getByText("non c’è per questi frame")).toBeTruthy()
  })
})

describe("la testa e gli oggetti, quando i dati mancano", () => {
  const conDettaglio = (corpo: unknown): Record<string, Voce> => ({
    ...FINESTRA,
    "/api/v1/nights/7": { stato: 200, corpo },
  })

  it("una notte senza ore dice i frame e che i file non hanno l'ora", async () => {
    const night = { ...DICIOTTO, integration_s: 0, frames: 4 }
    const corpo = { ...DETTAGLIO, night, first_start: null, last_end: null }
    const d = await finestra(conDettaglio(corpo))
    const testa = await within(d).findByRole("region", { name: "Riepilogo" })
    expect(within(testa).getByText(t("window.span.untimed", { sito: "Cima Ekar" }))).toBeTruthy()
    expect(within(testa).getByText(t("window.frames", { n: "4" }))).toBeTruthy()
    expect(within(testa).getByText(t("window.untimed"))).toBeTruthy()
  })

  it("con le ore, sotto le ore i frame e gli oggetti", async () => {
    const d = await finestra()
    const testa = await within(d).findByRole("region", { name: "Riepilogo" })
    expect(
      within(testa).getByText(
        `${t("window.frames", { n: "3" })} · ${t("window.objects", { n: 1 })}`,
      ),
    ).toBeTruthy()
  })

  it("un oggetto fuori catalogo lo dice e non ha dati; senza ore, i suoi frame", async () => {
    const night = {
      ...DICIOTTO,
      objects: [
        { key: "ngc-x", name: null, frames: 5, integration_s: 0, untimed: 5, bar_pct: 100 },
      ],
    }
    const d = await finestra(conDettaglio({ ...DETTAGLIO, night }))
    const ogg = await within(d).findByRole("region", { name: "Gli oggetti" })
    expect(within(ogg).getByText("ngc-x")).toBeTruthy()
    expect(within(ogg).getByText(t("window.objects.outside"))).toBeTruthy()
    expect(within(ogg).getByText(t("window.frames", { n: "5" }))).toBeTruthy()
    expect(within(ogg).queryByText(t("window.fact.type"))).toBeNull()
  })

  it("nel catalogo con la sola distanza: in anni luce, il resto non noto", async () => {
    const objects = [
      {
        key: "m-51",
        common_name: null,
        type_code: null,
        constellation: null,
        distance: { value: 900, unit: "ly" },
        extent_ly: null,
      },
    ]
    const d = await finestra(conDettaglio({ ...DETTAGLIO, objects }))
    const ogg = await within(d).findByRole("region", { name: "Gli oggetti" })
    expect(within(ogg).getByText(t("window.fact.ly", { n: "900" }))).toBeTruthy()
    expect(within(ogg).getByText(t("window.fact.extent.none"))).toBeTruthy()
    expect(within(ogg).getAllByText("—")).toHaveLength(2)
    expect(within(ogg).queryByText(t("window.objects.outside"))).toBeNull()
  })

  it("le misure che non arrivano lo dicono, col bottone per riprovare", async () => {
    const d = await finestra({
      ...FINESTRA,
      "/api/v1/nights/7/measures": { stato: 500, corpo: { detail: "boom" } },
    })
    expect(await within(d).findByText(t("window.failed"))).toBeTruthy()
    expect(within(d).getByRole("button", { name: t("window.retry") })).toBeTruthy()
  })

  it("la x la chiude, e cosi' un tocco fuori dal pannello", async () => {
    const d = await finestra()
    // v77: loading has its own x; wait for the head, or the click lands on a node already gone
    await within(d).findByRole("region", { name: "Riepilogo" })
    fireEvent.click(within(d).getByRole("link", { name: t("ui.close") }))
    expect(screen.queryByRole("dialog")).toBeNull()
    const ancora = await finestra()
    fireEvent.click(await within(ancora).findByRole("region", { name: "Riepilogo" }))
    expect(screen.queryByRole("dialog")).toBeTruthy()
    fireEvent.click(ancora)
    expect(screen.queryByRole("dialog")).toBeNull()
  })
})

describe("distanza ed estensione", () => {
  const fatti = (extra: Record<string, unknown>) =>
    ({ key: "x", distance: null, extent_ly: null, ...extra }) as never

  it("in anni luce o in milioni, o non nota", () => {
    expect(distanza(fatti({ distance: { value: 900, unit: "ly" } }))).toBe(
      t("window.fact.ly", { n: "900" }),
    )
    expect(distanza(fatti({ distance: { value: 23, unit: "million_ly" } }))).toBe(
      t("window.fact.mly", { n: "23" }),
    )
    expect(distanza(fatti({}))).toBe(t("window.fact.distance.none"))
    expect(estensione(fatti({ extent_ly: 0 }))).toBe(t("window.fact.extent.value", { n: "0" }))
    expect(estensione(fatti({}))).toBe(t("window.fact.extent.none"))
  })
})
