// @vitest-environment jsdom
/**
 * Il **Meteo sul telefono** (colonna sotto i 900, foglio v37): gli stessi dati della pagina larga,
 * in un markup suo. In testa il verdetto, che toccato apre gli altri fattori; le misure sono carte
 * piccole, quattro per riga, e una alla volta apre la sua carta intera sulla riga sotto.
 */
import { fireEvent, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { pulisci } from "./banco"
import { NOTTE, TENDENZA, apriMeteo, conNotti, misura, scheda } from "./meteo-banco"

afterEach(pulisci)
afterEach(() => vi.unstubAllGlobals())

/** La colonna misurata: jsdom non impagina, quindi la misura la da' la prova. */
function colonna(larga: number) {
  vi.stubGlobal(
    "ResizeObserver",
    class {
      constructor(private dice: (v: { contentRect: { width: number } }[]) => void) {}
      observe() {
        this.dice([{ contentRect: { width: larga } }])
      }
      disconnect() {}
    },
  )
}

async function sulTelefono(...notti: unknown[]) {
  conNotti(...notti)
  // dopo `conNotti`: il banco non deve togliere la misura
  colonna(390)
  const { container } = await apriMeteo()
  await scheda()
  return container
}

const piccole = (dove: HTMLElement) => [...dove.querySelectorAll<HTMLButtonElement>("button.as-tel-carta")]
const nomi = (dove: HTMLElement) => piccole(dove).map((c) => c.querySelector(".as-tel-carta__nome")?.textContent)
const piccola = (dove: HTMLElement, nome: string) => piccole(dove).find((c) => c.querySelector(".as-tel-carta__nome")?.textContent === nome) as HTMLButtonElement

describe("il Meteo sul telefono", () => {
  it("sulla pagina larga le carte sono quelle grandi, e le piccole del telefono non ci sono", async () => {
    conNotti(NOTTE)
    colonna(1440)
    const { container } = await apriMeteo()

    await scheda()
    expect(container.querySelector(".as-tel-meteo")).toBeNull()
    expect(container.querySelector(".as-tel-carte")).toBeNull()
    expect(container.querySelectorAll(".as-parametri article.as-parametro").length).toBeGreaterThan(0)
  })

  it("le misure sono carte piccole, ognuna al suo posto, col nome, il valore e la parola sola", async () => {
    const pagina = await sulTelefono(NOTTE)

    expect(pagina.querySelector(".as-meteo")?.classList.contains("as-tel-meteo")).toBe(true)
    expect(pagina.querySelector(".as-parametri")).toBeNull()
    expect(nomi(pagina)).toEqual([
      "Nuvole", "Nuvole basse", "Pioggia", "Visibilità", "Vento", "Seeing", "Aerosol",
      "Temperatura e rugiada", "Polvere", "Vento a 700 hPa",
    ])
    const vento = piccola(pagina, "Vento")
    expect(vento.querySelector(".as-tel-carta__valore")?.textContent).toBe("20km/h")
    // la parola sola: le ore le dice la carta aperta
    expect(vento.querySelector(".as-semaforo")?.textContent).toBe("non adatta")
    expect(vento.getAttribute("aria-expanded")).toBe("false")
    // le nuvole non hanno parola: e' il verdetto
    expect(piccola(pagina, "Nuvole").querySelector(".as-semaforo")).toBeNull()
    // nessuna carta intera finche' non se ne tocca una
    expect(pagina.querySelector("article.as-parametro")).toBeNull()
  })

  it("una misura senza valore ha la carta piccola vuota, col semaforo spento e la parola che lo dice", async () => {
    // Design, DECISIONI 14/10: niente trattino, la stessa parola a schermo e allo screen reader
    const cieca = { ...NOTTE, measures: NOTTE.measures.map((m) => (m.code === "wind" ? { ...m, value: null, level: null, known_hours: 0 } : m)) }
    const pagina = await sulTelefono(cieca)

    // come la tavola meteo-stati v37.1: niente righe del valore e delle barrette, la parola minuscola
    const vento = piccola(pagina, "Vento")
    expect(vento.querySelector(".as-tel-carta__valore, .as-tel-carta__barre")).toBeNull()
    const semaforo = vento.querySelector(".as-semaforo") as HTMLElement
    expect(semaforo.classList.contains("as-semaforo--ignoto")).toBe(true)
    expect(semaforo.textContent).toBe("non disponibile")
    expect(vento.querySelector(".as-solo-lettori")).toBeNull()
  })

  it("toccata, una carta apre la sua carta intera sotto; un'altra la sostituisce, lo stesso tocco la chiude", async () => {
    const pagina = await sulTelefono(NOTTE)

    fireEvent.click(piccola(pagina, "Vento"))
    const vento = piccola(pagina, "Vento")
    expect(vento.getAttribute("aria-expanded")).toBe("true")
    const dettaglio = document.getElementById(vento.getAttribute("aria-controls") ?? "") as HTMLElement
    expect(dettaglio.classList.contains("as-tel-dettaglio")).toBe(true)
    expect(within(dettaglio).getByRole("heading", { level: 3 }).textContent).toBe("Vento")
    expect(dettaglio.textContent).toContain("non adatta dalle 21:00")

    fireEvent.click(piccola(pagina, "Pioggia"))
    expect(piccola(pagina, "Vento").getAttribute("aria-expanded")).toBe("false")
    expect(pagina.querySelectorAll("article.as-parametro")).toHaveLength(1)
    expect(within(pagina).getByRole("heading", { level: 3 }).textContent).toBe("Pioggia")

    fireEvent.click(piccola(pagina, "Pioggia"))
    expect(pagina.querySelector("article.as-parametro")).toBeNull()
  })

  it("in testa il verdetto della notte e il modello; sotto, da quando e' la previsione e Aggiorna", async () => {
    const pagina = await sulTelefono(NOTTE)

    const testa = pagina.querySelector(".as-tel-testa") as HTMLElement
    expect(testa.querySelector(".as-tel-verdetto")?.textContent).toContain("Notte di sabato 26 · stanotte")
    expect(testa.querySelector(".as-tel-verdetto")?.textContent).toContain("3 ore di buio sereno")
    expect(testa.querySelector(".as-menu--telefono .as-menu__apri")?.textContent).toContain("Automatico")
    const arrivo = pagina.querySelector(".as-tel-arrivo") as HTMLElement
    expect(arrivo.textContent).toContain("Previsione del")
    expect(within(arrivo).getByRole("button", { name: "Aggiorna" })).toBeTruthy()
    // il verdetto sta in testa: la scheda non lo ripete
    expect((await scheda()).querySelector(".as-meteo__notte")).toBeNull()
  })

  it("toccato il verdetto si aprono gli altri fattori; una misura li chiude e apre la sua carta", async () => {
    const pagina = await sulTelefono(NOTTE)

    const verdetto = within(pagina).getByRole("button", { name: /Altri fattori/ })
    expect(verdetto.getAttribute("aria-expanded")).toBe("false")
    const riquadro = document.getElementById(verdetto.getAttribute("aria-controls") ?? "") as HTMLElement
    expect(riquadro.hidden).toBe(true)

    fireEvent.click(verdetto)
    expect(verdetto.getAttribute("aria-expanded")).toBe("true")
    expect(riquadro.hidden).toBe(false)
    expect(riquadro.textContent).toContain("Altri fattori (non modificano il verdetto)")
    expect(riquadro.textContent).toContain("Vento dalle 21:00 alle 23:00 · 2 ore")

    fireEvent.click(within(riquadro).getByRole("button", { name: /Vento/ }))
    expect(riquadro.hidden).toBe(true)
    expect(piccola(pagina, "Vento").getAttribute("aria-expanded")).toBe("true")
    // il fuoco va alla carta che si e' aperta, non si perde
    expect(document.activeElement).toBe(piccola(pagina, "Vento"))
  })

  it("con Tab il fuoco gira dentro gli altri fattori; richiusi col verdetto, il fuoco torna li'", async () => {
    const luna = misura("moon", { level: "nogo", weighs: true, value: 62, known_hours: 2 })
    const pagina = await sulTelefono({ ...NOTTE, measures: [...NOTTE.measures, luna] })

    const verdetto = within(pagina).getByRole("button", { name: /Altri fattori/ })
    fireEvent.click(verdetto)
    const riquadro = pagina.querySelector(".as-tel-pesanti") as HTMLElement
    const bottoni = [...riquadro.querySelectorAll("button")]
    const ultimo = bottoni[bottoni.length - 1] as HTMLElement
    ultimo.focus()
    fireEvent.keyDown(ultimo, { key: "Tab" })
    expect(document.activeElement).toBe(bottoni[0])
    fireEvent.keyDown(bottoni[0] as HTMLElement, { key: "Tab", shiftKey: true })
    expect(document.activeElement).toBe(ultimo)

    fireEvent.click(verdetto)
    expect(riquadro.hidden).toBe(true)
    expect(document.activeElement).toBe(verdetto)
  })

  it("aperti, gli altri fattori prendono il fuoco; Esc li chiude e lo rende al verdetto", async () => {
    const calma = { ...NOTTE, measures: NOTTE.measures.map((m) => ({ ...m, weighs: false })) }
    const pagina = await sulTelefono(calma)

    const verdetto = within(pagina).getByRole("button", { name: /Altri fattori/ })
    fireEvent.click(verdetto)
    const riquadro = pagina.querySelector(".as-tel-pesanti") as HTMLElement
    expect(riquadro.hidden).toBe(false)
    expect(riquadro.textContent).toContain("Nessun altro fattore.")
    expect(riquadro.contains(document.activeElement)).toBe(true)
    fireEvent.keyDown(document.activeElement as HTMLElement, { key: "Escape" })
    expect(riquadro.hidden).toBe(true)
    expect(document.activeElement).toBe(verdetto)
  })

  it("toccando fuori gli altri fattori si chiudono; toccando dentro restano", async () => {
    const pagina = await sulTelefono(NOTTE)

    const verdetto = within(pagina).getByRole("button", { name: /Altri fattori/ })
    fireEvent.click(verdetto)
    const riquadro = pagina.querySelector(".as-tel-pesanti") as HTMLElement
    fireEvent.mouseDown(riquadro.querySelector("li") as HTMLElement)
    expect(riquadro.hidden).toBe(false)
    fireEvent.mouseDown(piccola(pagina, "Pioggia"))
    expect(riquadro.hidden).toBe(true)
    // il verdetto toccato di nuovo li riapre, non li chiude e riapre
    fireEvent.mouseDown(verdetto)
    fireEvent.click(verdetto)
    expect(riquadro.hidden).toBe(false)
  })

  it("cambiando modello la carta aperta si chiude", async () => {
    const pagina = await sulTelefono(NOTTE)

    fireEvent.click(piccola(pagina, "Vento"))
    expect(pagina.querySelector("article.as-parametro")).not.toBeNull()
    const menu = pagina.querySelector(".as-tel-testa .as-menu--telefono") as HTMLElement
    fireEvent.click(menu.querySelector(".as-menu__apri") as HTMLElement)
    fireEvent.click(within(menu).getAllByRole("menuitemradio")[1] as HTMLElement)
    expect(pagina.querySelector("article.as-parametro")).toBeNull()
  })

  it("la Luna fra gli altri fattori non e' un bottone: non ha una carta da aprire", async () => {
    const luna = misura("moon", {
      level: "nogo", weighs: true, value: 62, known_hours: 2, known_from_start: false, known_to_end: true,
      known_since: "2026-09-26T23:00:00+02:00", known_until: "2026-09-27T02:00:00+02:00",
    })
    const pagina = await sulTelefono({ ...NOTTE, measures: [...NOTTE.measures, luna] })

    fireEvent.click(within(pagina).getByRole("button", { name: /Altri fattori/ }))
    const riquadro = pagina.querySelector(".as-tel-pesanti") as HTMLElement
    expect(riquadro.textContent).toContain("Luna")
    expect(within(riquadro).queryByRole("button", { name: /Luna/ })).toBeNull()
  })

  it("senza notti il telefono tiene la sua testa: il modello, da quando e' la previsione e Aggiorna", async () => {
    conNotti()
    colonna(390)
    const { container: pagina } = await apriMeteo()

    await within(pagina).findByText("Nessuna notte disponibile per questo modello.")
    expect(pagina.querySelector(".as-meteo__testa")).toBeNull()
    const testa = pagina.querySelector(".as-tel-testa") as HTMLElement
    expect(testa.querySelector(".as-tel-verdetti")).toBeNull()
    expect(testa.querySelector(".as-menu--telefono .as-menu__apri")?.textContent).toContain("Automatico")
    const arrivo = pagina.querySelector(".as-tel-arrivo") as HTMLElement
    expect(within(arrivo).getByRole("button", { name: "Aggiorna" })).toBeTruthy()
  })

  it("una notte in tendenza ha il verdetto in testa e nessun riquadro da aprire", async () => {
    const pagina = await sulTelefono(NOTTE, TENDENZA)

    fireEvent.click(within(pagina).getAllByRole("tab")[1] as HTMLElement)
    const testa = pagina.querySelector(".as-tel-testa") as HTMLElement
    expect(testa.textContent).toContain("tendenza")
    expect(within(testa).queryByRole("button", { name: /Altri fattori/ })).toBeNull()
    expect(pagina.querySelector(".as-tel-carte")).toBeNull()
    expect((await scheda()).textContent).toContain("Dalla quarta notte")
  })

  it("cambiando notte la carta aperta e gli altri fattori si chiudono", async () => {
    const pagina = await sulTelefono(NOTTE, { ...NOTTE, night: "2026-09-27" })

    fireEvent.click(piccola(pagina, "Vento"))
    fireEvent.click(within(pagina).getByRole("button", { name: /Altri fattori/ }))
    expect(pagina.querySelector("article.as-parametro")).not.toBeNull()
    expect((pagina.querySelector(".as-tel-pesanti") as HTMLElement).hidden).toBe(false)
    fireEvent.click(within(pagina).getAllByRole("tab")[1] as HTMLElement)
    expect(pagina.querySelector("article.as-parametro")).toBeNull()
    expect((pagina.querySelector(".as-tel-pesanti") as HTMLElement).hidden).toBe(true)
  })

  it("l'umidita' si accende dal menu della scala di destra, con le altre voci", async () => {
    const pagina = await sulTelefono(NOTTE)

    const menu = pagina.querySelector(".as-cielo .as-menu--telefono") as HTMLElement
    fireEvent.click(menu.querySelector(".as-menu__apri") as HTMLElement)
    const umidita = within(menu).getByRole("menuitemcheckbox", { name: /umidit/i })
    expect(umidita.getAttribute("aria-checked")).toBe("false")
    fireEvent.click(umidita)
    expect(within(menu).getByRole("menuitemcheckbox", { name: /umidit/i }).getAttribute("aria-checked")).toBe("true")
    // il bottone a parte e' della pagina larga
    expect(pagina.querySelector(".as-cielo .as-strati > button.as-strato:not(.as-meteo__solo-largo)")).toBeNull()
  })
})
