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

import {
  SALUTE,
  STANOTTE,
  daConfermare,
  disegna,
  domande,
  impostazioni,
  mosaicoProposto,
  postoIgnoto,
  prove,
  pulisci,
  riga,
  rispondi,
  scelta,
  scelto,
  scritture,
  vai,
  vaiASezione,
  voci,
} from "./banco"

afterEach(pulisci)

const CANDIDATI = [
  { id: 3, name: "Cima Ekar", distance_km: 0.4 },
  { id: 1, name: "Casa", distance_km: 16.2 },
]

const M42 = mosaicoProposto({
  key: "impronta-m42",
  ra_deg: 83.8,
  dec_deg: -5.4,
  object: "M 42, NGC 1977",
  panels: 3,
  frames: 90,
  integration_s: 10800,
  untimed: 2,
  nights: ["2024-01-10"],
  names: ["M 42", "NGC 1977"],
  // la proposta NON e' il primo soggetto in ordine alfabetico: il campo deve portare lei
  proposed: "NGC 1977",
})

const PAGINA = daConfermare({
  to_confirm: 5,
  unclear: [
    postoIgnoto({
      key: "45.85,11.58",
      latitude: 45.85,
      longitude: 11.58,
      distance_km: 16.2,
      frames: 391,
      nights: ["2024-05-17", "2024-06-01"],
      candidates: CANDIDATI,
    }),
    postoIgnoto({
      key: "34.00,-111.00",
      latitude: 34.0,
      longitude: -111.0,
      distance_km: 8000,
      frames: 1,
      // nessuna notte: del luogo non si riconosce un fuso, e l'app non indovina in che notte cadano
      nights: [],
      candidates: CANDIDATI,
    }),
    postoIgnoto({
      key: "46.10,12.00",
      latitude: 46.1,
      longitude: 12.0,
      distance_km: null,
      frames: 41,
      nights: ["2024-07-02"],
      site: "Casa",
      candidates: CANDIDATI,
    }),
  ],
  mosaics: [
    M42,
    mosaicoProposto({
      key: "impronta-m31",
      ra_deg: 10.7,
      dec_deg: 41.3,
      object: "M 31",
      panels: 2,
      frames: 40,
      integration_s: 7200,
      answer: "no",
      names: ["M 31"],
      proposed: "M 31",
    }),
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

describe("Da confermare -- da quale luogo", () => {
  it("un posto con quante pose, le sue notti e i luoghi dal piu' vicino, senza sceglierne uno", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza sito/i)
    const posto = riga(sezione, "45,8500 N - 11,5800 E")
    expect(posto.textContent).toMatch(/391 frame/)
    expect(prove(posto)).toEqual(["Distanza=16,2 km dal sito predefinito", "Notti=mag 2024: 17 | giu 2024: 1"])
    expect(voci(posto)).toEqual(["Cima Ekar, a 0,4 km", "Casa, a 16,2 km"])
    applicaSpento()
  })

  it("un posto di cui non si sa ancora la notte lo dice, invece di scrivere notti e basta", async () => {
    // L'app non indovina la notte di pose il cui istante non e' ancora certo: la lista esce
    // vuota, e senza una frase a schermo resterebbe **"notti:"** e poi il nulla.
    aperta()
    const sezione = await vaiASezione(/frame senza sito/i)
    const posto = riga(sezione, "34,0000 N - 111,0000 O")
    expect(prove(posto)).toContain("Notti=Notti non calcolabili senza sito")
  })

  it("la risposta porta le coordinate e il luogo scelto", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza sito/i)
    fireEvent.click(scelta(riga(sezione, "45,8500 N - 11,5800 E"), /cima ekar/i))
    expect((await mandato()).unclear).toEqual([{ key: "45.85,11.58", site_id: 3 }])
  })

  it("la risposta gia' data si legge, e ridarla uguale non manda niente", async () => {
    aperta()
    const sezione = await vaiASezione(/frame senza sito/i)
    const posto = riga(sezione, "46,1000 N - 12,0000 E")
    // il gruppo di scelte nomina il posto: con due posti aperti le scelte sono uguali
    expect(within(sezione).getByRole("radiogroup", { name: /46,1000 N - 12,0000 E/ })).toBeDefined()
    expect(scelto(scelta(posto, /^casa/i))).toBe(true)
    fireEvent.click(scelta(posto, /cima ekar/i))
    fireEvent.click(scelta(posto, /^casa/i))
    applicaSpento()
  })

  it("senza un luogo di casa non si dice una distanza da casa", async () => {
    // `distance_km` nullo e' "non c'e' una casa", non "sei a casa": uno zero sarebbe falso.
    aperta()
    const sezione = await vaiASezione(/frame senza sito/i)
    expect(riga(sezione, "46,1000 N - 12,0000 E").textContent).not.toMatch(/dal sito predefinito/)
  })

  it("senza nessun sito non si risponde: lo dice, e porta alle Impostazioni", async () => {
    aperta(daConfermare({ to_confirm: 1, unclear: [postoIgnoto({ key: "45.85,11.58", latitude: 45.85, longitude: 11.58, frames: 3 })] }))
    const posto = riga(await vaiASezione(/frame senza sito/i), "45,8500 N - 11,5800 E")
    expect(within(posto).queryAllByRole("radio")).toEqual([])
    expect(within(posto).getByText("Per rispondere serve almeno un sito: si aggiunge nelle Impostazioni.")).toBeDefined()
    fireEvent.click(within(posto).getByRole("button", { name: "Apri le Impostazioni" }))
    await waitFor(() => expect(window.location.pathname).toBe("/impostazioni/sito"))
  })
})

describe("Da confermare -- i mosaici proposti", () => {
  it("i soggetti, i pannelli, le pose e le ore, e il si' e il no senza sceglierne uno", async () => {
    aperta()
    const sezione = await vaiASezione(/mosaici/i)
    const mosaico = riga(sezione, "M 42, NGC 1977")
    // fra le ore e i frame senza durata c'e' un punto, non uno spazio solo
    expect(mosaico.querySelector(".al-conf__testo-7")?.textContent).toBe("3 pannelli · 90 frame · 3 h · 2 senza durata")
    expect(prove(mosaico)).toEqual(["Oggetti nel campo=M 42, NGC 1977", "Notte=10 gen 2024"])
    expect(voci(mosaico)).toEqual(["Mosaico", "Non è un mosaico"])
  })

  it("il si' porta la chiave del mosaico e di cosa e', gia' proposto", async () => {
    aperta()
    const sezione = await vaiASezione(/mosaici/i)
    const mosaico = riga(sezione, "M 42, NGC 1977")
    expect(within(mosaico).queryByLabelText(/oggetto del mosaico/i)).toBeNull()
    fireEvent.click(scelta(mosaico, "Mosaico"))
    const campo = within(mosaico).getByLabelText(/oggetto del mosaico/i) as HTMLInputElement
    expect(campo.value).toBe("NGC 1977")
    // un campo semplice, col nome proposto detto sotto
    expect(campo.list).toBeNull()
    expect(within(mosaico).getByText("Nome proposto dall'app: NGC 1977. Si cambia.")).toBeDefined()
    expect((await mandato()).mosaics).toEqual([
      { key: "impronta-m42", answer: "yes", name: "NGC 1977" },
    ])
  })

  it("il nome si cambia, e un nome vuoto non parte", async () => {
    aperta()
    const sezione = await vaiASezione(/mosaici/i)
    const mosaico = riga(sezione, "M 42, NGC 1977")
    fireEvent.click(scelta(mosaico, "Mosaico"))
    const campo = within(mosaico).getByLabelText(/oggetto del mosaico/i)
    fireEvent.change(campo, { target: { value: "   " } })
    applicaSpento()
    fireEvent.change(campo, { target: { value: "M 42" } })
    expect((await mandato()).mosaics).toEqual([expect.objectContaining({ name: "M 42" })])
  })

  it("un mosaico gia' confermato mostra il nome detto, e ridarlo uguale non manda niente", async () => {
    const detto = { ...M42, answer: "yes" as const, answer_name: "M 42" }
    aperta({ ...PAGINA, mosaics: [detto] })
    const sezione = await vaiASezione(/mosaici/i)
    const campo = within(riga(sezione, "M 42, NGC 1977")).getByLabelText(/oggetto del mosaico/i)
    expect(campo).toHaveProperty("value", "M 42")
    fireEvent.change(campo, { target: { value: "M 43" } })
    fireEvent.change(campo, { target: { value: "M 42" } })
    applicaSpento()
  })

  it("due mosaici degli stessi soggetti si distinguono, e ognuno nomina il suo gruppo di scelte", async () => {
    // Lo stesso soggetto ripreso in due regioni lontane da due parti: senza la regione le due righe
    // -- e i loro due gruppi di scelte -- avrebbero lo stesso nome, per chi guarda e per chi ascolta.
    const gemello = { ...M42, key: "impronta-gemello", ra_deg: 84.9, dec_deg: -1.2 }
    aperta({ ...PAGINA, mosaics: [M42, gemello] })
    const sezione = await vaiASezione(/mosaici/i)
    expect(domande(sezione)).toHaveLength(2)
    const nomi: (string | null)[] = []
    for (const quale of [/83,8/, /84,9/]) {
      // una sola domanda e' aperta: il gesto che apre l'altra dice gia' quale
      const gesto = within(sezione).queryByRole("button", { name: quale })
      if (gesto) fireEvent.click(gesto)
      nomi.push(within(sezione).getByRole("radiogroup").getAttribute("aria-label"))
    }
    expect(nomi[0]).toMatch(/M 42.*83,8/)
    expect(new Set(nomi).size).toBe(2)
  })

  it("un mosaico senza tempo non scrive zero ore", async () => {
    aperta({ ...PAGINA, mosaics: [{ ...M42, integration_s: 0, untimed: 90 }] })
    const sezione = await vaiASezione(/mosaici/i)
    const mosaico = riga(sezione, "M 42, NGC 1977")
    expect(mosaico.textContent).not.toMatch(/\b0 h/)
    expect(mosaico.textContent).toMatch(/90 senza durata/)
  })

  it("un no e' una risposta, resta, e ridarlo uguale non manda niente", async () => {
    aperta()
    const sezione = await vaiASezione(/mosaici/i)
    const mosaico = riga(sezione, "M 31")
    expect(scelto(scelta(mosaico, /^non è un mosaico$/i))).toBe(true)
    fireEvent.click(scelta(mosaico, "Mosaico"))
    fireEvent.click(scelta(mosaico, /^non è un mosaico$/i))
    applicaSpento()
  })
})

it("le sezioni senza domande non si vedono", async () => {
  aperta({ ...PAGINA, unclear: [], mosaics: [] })
  await disegna()
  vai("/da-confermare")
  // il conto, o "niente da confermare" se non resta nessuna sezione
  await waitFor(() => expect(document.querySelector(".al-conf__riga-1, .al-c-avviso__blocco-1")).not.toBeNull())
  for (const nome of [/frame senza sito/i, /mosaici/i]) {
    expect(screen.queryByRole("region", { name: nome })).toBeNull()
  }
})
