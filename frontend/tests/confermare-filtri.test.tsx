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

function aperta(pagina: unknown = PAGINA) {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: MODELLI } },
    "/api/v1/review/apply": {
      stato: 200,
      corpo: { changed: 1, requeued: 120, run_started: true },
    },
    "/api/v1/review": { stato: 200, corpo: pagina },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
}

/** Da confermare, sulla sezione dei filtri. La navigazione e la ricerca della riga vivono nel
 *  banco: le fanno tutte le sezioni, e scriverle qui sarebbe lo stesso pezzo in undici case. */
const vaiAConfermare = () => vaiASezione(/filtri/i)

/** Sceglie uno dei tre modi di rispondere: sono esclusivi, e si vede solo quello scelto. */
const modo = (dove: HTMLElement, quale: RegExp) =>
  fireEvent.click(within(dove).getByRole("radio", { name: quale }))

describe("Da confermare -- i filtri", () => {
  it("l ordine e quello dell API, e la pagina non lo tocca", async () => {
    // In cima chi chiede una risposta, poi i piu' usati: l'ordine e' una decisione del backend
    // (`review.py` lo dichiara). Se la pagina riordinasse, sarebbero due case per lo stesso fatto.
    aperta()
    const sezione = await vaiAConfermare()
    const righe = [...sezione.querySelectorAll(".as-domanda, .as-domanda-riga")]
    expect(righe.at(0)?.textContent).toMatch(/^H/)
    expect(righe.at(1)?.textContent).toMatch(/^Filter 3/)
    // chiusa e senza risposta, la riga dice fra cosa si sceglie
    expect(righe.at(1)?.querySelector(".as-domanda-riga__breve")?.textContent).toBe(
      "Filtro esistente · Modello da catalogo · Nuovo filtro",
    )
  })

  it("scrivendo nella tendina l elenco si restringe", async () => {
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    expect(await within(suHa).findByRole("option", { name: /ALP-T 3nm/ })).toBeDefined()
    expect(within(suHa).queryByRole("option", { name: /L-eXtreme/ })).toBeNull()
  })

  it("scelto un modello dal catalogo, e' la voce scelta dell'elenco: il suo nome non si scrive", async () => {
    // E' il modello: se si potesse correggere nascerebbe un doppione che si spaccia per voce
    // ufficiale, e `catalog_id` direbbe una cosa che il nome smentisce.
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    const voce = await within(suHa).findByRole("option", { name: /Antlia ALP-T 3nm/ })
    expect(voce.getAttribute("aria-selected")).toBe("false")
    fireEvent.click(voce)
    expect(within(suHa).getByRole("option", { name: /Antlia ALP-T 3nm/ }).getAttribute("aria-selected")).toBe("true")
    expect(within(suHa).queryByLabelText(/^nome/i)).toBeNull()
  })

  it("i tre modi sono pillole, se ne vede uno alla volta, e cambiarlo toglie la risposta", async () => {
    aperta()
    const sezione = await vaiAConfermare()
    const suH = riga(sezione, "H")
    const modi = within(suH).getByRole("group", { name: "Come rispondere per H" })
    expect(modi.className).toBe("as-scelta-fissa")
    expect(within(modi).getAllByRole("radio").map((r) => r.closest("label")?.textContent)).toEqual([
      "Filtro esistente",
      "Modello da catalogo",
      "Nuovo filtro",
    ])
    // si parte dal catalogo: e' la strada di quasi tutti
    expect(within(modi).getByRole("radio", { name: "Modello da catalogo" })).toHaveProperty("checked", true)
    expect(within(suH).getByLabelText(/cerca fra i modelli per H$/i).closest(".as-domanda-modo")).not.toBeNull()
    expect(within(suH).queryByLabelText(/filtro esistente: H$/i)).toBeNull()

    modo(suH, /^filtro esistente$/i)
    expect(within(suH).queryByLabelText(/cerca fra i modelli/i)).toBeNull()
    fireEvent.change(within(suH).getByLabelText(/filtro esistente: H$/i), { target: { value: "9" } })
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", false)
    // un'altra strada non si somma a quella di prima
    modo(suH, /^modello da catalogo$/i)
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", true)
  })

  it("una ricerca che non trova niente lo dice, e dice dove andare", async () => {
    aperta()
    const sezione = await vaiAConfermare()
    const suH = riga(sezione, "H")
    fireEvent.change(within(suH).getByLabelText(/cerca fra i modelli per H$/i), { target: { value: "baader 7nm" } })
    const niente = within(suH).getByText(/nessun modello per \u00abbaader 7nm\u00bb/i)
    expect(niente.className).toBe("as-comparsa as-comparsa--niente")
    expect(niente.textContent).toMatch(/nuovo filtro/i)
    expect(within(suH).queryByRole("listbox")).toBeNull()
  })

  it("l'elenco dei modelli e' il mattone del foglio, e si sceglie anche da tastiera", async () => {
    aperta()
    const sezione = await vaiAConfermare()
    const suH = riga(sezione, "H")
    fireEvent.change(within(suH).getByLabelText(/cerca fra i modelli per H$/i), { target: { value: "alp" } })
    const elenco = await within(suH).findByRole("listbox", { name: "Modelli trovati" })
    expect(elenco.className).toBe("as-comparsa")
    const voce = within(elenco).getAllByRole("option")[0]!
    expect(voce.className).toBe("as-comparsa__voce")
    expect(voce.querySelector(".as-comparsa__marca")?.textContent).toBe("Antlia")
    expect(voce.tabIndex).toBe(0)
    fireEvent.keyDown(voce, { key: "Enter" })
    expect(within(elenco).getAllByRole("option")[0]?.getAttribute("aria-selected")).toBe("true")
  })

  it("e la risposta porta il catalog_id del modello scelto", async () => {
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    fireEvent.click(await within(suHa).findByRole("option", { name: /Antlia ALP-T 3nm/ }))
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
    modo(suHa, /^nuovo filtro$/i)
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

  it("un filtro scritto a mano si rivede com'e' dopo che la sezione si e' chiusa e riaperta", async () => {
    // Una sezione chiusa si smonta: la strada "a mano" si rilegge dalla risposta in mano, o alla
    // riapertura si vedrebbe la tendina vuota mentre Applica manda il nome scritto.
    aperta({
      ...PAGINA,
      filters: PAGINA.filters.slice(0, 1),
      typeless: [{ key: "D:/Astro/dark", frames: 120, answer: null }],
    })
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    modo(suHa, /^nuovo filtro$/i)
    fireEvent.change(within(suHa).getByLabelText(/^nome/i), { target: { value: "Il mio Ha" } })
    fireEvent.click(screen.getByRole("button", { name: "Rispondi: D:/Astro/dark" }))
    fireEvent.click(screen.getByRole("button", { name: /^Riapri: Filtri/ }))
    const riaperta = riga(screen.getByRole("region", { name: /filtri/i }), "H")
    expect(within(riaperta).getByLabelText(/^nome/i)).toHaveProperty("value", "Il mio Ha")
    expect(within(riaperta).queryByLabelText(/filtro esistente: H$/i)).toBeNull()
  })

  it("la larghezza in nanometri e facoltativa: si risponde anche senza", async () => {
    // Un anti inquinamento luminoso non ha una larghezza, e pretenderla bloccherebbe la risposta
    // su una cosa che non esiste. Lo schema la lascia nulla apposta.
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    modo(suHa, /^nuovo filtro$/i)
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
    expect(within(suHa).queryByRole("option", { name: /ALP-T 3nm/ })).toBeNull()
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    expect(await within(suHa).findByRole("option", { name: /ALP-T 3nm/ })).toBeDefined()
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
    const voce = await within(suHa).findByRole("option", { name: /Quad Band/ })
    expect(voce.textContent).toBe("Antlia Quad Band")
  })

  it("la voce vuota toglie la risposta, invece di mandarne una vuota", async () => {
    aperta()
    const sezione = await vaiAConfermare()
    const suH = riga(sezione, "H")
    modo(suH, /^filtro esistente$/i)
    const tendina = within(suH).getByLabelText(/filtro esistente: H$/i)
    fireEvent.change(tendina, { target: { value: "9" } })
    fireEvent.change(tendina, { target: { value: "" } })
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", true)
  })

  it("passare a mano toglie uno dei miei, anche senza scrivere niente", async () => {
    // La tendina a quel punto e' nascosta: un'unione rimasta in mano partirebbe senza che si veda.
    aperta()
    const sezione = await vaiAConfermare()
    const suH = riga(sezione, "H")
    modo(suH, /^filtro esistente$/i)
    fireEvent.change(within(suH).getByLabelText(/filtro esistente: H$/i), { target: { value: "9" } })
    modo(suH, /^nuovo filtro$/i)
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", true)
  })

  it("scelto uno dei miei e poi scritto a mano, parte il nome scritto e non l'unione", async () => {
    // Sono due strade e non si sommano: col nome dentro la stessa risposta dell'unione, il
    // backend unirebbe e il nome scritto sparirebbe senza un messaggio.
    aperta()
    const sezione = await vaiAConfermare()
    const suH = riga(sezione, "H")
    modo(suH, /^filtro esistente$/i)
    fireEvent.change(within(suH).getByLabelText(/filtro esistente: H$/i), { target: { value: "9" } })
    modo(suH, /^nuovo filtro$/i)
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
    modo(suH, /^filtro esistente$/i)
    const tendina = within(suH).getByLabelText(/filtro esistente: H$/i)
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
    fireEvent.click(await within(suHa).findByRole("option", { name: /Antlia ALP-T 3nm/ }))
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    expect(await screen.findByRole("alert")).toBeDefined()
  })

  it("una sezione senza domande non si vede", async () => {
    // Scelta di Marco: una pagina di undici titoli vuoti sembra rotta, e il giorno che hai
    // finito vuoi vederlo.
    aperta({ ...PAGINA, filters: [], to_confirm: 0 })
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
    await waitFor(() => expect(document.querySelector(".as-conferma__conta")?.textContent).toMatch(/^\d+ da confermare$/))
    expect(screen.queryByRole("region", { name: /filtri/i })).toBeNull()
  })

  it("Applica manda solo le risposte, senza seen", async () => {
    // Applica scrive solo le risposte (ADR 0014): il server rifiuta un campo che non conosce.
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    fireEvent.click(await within(suHa).findByRole("option", { name: /Antlia ALP-T 3nm/ }))
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    await waitFor(() => {
      const scritta = scritture().find((s) => s.url.includes("/api/v1/review/apply"))
      expect(scritta?.corpo).toBeDefined()
      expect(scritta?.corpo).not.toHaveProperty("seen")
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
    fireEvent.click(await within(suHa).findByRole("option", { name: /Antlia ALP-T 3nm/ }))
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    await screen.findByRole("status")
    // la pagina si e' riletta: due chiamate a /review, quella d'apertura e quella dopo
    await waitFor(() =>
      expect(chiamate().filter((u) => /\/api\/v1\/review($|\?)/.test(u)).length).toBeGreaterThan(1),
    )
    // e l'Applica torna spento, perche' non c'e' piu' niente in mano
    expect(screen.getByRole("button", { name: /applica/i })).toHaveProperty("disabled", true)
  })

  it("un clic sbagliato si corregge: si sceglie un altro modello, o un altro modo", async () => {
    // Una scelta non e' un vicolo cieco finche' non si preme Applica.
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    fireEvent.click(await within(suHa).findByRole("option", { name: /Antlia ALP-T 3nm/ }))
    fireEvent.click(within(suHa).getByRole("option", { name: /Antlia ALP-T 5nm/ }))
    const scelte = within(suHa).getAllByRole("option").filter((o) => o.getAttribute("aria-selected") === "true")
    expect(scelte.map((o) => o.textContent)).toEqual(["Antlia ALP-T 5nm"])
    // una ricerca che non lo comprende non lo toglie dalla vista: sta per partire con Applica
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), { target: { value: "zzz" } })
    expect(within(suHa).getByRole("option", { name: /Antlia ALP-T 5nm/ }).getAttribute("aria-selected")).toBe("true")
    expect(within(suHa).getByText(/nessun modello per/i)).toBeDefined()
    expect(within(suHa).getByRole("radio", { name: /^nuovo filtro$/i })).toBeDefined()
  })

  it("le risposte si accumulano e partono con un solo Applica", async () => {
    // La scelta di Marco: una sola attesa e un solo ricalcolo, invece di uno per risposta.
    aperta()
    const sezione = await vaiAConfermare()
    const suHa = riga(sezione, "H")
    fireEvent.change(within(suHa).getByLabelText(/cerca fra i modelli per H$/i), {
      target: { value: "alp" },
    })
    fireEvent.click(await within(suHa).findByRole("option", { name: /Antlia ALP-T 3nm/ }))
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
    fireEvent.click(await within(suHa).findByRole("option", { name: /Antlia ALP-T 3nm/ }))
    fireEvent.click(screen.getByRole("button", { name: /applica/i }))
    // Si cerca la RICEVUTA, non il numero: "120 frame" e' gia' a schermo nella riga del filtro,
    // quindi cercarlo da solo passava anche togliendo la ricevuta -- provato dal revisore.
    const ricevuta = await screen.findByRole("status")
    expect(ricevuta.textContent).toContain("120")
    expect(ricevuta.textContent).toMatch(/da rielaborare/i)
  })
})
