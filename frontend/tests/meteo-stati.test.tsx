// @vitest-environment jsdom
/**
 * Il **Meteo, gli stati** (`pagine/meteo-stati.html` del progetto Design, v37): gli stati difficili
 * della pagina, ognuno con la testa che resta, un avviso che dice cosa succede e, quando c'e', una
 * sola azione. Qui si prova la forma di ognuno: tono, titolo, azione, cosa resta in testa.
 */
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { pulisci } from "./banco"
import { NOTTE, apriMeteo, conNotti, meteo, misura, scheda } from "./meteo-banco"

afterEach(pulisci)
afterEach(() => vi.unstubAllGlobals())

const testa = () => document.querySelector(".as-meteo .as-meteo__testa") as HTMLElement
const aggiorna = () => screen.queryAllByRole("button", { name: /^aggiorna$/i })

/** L'avviso che dice quel titolo: tono, riga di pagina, testo e azione. */
async function avviso(titolo: RegExp) {
  const t = await screen.findByText(titolo, { selector: ".as-avviso__titolo" })
  const a = t.closest(".as-avviso") as HTMLElement
  return {
    classi: a.className,
    testo: a.querySelector(".as-avviso__testo")?.textContent ?? null,
    azione: a.querySelector(".as-avviso__azioni .as-bottone") as HTMLElement | null,
  }
}

describe("il Meteo, gli stati della pagina", () => {
  it("senza sito: la testa dice Meteo, l'avviso chiede il sito con Aggiungi sito", async () => {
    meteo({ site: null })
    await apriMeteo()

    const a = await avviso(/^Sito predefinito mancante$/)
    expect(a.classi).toBe("as-avviso as-avviso--attesa as-avviso--pagina")
    expect(a.testo).toBe("La previsione richiede un sito predefinito.")
    expect(a.azione?.textContent).toBe("Aggiungi sito")
    expect(a.azione?.className).toContain("as-bottone--primario")
    expect(testa().querySelector(".as-soprattitolo")?.textContent).toBe("Meteo")
  })

  it("senza fuso: la testa del sito senza Aggiorna, l'allarme col solo titolo e Modifica sito", async () => {
    meteo({ missing: "no_timezone" })
    await apriMeteo()

    const a = await avviso(/^Fuso orario del sito non riconosciuto/)
    expect(a.classi).toBe("as-avviso as-avviso--allarme as-avviso--pagina")
    expect(a.testo).toBeNull()
    expect(a.azione?.textContent).toBe("Modifica sito")
    expect(a.azione?.className).toContain("as-bottone--primario")
    expect(testa().textContent).toContain("meteo a Casa")
    expect(testa().querySelector(".as-meteo__arrivo")?.textContent).toBe("")
    expect(aggiorna()).toHaveLength(0)
  })

  it("prima previsione non arrivata: la riga dell'arrivo resta vuota", async () => {
    meteo({})
    await apriMeteo()

    const a = await avviso(/^Nessuna previsione disponibile\.$/)
    expect(a.classi).toBe("as-avviso as-avviso--attesa as-avviso--pagina")
    expect(a.testo).toBe("La previsione si aggiorna ogni tre ore.")
    expect(testa().querySelector(".as-meteo__arrivo")?.textContent).toBe("")
    expect(aggiorna()).toHaveLength(1)
  })

  it("servizio che tace senza previsione valida: un allarme con Aggiorna primario, e nient'altro", async () => {
    meteo({ fetched_at: "2026-09-21T11:00:00.000Z", last_request: { at: "2026-09-25T12:00:00.000Z", status: "unreachable" }, nights: [] })
    await apriMeteo()

    const a = await avviso(/^Aggiornamento delle \S+ non riuscito\. Nessuna previsione disponibile\.$/)
    expect(a.classi).toBe("as-avviso as-avviso--allarme as-avviso--pagina")
    expect(a.azione?.className).toContain("as-bottone--primario")
    expect(screen.queryByText(/nessuna notte disponibile per questo modello/i)).toBeNull()
  })

  it("servizio che tace prima di ogni previsione: l'allarme sostituisce l'attesa della prima", async () => {
    meteo({ last_request: { at: "2026-09-25T12:00:00.000Z", status: "unreachable" } })
    await apriMeteo()

    const a = await avviso(/^Aggiornamento delle \S+ non riuscito\. Nessuna previsione disponibile\.$/)
    expect(a.classi).toContain("as-avviso--allarme")
    expect(screen.queryByText(/^Nessuna previsione disponibile\.$/)).toBeNull()
  })

  it("servizio che tace, previsione ancora buona: riga d'attesa sotto la testa, Aggiorna solo li' e tenue", async () => {
    meteo({ fetched_at: "2026-09-25T06:00:00.000Z", last_request: { at: "2026-09-25T12:00:00.000Z", status: "unreachable" }, nights: [NOTTE] })
    await apriMeteo()

    const a = await avviso(/^Aggiornamento delle \S+ non riuscito\. Previsione delle/)
    expect(a.classi).toBe("as-avviso as-avviso--attesa")
    expect(a.azione?.className).toContain("as-bottone--tenue")
    expect(aggiorna()).toHaveLength(1)
  })

  it("un modello senza notti: un avviso d'attesa col solo titolo", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [] })
    await apriMeteo()

    const a = await avviso(/^Nessuna notte disponibile per questo modello\.$/)
    expect(a.classi).toBe("as-avviso as-avviso--attesa as-avviso--pagina")
    expect(a.azione).toBeNull()
  })

  it("Meteoblue muto: riga d'attesa col titolo e Aggiorna tenue", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], seeing: { key: true, source: "meteoblue", meteoblue: "unreachable" } })
    await apriMeteo()

    const a = await avviso(/^Ultimo aggiornamento del seeing non riuscito: dati precedenti\.$/)
    expect(a.classi).toBe("as-avviso as-avviso--attesa")
    expect(a.azione?.textContent).toBe("Aggiorna")
    expect(a.azione?.className).toContain("as-bottone--tenue")
  })
})

describe("il Meteo, gli stati della notte", () => {
  it("Sole sempre su: la parola sola e, sotto, perche'", async () => {
    conNotti({ ...NOTTE, verdict: null, usable_hours: null, usable_since: null, usable_until: null, window: null, window_hours: 0 })
    await apriMeteo()

    const notte = await scheda()
    expect(notte.querySelector(".as-meteo__parola")?.textContent).toBe("Nessuna notte astronomica")
    expect(notte.querySelector(".as-meteo__quando")?.textContent).toBe("Il Sole non tramonta: nessuna ora di buio.")
  })

  it("non si sa: la parola sola, senza ore serene, e perche' non si valuta", async () => {
    conNotti({ ...NOTTE, verdict: null })
    await apriMeteo()

    const notte = await scheda()
    expect(notte.querySelector(".as-meteo__grande")).toBeNull()
    expect(notte.querySelector(".as-meteo__quando")?.textContent).toBe("Non valutabile: copertura nuvolosa incompleta per le ore di buio.")
  })
})

describe("il Meteo, la scala di destra", () => {
  const cielo = () => document.querySelector(".as-cielo") as HTMLElement

  it("il seeing senza chiave dice perche' anche nel bottone", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    const seeing = within(cielo()).getByRole("button", { name: "seeing · Richiede una chiave Meteoblue" })
    expect(seeing.getAttribute("aria-disabled")).toBe("true")
  })

  it("la metrica scelta scrive il suo valore ora per ora sotto la linea; la pioggia no", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    fireEvent.click(within(cielo()).getByRole("button", { name: "vento" }))
    // l'ora senza vento non ha numero: tre ore disegnate, due valori
    expect([...cielo().querySelectorAll(".as-scala__valore")].map((v) => v.textContent)).toEqual(["5", "5"])
    fireEvent.click(within(cielo()).getByRole("button", { name: "pioggia" }))
    expect(cielo().querySelectorAll(".as-scala__valore")).toHaveLength(0)
  })

  it("il vento dice quale linea sono le raffiche, la condensa quale l'aria e quale la rugiada", async () => {
    conNotti({ ...NOTTE, measures: [...NOTTE.measures, misura("condensation", { level: "go", value: 8 })] })
    await apriMeteo()

    await scheda()
    const scritte = () => [...cielo().querySelectorAll(".as-scala__eti[text-anchor='end']")].map((e) => e.textContent)
    fireEvent.click(within(cielo()).getByRole("button", { name: "vento" }))
    expect(scritte()).toEqual(["raffiche"])
    fireEvent.click(within(cielo()).getByRole("button", { name: "condensa" }))
    expect(scritte()).toEqual(["rugiada", "aria"])
  })
})
