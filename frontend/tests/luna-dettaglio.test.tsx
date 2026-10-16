// @vitest-environment jsdom
/**
 * Il **dettaglio della Luna** della Dashboard (tavola v37, `as-pannello--luna`): si apre dalla Luna
 * in testa, dice luce, eta', orari con la direzione, distanza, prossime fasi, e il calendario di
 * questo mese e del prossimo con le notti buone per la banda larga. Tutto arriva scritto.
 */
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { pulisci } from "./banco"
import { STANOTTE_CON_LUNA, montaDashboard } from "./dashboard-banco"

afterEach(pulisci)
afterEach(() => vi.unstubAllGlobals())

const STANOTTE = STANOTTE_CON_LUNA["/api/v1/tonight"].corpo
const LUNA = {
  ...STANOTTE.moon,
  rise_compass: "ENE", age_days: 21, distance_km: 396200, next_new: "2026-10-08", next_full: "2026-10-23",
  highest: { at: "2026-09-27T07:30:00+02:00", altitude_deg: 68.2 },
}

/** Settembre e ottobre 2026: buone le notti dal 2 al 17 settembre, la nuova l'8, oggi il 26. */
function calendario() {
  const notti = []
  for (let i = 0; i < 61; i++) {
    const d = new Date(Date.UTC(2026, 8, 1 + i)).toISOString().slice(0, 10)
    notti.push({
      date: d, phase_key: "waning_gibbous", illumination_pct: 50, moonless_dark_s: 3 * 3600 + 50 * 60,
      event: d === "2026-09-08" ? "new" : d === "2026-09-23" ? "full" : null, good: d >= "2026-09-02" && d <= "2026-09-17",
      lit_side: "left",
    })
  }
  return { today: "2026-09-26", max_pct: 25, min_dark_h: 4, nights: notti }
}

async function apriLuna() {
  await montaDashboard({
    altre: {
      "/api/v1/tonight": { stato: 200, corpo: { ...STANOTTE, moon: LUNA } },
      "/api/v1/moon/calendar": { stato: 200, corpo: calendario() },
    },
  })
  const bottone = await screen.findByRole("button", { name: /Gibbosa calante, illuminata al 62%/ })
  expect(bottone.getAttribute("aria-expanded")).toBe("false")
  fireEvent.click(bottone)
  expect(bottone.getAttribute("aria-expanded")).toBe("true")
  return screen.findByRole("dialog", { name: "La Luna stanotte" })
}

describe("il dettaglio della Luna", () => {
  it("si apre dalla Luna in testa e dice luce, eta', orari con la direzione, distanza e prossime fasi", async () => {
    const pannello = await apriLuna()

    const righe = [...pannello.querySelectorAll(".as-pannello__dettagli div")].map((d) => [
      d.querySelector("dt")?.textContent, d.querySelector("dd")?.textContent,
    ])
    expect(righe).toEqual([
      ["illuminata", "al 62%"],
      ["età", "21 giorni"],
      ["sorge", "23:40 · a est-nord-est"],
      ["culmina", "07:30 · 68°"],
      ["tramonta", "15:17 di domani"],
      ["distanza", "396.200 km"],
      ["Luna nuova", "giovedì 8 ottobre"],
      ["Luna piena", "venerdì 23 ottobre"],
    ])
    expect(within(pannello).getByText("Gibbosa calante")).toBeTruthy()
  })

  it("il calendario del mese: le notti buone, la nuova, oggi; e il mese dopo con la freccia", async () => {
    const pannello = await apriLuna()

    expect(await within(pannello).findByText("settembre 2026")).toBeTruthy()
    const otto = within(pannello).getByTitle("8 settembre: Luna al 50%, 3 h 50 min di buio senza Luna")
    expect(otto.classList.contains("as-calendario__giorno--buio")).toBe(true)
    expect(otto.textContent).toBe("8nuova")
    expect(within(pannello).getByTitle(/^26 settembre/).classList.contains("as-calendario__giorno--oggi")).toBe(true)
    expect(within(pannello).getByTitle(/^20 settembre/).classList.contains("as-calendario__giorno--buio")).toBe(false)
    expect(within(pannello).getByText(
      "Notti buone per la banda larga: Luna sotto il 25%, o almeno 4 ore di buio senza Luna",
    )).toBeTruthy()

    expect((within(pannello).getByRole("button", { name: "Mese prima" }) as HTMLButtonElement).disabled).toBe(true)
    fireEvent.click(within(pannello).getByRole("button", { name: "Mese dopo" }))
    expect(within(pannello).getByText("ottobre 2026")).toBeTruthy()
    expect((within(pannello).getByRole("button", { name: "Mese dopo" }) as HTMLButtonElement).disabled).toBe(true)
  })

  it("chiudi lo richiude e torna sulla Luna", async () => {
    const pannello = await apriLuna()

    fireEvent.click(within(pannello).getByRole("button", { name: "chiudi" }))
    expect(screen.queryByRole("dialog", { name: "La Luna stanotte" })).toBeNull()
    expect(document.activeElement?.textContent).toContain("Gibbosa calante")
  })
})
