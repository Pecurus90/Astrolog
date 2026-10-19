// @vitest-environment jsdom
/**
 * L'**anno** della Dashboard (tavola v37, `as-dashboard__anno`): "il 2026, fino a oggi" con notti,
 * ore, la media a notte e al mese, e un quadretto per giorno. I conti arrivano da `/year`.
 */
import { screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { chiamate, pulisci } from "./banco"
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
      ["al mese", "4.6 notti"],
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
    expect(screen.getByRole("region", { name: "da riprendere" })).toBeTruthy()
  })

  it("durante la prima scansione l'anno si rilegge da solo", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    try {
      const evento = { current: 10, total: 100, file: "D:/Astro/a.fits", run_id: 1, folder_id: 1, found: 10, new: 10, unchanged: 0, duplicates: 0, missing: 0, skipped: 0, errors: 0, online_only: 0 }
      const scansione = {
        worker: { state: "running", stage: "scan", started_at: "2026-09-25T15:00:00Z", ended_at: null, stages: [] },
        scan: { state: "running", folder_id: 1, run_id: 1, last_event: evento, receipt: null, remaining_s: null, first: true },
        pending: {},
        action: "stop",
      }
      await apriAnno(anno(), { "/api/v1/pipeline/status": { stato: 200, corpo: scansione } })
      const prima = chiamate().filter((u) => u.includes("/api/v1/year")).length

      await vi.advanceTimersByTimeAsync(16_000)
      expect(chiamate().filter((u) => u.includes("/api/v1/year")).length).toBeGreaterThan(prima)
    } finally {
      vi.useRealTimers()
    }
  })

  it("un anno senza notti non ha la media a notte: lo dice con un trattino, non con zero", async () => {
    const sezione = await apriAnno({ ...anno({}), nights: 0, integration_s: 0, per_night_s: null, per_month: 0 })

    const media = [...sezione.querySelectorAll(".as-dashboard__medie div")][2]
    expect(media?.querySelector("dd")?.textContent).toBe("—")
  })

  it("durante la prima scansione le notti e le ore sono finora, e le medie a scansione finita", async () => {
    const evento = { current: 10, total: 100, file: "D:/Astro/a.fits", run_id: 1, folder_id: 1, found: 10, new: 10, unchanged: 0, duplicates: 0, missing: 0, skipped: 0, errors: 0, online_only: 0 }
    const scansione = {
      worker: { state: "running", stage: "scan", started_at: "2026-09-25T15:00:00Z", ended_at: null, stages: [] },
      scan: { state: "running", folder_id: 1, run_id: 1, last_event: evento, receipt: null, remaining_s: null, first: true },
      pending: {},
      action: "stop",
    }
    const sezione = await apriAnno(anno(), {
      "/api/v1/pipeline/status": { stato: 200, corpo: scansione },
      "/api/v1/nights": {
        stato: 200,
        corpo: {
          items: [], total: 0, limit: 1, offset: 0, totals: { nights: 0, frames: 0, integration_s: 0, untimed: 0 },
          waiting: [], waiting_frames: 0, still_reading: 90, reading_done_pct: 15,
        },
      },
    })

    expect(within(sezione).getByText("in lettura, 15%")).toBeTruthy()
    const medie = [...sezione.querySelectorAll(".as-dashboard__medie dd")].map((d) => d.textContent)
    expect(medie).toEqual(["41finora", "128 h 40 minfinora", "—a scansione finita", "—a scansione finita"])
  })

  it("finito lo stadio della scansione, la prima lettura continua finche' i frame non hanno la loro notte", async () => {
    const scansione = {
      worker: { state: "running", stage: "solve", started_at: "2026-09-25T15:00:00Z", ended_at: null, stages: [] },
      scan: { state: "completed", folder_id: 1, run_id: 1, last_event: null, receipt: null, remaining_s: null, first: true },
      pending: {},
      action: "stop",
    }
    const sezione = await apriAnno(anno(), {
      "/api/v1/pipeline/status": { stato: 200, corpo: scansione },
      "/api/v1/nights": {
        stato: 200,
        corpo: {
          items: [], total: 0, limit: 1, offset: 0, totals: { nights: 0, frames: 0, integration_s: 0, untimed: 0 },
          waiting: [], waiting_frames: 0, still_reading: 90, reading_done_pct: 15,
        },
      },
    })

    expect(await within(sezione).findByText("in lettura, 15%")).toBeTruthy()
    expect(within(sezione).queryByRole("link", { name: "Statistiche" })).toBeNull()
    const medie = [...sezione.querySelectorAll(".as-dashboard__medie dd")].map((d) => d.textContent)
    expect(medie).toEqual(["41finora", "128 h 40 minfinora", "—a scansione finita", "—a scansione finita"])
  })

  it("a scansione finita l'anno si rilegge: i conti veri, non quelli dell'apertura", async () => {
    const evento = { current: 10, total: 100, file: "D:/Astro/a.fits", run_id: 1, folder_id: 1, found: 10, new: 10, unchanged: 0, duplicates: 0, missing: 0, skipped: 0, errors: 0, online_only: 0 }
    const scansione: Record<string, unknown> = {
      worker: { state: "running", stage: "scan", started_at: "2026-09-25T15:00:00Z", ended_at: null, stages: [] },
      scan: { state: "running", folder_id: 1, run_id: 1, last_event: evento, receipt: null, remaining_s: null, first: true },
      pending: {},
      action: "stop",
    }
    // il banco serializza a ogni chiamata: cambiare l'oggetto e' cio' che il backend dira' dopo
    const corpo: Record<string, unknown> = { ...anno({}), nights: 0, integration_s: 0, per_night_s: null, per_month: 0 }
    const sezione = await apriAnno(corpo, { "/api/v1/pipeline/status": { stato: 200, corpo: scansione } })
    expect(within(sezione).getByText("in lettura, 0%")).toBeTruthy()

    Object.assign(corpo, anno())
    scansione.worker = { state: "completed", stage: null, started_at: "2026-09-25T15:00:00Z", ended_at: "2026-09-25T16:00:00Z", stages: [] }
    scansione.scan = null
    scansione.action = "start"

    // il battito dello stato mentre gira e' 1,5 s
    await within(sezione).findByText("3 h 8 min", {}, { timeout: 5000 })
    const medie = [...sezione.querySelectorAll(".as-dashboard__medie dd")].map((d) => d.textContent)
    expect(medie).toEqual(["41", "128 h 40 min", "3 h 8 min", "4.6 notti"])
  })

  it("sul telefono l'anno non c'e': la tavola del telefono dice nient'altro, e niente rimandi", async () => {
    await montaDashboard({ altre: { "/api/v1/year": { stato: 200, corpo: anno() } }, larga: 390 })

    await screen.findByText("meteo della notte")
    // montato, chiederebbe l'anno insieme al resto della pagina: qui non lo chiede nessuno
    expect(chiamate().some((u) => u.includes("/api/v1/year"))).toBe(false)
    expect(screen.queryByRole("region", { name: "il 2026, fino a oggi" })).toBeNull()
  })
})
