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

import { pulisci } from "./banco"
import { NOTTE_ARCHIVIO, montaDashboard, notti } from "./dashboard-banco"

afterEach(pulisci)
afterEach(() => vi.unstubAllGlobals())

async function apriDashboard(altre: Record<string, unknown> = {}, larga?: number) {
  await montaDashboard({ altre, larga })
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

  it("Meteo porta alla pagina del Meteo, Stanotte intera apre Stanotte", async () => {
    const stanotte = await apriDashboard()

    expect(within(stanotte).getByRole("link", { name: "Meteo" }).getAttribute("href")).toBe("/meteo")
    fireEvent.click(within(stanotte).getByRole("button", { name: "Stanotte intera" }))
    expect(document.querySelector(".as-telaio")?.getAttribute("data-stanotte")).toBe("aperta")
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
  it("finche' i progetti non esistono la loro sezione lo dice, con Crea un progetto primario verso Progetti", async () => {
    const stanotte = await apriDashboard()

    const progetti = await screen.findByRole("region", { name: "progetti in corso" })
    expect(within(stanotte).queryByText(/^Nessun progetto in corso\./)).toBeNull()
    expect(within(progetti).getByText(/^Nessun progetto in corso\./)).toBeTruthy()
    const crea = within(progetti).getByRole("link", { name: "Crea un progetto" })
    expect(crea.getAttribute("href")).toBe("/progetti")
    expect(crea.className).toContain("as-bottone--primario")
    expect(progetti.parentElement?.className).toBe("as-dashboard__coppia")
  })

  it("col primario sui progetti Rispondi scende a tenue", async () => {
    await apriDashboard()

    const lavoro = await screen.findByRole("region", { name: "da riprendere" })
    expect((await within(lavoro).findByRole("link", { name: "Rispondi" })).className).toContain("as-bottone--tenue")
  })
})

describe("la Dashboard sul telefono", () => {
  const sulTelefono = () => apriDashboard({}, 390)

  it("ha il suo markup: stanotte col vuoto dei progetti, niente da riprendere e niente rimandi", async () => {
    const stanotte = await sulTelefono()

    expect(document.querySelector(".as-dashboard")?.className).toBe("as-dashboard as-tel-dash")
    expect(within(stanotte).getByText(/^Nessun progetto in corso\./)).toBeTruthy()
    expect(screen.queryByRole("region", { name: "da riprendere" })).toBeNull()
    expect(within(stanotte).queryByRole("link", { name: "Meteo" })).toBeNull()
  })

  it("le sei misure sono carte piccole; toccata, una apre sotto il suo grafico, chiudi lo richiude", async () => {
    const stanotte = await sulTelefono()

    const carte = [...stanotte.querySelectorAll<HTMLButtonElement>("button.as-tel-carta")]
    expect(carte.map((c) => c.querySelector(".as-tel-carta__nome")?.textContent)).toEqual(["Nuvole", "Seeing", "Jet stream", "Vento", "Condensa", "Aerosol"])
    const vento = carte[3] as HTMLButtonElement
    fireEvent.click(vento)
    const dettaglio = document.getElementById(vento.getAttribute("aria-controls") ?? "") as HTMLElement
    expect(dettaglio.className).toBe("as-tel-dettaglio")
    expect(dettaglio.hidden).toBe(false)
    expect(dettaglio.querySelector("svg")?.getAttribute("viewBox")).toBe("0 0 340 170")
    fireEvent.click(within(dettaglio).getByRole("button", { name: "chiudi" }))
    expect(dettaglio.hidden).toBe(true)
    expect(document.activeElement).toBe(vento)
  })

  it("le prossime 3 notti stanno in una riga sempre aperta, senza collegamenti", async () => {
    await sulTelefono()

    const riga = (await screen.findByRole("heading", { level: 3, name: "Le prossime 3 notti" })).closest("li") as HTMLElement
    expect(riga.className).toBe("as-tel-sez as-tel-sez--aperta")
    expect(riga.querySelectorAll("article.as-serata")).toHaveLength(3)
    expect(within(riga).queryAllByRole("link")).toHaveLength(0)
  })
})
