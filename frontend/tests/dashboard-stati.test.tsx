// @vitest-environment jsdom
/**
 * Gli **stati** della Dashboard (tavola v79, `stato`): senza sito, prima volta, prima scansione,
 * meteo che non risponde, prima previsione, sito senza fuso, notte senza buio, calendario non
 * ancora scritto, Luna che non sorge, caricamento, errore. Ogni vuoto e' una frase.
 */
import { fireEvent, screen, waitFor } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { chiamate, pulisci } from "./banco"
import { calendario, cartelle, montaDashboard, notti } from "./dashboard-banco"

afterEach(pulisci)

const testo = () => document.body.textContent ?? ""

describe("gli stati della Dashboard", () => {
  it("senza sito: Per cominciare con il sito e la cartella, e niente stanotte", async () => {
    await montaDashboard({
      stanotte: { night: null, site: null, moon: null, chart: null, sky_bands: [], planets: [], shooting: [], weather: null, dark_s: null },
      altre: { ...cartelle(0), ...notti([]) },
    })
    expect(await screen.findByText("Per cominciare")).toBeDefined()
    expect(screen.getByRole("link", { name: "Scegli il sito" }).getAttribute("href")).toBe("/impostazioni/sito")
    expect(screen.getByRole("link", { name: "Scegli la cartella" }).getAttribute("href")).toBe("/impostazioni/cartelle")
    expect(screen.queryByText("Ore di posa stanotte")).toBeNull()
    expect(screen.getByText("si riempie dopo la prima scansione")).toBeDefined()
    // tavola v80, `monthsEmpty`: anche qui le iniziali per il grafico stretto
    const corti = [...document.querySelectorAll(".al-dash__mese-corto")].map((m) => m.textContent)
    expect(corti.join("")).toBe("GFMAMGLASOND")
  })

  it("prima volta: il sito c'e', la cartella no; la notte si vede gia'", async () => {
    await montaDashboard({ altre: { ...cartelle(0), ...notti([]) } })
    expect(await screen.findByText("Per cominciare")).toBeDefined()
    expect(screen.getByText("Scegli la cartella delle riprese")).toBeDefined()
    expect(screen.getByText("Ore di posa stanotte")).toBeDefined()
    expect(screen.queryByText("Da riprendere")).toBeNull()
  })

  it("prima scansione: quanti file su quanti, e i casi da confermare a scansione finita", async () => {
    await montaDashboard({
      altre: {
        "/api/v1/pipeline/status": { stato: 200, corpo: {
          worker: { state: "running" },
          scan: { first: true, state: "running", last_event: { current: 3412, total: 18430 }, remaining_s: 4800 },
        } },
      },
    })
    expect(await screen.findByText("Prima scansione in corso")).toBeDefined()
    expect(testo()).toContain("file letti 3412 su 18 430 · ancora circa 1 h 20")
    expect(screen.getByRole("progressbar", { name: "Prima scansione" }).getAttribute("aria-valuenow")).toBe("19")
  })

  it("prima scansione: dice la cartella in lettura (tavola 583)", async () => {
    await montaDashboard({
      altre: {
        "/api/v1/pipeline/status": { stato: 200, corpo: {
          worker: { state: "running" },
          scan: { first: true, state: "running", last_event: { current: 1, total: 9 }, folder_path: "D:\\Dati\\Astro" },
        } },
      },
    })
    await screen.findByText("Prima scansione in corso")
    expect(testo()).toContain("Cartella D:\\Dati\\Astro. Si può usare AstroLog intanto; si ferma dall'ingranaggio.")
  })

  it("meteo che non risponde: l'avviso con Riprova ora, le carte mancanti, il buio calcolato", async () => {
    await montaDashboard({
      previsione: { fetched_at: null, nights: [], last_request: { at: "2026-09-30T12:05:00.000Z", status: "unreachable" } },
      stanotte: { weather: null },
    })
    expect(await screen.findByText("Meteo non raggiungibile")).toBeDefined()
    expect(screen.getByRole("button", { name: "Riprova ora" })).toBeDefined()
    expect(screen.getByText("Buio stanotte, calcolato")).toBeDefined()
    expect(screen.getByText("? senza meteo")).toBeDefined()
    expect(screen.getAllByText("? Non disponibile")).toHaveLength(6)
    // tavola 526: le tre notti restano, col buio dal calendario della Luna (#66)
    expect(await screen.findByText("Le prossime 3 notti")).toBeDefined()
    expect(screen.getAllByText("9 ore di buio")).toHaveLength(3)
    expect(screen.getAllByText("Nuvole non disponibili: serve la previsione")).toHaveLength(3)
    expect(testo()).toContain("Giovedì 1")
  })

  it("Riprova ora chiede la previsione subito", async () => {
    await montaDashboard({
      previsione: { fetched_at: null, nights: [], last_request: { at: "2026-09-30T12:05:00.000Z", status: "unreachable" } },
      stanotte: { weather: null },
      altre: { "/api/v1/weather/refresh": { stato: 200, corpo: { status: "unreachable" } } },
    })
    fireEvent.click(await screen.findByRole("button", { name: "Riprova ora" }))
    await waitFor(() => expect(chiamate().some((u) => u.includes("/api/v1/weather/refresh"))).toBe(true))
  })

  it("prima previsione non arrivata: lo dice, senza Riprova", async () => {
    await montaDashboard({ previsione: { fetched_at: null, nights: [], last_request: null }, stanotte: { weather: null } })
    expect(await screen.findByText("Prima previsione in arrivo")).toBeDefined()
    expect(screen.queryByRole("button", { name: "Riprova ora" })).toBeNull()
  })

  it("sito senza fuso: l'avviso in testa porta a modificare il sito", async () => {
    await montaDashboard({
      previsione: { missing: "no_timezone", nights: [] },
      stanotte: { night: null, moon: null, chart: null, sky_bands: [], planets: [], shooting: [], weather: null, dark_s: null },
    })
    expect(await screen.findByText("Fuso orario del sito non riconosciuto: le notti non si possono calcolare.")).toBeDefined()
    expect(screen.getByText("? senza fuso orario")).toBeDefined()
    expect(screen.getByText("Notti non calcolabili")).toBeDefined()
  })

  it("giorni polari: nessun buio, detto a parole", async () => {
    await montaDashboard({ stanotte: { dark_s: 0, weather: null } })
    expect(await screen.findByText("? senza buio")).toBeDefined()
    expect(screen.getByText("Nessun buio")).toBeDefined()
  })

  it("giorni polari col buio che torna: la data nella frase (tavola, 427)", async () => {
    await montaDashboard({ stanotte: { dark_s: 0, weather: null, dark_returns: "2027-08-12" } })
    await screen.findByText("? senza buio")
    expect(
      screen.getByText(
        "A questa latitudine il Sole non scende sotto −18° fino al 12 agosto: nessuna ora di buio astronomico, nessuna ora di posa.",
      ),
    ).toBeDefined()
  })

  it("calendario non ancora scritto: una riga che lo dice", async () => {
    await montaDashboard({ altre: calendario(true) })
    expect(await screen.findByText("Il calendario della Luna non è ancora scritto: si scrive da solo dopo il primo avvio.")).toBeDefined()
  })

  it("col calendario non ancora scritto (primo giro, sito appena spostato) lo rilegge finche' arriva", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    try {
      await montaDashboard({ altre: calendario(true) })
      await screen.findByText(/non è ancora scritto/)
      const letture = () => chiamate().filter((u) => u.includes("/api/v1/moon/calendar")).length
      const prima = letture()
      await vi.advanceTimersByTimeAsync(16_000)
      expect(letture()).toBeGreaterThan(prima)
    } finally {
      vi.useRealTimers()
    }
  })

  it("un archivio che ha ancora i suoi frame non e' vuoto, anche senza cartelle attive", async () => {
    await montaDashboard({ altre: cartelle(0) })
    expect(await screen.findByText("Da confermare, 32")).toBeDefined()
    expect(screen.queryByText("Scegli la cartella delle riprese")).toBeNull()
    expect(screen.queryByText("Per cominciare")).toBeNull()
  })

  it("una previsione che vale ancora non e' un meteo che non risponde", async () => {
    await montaDashboard({ previsione: { last_request: { at: "2026-09-30T19:05:00.000Z", status: "unreachable" } } })
    expect(await screen.findByText("Nuvole")).toBeDefined()
    expect(screen.queryByText("Meteo non raggiungibile")).toBeNull()
    expect(screen.getByText("Le prossime 3 notti")).toBeDefined()
  })

  it("Luna che non sorge stanotte", async () => {
    await montaDashboard({ stanotte: { moon_in_dark: null, moon: { phase_key: "new", illumination_pct: 1, rise: null, set: null, rise_compass: null, age_days: 0,
      distance_km: 380000, next_new: null, next_full: null, lit_side: "right", highest: { at: "2026-10-01T00:00:00+02:00", altitude_deg: -10 }, track: [], ceiling_deg: 75 } } })
    expect(await screen.findAllByText("non sorge stanotte")).toHaveLength(2)
  })

  it("caricamento: lo scheletro dice Caricamento", async () => {
    await montaDashboard({ altre: { "/api/v1/tonight": { stato: 200, corpo: {}, attesa: new Promise(() => {}) } } })
    expect((await screen.findAllByText(/Caricamento/)).length).toBeGreaterThan(0)
  })

  it("errore: stanotte che non risponde e' un avviso con Riprova", async () => {
    await montaDashboard({ altre: { "/api/v1/tonight": { stato: 500, corpo: {} } } })
    expect(await screen.findByRole("button", { name: "Riprova" })).toBeDefined()
  })
})
