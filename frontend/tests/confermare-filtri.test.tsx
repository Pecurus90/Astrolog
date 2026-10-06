// @vitest-environment jsdom
/**
 * La sezione **filtri** di Da confermare: la prima che si risponde davvero.
 *
 * Due strade, e si sa sempre in quale sei (Marco, 14/9/2026):
 *
 * - **dal catalogo**: si cerca scrivendo fra i 38 modelli in commercio; marca, nome e banda si
 *   compilano e restano **fissi**, perche' sono il modello -- correggerli farebbe nascere un
 *   doppione travestito da voce ufficiale. La risposta porta `catalog_id`.
 * - **a mano**: chi ha un filtro che il catalogo non conosce scrive nome e banda; `catalog_id`
 *   resta fuori, ed e' esattamente cio' che lo schema prevede ("NULL se nome libero").
 *
 * Il filtro **esiste gia'** in tutti e due i casi: nasce dagli header quando la scansione lo
 * incontra, con banda `UNKNOWN`. La tendina non lo crea, gli da' un'identita'.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, STANOTTE, chiamate, disegna, impostazioni, pulisci, riga, rispondi, scritture, vaiASezione } from "./banco"

afterEach(pulisci)

const MODELLI = [
  { id: "antlia-alp-t-3nm", brand: "Antlia", name: "ALP-T 3nm", passband: "DUO_HAOIII" },
  { id: "antlia-alp-t-5nm", brand: "Antlia", name: "ALP-T 5nm", passband: "DUO_HAOIII" },
  { id: "optolong-l-extreme", brand: "Optolong", name: "L-eXtreme", passband: "DUO_HAOIII" },
]

/** Due filtri che l'app non riconosce, il piu' usato in cima: l'ordine e' quello che manda l'API,
 *  e la pagina non lo tocca. E uno dei tuoi, fra cui scegliere. */
const PAGINA = {
  seen: { instruments: 0, rigs: 0, objects: 0 },
  to_confirm: 2,
  filters: [
    { id: 7, name: "H", brand: null, model: null, catalog_id: null, passband: "UNKNOWN", is_none: false, bands: [], frames: 120 },
    { id: 8, name: "Filter 3", brand: null, model: null, catalog_id: null, passband: "UNKNOWN", is_none: false, bands: [], frames: 40 },
  ],
  filter_choices: [{ id: 9, name: "Antlia ALP-T 3nm", passband: "DUO_HAOIII" }],
  instruments: [],
  rigs: [],
  objects: [],
  mosaics: [],
  unclear: [],
  gear: [],
}

function aperta(pagina = PAGINA) {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: MODELLI } },
    "/api/v1/review/apply": {
      stato: 200,
      corpo: { changed: 1, confirmed: 0, requeued: 120, run_started: true },
    },
    "/api/v1/review": { stato: 200, corpo: pagina },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
}

/** Da confermare, sulla sezione dei filtri. La navigazione e la ricerca della riga vivono nel
 *  banco: le fanno tutte le sezioni, e scriverle qui sarebbe lo stesso pezzo in undici case. */
const vaiAConfermare = () => vaiASezione(/filtri/i)

describe("Da confermare -- i filtri", () => {
  it("l ordine e quello dell API, e la pagina non lo tocca", async () => {
    // In cima chi chiede una risposta, poi i piu' usati: l'ordine e' una decisione del backend
    // (`review.py` lo dichiara). Se la pagina riordinasse, sarebbero due case per lo stesso fatto.
    aperta()
    const sezione = await vaiAConfermare()
    const righe = within(sezione).getAllByRole("listitem")
    expect(righe.at(0)?.textContent).toMatch(/^H/)
    expect(righe.at(1)?.textContent).toMatch(/^Filter 3/)
  })

  it("scrivendo nella tendina l elenco si restringe", async () => {
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    expect(await within(suHa).findByRole("button", { name: /ALP-T 3nm/ })).toBeDefined()
    expect(within(suHa).queryByRole("button", { name: /L-eXtreme/ })).toBeNull()
  })

  it("scelto un modello dal catalogo, marca nome e banda sono FISSI", async () => {
    // Sono il modello: se si potessero correggere nascerebbe un doppione che si spaccia per voce
    // ufficiale, e `catalog_id` direbbe una cosa che il nome smentisce.
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    fireEvent.click(await within(suHa).findByRole("button", { name: /Antlia ALP-T 3nm/ }))
    expect(within(suHa).getByLabelText(/^nome/i)).toHaveProperty("readOnly", true)
  })

  it("e la risposta porta il catalog_id del modello scelto", async () => {
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    fireEvent.click(await within(suHa).findByRole("button", { name: /Antlia ALP-T 3nm/ }))
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.includes("/api/v1/review/apply"))
      expect(scritta).toBeDefined()
      expect(scritta?.corpo).toMatchObject({
        filters: [{ id: 7, catalog_id: "antlia-alp-t-3nm" }],
      })
    })
  })

  it("chi in catalogo non c e scrive nome e banda, e catalog_id resta fuori", async () => {
    // La seconda strada, e non e' un ripiego: e' la sola per chi ha un filtro che il catalogo
    // non conosce. Lo schema la prevede -- `catalog_id` NULL se nome libero.
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.click(within(suHa).getByRole("button", { name: /non e' in elenco/i }))
    fireEvent.change(within(suHa).getByLabelText(/^nome/i), { target: { value: "Il mio Ha" } })
    fireEvent.change(within(suHa).getByLabelText(/banda/i), { target: { value: "HA" } })
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.includes("/api/v1/review/apply"))
      const corpo = scritta?.corpo as { filters: Record<string, unknown>[] } | undefined
      const filtro = corpo?.filters[0]
      expect(filtro).toMatchObject({ id: 7, name: "Il mio Ha" })
      expect(filtro?.catalog_id).toBeUndefined()
    })
  })

  it("la larghezza in nanometri e facoltativa: si risponde anche senza", async () => {
    // Un anti inquinamento luminoso non ha una larghezza, e pretenderla bloccherebbe la risposta
    // su una cosa che non esiste. Lo schema la lascia nulla apposta.
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.click(within(suHa).getByRole("button", { name: /non e' in elenco/i }))
    fireEvent.change(within(suHa).getByLabelText(/^nome/i), { target: { value: "L-Pro" } })
    fireEvent.change(within(suHa).getByLabelText(/banda/i), { target: { value: "L" } })
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    await waitFor(() =>
      expect(scritture().some((s) => s.url.includes("/api/v1/review/apply"))).toBe(true),
    )
  })

  it("l elenco dei modelli si apre scrivendo, non prima", async () => {
    // Trovato collaudando sull'archivio vero il 14/9/2026: con otto filtri da rispondere la
    // pagina disegnava **304 bottoni** tutti insieme -- 8 x 38 modelli -- e il renderer del
    // browser e' andato in timeout. Il banco non lo mostrava: tre modelli finti e due filtri.
    // Una tendina e' una tendina: si apre quando la si usa.
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    expect(within(suHa).queryByRole("button", { name: /ALP-T 3nm/ })).toBeNull()
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    expect(await within(suHa).findByRole("button", { name: /ALP-T 3nm/ })).toBeDefined()
  })

  it("il nome del modello non ripete la marca", async () => {
    // Otto modelli su 38 portano gia' la marca dentro il nome ("Antlia Quad Band"), e comporre
    // marca + nome dava "Antlia Antlia Quad Band". Misurato sul vocabolario vero.
    rispondi({
      ...STANOTTE,
      "/api/v1/vocab/filter-models": {
        stato: 200,
        corpo: {
          items: [
            { id: "antlia-quad-band", brand: "Antlia", name: "Antlia Quad Band", passband: "MULTI_NB" },
          ],
        },
      },
      "/api/v1/review": { stato: 200, corpo: PAGINA },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "quad" },
    })
    const voce = await within(suHa).findByRole("button", { name: /Quad Band/ })
    expect(voce.textContent).toBe("Antlia Quad Band")
  })

  it("la voce vuota toglie la risposta, invece di mandarne una vuota", async () => {
    aperta()
    const sezione = await vaiAConfermare()
    const tendina = within(riga(sezione, "H")).getByLabelText(/uno dei miei filtri: H$/i)
    fireEvent.change(tendina, { target: { value: "9" } })
    fireEvent.change(tendina, { target: { value: "" } })
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", true)
  })

  it("passare a mano toglie uno dei miei, anche senza scrivere niente", async () => {
    // La tendina a quel punto e' nascosta: un'unione rimasta in mano partirebbe senza che si veda.
    aperta()
    const sezione = await vaiAConfermare()
    const suH = riga(sezione, "H")
    fireEvent.change(within(suH).getByLabelText(/uno dei miei filtri: H$/i), { target: { value: "9" } })
    fireEvent.click(within(suH).getByRole("button", { name: /non e' in elenco/i }))
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", true)
  })

  it("scelto uno dei miei e poi scritto a mano, parte il nome scritto e non l'unione", async () => {
    // Sono due strade e non si sommano: col nome dentro la stessa risposta dell'unione, il
    // backend unirebbe e il nome scritto sparirebbe senza un messaggio.
    aperta()
    const sezione = await vaiAConfermare()
    const suH = riga(sezione, "H")
    fireEvent.change(within(suH).getByLabelText(/uno dei miei filtri: H$/i), { target: { value: "9" } })
    fireEvent.click(within(suH).getByRole("button", { name: /non e' in elenco/i }))
    fireEvent.change(within(suH).getByLabelText(/^nome/i), { target: { value: "Il mio H" } })
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.includes("/api/v1/review/apply"))
      expect((scritta?.corpo as { filters: unknown[] } | undefined)?.filters).toEqual([
        { id: 7, name: "Il mio H" },
      ])
    })
  })

  it("e' uno dei miei: la risposta e' l'unione, e si puo' tornare indietro", async () => {
    // La grafia dell'header diventa per sempre quel filtro: e' l'unione, che impara la regola.
    aperta()
    const sezione = await vaiAConfermare()
    const suH = riga(sezione, "H")
    const tendina = within(suH).getByLabelText(/uno dei miei filtri: H$/i)
    fireEvent.change(tendina, { target: { value: "9" } })
    fireEvent.change(tendina, { target: { value: "" } })
    fireEvent.change(tendina, { target: { value: "9" } })
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.includes("/api/v1/review/apply"))
      expect((scritta?.corpo as { filters: unknown[] } | undefined)?.filters).toEqual([
        { id: 7, merge_into: 9 },
      ])
    })
  })

  it("se l elenco dei modelli non risponde, lo dice invece di sembrare vuoto", async () => {
    // **La bugia piu' costosa di questa pagina**, portata da `old/`: una coda che non si e'
    // potuta leggere non e' una coda vuota. Con la tendina muta l'utente cerca il suo filtro,
    // non lo trova, e conclude che in catalogo non c'e' -- scrivendolo a mano per sempre.
    aperta()
    rispondi({
      ...STANOTTE,
      "/api/v1/vocab/filter-models": { stato: 500, corpo: { detail: { code: "rotto" } } },
      "/api/v1/review": { stato: 200, corpo: PAGINA },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    await vaiAConfermare()
    expect(await screen.findByRole("alert")).toBeDefined()
  })

  it("se Applica fallisce, lo dice", async () => {
    rispondi({
      ...STANOTTE,
      "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: MODELLI } },
      "/api/v1/review/apply": { stato: 500, corpo: { detail: { code: "rotto" } } },
      "/api/v1/review": { stato: 200, corpo: PAGINA },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    fireEvent.click(await within(suHa).findByRole("button", { name: /Antlia ALP-T 3nm/ }))
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    expect(await screen.findByRole("alert")).toBeDefined()
  })

  it("una sezione senza domande non si vede", async () => {
    // Scelta di Marco: una pagina di undici titoli vuoti sembra rotta, e il giorno che hai
    // finito vuoi vederlo.
    aperta({ ...PAGINA, filters: [], to_confirm: 0 })
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
    await screen.findByRole("heading", { name: /da confermare/i })
    expect(screen.queryByRole("region", { name: /filtri/i })).toBeNull()
  })

  it("Applica manda seen: si conferma solo cio che era li quando hai letto", async () => {
    // La riga che evita di confermare cio' che non hai visto: una voce arrivata dopo, da una
    // scansione finita nel frattempo, resta nuova.
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    fireEvent.click(await within(suHa).findByRole("button", { name: /Antlia ALP-T 3nm/ }))
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.includes("/api/v1/review/apply"))
      expect(scritta?.corpo).toMatchObject({
        seen: { instruments: 0, rigs: 0, objects: 0 },
      })
    })
  })

  it("dopo Applica la pagina si rilegge e l accumulatore si svuota", async () => {
    // L'elenco di prima direbbe cose non piu' vere: la risposta rifa' il lavoro sulle pose
    // toccate. E le risposte gia' mandate non restano in mano.
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    fireEvent.click(await within(suHa).findByRole("button", { name: /Antlia ALP-T 3nm/ }))
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    await screen.findByRole("status")
    // la pagina si e' riletta: due chiamate a /review, quella d'apertura e quella dopo
    await waitFor(() =>
      expect(chiamate().filter((u) => /\/api\/v1\/review($|\?)/.test(u)).length).toBeGreaterThan(1),
    )
    // e l'Applica torna spento, perche' non c'e' piu' niente in mano
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", true)
  })

  it("un clic sbagliato si corregge: si torna a scegliere", async () => {
    // Prima, scelto un modello, sparivano sia la ricerca sia "non e' in elenco": l'unico modo di
    // cambiare idea era ricaricare la pagina. Una scelta non e' un vicolo cieco finche' non si
    // preme Applica.
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    fireEvent.click(await within(suHa).findByRole("button", { name: /Antlia ALP-T 3nm/ }))
    fireEvent.click(within(suHa).getByRole("button", { name: /scegli un altro modello/i }))
    expect(within(suHa).getByLabelText(/cerca fra i modelli per H$/i)).toBeDefined()
    expect(within(suHa).getByRole("button", { name: /non e' in elenco/i })).toBeDefined()
  })

  it("le risposte si accumulano e partono con un solo Applica", async () => {
    // La scelta di Marco: una sola attesa e un solo ricalcolo, invece di uno per risposta.
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    fireEvent.click(await within(suHa).findByRole("button", { name: /Antlia ALP-T 3nm/ }))
    // Prima di Applica non e' partita nessuna scrittura: le risposte stanno nella pagina.
    expect(scritture().some((s) => s.url.includes("/apply"))).toBe(false)
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    await waitFor(() =>
      expect(chiamate().filter((u) => u.includes("/api/v1/review/apply")).length).toBe(1),
    )
  })

  it("dopo Applica la pagina dice cosa e cambiato", async () => {
    // La ricevuta porta numeri veri (`changed`, `requeued`): un "fatto!" muto lascerebbe
    // l'utente a chiedersi se e' successo qualcosa.
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    fireEvent.click(await within(suHa).findByRole("button", { name: /Antlia ALP-T 3nm/ }))
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    // Si cerca la RICEVUTA, non il numero: "120 frame" e' gia' a schermo nella riga del filtro,
    // quindi cercarlo da solo passava anche togliendo la ricevuta -- provato dal revisore.
    const ricevuta = await screen.findByRole("status")
    expect(ricevuta.textContent).toContain("120")
    expect(ricevuta.textContent).toMatch(/rimessi in coda/i)
  })
})
