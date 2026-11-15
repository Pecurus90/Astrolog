// @vitest-environment jsdom
/**
 * Impostazioni v82, il guscio e Generale: linguette e indirizzi delle sezioni, l'indice del
 * telefono, nome, lingua e tema che si salvano e valgono subito, il salvataggio non riuscito.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  SITO_DI_CASA,
  SPINA,
  STANOTTE,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  scritture,
  type Voce,
} from "./banco"
import { impronta } from "./impronta"

afterEach(pulisci)

const BASE = impostazioni(true)

function app(extra: Record<string, Voce> = {}, valori: Record<string, unknown> = {}) {
  const corpo = { ...BASE, values: { ...BASE.values, ...valori } }
  rispondi({
    ...extra,
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/sites": {
      stato: 200,
      corpo: { items: [SITO_DI_CASA], total: 1, limit: 50, offset: 0 },
    },
    ...SPINA,
  })
  return disegna()
}

/** La risposta di una scrittura: le impostazioni come ora sono. */
const scritte = (valori: Record<string, unknown>): Voce => ({
  stato: 200,
  corpo: { ...BASE, values: { ...BASE.values, ...valori } },
})

describe("Impostazioni, il guscio", () => {
  it("ogni linguetta e' un indirizzo, coi nomi della tavola", async () => {
    window.history.pushState({}, "", "/impostazioni/astap")
    await app()

    const linguette = await screen.findByRole("tablist", { name: "Sezioni" })
    expect(
      within(linguette)
        .getAllByRole("tab")
        .map((x) => x.textContent),
    ).toEqual([
      "Generale",
      "Siti",
      "Cartelle e scansione",
      "ASTAP",
      "Luna",
      "Servizi",
      "Scansioni",
      "Backup",
    ])
    expect(
      within(linguette).getByRole("tab", { name: "ASTAP" }).getAttribute("aria-selected"),
    ).toBe("true")
    // la riga accanto al titolo dice cosa c'e' nella sezione
    expect(screen.getByText("identificazione degli oggetti")).toBeDefined()

    fireEvent.click(within(linguette).getByRole("tab", { name: "Generale" }))
    expect(window.location.pathname).toBe("/impostazioni/generale")
  })

  it("sul telefono si parte dall'indice, e la sezione torna indietro all'indice", async () => {
    window.history.pushState({}, "", "/impostazioni?formato=telefono")
    await app({}, { user_name: "Elena" })

    const indice = await screen.findByRole("list")
    const voci = within(indice).getAllByRole("listitem")
    expect(voci[0]!.textContent).toContain("Elena · modo scuro")
    await waitFor(() =>
      expect(voci[1]!.textContent).toContain(`1 sito · ${SITO_DI_CASA.name} predefinito`),
    )
    // le altre col loro riassunto della tavola
    expect(voci[3]!.textContent).toContain("identificazione degli oggetti")

    fireEvent.click(voci[0]!)
    expect(await screen.findByRole("textbox", { name: "Nome utente" })).toBeDefined()
    fireEvent.click(screen.getByRole("link", { name: "← Impostazioni" }))
    expect(await screen.findByRole("list")).toBeDefined()
  })
})

describe("Impostazioni, Generale", () => {
  it("il nome si cambia anche qui (Issue #19), e dice che e' salvato", async () => {
    window.history.pushState({}, "", "/impostazioni/generale")
    await app({ "PATCH /api/v1/settings": scritte({ user_name: "Elena" }) })

    const campo = await screen.findByRole("textbox", { name: "Nome utente" })
    fireEvent.change(campo, { target: { value: "  Elena " } })
    fireEvent.click(screen.getByText("Salva"))

    await waitFor(() =>
      expect(scritture()).toContainEqual(
        expect.objectContaining({ metodo: "PATCH", corpo: { values: { user_name: "Elena" } } }),
      ),
    )
    expect(await screen.findByText("✓ Salvato")).toBeDefined()
  })

  it("senza nome Salva e' spento, e non scrive", async () => {
    window.history.pushState({}, "", "/impostazioni/generale")
    await app()

    const salva = await screen.findByText("Salva")
    expect(salva.getAttribute("aria-disabled")).toBe("true")
    fireEvent.click(salva)
    expect(scritture().some((s) => s.metodo === "PATCH")).toBe(false)
  })

  it("la lingua scelta cambia le parole dell'app subito", async () => {
    window.history.pushState({}, "", "/impostazioni/generale")
    await app({ "PATCH /api/v1/settings": scritte({ language: "en" }) })

    const lingua = await screen.findByRole("radiogroup", { name: "Lingua" })
    fireEvent.click(within(lingua).getByRole("radio", { name: "English" }))

    expect(await screen.findByRole("tab", { name: "General" })).toBeDefined()
    expect(screen.getByRole("radio", { name: "English" }).getAttribute("aria-checked")).toBe("true")
  })

  it("il tema scelto si salva e veste l'app", async () => {
    window.history.pushState({}, "", "/impostazioni/generale")
    const { container } = await app({ "PATCH /api/v1/settings": scritte({ theme_mode: "chiaro" }) })

    const modo = await screen.findByRole("radiogroup", { name: "Modo" })
    // Automatico arriva col passo Tema (Marco 15/11/2026)
    expect(
      within(modo).getByRole("radio", { name: "Automatico" }).getAttribute("aria-disabled"),
    ).toBe("true")
    fireEvent.click(within(modo).getByRole("radio", { name: "Chiaro" }))

    await waitFor(() =>
      expect(scritture()).toContainEqual(
        expect.objectContaining({ corpo: { values: { theme_mode: "chiaro" } } }),
      ),
    )
    await waitFor(() =>
      expect(screen.getByRole("tablist").closest("[data-modo]")?.getAttribute("data-modo")).toBe(
        "chiaro",
      ),
    )
    expect(container.querySelector(".al-imp__griglia-1")).not.toBeNull()
  })

  it("sul telefono Salva compare solo per un nome cambiato, e sparisce dopo", async () => {
    window.history.pushState({}, "", "/impostazioni/generale?formato=telefono")
    await app({ "PATCH /api/v1/settings": scritte({ user_name: "Elena" }) }, { user_name: "Elena" })

    const campo = await screen.findByRole("textbox", { name: "Nome utente" })
    expect(screen.queryByText("Salva")).toBeNull()
    fireEvent.change(campo, { target: { value: " Elena " } })
    expect(screen.queryByText("Salva")).toBeNull()
    fireEvent.change(campo, { target: { value: "   " } })
    expect(screen.queryByText("Salva")).toBeNull()
    fireEvent.change(campo, { target: { value: "Elena B" } })
    fireEvent.click(screen.getByText("Salva"))
    await waitFor(() =>
      expect(scritture()).toContainEqual(
        expect.objectContaining({ corpo: { values: { user_name: "Elena B" } } }),
      ),
    )
    await waitFor(() => expect(screen.queryByText("Salva")).toBeNull())
  })

  it("Generale resta come nella consegna, su desktop e telefono", async () => {
    // impronta del markup della sezione: classi e misure per formato della tavola v82
    const visti: string[] = []
    for (const [indirizzo, classe] of [
      ["/impostazioni/generale", ".al-imp__griglia-2"],
      ["/impostazioni/generale?formato=telefono", ".al-imp__colonna-18"],
    ] as const) {
      window.history.pushState({}, "", indirizzo)
      const { container } = await app({}, { user_name: "Elena" })
      await screen.findByRole("textbox", { name: "Nome utente" })
      visti.push(impronta(container.querySelector(classe)?.outerHTML ?? ""))
      pulisci()
    }
    expect(visti).toEqual(["78f1ffd4", "eee3e93e"])
  })

  it("una sezione non ancora ridisegnata sta nel riquadro del foglio vecchio", async () => {
    window.history.pushState({}, "", "/impostazioni/astap")
    const { container } = await app({})

    expect(await screen.findByRole("tab", { name: "ASTAP" })).toBeDefined()
    // under data-modo the old sheet would take the new --inchiostro: `.app-vecchio` gives it back
    expect(screen.getByRole("tablist").closest("[data-modo]")).not.toBeNull()
    expect(container.querySelector(".al-imp__griglia-2 > .app-vecchio")).not.toBeNull()
    expect(container.querySelector(".al-imp__griglia-2:not(:has(.app-vecchio))")).toBeNull()
  })

  it("un salvataggio non riuscito lo dice in testa, e Riprova riscrive", async () => {
    window.history.pushState({}, "", "/impostazioni/generale")
    await app({ "PATCH /api/v1/settings": { stato: 500, corpo: {} } })

    fireEvent.click(
      within(await screen.findByRole("radiogroup", { name: "Accento" })).getByRole("radio", {
        name: /corallo/,
      }),
    )
    expect(
      await screen.findByText("Impostazione non salvata: AstroLog non risponde, riprova."),
    ).toBeDefined()

    fireEvent.click(screen.getByText("Riprova"))
    await waitFor(() => expect(scritture().filter((s) => s.metodo === "PATCH")).toHaveLength(2))
  })
})
