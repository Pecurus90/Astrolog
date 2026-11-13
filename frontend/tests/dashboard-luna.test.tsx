// @vitest-environment jsdom
/**
 * La **Luna della Dashboard** (tavola v79): le pillole e il dettaglio da `/tonight`, il
 * calendario a tre gradini da `/moon/calendar` coi suoi mesi, la notte ripresa che si apre e si
 * chiude, e la Luna che non si calcola senza fuso.
 */
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { numero } from "../src/i18n"
import { pulisci } from "./banco"
import { STANOTTE_PIENA, calendario, montaDashboard } from "./dashboard-banco"

afterEach(pulisci)

const pillole = () =>
  [...document.querySelectorAll(".al-dash__pillola-3")].map((p) => p.textContent)
const luna = (campi: Record<string, unknown>) => ({
  stanotte: { moon: { ...STANOTTE_PIENA.moon, ...campi } },
})

describe("la Luna stanotte", () => {
  it("le pillole: il massimo, la distanza, l'eta' e dove sorge", async () => {
    await montaDashboard()
    await screen.findByText("La Luna stanotte")
    expect(pillole()).toEqual([
      "sale fino a 52° alle 05:30",
      `distanza ${numero(371200)} km`,
      "età 21 giorni",
      "sorge a est-nord-est",
    ])
    expect(screen.getByText("Gibbosa calante")).toBeDefined()
    expect(screen.getByText("62%")).toBeDefined()
  })

  it("il massimo dentro il grafico vince su quello della notte; un giorno e' al singolare", async () => {
    await montaDashboard(
      luna({
        highest_in_chart: { at: "2026-10-01T01:00:00+02:00", altitude_deg: 40.6 },
        age_days: 1,
        rise_compass: null,
      }),
    )
    await screen.findByText("La Luna stanotte")
    expect(pillole()).toEqual([
      "sale fino a 41° alle 01:00",
      `distanza ${numero(371200)} km`,
      "età 1 giorno",
    ])
  })

  it("il dettaglio: eta' con la prossima piena, distanza, dove e quando sorge, i tre gradini", async () => {
    await montaDashboard()
    fireEvent.click(await screen.findByRole("link", { name: "La Luna in dettaglio" }))
    const det = await screen.findByRole("region", { name: "La Luna, in dettaglio" })
    const voci = [...det.querySelectorAll(".al-dash__colonna-1")].map((v) =>
      [...v.children].map((c) => c.textContent),
    )
    expect(voci).toEqual([
      ["età", "21 giorni", "piena il 24 ottobre"],
      ["distanza", `${numero(371200)} km`, ""],
      ["sorge", "est-nord-est", "alle 23:40"],
    ])
    expect(det.textContent).toContain(
      "banda larga buona con la Luna fino al 25%, al limite fino al 65%",
    )
    const chiudi = within(det).getByRole("link", { name: "Chiudi il dettaglio" })
    expect(chiudi.style.width).toBe("28px")
    expect(
      screen.getByRole("link", { name: "La Luna in dettaglio" }).getAttribute("aria-expanded"),
    ).toBe("true")
    fireEvent.click(screen.getByRole("link", { name: "La Luna in dettaglio" }))
    expect(screen.queryByRole("region", { name: "La Luna, in dettaglio" })).toBeNull()
  })

  it("il dettaglio dice da dove vengono le soglie: la scala della Luna del Meteo (Marco, 13/11)", async () => {
    await montaDashboard()
    fireEvent.click(await screen.findByRole("link", { name: "La Luna in dettaglio" }))
    const det = await screen.findByRole("region", { name: "La Luna, in dettaglio" })
    expect(det.querySelector(".al-dash__testo-16")?.textContent).toBe(
      "Tre gradini: banda larga buona con la Luna fino al 25%, al limite fino al 65%, poi solo banda" +
        " stretta. Accanto, le ore di buio con la Luna sotto l'orizzonte (le soglie vengono dalla" +
        " scala della Luna del Meteo).",
    )
  })

  it("una Luna che non sorge stanotte, a un giorno, senza piena", async () => {
    await montaDashboard({
      ...luna({ rise: null, rise_compass: null, age_days: 1, next_full: null }),
      previsione: { scales: [] },
    })
    fireEvent.click(await screen.findByRole("link", { name: "La Luna in dettaglio" }))
    const det = await screen.findByRole("region", { name: "La Luna, in dettaglio" })
    const voci = [...det.querySelectorAll(".al-dash__colonna-1")].map((v) =>
      [...v.children].map((c) => c.textContent),
    )
    expect(voci).toEqual([
      ["età", "1 giorno", ""],
      ["distanza", `${numero(371200)} km`, ""],
      ["sorge", "non stanotte", ""],
    ])
    expect(det.textContent).not.toContain("Tre gradini")
  })

  it("senza fuso la Luna non si calcola, e lo dice", async () => {
    await montaDashboard({ stanotte: { moon: null, shooting: [] } })
    expect(await screen.findByText("La Luna si calcola col fuso orario del sito.")).toBeDefined()
    expect(screen.queryByText("La Luna stanotte")).toBeNull()
    expect(pillole()).toEqual([])
    expect(screen.queryByText("2 h 52")).toBeNull()
  })

  it("sul telefono il dettaglio si chiude con un tondo largo", async () => {
    await montaDashboard({ larga: 390 })
    fireEvent.click(await screen.findByRole("link", { name: "La Luna in dettaglio" }))
    const det = await screen.findByRole("region", { name: "La Luna, in dettaglio" })
    expect(within(det).getByRole("link", { name: "Chiudi il dettaglio" }).style.width).toBe("44px")
    expect(screen.getByText("Gibbosa calante")).toBeDefined()
  })
})

describe("il calendario della Luna", () => {
  it("ogni giorno il suo gradino e le ore senza Luna; oggi segnato; la stella sulla notte ripresa", async () => {
    await montaDashboard()
    const giorno = await screen.findByRole("button", { name: /19 settembre/ })
    expect(giorno.getAttribute("aria-label")).toBe(
      "sabato 19 settembre: banda larga al limite, 4 h di buio senza Luna, notte di ripresa",
    )
    expect(giorno.textContent).toBe("19! 4 h★")
    expect(
      screen.getByLabelText("giovedì 3 settembre: banda larga buona, 4 h di buio senza Luna")
        .textContent,
    ).toBe("3✓ 4 h")
    expect(
      screen.getByLabelText("mercoledì 9 settembre: banda larga buona, 4 h di buio senza Luna")
        .textContent,
    ).toBe("9● 4 h")
    expect(
      screen.getByLabelText("giovedì 24 settembre: solo banda stretta, 4 h di buio senza Luna")
        .textContent,
    ).toBe("24○ 4 h")
    expect(
      (
        screen.getByLabelText(
          "mercoledì 30 settembre: solo banda stretta, 4 h di buio senza Luna",
        ) as HTMLElement
      ).style.fontWeight,
    ).toBe("600")
    expect(document.body.textContent).toContain("Luna nuova mercoledì 9")
    expect(document.body.textContent).toContain("Luna piena giovedì 24")
  })

  it("la notte ripresa: ore, oggetti, la notte in Notti; si chiude con la x o ripremendo", async () => {
    await montaDashboard()
    const giorno = await screen.findByRole("button", { name: /19 settembre/ })
    fireEvent.click(giorno)
    expect(await screen.findByText("★ Sabato 19 settembre · 4 h 12")).toBeDefined()
    expect(giorno.getAttribute("aria-pressed")).toBe("true")
    fireEvent.click(screen.getByRole("link", { name: "Chiudi" }))
    expect(screen.queryByText("Casa: M 31 · M 33 · 180 frame")).toBeNull()
    fireEvent.click(giorno)
    expect(await screen.findByText("Casa: M 31 · M 33 · 180 frame")).toBeDefined()
    fireEvent.click(giorno)
    expect(screen.queryByText("Casa: M 31 · M 33 · 180 frame")).toBeNull()
  })

  it("una notte senza durata lo dice", async () => {
    const cal = calendario()
    const giorni = cal["/api/v1/moon/calendar"].corpo.nights.map((g) =>
      g.date === "2026-09-19"
        ? {
            ...g,
            shots: [
              { ...g.shots[0], integration_s: 0, untimed: 180 },
              {
                night_id: 8,
                site: "Rifugio",
                objects: ["M 45"],
                frames: 20,
                integration_s: 600,
                untimed: 0,
              },
            ],
          }
        : g,
    )
    await montaDashboard({
      altre: {
        "/api/v1/moon/calendar": {
          stato: 200,
          corpo: { ...cal["/api/v1/moon/calendar"].corpo, nights: giorni },
        },
      },
    })
    fireEvent.click(await screen.findByRole("button", { name: /19 settembre/ }))
    expect(await screen.findByText("★ Sabato 19 settembre · senza durata")).toBeDefined()
    expect(
      screen.getByText("Casa: M 31 · M 33 · 180 frame · Rifugio: M 45 · 20 frame"),
    ).toBeDefined()
  })

  it("i mesi: prima fermo al primo, dopo fino all'ultimo, e il giorno scelto si scorda", async () => {
    await montaDashboard()
    await screen.findByText("Settembre 2026")
    const prima = screen.getByRole("link", { name: "Mese prima" })
    const dopo = screen.getByRole("link", { name: "Mese dopo" })
    expect(prima.getAttribute("aria-disabled")).toBe("true")
    expect(dopo.getAttribute("aria-disabled")).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: /19 settembre/ }))
    fireEvent.click(dopo)
    expect(await screen.findByText("Ottobre 2026")).toBeDefined()
    expect(screen.queryByText(/Casa: M 31/)).toBeNull()
    expect(screen.getByRole("link", { name: "Mese dopo" }).getAttribute("aria-disabled")).toBe(
      "true",
    )
    expect(
      screen.getByRole("link", { name: "Mese prima" }).getAttribute("aria-disabled"),
    ).toBeNull()
    expect(
      (
        screen.getByLabelText(
          "giovedì 1 ottobre: solo banda stretta, 4 h di buio senza Luna",
        ) as HTMLElement
      ).style.fontWeight,
    ).toBe("500")
    fireEvent.click(screen.getByRole("link", { name: "Mese prima" }))
    expect(await screen.findByText("Settembre 2026")).toBeDefined()
  })

  it("un calendario che non si legge e' un avviso", async () => {
    await montaDashboard({ altre: { "/api/v1/moon/calendar": { stato: 500, corpo: {} } } })
    expect(
      await screen.findByText("Il calendario della Luna non si legge: l'app non risponde."),
    ).toBeDefined()
  })
})
