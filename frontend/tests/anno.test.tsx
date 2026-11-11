// @vitest-environment jsdom
/**
 * L'**anno** della Dashboard (tavola v79): «Il 2026, fino a oggi» con una barra per mese e il 2025
 * tratteggiato, e «Filtri del 2026» con l'anello. I conti arrivano da `/year`, gia' fatti.
 */
import { screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { pulisci } from "./banco"
import { montaDashboard } from "./dashboard-banco"

afterEach(pulisci)
afterEach(() => vi.unstubAllGlobals())

const MESI = Array.from({ length: 12 }, (_, i) => ({
  month: i + 1,
  integration_s: i === 8 ? 52800 : 0,
  previous_s: 0,
  bar: i === 2 ? 1 : i === 8 ? 0.5 : 0,
  previous_bar: i === 3 ? 0.25 : 0,
  current: i === 8,
  future: i > 8,
}))

/** Il 2026 fino al 30 settembre, come la tavola: 128 h 40 in 41 notti, il 2025 a 131 h. */
function anno(altro: Record<string, unknown> = {}) {
  return {
    year: 2026, until: "2026-09-30", nights: 41, integration_s: 463200, per_night_s: 11280, per_month: 4.6,
    months: MESI, previous_same_period_s: 471600, previous_known: true, vs_previous_s: -8400,
    filters: [
      { name: "Hα", passband: "HA", integration_s: 166800, share_pct: 36, ring_from: 0, ring_to: 36.01 },
      { name: "OIII", passband: "OIII", integration_s: 137400, share_pct: 30, ring_from: 36.01, ring_to: 65.67 },
      { name: "__no_filter__", passband: "UNKNOWN", integration_s: 159000, share_pct: 34, ring_from: 65.67, ring_to: 100 },
    ],
    ...altro,
  }
}

async function apri(corpo: unknown = anno(), larga?: number) {
  await montaDashboard({ altre: { "/api/v1/year": { stato: 200, corpo } }, larga })
}

describe("l'anno della Dashboard, desktop", () => {
  it("le ore, le notti e le due medie della tavola, coi numeri all'italiana", async () => {
    await apri()
    const carta = await screen.findByRole("region", { name: "Il 2026, fino a oggi" })

    expect(within(carta).getByText("128 h 40")).toBeTruthy()
    expect(within(carta).getByText("in 41 notti")).toBeTruthy()
    expect(within(carta).getByText("3 h 08")).toBeTruthy()
    expect(within(carta).getByText("4,6")).toBeTruthy()
    expect(within(carta).getByRole("link", { name: "Apri Statistiche" }).getAttribute("href")).toBe("/statistiche")
  })

  it("una barra per mese: il mese in corso acceso con le sue ore, quelli dopo tratteggiati", async () => {
    await apri()
    const carta = await screen.findByRole("region", { name: "Il 2026, fino a oggi" })

    const barre = [...carta.querySelectorAll<HTMLElement>(".al-dash__pillola-9")]
    expect(barre).toHaveLength(12)
    expect(barre[2]?.style.height).toBe("86%")
    expect(barre[8]?.style.height).toBe("50%")
    expect(barre[8]?.style.background).toBe("var(--giorno-su)")
    expect(barre[11]?.style.height).toBe("40%")
    expect(within(carta).getByText("14 h 40")).toBeTruthy()
    const prima = [...carta.querySelectorAll<HTMLElement>(".al-dash__strato-2")]
    expect(prima).toHaveLength(12)
    expect(prima[3]?.style.height).toBe("32%")
  })

  it("il confronto con lo stesso periodo dell'anno prima, col segno", async () => {
    await apri()
    const carta = await screen.findByRole("region", { name: "Il 2026, fino a oggi" })

    expect(within(carta).getByText(/128 h 40 contro 131 h nello stesso periodo del 2025/)).toBeTruthy()
    expect(within(carta).getByText("−2 h 20")).toBeTruthy()
  })

  it("senza l'anno prima ne' tratteggio ne' confronto: non un confronto con zero ore", async () => {
    await apri(anno({ previous_known: false, previous_same_period_s: 0, vs_previous_s: 463200 }))
    const carta = await screen.findByRole("region", { name: "Il 2026, fino a oggi" })

    expect(carta.querySelectorAll(".al-dash__strato-2")).toHaveLength(0)
    expect(within(carta).queryByText("2025")).toBeNull()
    expect(within(carta).queryByText(/contro/)).toBeNull()
  })

  it("i filtri con ore e quota, i frame senza filtro per ultimi e a parole, l'anello dall'API", async () => {
    await apri()
    const carta = await screen.findByRole("region", { name: "Filtri del 2026" })

    const righe = [...carta.querySelectorAll(".al-dash__griglia-15")].map((r) => r.textContent)
    expect(righe).toEqual(["Hα 46 h 2036%", "OIII 38 h 1030%", "Filtro non indicato 44 h 1034%"])
    expect(carta.querySelector(".al-dash__tondo-11")?.textContent).toBe("36%in Hα")
    expect(within(carta).getByText("Quota delle 128 h 40 per filtro, da gennaio a oggi.")).toBeTruthy()
    const anello = carta.querySelector<HTMLElement>(".al-dash__tondo-10")
    expect(anello?.style.background).toContain("36.01%")
    expect(anello?.style.background).toContain("var(--ignoto-tratteggio) 65.67%")
  })

  it("un anno senza ore: zeri, la media col trattino, e una riga al posto dell'anello", async () => {
    await apri(anno({ nights: 0, integration_s: 0, per_night_s: null, per_month: 0, filters: [], vs_previous_s: -471600 }))
    const carta = await screen.findByRole("region", { name: "Il 2026, fino a oggi" })

    expect(within(carta).getByText("in 0 notti")).toBeTruthy()
    expect(within(carta).getByText("—")).toBeTruthy()
    const filtri = screen.getByRole("region", { name: "Filtri del 2026" })
    expect(within(filtri).getByText("Nessuna posa nel 2026, per ora.")).toBeTruthy()
    expect(filtri.querySelector(".al-dash__tondo-10")).toBeNull()
    expect(filtri.style.justifyContent).toBe("flex-start")
  })

  it("un filtro a colori e' tre fette R, G, B: un gradiente dentro l'anello lo cancellerebbe (collaudo 11/11)", async () => {
    await apri(anno({ filters: [{ name: "RGB", passband: "OSC", integration_s: 463200, share_pct: 100, ring_from: 0, ring_to: 100 }] }))
    const carta = await screen.findByRole("region", { name: "Filtri del 2026" })

    const anello = carta.querySelector<HTMLElement>(".al-dash__tondo-10")?.style.background ?? ""
    expect(anello).not.toContain("--filtro-a-colori")
    expect(anello).toContain("var(--filtro-r) 0%")
    expect(anello).toContain("var(--filtro-b)")
  })

  it("le notti al mese a un decimale, come la tavola: 2,0 e non 2", async () => {
    await apri(anno({ per_month: 2 }))
    expect(await screen.findByText("2,0")).toBeTruthy()
  })

  it("senza l'anno prima le barre non dicono di averlo accanto", async () => {
    await apri(anno({ previous_known: false }))
    expect(await screen.findByRole("img", { name: "Il 2026 mese per mese" })).toBeTruthy()
  })

  it("una notte e' al singolare", async () => {
    await apri(anno({ nights: 1 }))
    expect(await screen.findByText("in 1 notte")).toBeTruthy()
  })

  it("l'anno che non risponde lo dice, e il resto della pagina c'e'", async () => {
    await montaDashboard({ altre: { "/api/v1/year": { stato: 500, corpo: {} } } })

    expect(await screen.findByText("L'anno non si legge: l'app non risponde.")).toBeTruthy()
    expect(screen.getByText("Da confermare, 32")).toBeTruthy()
  })

  it("col meteo che non risponde l'anno e da riprendere ci sono lo stesso", async () => {
    await montaDashboard({ altre: { "/api/v1/year": { stato: 200, corpo: anno() }, "/api/v1/weather": { stato: 500, corpo: {} } } })

    expect(await screen.findByRole("region", { name: "Il 2026, fino a oggi" })).toBeTruthy()
    expect(screen.getByText("Da confermare, 32")).toBeTruthy()
  })
})

describe("l'anno della Dashboard, telefono", () => {
  it("una carta sola: il riassunto in una riga, le barre, il confronto e i filtri con la quota", async () => {
    await apri(anno(), 390)
    const carta = await screen.findByRole("region", { name: "Il 2026" })

    expect(within(carta).getByText("41 notti · 3 h 08 a notte · 4,6 al mese")).toBeTruthy()
    expect(carta.querySelectorAll(".al-dash__strato-3")).toHaveLength(12)
    expect(within(carta).getByText("tratteggio = 2025 · −2 h 20 rispetto allo stesso periodo")).toBeTruthy()
    const righe = [...carta.querySelectorAll(".al-dash__griglia-22")].map((r) => r.textContent)
    expect(righe).toEqual(["Hα36%", "OIII30%", "Filtro non indicato34%"])
    expect(screen.queryByRole("region", { name: "Filtri del 2026" })).toBeNull()
  })

  it("un anno senza notti dice la media col trattino, come il desktop", async () => {
    await apri(anno({ nights: 0, integration_s: 0, per_night_s: null, per_month: 0, filters: [] }), 390)
    const carta = await screen.findByRole("region", { name: "Il 2026" })
    expect(within(carta).getByText("0 notti · — a notte · 0,0 al mese")).toBeTruthy()
  })
})
