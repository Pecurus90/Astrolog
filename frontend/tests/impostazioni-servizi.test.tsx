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

describe("Impostazioni / Servizi, la veste e chi non vede", () => {
  it("la sezione passa dalla guardia di accessibilita', con una chiave salvata", async () => {
    const { container } = await app("...1234", { stato: 200, corpo: { status: "ok", hint: "...1234" } })
    await vaiAiServizi()
    await screen.findByRole("button", { name: /^togli$/i })

    expect(await violazioni(container)).toEqual([])
  })
})
