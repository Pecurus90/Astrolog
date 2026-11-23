// @vitest-environment jsdom
/**
 * Il **Meteo, gli stati** (tavola v82): gli stati difficili della pagina, ognuno con la testa che
 * resta, un avviso che dice cosa succede e, quando c'e', una sola azione. Qui si prova la forma di
 * ognuno: segno, titolo, azione, cosa resta in testa.
 */
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { pulisci } from "./banco"
import { NOTTE, apriMeteo, carta, conNotti, meteo, misura, scheda } from "./meteo-banco"

afterEach(pulisci)
afterEach(() => vi.unstubAllGlobals())

const testa = () => screen.getByRole("region", { name: "Le prossime notti" })
const aggiorna = () => screen.queryAllByRole("button", { name: /^aggiorna/i })
const modello = () => screen.queryByRole("button", { name: /^Modello:/ })

/** L'avviso che dice quel titolo: il segno, il testo sotto e l'azione. */
async function avviso(titolo: RegExp) {
  const t = await screen.findByText(titolo)
  const a = t.closest("[role=status]") as HTMLElement
  return {
    segno: a.querySelector("[aria-hidden=true]")?.textContent ?? null,
    pagina: a.classList.contains("al-c-avviso__griglia-1"),
    testo: a.querySelector(".al-c-avviso__testo-2")?.textContent ?? null,
    azione: within(a).queryByRole("button"),
  }
}

describe("il Meteo, gli stati della pagina", () => {
  it("se AstroLog non risponde la pagina lo dice, con Riprova che richiede la previsione", async () => {
    meteo({}, { "/api/v1/weather": { stato: 500, corpo: {} } })
    await apriMeteo()

    const a = await avviso(/^AstroLog non risponde, riprova$/)
    expect(a.segno).toBe("!")
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] })
    fireEvent.click(a.azione as HTMLElement)
    expect(await scheda()).toBeDefined()
  })

  it("senza sito: la testa senza modello ne' Aggiorna, l'avviso chiede il sito con Aggiungi sito", async () => {
    meteo({ site: null })
    await apriMeteo()

    const a = await avviso(/^Sito predefinito mancante$/)
    expect(a.segno).toBe("?")
    expect(a.pagina).toBe(true)
    expect(a.testo).toBe("La previsione richiede un sito predefinito.")
    expect(a.azione?.textContent).toBe("Aggiungi sito")
    expect(testa().textContent).toContain("Le prossime notti")
    expect(modello()).toBeNull()
    expect(aggiorna()).toHaveLength(0)
  })

  it("senza fuso: la testa del sito senza Aggiorna, l'allarme col solo titolo e Modifica sito", async () => {
    meteo({ missing: "no_timezone" })
    await apriMeteo()

    const a = await avviso(/^Fuso orario del sito non riconosciuto/)
    expect(a.segno).toBe("!")
    expect(a.pagina).toBe(true)
    expect(a.testo).toBeNull()
    expect(a.azione?.textContent).toBe("Modifica sito")
    expect(testa().textContent).not.toContain("Previsione Open-Meteo")
    expect(modello()).not.toBeNull()
    expect(aggiorna()).toHaveLength(0)
  })

  it("prima previsione non arrivata: la riga dell'arrivo resta vuota", async () => {
    meteo({})
    await apriMeteo()

    const a = await avviso(/^Nessuna previsione disponibile\.$/)
    expect(a.segno).toBe("?")
    expect(a.testo).toBe("La previsione si aggiorna ogni tre ore.")
    expect(testa().textContent).not.toContain("Previsione Open-Meteo")
    expect(aggiorna()).toHaveLength(1)
  })

  it("servizio che tace senza previsione valida: un allarme con Aggiorna, e nient'altro", async () => {
    meteo({ fetched_at: "2026-09-21T11:00:00.000Z", last_request: { at: "2026-09-25T12:00:00.000Z", status: "unreachable" }, nights: [] })
    await apriMeteo()

    const a = await avviso(/^Aggiornamento delle \S+ non riuscito\. Nessuna previsione disponibile\.$/)
    expect(a.segno).toBe("!")
    expect(a.pagina).toBe(true)
    expect(a.testo).toBe("Le notti dell'ultima previsione sono passate tutte.")
    expect(a.azione?.textContent).toBe("Aggiorna")
    expect(aggiorna()).toHaveLength(1)
    expect(screen.queryByText(/nessuna notte disponibile per questo modello/i)).toBeNull()
  })

  it("servizio che tace prima di ogni previsione: l'allarme sostituisce l'attesa della prima", async () => {
    meteo({ last_request: { at: "2026-09-25T12:00:00.000Z", status: "unreachable" } })
    await apriMeteo()

    const a = await avviso(/^Aggiornamento delle \S+ non riuscito\. Nessuna previsione disponibile\.$/)
    expect(a.segno).toBe("!")
    expect(screen.queryByText(/^Nessuna previsione disponibile\.$/)).toBeNull()
  })

  it("servizio che tace, previsione ancora buona: una riga sotto la testa, e Aggiorna solo li'", async () => {
    meteo({ fetched_at: "2026-09-25T06:00:00.000Z", last_request: { at: "2026-09-25T12:00:00.000Z", status: "unreachable" }, nights: [NOTTE] })
    await apriMeteo()

    const a = await avviso(/^Aggiornamento delle \S+ non riuscito\. Previsione delle/)
    expect(a.segno).toBe("!")
    expect(a.pagina).toBe(false)
    expect(a.azione?.textContent).toBe("Aggiorna")
    expect(testa().contains(a.azione)).toBe(true)
    expect(aggiorna()).toHaveLength(1)
  })

  it("un modello senza notti: un avviso d'attesa che manda agli altri modelli", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [] })
    await apriMeteo()

    const a = await avviso(/^Nessuna notte disponibile per questo modello\.$/)
    expect(a.segno).toBe("?")
    expect(a.testo).toBe("Gli altri modelli si scelgono qui sopra.")
    expect(a.azione).toBeNull()
  })

  it("Meteoblue muto: la carta del seeing lo dice, con Aggiorna accanto", async () => {
    const vista = { ...NOTTE, measures: NOTTE.measures.map((m) => (m.code === "seeing" ? misura("seeing", { level: "go", value: 1.2, axis_max: 5 }) : m)) }
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [vista], seeing: { key: true, source: "meteoblue", meteoblue: "unreachable" } })
    await apriMeteo()
    await scheda()

    const seeing = carta(/^Seeing$/)
    expect(seeing.textContent).toContain("Ultimo aggiornamento del seeing non riuscito: dati precedenti.")
    expect(within(seeing).getByRole("link", { name: "Aggiorna" })).toBeTruthy()
  })

  it("crediti Meteoblue finiti, anche senza seeing di prima: la chiave e' buona, si riprova", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], seeing: { key: true, source: null, meteoblue: "limited" } })
    await apriMeteo()
    await scheda()

    const seeing = carta(/^Seeing$/)
    expect(seeing.textContent).toContain("crediti o richieste esauriti. La chiave è buona, riprovo più tardi.")
    expect(seeing.textContent).not.toContain("chiave Meteoblue non valida")
  })
})

describe("il Meteo, gli stati della notte", () => {
  const valore = (n: HTMLElement) => n.querySelector(".al-meteo__testo-4")?.textContent
  const sotto = (n: HTMLElement) => n.querySelector(".al-meteo__testo-5")?.textContent

  it("Sole sempre su: la parola sola e, sotto, perche'", async () => {
    conNotti({ ...NOTTE, verdict: null, usable_hours: null, usable_since: null, usable_until: null, window: null, window_hours: 0 })
    await apriMeteo()

    const notte = await scheda()
    expect(valore(notte)).toBe("Nessun buio")
    expect(notte.querySelector(".al-meteo__pillola-1")).toBeNull()
    expect(sotto(notte)).toBe("Il Sole non tramonta: nessuna ora di buio.")
  })

  it("non si sa: la parola sola, senza ore serene, e perche' non si valuta", async () => {
    conNotti({ ...NOTTE, verdict: null })
    await apriMeteo()

    const notte = await scheda()
    expect(valore(notte)).toBe("Non disponibile")
    expect(notte.querySelector(".al-meteo__pillola-1")).toBeNull()
    expect(sotto(notte)).toBe("Non valutabile: copertura nuvolosa incompleta per le ore di buio.")
  })
})

describe("il Meteo, la scala di destra", () => {
  it("il seeing senza chiave dice perche' anche nel bottone", async () => {
    conNotti(NOTTE)
    await apriMeteo()
    await scheda()

    const seeing = within(screen.getByRole("group", { name: "Sul grafico" })).getByRole("checkbox", { name: "seeing" })
    expect(seeing.getAttribute("aria-disabled")).toBe("true")
    expect(seeing.getAttribute("title")).toBe("Il seeing richiede una chiave Meteoblue.")
    // toccato non si accende
    fireEvent.click(seeing)
    expect(seeing.getAttribute("aria-checked")).toBe("false")
  })
})
