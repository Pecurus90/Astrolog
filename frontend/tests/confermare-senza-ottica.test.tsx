// @vitest-environment jsdom
/**
 * Da confermare, **quale ottica era**: le pose i cui file non nominano l'ottica (l'ASIAIR ci scrive
 * la montatura), una domanda per camera e focale.
 *
 * - **Si sceglie un'ottica che hai o se ne scrive il nome**, in un campo solo: il pezzo nuovo nasce
 *   dal nome nel backend.
 * - **Una domanda risposta resta in pagina con la sua risposta**, e ridare la stessa non manda
 *   niente: rimetterebbe in coda pose che non cambiano.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, STANOTTE, disegna, impostazioni, pulisci, riga, rispondi, scritture, vaiASezione } from "./banco"

afterEach(pulisci)

const PAGINA = {
  seen: { objects: 0 },
  to_confirm: 1,
  lookalikes: [],
  filters: [],
  filter_choices: [],
  rig_choices: [],
  objects: [],
  unfiltered: [],
  rigless: [],
  unnamed: [],
  unclear: [],
  typeless: [],
  mosaics: [],
  optics_choices: ["Askar 107PHQ", "Newton 200/800"],
  opticsless: [
    {
      key: "|ZWO ASI2600MC Pro|800.0",
      camera: "ZWO ASI2600MC Pro",
      focal_mm: 800,
      frames: 120,
      integration_s: 36000,
      untimed: 0,
      answer: null,
      subjects: { found: [{ name: "M 51", frames: 120 }], not_found: 0, not_yet: 0 },
    },
    {
      key: "|QHY268M|400.0",
      camera: "QHY268M",
      focal_mm: 400,
      frames: 12,
      integration_s: 3600,
      untimed: 2,
      answer: "Askar 107PHQ",
      subjects: { found: [], not_found: 12, not_yet: 0 },
    },
  ],
}

const RICEVUTA = { stato: 200, corpo: { changed: 1, confirmed: 0, requeued: 3, run_started: true } }

function aperta() {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review/apply": RICEVUTA,
    "/api/v1/review": { stato: 200, corpo: PAGINA },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
}

async function mandato() {
  fireEvent.click(screen.getByRole("button", { name: /applica/i }))
  let corpo: Record<string, unknown> | undefined
  await waitFor(() => {
    corpo = scritture().find((s) => s.url.includes("/api/v1/review/apply"))?.corpo as
      | Record<string, unknown>
      | undefined
    expect(corpo).toBeDefined()
  })
  return corpo as Record<string, unknown>
}

const applicaSpento = () =>
  expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", true)

describe("Da confermare -- quale ottica era", () => {
  it("la camera, la focale, le pose, le ore e cosa ci hai ripreso", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza ottica/i)
    const domanda = riga(sezione, "ZWO ASI2600MC Pro")
    expect(domanda.textContent).toMatch(/a 800 mm/)
    expect(domanda.textContent).toMatch(/120 frame/)
    expect(domanda.textContent).toMatch(/10 h/)
    expect(domanda.textContent).toMatch(/M 51/)
    // il campo non inventa una risposta: e' vuoto finche' non scrivi
    expect(within(domanda).getByRole("combobox")).toHaveProperty("value", "")
    applicaSpento()
  })

  it("si sceglie fra le tue ottiche, o si scrive un nome, e la risposta porta la chiave", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza ottica/i)
    const campo = within(riga(sezione, "ZWO ASI2600MC Pro")).getByRole("combobox")
    const suggerite = [...(campo as HTMLInputElement).list!.options].map((o) => o.value)
    expect(suggerite).toEqual(["Askar 107PHQ", "Newton 200/800"])

    fireEvent.change(campo, { target: { value: "  Newton 200/800 " } })
    expect((await mandato()).opticsless).toEqual([
      { key: "|ZWO ASI2600MC Pro|800.0", optics: "Newton 200/800" },
    ])
  })

  it("la risposta gia' data si legge, e ridarla uguale o svuotare il campo non manda niente", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza ottica/i)
    const domanda = riga(sezione, "QHY268M")
    const campo = within(domanda).getByRole("combobox")
    expect(campo).toHaveProperty("value", "Askar 107PHQ")
    expect(domanda.textContent).toMatch(/2 senza tempo/)

    fireEvent.change(campo, { target: { value: "Altro" } })
    fireEvent.change(campo, { target: { value: "Askar 107PHQ" } })
    applicaSpento()
    fireEvent.change(campo, { target: { value: "   " } })
    applicaSpento()
  })

  it("senza domande la sezione non c'e'", async () => {
    rispondi({
      ...STANOTTE,
      "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
      "/api/v1/review": { stato: 200, corpo: { ...PAGINA, opticsless: [], to_confirm: 0 } },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
    await screen.findByRole("heading", { name: /da confermare/i })
    expect(screen.queryByRole("region", { name: /frame senza ottica/i })).toBeNull()
  })
})
