// @vitest-environment jsdom
/**
 * Impostazioni, la sezione *Luna*: le due soglie delle notti buone per la banda larga che il
 * calendario della Luna segna. Valori di fabbrica 25% e 4 ore (Marco, 15/10/2026); si salvano
 * lasciando il campo, e un numero fuori misura non parte.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, SPINA, STANOTTE, disegna, impostazioni, pulisci, rispondi, scritture } from "./banco"

afterEach(pulisci)

async function vaiAllaLuna() {
  rispondi({
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...SPINA,
  })
  await disegna()
  const barra = await screen.findByRole("navigation", { name: /pagine/i })
  fireEvent.click(within(barra).getByRole("link", { name: /impostazioni/i }))
  fireEvent.click(await screen.findByRole("link", { name: "Luna" }))
  return screen.findByRole("region", { name: "Notti buone per la banda larga" })
}

describe("Impostazioni, la Luna", () => {
  it("le due soglie coi valori di fabbrica, e da dove vengono", async () => {
    const sezione = await vaiAllaLuna()

    expect((within(sezione).getByLabelText("Luna sotto il (%)") as HTMLInputElement).value).toBe("25")
    expect((within(sezione).getByLabelText("oppure almeno (ore di buio senza Luna)") as HTMLInputElement).value).toBe("4")
    expect(sezione.textContent).toContain("non c'è una soglia pubblica condivisa")
  })

  it("una soglia cambiata si salva lasciando il campo", async () => {
    const sezione = await vaiAllaLuna()

    const pct = within(sezione).getByLabelText("Luna sotto il (%)")
    fireEvent.change(pct, { target: { value: "20" } })
    fireEvent.blur(pct)
    await waitFor(() =>
      expect(scritture()).toContainEqual(
        expect.objectContaining({ metodo: "PATCH", corpo: { values: { moon_broadband_max_pct: 20 } } }),
      ),
    )
  })

  it("un numero fuori misura non parte e lo dice sotto il campo", async () => {
    const sezione = await vaiAllaLuna()

    const ore = within(sezione).getByLabelText("oppure almeno (ore di buio senza Luna)")
    fireEvent.change(ore, { target: { value: "30" } })
    fireEvent.blur(ore)
    expect(await within(sezione).findByText("Un numero da 0 a 12.")).toBeTruthy()
    expect(scritture().filter((s) => s.metodo === "PATCH")).toEqual([])
  })
})
