// @vitest-environment jsdom
/**
 * Impostazioni, la sezione *Luna* (tavola v82): la regola della banda larga a tre valori, letta da
 * tutta l'app (ADR 0034). Le percentuali si salvano lasciando il campo, la seconda non sta sotto
 * la prima, e le altezze sono quelle che manda il backend.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, SPINA, STANOTTE, apriImpostazioni, disegna, impostazioni, pulisci, rispondi, scritture } from "./banco"

afterEach(pulisci)

async function vaiAllaLuna(corpo: unknown = impostazioni(true)) {
  rispondi({
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo },
    "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...SPINA,
  })
  await disegna()
  await apriImpostazioni()
  fireEvent.click(await screen.findByRole("tab", { name: "Luna" }))
  return screen.findByRole("region", { name: "Luna" })
}

const BUONA = "Banda larga buona fino a, in percento"
const LIMITE = "Banda larga al limite fino a, in percento"
const patch = () => scritture().filter((s) => s.metodo === "PATCH")

describe("Impostazioni, la Luna", () => {
  it("i tre valori di adesso, ognuno con la sua fonte", async () => {
    const sezione = await vaiAllaLuna()

    expect((within(sezione).getByLabelText(BUONA) as HTMLInputElement).value).toBe("25")
    expect((within(sezione).getByLabelText(LIMITE) as HTMLInputElement).value).toBe("65")
    expect(sezione.textContent).toContain("regola di ING: buio sotto 0,25")
    const sopra = within(sezione).getByRole("radiogroup", { name: "La Luna conta sopra" })
    expect(within(sopra).getAllByRole("radio").map((r) => r.textContent)).toEqual(["−5°", "l'orizzonte", "5°", "10°"])
    expect(within(sopra).getByRole("radio", { name: "l'orizzonte" }).getAttribute("aria-checked")).toBe("true")
    expect(sezione.textContent).toContain("Ora: buona fino al 25%, al limite fino al 65%, conta sopra l'orizzonte.")
  })

  it("una percentuale cambiata si salva lasciando il campo", async () => {
    const sezione = await vaiAllaLuna()

    const pct = within(sezione).getByLabelText(BUONA)
    fireEvent.change(pct, { target: { value: "20" } })
    fireEvent.blur(pct)
    await waitFor(() =>
      expect(patch()).toContainEqual(
        expect.objectContaining({ corpo: { values: { moon_good_pct: 20, moon_limit_pct: 65 } } }),
      ),
    )
  })

  it("l altezza si sceglie con un tocco", async () => {
    const sezione = await vaiAllaLuna()

    fireEvent.click(within(sezione).getByRole("radio", { name: "−5°" }))
    await waitFor(() => expect(patch()).toContainEqual(expect.objectContaining({ corpo: { values: { moon_above_deg: -5 } } })))
  })

  it("al limite sotto buona non parte, e dice perche'", async () => {
    const sezione = await vaiAllaLuna()

    const limite = within(sezione).getByLabelText(LIMITE)
    fireEvent.change(limite, { target: { value: "20" } })
    fireEvent.blur(limite)
    expect(await within(sezione).findByText(/Deve essere almeno 25%\./)).toBeTruthy()
    expect(patch()).toEqual([])
  })

  it("la misura di ogni soglia la manda il backend", async () => {
    const corpo = { ...impostazioni(true), ranges: { moon_good_pct: { min: 0, max: 100 }, moon_limit_pct: { min: 0, max: 80 } } }
    const sezione = await vaiAllaLuna(corpo)

    const limite = within(sezione).getByLabelText(LIMITE)
    fireEvent.change(limite, { target: { value: "90" } })
    fireEvent.blur(limite)
    expect(await within(sezione).findByText(/Un numero da 0 a 80\./)).toBeTruthy()
    expect(patch()).toEqual([])
  })
})
