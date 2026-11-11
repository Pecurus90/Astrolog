// @vitest-environment jsdom
/**
 * L'**anno** della Dashboard (tavola v37, `as-dashboard__anno`): "il 2026, fino a oggi" con notti,
 * ore, la media a notte e al mese, e un quadretto per giorno. I conti arrivano da `/year`.
 */
import { screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { pulisci } from "./banco"
import { montaDashboard } from "./dashboard-banco"

afterEach(pulisci)
afterEach(() => vi.unstubAllGlobals())

/** Il 2026 fino al 30 settembre: il 3 gennaio 1 h 30, il 4 gennaio 5 h, il resto vuoto. */
function anno(fatte: Record<string, [string, number]> = { "2026-01-03": ["under2", 5400], "2026-01-04": ["4to6", 18000] }) {
  const giorni = Array.from({ length: 365 }, (_, i) => {
    const d = new Date(Date.UTC(2026, 0, 1 + i)).toISOString().slice(0, 10)
    const [level, integration_s] = fatte[d] ?? [d > "2026-09-30" ? "future" : "none", 0]
    return { date: d, level, integration_s }
  })
  return {
    year: 2026, until: "2026-09-30", nights: 41, integration_s: 463200, per_night_s: 11297, per_month: 4.6,
    lead_blank: 3, days: giorni,
  }
}

async function apriAnno(corpo: unknown = anno(), altre: Record<string, unknown> = {}, larga?: number) {
  await montaDashboard({ altre: { "/api/v1/year": { stato: 200, corpo }, ...altre }, larga })
  return screen.findByRole("region", { name: "il 2026, fino a oggi" })
}

describe("l'anno della Dashboard", () => {
  it("le quattro medie dell'anno, gia' contate", async () => {
    const sezione = await apriAnno()

    const medie = [...sezione.querySelectorAll(".as-dashboard__medie div")].map((d) => [
      d.querySelector("dt")?.textContent, d.querySelector("dd")?.textContent,
    ])
    expect(medie).toEqual([
      ["notti", "41"],
      ["ore", "128 h 40 min"],
      ["a notte, in media", "3 h 8 min"],
      ["al mese", "4,6 notti"],
    ])
    expect(within(sezione).getByRole("link", { name: "Statistiche" }).getAttribute("href")).toBe("/statistiche")
  })

  it("un quadretto per giorno da lunedi', col livello delle sue ore e i giorni che verranno", async () => {
    const sezione = await apriAnno()

    const griglia = within(sezione).getByRole("img", { name: "Il 2026, un quadretto per giorno: 41 notti fino al 30 settembre" })
    const celle = [...griglia.querySelectorAll(".as-heat__cella")]
    expect(celle).toHaveLength(3 + 365)
    expect(celle.slice(0, 3).every((c) => c.classList.contains("as-heat__cella--vuoto"))).toBe(true)
    expect(celle[3 + 2]?.className).toBe("as-heat__cella as-heat__cella--l1")
    expect(celle[3 + 3]?.className).toBe("as-heat__cella as-heat__cella--l3")
    expect(celle[3 + 3]?.getAttribute("title")).toBe("4 gennaio: 5 h")
    expect(celle[3 + 4]?.className).toBe("as-heat__cella as-heat__cella--zero")
    expect(celle[3 + 364]?.className).toBe("as-heat__cella as-heat__cella--fuori")
    expect(within(sezione).getByText("meno di 2 h")).toBeTruthy()
  })

  it("le ore vuote si dicono in ore, come la legenda, e una notte e' al singolare", async () => {
    const sezione = await apriAnno({ ...anno({ "2026-01-03": ["none", 0] }), nights: 1, integration_s: 0, per_night_s: 0, per_month: 1 })

    const medie = [...sezione.querySelectorAll(".as-dashboard__medie dd")].map((d) => d.textContent)
    expect(medie).toEqual(["1", "0 h", "0 h", "1 notte"])
    const griglia = within(sezione).getByRole("img", { name: "Il 2026, un quadretto per giorno: 1 notte fino al 30 settembre" })
    expect(griglia.querySelectorAll(".as-heat__cella")[3 + 2]?.getAttribute("title")).toBe("3 gennaio: 0 h")
  })

  it("col meteo che non risponde l'anno e da riprendere ci sono lo stesso: non dipendono dal meteo", async () => {
    await montaDashboard({ altre: { "/api/v1/year": { stato: 200, corpo: anno() }, "/api/v1/weather": { stato: 500, corpo: {} } } })

    expect(await screen.findByRole("region", { name: "il 2026, fino a oggi" })).toBeTruthy()
    expect(screen.getByText("Da confermare, 32")).toBeTruthy()
  })

  it("un anno senza notti non ha la media a notte: lo dice con un trattino, non con zero", async () => {
    const sezione = await apriAnno({ ...anno({}), nights: 0, integration_s: 0, per_night_s: null, per_month: 0 })

    const media = [...sezione.querySelectorAll(".as-dashboard__medie div")][2]
    expect(media?.querySelector("dd")?.textContent).toBe("—")
  })
})
