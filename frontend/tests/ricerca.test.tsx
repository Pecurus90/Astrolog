// @vitest-environment jsdom
/**
 * La ricerca nella barra in alto (`docs/domini/navigazione.md`): da ogni pagina trova oggetti,
 * notti, attrezzatura e siti, e una voce apre la pagina che gia' la mostra.
 *
 * L'indirizzo di una voce lo compone il frontend: la rotta dice chi e', non dove si apre.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { IGNOTO, M31, conArchivio, voceArchivio } from "./archivio-banco"
import { cambia, chiamate, disegna, pulisci, rispondi, violazioni } from "./banco"

afterEach(pulisci)

const NIENTE = {
  objects: { items: [], total: 0 },
  nights: { items: [], total: 0 },
  gear: { items: [], total: 0 },
  sites: { items: [], total: 0 },
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
}

function conRicerca(corpo: unknown) {
  rispondi({ ...conArchivio(voceArchivio([M31])), "/api/v1/search": { stato: 200, corpo } })
}

/** Apre la ricerca dalla barra e scrive: e' la strada dell'utente. */
async function cerca(testo: string) {
  await disegna()
  fireEvent.click(await screen.findByRole("button", { name: /^cerca$/i }))
  const campo = await screen.findByRole("combobox", { name: /cerca nell'archivio/i })
  fireEvent.change(campo, { target: { value: testo } })
  return campo
}

describe("la ricerca nella barra", () => {
  it("chiusa e' un bottone, e toccata diventa un campo col fuoco", async () => {
    conRicerca(NIENTE)
    await disegna()
    fireEvent.click(await screen.findByRole("button", { name: /^cerca$/i }))
    const campo = await screen.findByRole("combobox", { name: /cerca nell'archivio/i })
    await waitFor(() => expect(document.activeElement).toBe(campo))
    // niente da proporre prima della prima lettera
    expect(screen.queryByRole("listbox")).toBeNull()
    expect(campo.getAttribute("aria-expanded")).toBe("false")
  })

  it("un campo vuoto non chiede niente alla rotta", async () => {
    conRicerca(NIENTE)
    await cerca("   ")
    await new Promise((fatto) => setTimeout(fatto, 400))
    expect(chiamate().some((u) => u.includes("/api/v1/search"))).toBe(false)
  })

  it("mostra i quattro gruppi, ognuno con quante voci ha in tutto", async () => {
    conRicerca(TROVATI)
    await cerca("m31")
    const menu = await screen.findByRole("listbox", { name: /^risultati$/i })
    const oggetti = within(menu).getByRole("group", { name: /oggetti/i })
    expect(within(oggetti).getByRole("option", { name: /M 31.*Andromeda Galaxy.*10\.200 frame.*17 h/ })).toBeTruthy()
    // un mosaico dice i suoi pannelli
    expect(within(oggetti).getByRole("option", { name: /Velo intero.*mosaico, 4 pannelli/ })).toBeTruthy()
    // il gruppo dice quante sono in tutto quando ne mostra meno
    const notti = within(menu).getByRole("group", { name: /notti/i })
    expect(notti.textContent).toContain("2 di 7")
    expect(within(notti).getByRole("option", { name: /4 ott 2026.*Cima Ekar.*141 frame.*2,4 h/ })).toBeTruthy()
    // mai "0 h": una notte senza durata dice "senza durata"
    const senzaTempo = within(notti).getByRole("option", { name: /14 ago 2026/ })
    expect(senzaTempo.textContent).toContain("120 frame senza durata")
    expect(senzaTempo.textContent).not.toMatch(/\b0 h/)
    const pezzi = within(menu).getByRole("group", { name: /attrezzatura/i })
    expect(within(pezzi).getByRole("option", { name: /ZWO ASI2600MM Pro.*camera.*18\.420 frame.*210,5 h/ })).toBeTruthy()
    // ore non contate o non dette: il perche', mai uno zero
    expect(within(pezzi).getByRole("option", { name: /ZWO ASI533MC Pro/ }).textContent).toMatch(/Conteggio in corso/)
    expect(within(pezzi).getByRole("option", { name: /ZWO Duo-Band.*filtro/ }).textContent).toMatch(/Non indicato nei file/)
    const siti = within(menu).getByRole("group", { name: /siti/i })
    expect(within(siti).getByRole("option", { name: /Casa.*64 notti/ })).toBeTruthy()
  })

  it("un gruppo senza voci non si mostra", async () => {
    conRicerca({ ...NIENTE, sites: TROVATI.sites })
    await cerca("ca")
    const menu = await screen.findByRole("listbox")
    expect(within(menu).getAllByRole("group")).toHaveLength(1)
  })

  it("niente trovato lo dice, e dice cosa si cerca qui", async () => {
    conRicerca(NIENTE)
    await cerca("m 1033")
    expect(await screen.findByText(/nessun risultato per \u00abm 1033\u00bb/i)).toBeTruthy()
    expect(screen.getByText(/oggetti, notti, attrezzatura e siti/i)).toBeTruthy()
    expect(screen.queryByRole("listbox")).toBeNull()
  })

  it("le frecce scelgono e Invio apre: un oggetto apre l'Archivio ristretto a lui", async () => {
    conRicerca(TROVATI)
    const campo = await cerca("m31")
    const menu = await screen.findByRole("listbox")
    const voci = within(menu).getAllByRole("option")
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
    await waitFor(() => expect(window.location.pathname + window.location.search).toBe("/archivio?key=m-31"))
    // aperta la voce, la ricerca si chiude
    expect(screen.queryByRole("combobox", { name: /cerca nell'archivio/i })).toBeNull()
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
    await screen.findByRole("listbox")
    fireEvent.change(campo, { target: { value: "andromeda" } })
    expect(screen.queryByRole("listbox")).toBeNull()
    expect(campo.getAttribute("aria-expanded")).toBe("false")
    fireEvent.keyDown(campo, { key: "Enter" })
    expect(window.location.pathname + window.location.search).not.toContain("key=m-31")
    // la ricerca resta aperta e lo dice: sta cercando il testo nuovo
    expect(screen.getByText(/^ricerca\u2026$/i)).toBeTruthy()
    expect(await screen.findByRole("listbox")).toBeTruthy()
  })

  it("riaperta dopo una chiusura non ripropone le voci della ricerca di prima", async () => {
    conRicerca(TROVATI)
    const campo = await cerca("m31")
    await screen.findByRole("listbox")
    fireEvent.keyDown(campo, { key: "Escape" })
    cambia({ ...conArchivio(voceArchivio([M31])), "/api/v1/search": { stato: 200, corpo: NIENTE } })
    fireEvent.click(await screen.findByRole("button", { name: /^cerca$/i }))
    const riaperto = await screen.findByRole("combobox", { name: /cerca nell'archivio/i })
    fireEvent.change(riaperto, { target: { value: "zzzqq" } })
    expect(screen.queryByRole("listbox")).toBeNull()
    expect(await screen.findByText(/nessun risultato per \u00abzzzqq\u00bb/i)).toBeTruthy()
    expect(screen.queryByRole("listbox")).toBeNull()
  })

  it("Esc chiude e riporta il fuoco al bottone", async () => {
    conRicerca(TROVATI)
    const campo = await cerca("m31")
    await screen.findByRole("listbox")
    fireEvent.keyDown(campo, { key: "Escape" })
    const bottone = await screen.findByRole("button", { name: /^cerca$/i })
    await waitFor(() => expect(document.activeElement).toBe(bottone))
    expect(screen.queryByRole("listbox")).toBeNull()
  })

  it("Ctrl K la apre da ogni pagina", async () => {
    conRicerca(NIENTE)
    await disegna()
    await screen.findByRole("button", { name: /^cerca$/i })
    fireEvent.keyDown(window, { key: "k", ctrlKey: true })
    expect(await screen.findByRole("combobox", { name: /cerca nell'archivio/i })).toBeTruthy()
  })

  it("aperta, la barra lo dice al foglio: sul telefono il campo prende la riga", async () => {
    conRicerca(NIENTE)
    await cerca("m")
    expect(screen.getByRole("banner").className).toContain("as-telaio__alto--cerca")
    fireEvent.click(screen.getByRole("button", { name: /annulla/i }))
    await waitFor(() => expect(screen.getByRole("banner").className).not.toContain("as-telaio__alto--cerca"))
  })

  it("il menu aperto non ha difetti di accessibilita'", async () => {
    conRicerca(TROVATI)
    await cerca("m31")
    await screen.findByRole("listbox")
    expect(await violazioni(screen.getByRole("banner"))).toEqual([])
  })
})

describe("l'Archivio aperto dalla ricerca", () => {
  it("con ?key= chiede quell'oggetto solo, dice che e' ristretto e come tornare", async () => {
    conRicerca(NIENTE)
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /archivio/i }))
    await screen.findByRole("heading", { name: /archivio/i })
    window.history.replaceState(null, "", "/archivio?key=m-31")
    fireEvent.popState(window)
    const torna = await screen.findByRole("link", { name: /archivio completo/i })
    expect(torna.getAttribute("href")).toBe("/archivio")
    expect(torna.closest(".as-archivio__ristretto")?.textContent).toContain("M 31")
    expect(chiamate().some((u) => u.includes("/api/v1/archive") && u.includes("key=m-31"))).toBe(true)
    // la barra esce, resta la vista
    expect(screen.queryByLabelText(/cerca un oggetto/i)).toBeNull()
    expect(screen.getByRole("tab", { name: /elenco/i })).toBeTruthy()
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
    expect(document.querySelector(".as-archivio__ristretto")).toBeNull()

    liberala()
    const torna = await screen.findByRole("link", { name: /archivio completo/i })
    expect(torna.closest(".as-archivio__ristretto")?.textContent).toContain("M 31")
  })

  it("una chiave che non trova niente lo dice, e non sembra un archivio vuoto", async () => {
    rispondi({ ...conArchivio(voceArchivio([])), "/api/v1/search": { stato: 200, corpo: NIENTE } })
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /archivio/i }))
    await screen.findByRole("heading", { name: /archivio/i })
    window.history.replaceState(null, "", "/archivio?key=non-c-e")
    fireEvent.popState(window)
    expect(await screen.findByText(/^oggetto non trovato$/i)).toBeTruthy()
    expect(screen.getByRole("link", { name: /archivio completo/i })).toBeTruthy()
    expect(screen.queryByText(/^archivio vuoto$/i)).toBeNull()
  })
})
