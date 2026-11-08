// @vitest-environment jsdom
/**
 * **Tutto della notte** (`src/TuttoDellaNotte.tsx`, `src/MisureDellaNotte.tsx`): la finestra che
 * il ↗ della protagonista apre sopra le Notti. Scrive cio' che l'API manda: la testa, i setup, gli
 * oggetti col catalogo, le tessere delle misure, il frame, il confronto e la tabella per filtro.
 */
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { type Voce, pulisci } from "./banco"
import { DICIOTTO, apri, notte, pagina, rotte } from "./notti-banco"

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

const insieme = (object_key: string | null, filter: string | null, frames = 2) => ({
  object_key,
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
  objects: [{ key: "m-51", name: "M 51", frames: 2, pending: 0 }],
  filters: [{ name: "Ha", passband: "HA", frames: 2 }],
  sets: [insieme(null, null), insieme("m-51", null), insieme(null, "Ha"), insieme("m-51", "Ha")],
  series: [
    {
      frame_id: 1,
      start: "2024-05-18T23:00:00+02:00",
      object_key: "m-51",
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
      object_key: "m-51",
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
    const ecc = (await within(d).findAllByRole("button", { name: /^Eccentricità/ }))[0]
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
})
