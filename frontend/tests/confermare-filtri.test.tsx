// @vitest-environment jsdom
/**
 * La sezione **filtri** di Da confermare: la prima che si risponde davvero.
 *
 * Tre strade, e si sa sempre in quale sei (Marco, 14/9/2026; tavola v82, 190-199):
 *
 * - **filtro esistente**: uno dei tuoi, scelto fra le pillole; la grafia dell'header diventa quello.
 * - **dal catalogo**: si cerca scrivendo fra i modelli in commercio; marca, nome e banda **non si
 *   scrivono**, perche' sono il modello -- correggerli farebbe nascere un doppione travestito da
 *   voce ufficiale. La risposta porta `catalog_id`.
 * - **nuovo filtro**: nome, una o piu' bande, la larghezza facoltativa; `catalog_id` resta fuori.
 *   Parte solo intero: un filtro a meta' non e' una modifica.
 *
 * Il filtro **esiste gia'**: nasce dagli header con banda `UNKNOWN`. Qui gli si da' un'identita'.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  STANOTTE,
  cartellaSenzaTipo,
  chiamate,
  daConfermare,
  disegna,
  domande,
  filtroIgnoto,
  impostazioni,
  parti,
  pulisci,
  riga,
  rispondi,
  scelta,
  scelto,
  scritture,
  spento,
  vai,
  vaiASezione,
  voci,
} from "./banco"

afterEach(pulisci)

const MODELLI = [
  { id: "antlia-alp-t-3nm", brand: "Antlia", name: "ALP-T 3nm", passband: "DUO_HAOIII" },
  { id: "antlia-alp-t-5nm", brand: "Antlia", name: "ALP-T 5nm", passband: "DUO_HAOIII" },
  { id: "optolong-l-extreme", brand: "Optolong", name: "L-eXtreme", passband: "DUO_HAOIII" },
]

/** Due filtri che l'app non riconosce, il piu' usato in cima: l'ordine e' quello che manda l'API,
 *  e la pagina non lo tocca. E uno dei tuoi, fra cui scegliere. */
const PAGINA = daConfermare({
  to_confirm: 2,
  filters: [filtroIgnoto({ id: 7, name: "H", frames: 120 }), filtroIgnoto({ id: 8, name: "Filter 3", frames: 40 })],
  filter_choices: [{ id: 9, name: "Antlia ALP-T 3nm", passband: "DUO_HAOIII" }],
})

function aperta(pagina: unknown = PAGINA, modelli: unknown = { stato: 200, corpo: { items: MODELLI } }) {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": modelli as { stato: number; corpo: unknown },
    "/api/v1/review/apply": {
      stato: 200,
      corpo: { changed: 1, requeued: 120, run_started: true },
    },
    "/api/v1/review": { stato: 200, corpo: pagina },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
}

/** Da confermare, sulla sezione dei filtri. La navigazione e la ricerca della domanda vivono nel
 *  banco: le fanno tutte le sezioni. */
const vaiAConfermare = () => vaiASezione(/^filtri$/i)
const suH = async () => riga(await vaiAConfermare(), "H")

/** Sceglie una delle tre strade: sono esclusive, e si vede solo quella scelta. */
const modo = (dove: HTMLElement, quale: string) => fireEvent.click(scelta(dove, quale))
const cerca = (dove: HTMLElement, testo: string) =>
  fireEvent.change(within(dove).getByLabelText("Cerca fra i modelli per H"), { target: { value: testo } })
const applica = () => screen.getByRole("button", { name: /applica/i })
const applicaSpento = () => expect(applica().getAttribute("aria-disabled")).toBe("true")
const applicaAcceso = () => expect(applica().getAttribute("aria-disabled")).toBeNull()

async function filtriMandati() {
  fireEvent.click(applica())
  let corpo: { filters: unknown[] } | undefined
  await waitFor(() => {
    corpo = scritture().find((s) => s.url.includes("/api/v1/review/apply"))?.corpo as typeof corpo
    expect(corpo).toBeDefined()
  })
  return corpo?.filters
}

describe("Da confermare -- i filtri", () => {
  it("l ordine e quello dell API, e la pagina non lo tocca", async () => {
    // In cima chi chiede una risposta, poi i piu' usati: l'ordine e' una decisione del backend
    // (`review.py` lo dichiara). Se la pagina riordinasse, sarebbero due case per lo stesso fatto.
    aperta()
    const righe = domande(await vaiAConfermare())
    expect(righe.at(0)?.textContent).toMatch(/^H/)
    expect(righe.at(1)?.textContent).toMatch(/^Filter 3/)
    // chiusa e senza risposta, la riga dice fra cosa si sceglie
    expect(righe.at(1)?.querySelector(".al-conf__blocco-9")?.textContent).toBe(
      "Filtro esistente · Modello da catalogo · Nuovo filtro",
    )
  })

  it("scrivendo nella ricerca l elenco si restringe", async () => {
    aperta()
    const h = await suH()
    cerca(h, "alp")
    expect(await within(h).findByRole("option", { name: /ALP-T 3nm/ })).toBeDefined()
    expect(within(h).queryByRole("option", { name: /L-eXtreme/ })).toBeNull()
  })

  it("la ricerca cerca ogni parola scritta, in marca e nome", async () => {
    aperta()
    const h = await suH()
    cerca(h, "5nm antlia")
    expect(within(h).getAllByRole("option").map((o) => o.querySelector(".al-conf__blocco-14")?.textContent)).toEqual(["ALP-T 5nm"])
  })

  it("scelto un modello dal catalogo, e' la voce scelta dell'elenco: il suo nome non si scrive", async () => {
    // E' il modello: se si potesse correggere nascerebbe un doppione che si spaccia per voce
    // ufficiale, e `catalog_id` direbbe una cosa che il nome smentisce.
    aperta()
    const h = await suH()
    cerca(h, "alp")
    const voce = await within(h).findByRole("option", { name: /ALP-T 3nm/ })
    expect(voce.getAttribute("aria-selected")).toBe("false")
    fireEvent.click(voce)
    expect(within(h).getByRole("option", { name: /ALP-T 3nm/ }).getAttribute("aria-selected")).toBe("true")
    expect(within(h).queryByLabelText("Nome")).toBeNull()
  })

  it("le tre strade sono pillole, se ne vede una alla volta, e la risposta e' quella della strada scelta", async () => {
    aperta()
    const h = await suH()
    const modi = within(h).getByRole("radiogroup", { name: "Come rispondere per H" })
    expect(modi.className).toBe("al-scelta al-scelta--risposta")
    // si parte dal catalogo: e' la strada di quasi tutti
    expect(voci(modi)).toEqual(["Filtro esistente", "[x] Modello da catalogo", "Nuovo filtro"])
    expect(within(h).getByLabelText("Cerca fra i modelli per H")).toBeDefined()
    expect(within(h).queryByRole("radiogroup", { name: "Filtro esistente" })).toBeNull()

    modo(h, "Filtro esistente")
    expect(within(h).queryByLabelText(/cerca fra i modelli/i)).toBeNull()
    // i propri filtri si scelgono fra pillole, sotto
    const miei = within(h).getByRole("radiogroup", { name: "Filtro esistente" })
    expect(voci(miei)).toEqual(["Antlia ALP-T 3nm"])
    fireEvent.click(scelta(miei, "Antlia ALP-T 3nm"))
    applicaAcceso()
    // un'altra strada non si somma a quella di prima
    modo(h, "Modello da catalogo")
    applicaSpento()
    // e la strada di prima, ripresa, ha ancora la sua scelta
    modo(h, "Filtro esistente")
    expect(scelto(scelta(h, "Antlia ALP-T 3nm"))).toBe(true)
    expect(await filtriMandati()).toEqual([{ id: 7, merge_into: 9 }])
  })

  it("una ricerca che non trova niente lo dice, e dice dove andare", async () => {
    aperta()
    const h = await suH()
    cerca(h, "baader 7nm")
    const niente = within(h).getByText(/nessun modello per \u00abbaader 7nm\u00bb/i)
    expect(niente.className).toBe("al-conf__testo-17")
    expect(niente.textContent).toMatch(/seleziona Nuovo filtro/)
    expect(within(h).queryByRole("listbox")).toBeNull()
  })

  it("l'elenco dei modelli dice marca e nome, e si sceglie anche da tastiera", async () => {
    aperta()
    const h = await suH()
    cerca(h, "alp")
    const elenco = await within(h).findByRole("listbox", { name: "Modelli trovati" })
    const voce = within(elenco).getAllByRole("option")[0]!
    expect(voce.className).toBe("al-conf__riga-14")
    expect(voce.querySelector(".al-conf__testo-15")?.textContent).toBe("Antlia")
    expect(voce.querySelector(".al-conf__blocco-14")?.textContent).toBe("ALP-T 3nm")
    expect(voce.tabIndex).toBe(0)
    fireEvent.keyDown(voce, { key: "Enter" })
    expect(within(elenco).getAllByRole("option")[0]?.getAttribute("aria-selected")).toBe("true")
  })

  it("e la risposta porta il catalog_id del modello scelto, con marca, nome e modello", async () => {
    aperta()
    const h = await suH()
    cerca(h, "alp")
    fireEvent.click(await within(h).findByRole("option", { name: /ALP-T 3nm/ }))
    expect(await filtriMandati()).toEqual([
      { id: 7, catalog_id: "antlia-alp-t-3nm", brand: "Antlia", name: "Antlia ALP-T 3nm", model: "ALP-T 3nm" },
    ])
  })

  it("chi in catalogo non c e scrive nome e banda, e catalog_id resta fuori", async () => {
    // La terza strada, e non e' un ripiego: e' la sola per chi ha un filtro che il catalogo
    // non conosce. Lo schema la prevede -- `catalog_id` NULL se nome libero.
    aperta()
    const h = await suH()
    modo(h, "Nuovo filtro")
    fireEvent.change(within(h).getByLabelText("Nome"), { target: { value: " Il mio Ha " } })
    fireEvent.click(scelta(within(h).getByRole("group", { name: "Bande" }), "H\u03b1"))
    expect(await filtriMandati()).toEqual([{ id: 7, name: "Il mio Ha", bands: [{ band: "HA" }] }])
  })

  it("passando i 700 px e tornando la risposta data e la domanda aperta restano (Issue #61)", async () => {
    // Il telaio cambia forma sotto 700 px: la pagina sotto non deve rinascere, o perde cio'
    // che hai in mano (una finestra stretta e poi riallargata, un tablet girato).
    aperta()
    const h = await suH()
    modo(h, "Nuovo filtro")
    fireEvent.change(within(h).getByLabelText("Nome"), { target: { value: "Il mio Ha" } })
    fireEvent.click(scelta(within(h).getByRole("group", { name: "Bande" }), "Hα"))
    const largo = window.innerWidth
    try {
      for (const lato of [500, largo]) {
        window.innerWidth = lato
        fireEvent(window, new Event("resize"))
      }
    } finally {
      window.innerWidth = largo
    }
    const dopo = riga(await screen.findByRole("region", { name: /^filtri$/i }), "H")
    expect((within(dopo).getByLabelText("Nome") as HTMLInputElement).value).toBe("Il mio Ha")
  })

  it("un filtro nuovo con due bande e una larghezza manda le bande nell'ordine dell'elenco", async () => {
    aperta()
    const h = await suH()
    modo(h, "Nuovo filtro")
    fireEvent.change(within(h).getByLabelText("Nome"), { target: { value: "Duo" } })
    const bande = within(h).getByRole("group", { name: "Bande" })
    expect(voci(bande)).toEqual(["L", "R", "G", "B", "H\u03b1", "H\u03b2", "OIII", "SII"])
    fireEvent.click(scelta(bande, "OIII"))
    fireEvent.click(scelta(bande, "H\u03b1"))
    expect(voci(bande).filter((v) => v.startsWith("[x]"))).toEqual(["[x] H\u03b1", "[x] OIII"])
    // una parte per le larghezze, un campo per banda
    expect(parti(h)).toEqual(["Come rispondere per H", "Larghezza delle bande"])
    expect(within(h).getByLabelText("OIII, in nm")).toBeDefined()
    fireEvent.change(within(h).getByLabelText("H\u03b1, in nm"), { target: { value: "7,5" } })
    expect(await filtriMandati()).toEqual([
      { id: 7, name: "Duo", bands: [{ band: "HA", width_nm: 7.5 }, { band: "OIII" }] },
    ])
  })

  it("un filtro nuovo a meta' non e' una modifica: Applica resta spento, e il piede non lo conta", async () => {
    aperta()
    const h = await suH()
    modo(h, "Nuovo filtro")
    const piede = () => screen.getByRole("region", { name: "Le modifiche da applicare" }).querySelector(".al-conf__riga-18")?.textContent
    fireEvent.change(within(h).getByLabelText("Nome"), { target: { value: "Duo" } })
    // il nome senza bande
    applicaSpento()
    expect(piede()).toBe("0modifiche da applicare")
    const bande = within(h).getByRole("group", { name: "Bande" })
    fireEvent.click(scelta(bande, "SII"))
    applicaAcceso()
    // una larghezza che non e' un numero non parte vuota: la risposta aspetta
    fireEvent.change(within(h).getByLabelText("SII, in nm"), { target: { value: "stretto" } })
    applicaSpento()
    fireEvent.change(within(h).getByLabelText("SII, in nm"), { target: { value: "" } })
    applicaAcceso()
    // la banda tolta: di nuovo a meta'
    fireEvent.click(scelta(bande, "SII"))
    applicaSpento()
    // le bande senza nome, a meta' anche loro
    fireEvent.click(scelta(bande, "SII"))
    fireEvent.change(within(h).getByLabelText("Nome"), { target: { value: "  " } })
    applicaSpento()
    expect(piede()).toBe("0modifiche da applicare")
  })

  it("un filtro scritto a mano si rivede com'e' dopo che la sezione si e' chiusa e riaperta", async () => {
    // Una sezione chiusa si smonta: la strada "a mano" si rilegge dalla risposta in mano, o alla
    // riapertura si vedrebbero campi vuoti mentre Applica manda il nome scritto.
    aperta({
      ...PAGINA,
      filters: PAGINA.filters.slice(0, 1),
      typeless: [cartellaSenzaTipo({ key: "D:/Astro/dark", frames: 120 })],
    })
    const h = await suH()
    modo(h, "Nuovo filtro")
    fireEvent.change(within(h).getByLabelText("Nome"), { target: { value: "Il mio Ha" } })
    fireEvent.click(scelta(h, "H\u03b1"))
    fireEvent.change(within(h).getByLabelText("H\u03b1, in nm"), { target: { value: "7" } })
    fireEvent.click(screen.getByRole("button", { name: "Rispondi: D:/Astro/dark" }))
    expect(screen.queryByRole("region", { name: /^filtri$/i })).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: /^Riapri: Filtri/ }))
    const riaperta = riga(screen.getByRole("region", { name: /^filtri$/i }), "H")
    expect(scelto(scelta(riaperta, "Nuovo filtro"))).toBe(true)
    expect(within(riaperta).getByLabelText("Nome")).toHaveProperty("value", "Il mio Ha")
    expect(scelto(scelta(riaperta, "H\u03b1"))).toBe(true)
    expect(within(riaperta).getByLabelText("H\u03b1, in nm")).toHaveProperty("value", "7")
  })

  it("la larghezza in nanometri e facoltativa: si risponde anche senza", async () => {
    // Un anti inquinamento luminoso non ha una larghezza, e pretenderla bloccherebbe la risposta
    // su una cosa che non esiste. Lo schema la lascia nulla apposta.
    aperta()
    const h = await suH()
    modo(h, "Nuovo filtro")
    fireEvent.change(within(h).getByLabelText("Nome"), { target: { value: "L-Pro" } })
    fireEvent.click(scelta(h, "L"))
    expect(await filtriMandati()).toEqual([{ id: 7, name: "L-Pro", bands: [{ band: "L" }] }])
  })

  it("l elenco dei modelli si apre scrivendo, non prima", async () => {
    // Trovato collaudando sull'archivio vero il 14/9/2026: con otto filtri da rispondere la
    // pagina disegnava **304 bottoni** tutti insieme -- 8 x 38 modelli -- e il renderer del
    // browser e' andato in timeout. Il banco non lo mostrava: tre modelli finti e due filtri.
    aperta()
    const h = await suH()
    expect(within(h).queryByRole("option", { name: /ALP-T 3nm/ })).toBeNull()
    cerca(h, "alp")
    expect(await within(h).findByRole("option", { name: /ALP-T 3nm/ })).toBeDefined()
  })

  it("il nome del modello non ripete la marca", async () => {
    // Otto modelli su 38 portano gia' la marca dentro il nome ("Antlia Quad Band"), e comporre
    // marca + nome dava "Antlia Antlia Quad Band". Misurato sul vocabolario vero.
    aperta(PAGINA, {
      stato: 200,
      corpo: { items: [{ id: "antlia-quad-band", brand: "Antlia", name: "Antlia Quad Band", passband: "MULTI_NB" }] },
    })
    const h = await suH()
    cerca(h, "quad")
    const voce = await within(h).findByRole("option", { name: /Quad Band/ })
    expect(voce.querySelector(".al-conf__testo-15")?.textContent).toBe("Antlia")
    expect(voce.querySelector(".al-conf__blocco-14")?.textContent).toBe("Quad Band")
    fireEvent.click(voce)
    expect(await filtriMandati()).toEqual([
      { id: 7, catalog_id: "antlia-quad-band", brand: "Antlia", name: "Antlia Quad Band", model: "Antlia Quad Band" },
    ])
  })

  it("filtro esistente senza dire quale non e' una risposta", async () => {
    aperta()
    const h = await suH()
    modo(h, "Filtro esistente")
    expect(scelto(scelta(h, "Antlia ALP-T 3nm"))).toBe(false)
    applicaSpento()
  })

  it("passare a mano toglie uno dei miei, anche senza scrivere niente", async () => {
    // Le pillole dei miei a quel punto sono nascoste: un'unione rimasta in mano partirebbe senza che si veda.
    aperta()
    const h = await suH()
    modo(h, "Filtro esistente")
    fireEvent.click(scelta(h, "Antlia ALP-T 3nm"))
    modo(h, "Nuovo filtro")
    applicaSpento()
  })

  it("scelto uno dei miei e poi scritto a mano, parte il filtro scritto e non l'unione", async () => {
    // Sono due strade e non si sommano: col nome dentro la stessa risposta dell'unione, il
    // backend unirebbe e il nome scritto sparirebbe senza un messaggio.
    aperta()
    const h = await suH()
    modo(h, "Filtro esistente")
    fireEvent.click(scelta(h, "Antlia ALP-T 3nm"))
    modo(h, "Nuovo filtro")
    fireEvent.change(within(h).getByLabelText("Nome"), { target: { value: "Il mio H" } })
    fireEvent.click(scelta(h, "H\u03b1"))
    expect(await filtriMandati()).toEqual([{ id: 7, name: "Il mio H", bands: [{ band: "HA" }] }])
  })

  it("se l elenco dei modelli non risponde, lo dice nella domanda e la strada del catalogo si spegne", async () => {
    // **La bugia piu' costosa di questa pagina**, portata da `old/`: una coda che non si e'
    // potuta leggere non e' una coda vuota. Con l'elenco muto l'utente cerca il suo filtro,
    // non lo trova, e conclude che in catalogo non c'e' -- scrivendolo a mano per sempre.
    aperta(PAGINA, { stato: 500, corpo: { detail: { code: "rotto" } } })
    const sezione = await vaiAConfermare()
    const h = riga(sezione, "H")
    expect(await within(h).findByText("Elenco dei modelli non disponibile")).toBeDefined()
    expect(spento(scelta(h, "Modello da catalogo"))).toBe(true)
    // senza modelli si parte dai propri filtri
    expect(voci(within(h).getByRole("radiogroup", { name: "Come rispondere per H" }))).toEqual([
      "[x] Filtro esistente",
      "Modello da catalogo",
      "Nuovo filtro",
    ])
    expect(within(h).queryByLabelText(/cerca fra i modelli/i)).toBeNull()
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
    const h = await suH()
    cerca(h, "alp")
    fireEvent.click(await within(h).findByRole("option", { name: /ALP-T 3nm/ }))
    fireEvent.click(applica())
    expect(await screen.findByRole("alert")).toBeDefined()
  })

  it("una sezione senza domande non si vede", async () => {
    // Scelta di Marco: una pagina di undici titoli vuoti sembra rotta, e il giorno che hai
    // finito vuoi vederlo.
    aperta({ ...PAGINA, filters: [], to_confirm: 0 })
    await disegna()
    vai("/da-confermare")
    // il conto, o "niente da confermare" se non resta nessuna sezione
    await waitFor(() => expect(document.querySelector(".al-conf__riga-1, .al-c-avviso__blocco-1")).not.toBeNull())
    expect(screen.queryByRole("region", { name: /^filtri$/i })).toBeNull()
  })

  it("Applica manda solo le risposte, senza seen", async () => {
    // Applica scrive solo le risposte (ADR 0014): il server rifiuta un campo che non conosce.
    aperta()
    const h = await suH()
    cerca(h, "alp")
    fireEvent.click(await within(h).findByRole("option", { name: /ALP-T 3nm/ }))
    fireEvent.click(applica())
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
    const h = await suH()
    cerca(h, "alp")
    fireEvent.click(await within(h).findByRole("option", { name: /ALP-T 3nm/ }))
    fireEvent.click(applica())
    await screen.findByRole("status")
    // la pagina si e' riletta: due chiamate a /review, quella d'apertura e quella dopo
    await waitFor(() =>
      expect(chiamate().filter((u) => /\/api\/v1\/review($|\?)/.test(u)).length).toBeGreaterThan(1),
    )
    // e l'Applica torna spento, perche' non c'e' piu' niente in mano
    applicaSpento()
  })

  it("un clic sbagliato si corregge: si sceglie un altro modello, o un'altra strada", async () => {
    // Una scelta non e' un vicolo cieco finche' non si preme Applica.
    aperta()
    const h = await suH()
    cerca(h, "alp")
    fireEvent.click(await within(h).findByRole("option", { name: /ALP-T 3nm/ }))
    fireEvent.click(within(h).getByRole("option", { name: /ALP-T 5nm/ }))
    const scelti = within(h).getAllByRole("option").filter((o) => o.getAttribute("aria-selected") === "true")
    expect(scelti.map((o) => o.querySelector(".al-conf__blocco-14")?.textContent)).toEqual(["ALP-T 5nm"])
    // una ricerca che non lo comprende non toglie la risposta: sta per partire con Applica
    cerca(h, "zzz")
    expect(within(h).getByText(/nessun modello per/i)).toBeDefined()
    // e il modello in mano resta in vista, scelto
    const resta = within(h).getAllByRole("option")
    expect(resta.map((o) => [o.querySelector(".al-conf__blocco-14")?.textContent, o.getAttribute("aria-selected")])).toEqual([
      ["ALP-T 5nm", "true"],
    ])
    expect(scelta(h, "Nuovo filtro")).toBeDefined()
    expect(await filtriMandati()).toEqual([expect.objectContaining({ id: 7, catalog_id: "antlia-alp-t-5nm" })])
  })

  it("le risposte si accumulano e partono con un solo Applica", async () => {
    // La scelta di Marco: una sola attesa e un solo ricalcolo, invece di uno per risposta.
    aperta()
    const h = await suH()
    cerca(h, "alp")
    fireEvent.click(await within(h).findByRole("option", { name: /ALP-T 3nm/ }))
    // Prima di Applica non e' partita nessuna scrittura: le risposte stanno nella pagina.
    expect(scritture().some((s) => s.url.includes("/apply"))).toBe(false)
    fireEvent.click(applica())
    await waitFor(() =>
      expect(chiamate().filter((u) => u.includes("/api/v1/review/apply")).length).toBe(1),
    )
  })

  it("dopo Applica la pagina dice cosa e cambiato", async () => {
    // La ricevuta porta numeri veri (`changed`, `requeued`): un "fatto!" muto lascerebbe
    // l'utente a chiedersi se e' successo qualcosa.
    aperta()
    const h = await suH()
    cerca(h, "alp")
    fireEvent.click(await within(h).findByRole("option", { name: /ALP-T 3nm/ }))
    fireEvent.click(applica())
    // Si cerca la RICEVUTA, non il numero: "120 frame" e' gia' a schermo nella riga del filtro,
    // quindi cercarlo da solo passava anche togliendo la ricevuta -- provato dal revisore.
    const ricevuta = await screen.findByRole("status")
    expect(ricevuta.textContent).toContain("120")
    expect(ricevuta.textContent).toMatch(/da rielaborare/i)
  })
})
