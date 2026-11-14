// @vitest-environment jsdom
/**
 * I **gesti** della pagina Attrezzatura (tavola v82, `modulo`): correggere la scheda di un pezzo o di
 * un filtro, unirli, eliminarli. Un campo non toccato non parte; un rifiuto si legge.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  FILTRO,
  MONTATURA,
  OTTICA,
  apriAttrezzatura,
  attrezzatura,
  carta,
  vedi,
} from "./attrezzatura-banco"
import { pulisci, scritture } from "./banco"

afterEach(pulisci)

describe("i gesti sull attrezzatura", () => {
  /** Apre la scheda di un pezzo dalla sua riga: e' la strada dell'utente, che vede l'errore
   *  mentre guarda il pezzo e lo corregge li'. */
  async function apriLaScheda(genere: RegExp, nomeDelPezzo: RegExp) {
    const elenco = await vedi(genere)
    const riga = within(elenco)
      .getAllByRole("listitem")
      .find((l) => nomeDelPezzo.test(l.querySelector(".al-attr__testo-26")?.textContent ?? ""))
    fireEvent.click(within(riga as HTMLElement).getByRole("button", { name: /^modifica/i }))
  }

  it("correggo la scheda di un pezzo dalla pagina in cui lo guardo", async () => {
    attrezzatura(
      {},
      {
        "PATCH /api/v1/gear/instruments/1": {
          stato: 200,
          corpo: { id: 1, requeued: 0, run_started: false },
        },
      },
    )
    await apriAttrezzatura()
    await apriLaScheda(/telescopi/i, /TS 130 APO/)

    fireEvent.change(screen.getByLabelText(/apertura/i), { target: { value: "132" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))

    await waitFor(() => expect(scritture()).toHaveLength(1))
    const mandato = scritture()[0]
    expect(mandato?.url).toContain("/api/v1/gear/instruments/1")
    expect(mandato?.metodo).toBe("PATCH")
    // **Per intero, non a sottoinsieme**: la regola e' che un campo non toccato NON parte --
    // rimandare cio' che l'app ha letto dai file lo farebbe diventare una tua dichiarazione. Con
    // `toMatchObject` una scheda rimandata tutta intera resterebbe verde.
    expect(mandato?.corpo).toEqual({ aperture_mm: 132 })
  })

  it("la scheda chiede i campi del genere che sta guardando, e li decide il backend", async () => {
    // La portata e' della montatura, l'apertura del telescopio: la pagina non tiene un secondo
    // elenco di quali campi valgono per quale genere, lo manda l'API con ogni pezzo.
    attrezzatura()
    await apriAttrezzatura()
    await apriLaScheda(/montature/i, /EQ6-R/)

    expect(screen.getByLabelText(/carico con contrappeso/i)).toBeDefined()
    expect(screen.queryByLabelText(/apertura/i)).toBeNull()
  })

  it("cio' che scelgo in una scheda resta scelto, e parte solo quello", async () => {
    // Visto dal vivo: la scelta del colore tornava indietro appena la si mollava, perche'
    // mostrava il valore **letto dai file** invece di quello appena scelto.
    attrezzatura(
      {
        instruments: [
          {
            ...OTTICA,
            id: 4,
            kind: "camera",
            name: "ASI2600MM",
            aperture_mm: null,
            focal_mm: null,
          },
        ],
      },
      {
        "PATCH /api/v1/gear/instruments/4": {
          stato: 200,
          corpo: { id: 4, requeued: 0, run_started: false },
        },
      },
    )
    await apriAttrezzatura()
    await apriLaScheda(/^camere/i, /ASI2600MM/)

    const mono = within(screen.getByRole("radiogroup", { name: /tipo di sensore/i })).getByRole(
      "radio",
      { name: /^mono/i },
    )
    fireEvent.click(mono)
    expect(mono.getAttribute("aria-checked")).toBe("true")
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ camera_type: "mono" })
  })

  it("la risoluzione si scrive in un campo, larghezza per altezza, e il campo dice da dove viene", async () => {
    const camera = {
      ...OTTICA,
      id: 4,
      kind: "camera",
      name: "ASI2600MM",
      aperture_mm: null,
      focal_mm: null,
    }
    attrezzatura(
      { instruments: [{ ...camera, pixel_size_um: 3.76, from_files: ["pixel_size_um"] }] },
      {
        "PATCH /api/v1/gear/instruments/4": {
          stato: 200,
          corpo: { id: 4, requeued: 0, run_started: false },
        },
      },
    )
    await apriAttrezzatura()
    await apriLaScheda(/^camere/i, /ASI2600MM/)

    const pixel = screen.getByLabelText(/^pixel/i)
    expect(pixel.closest("div")?.textContent).toContain("dai file")
    fireEvent.change(pixel, { target: { value: "3,8" } })
    expect(pixel.closest("div")?.textContent).toContain("inserito")
    fireEvent.change(screen.getByLabelText(/^risoluzione/i), { target: { value: "6248 × 4176" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ pixel_size_um: 3.8, width_px: 6248, height_px: 4176 })
  })

  it("il bias si scrive per offset, uno per campo", async () => {
    const camera = {
      ...OTTICA,
      id: 4,
      kind: "camera",
      name: "ASI2600MM",
      aperture_mm: null,
      focal_mm: null,
    }
    attrezzatura(
      {
        instruments: [
          {
            ...camera,
            biases: [
              { offset: 30, bias_adu: null, frames: 1 },
              { offset: 50, bias_adu: 500, frames: 2 },
            ],
          },
        ],
      },
      {
        "PATCH /api/v1/gear/instruments/4": {
          stato: 200,
          corpo: { id: 4, requeued: 0, run_started: false },
        },
        "PUT /api/v1/gear/instruments/4/biases": {
          stato: 200,
          corpo: { offset: 30, bias_adu: 480, frames: 1 },
        },
      },
    )
    await apriAttrezzatura()
    const camere = await vedi(/^camere/i)
    expect(camere.textContent).toContain("bias 500 ADU, offset 50")
    await apriLaScheda(/^camere/i, /ASI2600MM/)

    fireEvent.change(screen.getByLabelText("Bias (ADU), offset 30"), { target: { value: "480" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(2))
    // prima il bias: il PATCH puo' far partire il lavoro, e allora il bias aspetterebbe (409)
    expect(scritture()[0]?.url).toContain("/api/v1/gear/instruments/4/biases")
    expect(scritture()[0]?.corpo).toEqual({ offset: 30, bias_adu: 480 })
  })

  it("senza nome non si salva, e il perche' e' accanto a Salva", async () => {
    attrezzatura()
    await apriAttrezzatura()
    await apriLaScheda(/telescopi/i, /TS 130 APO/)
    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "  " } })
    expect(screen.getByRole("button", { name: /salva/i }).getAttribute("aria-disabled")).toBe(
      "true",
    )
    expect(screen.getByText("Per salvare serve il nome.")).toBeDefined()
  })

  it("unisco due grafie dello stesso pezzo, solo fra quelle che l'API offre", async () => {
    const altra = { ...OTTICA, id: 5, name: "TS130APO", mergeable_into: [1] }
    attrezzatura(
      { instruments: [{ ...OTTICA, mergeable_into: [5] }, altra, MONTATURA] },
      {
        "PATCH /api/v1/gear/instruments/1": {
          stato: 200,
          corpo: { id: 1, requeued: 3, run_started: true },
        },
      },
    )
    await apriAttrezzatura()
    await apriLaScheda(/telescopi/i, /^TS 130 APO/)
    fireEvent.change(screen.getByLabelText(/^unisci a/i), { target: { value: "5" } })
    // scelta l'unione, la scheda si nasconde: non partirebbe, e si perderebbe in silenzio
    expect(screen.queryByLabelText(/apertura/i)).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ merge_into: 5 })
  })

  it("scelgo un'unione e torno indietro: parte cio' che vedo, non cio' che avevo scritto prima", async () => {
    // Il nome riappare col valore di prima: se la scritta tenesse "Pippo", il pezzo verrebbe
    // rinominato senza che a video si veda.
    const altra = { ...OTTICA, id: 5, name: "TS130APO", mergeable_into: [1] }
    attrezzatura(
      { instruments: [{ ...OTTICA, mergeable_into: [5] }, altra, MONTATURA] },
      {
        "PATCH /api/v1/gear/instruments/1": {
          stato: 200,
          corpo: { id: 1, requeued: 0, run_started: false },
        },
      },
    )
    await apriAttrezzatura()
    await apriLaScheda(/telescopi/i, /^TS 130 APO/)
    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "Pippo" } })
    const unione = screen.getByLabelText(/^unisci a/i)
    fireEvent.change(unione, { target: { value: "5" } })
    fireEvent.change(unione, { target: { value: "" } })
    expect(screen.getByLabelText(/^nome/i)).toHaveProperty("value", "TS 130 APO")
    fireEvent.change(screen.getByLabelText(/apertura/i), { target: { value: "132" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ aperture_mm: 132 })
  })

  it("un pezzo senza unioni possibili non offre la tendina", async () => {
    attrezzatura()
    await apriAttrezzatura()
    await apriLaScheda(/montature/i, /EQ6-R/)
    expect(screen.queryByLabelText(/^unisci a/i)).toBeNull()
  })

  it("do un nome a un setup", async () => {
    attrezzatura(
      {},
      {
        "PATCH /api/v1/gear/rigs/10": {
          stato: 200,
          corpo: { id: 10, requeued: 0, run_started: false },
        },
      },
    )
    await apriAttrezzatura()
    const nome = await carta()
    fireEvent.click(within(nome).getByRole("button", { name: "Rinomina Il grande" }))
    // la casella, non la regione: anche la scheda ora si chiama "Nome di ..."
    fireEvent.change(screen.getByRole("textbox", { name: /^nome/i }), {
      target: { value: "Il piccolo" },
    })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.url).toContain("/api/v1/gear/rigs/10")
    expect(scritture()[0]?.corpo).toEqual({ name: "Il piccolo" })
  })

  it("correggo la marca di un filtro fra quelle gia' scritte, o ne scrivo una nuova", async () => {
    attrezzatura(
      { brands: ["Baader"] },
      {
        "PATCH /api/v1/gear/filters/3": {
          stato: 200,
          corpo: { id: 3, requeued: 0, run_started: false },
        },
      },
    )
    await apriAttrezzatura()
    await apriLaScheda(/filtri/i, /^Ha/)
    const marca = screen.getByLabelText(/^marca/i)
    expect(within(marca).getByRole("option", { name: "Baader" })).toBeDefined()
    fireEvent.change(marca, { target: { value: "__altra__" } })
    fireEvent.change(screen.getByLabelText(/^nuova marca/i), { target: { value: "Antlia" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.url).toContain("/api/v1/gear/filters/3")
    expect(scritture()[0]?.corpo).toEqual({ brand: "Antlia" })
  })

  it("le bande di un filtro si scrivono con la larghezza, e senza bande non si salva", async () => {
    attrezzatura(
      {},
      {
        "PATCH /api/v1/gear/filters/3": {
          stato: 200,
          corpo: { id: 3, requeued: 60, run_started: true },
        },
      },
    )
    await apriAttrezzatura()
    await apriLaScheda(/filtri/i, /^Ha/)
    fireEvent.click(
      within(screen.getByRole("radiogroup", { name: /quante bande/i })).getByRole("radio", {
        name: "2",
      }),
    )
    fireEvent.change(screen.getByLabelText("Banda 2"), { target: { value: "OIII" } })
    fireEvent.change(screen.getAllByLabelText(/larghezza/i)[1] as HTMLElement, {
      target: { value: "3,5" },
    })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({
      bands: [
        { band: "HA", width_nm: 3 },
        { band: "OIII", width_nm: 3.5 },
      ],
    })
    expect(await screen.findByText("60 frame da rielaborare")).toBeDefined()
  })

  it("un filtro che l'app conosce dal nome mostra la sua banda e si rinomina senza scriverla", async () => {
    // visto dal collaudatore, 14/11: senza bande scritte Salva restava spento
    attrezzatura(
      { filters: [{ ...FILTRO, passband: "L", bands: [], name: "Lum" }] },
      {
        "PATCH /api/v1/gear/filters/3": {
          stato: 200,
          corpo: { id: 3, requeued: 0, run_started: false },
        },
      },
    )
    await apriAttrezzatura()
    expect(within(await vedi(/filtri/i)).getByText("L")).toBeDefined()
    await apriLaScheda(/filtri/i, /^Lum/)
    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "Luminanza" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ name: "Luminanza" })
  })

  it("una banda che l'app non conosce non si scrive col suo codice", async () => {
    // visto sulle catture, 14/11: «UNKNOWN», «OSC», «DUO_HAOIII» a schermo
    attrezzatura({ filters: [{ ...FILTRO, passband: "UNKNOWN", bands: [], name: "X" }] })
    await apriAttrezzatura()
    expect((await vedi(/filtri/i)).textContent).not.toContain("UNKNOWN")
  })

  it("il nome di un altro filtro si dice con le parole dei filtri", async () => {
    attrezzatura(
      {},
      { "PATCH /api/v1/gear/filters/3": { stato: 409, corpo: { detail: { code: "name_taken" } } } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/filtri/i, /^Ha/)
    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "Lum" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    expect((await screen.findByRole("alert")).textContent).toContain(
      "Nome già usato da un altro filtro.",
    )
  })

  it("un pezzo senza frame non dice un'ora che non c'e'", async () => {
    attrezzatura({ instruments: [{ ...OTTICA, frames: 0, integration_s: 0, bar_pct: 3 }] })
    await apriAttrezzatura()
    const telescopi = await vedi(/telescopi/i)
    expect(telescopi.textContent).toContain("non indicato nei file")
    expect(telescopi.querySelector('[data-an="barra"]')).toBeNull()
  })

  it("un'eliminazione rifiutata si dice come gli altri errori del modulo", async () => {
    attrezzatura(
      {},
      {
        "DELETE /api/v1/gear/instruments/2": {
          stato: 404,
          corpo: { detail: { code: "not_found" } },
        },
      },
    )
    await apriAttrezzatura()
    await apriLaScheda(/montature/i, /EQ6-R/)
    fireEvent.click(screen.getByRole("button", { name: /^elimina$/i }))
    fireEvent.click(
      within(screen.getByRole("alertdialog")).getByRole("button", { name: /^elimina$/i }),
    )
    expect((await screen.findByRole("alert")).textContent).toContain("Dati non aggiornati")
  })

  it("un pezzo usato non si elimina: Elimina spento, chi lo usa e Unisci a", async () => {
    const altra = { ...OTTICA, id: 5, name: "TS130APO" }
    attrezzatura({
      instruments: [
        {
          ...OTTICA,
          mergeable_into: [5],
          delete_refused: { code: "in_use", frames: 120, rigs: [10] },
        },
        altra,
      ],
    })
    await apriAttrezzatura()
    await apriLaScheda(/telescopi/i, /^TS 130 APO/)

    const elimina = screen.getByRole("button", { name: /^elimina$/i })
    expect(elimina.getAttribute("aria-disabled")).toBe("true")
    expect(
      screen.getByText(
        "Lo usano 120 frame di Il grande: nessuna ora si perde. Uniscilo a un altro pezzo, se è lo stesso.",
      ),
    ).toBeDefined()
    fireEvent.click(elimina)
    expect(screen.queryByRole("alertdialog")).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: /^unisci a$/i }))
    expect(document.activeElement).toBe(screen.getByLabelText(/^unisci a/i))
  })

  it("l'ottica di un setup senza frame dice che ne fa parte", async () => {
    attrezzatura({
      instruments: [{ ...OTTICA, delete_refused: { code: "in_rig", frames: 0, rigs: [10] } }],
    })
    await apriAttrezzatura()
    await apriLaScheda(/telescopi/i, /TS 130 APO/)
    expect(
      screen.getByText(
        "Fa parte di Il grande: un setup è fatto della sua ottica e della sua camera.",
      ),
    ).toBeDefined()
  })

  it("un pezzo senza frame si elimina dopo la conferma, che dice da quali setup esce", async () => {
    attrezzatura(
      {
        instruments: [OTTICA, { ...MONTATURA, in_rigs: [{ rig_id: 10, frames: 0, chosen: true }] }],
      },
      { "DELETE /api/v1/gear/instruments/2": { stato: 204, corpo: null } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/montature/i, /EQ6-R/)
    fireEvent.click(screen.getByRole("button", { name: /^elimina$/i }))

    const domanda = screen.getByRole("alertdialog", { name: "Eliminare EQ6-R? Non tiene frame." })
    expect(domanda.textContent).toContain("Esce anche da Il grande.")
    fireEvent.click(within(domanda).getByRole("button", { name: /^elimina$/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.metodo).toBe("DELETE")
    expect(scritture()[0]?.url).toContain("/api/v1/gear/instruments/2")
  })

  it("con la scansione in corso Salva ed Elimina sono spenti, e lo dicono", async () => {
    attrezzatura(
      {},
      {
        "/api/v1/pipeline/status": {
          stato: 200,
          corpo: { action: "stop", worker: { state: "running", stage: null, stages: [] } },
        },
      },
    )
    await apriAttrezzatura()
    await apriLaScheda(/montature/i, /EQ6-R/)
    expect(await screen.findByText("Scansione in corso: si salva al termine.")).toBeDefined()
    expect(screen.getByRole("button", { name: /salva/i }).getAttribute("aria-disabled")).toBe(
      "true",
    )
    expect(screen.getByText("Scansione in corso: si elimina al termine.")).toBeDefined()
    expect(screen.getByRole("button", { name: /^elimina$/i }).getAttribute("aria-disabled")).toBe(
      "true",
    )
  })

  it("dico che un filtro e' lo stesso di un altro, fra quelli che l'API offre", async () => {
    attrezzatura(
      {
        filters: [
          { ...FILTRO, mergeable_into: [4] },
          { ...FILTRO, id: 4, name: "Baader Ha" },
          { ...FILTRO, id: 5, name: "H" },
        ],
      },
      {
        "PATCH /api/v1/gear/filters/3": {
          stato: 200,
          corpo: { id: 3, requeued: 60, run_started: true },
        },
      },
    )
    await apriAttrezzatura()
    await apriLaScheda(/filtri/i, /^Ha/)
    const tendina = screen.getByLabelText(/^unisci a/i)
    expect(within(tendina).queryByRole("option", { name: "H" })).toBeNull()
    fireEvent.change(tendina, { target: { value: "4" } })
    expect(screen.queryByLabelText(/marca/i)).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ merge_into: 4 })
  })
})
