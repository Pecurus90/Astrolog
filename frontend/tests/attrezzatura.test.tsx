// @vitest-environment jsdom
/**
 * La pagina **Attrezzatura**: con cosa hai ripreso, e quanto.
 *
 * La regola che la pagina non deve tradire e' una sola, e viene dal contratto: **si mostra solo
 * cio' che l'app possiede davvero**. Dove un numero non c'e' -- le ore di una montatura, la scala
 * di un corredo di cui non si sono ancora riconosciute le pose -- si scrive **perche'**, mai uno zero
 * (`docs/domini/attrezzatura.md`).
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { CORREDO, FILTRO, MONTATURA, OTTICA, apriAttrezzatura, attrezzatura } from "./attrezzatura-banco"
import { SALUTE, SPINA, STANOTTE, impostazioni, pulisci, rispondi, scritture } from "./banco"

afterEach(pulisci)

describe("l Attrezzatura", () => {
  it("elenca i pezzi che possiedi, raccolti per genere", async () => {
    attrezzatura()
    await apriAttrezzatura()

    const telescopi = await screen.findByRole("list", { name: /telescopi/i })
    expect(within(telescopi).getByText(/TS 130 APO/)).toBeDefined()
    const montature = screen.getByRole("list", { name: /montature/i })
    expect(within(montature).getByText(/EQ6-R/)).toBeDefined()
    expect(screen.getByRole("list", { name: /corredi/i })).toBeDefined()
    expect(screen.getByRole("list", { name: /filtri/i })).toBeDefined()
  })

  it("un genere senza pezzi non compare affatto", async () => {
    // Otto titoli vuoti sarebbero l'elenco di cio' che **non** hai. Visto verde togliendo la
    // riga che nasconde i gruppi vuoti: senza questa prova, quella riga era un commento.
    attrezzatura({ instruments: [OTTICA] })
    await apriAttrezzatura()

    expect(await screen.findByRole("list", { name: /telescopi/i })).toBeDefined()
    expect(screen.queryByRole("list", { name: /montature/i })).toBeNull()
    expect(screen.queryByRole("list", { name: /focheggiatori/i })).toBeNull()
  })

  it("un pezzo dice cosa ci hai ripreso", async () => {
    attrezzatura()
    await apriAttrezzatura()

    const corredi = await screen.findByRole("list", { name: /corredi/i })
    const riga = within(corredi).getByRole("listitem")
    expect(riga.textContent).toContain("M 31")
    expect(riga.textContent).toContain("120 frame")
    expect(riga.textContent).toContain("10 h") // 36.000 s, gia' sommate dal backend
    expect(riga.textContent).toContain("7 notti")
    // e lo stesso vale per un pezzo e per un filtro, non solo per il corredo
    const telescopi = screen.getByRole("list", { name: /telescopi/i })
    expect(telescopi.textContent).toContain("M 31")
    expect(screen.getByRole("list", { name: /filtri/i }).textContent).toContain("M 42")
  })

  it("un pezzo non ancora contato dice che si sta contando, non che i file tacciono", async () => {
    // Alla prima scansione una camera nasce a meta' giro e i suoi numeri arrivano a fine giro:
    // "i tuoi file non dicono quale hai usato" sarebbe falso, e lo dice gia' una ruota che nessun
    // file nomina.
    attrezzatura({
      instruments: [
        { ...OTTICA, frames: null, integration_s: null, untimed: null, nights: null, counted: false },
        { ...MONTATURA, id: 7, kind: "filter_wheel", name: "EFW", payload_kg: null, no_hours: "files_silent" },
      ],
    })
    await apriAttrezzatura()

    const telescopi = await screen.findByRole("list", { name: /telescopi/i })
    expect(telescopi.textContent).toMatch(/si sta contando/)
    expect(telescopi.textContent).not.toMatch(/non dicono/)
    expect(screen.getByRole("list", { name: /ruote/i }).textContent).toMatch(/non dicono/)
  })

  it("il pixel ricavato dal cielo si dice ricavato, e quello dei file vince", async () => {
    // Marco, 23/9/2026: quando i file non dicono il pixel, si ricava dalla scala misurata. Si dice
    // da dove viene, perche' non e' la stessa certezza; e se i file lo dicono, si legge quello.
    const camera = { ...OTTICA, id: 5, kind: "camera", name: "ATR2600M", aperture_mm: null, focal_mm: null }
    attrezzatura({
      instruments: [
        { ...camera, pixel_from_sky_um: 3.8 },
        { ...camera, id: 6, name: "ASI2600MM", pixel_size_um: 3.76, pixel_from_sky_um: 3.8 },
      ],
    })
    await apriAttrezzatura()

    const camere = await screen.findByRole("list", { name: /camere/i })
    expect(within(camere).getByText(/ATR2600M/).closest("li")?.textContent).toMatch(
      /pixel 3,8 micron, ricavato dal cielo/,
    )
    const detto = within(camere).getByText(/ASI2600MM/).closest("li")?.textContent
    expect(detto).toMatch(/pixel 3,76 micron/)
    expect(detto).not.toMatch(/ricavato/)
  })

  it("un corredo dice quanto cielo inquadra", async () => {
    attrezzatura()
    await apriAttrezzatura()

    const corredi = await screen.findByRole("list", { name: /corredi/i })
    expect(corredi.textContent).toContain("0,85")
    expect(corredi.textContent).toMatch(/1,5/)
  })

  it("un corredo di cui non si sa quanto inquadra non scrive una scala", async () => {
    // La riga tace e dice perche': un numero preso dalla scheda sarebbe giusto sulla carta e
    // sbagliato nel cielo, e nessuno potrebbe accorgersene. Il caso non e' solo "non ha mai
    // ripreso": visto dal vivo, un corredo con otto pose **non ancora riconosciute** non ha una
    // scala, e dirgli "dopo la prima ripresa" sarebbe falso.
    attrezzatura({
      rigs: [
        {
          ...CORREDO,
          frames: 0,
          integration_s: 0,
          nights: 0,
          objects: [],
          scale_arcsec_px: null,
          width_deg: null,
          height_deg: null,
        },
      ],
    })
    await apriAttrezzatura()

    const corredi = await screen.findByRole("list", { name: /corredi/i })
    expect(corredi.textContent).toMatch(/quando l'app avra' riconosciuto/i)
    expect(corredi.textContent).not.toMatch(/arcosecondi/i)
  })

  it("scelgo la montatura di un corredo dalla sua scheda", async () => {
    attrezzatura(
      {},
      { "PUT /api/v1/gear/rigs/10/mount": { stato: 200, corpo: { id: 10, requeued: 120, run_started: true } } },
    )
    await apriAttrezzatura()
    const elenco = await screen.findByRole("list", { name: /corredi/i })
    fireEvent.click(within(elenco).getByRole("button", { name: /scegli la montatura/i }))
    fireEvent.change(screen.getByLabelText(/^montatura/i), { target: { value: "2" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.url).toContain("/api/v1/gear/rigs/10/mount")
    expect(scritture()[0]?.corpo).toEqual({ mount_id: 2 })
  })

  it("un corredo dice su che montatura sta, e la voce vuota torna ai file", async () => {
    attrezzatura(
      { rigs: [{ ...CORREDO, mount_id: 2 }] },
      { "PUT /api/v1/gear/rigs/10/mount": { stato: 200, corpo: { id: 10, requeued: 120, run_started: true } } },
    )
    await apriAttrezzatura()
    const elenco = await screen.findByRole("list", { name: /corredi/i })
    expect(elenco.textContent).toContain("sulla EQ6-R")
    fireEvent.click(within(elenco).getByRole("button", { name: /scegli la montatura/i }))
    fireEvent.change(screen.getByLabelText(/^montatura/i), { target: { value: "" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ mount_id: null })
  })

  it("senza montature da scegliere il corredo non offre il gesto", async () => {
    attrezzatura({ instruments: [OTTICA] })
    await apriAttrezzatura()
    const elenco = await screen.findByRole("list", { name: /corredi/i })
    expect(within(elenco).queryByRole("button", { name: /scegli la montatura/i })).toBeNull()
  })

  it("una montatura portata dalle pose ha le sue ore", async () => {
    attrezzatura({
      instruments: [OTTICA, { ...MONTATURA, frames: 120, integration_s: 36000, untimed: 0, nights: 7, no_hours: null }],
    })
    await apriAttrezzatura()
    const montature = await screen.findByRole("list", { name: /montature/i })
    expect(montature.textContent).not.toMatch(/nessun corredo la porta/i)
    expect(montature.textContent).toMatch(/10 h/)
  })

  it("una montatura che nessuna posa porta, in un archivio dove altre ce l'hanno, non dice zero", async () => {
    attrezzatura({ instruments: [OTTICA, { ...MONTATURA, frames: 0, integration_s: 0, untimed: 0, nights: 0 }] })
    await apriAttrezzatura()
    const montature = await screen.findByRole("list", { name: /montature/i })
    expect(montature.textContent).toMatch(/nessun corredo la porta ancora/i)
  })

  it("la montatura dice perche' non ha ore", async () => {
    attrezzatura()
    await apriAttrezzatura()

    const montature = await screen.findByRole("list", { name: /montature/i })
    expect(montature.textContent).toMatch(/nessun corredo la porta ancora/i)
    expect(montature.textContent).not.toMatch(/\b0 h\b/)
    expect(montature.textContent).toContain("20") // la scheda pero' si legge: regge 20 kg
  })

  it("a mani vuote dice cosa fare, non nessun risultato", async () => {
    attrezzatura({ instruments: [], rigs: [], filters: [] })
    await apriAttrezzatura()

    expect(await screen.findByText(/non so ancora con cosa riprendi/i)).toBeDefined()
    expect(screen.getByRole("link", { name: /aggiungi una cartella/i })).toBeDefined()
  })

  it("se l attrezzatura non si legge lo dice, invece di sembrare vuota", async () => {
    rispondi({
      ...STANOTTE,
      "/api/v1/gear": { stato: 500, corpo: { detail: "boom" } },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      ...SPINA,
    })
    await apriAttrezzatura()

    expect(await screen.findByText(/non sono riuscito a leggere l'attrezzatura/i)).toBeDefined()
  })
})

describe("i gesti sull attrezzatura", () => {
  /** Apre la scheda di un pezzo dalla sua riga: e' la strada dell'utente, che vede l'errore
   *  mentre guarda il pezzo e lo corregge li'. */
  async function apriLaScheda(genere: RegExp, nomeDelPezzo: RegExp) {
    const elenco = await screen.findByRole("list", { name: genere })
    const riga = within(elenco)
      .getAllByRole("listitem")
      .find((l) => nomeDelPezzo.test(l.textContent ?? ""))
    fireEvent.click(within(riga as HTMLElement).getByRole("button", { name: /correggi/i }))
  }

  it("correggo la scheda di un pezzo dalla pagina in cui lo guardo", async () => {
    attrezzatura(
      {},
      {
        "PATCH /api/v1/gear/instruments/1": { stato: 200, corpo: { id: 1, requeued: 0, run_started: false } },
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

    expect(screen.getByLabelText(/carico che regge/i)).toBeDefined()
    expect(screen.queryByLabelText(/apertura/i)).toBeNull()
  })

  it("cio' che scelgo in una scheda resta scelto", async () => {
    // Visto dal vivo: la tendina del colore tornava su "--" appena la si mollava, perche'
    // mostrava il valore **letto dai file** invece di quello appena scelto. I campi di testo non
    // lo facevano -- sono liberi -- quindi solo guidando l'app si vedeva.
    attrezzatura({
      instruments: [{ ...OTTICA, id: 4, kind: "camera", name: "ASI2600MM", camera_type: null }],
    })
    await apriAttrezzatura()
    await apriLaScheda(/camere/i, /ASI2600MM/)

    const colore = screen.getByLabelText(/colore/i)
    fireEvent.change(colore, { target: { value: "mono" } })

    expect((colore as HTMLSelectElement).value).toBe("mono")
  })

  it("unisco due grafie dello stesso pezzo, solo fra quelle che l'API offre", async () => {
    const altra = { ...OTTICA, id: 5, name: "TS130APO", mergeable_into: [1] }
    attrezzatura(
      { instruments: [{ ...OTTICA, mergeable_into: [5] }, altra, MONTATURA] },
      { "PATCH /api/v1/gear/instruments/1": { stato: 200, corpo: { id: 1, requeued: 3, run_started: true } } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/telescopi/i, /^TS 130 APO/)
    fireEvent.change(screen.getByLabelText(/lo stesso pezzo di/i), { target: { value: "5" } })
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
      { "PATCH /api/v1/gear/instruments/1": { stato: 200, corpo: { id: 1, requeued: 0, run_started: false } } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/telescopi/i, /^TS 130 APO/)
    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "Pippo" } })
    const unione = screen.getByLabelText(/lo stesso pezzo di/i)
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
    expect(screen.queryByLabelText(/lo stesso pezzo di/i)).toBeNull()
  })

  it("do un nome a un corredo", async () => {
    attrezzatura(
      {},
      { "PATCH /api/v1/gear/rigs/10": { stato: 200, corpo: { id: 10, requeued: 0, run_started: false } } },
    )
    await apriAttrezzatura()
    const elenco = await screen.findByRole("list", { name: /corredi/i })
    fireEvent.click(within(elenco).getByRole("button", { name: /dagli un nome/i }))
    fireEvent.change(screen.getByLabelText(/^nome/i), { target: { value: "Il piccolo" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.url).toContain("/api/v1/gear/rigs/10")
    expect(scritture()[0]?.corpo).toEqual({ name: "Il piccolo" })
  })

  it("correggo la marca di un filtro", async () => {
    attrezzatura(
      {},
      { "PATCH /api/v1/gear/filters/3": { stato: 200, corpo: { id: 3, requeued: 0, run_started: false } } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/filtri/i, /^Ha/)
    fireEvent.change(screen.getByLabelText(/marca/i), { target: { value: "Baader" } })
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.url).toContain("/api/v1/gear/filters/3")
    expect(scritture()[0]?.corpo).toEqual({ brand: "Baader" })
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
      { "PATCH /api/v1/gear/filters/3": { stato: 200, corpo: { id: 3, requeued: 60, run_started: true } } },
    )
    await apriAttrezzatura()
    await apriLaScheda(/filtri/i, /^Ha/)
    const tendina = screen.getByLabelText(/lo stesso filtro di/i)
    expect(within(tendina).queryByRole("option", { name: "H" })).toBeNull()
    fireEvent.change(tendina, { target: { value: "4" } })
    expect(screen.queryByLabelText(/marca/i)).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: /salva/i }))
    await waitFor(() => expect(scritture()).toHaveLength(1))
    expect(scritture()[0]?.corpo).toEqual({ merge_into: 4 })
  })
})
