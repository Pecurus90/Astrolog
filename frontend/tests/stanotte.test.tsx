// @vitest-environment jsdom
/**
 * Stanotte nel telaio v76 (tavola `Telaio`, pastiglia v70): la pastiglia dice il sito e apre il
 * pannello con il sito, la Luna e il meteo della notte.
 *
 * Qui si provano le regole che una lettura del codice non prende: che ogni vuoto diventi una
 * frase, che l'ora sia quella del sito e non del browser, che la frase della Luna venga dai campi
 * del backend, e che senza sito si vada ad aggiungerlo.
 */
// Il fuso della macchina si fissa **prima** che qualcuno legga una data: su un computer a +02:00
// l'ora del sito e quella del browser sarebbero lo stesso numero, e il difetto passerebbe verde.
process.env.TZ = "UTC"

import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { rileggiOgni } from "../src/Stanotte"
import { FERMO, SALUTE, SITO_DI_CASA, STANOTTE, disegna, impostazioni, pulisci, rispondi } from "./banco"

afterEach(pulisci)

const LUNA = {
  phase_key: "waxing_gibbous",
  illumination_pct: 62,
  rise: "2026-09-30T23:40:26+02:00",
  set: "2026-10-01T14:48:58+02:00",
  highest: { at: "2026-10-01T05:30:00+02:00", altitude_deg: 64 },
  track: [],
  ceiling_deg: 75,
  lit_side: "right",
}

const NOTTE = {
  night: "2026-09-30",
  site: { name: "Cima Ekar", sky_sqm: 21.4, bortle: 3 },
  moon: LUNA,
  sky_bands: [],
  planets: [],
  shooting: [],
  chart: {
    starts_at: "2026-09-30T18:30:00+02:00",
    ends_at: "2026-10-01T07:30:00+02:00",
    dark_from: "2026-09-30T20:48:00+02:00",
    dark_until: "2026-10-01T05:48:00+02:00",
  },
  moonless_dark: [{ starts_at: "2026-09-30T20:48:00+02:00", ends_at: "2026-09-30T23:40:00+02:00" }],
  moon_in_dark: {
    level: "marginal",
    since: "2026-09-30T23:40:00+02:00",
    until: "2026-10-01T05:48:00+02:00",
    from_start: false,
    to_end: true,
  },
  weather: {
    verdict: "go",
    cloud_total_pct: 10,
    usable_hours: 7,
    window: "dark",
    window_hours: 9,
    exposure_hours: 7.5,
    agreement: { go: 3, marginal: 1, nogo: 0, unknown: 0, total: 4 },
    wind_700hpa_kmh: 30,
    wind_700hpa_tenths: 6,
  },
}

function app(stanotte: Record<string, unknown>, formato = "") {
  if (formato) window.history.pushState({}, "", `/?formato=${formato}`)
  rispondi({
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0, sections: [] } },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/pipeline/status": { stato: 200, corpo: FERMO },
    "/api/v1/tonight": { stato: 200, corpo: { ...NOTTE, ...stanotte } },
    "/api/v1/sites": { stato: 200, corpo: { items: [SITO_DI_CASA], total: 1, limit: 50, offset: 0 } },
  })
  return disegna()
}

/** Apre Stanotte dalla pastiglia, come chi usa l'app, e torna il pannello. */
async function apri(nome: RegExp) {
  fireEvent.click(await screen.findByRole("link", { name: nome }))
  return screen.findByRole("dialog", { name: "Stanotte" })
}

/** Le righe del pannello: etichetta, valore, riga sotto. */
function righe(pannello: HTMLElement) {
  return [...pannello.querySelectorAll(".al-c-telaio__notte-riga")].map((r) => [
    r.querySelector(".al-c-telaio__notte-l")?.textContent,
    r.querySelector(".al-c-telaio__notte-v b")?.textContent,
    r.querySelector(".al-c-telaio__notte-s")?.textContent,
  ])
}

describe("la pastiglia", () => {
  it("dice Stanotte e il sito, e apre il pannello", async () => {
    await app({})
    const pastiglia = await screen.findByRole("link", { name: "Stanotte a Cima Ekar: sito, Luna e meteo" })
    expect(pastiglia.textContent).toBe("StanotteCima Ekar▾")
    // v78: a long name gets the dots, the whole name in the title; the arrow apart
    const sito = pastiglia.querySelector(".al-c-telaio__stanotte-sito")
    expect(sito?.textContent).toBe("Cima Ekar")
    expect(sito?.getAttribute("title")).toBe("Cima Ekar")
    expect(pastiglia.querySelector(".al-c-telaio__stanotte-giu")?.getAttribute("aria-hidden")).toBe("true")
    expect(pastiglia.getAttribute("aria-haspopup")).toBe("dialog")
    expect(pastiglia.getAttribute("aria-expanded")).toBe("false")
    expect(screen.queryByRole("dialog", { name: "Stanotte" })).toBeNull()

    fireEvent.click(pastiglia)
    expect(pastiglia.getAttribute("aria-expanded")).toBe("true")
    expect(await screen.findByRole("dialog", { name: "Stanotte" })).toBeDefined()
  })

  it("senza sito porta ad aggiungerlo", async () => {
    await app({ night: null, site: null, moon: null, chart: null, moonless_dark: [], moon_in_dark: null, weather: null })
    const pastiglia = await screen.findByRole("link", { name: "Nessun sito: aggiungine uno nelle Impostazioni" })
    expect(pastiglia.textContent).toBe("Aggiungi sito")
    expect(pastiglia.getAttribute("href")).toBe("/impostazioni/sito")
  })

  it("Esc chiude Stanotte e il fuoco torna alla pastiglia; un clic fuori la chiude", async () => {
    await app({})
    const pannello = await apri(/^stanotte a cima ekar/i)
    const pastiglia = screen.getByRole("link", { name: /^stanotte a cima ekar/i })
    const cambia = within(pannello).getByRole("link", { name: "Cambia ↗" })
    cambia.focus()
    fireEvent.keyDown(cambia, { key: "Escape" })
    expect(screen.queryByRole("dialog", { name: "Stanotte" })).toBeNull()
    await waitFor(() => expect(document.activeElement).toBe(pastiglia))

    fireEvent.click(pastiglia)
    await screen.findByRole("dialog", { name: "Stanotte" })
    fireEvent.mouseDown(document.body)
    expect(screen.queryByRole("dialog", { name: "Stanotte" })).toBeNull()
  })
})

describe("il pannello di Stanotte", () => {
  it("dice la notte, il sito col suo cielo, la Luna e il meteo, con l'ora del sito", async () => {
    // 23:40 e' l'ora a Cima Ekar: la macchina sta su UTC, quindi passando da Date direbbe 21:40.
    await app({})
    const pannello = await apri(/^stanotte a cima ekar/i)
    expect(pannello.querySelector(".al-c-telaio__notte-tit")?.textContent).toBe("Stanotte · mercoledì 30 settembre")
    expect(righe(pannello)).toEqual([
      ["Sito", "Cima Ekar", "Bortle 3 · il sito predefinito"],
      ["Luna", "◐ 62% · sorge alle 23:40", "dopo le 23:40 la banda larga è al limite"],
      ["Meteo", "✓ notte buona · 7,5 ore di posa", "buio 20:48–05:48 · senza Luna 20:48–23:40"],
    ])
    expect(within(pannello).getByRole("link", { name: "Cambia ↗" }).getAttribute("href")).toBe("/impostazioni/sito")
    expect(within(pannello).getByRole("link", { name: "Meteo ↗" }).getAttribute("href")).toBe("/meteo")
    expect(within(pannello).getByRole("link", { name: "Apri il Meteo ↗" }).getAttribute("href")).toBe("/meteo")
    expect(within(pannello).getByRole("link", { name: "Piano della notte ↗" }).getAttribute("href")).toBe("/piano-della-notte")
    // i dati sono veri: la riga della tavola "dati simulati" non c'e'
    expect(within(pannello).queryByText(/simulati/)).toBeNull()
  })

  const BUIO = { since: "2026-09-30T21:10:00+02:00", until: "2026-10-01T02:30:00+02:00" }
  it.each([
    [{ level: "marginal", ...BUIO, from_start: false, to_end: true }, "dopo le 21:10 la banda larga è al limite"],
    [{ level: "marginal", ...BUIO, from_start: true, to_end: false }, "fino alle 02:30 la banda larga è al limite"],
    [{ level: "marginal", ...BUIO, from_start: false, to_end: false }, "dalle 21:10 alle 02:30 la banda larga è al limite"],
    [{ level: "marginal", ...BUIO, from_start: true, to_end: true }, "tutta la notte la banda larga è al limite"],
    [{ level: "nogo", ...BUIO, from_start: false, to_end: true }, "dopo le 21:10 consigliata banda stretta"],
    [{ level: "nogo", ...BUIO, from_start: true, to_end: true }, "tutta la notte consigliata banda stretta"],
    [{ level: "go", ...BUIO, from_start: false, to_end: true }, "la Luna non disturba la banda larga"],
    [null, "col buio la Luna non c'è"],
  ])("la Luna nel buio %j si dice: %s", async (nelBuio, frase) => {
    await app({ moon_in_dark: nelBuio })
    const pannello = await apri(/^stanotte a cima ekar/i)
    expect(righe(pannello)[1]?.[2]).toBe(frase)
  })

  it("una Luna che non sorge lo dice a parole", async () => {
    await app({ moon: { ...LUNA, rise: null } })
    expect(righe(await apri(/^stanotte a cima ekar/i))[1]?.[1]).toBe("◐ 62% · non sorge")
  })

  it("un sito col fuso irriconoscibile si legge lo stesso, e dice cosa manca", async () => {
    await app({ night: null, moon: null, chart: null, moonless_dark: [], moon_in_dark: null, weather: null })
    const pannello = await apri(/^stanotte a cima ekar/i)
    expect(pannello.querySelector(".al-c-telaio__notte-tit")?.textContent).toBe("Stanotte")
    expect(righe(pannello)[1]?.[1]).toBe("Fuso orario del sito non riconosciuto: Luna non calcolabile.")
  })

  it("un cielo mai dichiarato si legge, non sparisce", async () => {
    await app({ site: { name: "Passo Giau", sky_sqm: null, bortle: null } })
    expect(righe(await apri(/^stanotte a passo giau/i))[0]?.[2]).toBe("Bortle non indicato · il sito predefinito")
  })

  it("senza la previsione lo dice; una notte incerta e una senza ore di posa pure", async () => {
    await app({ weather: null })
    expect(righe(await apri(/^stanotte a cima ekar/i))[2]?.[1]).toBe("Previsione non disponibile. Dettagli nella pagina Meteo.")
    pulisci()

    await app({ weather: { ...NOTTE.weather, verdict: "marginal", exposure_hours: 0 } })
    expect(righe(await apri(/^stanotte a cima ekar/i))[2]?.[1]).toBe("! notte incerta · nessuna ora di posa")
  })

  it("se stanotte non si legge lo dice, invece di restare vuoto", async () => {
    rispondi({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0, sections: [] } },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/pipeline/status": { stato: 200, corpo: FERMO },
      "/api/v1/tonight": { stato: 500, corpo: {} },
    })
    await disegna()
    const pannello = await apri(/^stanotte$/i)
    expect((await within(pannello).findByRole("status")).textContent).toContain("Dati di stanotte non disponibili.")
  })
})

describe("Stanotte sul telefono", () => {
  it("il titolo della pagina apre Stanotte sotto la testa", async () => {
    await app({}, "telefono")
    const titolo = await screen.findByRole("link", { name: "Dashboard · Stanotte a Cima Ekar: sito, Luna e meteo" })
    expect(titolo.textContent).toBe("DashboardCima Ekar▾")
    expect(titolo.querySelector("span[title='Cima Ekar']")?.textContent).toBe("Cima Ekar▾")
    fireEvent.click(titolo)
    const pannello = await screen.findByRole("dialog", { name: "Stanotte" })
    expect(pannello.className).toBe("al-c-telaio__notte al-c-telaio__notte--tel")
  })
})

describe("quando Stanotte si rilegge da sola", () => {
  it("spesso solo mentre la previsione di una notte che si divide non e' arrivata", () => {
    expect(rileggiOgni({ moon: LUNA, weather: null })).toBe(5 * 60 * 1000)
    expect(rileggiOgni({ moon: LUNA, weather: { verdict: "go" } })).toBe(false)
    expect(rileggiOgni({ moon: null, weather: null })).toBe(false)
    expect(rileggiOgni(undefined)).toBe(false)
  })
})
