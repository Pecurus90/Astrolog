// @vitest-environment jsdom
/**
 * La pagina **Attrezzatura** attorno al suo indice (tavola v82): cosa apre un indirizzo `?pezzo=`,
 * il telefono che porta su a ogni scelta, il vuoto che e' vuoto davvero.
 */
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { FILTRO, OTTICA, apriAttrezzatura, attrezzatura, carta, parti } from "./attrezzatura-banco"
import { disegna, pulisci } from "./banco"

const scrollTo = window.scrollTo

afterEach(() => {
  window.scrollTo = scrollTo
  delete (Element.prototype as Partial<Element>).scrollIntoView
  pulisci()
})

const indice = () => screen.findByRole("navigation", { name: /indice dell'attrezzatura/i })

describe("la pagina Attrezzatura", () => {
  it("non e' vuota se c'e' anche solo un pezzo, un setup o un filtro", async () => {
    attrezzatura({ rigs: [], filters: [] })
    await apriAttrezzatura()
    expect(await indice()).toBeDefined()
    expect(screen.queryByText(/^nessuna attrezzatura$/i)).toBeNull()
    pulisci()

    attrezzatura({ instruments: [], rigs: [] })
    await apriAttrezzatura()
    expect(await screen.findByRole("list", { name: /filtri/i })).toBeDefined()
    expect(screen.queryByText(/^nessuna attrezzatura$/i)).toBeNull()
  })

  it("un ?pezzo= che non c'e' piu' apre il primo setup, non un gruppo a caso", async () => {
    attrezzatura()
    // 3 e' l'id del filtro: come strumento non esiste
    window.history.pushState({}, "", `/attrezzatura?pezzo=strumento-${FILTRO.id}`)
    await disegna()
    expect(await carta()).toBeDefined()
    expect(screen.queryByRole("list", { name: /filtri/i })).toBeNull()
    pulisci()

    attrezzatura()
    window.history.pushState({}, "", `/attrezzatura?pezzo=filtro-${OTTICA.id}`)
    await disegna()
    expect(await carta()).toBeDefined()
    expect(screen.queryByRole("list", { name: /filtri/i })).toBeNull()
  })

  it("la riga cercata viene in vista", async () => {
    const vista = vi.fn()
    Element.prototype.scrollIntoView = vista
    attrezzatura()
    window.history.pushState({}, "", `/attrezzatura?pezzo=strumento-${OTTICA.id}`)
    await disegna()

    const telescopi = await screen.findByRole("list", { name: /telescopi/i })
    const riga = within(telescopi)
      .getByText(/TS 130 APO/)
      .closest("li") as HTMLElement
    expect(vista).toHaveBeenCalledWith({ block: "center" })
    expect(vista.mock.contexts).toContain(riga)
  })

  it("Aggiungi strumento si apre e si chiude, e porta in cima", async () => {
    const su = vi.fn()
    window.scrollTo = su as unknown as typeof window.scrollTo
    attrezzatura()
    await apriAttrezzatura()
    const aggiungi = await screen.findByRole("button", { name: /^aggiungi strumento$/i })
    expect(aggiungi.getAttribute("aria-expanded")).toBe("false")

    fireEvent.click(aggiungi)
    expect(aggiungi.getAttribute("aria-expanded")).toBe("true")
    expect(su).toHaveBeenCalledWith({ top: 0, behavior: "smooth" })

    su.mockClear()
    fireEvent.click(aggiungi)
    expect(aggiungi.getAttribute("aria-expanded")).toBe("false")
    expect(su).not.toHaveBeenCalled()
  })
})

describe("la pagina Attrezzatura sul telefono", () => {
  it("un ?pezzo= apre subito il suo gruppo a pagina intera, con la via per tornare", async () => {
    attrezzatura()
    window.history.pushState({}, "", `/attrezzatura?formato=telefono&pezzo=strumento-${OTTICA.id}`)
    await disegna()

    expect(await screen.findByRole("list", { name: /telescopi/i })).toBeDefined()
    expect(screen.queryByRole("navigation", { name: /indice dell'attrezzatura/i })).toBeNull()
    expect(screen.getByRole("button", { name: /attrezzatura/i })).toBeDefined()
  })

  it("un ?pezzo= che non c'e' piu' apre l'indice", async () => {
    attrezzatura()
    window.history.pushState({}, "", "/attrezzatura?formato=telefono&pezzo=strumento-999")
    await disegna()

    expect(await indice()).toBeDefined()
    expect(screen.queryByRole("region", { name: /^parti$/i })).toBeNull()
    expect(screen.queryByRole("button", { name: /^.?\s*attrezzatura$/i })).toBeNull()
  })

  it("una scelta dall'indice porta in cima, sul computer no", async () => {
    const su = vi.fn()
    window.scrollTo = su as unknown as typeof window.scrollTo
    attrezzatura()
    window.history.pushState({}, "", "/attrezzatura?formato=telefono")
    await disegna()
    fireEvent.click(within(await indice()).getByRole("link", { name: /il grande/i }))
    expect(await parti()).toBeDefined()
    expect(su).toHaveBeenCalledWith({ top: 0, behavior: "smooth" })
    pulisci()

    su.mockClear()
    attrezzatura()
    await apriAttrezzatura()
    fireEvent.click(within(await indice()).getByRole("link", { name: /il grande/i }))
    expect(await parti()).toBeDefined()
    expect(su).not.toHaveBeenCalled()
  })
})
