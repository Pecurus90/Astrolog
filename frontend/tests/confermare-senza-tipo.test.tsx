// @vitest-environment jsdom
/**
 * La domanda **che file sono**: una per cartella, due risposte -- Light o Calibrazione.
 *
 * - **Niente e' preselezionato**: finche' l'utente non sceglie, l'app non decide per lui.
 * - **Una cartella risposta resta in pagina** con la sua risposta, e si cambia scegliendo l'altra.
 * - **Ridare la risposta gia' data non manda niente**: rimetterebbe in coda quei frame per non
 *   cambiare nulla.
 * - **Cio' che il cielo ha trovato non si mostra**: su quei frame il cielo non ha saputo dire.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, STANOTTE, disegna, impostazioni, pulisci, riga, rispondi, scritture, vaiASezione } from "./banco"

afterEach(pulisci)

const PAGINA = {
  to_confirm: 1,
  instruments: [],
  filters: [],
  objects: [],
  mosaics: [],
  unclear: [],
  gear: [],
  filter_choices: [],
  rigs: [],
  typeless: [
    { key: "D:/Astro/2024-05-17/dark", frames: 120, answer: null },
    { key: "D:/Astro/2024-06-01/M51", frames: 30, answer: "light" },
  ],
}

const RICEVUTA = { stato: 200, corpo: { changed: 1, requeued: 0, run_started: false } }

function aperta(pagina: unknown = PAGINA) {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review/apply": RICEVUTA,
    "/api/v1/review": { stato: 200, corpo: pagina },
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

describe("Da confermare -- i file che non dicono che file sono", () => {
  it("una domanda per cartella, e niente e' gia' scelto", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const cartella = riga(sezione, "D:/Astro/2024-05-17/dark")
    expect(cartella.textContent).toMatch(/120 frame/)
    for (const scelta of within(cartella).getAllByRole("radio")) {
      expect(scelta).toHaveProperty("checked", false)
    }
    applicaSpento()
  })

  it("la risposta porta la cartella e che file sono", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const cartella = riga(sezione, "D:/Astro/2024-05-17/dark")
    fireEvent.click(within(cartella).getByLabelText("Calibrazione"))
    expect((await mandato()).typeless).toEqual([
      { key: "D:/Astro/2024-05-17/dark", kind: "calibration" },
    ])
  })

  it("la risposta gia' data si legge, e tornarci sopra non manda niente", async () => {
    // Il giro e' quello vero: la riga porta gia' "Light", si sceglie l'altra (l'Applica
    // si accende) e poi si torna sulla prima -- li' la risposta esce dall'accumulatore e l'Applica
    // torna spento. Cliccare due volte la stessa scelta non proverebbe niente: sulla radio gia'
    // spuntata il browser non manda nessun evento, e il test resterebbe verde anche senza la
    // regola.
    aperta()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const risposta = riga(sezione, "D:/Astro/2024-06-01/M51")
    // la risposta salvata sta in testa alla riga, accanto ai frame: la scelta ha lo stesso nome
    expect(risposta.querySelector(".as-riga__testa")?.textContent).toMatch(/30 frame\s+Light$/)
    expect(within(risposta).getByLabelText("Light")).toHaveProperty("checked", true)
    fireEvent.click(within(risposta).getByLabelText("Calibrazione"))
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", false)
    fireEvent.click(within(risposta).getByLabelText("Light"))
    applicaSpento()
  })

  it("la scelta si vede subito, prima di applicare", async () => {
    // Senza questo, il componente leggerebbe solo la risposta gia' salvata: chi sceglie non
    // vedrebbe succedere niente finche' non applica. Visto dal vivo nel browser, non nei test.
    aperta()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const cartella = riga(sezione, "D:/Astro/2024-05-17/dark")
    fireEvent.click(within(cartella).getByLabelText("Calibrazione"))
    expect(within(cartella).getByLabelText("Calibrazione")).toHaveProperty("checked", true)
    expect(within(cartella).getByLabelText("Light")).toHaveProperty("checked", false)
  })

  it("si cambia idea scegliendo l'altra", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const risposta = riga(sezione, "D:/Astro/2024-06-01/M51")
    fireEvent.click(within(risposta).getByLabelText("Calibrazione"))
    expect((await mandato()).typeless).toEqual([
      { key: "D:/Astro/2024-06-01/M51", kind: "calibration" },
    ])
  })

  it("la sezione non c'e' quando non ci sono cartelle da chiedere", async () => {
    aperta({ ...PAGINA, typeless: [], to_confirm: 0 })
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
    await waitFor(() => expect(screen.getByRole("button", { name: /applica/i })).toBeDefined())
    expect(screen.queryByRole("heading", { name: /frame senza tipo/i })).toBeNull()
  })
})
