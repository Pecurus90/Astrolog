// @vitest-environment jsdom
/**
 * Impostazioni, la sezione *Servizi* (tavola v82, `SezioneServizi`): la chiave Meteoblue e quella
 * del servizio del cielo, provate prima di salvarle e mostrate solo da come finiscono.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  SPINA,
  STANOTTE,
  type Voce,
  apriImpostazioni,
  cambia,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  scritture,
  violazioni,
} from "./banco"

afterEach(pulisci)

function conChiavi(meteoblue: string | null, cielo: string | null = null) {
  const base = impostazioni(true)
  return { ...base, values: { ...base.values, meteoblue_key: meteoblue, sky_service_key: cielo } }
}

function comune(meteoblue: string | null, cielo: string | null = null): Record<string, Voce> {
  return {
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: conChiavi(meteoblue, cielo) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...SPINA,
  }
}

function app(chiave: string | null, risposta: Voce, cielo: Voce = risposta) {
  rispondi({
    "PUT /api/v1/weather/meteoblue-key": risposta,
    "PUT /api/v1/services/sky-key": cielo,
    ...comune(chiave),
  })
  return disegna()
}

async function vaiAiServizi() {
  await apriImpostazioni()
  fireEvent.click(await screen.findByRole("tab", { name: /^servizi$/i }))
}

const carta = (nome: RegExp) => screen.findByRole("region", { name: nome })

describe("Impostazioni / Servizi", () => {
  it("una chiave che vale si manda al backend, e dopo si vede solo come finisce", async () => {
    await app(null, { stato: 200, corpo: { status: "ok", hint: "...1234" } })
    await vaiAiServizi()
    const meteoblue = await carta(/^meteoblue$/i)
    expect(within(meteoblue).getByText(/senza la chiave il meteo non mostra il seeing/i)).toBeDefined()

    fireEvent.change(within(meteoblue).getByLabelText("Chiave di Meteoblue"), {
      target: { value: "segretissima1234" },
    })
    cambia({
      "PUT /api/v1/weather/meteoblue-key": { stato: 200, corpo: { status: "ok", hint: "...1234" } },
      ...comune("...1234"),
    })
    fireEvent.click(within(meteoblue).getByRole("button", { name: /^verifica$/i }))

    expect(await within(meteoblue).findByText(/chiave valida, salvata/i)).toBeDefined()
    expect(await within(meteoblue).findByText("...1234")).toBeDefined()
    await waitFor(() =>
      expect(scritture()).toContainEqual({
        url: expect.stringContaining("/api/v1/weather/meteoblue-key"),
        metodo: "PUT",
        corpo: { key: "segretissima1234" },
      }),
    )
    // e il campo sparisce: la chiave intera non resta a schermo
    expect(within(meteoblue).queryByLabelText("Chiave di Meteoblue")).toBeNull()
  })

  it("una chiave che il servizio rifiuta non si salva, e lo dice", async () => {
    await app(null, { stato: 200, corpo: { status: "refused", hint: null } })
    await vaiAiServizi()
    const cielo = await carta(/servizio del cielo/i)
    fireEvent.change(within(cielo).getByLabelText(/^chiave di servizio del cielo/i), {
      target: { value: "sbagliata" },
    })
    fireEvent.click(within(cielo).getByRole("button", { name: /^verifica$/i }))

    expect(await within(cielo).findByText(/chiave rifiutata: controlla la chiave/i)).toBeDefined()
    await waitFor(() =>
      expect(scritture()).toContainEqual({
        url: expect.stringContaining("/api/v1/services/sky-key"),
        metodo: "PUT",
        corpo: { key: "sbagliata" },
      }),
    )
  })

  it("un servizio che non risponde lo dice col suo nome", async () => {
    await app(null, { stato: 200, corpo: { status: "unreachable", hint: null } })
    await vaiAiServizi()
    const meteoblue = await carta(/^meteoblue$/i)
    fireEvent.change(within(meteoblue).getByLabelText("Chiave di Meteoblue"), {
      target: { value: "k" },
    })
    fireEvent.click(within(meteoblue).getByRole("button", { name: /^verifica$/i }))
    expect(await within(meteoblue).findByText(/meteoblue non risponde/i)).toBeDefined()
  })

  it("una chiave salvata si toglie, e Cambia apre il campo", async () => {
    await app("...1234", { stato: 200, corpo: { status: "removed", hint: null } })
    await vaiAiServizi()
    const meteoblue = await carta(/^meteoblue$/i)
    fireEvent.click(within(meteoblue).getByRole("button", { name: /^cambia$/i }))
    expect(within(meteoblue).getByLabelText("Chiave di Meteoblue")).toBeDefined()
    fireEvent.click(within(meteoblue).getByRole("button", { name: /^annulla$/i }))

    fireEvent.click(within(meteoblue).getByRole("button", { name: /^togli$/i }))
    expect(await within(meteoblue).findByText(/chiave tolta/i)).toBeDefined()
    await waitFor(() =>
      expect(scritture()).toContainEqual({
        url: expect.stringContaining("/api/v1/weather/meteoblue-key"),
        metodo: "PUT",
        corpo: { key: "" },
      }),
    )
  })

  it("senza niente scritto non si prova niente", async () => {
    await app(null, { stato: 200, corpo: { status: "ok", hint: null } })
    await vaiAiServizi()
    const meteoblue = await carta(/^meteoblue$/i)
    const bottone = within(meteoblue).getByRole("button", { name: /^verifica$/i })
    expect(bottone.getAttribute("aria-disabled")).toBe("true")
    fireEvent.click(bottone)
    expect(scritture().filter((s) => s.metodo === "PUT")).toEqual([])
  })
})

describe("Impostazioni / Servizi, gli esiti uno per uno", () => {
  const nota = (dentro: HTMLElement) =>
    [...dentro.querySelectorAll("p.al-imp-nota[aria-live]")].map((p) => p.textContent)
  const campoDi = (dentro: HTMLElement) =>
    within(dentro).getByLabelText<HTMLInputElement>(/^chiave di /i)

  async function prova(risposta: Voce, quale: RegExp, chiave = "abc") {
    await app(null, risposta)
    await vaiAiServizi()
    const c = await carta(quale)
    fireEvent.change(campoDi(c), { target: { value: chiave } })
    fireEvent.click(within(c).getByRole("button", { name: /^verifica$/i }))
    return c
  }

  it.each([
    ["ok", "✓ Chiave valida, salvata."],
    ["refused", "✕ Chiave rifiutata: controlla la chiave sul sito del servizio e incollala di nuovo."],
    ["unreachable", "! Meteoblue non risponde: chiave non verificata e non salvata. Riprova più tardi."],
    ["bad_answer", "! Risposta non valida da Meteoblue: chiave non salvata."],
  ])("l'esito %s ha la sua frase col suo segno", async (esito, frase) => {
    const c = await prova({ stato: 200, corpo: { status: esito, hint: null } }, /^meteoblue$/i)
    await waitFor(() => expect(nota(c)).toEqual([frase]))
  })

  it("chiave valida: il campo si vuota; rifiutata: resta com'era scritta", async () => {
    const buona = await prova({ stato: 200, corpo: { status: "ok", hint: null } }, /^meteoblue$/i, "buona")
    await waitFor(() => expect(nota(buona)).toHaveLength(1))
    expect(campoDi(buona).value).toBe("")
    pulisci()
    const cattiva = await prova({ stato: 200, corpo: { status: "refused", hint: null } }, /^meteoblue$/i, "cattiva")
    await waitFor(() => expect(nota(cattiva)).toHaveLength(1))
    expect(campoDi(cattiva).value).toBe("cattiva")
  })

  it("tolta, la nota non ha segno davanti", async () => {
    await app("...1234", { stato: 200, corpo: { status: "removed", hint: null } })
    await vaiAiServizi()
    const c = await carta(/^meteoblue$/i)
    fireEvent.click(within(c).getByRole("button", { name: /^togli$/i }))
    await waitFor(() => expect(nota(c)).toEqual(["Chiave tolta."]))
  })

  it.each([
    [/^meteoblue$/i, "/api/v1/weather/meteoblue-key"],
    [/servizio del cielo/i, "/api/v1/services/sky-key"],
  ])("un invio che non arriva lo dice col segno del rifiuto (%s)", async (quale, rotta) => {
    const c = await prova({ stato: 500, corpo: {} }, quale)
    await waitFor(() => expect(nota(c)).toEqual(["✕ AstroLog non risponde: chiave non inviata. Riprova."]))
    expect(scritture().some((s) => s.url.includes(rotta))).toBe(true)
  })

  it("Invio nel campo verifica; vuoto o con un altro tasto, niente parte", async () => {
    await app(null, { stato: 200, corpo: { status: "ok", hint: null } })
    await vaiAiServizi()
    const c = await carta(/servizio del cielo/i)
    fireEvent.keyDown(campoDi(c), { key: "Enter" })
    fireEvent.change(campoDi(c), { target: { value: "  " } })
    fireEvent.keyDown(campoDi(c), { key: "Enter" })
    fireEvent.change(campoDi(c), { target: { value: "k9" } })
    fireEvent.keyDown(campoDi(c), { key: "a" })
    await new Promise((r) => setTimeout(r, 20))
    expect(scritture().filter((s) => s.metodo === "PUT")).toEqual([])
    fireEvent.keyDown(campoDi(c), { key: "Enter" })
    await waitFor(() =>
      expect(scritture().filter((s) => s.metodo === "PUT")).toEqual([
        { url: expect.stringContaining("/api/v1/services/sky-key"), metodo: "PUT", corpo: { key: "k9" } },
      ]),
    )
  })

  it("Annulla chiude il campo e butta cio' che c'era scritto", async () => {
    await app("...1234", { stato: 200, corpo: { status: "ok", hint: null } })
    await vaiAiServizi()
    const c = await carta(/^meteoblue$/i)
    fireEvent.click(within(c).getByRole("button", { name: /^cambia$/i }))
    fireEvent.change(campoDi(c), { target: { value: "mezza" } })
    fireEvent.click(within(c).getByRole("button", { name: /^annulla$/i }))
    expect(within(c).queryByLabelText(/^chiave di /i)).toBeNull()
    expect(within(c).getByText("...1234")).toBeDefined()
    fireEvent.click(within(c).getByRole("button", { name: /^cambia$/i }))
    expect(campoDi(c).value).toBe("")
  })

  it("ogni carta dice a cosa serve, dove si prende la chiave e cosa manca senza", async () => {
    await app(null, { stato: 200, corpo: { status: "ok", hint: null } })
    await vaiAiServizi()
    const meteo = await carta(/^meteoblue$/i)
    const cielo = await carta(/servizio del cielo/i)
    expect(within(meteo).getByRole("link", { name: /dove si prende/i }).getAttribute("href")).toBe(
      "https://www.meteoblue.com/it/weather-api",
    )
    expect(within(cielo).getByRole("link", { name: /dove si prende/i }).getAttribute("href")).toBe(
      "https://www.lightpollutionmap.info/",
    )
    expect(within(meteo).getByText("Il seeing della notte in secondi d'arco, nel Meteo.")).toBeDefined()
    expect(within(cielo).getByText(/^Il cielo di un sito dal World Atlas/)).toBeDefined()
    expect(within(cielo).getByText(/^Senza la chiave, in Siti la via/)).toBeDefined()
    expect(within(meteo).getByText("Chiave")).toBeDefined()
    expect(campoDi(meteo).getAttribute("placeholder")).toBe("Incolla la chiave")
    expect(campoDi(meteo).getAttribute("spellcheck")).toBe("false")
  })

  it("la chiave del cielo salvata si legge dalla sua voce, non da quella di Meteoblue", async () => {
    rispondi({ ...comune(null, "...cielo") })
    await disegna()
    await vaiAiServizi()
    const cielo = await carta(/servizio del cielo/i)
    expect(within(cielo).getByText("...cielo")).toBeDefined()
    const meteo = await carta(/^meteoblue$/i)
    expect(within(meteo).queryByText("...cielo")).toBeNull()
  })
})

describe("Impostazioni / Servizi, la veste e chi non vede", () => {
  it("la sezione passa dalla guardia di accessibilita', con una chiave salvata", async () => {
    const { container } = await app("...1234", { stato: 200, corpo: { status: "ok", hint: "...1234" } })
    await vaiAiServizi()
    await screen.findByRole("button", { name: /^togli$/i })

    expect(await violazioni(container)).toEqual([])
  })
})
