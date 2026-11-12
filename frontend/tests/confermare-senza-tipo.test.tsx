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

import {
  SALUTE,
  STANOTTE,
  cartellaSenzaTipo,
  daConfermare,
  disegna,
  impostazioni,
  prove,
  pulisci,
  riga,
  rispondi,
  scelta,
  scelto,
  scritture,
  statoDellaDomanda,
  vai,
  vaiASezione,
} from "./banco"

afterEach(pulisci)

const PAGINA = daConfermare({
  to_confirm: 1,
  typeless: [
    cartellaSenzaTipo({ key: "D:/Astro/2024-05-17/dark", frames: 120, nights: ["2024-05-17"], integration_s: 7200, untimed: 3 }),
    cartellaSenzaTipo({ key: "D:/Astro/2024-06-01/M51", frames: 30, answer: "light" }),
  ],
})

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
  expect(screen.getByRole("button", { name: /applica/i }).getAttribute("aria-disabled")).toBe("true")

describe("Da confermare -- i file che non dicono che file sono", () => {
  it("una domanda per cartella, e niente e' gia' scelto", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const cartella = riga(sezione, "D:/Astro/2024-05-17/dark")
    expect(cartella.textContent).toMatch(/120 frame/)
    for (const voce of within(cartella).getAllByRole("radio")) {
      expect(scelto(voce)).toBe(false)
    }
    applicaSpento()
  })

  it("le prove dicono la notte e la durata, coi frame senza durata", async () => {
    aperta()
    const cartella = riga(await vaiASezione(/frame senza tipo/i), "D:/Astro/2024-05-17/dark")
    expect(prove(cartella)).toEqual(["Notte=17 mag 2024", "Durata=2 h · 3 senza durata"])
  })

  it("la risposta porta la cartella e che file sono", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const cartella = riga(sezione, "D:/Astro/2024-05-17/dark")
    fireEvent.click(scelta(cartella, "Calibrazione"))
    expect((await mandato()).typeless).toEqual([
      { key: "D:/Astro/2024-05-17/dark", kind: "calibration" },
    ])
  })

  it("la risposta gia' data si legge, e tornarci sopra non manda niente", async () => {
    // Il giro e' quello vero: la riga porta gia' "Light", si sceglie l'altra (l'Applica
    // si accende) e poi si torna sulla prima -- li' la risposta esce dall'accumulatore e l'Applica
    // torna spento.
    aperta()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const risposta = riga(sezione, "D:/Astro/2024-06-01/M51")
    // la risposta salvata e' la scelta stessa, e lo stato lo dice: non una parola accanto
    expect(statoDellaDomanda(risposta)).toBe("salvata")
    expect(scelto(scelta(risposta, "Light"))).toBe(true)
    fireEvent.click(scelta(risposta, "Calibrazione"))
    expect(screen.getByRole("button", { name: /applica/i }).getAttribute("aria-disabled")).toBeNull()
    fireEvent.click(scelta(risposta, "Light"))
    applicaSpento()
  })

  it("la scelta si vede subito, prima di applicare", async () => {
    // Senza questo, il componente leggerebbe solo la risposta gia' salvata: chi sceglie non
    // vedrebbe succedere niente finche' non applica. Visto dal vivo nel browser, non nei test.
    aperta()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const cartella = riga(sezione, "D:/Astro/2024-05-17/dark")
    fireEvent.click(scelta(cartella, "Calibrazione"))
    expect(scelto(scelta(cartella, "Calibrazione"))).toBe(true)
    expect(scelto(scelta(cartella, "Light"))).toBe(false)
  })

  it("si cambia idea scegliendo l'altra", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza tipo/i)
    const risposta = riga(sezione, "D:/Astro/2024-06-01/M51")
    fireEvent.click(scelta(risposta, "Calibrazione"))
    expect((await mandato()).typeless).toEqual([
      { key: "D:/Astro/2024-06-01/M51", kind: "calibration" },
    ])
  })

  it("la sezione non c'e' quando non ci sono cartelle da chiedere", async () => {
    aperta(daConfermare())
    await disegna()
    vai("/da-confermare")
    expect(await screen.findByText("Niente da confermare")).toBeDefined()
    expect(screen.queryByRole("heading", { name: /frame senza tipo/i })).toBeNull()
  })
})
