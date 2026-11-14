// @vitest-environment jsdom
/**
 * Impostazioni, la sezione *Luna*: le due soglie delle notti buone per la banda larga che il
 * calendario della Luna segna. Valori di fabbrica 25% e 4 ore (Marco, 15/10/2026); si salvano
 * lasciando il campo, e un numero fuori misura non parte.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, SPINA, STANOTTE, apriImpostazioni, disegna, impostazioni, pulisci, rispondi, scritture } from "./banco"

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
  await apriImpostazioni()
  fireEvent.click(await screen.findByRole("link", { name: "Luna" }))
  return screen.findByRole("region", { name: "Luna" })
}

describe("Impostazioni, la Luna", () => {
  it("le due soglie coi valori di fabbrica, e da dove vengono", async () => {
    const sezione = await vaiAllaLuna()

    expect((within(sezione).getByLabelText("Banda larga buona fino a (%)") as HTMLInputElement).value).toBe("25")
    expect((within(sezione).getByLabelText("Banda larga al limite fino a (%)") as HTMLInputElement).value).toBe("65")
    expect(sezione.textContent).toContain("regola di ING")
  })

  it("una soglia cambiata si salva lasciando il campo", async () => {
    const sezione = await vaiAllaLuna()

    const pct = within(sezione).getByLabelText("Banda larga buona fino a (%)")
    fireEvent.change(pct, { target: { value: "20" } })
    fireEvent.blur(pct)
    await waitFor(() =>
      expect(scritture()).toContainEqual(
        expect.objectContaining({ metodo: "PATCH", corpo: { values: { moon_good_pct: 20 } } }),
      ),
    )
  })

  it("la misura di ogni soglia la manda il backend", async () => {
    const corpo = { ...impostazioni(true), ranges: { moon_good_pct: { min: 0, max: 100 }, moon_limit_pct: { min: 0, max: 80 } } }
    rispondi({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      ...SPINA,
    })
    await disegna()
    await apriImpostazioni()
    fireEvent.click(await screen.findByRole("link", { name: "Luna" }))
    const sezione = await screen.findByRole("region", { name: "Luna" })

    const ore = within(sezione).getByLabelText("Banda larga al limite fino a (%)")
    expect(ore.getAttribute("max")).toBe("80")
    fireEvent.change(ore, { target: { value: "90" } })
    fireEvent.blur(ore)
    expect(await within(sezione).findByText("Un numero da 0 a 80.")).toBeTruthy()
  })

  it("un numero fuori misura non parte e lo dice sotto il campo", async () => {
    const sezione = await vaiAllaLuna()

    const ore = within(sezione).getByLabelText("Banda larga al limite fino a (%)")
    fireEvent.change(ore, { target: { value: "130" } })
    fireEvent.blur(ore)
    expect(await within(sezione).findByText("Un numero da 0 a 100.")).toBeTruthy()
    expect(scritture().filter((s) => s.metodo === "PATCH")).toEqual([])
  })
})
