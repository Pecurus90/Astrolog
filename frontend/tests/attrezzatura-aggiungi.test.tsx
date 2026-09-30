// @vitest-environment jsdom
/**
 * Il gesto **Aggiungi un pezzo** dell'Attrezzatura: uno strumento che i file non nominano, e dallo
 * stesso gesto un filtro o un corredo (`docs/domini/attrezzatura.md`). Le righe di fabbrica stanno
 * in `attrezzatura-banco.tsx`.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { MONTATURA, OTTICA, apriAttrezzatura, attrezzatura } from "./attrezzatura-banco"
import { pulisci, scritture } from "./banco"

afterEach(pulisci)

describe("aggiungo alla mia attrezzatura", () => {
  it("aggiungo un pezzo che nessun file nomina, scegliendone il genere", async () => {
    // Il genere si sceglie **dentro** il gesto e non fuori: un genere senza pezzi non compare
    // nell'elenco, quindi un "aggiungi" per gruppo non permetterebbe mai il primo focheggiatore.
    attrezzatura(
      {},
      {
        "POST /api/v1/gear/instruments": { stato: 201, corpo: { id: 9, requeued: 0, run_started: false } },
      },
    )
    await apriAttrezzatura()

    fireEvent.click(await screen.findByRole("button", { name: /aggiungi un pezzo/i }))
    fireEvent.change(screen.getByLabelText(/genere/i), { target: { value: "focuser" } })
    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "EAF" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))

    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.metodo).toBe("POST")
    expect(scritture()[0]?.corpo).toEqual({ kind: "focuser", name: "EAF" })
  })

  it("scrivo a mano un filtro, con la sua banda", async () => {
    attrezzatura({}, { "POST /api/v1/gear/filters": { stato: 201, corpo: { id: 4, requeued: 0, run_started: false } } })
    await apriAttrezzatura()

    fireEvent.click(await screen.findByRole("button", { name: /aggiungi un pezzo/i }))
    fireEvent.change(screen.getByLabelText(/genere/i), { target: { value: "filter" } })
    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "Antlia 3nm" } })
    // senza banda non si salva: e' cio' che sblocca le pose
    expect((screen.getByRole("button", { name: /salva/i }) as HTMLButtonElement).disabled).toBe(true)
    fireEvent.change(screen.getByLabelText(/^banda/i), { target: { value: "HA" } })
    fireEvent.change(screen.getByLabelText(/^marca/i), { target: { value: "Antlia" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))

    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.url).toContain("/api/v1/gear/filters")
    expect(scritture()[0]?.corpo).toEqual({ name: "Antlia 3nm", bands: [{ band: "HA" }], brand: "Antlia" })
  })

  it("il nome scritto per uno strumento non parte dopo un giro su filtro o corredo", async () => {
    attrezzatura()
    await apriAttrezzatura()

    fireEvent.click(await screen.findByRole("button", { name: /aggiungi un pezzo/i }))
    fireEvent.change(screen.getByLabelText(/genere/i), { target: { value: "focuser" } })
    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "EAF" } })
    fireEvent.change(screen.getByLabelText(/genere/i), { target: { value: "filter" } })
    fireEvent.change(screen.getByLabelText(/genere/i), { target: { value: "focuser" } })

    // la casella e' vuota, e Salva non manda il nome che non si vede piu'
    expect((screen.getByLabelText(/^nome/i) as HTMLInputElement).value).toBe("")
    expect((screen.getByRole("button", { name: /salva/i }) as HTMLButtonElement).disabled).toBe(true)
  })

  it("scrivo a mano un corredo, con ottica e camera fra i miei pezzi e la focale", async () => {
    const camera = { ...OTTICA, id: 5, kind: "camera", name: "ASI533MC" }
    attrezzatura(
      { instruments: [OTTICA, camera, MONTATURA] },
      { "POST /api/v1/gear/rigs": { stato: 201, corpo: { id: 11, requeued: 0, run_started: false } } },
    )
    await apriAttrezzatura()

    fireEvent.click(await screen.findByRole("button", { name: /aggiungi un pezzo/i }))
    fireEvent.change(screen.getByLabelText(/genere/i), { target: { value: "rig" } })
    const ottiche = within(screen.getByLabelText(/^ottica/i)).getAllByRole("option").map((o) => o.textContent)
    expect(ottiche).toEqual(["--", "TS 130 APO"]) // solo le ottiche, non la montatura
    fireEvent.change(screen.getByLabelText(/^ottica/i), { target: { value: "1" } })
    fireEvent.change(screen.getByLabelText(/^camera/i), { target: { value: "5" } })
    expect((screen.getByRole("button", { name: /salva/i }) as HTMLButtonElement).disabled).toBe(true)
    fireEvent.change(screen.getByLabelText(/^focale/i), { target: { value: "910" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))

    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.url).toContain("/api/v1/gear/rigs")
    expect(scritture()[0]?.corpo).toEqual({ optics_id: 1, camera_id: 5, focal_mm: 910 })
  })

  it("un corredo che ho gia' si rifiuta, e me lo dice", async () => {
    const camera = { ...OTTICA, id: 5, kind: "camera", name: "ASI2600MM" }
    attrezzatura(
      { instruments: [OTTICA, camera] },
      { "POST /api/v1/gear/rigs": { stato: 409, corpo: { detail: { code: "rig_exists" } } } },
    )
    await apriAttrezzatura()

    fireEvent.click(await screen.findByRole("button", { name: /aggiungi un pezzo/i }))
    fireEvent.change(screen.getByLabelText(/genere/i), { target: { value: "rig" } })
    fireEvent.change(screen.getByLabelText(/^ottica/i), { target: { value: "1" } })
    fireEvent.change(screen.getByLabelText(/^camera/i), { target: { value: "5" } })
    fireEvent.change(screen.getByLabelText(/^focale/i), { target: { value: "920" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))

    expect(await screen.findByText(/questo corredo ce l'hai gia'/i)).toBeDefined()
  })

  it("cambiando genere non porto con me i campi del genere di prima", async () => {
    // Trovato in revisione: scritta l'apertura su un telescopio e poi scelta "montatura", la
    // montatura nasceva **con un'apertura**. Su quei due campi lo schema non ha nessun CHECK che
    // la fermi, quindi il database la salvava e la riga la stampava.
    attrezzatura(
      {},
      {
        "POST /api/v1/gear/instruments": { stato: 201, corpo: { id: 9, requeued: 0, run_started: false } },
      },
    )
    await apriAttrezzatura()

    fireEvent.click(await screen.findByRole("button", { name: /aggiungi un pezzo/i }))
    fireEvent.change(screen.getByLabelText(/apertura/i), { target: { value: "130" } })
    // La marca invece e' di **tutti** i generi: resta in pagina con cio' che ci ho scritto, e
    // buttarla via vorrebbe dire una casella che dice una cosa e un'app che ne manda un'altra.
    fireEvent.change(screen.getByLabelText(/marca/i), { target: { value: "ZWO" } })
    fireEvent.change(screen.getByLabelText(/genere/i), { target: { value: "mount" } })
    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "EQ6-R" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))

    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ brand: "ZWO", kind: "mount", name: "EQ6-R" })
  })

  it("senza nome non posso salvare, e lo vedo prima di premere", async () => {
    // Un nome vuoto l'API lo rifiuta: mandarlo vorrebbe dire far leggere all'utente un errore
    // generico per una cosa che si vede prima. E' la stessa scelta della scheda di un sito.
    attrezzatura()
    await apriAttrezzatura()

    fireEvent.click(await screen.findByRole("button", { name: /aggiungi un pezzo/i }))
    const salva = screen.getByRole("button", { name: /salva/i })
    expect(salva).toHaveProperty("disabled", true)

    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "EAF" } })

    expect(salva).toHaveProperty("disabled", false)
  })

  it("a mani vuote posso scrivere cosa possiedo", async () => {
    // Chi non ha ancora scansionato e' proprio quello che ha piu' bisogno di dirlo: se il gesto
    // vivesse solo accanto a un pezzo, a mani vuote non ci sarebbe nessun pezzo accanto a cui
    // metterlo.
    attrezzatura({ instruments: [], rigs: [], filters: [] })
    await apriAttrezzatura()

    expect(await screen.findByRole("button", { name: /aggiungi un pezzo/i })).toBeDefined()
  })

  it("un nome che possiedo gia' me lo dice, invece di far finta", async () => {
    attrezzatura(
      {},
      {
        "POST /api/v1/gear/instruments": { stato: 409, corpo: { detail: { code: "name_taken" } } },
      },
    )
    await apriAttrezzatura()

    fireEvent.click(await screen.findByRole("button", { name: /aggiungi un pezzo/i }))
    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "TS 130 APO" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))

    expect(await screen.findByText(/lo possiedi gia'/i)).toBeDefined()
  })
})
