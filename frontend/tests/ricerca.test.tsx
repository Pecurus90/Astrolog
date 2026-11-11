// @vitest-environment jsdom
/**
 * La ricerca nella barra in alto (`docs/domini/navigazione.md`): da ogni pagina trova oggetti,
 * notti, attrezzatura e siti, e una voce apre la pagina che gia' la mostra.
 *
 * L'indirizzo di una voce lo compone il frontend: la rotta dice chi e', non dove si apre.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { IGNOTO, INTERO, M31, conArchivio, voceArchivio } from "./archivio-banco"
import { FERMO, cambia, chiamate, disegna, pulisci, rispondi, violazioni } from "./banco"

afterEach(pulisci)

const NIENTE = {
  objects: { items: [], total: 0 },
  nights: { items: [], total: 0, why: null },
  gear: { items: [], total: 0 },
  sites: { items: [], total: 0 },
  archive_empty: false,
  examples: { gear: "Askar 107PHQ", site: "Monte Lema" },
}

const TROVATI = {
  objects: {
    items: [
      { key: "m-31", name: "M 31", common_name: "Andromeda Galaxy", frames: 10200, integration_s: 61200, untimed: 0, panels: null },
      { key: "mosaic-7", name: "Velo intero", common_name: null, frames: 864, integration_s: 103680, untimed: 0, panels: 4 },
    ],
    total: 2,
  },
  nights: {
    items: [
      { id: 41, night_date: "2026-10-04", site: "Cima Ekar", frames: 141, integration_s: 8640, untimed: 0 },
      { id: 12, night_date: "2026-08-14", site: "Casa", frames: 120, integration_s: 0, untimed: 120 },
    ],
    total: 7,
    why: { by: "object", dates: [], object: "M 31" },
  },
  gear: {
    items: [
      { id: 3, kind: "camera", name: "ZWO ASI2600MM Pro", counted: true, frames: 18420, integration_s: 757800, untimed: 0, no_hours: null },
      { id: 5, kind: "camera", name: "ZWO ASI533MC Pro", counted: false, frames: null, integration_s: null, untimed: null, no_hours: null },
      { id: 9, kind: "filter", name: "ZWO Duo-Band", counted: true, frames: null, integration_s: null, untimed: null, no_hours: "files_silent" },
    ],
    total: 3,
  },
  sites: { items: [{ id: 2, name: "Casa", nights: 64 }], total: 1 },
  archive_empty: false,
  examples: { gear: "ZWO ASI2600MM Pro", site: "Casa" },
}

function conRicerca(corpo: unknown, lavoro: unknown = FERMO) {
  rispondi({
    ...conArchivio(voceArchivio([M31])),
    "/api/v1/search": { stato: 200, corpo },
    "/api/v1/pipeline/status": { stato: 200, corpo: lavoro },
  })
}

/** Il bottone Cerca della testa (Telaio v76) e il campo di Cerca v77: il nome dice cosa si cerca. */
const CERCA = /^cerca oggetto, notte, attrezzatura, sito o pagina$/i

/** Apre la ricerca dalla barra e scrive: e' la strada dell'utente. */
async function cerca(testo: string) {
  await disegna()
  fireEvent.click(await screen.findByRole("link", { name: CERCA }))
  const campo = await screen.findByRole("combobox", { name: CERCA })
  fireEvent.change(campo, { target: { value: testo } })
  return campo
}

function trovati() {
  return screen.getByRole("listbox", { name: /^trovati$/i })
}

describe("Cerca, la finestra", () => {
  it("chiusa e' un bottone; toccata apre la finestra col campo col fuoco e dice cosa si cerca", async () => {
    conRicerca(NIENTE)
    await disegna()
    const bottone = await screen.findByRole("link", { name: CERCA })
    expect(bottone.textContent).toBe("Cerca")
    expect(bottone.getAttribute("title")).toBe("Cerca · Ctrl K")
    fireEvent.click(bottone)
    const finestra = await screen.findByRole("dialog", { name: "Cerca" })
    expect(finestra.getAttribute("aria-modal")).toBe("true")
    const campo = within(finestra).getByRole("combobox", { name: CERCA })
    await waitFor(() => expect(document.activeElement).toBe(campo))
    expect(campo.getAttribute("aria-expanded")).toBe("false")
    expect(within(trovati()).queryAllByRole("option")).toHaveLength(0)
    expect(within(finestra).getByText("Si cercano")).toBeTruthy()
  })

  it("il campo vuoto prende gli esempi di attrezzatura e sito dal tuo archivio", async () => {
    conRicerca(NIENTE)
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: CERCA }))
    const aiuto = (await screen.findByText("Si cercano")).parentElement as HTMLElement
    await waitFor(() => expect(aiuto.textContent).toContain("Attrezzatura · Askar 107PHQ"))
    expect(aiuto.textContent).toContain("Siti · Monte Lema")
    expect(aiuto.textContent).toContain("Oggetti · m31, NGC 224, Velo")
    // v79: each line on one line with the dots, all of it in the title
    const righe = [...aiuto.querySelectorAll(".al-c-cerca__aiuto-t")].map((r) => r.getAttribute("title"))
    expect(righe).toContain("Siti · Monte Lema")
    // Progetti arriva con la sua pagina
    expect(aiuto.textContent).not.toContain("Progetti")
  })

  it("mostra i gruppi, ognuno con quante voci ha in tutto, e le notti dicono perche'", async () => {
    conRicerca(TROVATI)
    await cerca("m31")
    const menu = await screen.findByRole("listbox", { name: /^trovati$/i })
    const oggetti = await within(menu).findByRole("group", { name: /oggetti/i })
    expect(within(oggetti).getByRole("option", { name: /M 31.*Andromeda Galaxy.*10\u202F200 frame.*17 h/ })).toBeTruthy()
    // un mosaico dice i suoi pannelli
    expect(within(oggetti).getByRole("option", { name: /Velo intero.*mosaico, 4 pannelli/ })).toBeTruthy()
    // il gruppo dice quante sono in tutto quando ne mostra meno
    const notti = within(menu).getByRole("group", { name: /notti/i })
    expect(notti.textContent).toContain("2 di 7")
    expect(notti.textContent).toContain("con M 31")
    expect(within(notti).getByRole("option", { name: /4 ott 2026.*Cima Ekar.*141 frame · 2 h 24/ })).toBeTruthy()
    // mai "0 h": una notte senza durata dice "senza durata"
    const senzaTempo = within(notti).getByRole("option", { name: /14 ago 2026/ })
    expect(senzaTempo.textContent).toContain("120 frame senza durata")
    expect(senzaTempo.textContent).not.toMatch(/\b0 h/)
    const pezzi = within(menu).getByRole("group", { name: /attrezzatura/i })
    expect(within(pezzi).getByRole("option", { name: /ZWO ASI2600MM Pro.*camera.*18\u202F420 frame \u00B7 210 h 30/ })).toBeTruthy()
    // ore non contate o non dette: il perche', mai uno zero
    expect(within(pezzi).getByRole("option", { name: /ZWO ASI533MC Pro/ }).textContent).toMatch(/conteggio in corso/)
    expect(within(pezzi).getByRole("option", { name: /ZWO Duo-Band.*filtro/ }).textContent).toMatch(/non indicato nei file/)
    const siti = within(menu).getByRole("group", { name: /siti/i })
    expect(within(siti).getByRole("option", { name: /Casa.*64 notti/ })).toBeTruthy()
  })

  it("le notti trovate per data dicono le date lette, anche nei due versi", async () => {
    const perData = { by: "dates", object: null, dates: [{ year: null, month: 6, day: 5 }, { year: null, month: 5, day: 6 }] }
    conRicerca({ ...NIENTE, nights: { ...TROVATI.nights, why: perData } })
    await cerca("5/6")
    const notti = await screen.findByRole("group", { name: /notti/i })
    expect(notti.textContent).toContain("5 giugno e 6 maggio")
  })

  it("trova le pagine e le voci delle Impostazioni, e le apre", async () => {
    conRicerca(NIENTE)
    await cerca("bortle")
    const imp = await screen.findByRole("group", { name: /impostazioni/i })
    fireEvent.click(within(imp).getByRole("option", { name: /Bortle.*Siti/ }))
    await waitFor(() => expect(window.location.pathname).toBe("/impostazioni/sito"))

    fireEvent.click(await screen.findByRole("link", { name: CERCA }))
    fireEvent.change(await screen.findByRole("combobox", { name: CERCA }), { target: { value: "met" } })
    const pagine = await screen.findByRole("group", { name: /pagine/i })
    fireEvent.click(within(pagine).getByRole("option", { name: /^Meteo$/ }))
    await waitFor(() => expect(window.location.pathname).toBe("/meteo"))
  })

  it("due voci delle Impostazioni verso la stessa sezione si vedono tutte e due", async () => {
    conRicerca(NIENTE)
    await cerca("sito")
    const imp = await screen.findByRole("group", { name: /impostazioni/i })
    // the chosen row also carries the "Invio" badge
    expect(within(imp).getAllByRole("option").map((o) => o.textContent?.replace("Invio", ""))).toEqual([
      "Coordinate del sito · Siti",
      "Sito predefinito · Siti",
    ])
  })

  it("un gruppo senza voci non si mostra", async () => {
    conRicerca({ ...NIENTE, sites: TROVATI.sites })
    await cerca("zz")
    await screen.findByRole("option", { name: /Casa/ })
    expect(within(trovati()).getAllByRole("group")).toHaveLength(1)
  })

  it("niente trovato lo dice, e dice cosa si cerca qui", async () => {
    conRicerca(NIENTE)
    await cerca("m 1033")
    expect(await screen.findByText("Niente per \u00abm 1033\u00bb.")).toBeTruthy()
    expect(screen.getByText("Qui si cercano oggetti, notti, attrezzatura, siti e pagine.")).toBeTruthy()
    expect(within(trovati()).queryAllByRole("option")).toHaveLength(0)
  })

  it("se AstroLog non risponde lo dice, senza righe", async () => {
    rispondi({ ...conArchivio(voceArchivio([M31])), "/api/v1/search": { stato: 500, corpo: {} } })
    await cerca("m31")
    expect(await screen.findByText("AstroLog non risponde, riprova.")).toBeTruthy()
    expect(within(trovati()).queryAllByRole("option")).toHaveLength(0)
  })

  it("con l'archivio vuoto dice che si trovano solo le pagine", async () => {
    conRicerca({ ...NIENTE, archive_empty: true })
    await cerca("met")
    expect(await screen.findByText(/^L'archivio \u00e8 vuoto: .* Intanto si trovano le pagine\.$/)).toBeTruthy()
    expect(await screen.findByRole("option", { name: /^Meteo$/ })).toBeTruthy()
  })

  it("con la scansione in corso dice la percentuale del backend", async () => {
    const lavoro = {
      ...FERMO,
      action: "stop",
      worker: { state: "running", stage: "scan", started_at: "2026-11-10T20:00:00Z", ended_at: null, stages: [{ name: "scan", state: "running", current: 19, total: 100, tally: {}, pct: 19 }] },
    }
    conRicerca(TROVATI, lavoro)
    await cerca("m31")
    expect(await screen.findByText("Scansione in corso, 19%: quello che non \u00e8 ancora stato letto non si trova.")).toBeTruthy()
    expect(await screen.findByRole("option", { name: /M 31/ })).toBeTruthy()
  })

  it("le frecce scelgono e Invio apre: un oggetto apre la sua finestra sulla pagina dove sei", async () => {
    conRicerca(TROVATI)
    const campo = await cerca("m31")
    const qui = window.location.pathname + window.location.search
    const menu = await screen.findByRole("listbox")
    const voci = await within(menu).findAllByRole("option")
    // la prima voce e' gia' scelta: Invio subito apre il primo trovato
    expect(voci[0]?.getAttribute("aria-selected")).toBe("true")
    expect(campo.getAttribute("aria-activedescendant")).toBe(voci[0]?.id)
    fireEvent.keyDown(campo, { key: "ArrowDown" })
    expect(voci[1]?.getAttribute("aria-selected")).toBe("true")
    expect(voci[0]?.getAttribute("aria-selected")).toBe("false")
    fireEvent.keyDown(campo, { key: "ArrowUp" })
    fireEvent.keyDown(campo, { key: "ArrowUp" })
    // dalla prima, su porta all'ultima: il menu gira
    expect(voci[voci.length - 1]?.getAttribute("aria-selected")).toBe("true")
    fireEvent.keyDown(campo, { key: "ArrowDown" })
    fireEvent.keyDown(campo, { key: "Enter" })
    const finestra = await screen.findByRole("dialog", { name: "Riepilogo: M 31" })
    // nessuna rotta d'oggetto: la pagina resta quella di prima
    expect(window.location.pathname + window.location.search).toBe(qui)
    // aperta la voce, la ricerca si chiude
    expect(screen.queryByRole("combobox", { name: CERCA })).toBeNull()
    expect(chiamate().some((u) => u.includes("/api/v1/objects/m-31"))).toBe(true)
    // Esc chiude la finestra
    fireEvent.keyDown(finestra, { key: "Escape" })
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull())
  })

  it("cambiata la pagina, la finestra dell'oggetto si chiude", async () => {
    conRicerca(TROVATI)
    await cerca("m31")
    fireEvent.click(await screen.findByRole("option", { name: /Velo intero/ }))
    expect(await screen.findByRole("dialog", { name: "Riepilogo: Velo intero" })).toBeTruthy()
    // la pagina cambia sotto la finestra: una finestra rimasta aperta coprirebbe la pagina chiesta
    fireEvent.click(await screen.findByRole("link", { name: /^archivio$/i }))
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull())
  })

  it.each([
    [/4 ott 2026/, "/notti?notte=41"],
    [/ZWO ASI2600MM Pro/, "/attrezzatura?pezzo=strumento-3"],
    [/ZWO Duo-Band/, "/attrezzatura?pezzo=filtro-9"],
    [/Casa.*64 notti/, "/impostazioni/sito?sito=2"],
  ])("la voce %s apre la pagina che gia' la mostra", async (nome, indirizzo) => {
    conRicerca(TROVATI)
    await cerca("x")
    fireEvent.click(await screen.findByRole("option", { name: nome }))
    await waitFor(() => expect(window.location.pathname + window.location.search).toBe(indirizzo))
  })

  it("cambiato il testo, le voci di prima spariscono: Invio subito non apre la ricerca vecchia", async () => {
    conRicerca(TROVATI)
    const campo = await cerca("m31")
    await screen.findByRole("option", { name: /M 31/ })
    fireEvent.change(campo, { target: { value: "andromeda" } })
    expect(within(trovati()).queryAllByRole("option")).toHaveLength(0)
    expect(campo.getAttribute("aria-expanded")).toBe("false")
    fireEvent.keyDown(campo, { key: "Enter" })
    expect(window.location.pathname + window.location.search).not.toContain("key=m-31")
    // la ricerca resta aperta e lo dice: sta cercando il testo nuovo
    expect(screen.getByText("Cerco\u2026")).toBeTruthy()
    expect(await screen.findByRole("option", { name: /M 31/ })).toBeTruthy()
  })

  it("riaperta dopo una chiusura non ripropone le voci della ricerca di prima", async () => {
    conRicerca(TROVATI)
    const campo = await cerca("m31")
    await screen.findByRole("option", { name: /M 31/ })
    fireEvent.keyDown(campo, { key: "Escape" })
    cambia({ ...conArchivio(voceArchivio([M31])), "/api/v1/search": { stato: 200, corpo: NIENTE } })
    fireEvent.click(await screen.findByRole("link", { name: CERCA }))
    const riaperto = await screen.findByRole("combobox", { name: CERCA })
    fireEvent.change(riaperto, { target: { value: "zzzqq" } })
    expect(within(trovati()).queryAllByRole("option")).toHaveLength(0)
    expect(await screen.findByText("Niente per \u00abzzzqq\u00bb.")).toBeTruthy()
    expect(within(trovati()).queryAllByRole("option")).toHaveLength(0)
  })

  it("Esc chiude e riporta il fuoco al bottone", async () => {
    conRicerca(TROVATI)
    const campo = await cerca("m31")
    await screen.findByRole("option", { name: /M 31/ })
    fireEvent.keyDown(campo, { key: "Escape" })
    const bottone = await screen.findByRole("link", { name: CERCA })
    await waitFor(() => expect(document.activeElement).toBe(bottone))
    expect(screen.queryByRole("dialog")).toBeNull()
  })

  it("Ctrl K la apre da ogni pagina", async () => {
    conRicerca(NIENTE)
    await disegna()
    await screen.findByRole("link", { name: CERCA })
    fireEvent.keyDown(document, { key: "k", ctrlKey: true })
    expect(await screen.findByRole("combobox", { name: CERCA })).toBeTruthy()
  })

  it("aperta, il bottone Cerca lo dice; un tocco sul velo la chiude e il fuoco torna", async () => {
    conRicerca(NIENTE)
    await cerca("m")
    const bottone = screen.getByRole("link", { name: CERCA })
    expect(bottone.getAttribute("aria-haspopup")).toBe("dialog")
    expect(bottone.getAttribute("aria-expanded")).toBe("true")
    // sul desktop non c'e' Annulla: c'e' Esc, scritto nel campo
    expect(screen.queryByRole("link", { name: /^annulla$/i })).toBeNull()
    fireEvent.mouseDown(screen.getByRole("dialog", { name: "Cerca" }).parentElement as HTMLElement)
    await waitFor(() => expect(bottone.getAttribute("aria-expanded")).toBe("false"))
    expect(screen.queryByRole("combobox")).toBeNull()
    expect(document.activeElement).toBe(bottone)
  })

  it("un tocco dentro la finestra non la chiude", async () => {
    conRicerca(NIENTE)
    await cerca("zzz")
    fireEvent.mouseDown((await screen.findByText("Niente per \u00abzzz\u00bb.")).parentElement as HTMLElement)
    expect(screen.getByRole("dialog", { name: "Cerca" })).toBeTruthy()
  })

  it("sul telefono Cerca e' un tondo nella testa, apre la pagina intera e Annulla la chiude", async () => {
    window.history.pushState({}, "", "/?formato=telefono")
    conRicerca(NIENTE)
    await disegna()
    fireEvent.click(within(await screen.findByRole("banner")).getByRole("link", { name: "Cerca" }))
    const campo = await screen.findByRole("combobox", { name: CERCA })
    expect(campo.getAttribute("placeholder")).toBe("Cerca")
    // il piede dei tasti e' del desktop
    expect(screen.queryByText("Esc chiude")).toBeNull()
    fireEvent.click(screen.getByRole("link", { name: /^annulla$/i }))
    await waitFor(() => expect(screen.queryByRole("dialog", { name: "Cerca" })).toBeNull())
  })

  it("la finestra aperta non ha difetti di accessibilita'", async () => {
    conRicerca(TROVATI)
    await cerca("m31")
    await screen.findByRole("option", { name: /M 31/ })
    expect(await violazioni(screen.getByRole("dialog", { name: "Cerca" }))).toEqual([])
  })
})

describe("l'Archivio aperto dalla ricerca", () => {
  it("con ?key= chiede quell'oggetto solo, dice che e' ristretto e come tornare", async () => {
    conRicerca(NIENTE)
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /archivio/i }))
    await waitFor(() => expect(window.location.pathname).toBe("/archivio"))
    window.history.replaceState(null, "", "/archivio?key=m-31")
    fireEvent.popState(window)
    const torna = await screen.findByRole("link", { name: /archivio completo/i })
    expect(torna.getAttribute("href")).toBe("/archivio")
    expect(torna.closest(".al-arch__riga-6")?.textContent).toContain("M 31")
    expect(chiamate().some((u) => u.includes("/api/v1/archive") && u.includes("key=m-31"))).toBe(true)
    // la barra esce, resta la vista
    expect(screen.queryByLabelText(/cerca un oggetto/i)).toBeNull()
    expect(screen.getByRole("radio", { name: /elenco/i })).toBeTruthy()
  })

  it("finche' la risposta non arriva non dice ristretto a un oggetto che non e' quello chiesto", async () => {
    // Chi cerca stando gia' nell'Archivio ha a schermo l'elenco intero: le righe di prima restano
    // durante l'attesa, e la prima di quelle non e' l'oggetto chiesto.
    rispondi({ ...conArchivio(voceArchivio([IGNOTO, M31])), "/api/v1/search": { stato: 200, corpo: NIENTE } })
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /archivio/i }))
    await screen.findByLabelText(/cerca un oggetto/i)

    let liberala = () => {}
    cambia({
      ...conArchivio({ ...voceArchivio([M31]), attesa: new Promise<unknown>((r) => (liberala = () => r(null))) }),
      "/api/v1/search": { stato: 200, corpo: NIENTE },
    })
    window.history.pushState(null, "", "/archivio?key=m-31")
    fireEvent.popState(window)
    await waitFor(() => expect(chiamate().some((u) => u.includes("key=m-31"))).toBe(true))
    expect(document.querySelector(".al-arch__riga-6")).toBeNull()

    liberala()
    const torna = await screen.findByRole("link", { name: /archivio completo/i })
    expect(torna.closest(".al-arch__riga-6")?.textContent).toContain("M 31")
  })

  it("una chiave che non trova niente lo dice, e non sembra un archivio vuoto", async () => {
    rispondi({ ...conArchivio(voceArchivio([], { whole: INTERO })), "/api/v1/search": { stato: 200, corpo: NIENTE } })
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /archivio/i }))
    await waitFor(() => expect(window.location.pathname).toBe("/archivio"))
    window.history.replaceState(null, "", "/archivio?key=non-c-e")
    fireEvent.popState(window)
    expect(await screen.findByText(/^oggetto non trovato$/i)).toBeTruthy()
    expect(screen.getByRole("link", { name: /archivio completo/i })).toBeTruthy()
    expect(screen.queryByText(/^archivio vuoto$/i)).toBeNull()
  })
})
