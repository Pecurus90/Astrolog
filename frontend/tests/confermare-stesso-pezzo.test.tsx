// @vitest-environment jsdom
/**
 * La sezione **Stesso pezzo?** di Da confermare: due grafie che hanno l'aria di essere la stessa
 * camera, e l'app chiede (Marco, 25/9/2026: non puo' saperlo da sola).
 *
 * - **Niente e' preselezionato**: un'unione non si disfa, e si sceglie cliccando.
 * - **Si' e no mandano la coppia** che l'API ha proposto: quale grafia resta non si sceglie qui.
 * - **L'attrezzatura non c'e' piu'**: schede e corredi stanno nell'Attrezzatura.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, STANOTTE, disegna, impostazioni, pulisci, riga, rispondi, scritture, vaiASezione } from "./banco"

afterEach(pulisci)

const PAGINA = {
  seen: { objects: 0 },
  to_confirm: 1,
  lookalikes: [
    {
      id: 7,
      name: "ATR 2600M",
      frames: 432,
      into_id: 4,
      into_name: "ATR2600M(USB2.0)",
      into_frames: 6558,
    },
  ],
  rig_choices: [],
  filters: [],
  objects: [],
  mosaics: [],
  unclear: [],
  gear: [],
  filter_choices: [],
  typeless: [],
  unnamed: [],
}

const RICEVUTA = { stato: 200, corpo: { changed: 1, confirmed: 0, requeued: 1, run_started: false } }

function aperta(pagina: unknown = PAGINA, apply: { stato: number; corpo: unknown } = RICEVUTA) {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review/apply": apply,
    "/api/v1/review": { stato: 200, corpo: pagina },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
}

/** Il corpo dell'Applica, quando e' partito. */
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

describe("Da confermare -- stesso pezzo?", () => {
  it("la riga dice a chi somiglia, e con quante pose", async () => {
    aperta()
    const sezione = await vaiASezione(/stesso pezzo/i)
    expect(riga(sezione, "ATR 2600M").textContent).toMatch(/somiglia a ATR2600M\(USB2\.0\) \(6.?558 frame\)/)
  })

  it("una grafia che somiglia a un altra propone l unione, senza sceglierla", async () => {
    // Marco, 15/9/2026: due grafie della stessa camera si consigliano di unire. Ma un'unione non
    // si disfa, quindi **niente e' preselezionato**: la domanda si legge, e si sceglie cliccando.
    aperta()
    const sezione = await vaiASezione(/stesso pezzo/i)
    const atr = riga(sezione, "ATR 2600M")
    expect(within(atr).getAllByRole("radio").some((r) => (r as HTMLInputElement).checked)).toBe(false)
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", true)
    fireEvent.click(within(atr).getByRole("radio", { name: /uniscila a ATR2600M\(USB2\.0\)/i }))
    expect((await mandato()).lookalikes).toEqual([{ id: 7, into_id: 4, same: true }])
  })

  it("il no manda la stessa coppia, e dice che sono due", async () => {
    aperta()
    const sezione = await vaiASezione(/stesso pezzo/i)
    fireEvent.click(within(riga(sezione, "ATR 2600M")).getByRole("radio", { name: /due pezzi/i }))
    expect((await mandato()).lookalikes).toEqual([{ id: 7, into_id: 4, same: false }])
  })

  it("le scelte dicono di quale coppia sono", async () => {
    aperta()
    const sezione = await vaiASezione(/stesso pezzo/i)
    expect(
      within(sezione).getByRole("group", { name: /ATR 2600M e ATR2600M\(USB2\.0\) sono lo stesso pezzo/ }),
    ).toBeDefined()
  })

  it("e se il backend rifiuta la risposta lo si dice per nome", async () => {
    aperta(PAGINA, { stato: 404, corpo: { detail: { code: "not_found" } } })
    const sezione = await vaiASezione(/stesso pezzo/i)
    fireEvent.click(within(riga(sezione, "ATR 2600M")).getByRole("radio", { name: /uniscila/i }))
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    expect((await screen.findByRole("alert")).textContent).toMatch(/pagina e' vecchia/i)
  })

  it("una sezione senza pezzi non si vede, e nemmeno strumenti e corredi", async () => {
    aperta({ ...PAGINA, lookalikes: [] })
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
    await screen.findByRole("heading", { name: /da confermare/i })
    expect(screen.queryByRole("region", { name: /stesso pezzo/i })).toBeNull()
    expect(screen.queryByRole("region", { name: /strumenti/i })).toBeNull()
    expect(screen.queryByRole("region", { name: /corredi/i })).toBeNull()
  })
})
