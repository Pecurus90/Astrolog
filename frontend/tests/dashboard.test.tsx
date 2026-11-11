// @vitest-environment jsdom
/**
 * La **Dashboard** piena (tavola v79): la carta grande con le ore di posa e il Sistema solare,
 * la Luna col calendario, le sei carte del meteo, le prossime 3 notti, Da riprendere. Ogni numero
 * a schermo e' quello che l'API ha scritto.
 */
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { pulisci } from "./banco"
import { NOTTE, SCALA_DELLA_LUNA, STANOTTE_PIENA, montaDashboard } from "./dashboard-banco"
import { misura } from "./meteo-banco"

afterEach(pulisci)

const testo = () => document.body.textContent ?? ""

describe("la Dashboard piena", () => {
  it("la carta grande dice le ore di posa, il verdetto e da dove vengono", async () => {
    await montaDashboard()
    expect(await screen.findByText("Ore di posa stanotte")).toBeDefined()
    expect(screen.getByText("4,6 ore")).toBeDefined()
    expect(screen.getByText("✓ notte buona")).toBeDefined()
    const sotto = testo()
    expect(sotto).toContain("3,1 in banda larga, 1,5 solo banda stretta")
    expect(sotto).toContain("buio 20:48–05:48")
    expect(sotto).toContain("trasparenza media 78/100")
    expect(sotto).toContain("3 modelli d'accordo su 4")
    expect(sotto).toContain("vento a 700 hPa 15 km/h, meno vento in 2 notti su 10 dell'ultimo anno")
  })

  it("la fascia della ripresa e le due tessere vengono dai tratti del buio", async () => {
    await montaDashboard()
    await screen.findByText("Ore di posa stanotte")
    expect(screen.getAllByText("banda larga").length).toBeGreaterThan(0)
    expect(screen.getByText("2 h 52")).toBeDefined()
    expect(screen.getByText("6 h 08")).toBeDefined()
    expect(testo()).toContain("23:40–05:48")
  })

  it("la vista del Sistema solare dice il pianeta piu' alto e quando sorgono gli altri", async () => {
    await montaDashboard()
    fireEvent.click(await screen.findByRole("tab", { name: "Sistema solare" }))
    expect(await screen.findByText("Più alto stanotte, nel Sistema solare")).toBeDefined()
    expect(screen.getAllByText("Saturno").length).toBeGreaterThan(0)
    expect(screen.getByText("41° alle 23:00")).toBeDefined()
    expect(testo()).toContain("Giove sorge alle 23:05")
    expect(testo()).toContain("Venere tramonta alle 19:40")
  })

  it("la Luna porta fase, pillole e calendario a tre gradini, con la notte ripresa", async () => {
    await montaDashboard()
    expect(await screen.findByText("La Luna stanotte")).toBeDefined()
    // nella carta della Luna e nella legenda del grafico
    expect(screen.getAllByText("sorge 23:40 · tramonta domani 15:17")).toHaveLength(2)
    expect(screen.getByText(/^distanza 371.200 km$/)).toBeDefined()
    expect(screen.getByText("sorge a est-nord-est")).toBeDefined()
    expect(await screen.findByText("banda larga buona, Luna fino al 25%")).toBeDefined()
    expect(screen.getByText("al limite, fino al 65%")).toBeDefined()
    const giorno = await screen.findByRole("button", { name: /19 settembre.*notte di ripresa/ })
    fireEvent.click(giorno)
    expect(await screen.findByText("Casa: M 31 · M 33 · 180 frame")).toBeDefined()
    expect(screen.getByRole("link", { name: "Apri la notte in Notti" }).getAttribute("href")).toBe("/notti?notte=7")
  })

  it("il dettaglio della Luna si apre e si chiude", async () => {
    await montaDashboard()
    fireEvent.click(await screen.findByRole("link", { name: "La Luna in dettaglio" }))
    const det = await screen.findByRole("region", { name: "La Luna, in dettaglio" })
    expect(within(det).getByText("21 giorni")).toBeDefined()
    fireEvent.click(within(det).getByRole("link", { name: "Chiudi il dettaglio" }))
    expect(screen.queryByRole("region", { name: "La Luna, in dettaglio" })).toBeNull()
  })

  it("le sei carte del meteo, ognuna al suo posto; senza chiave il seeing lo dice", async () => {
    await montaDashboard()
    expect(await screen.findByText("Meteo della notte")).toBeDefined()
    for (const nome of ["Nuvole", "Seeing", "Jet stream", "Vento", "Condensa", "Aerosol"]) {
      expect(screen.getAllByText(nome).length).toBeGreaterThan(0)
    }
    expect(testo()).toContain("serve una chiave Meteoblue")
    expect(testo()).toContain("Previsione del 30 settembre")
  })

  it("le prossime 3 notti: il giorno, la ripresa, le ore di posa e il cielo", async () => {
    await montaDashboard()
    expect(await screen.findByText("Le prossime 3 notti")).toBeDefined()
    expect(screen.getByText("Giovedì 1")).toBeDefined()
    expect(screen.getByText("nessuna ora di posa")).toBeDefined()
    expect(screen.getByText("8,4 ore di posa · 21–06")).toBeDefined()
    expect(screen.getByText("Coperto · 96%")).toBeDefined()
    expect(screen.getByText("9 ore di buio · tendenza")).toBeDefined()
    // la tendenza non ha le ore, ma la sua Trasparenza c'e'
    expect(screen.getAllByText("trasparenza media nel buio").length).toBe(3)
  })

  it("una Luna che tramonta la sera e sorge il mattino dopo lo dice in quest'ordine", async () => {
    await montaDashboard({ stanotte: { moon: { ...STANOTTE_PIENA.moon, set: "2026-09-30T17:07:00+02:00", rise: "2026-10-01T09:49:00+02:00" } } })
    expect((await screen.findAllByText("tramonta 17:07 · sorge domani 09:49")).length).toBeGreaterThan(0)
  })

  it("un aerosol fra le due soglie non e' un dato che manca: dice fra quali", async () => {
    const aerosol = misura("aerosol", { level: null, value: 0.14, axis_max: 0.2 })
    await montaDashboard({
      previsione: {
        nights: [{ ...NOTTE, measures: [...NOTTE.measures.filter((m) => m.code !== "aerosol"), aerosol] }],
        scales: [SCALA_DELLA_LUNA, { code: "aerosol", steps: [{ level: "nogo", bound: 1, strict: false }, { level: null, bound: 0.1, strict: false }], lower_is_worse: false }],
      },
    })
    expect(await screen.findByText("fra 0,1 e 1")).toBeDefined()
    expect(screen.getByText("0,14")).toBeDefined()
  })

  it("Da riprendere: i casi da confermare portano a rispondere, i frame fuori alle Notti", async () => {
    await montaDashboard({ altre: { "/api/v1/nights": { stato: 200, corpo: {
      items: [], total: 0, limit: 1, offset: 0, totals: { nights: 1, frames: 500, integration_s: 0, untimed: 0, objects: 3 },
      waiting: [{ answer_at: "site", frames: 412 }], waiting_frames: 412, still_reading: 0, reading_done_pct: null } } } })
    expect(await screen.findByText("Da confermare, 32")).toBeDefined()
    expect(screen.getByRole("link", { name: "Rispondi" }).getAttribute("href")).toBe("/da-confermare")
    expect(screen.getByText("412 frame fuori dai conti")).toBeDefined()
    expect(screen.getByRole("link", { name: "Vedi in Notti" }).getAttribute("href")).toBe("/notti")
  })

  it("sul telefono le prossime notti mostrano la prima, le altre a richiesta", async () => {
    await montaDashboard({ larga: 390 })
    expect(await screen.findByText("Giovedì 1")).toBeDefined()
    expect(screen.queryByText("Venerdì 2")).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: /Le altre 2 notti/ }))
    expect(await screen.findByText("Venerdì 2")).toBeDefined()
  })
})
