// @vitest-environment jsdom
/**
 * La **Dashboard** sul disegno v37 (`pagine/dashboard.html` del progetto Design), prima fetta: la
 * testa di stanotte, le sei carte del meteo della notte col grafico che si apre sotto, le prossime
 * tre notti, cio' che resta da riprendere e i progetti che ancora non ci sono.
 *
 * La pagina non calcola niente: verdetto, ore serene, giudizi e conti arrivano scritti dal
 * backend. Qui si prova che li mostra al posto della tavola e che i gesti aprono cio' che dicono.
 */
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { STANOTTE, disegna, pulisci } from "./banco"
import { NOTTE as DEL_METEO, TENDENZA, meteo, misura } from "./meteo-banco"

// le sei misure della Dashboard: il banco del Meteo non ha jet stream e condensa con un valore
const NOTTE = {
  ...DEL_METEO,
  measures: [
    ...DEL_METEO.measures,
    misura("jet", { level: "go", value: 96, axis_max: 200 }),
    misura("condensation", { level: "go", value: 8, axis_min: -5, axis_max: 15 }),
  ],
}

afterEach(pulisci)
afterEach(() => vi.unstubAllGlobals())

const STANOTTE_CON_LUNA = {
  "/api/v1/tonight": {
    stato: 200,
    corpo: {
      night: "2026-09-26",
      site: null,
      moon: {
        phase_key: "waning_gibbous", illumination_pct: 62, rise: "2026-09-26T23:40:00+02:00", set: "2026-09-27T15:17:00+02:00",
        lit_side: "left", highest: null, track: [], ceiling_deg: 90,
      },
      sky_bands: [],
      weather: null,
    },
  },
}

const NOTTE_ARCHIVIO = {
  id: 7, night_date: "2026-09-19", site: "Casa", site_source: "header", frames: 180, integration_s: 15120, untimed: 0,
  objects: [
    { key: "m31", name: "M 31", frames: 120, integration_s: 9000, untimed: 0, bar_pct: 100 },
    { key: "m33", name: "M 33", frames: 40, integration_s: 4000, untimed: 0, bar_pct: 44 },
    { key: "m45", name: "M 45", frames: 20, integration_s: 2120, untimed: 0, bar_pct: 24 },
  ],
  filters: [], moon: null, weather: { verdict: null, cloud_total_pct: null, usable_hours: null, window: null, window_hours: null, state: "unknown", arrives_on: null },
}

function notti(items: unknown[]) {
  return {
    "/api/v1/nights": {
      stato: 200,
      corpo: { items, total: items.length, limit: 1, offset: 0, totals: { nights: items.length, frames: 0, integration_s: 0, untimed: 0 }, waiting: [], still_reading: 0, reading_done_pct: null },
    },
  }
}

const PROSSIME = [
  { ...NOTTE, night: "2026-09-27", verdict: "nogo", usable_hours: 0, usable_since: null, usable_until: null },
  { ...NOTTE, night: "2026-09-28", verdict: "go", usable_hours: 8, usable_since: "2026-09-28T21:00:00+02:00", usable_until: "2026-09-29T05:00:00+02:00" },
  { ...TENDENZA, night: "2026-09-29", window_hours: 9 },
]

async function apriDashboard(altre: Record<string, unknown> = {}) {
  meteo(
    { fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE, ...PROSSIME] },
    { ...STANOTTE, ...STANOTTE_CON_LUNA, ...notti([NOTTE_ARCHIVIO]), "/api/v1/review": { stato: 200, corpo: { to_confirm: 32 } }, ...altre } as never,
  )
  await disegna()
  return screen.findByRole("region", { name: /stanotte a Casa/i })
}

describe("la Dashboard, stanotte", () => {
  it("in testa il sito, le ore di buio sereno col semaforo grande e la Luna con fase, luce e orari", async () => {
    const stanotte = await apriDashboard()

    expect(stanotte.querySelector(".as-dashboard__grande")?.textContent).toBe("3 ore di buio sereno")
    expect(stanotte.querySelector(".as-semaforo--grande")?.textContent).toBe("incerta")
    const luna = await within(stanotte).findByText("Gibbosa calante, illuminata al 62%")
    expect(luna.closest(".as-luna")?.textContent).toContain("sorge alle 23:40 · tramonta alle 15:17")
  })

  it("le sei carte del meteo della notte, sempre al loro posto, con l'eta' della previsione", async () => {
    const stanotte = await apriDashboard()

    const carte = await within(stanotte).findAllByRole("button", { expanded: false, name: /buio|Meteoblue|hPa|10 m|rugiada|ottico|Non disponibile/ })
    expect(carte.map((c) => c.querySelector(".as-parametro__nome")?.textContent)).toEqual(["Nuvole", "Seeing", "Jet stream", "Vento", "Condensa", "Aerosol"])
    expect(stanotte.querySelector(".as-dashboard__aggiornato")?.textContent).toMatch(/^Previsione del /)
  })

  it("la carta delle Nuvole non ha la riga del giudizio: la sua parola e' il verdetto in testa", async () => {
    const stanotte = await apriDashboard()

    const [nuvole, , , vento] = await within(stanotte).findAllByRole("button", { expanded: false, name: /buio|Meteoblue|hPa|10 m|rugiada|ottico|Non disponibile/ })
    expect(nuvole?.querySelector(".as-semaforo")).toBeNull()
    expect(vento?.querySelector(".as-semaforo")?.textContent).toContain("non adatta dalle")
    expect(vento?.querySelector(".as-parametro__picco")?.textContent).toBe("raffiche fino a 35 km/h tra le 22:00 e le 23:00")
  })

  it("una carta apre sotto il suo grafico, una alla volta, e chiudi lo richiude", async () => {
    const stanotte = await apriDashboard()

    const vento = within(stanotte).getAllByRole("button", { name: /a 10 m/ })[0] as HTMLElement
    const condensa = within(stanotte).getByRole("button", { name: /rugiada/ })
    fireEvent.click(vento)
    expect(vento.getAttribute("aria-expanded")).toBe("true")
    const pannello = document.getElementById(vento.getAttribute("aria-controls") ?? "") as HTMLElement
    expect(pannello.hidden).toBe(false)
    expect(pannello.textContent).toContain("Vento, dal tramonto all'alba")
    expect(pannello.querySelector("svg .as-scala__tratto")).not.toBeNull()

    fireEvent.click(condensa)
    expect(vento.getAttribute("aria-expanded")).toBe("false")
    expect(condensa.getAttribute("aria-expanded")).toBe("true")

    const aperto = document.getElementById(condensa.getAttribute("aria-controls") ?? "") as HTMLElement
    fireEvent.click(within(aperto).getByRole("button", { name: "chiudi" }))
    expect(condensa.getAttribute("aria-expanded")).toBe("false")
    expect(document.activeElement).toBe(condensa)
  })

  it("Meteo porta alla pagina del Meteo", async () => {
    const stanotte = await apriDashboard()

    expect(within(stanotte).getByRole("link", { name: "Meteo" }).getAttribute("href")).toBe("/meteo")
  })
})

describe("la Dashboard, le prossime tre notti", () => {
  it("dopo stanotte le tre notti seguenti col giorno, le ore serene e il semaforo, verso il Meteo", async () => {
    await apriDashboard()

    const prossime = await screen.findByRole("region", { name: "meteo delle prossime 3 notti" })
    const serate = within(prossime).getAllByRole("link")
    expect(serate).toHaveLength(3)
    expect(serate[0]?.textContent).toContain("Domenica 27")
    expect(serate[0]?.textContent).toContain("nessuna serena")
    expect(serate[0]?.textContent).toContain("non adatta")
    expect(serate[1]?.textContent).toContain("8 ore · 21–05")
    expect(serate[1]?.textContent).toContain("buona")
    expect(serate[1]?.getAttribute("href")).toBe("/meteo")
    expect(serate[1]?.getAttribute("aria-label")).toBe("Meteo di lunedì 28")
  })

  it("la terza e' gia' tendenza, come nel Meteo: lo dice, con le ore di buio e non quelle serene", async () => {
    await apriDashboard()

    const prossime = await screen.findByRole("region", { name: "meteo delle prossime 3 notti" })
    const terza = within(prossime).getAllByRole("link")[2]
    expect(terza?.querySelector("b")?.textContent).toBe("Martedì 29 · tendenza")
    expect(terza?.textContent).toContain("9 ore di buio")
  })
})

describe("la Dashboard, da riprendere", () => {
  it("i casi da confermare con Rispondi, e l'ultima notte verso la sua pagina", async () => {
    await apriDashboard()

    const lavoro = await screen.findByRole("region", { name: "da riprendere" })
    expect(await within(lavoro).findByText("32 da confermare")).toBeTruthy()
    expect(within(lavoro).getByRole("link", { name: "Rispondi" }).getAttribute("href")).toBe("/da-confermare")
    const ultima = await within(lavoro).findByRole("link", { name: /Sabato 19 settembre/ })
    expect(ultima.getAttribute("href")).toBe("/notti?notte=7")
    expect(ultima.textContent).toContain("4 h 12 min su M 31 e altri 2, 180 frame")
  })

  it("con un oggetto solo la notte dice quello, senza altri", async () => {
    await apriDashboard(notti([{ ...NOTTE_ARCHIVIO, objects: NOTTE_ARCHIVIO.objects.slice(0, 1) }]))

    const lavoro = await screen.findByRole("region", { name: "da riprendere" })
    const ultima = await within(lavoro).findByRole("link", { name: /Sabato 19 settembre/ })
    expect(ultima.textContent).toContain("4 h 12 min su M 31, 180 frame")
  })

  it("senza notti nell'archivio non c'e' l'ultima notte, e niente da confermare non e' una riga", async () => {
    await apriDashboard({ ...notti([]), "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } } })

    await screen.findByRole("region", { name: "meteo delle prossime 3 notti" })
    expect(screen.queryByRole("region", { name: "da riprendere" })).toBeNull()
  })
})

describe("la Dashboard, i progetti", () => {
  it("finche' i progetti non esistono lo dice, con Crea un progetto verso Progetti", async () => {
    const stanotte = await apriDashboard()

    expect(within(stanotte).getByText(/^Nessun progetto in corso\./)).toBeTruthy()
    expect(within(stanotte).getByRole("link", { name: "Crea un progetto" }).getAttribute("href")).toBe("/progetti")
  })
})
