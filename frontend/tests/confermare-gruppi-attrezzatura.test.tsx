// @vitest-environment jsdom
/**
 * Le due domande sui **gruppi di pose** dell'attrezzatura: le pose che non dicono il filtro, una
 * domanda per camera; e quelle che non dicono la camera, una domanda per notte e valori dell'header.
 *
 * - **Si chiede per gruppo, mai per posa**, e la risposta vale anche per le pose che verranno.
 * - **Niente e' preselezionato**: il colore che i file suggeriscono e la focale nativa dell'ottica
 *   sono proposte scritte a schermo, e la risposta parte solo quando l'utente la da'.
 * - **Un gruppo risposto resta in pagina** con la sua risposta, perche' si deve poter cambiare idea.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, SENZA_SOGGETTI, STANOTTE, disegna, impostazioni, pulisci, riga, rispondi, scritture, vaiASezione } from "./banco"

afterEach(pulisci)

// La chiave del gruppo e' un nome da rimandare, non da leggere: a schermo la riga dice la notte.
const K1 = '["2024-05-17", "askar 103apo", 6248, 4176, 3.76]'
const K2 = '["2024-06-01", null, null, null, null]'
const PRIMA = "notte del 17 mag 2024"
const SECONDA = "notte del 1 giu 2024"

const PAGINA = {
  seen: { objects: 0 },
  to_confirm: 3,
  lookalikes: [],
  filters: [],
  objects: [],
  mosaics: [],
  unclear: [],
  filter_choices: [{ id: 3, name: "Lum", passband: "L" }, { id: 4, name: "Ha", passband: "HA" }],
  unnamed: [],
  unfiltered: [
    { key: "Poseidon-C PRO", frames: 3388, answer: null, filter_id: null, subjects: SENZA_SOGGETTI },
    { key: "ZWO ASI6200MM", frames: 40, answer: "filter", filter_id: 3, subjects: SENZA_SOGGETTI },
  ],
  rig_choices: [{ id: 2, name: "Principale", optics: "Askar 103Apo", camera: "ATR2600M", focal_mm: 560 }],
  rigless: [
    { key: K1, night: "2024-05-17", telescope: "Askar 103Apo", width_px: 6248, height_px: 4176, pixel_um: 3.76, frames: 120, optics: "Askar 103Apo", focal_mm: null, focal_suggested: 560, answer: null, subjects: SENZA_SOGGETTI },
    {
      key: K2,
      night: "2024-06-01",
      telescope: null,
      width_px: null,
      height_px: null,
      pixel_um: null,
      frames: 30,
      optics: null,
      focal_mm: null,
      focal_suggested: null,
      answer: { optics: null, camera: "Canon EOS 700D", focal_mm: 300 },
      subjects: SENZA_SOGGETTI,
    },
  ],
}

const RICEVUTA = { stato: 200, corpo: { changed: 1, confirmed: 0, requeued: 0, run_started: false } }

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

describe("Da confermare -- le pose che non dicono il filtro", () => {
  it("una domanda per camera, e niente e' scelto prima dell'utente", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza filtro/i)
    const poseidon = riga(sezione, "Poseidon-C PRO")
    expect(poseidon.textContent).toMatch(/3388 frame/) // in italiano quattro cifre non hanno il punto
    for (const scelta of within(poseidon).getAllByRole("radio")) {
      expect(scelta).toHaveProperty("checked", false)
    }
    applicaSpento()
  })

  it("la risposta porta la camera e cosa c'era davanti", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza filtro/i)
    fireEvent.click(within(riga(sezione, "Poseidon-C PRO")).getByLabelText(/nessun filtro/i))
    expect((await mandato()).unfiltered).toEqual([{ key: "Poseidon-C PRO", answer: "no_filter" }])
  })

  it("uno dei miei filtri si sceglie dalla tendina, e senza filtro non manda niente", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza filtro/i)
    const poseidon = riga(sezione, "Poseidon-C PRO")
    fireEvent.click(within(poseidon).getByLabelText(/uno dei miei filtri/i))
    applicaSpento()
    fireEvent.change(within(poseidon).getByLabelText(/quale filtro, su Poseidon-C PRO/i), {
      target: { value: "4" },
    })
    expect((await mandato()).unfiltered).toEqual([
      { key: "Poseidon-C PRO", answer: "filter", filter_id: 4 },
    ])
  })

  it("la risposta gia' data si legge, e ridarla uguale non manda niente", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza filtro/i)
    const mono = riga(sezione, "ZWO ASI6200MM")
    const data = within(mono).getByLabelText(/uno dei miei filtri/i)
    expect(data).toHaveProperty("checked", true)
    const tendina = within(mono).getByLabelText(/quale filtro, su ZWO ASI6200MM/i)
    expect(tendina).toHaveProperty("value", "3")
    fireEvent.click(within(mono).getByLabelText(/nessun filtro/i))
    fireEvent.click(data)
    fireEvent.change(within(mono).getByLabelText(/quale filtro/i), { target: { value: "3" } })
    applicaSpento()
    fireEvent.click(within(mono).getByLabelText(/nessun filtro/i))
    expect((await mandato()).unfiltered).toEqual([{ key: "ZWO ASI6200MM", answer: "no_filter" }])
  })
})

describe("Da confermare -- le pose che non dicono la camera", () => {
  it("si sceglie un corredo fra quelli che l API offre, col nome e i pezzi", async () => {
    // Quali corredi rispondono a "con che camera" lo dice l'API (`rig_choices`): qui non si filtra.
    aperta()
    const sezione = await vaiASezione(/frame senza camera/i)
    const cartella = riga(sezione, PRIMA)
    const elenco = within(cartella).getByLabelText(/corredo/i)
    expect(within(elenco).getAllByRole("option").map((o) => o.textContent)).toEqual([
      "--",
      "Principale (Askar 103Apo + ATR2600M, 560 mm)",
    ])
    fireEvent.change(elenco, { target: { value: "2" } })
    expect((await mandato()).rigless).toEqual([{ key: K1, rig_id: 2 }])
  })

  it("o si scrivono i pezzi, con l'ottica che le pose dicono e la focale nativa proposte", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza camera/i)
    const cartella = riga(sezione, PRIMA)
    fireEvent.click(within(cartella).getByRole("button", { name: /lo scrivo io/i }))
    expect(within(cartella).getByLabelText(/ottica/i)).toHaveProperty("value", "Askar 103Apo")
    expect(within(cartella).getByLabelText(/focale/i)).toHaveProperty("value", "560")
    // senza la camera non c'e' risposta: e' proprio cio' che la domanda chiede
    applicaSpento()
    fireEvent.change(within(cartella).getByLabelText(/camera/i), { target: { value: "ATR2600M" } })
    expect((await mandato()).rigless).toEqual([
      { key: K1, optics: "Askar 103Apo", camera: "ATR2600M", focal_mm: 560 },
    ])
  })

  it("la focale che le pose dicono vince su quella nativa dell'ottica", async () => {
    // Quella nativa e' una proposta per chi non ne ha una; se le pose la scrivono, e' quella.
    aperta({
      ...PAGINA,
      rigless: [{ ...PAGINA.rigless[0], focal_mm: 448, focal_suggested: 560 }],
    })
    const sezione = await vaiASezione(/frame senza camera/i)
    const cartella = riga(sezione, PRIMA)
    fireEvent.click(within(cartella).getByRole("button", { name: /lo scrivo io/i }))
    expect(within(cartella).getByLabelText(/focale/i)).toHaveProperty("value", "448")
  })

  it("passare ai pezzi scritti toglie il corredo scelto prima", async () => {
    // "Un corredo dall'elenco oppure i pezzi, mai tutti e due": col modulo vuoto a schermo
    // partirebbe il corredo di prima, che l'utente non vede piu'.
    aperta()
    const sezione = await vaiASezione(/frame senza camera/i)
    const cartella = riga(sezione, PRIMA)
    fireEvent.change(within(cartella).getByLabelText(/corredo/i), { target: { value: "2" } })
    fireEvent.click(within(cartella).getByRole("button", { name: /lo scrivo io/i }))
    applicaSpento()
  })

  it("una risposta con la focale ignota non scrive una focale finta", async () => {
    aperta({
      ...PAGINA,
      rigless: [
        { ...PAGINA.rigless[1], answer: { optics: "Askar 103Apo", camera: "ATR2600M", focal_mm: null } },
      ],
    })
    const sezione = await vaiASezione(/frame senza camera/i)
    const cartella = riga(sezione, SECONDA)
    expect(cartella.textContent).toMatch(/risposta: Askar 103Apo \+ ATR2600M/)
    expect(cartella.textContent).not.toMatch(/mm/)
  })

  it("ridare la stessa risposta a un gruppo non manda niente", async () => {
    // Misurato dall'auditor (15/9/2026): la stessa risposta rimetteva in coda tutte le pose della
    // cartella e non ne cambiava nessuna. Vale scegliendo lo stesso corredo e scrivendo gli stessi
    // pezzi, come per la risposta sul filtro.
    const risposta = { optics: "Askar 103Apo", camera: "ATR2600M", focal_mm: 560 }
    aperta({ ...PAGINA, rigless: [{ ...PAGINA.rigless[0], answer: risposta }] })
    const sezione = await vaiASezione(/frame senza camera/i)
    const cartella = riga(sezione, PRIMA)
    fireEvent.click(within(cartella).getByRole("button", { name: /cambia/i }))
    fireEvent.change(within(cartella).getByLabelText(/corredo/i), { target: { value: "2" } })
    applicaSpento()
    // e la tendina tiene la scelta: tornare a "--" direbbe che il clic non e' stato preso
    expect(within(cartella).getByLabelText(/corredo/i)).toHaveProperty("value", "2")
    fireEvent.click(within(cartella).getByRole("button", { name: /lo scrivo io/i }))
    fireEvent.change(within(cartella).getByLabelText(/camera/i), { target: { value: "ATR2600M" } })
    applicaSpento()
  })

  it("una chiave con spazi e virgolette non finisce negli id della pagina", async () => {
    // La chiave porta spazi e virgolette, e un `TELESCOP` puo' portare di tutto. Un id con dentro
    // uno spazio non e' un id valido, e l'etichetta resterebbe appesa al niente.
    const key = '["2024-05-17", "sky-watcher esprit 100 ed", 6248, 4176, 3.76]'
    aperta({ ...PAGINA, rigless: [{ ...PAGINA.rigless[0], key }] })
    const sezione = await vaiASezione(/frame senza camera/i)
    fireEvent.click(within(riga(sezione, PRIMA)).getByRole("button", { name: /lo scrivo io/i }))
    const ids = Array.from(sezione.querySelectorAll("[id]")).map((e) => e.id)
    expect(ids.length).toBeGreaterThan(0)
    expect(ids.filter((id) => /\s/.test(id))).toEqual([])
  })

  it("la riga si chiama con tutti i valori del gruppo, e senza data lo dice", async () => {
    // Il telescopio sta nella chiave: senza, due gruppi della stessa notte si chiamerebbero uguali.
    aperta({ ...PAGINA, rigless: [PAGINA.rigless[0], { ...PAGINA.rigless[1], night: null }] })
    const sezione = await vaiASezione(/frame senza camera/i)
    expect(riga(sezione, PRIMA).textContent).toMatch(
      /^notte del 17 mag 2024 \u00b7 Askar 103Apo \u00b7 sensore 6248 x 4176 \u00b7 pixel 3,76 um/,
    )
    expect(riga(sezione, "senza data").textContent).not.toMatch(/sensore|pixel/)
  })

  it("i bottoni dicono di quale gruppo sono", async () => {
    // Due gruppi aperti sono due "lo scrivo io": chi legge con uno schermo deve sapere di chi.
    aperta()
    const sezione = await vaiASezione(/frame senza camera/i)
    expect(
      within(sezione).getByRole("button", { name: /lo scrivo io.*17 mag 2024/i }),
    ).toBeDefined()
    expect(within(sezione).getByRole("button", { name: /cambia.*1 giu 2024/i })).toBeDefined()
  })

  it("senza una focale la risposta scritta non parte", async () => {
    // `RiglessGroupEdit` vuole la focale con la camera: un corredo a focale ignota resterebbe il
    // gemello di quello che i file diranno domani, con le ore spartite fra i due.
    aperta()
    const sezione = await vaiASezione(/frame senza camera/i)
    const cartella = riga(sezione, PRIMA)
    fireEvent.click(within(cartella).getByRole("button", { name: /lo scrivo io/i }))
    fireEvent.change(within(cartella).getByLabelText(/camera/i), { target: { value: "ATR2600M" } })
    fireEvent.change(within(cartella).getByLabelText(/focale/i), { target: { value: "" } })
    applicaSpento()
  })

  it("la risposta gia' data si legge, e si cambia", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza camera/i)
    const cartella = riga(sezione, SECONDA)
    expect(cartella.textContent).toMatch(/risposta: Canon EOS 700D, 300 mm/i)
    expect(within(cartella).queryByLabelText(/corredo/i)).toBeNull()
    fireEvent.click(within(cartella).getByRole("button", { name: /cambia/i }))
    expect(within(cartella).getByLabelText(/corredo/i)).toBeDefined()
  })
})

it("le sezioni senza domande non si vedono", async () => {
  aperta({ ...PAGINA, unfiltered: [], rigless: [] })
  await disegna()
  fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
  await screen.findByRole("heading", { name: /da confermare/i })
  expect(screen.queryByRole("region", { name: /frame senza filtro/i })).toBeNull()
  expect(screen.queryByRole("region", { name: /frame senza camera/i })).toBeNull()
})
