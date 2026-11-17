// @vitest-environment jsdom
/**
 * Il gesto **Aggiungi strumento** dell'Attrezzatura: uno strumento che i file non nominano, e dallo
 * stesso gesto un filtro o un setup (`docs/domini/attrezzatura.md`). Il tipo si sceglie a tasselli
 * in testa al Modulo, poi «Tipo: ... Cambia» (tavola v82 `modulo`, `componenti/Modulo` 18-19). Le
 * righe di fabbrica stanno in `attrezzatura-banco.tsx`.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { MONTATURA, OTTICA, apriAttrezzatura, attrezzatura } from "./attrezzatura-banco"
import { pulisci, scritture } from "./banco"

afterEach(pulisci)

const apri = async () =>
  fireEvent.click(await screen.findByRole("button", { name: /^aggiungi strumento$/i }))
// each kind draws its own form: the group is looked up again after every choice
const modulo = () => screen.getByRole("group", { name: "Nuovo strumento" })
const tipo = (nome: RegExp) => fireEvent.click(screen.getByRole("radio", { name: nome }))
const salva = () => screen.getByRole("button", { name: /^salva$/i })
const spento = () => salva().getAttribute("aria-disabled") === "true"
const scrivi = (etichetta: RegExp, valore: string) =>
  fireEvent.change(screen.getByLabelText(etichetta), { target: { value: valore } })

describe("aggiungo alla mia attrezzatura", () => {
  it("il tipo si sceglie a tasselli, nell'ordine della tavola, e senza tipo non si salva", async () => {
    attrezzatura()
    await apriAttrezzatura()
    await apri()

    const tasselli = within(within(modulo()).getByRole("radiogroup", { name: "Tipo" })).getAllByRole("radio")
    expect(tasselli.map((x) => x.textContent)).toEqual([
      "ottica",
      "camera",
      "montatura",
      "riduttore",
      "ruota portafiltri",
      "ottica di guida",
      "guida fuori asse",
      "camera di guida",
      "focheggiatore",
      "distanziale",
      "Filtro",
      "Setup",
    ])
    expect(spento()).toBe(true)
    expect(within(modulo()).queryByLabelText(/^nome/i)).toBeNull()
  })

  it("aggiungo un pezzo che nessun file nomina, scegliendone il tipo", async () => {
    // Il tipo si sceglie **dentro** il gesto e non fuori: un tipo senza pezzi non compare
    // nell'elenco, quindi un "aggiungi" per gruppo non permetterebbe mai il primo focheggiatore.
    attrezzatura(
      {},
      {
        "POST /api/v1/gear/instruments": { stato: 201, corpo: { id: 9, requeued: 0, run_started: false } },
      },
    )
    await apriAttrezzatura()
    await apri()

    tipo(/^focheggiatore$/)
    expect(within(modulo()).getByText("focheggiatore", { selector: "b" })).toBeDefined()
    expect(within(modulo()).queryByRole("radiogroup", { name: "Tipo" })).toBeNull()
    scrivi(/^nome/i, "EAF")
    fireEvent.click(salva())

    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.metodo).toBe("POST")
    expect(scritture()[0]?.corpo).toEqual({ kind: "focuser", name: "EAF" })
  })

  it("Cambia riapre i tasselli", async () => {
    attrezzatura()
    await apriAttrezzatura()
    await apri()

    tipo(/^ottica$/)
    fireEvent.click(within(modulo()).getByRole("button", { name: /^cambia$/i }))

    expect(within(modulo()).getByRole("radiogroup", { name: "Tipo" })).toBeDefined()
  })

  it("scrivo a mano un filtro, con la sua banda", async () => {
    attrezzatura({}, { "POST /api/v1/gear/filters": { stato: 201, corpo: { id: 4, requeued: 0, run_started: false } } })
    await apriAttrezzatura()
    await apri()

    tipo(/^filtro$/i)
    scrivi(/^nome/i, "Antlia 3nm")
    // senza banda non si salva: e' cio' che sblocca le pose
    expect(spento()).toBe(true)
    expect(screen.getByText("Per salvare serve almeno una banda.")).toBeDefined()
    scrivi(/^banda/i, "HA")
    scrivi(/^marca/i, "__altra__")
    scrivi(/^nuova marca/i, "Antlia")
    fireEvent.click(salva())

    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.url).toContain("/api/v1/gear/filters")
    expect(scritture()[0]?.corpo).toEqual({
      name: "Antlia 3nm",
      bands: [{ band: "HA", width_nm: null }],
      brand: "Antlia",
    })
  })

  it("il disco del filtro nuovo ha il colore delle sue bande, e senza bande e' l'ignoto", async () => {
    // tavola v82 `discoK`: il colore di HA + OIII e' quello del duo, non della prima banda
    attrezzatura()
    await apriAttrezzatura()
    await apri()
    tipo(/^filtro$/i)
    const disco = () => modulo().querySelector(".al-c-modulo__tondo-1") as HTMLElement
    expect(disco().style.border).toContain("dashed")

    fireEvent.click(within(screen.getByRole("radiogroup", { name: "Quante bande" })).getByRole("radio", { name: "2" }))
    scrivi(/^banda 1/i, "OIII")
    scrivi(/^banda 2/i, "HA")

    expect(disco().style.background).toBe("var(--filtro-ha-oiii)")
  })

  it("il nome scritto per uno strumento non parte dopo un giro su filtro o setup", async () => {
    attrezzatura()
    await apriAttrezzatura()
    await apri()
    const cambia = () => fireEvent.click(within(modulo()).getByRole("button", { name: /^cambia$/i }))

    tipo(/^focheggiatore$/)
    scrivi(/^nome/i, "EAF")
    cambia()
    tipo(/^filtro$/i)
    cambia()
    tipo(/^focheggiatore$/)

    // la casella e' vuota, e Salva non manda il nome che non si vede piu'
    expect((screen.getByLabelText(/^nome/i) as HTMLInputElement).value).toBe("")
    expect(spento()).toBe(true)
  })

  it("scrivo a mano un setup, con ottica e camera fra i miei pezzi e la focale", async () => {
    const camera = { ...OTTICA, id: 5, kind: "camera", name: "ASI533MC" }
    attrezzatura(
      { instruments: [OTTICA, camera, MONTATURA] },
      { "POST /api/v1/gear/rigs": { stato: 201, corpo: { id: 11, requeued: 0, run_started: false } } },
    )
    await apriAttrezzatura()
    await apri()

    tipo(/^setup$/i)
    const ottiche = within(screen.getByRole("radiogroup", { name: "Ottica" })).getAllByRole("radio")
    expect(ottiche.map((o) => o.textContent)).toEqual(["TS 130 APO"]) // solo le ottiche, non la montatura
    fireEvent.click(ottiche[0] as HTMLElement)
    fireEvent.click(within(screen.getByRole("radiogroup", { name: "Camera" })).getByRole("radio", { name: "ASI533MC" }))
    expect(spento()).toBe(true)
    expect(screen.getByText("Per salvare servono ottica, camera e focale effettiva.")).toBeDefined()
    scrivi(/^focale effettiva/i, "910")
    fireEvent.click(salva())

    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.url).toContain("/api/v1/gear/rigs")
    expect(scritture()[0]?.corpo).toEqual({ optics_id: 1, camera_id: 5, focal_mm: 910 })
  })

  it("un setup che ho gia' si rifiuta, e me lo dice", async () => {
    const camera = { ...OTTICA, id: 5, kind: "camera", name: "ASI2600MM" }
    attrezzatura(
      { instruments: [OTTICA, camera] },
      { "POST /api/v1/gear/rigs": { stato: 409, corpo: { detail: { code: "rig_exists" } } } },
    )
    await apriAttrezzatura()
    await apri()

    tipo(/^setup$/i)
    fireEvent.click(screen.getByRole("radio", { name: "TS 130 APO" }))
    fireEvent.click(screen.getByRole("radio", { name: "ASI2600MM" }))
    scrivi(/^focale effettiva/i, "920")
    fireEvent.click(salva())

    expect(await screen.findByText(/setup già presente/i)).toBeDefined()
  })

  it("cambiando tipo non porto con me i campi del tipo di prima", async () => {
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
    await apri()

    tipo(/^ottica$/)
    scrivi(/apertura/i, "130")
    // La marca invece e' di **tutti** i tipi: resta in pagina con cio' che ci ho scritto, e
    // buttarla via vorrebbe dire una casella che dice una cosa e un'app che ne manda un'altra.
    scrivi(/^marca/i, "__altra__")
    scrivi(/^nuova marca/i, "ZWO")
    fireEvent.click(within(modulo()).getByRole("button", { name: /^cambia$/i }))
    tipo(/^montatura$/)
    expect((screen.getByLabelText(/^nuova marca/i) as HTMLInputElement).value).toBe("ZWO")
    scrivi(/^nome/i, "EQ6-R")
    fireEvent.click(salva())

    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ brand: "ZWO", kind: "mount", name: "EQ6-R" })
  })

  it("un campo che il modulo non mostra piu' non parte", async () => {
    // Trovato in revisione: raffreddamento scritto, poi "Raffreddata: no" lo nasconde; la camera
    // nasceva lo stesso coi gradi che a schermo non c'erano piu'.
    attrezzatura(
      {},
      {
        "POST /api/v1/gear/instruments": { stato: 201, corpo: { id: 9, requeued: 0, run_started: false } },
      },
    )
    await apriAttrezzatura()
    await apri()

    tipo(/^camera$/)
    scrivi(/^nome/i, "ASI2600MM")
    const raffreddata = () => screen.getByRole("radiogroup", { name: "Raffreddata" })
    fireEvent.click(within(raffreddata()).getByRole("radio", { name: "sì" }))
    scrivi(/^raffreddamento/i, "10")
    fireEvent.click(within(raffreddata()).getByRole("radio", { name: "no" }))
    fireEvent.click(salva())

    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ kind: "camera", name: "ASI2600MM", cooled: false })
  })

  it("senza nome non posso salvare, e lo vedo prima di premere", async () => {
    // Un nome vuoto l'API lo rifiuta: mandarlo vorrebbe dire far leggere all'utente un errore
    // generico per una cosa che si vede prima. E' la stessa scelta della scheda di un sito.
    attrezzatura()
    await apriAttrezzatura()
    await apri()

    tipo(/^focheggiatore$/)
    expect(spento()).toBe(true)
    expect(screen.getByText("Per salvare serve il nome.")).toBeDefined()

    scrivi(/^nome/i, "EAF")

    expect(spento()).toBe(false)
  })

  it("a mani vuote posso scrivere cosa possiedo", async () => {
    // Chi non ha ancora scansionato e' proprio quello che ha piu' bisogno di dirlo: se il gesto
    // vivesse solo accanto a un pezzo, a mani vuote non ci sarebbe nessun pezzo accanto a cui
    // metterlo.
    attrezzatura({ instruments: [], rigs: [], filters: [] })
    await apriAttrezzatura()

    expect(await screen.findByRole("button", { name: /^aggiungi strumento$/i })).toBeDefined()
  })

  it("un nome che possiedo gia' me lo dice, invece di far finta", async () => {
    attrezzatura(
      {},
      {
        "POST /api/v1/gear/instruments": { stato: 409, corpo: { detail: { code: "name_taken" } } },
      },
    )
    await apriAttrezzatura()
    await apri()

    tipo(/^ottica$/)
    scrivi(/^nome/i, "TS 130 APO")
    fireEvent.click(salva())

    expect(await screen.findByText(/nome già usato da uno strumento dello stesso tipo/i)).toBeDefined()
  })
})
