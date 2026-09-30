// @vitest-environment jsdom
/**
 * Le pose **senza nome e senza cielo**: l'header non dice l'oggetto e il cielo non dice niente, e
 * si chiede **una volta per gruppo** -- notte, camera, telescopio, puntamento --, non per cartella.
 *
 * - **Si risponde scrivendo l'oggetto oppure "non e' un oggetto"**, mai tutti e due: qui non ci
 *   sono candidati da cliccare. Una sigla scritta (`M 81`) il backend la porta sulla voce del
 *   catalogo.
 * - **Niente e' preselezionato**, e un nome vuoto o di soli spazi non parte: l'Applica e' una
 *   transazione sola, e un rifiuto annullerebbe anche le risposte buone.
 * - **Un gruppo risposto resta in pagina** con la sua risposta, si cambia, e ridare la stessa
 *   risposta non manda niente.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { t } from "../src/i18n"
import { SALUTE, STANOTTE, impostazioni, pulisci, riga, rispondi, scritture, vaiASezione } from "./banco"

afterEach(pulisci)

// `t` passa dal vero: il conto delle sue chiamate dice quante righe si sono ridisegnate.
vi.mock("../src/i18n", async (vero) => {
  const modulo = await vero<typeof import("../src/i18n")>()
  return { ...modulo, t: vi.fn(modulo.t) }
})

// Le chiavi si rimandano e non si leggono: a schermo la riga si chiama con la notte e i valori.
const ROSETTA = '["2024-03-12", "canon eos 700d", null, 1, 2]'
const M81 = '["2024-04-01", "canon eos 700d", null, 7, 8]'
const PROVA = '[null, "canon eos 700d", null, null, null]'
const GRUPPO = { camera: "Canon EOS 700D", telescope: null }
const R_NOME = "notte del 12 mar 2024"
const M_NOME = "notte del 1 apr 2024"
const P_NOME = "senza data"

const PAGINA = {
  seen: { instruments: 0, rigs: 0, objects: 0 },
  to_confirm: 2,
  instruments: [],
  filters: [],
  rigs: [],
  objects: [],
  mosaics: [],
  unclear: [],
  unfiltered: [],
  filter_choices: [],
  rigless: [],
  unnamed: [
    {
      key: ROSETTA, night: "2024-03-12", ...GRUPPO, ra_deg: 98.03, dec_deg: 4.92, frames: 21, answer: null,
      // l'ora del posto, col suo scarto: la pagina la taglia e basta
      first_frame: "2024-03-12T21:10:00+01:00", last_frame: "2024-03-13T03:40:00+01:00",
    },
    {
      key: M81, night: "2024-04-01", ...GRUPPO, ra_deg: 148.9, dec_deg: 69.07, frames: 2,
      answer: { kind: "catalog", value: "m-81", name: "M 81" },
      first_frame: "2024-04-01T22:00:00+02:00", last_frame: "2024-04-01T22:00:00+02:00",
    },
    {
      key: PROVA, night: null, ...GRUPPO, ra_deg: null, dec_deg: null, frames: 4,
      answer: { kind: "none", value: null, name: null }, first_frame: null, last_frame: null,
    },
  ],
}

function aperta() {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review/apply": {
      stato: 200,
      corpo: { changed: 1, confirmed: 0, requeued: 0, run_started: false },
    },
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

describe("Da confermare -- le pose senza nome", () => {
  it("una domanda per gruppo, chiamato coi suoi valori, e niente e' preselezionato", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza nome/i)
    const rosetta = riga(sezione, R_NOME)
    expect(rosetta.textContent).toMatch(
      /^notte del 12 mar 2024 \u00b7 Canon EOS 700D \u00b7 verso RA 98 Dec 4,9/,
    )
    expect(riga(sezione, P_NOME).textContent).not.toMatch(/verso RA/)
    expect(rosetta.textContent).toMatch(/21 frame/)
    expect(within(rosetta).getByLabelText(/^oggetto$/i)).toHaveProperty("value", "")
    expect(within(rosetta).getByLabelText(/non e' un oggetto/i)).toHaveProperty("checked", false)
    applicaSpento()
  })

  it("la riga dice dalla prima all'ultima posa, nell'ora del posto", async () => {
    // due oggetti senza nome e senza puntamento nella stessa notte sono una domanda sola: le ore
    // dicono a chi risponde se e' una serie o due (Marco, 27/9/2026)
    aperta()
    const sezione = await vaiASezione(/frame senza nome/i)
    expect(riga(sezione, R_NOME).textContent).toMatch(/dalle 21:10 alle 03:40/)
    expect(riga(sezione, M_NOME).textContent).toMatch(/alle 22:00/)
    expect(riga(sezione, M_NOME).textContent).not.toMatch(/dalle/)
    expect(riga(sezione, P_NOME).textContent).not.toMatch(/alle \d/)
  })

  it("scrivere l'oggetto manda il gruppo e il nome, e svuotarlo lo toglie", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza nome/i)
    const campo = within(riga(sezione, R_NOME)).getByLabelText(/^oggetto$/i)
    fireEvent.change(campo, { target: { value: "   " } })
    applicaSpento() // un nome di soli spazi non e' una risposta
    fireEvent.change(campo, { target: { value: "M 42" } })
    fireEvent.change(campo, { target: { value: "" } })
    applicaSpento()
    fireEvent.change(campo, { target: { value: "Nebulosa Rosetta" } })
    expect((await mandato()).unnamed).toEqual([
      { key: ROSETTA, name: "Nebulosa Rosetta", not_an_object: false },
    ])
  })

  it("non e' un oggetto e' una risposta anche lei, e spegne il nome", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza nome/i)
    const rosetta = riga(sezione, R_NOME)
    fireEvent.change(within(rosetta).getByLabelText(/^oggetto$/i), { target: { value: "M 42" } })
    fireEvent.click(within(rosetta).getByLabelText(/non e' un oggetto/i))
    expect(within(rosetta).getByLabelText(/^oggetto$/i)).toHaveProperty("disabled", true)
    expect((await mandato()).unnamed).toEqual([{ key: ROSETTA, not_an_object: true }])
  })

  it("scrivere in un gruppo non ridisegna gli altri", async () => {
    // Ogni risposta riscrive l'accumulatore della pagina: con migliaia di gruppi, ridisegnarli
    // tutti a ogni tasto rende lenta la scrittura.
    aperta()
    const sezione = await vaiASezione(/frame senza nome/i)
    const righe = () =>
      vi.mocked(t).mock.calls.filter(([chiave]) => chiave === "review.unnamed.why").length
    const prima = righe()
    fireEvent.change(within(riga(sezione, R_NOME)).getByLabelText(/^oggetto$/i), {
      target: { value: "M 42" },
    })
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", false),
    )
    expect(righe() - prima).toBe(0) // la sezione non si ridisegna: solo la riga toccata
  })

  it("la risposta gia' data si legge, si cambia, e ridarla uguale non manda niente", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza nome/i)
    expect(riga(sezione, M_NOME).textContent).toMatch(/risposta: M 81/)
    expect(riga(sezione, P_NOME).textContent).toMatch(/risposta: non e' un oggetto/i)
    const m81 = riga(sezione, M_NOME)
    fireEvent.click(within(m81).getByRole("button", { name: /cambia/i }))
    // il campo parte con la risposta data: si va altrove e si torna, o React non vede il cambio
    fireEvent.change(within(m81).getByLabelText(/^oggetto$/i), { target: { value: "M 82" } })
    fireEvent.change(within(m81).getByLabelText(/^oggetto$/i), { target: { value: "M 81" } })
    applicaSpento()
    const prova = riga(sezione, P_NOME)
    fireEvent.click(within(prova).getByRole("button", { name: /cambia/i }))
    const nessuno = within(prova).getByLabelText(/non e' un oggetto/i)
    expect(nessuno).toHaveProperty("checked", true)
    fireEvent.click(nessuno) // tolta...
    fireEvent.click(nessuno) // ...e rimessa: e' la risposta gia' data
    applicaSpento()
    fireEvent.click(nessuno)
    fireEvent.change(within(prova).getByLabelText(/^oggetto$/i), { target: { value: "Luna" } })
    expect((await mandato()).unnamed).toEqual([{ key: PROVA, name: "Luna", not_an_object: false }])
  })
})
