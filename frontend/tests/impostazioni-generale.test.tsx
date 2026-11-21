// @vitest-environment jsdom
/**
 * Impostazioni v82, il guscio e Generale: linguette e indirizzi delle sezioni, l'indice del
 * telefono, nome, lingua e tema che si salvano e valgono subito, il salvataggio non riuscito.
 */
import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import {
  SALUTE,
  SITO_DI_CASA,
  SPINA,
  STANOTTE,
  chiamate,
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

function app(
  extra: Record<string, Voce> = {},
  valori: Record<string, unknown> = {},
  resto: Record<string, unknown> = {},
) {
  const corpo = { ...BASE, ...resto, values: { ...BASE.values, ...valori } }
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
      "Meteo",
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
    expect(voci[4]!.textContent).toContain("identificazione degli oggetti")

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

  it("con l'inglese salvato l'app si apre in inglese, senza un attimo d'italiano", async () => {
    window.history.pushState({}, "", "/impostazioni/generale")
    let italiano = false
    const spia = new MutationObserver(() => {
      if (document.body.textContent?.includes("Cartelle e scansione")) italiano = true
    })
    spia.observe(document.body, { childList: true, subtree: true, characterData: true })
    await app({}, { language: "en" })

    expect(await screen.findByRole("tab", { name: "General" })).toBeDefined()
    spia.disconnect()
    expect(italiano).toBe(false)
  })

  it("il tema scelto si salva e veste l'app", async () => {
    window.history.pushState({}, "", "/impostazioni/generale")
    const { container } = await app({ "PATCH /api/v1/settings": scritte({ theme_mode: "chiaro" }) })

    const modo = await screen.findByRole("radiogroup", { name: "Modo" })
    // c'e' il sito di casa: Automatico si sceglie (tavola v82)
    expect(
      within(modo).getByRole("radio", { name: "Automatico" }).getAttribute("aria-disabled"),
    ).toBeNull()
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

  it("automatico veste il modo che l'API dice in vigore e nomina il sito di casa", async () => {
    window.history.pushState({}, "", "/impostazioni/generale")
    const ora = { mode: "chiaro", until: "2026-10-16T18:27:00+02:00" }
    await app({}, { theme_mode: "automatico" }, { theme_now: ora })

    const modo = await screen.findByRole("radiogroup", { name: "Modo" })
    const auto = within(modo).getByRole("radio", { name: "Automatico" })
    expect(auto.getAttribute("aria-checked")).toBe("true")
    screen.getByText("Scuro dal tramonto all'alba di Vicenza, chiaro di giorno.")
    expect(screen.getByRole("tablist").closest("[data-modo]")?.getAttribute("data-modo")).toBe(
      "chiaro",
    )
    // l'indice dice la scelta, non il modo vestito
    expect(document.body.textContent).not.toMatch(/modo chiaro/)
  })

  it("automatico senza la notte scritta rilegge ogni minuto, non una volta sola", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    try {
      window.history.pushState({}, "", "/impostazioni/generale")
      await app({}, { theme_mode: "automatico" })
      await screen.findByRole("radiogroup", { name: "Modo" })
      const letture = () => chiamate().filter((u) => u.endsWith("/api/v1/settings")).length
      const prima = letture()
      await vi.advanceTimersByTimeAsync(60_000)
      await waitFor(() => expect(letture()).toBe(prima + 1))
      // la rilettura riporta lo stesso: si rilegge ancora
      await vi.advanceTimersByTimeAsync(60_000)
      await waitFor(() => expect(letture()).toBe(prima + 2))
    } finally {
      vi.useRealTimers()
    }
  })

  it("automatico rilegge un secondo dopo il cambio annunciato, non prima, e riarma", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    try {
      vi.setSystemTime(new Date("2026-10-16T18:17:00+02:00"))
      window.history.pushState({}, "", "/impostazioni/generale")
      const ora = { mode: "chiaro", until: "2026-10-16T18:27:00+02:00" }
      await app({}, { theme_mode: "automatico" }, { theme_now: ora })
      await screen.findByRole("radiogroup", { name: "Modo" })
      const letture = () => chiamate().filter((u) => u.endsWith("/api/v1/settings")).length
      const prima = letture()
      await vi.advanceTimersByTimeAsync(600_200)
      expect(letture()).toBe(prima)
      await vi.advanceTimersByTimeAsync(1_000)
      await waitFor(() => expect(letture()).toBe(prima + 1))
      // la rilettura riporta lo stesso cambio, gia' passato: si rilegge un secondo dopo
      await vi.advanceTimersByTimeAsync(1_100)
      await waitFor(() => expect(letture()).toBe(prima + 2))
    } finally {
      vi.useRealTimers()
    }
  })

  it("automatico senza sito di casa, o un modo fisso, non rilegge", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    try {
      for (const [valori, resto] of [
        [{ theme_mode: "automatico" }, { theme_site: null }],
        [
          { theme_mode: "scuro" },
          { theme_now: { mode: "chiaro", until: new Date().toISOString() } },
        ],
      ] as const) {
        pulisci()
        window.history.pushState({}, "", "/impostazioni/generale")
        await app({}, valori, resto)
        await screen.findByRole("radiogroup", { name: "Modo" })
        const letture = () => chiamate().filter((u) => u.endsWith("/api/v1/settings")).length
        const prima = letture()
        await vi.advanceTimersByTimeAsync(120_000)
        expect(letture()).toBe(prima)
      }
    } finally {
      vi.useRealTimers()
    }
  })

  it("chiusa l'app, l'attesa del tema si spegne", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    try {
      window.history.pushState({}, "", "/impostazioni/generale")
      await app({}, { theme_mode: "automatico" })
      await screen.findByRole("radiogroup", { name: "Modo" })
      const letture = () => chiamate().filter((u) => u.endsWith("/api/v1/settings")).length
      const prima = letture()
      cleanup()
      await vi.advanceTimersByTimeAsync(120_000)
      expect(letture()).toBe(prima)
    } finally {
      vi.useRealTimers()
    }
  })

  it("una rilettura che dice un altro cambio non riarma il vecchio", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true })
    try {
      window.history.pushState({}, "", "/impostazioni/generale")
      await app({}, { theme_mode: "automatico" })
      await screen.findByRole("radiogroup", { name: "Modo" })
      const letture = () => chiamate().filter((u) => u.endsWith("/api/v1/settings")).length
      const prima = letture()
      const poi = new Date(Date.now() + 3_600_000).toISOString()
      const corpo = {
        ...BASE,
        theme_now: { mode: "chiaro", until: poi },
        values: { ...BASE.values, theme_mode: "automatico" },
      }
      rispondi({ ...STANOTTE, ...SPINA, "/api/v1/settings": { stato: 200, corpo } })
      await vi.advanceTimersByTimeAsync(60_000)
      await waitFor(() => expect(letture()).toBe(prima + 1))
      // il cambio nuovo e' fra un'ora: nessuna rilettura al minuto
      await vi.advanceTimersByTimeAsync(180_000)
      expect(letture()).toBe(prima + 1)
    } finally {
      vi.useRealTimers()
    }
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
    expect(visti).toEqual(["517373ea", "fc6d2a74"])
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
