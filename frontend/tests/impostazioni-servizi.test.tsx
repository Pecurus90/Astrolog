// @vitest-environment jsdom
/**
 * Impostazioni, la sezione *Servizi*: la chiave Meteoblue, provata sul conto prima di salvarla, e
 * mostrata solo dalle sue ultime cifre. La stessa parte sta nel primo avvio, come passo facoltativo.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  SPINA,
  STANOTTE,
  type Voce,
  cambia,
  disegna,
  fuoriDaiMattoni,
  impostazioni,
  pulisci,
  rispondi,
  scritture,
  violazioni,
} from "./banco"

afterEach(pulisci)

function conChiave(fine: string | null) {
  const base = impostazioni(true)
  return { ...base, values: { ...base.values, meteoblue_key: fine } }
}

function comune(chiave: string | null): Record<string, Voce> {
  return {
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: conChiave(chiave) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...SPINA,
  }
}

function app(chiave: string | null, risposta: Voce) {
  rispondi({ "PUT /api/v1/weather/meteoblue-key": risposta, ...comune(chiave) })
  return disegna()
}

async function vaiAiServizi() {
  const barra = await screen.findByRole("navigation", { name: /pagine/i })
  fireEvent.click(within(barra).getByRole("link", { name: /impostazioni/i }))
  fireEvent.click(await screen.findByRole("link", { name: /servizi/i }))
}

describe("Impostazioni / Servizi", () => {
  it("una chiave che vale si manda al backend, e dopo si vede solo come finisce", async () => {
    await app(null, { stato: 200, corpo: { status: "ok", hint: "...1234" } })
    await vaiAiServizi()
    expect(await screen.findByText(/nessuna chiave/i)).toBeDefined()

    fireEvent.change(screen.getByLabelText(/chiave meteoblue/i), { target: { value: "segretissima1234" } })
    cambia({ "PUT /api/v1/weather/meteoblue-key": { stato: 200, corpo: { status: "ok", hint: "...1234" } }, ...comune("...1234") })
    fireEvent.click(screen.getByRole("button", { name: /^verifica e salva$/i }))

    expect(await screen.findByText(/chiave valida: seeing attivo/i)).toBeDefined()
    expect(await screen.findByText(/termina con \.\.\.1234/i)).toBeDefined()
    await waitFor(() =>
      expect(scritture()).toContainEqual({
        url: expect.stringContaining("/api/v1/weather/meteoblue-key"),
        metodo: "PUT",
        corpo: { key: "segretissima1234" },
      }),
    )
    // e il campo si svuota: la chiave intera non resta a schermo
    expect((screen.getByLabelText(/chiave meteoblue/i) as HTMLInputElement).value).toBe("")
  })

  it("una chiave che il conto rifiuta non si salva, e lo dice", async () => {
    await app(null, { stato: 200, corpo: { status: "refused", hint: null } })
    await vaiAiServizi()
    fireEvent.change(await screen.findByLabelText(/chiave meteoblue/i), { target: { value: "sbagliata" } })
    fireEvent.click(screen.getByRole("button", { name: /^verifica e salva$/i }))

    expect(await screen.findByText(/chiave non riconosciuta da meteoblue/i)).toBeDefined()
  })

  it("una chiave salvata si toglie", async () => {
    await app("...1234", { stato: 200, corpo: { status: "removed", hint: null } })
    await vaiAiServizi()
    fireEvent.click(await screen.findByRole("button", { name: /^rimuovi chiave$/i }))

    expect(await screen.findByText(/chiave rimossa/i)).toBeDefined()
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
    const bottone = await screen.findByRole("button", { name: /^verifica e salva$/i })
    expect((bottone as HTMLButtonElement).disabled).toBe(true)
  })
})

describe("Impostazioni / Servizi, la veste e chi non vede", () => {
  it("la sezione passa dai mattoni e dalla guardia di accessibilita', con la chiave salvata", async () => {
    const { container } = await app("...1234", { stato: 200, corpo: { status: "ok", hint: "...1234" } })
    await vaiAiServizi()
    await screen.findByRole("button", { name: /^rimuovi chiave$/i })

    expect(fuoriDaiMattoni()).toEqual([])
    expect(await violazioni(container)).toEqual([])
  })
})
