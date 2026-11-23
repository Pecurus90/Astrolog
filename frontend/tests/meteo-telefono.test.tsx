// @vitest-environment jsdom
/**
 * Il **Meteo sul telefono** (tavola v82, sotto i 700 o `?formato=telefono`): gli stessi dati della
 * pagina larga, in un markup suo. Le misure sono carte piccole, due per riga, e una alla volta apre
 * il suo dettaglio sotto la sua coppia.
 */
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { impostazioni, pulisci } from "./banco"
import { NOTTE, TENDENZA, apriMeteo, apriMeteoTelefono, comeVa, conNotti, meteo, misura, ora, scheda } from "./meteo-banco"

afterEach(pulisci)
afterEach(() => vi.unstubAllGlobals())

async function sulTelefono(...notti: unknown[]) {
  conNotti(...notti)
  const { container } = await apriMeteoTelefono()
  await scheda()
  return container
}

const piccole = (dove: HTMLElement) => [...dove.querySelectorAll<HTMLElement>("a.al-c-card-meteo__colonna-7")]
const nomeDi = (c: HTMLElement) => c.querySelector(".al-c-card-meteo__riga-8 > span")?.textContent
const nomi = (dove: HTMLElement) => piccole(dove).map(nomeDi)
const piccola = (dove: HTMLElement, nome: string) => piccole(dove).find((c) => nomeDi(c) === nome) as HTMLElement
const dettagli = (dove: HTMLElement) => [...dove.querySelectorAll<HTMLElement>(".al-meteo__colonna-24")]
const sulGrafico = (nome: string) => within(screen.getByRole("group", { name: "Sul grafico" })).getByRole("checkbox", { name: nome })

describe("il Meteo sul telefono", () => {
  it("sulla pagina larga le carte sono quelle grandi, e le piccole del telefono non ci sono", async () => {
    conNotti(NOTTE)
    const { container } = await apriMeteo()
    await scheda()

    expect(piccole(container)).toHaveLength(0)
    expect(container.querySelectorAll(".al-c-card-meteo__colonna-1").length).toBeGreaterThan(0)
  })

  it("le misure sono carte piccole, ognuna al suo posto, col nome, il valore e la parola sola", async () => {
    const pagina = await sulTelefono(NOTTE)

    expect(pagina.querySelector(".al-c-card-meteo__colonna-1")).toBeNull()
    expect(nomi(pagina)).toEqual(["Nuvole", "Nuvole basse", "Pioggia", "Visibilità", "Vento", "Seeing", "Aerosol"])
    const vento = piccola(pagina, "Vento")
    expect(vento.querySelector(".al-c-card-meteo__testo-9")?.textContent).toBe("20")
    expect(vento.querySelector(".al-c-card-meteo__testo-10")?.textContent).toBe("km/h")
    // la parola sola: le ore le dice il dettaglio aperto
    expect(vento.textContent).toContain("non adatta")
    expect(vento.textContent).not.toContain("dalle")
    expect(vento.getAttribute("aria-expanded")).toBe("false")
    // nessun dettaglio finche' non se ne tocca una
    expect(dettagli(pagina)).toHaveLength(0)
  })

  it("una misura senza valore ha la carta piccola vuota, col semaforo spento e la parola che lo dice", async () => {
    const cieca = { ...NOTTE, measures: NOTTE.measures.map((m) => (m.code === "wind" ? { ...m, value: null, level: null, known_hours: 0 } : m)) }
    const pagina = await sulTelefono(cieca)

    const vento = piccola(pagina, "Vento")
    expect(vento.querySelector(".al-c-card-meteo__testo-9")?.textContent).toBe("?")
    expect(vento.querySelector(".al-c-card-meteo__testo-10")).toBeNull()
    const barre = [...vento.querySelectorAll<HTMLElement>(".al-c-card-meteo__pillola-3")]
    expect(barre.every((b) => b.style.background.startsWith("repeating-linear-gradient"))).toBe(true)
    expect(vento.textContent).toContain("non disponibile")
  })

  it("toccata, una carta apre la sua carta intera sotto; un'altra la sostituisce, lo stesso tocco la chiude", async () => {
    const pagina = await sulTelefono(NOTTE)

    fireEvent.click(piccola(pagina, "Vento"))
    expect(piccola(pagina, "Vento").getAttribute("aria-expanded")).toBe("true")
    const [dettaglio] = dettagli(pagina)
    expect(dettaglio?.querySelector("b")?.textContent).toBe("Vento")
    expect(dettaglio?.textContent).toContain("media nel buio · a 10 m")
    expect(dettaglio?.textContent).toContain("non adatta dalle 21:00 alle 23:00, 2 ore")

    fireEvent.click(piccola(pagina, "Pioggia"))
    expect(piccola(pagina, "Vento").getAttribute("aria-expanded")).toBe("false")
    expect(dettagli(pagina)).toHaveLength(1)
    expect(dettagli(pagina)[0]?.querySelector("b")?.textContent).toBe("Pioggia")

    fireEvent.click(piccola(pagina, "Pioggia"))
    expect(dettagli(pagina)).toHaveLength(0)
  })

  it("in testa il modello, Aggiorna e da quando e' la previsione, che toccato si dice per intero", async () => {
    await sulTelefono(NOTTE)

    const testa = screen.getByRole("region", { name: "Le prossime notti" })
    expect(within(testa).getByRole("button", { name: "Modello: Automatico" })).toBeTruthy()
    expect(within(testa).getByRole("button", { name: "Aggiorna la previsione" })).toBeTruthy()
    const arrivo = within(testa).getByRole("button", { name: /^Previsione Open-Meteo del/ })
    expect(arrivo.textContent).toMatch(/^Open-Meteo .+ fa$/)
    fireEvent.click(arrivo)
    expect(arrivo.getAttribute("aria-expanded")).toBe("true")
    expect(arrivo.textContent).toContain("ora locale del sito")
  })

  it("fra gli altri fattori una misura del grafico si accende toccandola; la Luna e le raffiche no", async () => {
    const luna = misura("moon", {
      level: "nogo", weighs: true, value: 62, known_from_start: false, known_to_end: true,
      known_since: "2026-09-26T23:00:00+02:00", known_until: "2026-09-27T02:00:00+02:00",
    })
    await sulTelefono({ ...NOTTE, measures: [...NOTTE.measures, luna] })

    fireEvent.click(within(comeVa()).getByRole("button", { name: /^Altri \d+ fattori$/ }))
    expect(comeVa().textContent).toContain("Luna")
    expect(within(comeVa()).queryByRole("button", { name: /^Luna/ })).toBeNull()
    expect(within(comeVa()).queryByRole("button", { name: /^Raffiche/ })).toBeNull()
    fireEvent.click(within(comeVa()).getByRole("button", { name: /^Vento/ }))
    expect(sulGrafico("vento").getAttribute("aria-checked")).toBe("true")
  })

  it("cambiando modello la carta aperta si chiude", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] }, {
      "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    })
    const { container: pagina } = await apriMeteoTelefono()
    await scheda()

    fireEvent.click(piccola(pagina, "Vento"))
    expect(dettagli(pagina)).toHaveLength(1)
    fireEvent.click(screen.getByRole("button", { name: "Modello: Automatico" }))
    fireEvent.click(screen.getAllByRole("menuitemradio")[1] as HTMLElement)
    expect(dettagli(pagina)).toHaveLength(0)
  })

  it("senza notti il telefono ha la testa: da quando e' la previsione, Aggiorna e il modello", async () => {
    conNotti()
    await apriMeteoTelefono()

    await screen.findByText("Nessuna notte disponibile per questo modello.")
    const testa = screen.getByRole("region", { name: "Le prossime notti" })
    expect(within(testa).getByRole("button", { name: /^Previsione Open-Meteo del/ })).toBeTruthy()
    expect(within(testa).getByRole("button", { name: "Modello: Automatico" })).toBeTruthy()
    expect(within(testa).getByRole("button", { name: "Aggiorna la previsione" })).toBeTruthy()
    expect(screen.queryByRole("tablist")).toBeNull()
  })

  it("nella fila delle notti le Ore di posa e la finestra stanno su due righe", async () => {
    await sulTelefono(NOTTE)

    const tessera = screen.getAllByRole("tab")[0] as HTMLElement
    expect(tessera.querySelector(".al-c-striscia__testo-7")?.textContent).toBe("3,0 ore")
    expect(tessera.querySelector(".al-c-striscia__testo-8")?.textContent).toBe("23–02")
  })

  it("il cielo ha la tela del telefono: le ore ogni quattro, solo i confini del buio, e la legenda senza note", async () => {
    const ore = [19, 20, 21, 22, 23].map((h) => ora(`2026-09-26T${h}:00:00+02:00`, "dark"))
    const notte = await sulTelefono({ ...NOTTE, hours: [...ore, ora("2026-09-27T00:00:00+02:00", "dark")] })

    const laNotte = screen.getByRole("region", { name: "La notte" })
    const sotto = laNotte.querySelector(".al-meteo__riga-26") as HTMLElement
    expect([...sotto.children].map((s) => s.textContent)).toEqual(["20", "00"])
    const tela = screen.getByRole("slider", { name: /^Il cielo/ }).parentElement?.parentElement as HTMLElement
    expect([...(tela.firstElementChild?.children ?? [])].map((s) => s.textContent)).toEqual(["21:00"])
    fireEvent.click(sulGrafico("pioggia"))
    expect(laNotte.textContent).toContain("Pioggia")
    expect(laNotte.textContent).not.toContain("a destra, col colore del giudizio")
    expect(notte.querySelector(".al-meteo__riga-6")).toBeNull()
  })

  it("una notte in tendenza sul telefono: il buio in grande, e niente carte delle misure", async () => {
    await sulTelefono(NOTTE, TENDENZA)

    fireEvent.click(screen.getAllByRole("tab")[1] as HTMLElement)
    const notte = await scheda()
    expect(notte.textContent).toMatch(/Buio · notte di \S+ 29 · tendenza/)
    expect(notte.querySelector(".al-meteo__testo-25")?.textContent).toBe("8 ore")
    expect(notte.textContent).toContain("Dalla quarta notte")
    expect(screen.queryByRole("region", { name: "Le misure" })).toBeNull()
  })

  it("cambiando notte la carta aperta si chiude", async () => {
    const pagina = await sulTelefono(NOTTE, { ...NOTTE, night: "2026-09-27" })

    fireEvent.click(piccola(pagina, "Vento"))
    expect(dettagli(pagina)).toHaveLength(1)
    fireEvent.click(screen.getAllByRole("tab")[1] as HTMLElement)
    expect(dettagli(pagina)).toHaveLength(0)
    expect(piccola(pagina, "Vento").getAttribute("aria-expanded")).toBe("false")
  })

  it("l'umidita' si accende fra le voci di «Sul grafico», con le altre", async () => {
    await sulTelefono(NOTTE)

    const voci = within(screen.getByRole("group", { name: "Sul grafico" })).getAllByRole("checkbox")
    expect(voci.map((v) => v.textContent)).toEqual(["umidità %", "pioggia", "vento", "seeing", "aerosol", "visibilità"])
    expect(sulGrafico("umidità %").getAttribute("aria-checked")).toBe("false")
    fireEvent.click(sulGrafico("umidità %"))
    expect(sulGrafico("umidità %").getAttribute("aria-checked")).toBe("true")
  })
})
