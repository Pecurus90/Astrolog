// @vitest-environment jsdom
/**
 * Due domande sul **dove** delle pose: da quale luogo sono state riprese certe coordinate, e se
 * dei pannelli affiancati sono un mosaico.
 *
 * - **Si chiede per gruppo** (le coordinate, il mosaico), mai per posa.
 * - **Niente e' preselezionato**: il luogo piu' vicino sta in cima ma non e' scelto, e il mosaico
 *   si propone ma non si fonde.
 * - **Un gruppo risposto resta in pagina con la risposta**, e ridare la stessa non manda niente:
 *   rimetterebbe in coda pose che non cambiano.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, SENZA_SOGGETTI, STANOTTE, disegna, impostazioni, pulisci, riga, rispondi, scritture, vaiASezione } from "./banco"

afterEach(pulisci)

const CANDIDATI = [
  { id: 3, name: "Cima Ekar", distance_km: 0.4 },
  { id: 1, name: "Casa", distance_km: 16.2 },
]

const PAGINA = {
  seen: { instruments: 0, rigs: 0, objects: 0 },
  to_confirm: 5,
  instruments: [],
  filters: [],
  rigs: [],
  objects: [],
  gear: [],
  filter_choices: [],
  unnamed: [],
  unclear: [
    {
      key: "45.85,11.58",
      latitude: 45.85,
      longitude: 11.58,
      distance_km: 16.2,
      frames: 391,
      nights: ["2024-05-17", "2024-06-01"],
      site: null,
      candidates: CANDIDATI,
      subjects: SENZA_SOGGETTI,
    },
    {
      key: "34.00,-111.00",
      latitude: 34.0,
      longitude: -111.0,
      distance_km: 8000,
      frames: 1,
      // nessuna notte: del luogo non si riconosce un fuso, e l'app non
      // indovina in che notte cadano
      nights: [],
      site: null,
      candidates: CANDIDATI,
      subjects: SENZA_SOGGETTI,
    },
    {
      key: "46.10,12.00",
      latitude: 46.1,
      longitude: 12.0,
      distance_km: null,
      frames: 41,
      nights: ["2024-07-02"],
      site: "Casa",
      candidates: CANDIDATI,
      subjects: SENZA_SOGGETTI,
    },
  ],
  mosaics: [
    {
      key: "impronta-m42",
      ra_deg: 83.8,
      dec_deg: -5.4,
      object: "M 42, NGC 1977",
      panels: 3,
      frames: 90,
      integration_s: 10800,
      untimed: 2,
      answer: null,
      answer_name: null,
      names: ["M 42", "NGC 1977"],
      // la proposta NON e' il primo soggetto in ordine alfabetico: il campo deve portare lei
      proposed: "NGC 1977",
    },
    {
      key: "impronta-m31",
      ra_deg: 10.7,
      dec_deg: 41.3,
      object: "M 31",
      panels: 2,
      frames: 40,
      integration_s: 7200,
      untimed: 0,
      answer: "no",
      answer_name: null,
      names: ["M 31"],
      proposed: "M 31",
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

const scelte = (dove: HTMLElement) =>
  within(dove)
    .getAllByRole("radio")
    .map((r) => [r.closest("label")?.textContent, (r as HTMLInputElement).checked])

describe("Da confermare -- da quale luogo", () => {
  it("un posto con quante pose, le sue notti e i luoghi dal piu' vicino, senza sceglierne uno", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza sito/i)
    const posto = riga(sezione, "45.85,11.58")
    expect(posto.textContent).toMatch(/391 frame/)
    expect(posto.textContent).toMatch(/a 16,2 km da casa/)
    expect(posto.textContent).toMatch(/2024-05-17.*2024-06-01/)
    expect(scelte(posto)).toEqual([
      ["Cima Ekar, a 0,4 km", false],
      ["Casa, a 16,2 km", false],
    ])
    applicaSpento()
  })

  it("un posto di cui non si sa ancora la notte lo dice, invece di scrivere notti e basta", async () => {
    // L'app non indovina la notte di pose il cui istante non e' ancora certo: la lista esce
    // vuota, e senza una frase a schermo resterebbe **"notti:"** e poi il nulla. La frase nomina
    // la domanda di **questa** riga -- da dove osservavi -- perche' e' quella che l'utente ha
    // davanti.
    aperta()
    const sezione = await vaiASezione(/frame senza sito/i)

    const posto = riga(sezione, "34.00,-111.00")
    expect(posto.textContent).toMatch(/quando avrai detto da dove osservavi/i)
    expect(posto.textContent).not.toMatch(/notti:\s*$/)
  })

  it("la risposta porta le coordinate e il luogo scelto", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza sito/i)
    fireEvent.click(within(riga(sezione, "45.85,11.58")).getByLabelText(/cima ekar/i))
    expect((await mandato()).unclear).toEqual([{ key: "45.85,11.58", site_id: 3 }])
  })

  it("la risposta gia' data si legge, e ridarla uguale non manda niente", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza sito/i)
    const posto = riga(sezione, "46.10,12.00")
    // il gruppo di scelte nomina il posto: con due posti aperti le scelte sono uguali
    expect(within(sezione).getByRole("group", { name: /46\.10,12\.00/ })).toBeDefined()
    expect(within(posto).getByLabelText(/^casa/i)).toHaveProperty("checked", true)
    fireEvent.click(within(posto).getByLabelText(/cima ekar/i))
    fireEvent.click(within(posto).getByLabelText(/^casa/i))
    applicaSpento()
  })

  it("senza un luogo di casa non si dice una distanza da casa", async () => {
    // `distance_km` nullo e' "non c'e' una casa", non "sei a casa": uno zero sarebbe falso.
    aperta()
    const sezione = await vaiASezione(/frame senza sito/i)
    expect(riga(sezione, "46.10,12.00").textContent).not.toMatch(/da casa/)
  })
})

describe("Da confermare -- i mosaici proposti", () => {
  it("i soggetti, i pannelli, le pose e le ore, e il si' e il no senza sceglierne uno", async () => {
    aperta()
    const sezione = await vaiASezione(/mosaici/i)
    const mosaico = riga(sezione, "M 42, NGC 1977")
    expect(mosaico.textContent).toMatch(/3 pannelli/)
    expect(mosaico.textContent).toMatch(/90 frame/)
    expect(mosaico.textContent).toMatch(/3 h/)
    expect(mosaico.textContent).toMatch(/2 senza tempo/)
    expect(scelte(mosaico).map(([, spuntata]) => spuntata)).toEqual([false, false])
  })

  it("il si' porta la chiave del mosaico e di cosa e', gia' proposto", async () => {
    aperta()
    const sezione = await vaiASezione(/mosaici/i)
    const mosaico = riga(sezione, "M 42, NGC 1977")
    expect(within(mosaico).queryByLabelText(/di cosa/i)).toBeNull()
    fireEvent.click(within(mosaico).getByLabelText(/^e' un mosaico/i))
    const campo = within(mosaico).getByLabelText(/di cosa/i) as HTMLInputElement
    expect(campo.value).toBe("NGC 1977")
    expect([...(campo.list?.options ?? [])].map((o) => o.value)).toEqual(["M 42", "NGC 1977"])
    expect((await mandato()).mosaics).toEqual([
      { key: "impronta-m42", answer: "yes", name: "NGC 1977" },
    ])
  })

  it("il nome si cambia, e un nome vuoto non parte", async () => {
    aperta()
    const sezione = await vaiASezione(/mosaici/i)
    const mosaico = riga(sezione, "M 42, NGC 1977")
    fireEvent.click(within(mosaico).getByLabelText(/^e' un mosaico/i))
    const campo = within(mosaico).getByLabelText(/di cosa/i)
    fireEvent.change(campo, { target: { value: "   " } })
    applicaSpento()
    fireEvent.change(campo, { target: { value: "M 42" } })
    expect((await mandato()).mosaics).toEqual([expect.objectContaining({ name: "M 42" })])
  })

  it("un mosaico gia' confermato mostra il nome detto, e ridarlo uguale non manda niente", async () => {
    const detto = { ...PAGINA.mosaics[0], answer: "yes", answer_name: "M 42" }
    aperta({ ...PAGINA, mosaics: [detto] })
    const sezione = await vaiASezione(/mosaici/i)
    const campo = within(riga(sezione, "M 42, NGC 1977")).getByLabelText(/di cosa/i)
    expect(campo).toHaveProperty("value", "M 42")
    fireEvent.change(campo, { target: { value: "M 43" } })
    fireEvent.change(campo, { target: { value: "M 42" } })
    applicaSpento()
  })

  it("due mosaici degli stessi soggetti si distinguono, e ognuno nomina il suo gruppo di scelte", async () => {
    // Lo stesso soggetto ripreso in due regioni lontane da due parti: senza la regione le due righe
    // -- e i loro due gruppi di scelte -- avrebbero lo stesso nome, per chi guarda e per chi ascolta.
    const gemello = { ...PAGINA.mosaics[0], key: "impronta-gemello", ra_deg: 84.9, dec_deg: -1.2 }
    aperta({ ...PAGINA, mosaics: [PAGINA.mosaics[0], gemello] })
    const sezione = await vaiASezione(/mosaici/i)
    const nomi = within(sezione)
      .getAllByRole("group")
      .map((g) => g.querySelector("legend")?.textContent)
    expect(nomi).toHaveLength(2)
    expect(new Set(nomi).size).toBe(2)
    expect(within(sezione).getByRole("group", { name: /M 42.*83,8/ })).toBeDefined()
  })

  it("un mosaico senza tempo non scrive zero ore", async () => {
    aperta({ ...PAGINA, mosaics: [{ ...PAGINA.mosaics[0], integration_s: 0, untimed: 90 }] })
    const sezione = await vaiASezione(/mosaici/i)
    const mosaico = riga(sezione, "M 42, NGC 1977")
    expect(mosaico.textContent).not.toMatch(/\b0 h/)
    expect(mosaico.textContent).toMatch(/90 senza tempo/)
  })

  it("un no e' una risposta, resta, e ridarlo uguale non manda niente", async () => {
    aperta()
    const sezione = await vaiASezione(/mosaici/i)
    const mosaico = riga(sezione, "M 31")
    expect(within(mosaico).getByLabelText(/non e' un mosaico/i)).toHaveProperty("checked", true)
    fireEvent.click(within(mosaico).getByLabelText(/^e' un mosaico/i))
    fireEvent.click(within(mosaico).getByLabelText(/non e' un mosaico/i))
    applicaSpento()
  })
})

it("le sezioni senza domande non si vedono", async () => {
  aperta({ ...PAGINA, unclear: [], mosaics: [] })
  await disegna()
  fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
  await screen.findByRole("heading", { name: /da confermare/i })
  for (const nome of [/frame senza sito/i, /mosaici/i]) {
    expect(screen.queryByRole("region", { name: nome })).toBeNull()
  }
})
