// @vitest-environment jsdom
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, STANOTTE, cambia, chiamate, disegna, impostazioni, pulisci, rispondi } from "./banco"

afterEach(pulisci)

/**
 * L'ossatura di *Da confermare* nel foglio v34: l'indice, il conto, le sezioni e il piede. Cio'
 * che una sezione chiede lo provano i file delle sezioni; qui si prova cio' che le tiene insieme.
 */

const PAGINA = {
  to_confirm: 3,
  lookalikes: [
    { id: 4, name: "ATR2600M(USB2.0)", frames: 38, into_id: 1, into_name: "ATR2600M", into_frames: 412 },
  ],
  filters: [],
  filter_choices: [],
  objects: [],
  gear: [],
  rig_choices: [],
  optics_choices: [],
  settled_objects: 0,
  unclear: [],
  mosaics: [],
  typeless: [
    { key: "D:/Astro/dark", frames: 120, answer: null },
    { key: "D:/Astro/M51", frames: 30, answer: "light" },
  ],
}

const VUOTA = { ...PAGINA, to_confirm: 0, lookalikes: [], typeless: [] }

function aperta(pagina: unknown = PAGINA, extra: Parameters<typeof rispondi>[0] = {}) {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review/apply": { stato: 200, corpo: { changed: 1, requeued: 320, run_started: true } },
    "/api/v1/review": { stato: 200, corpo: pagina },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
    // per ultimo: una voce gia' scritta sopra tiene il suo posto e prende questo valore
    ...extra,
  })
}

async function apri() {
  await disegna()
  fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
}

/** Le voci dell'indice, come si leggono: il nome e, dopo, quante senza risposta o la spunta. */
const indice = () =>
  within(screen.getByRole("navigation", { name: "Sezioni" }))
    .getAllByRole("listitem")
    .map((v) => v.textContent)

describe("Da confermare -- l'ossatura della pagina", () => {
  it("in cima il conto e la regola, a sinistra l'indice, e una carta per sezione", async () => {
    aperta()
    await apri()
    const piede = await screen.findByRole("region", { name: "Modifiche da applicare" })
    const pagina = piede.closest(".as-conferma") as HTMLElement
    expect(pagina.className).toBe("as-conferma as-conferma--indice")
    expect(pagina.querySelector(".as-conferma__conta")?.textContent).toBe("3 da confermare")
    expect(pagina.querySelector(".as-conferma__conta b")?.textContent).toBe("3")
    expect(pagina.querySelector(".as-conferma__regola")?.textContent).toMatch(/Applica/)

    // l'indice ha le sole sezioni che ci sono, nell'ordine della pagina, e quante aspettano
    expect(indice()).toEqual(["Strumenti duplicati1", "Frame senza tipo1"])
    // sticky at every width in the sheet: in a single column it would cover the answers
    expect(screen.getByRole("navigation", { name: "Sezioni" }).className).toBe("as-conferma-indice as-solo-largo")

    const sezione = screen.getByRole("region", { name: "Frame senza tipo" })
    expect(sezione.className).toBe("as-carta as-conferma-sezione")
    expect(sezione.querySelector(".as-conferma-sezione__quante")?.textContent).toBe("2 domande")
    expect(screen.getByRole("region", { name: "Strumenti duplicati" }).querySelector(".as-conferma-sezione__quante")?.textContent).toBe("1 domanda")

    // il piede: niente in mano, e Applica spento
    expect(piede.className).toBe("as-conferma-tutto")
    expect(piede.querySelector(".as-conferma-tutto__conta")?.textContent).toBe("0 modifiche da applicare")
    expect(within(piede).getByRole("button", { name: "Applica" })).toHaveProperty("disabled", true)
  })

  it("una voce dell'indice porta alla sua sezione", async () => {
    aperta()
    await apri()
    const voce = within(await screen.findByRole("navigation", { name: "Sezioni" })).getByRole("link", { name: /frame senza tipo/i })
    const sezione = screen.getByRole("region", { name: "Frame senza tipo" })
    expect(voce.getAttribute("href")).toBe(`#${sezione.id}`)
    expect(sezione.id).not.toBe("")
  })

  it("rispondendo, l'indice conta una domanda in meno, e a zero mette la spunta", async () => {
    aperta()
    await apri()
    fireEvent.click(await screen.findByRole("button", { name: "Rispondi: D:/Astro/dark" }))
    fireEvent.click(screen.getByRole("radio", { name: "Light" }))
    expect(indice()).toEqual(["Strumenti duplicati1", "Frame senza tipo\u2713"])
    // la spunta non e' sola: chi ascolta sente che sono tutte risposte
    expect(within(screen.getByRole("navigation", { name: "Sezioni" })).getByLabelText("tutte con risposta")).toBeDefined()
  })

  it("un'unione di strumenti in mano si dice accanto ad Applica, prima di premerlo", async () => {
    // Unire non si annulla: e' l'unica risposta della pagina che non torna indietro.
    aperta()
    await apri()
    const piede = await screen.findByRole("region", { name: "Modifiche da applicare" })
    expect(piede.querySelector(".as-conferma-avverte")).toBeNull()

    const sezione = screen.getByRole("region", { name: "Strumenti duplicati" })
    fireEvent.click(within(sezione).getByRole("radio", { name: /unisci a ATR2600M/i }))
    expect(piede.querySelector(".as-conferma-avverte")?.textContent).toMatch(/unione di strumenti.*non .* reversibile/i)

    fireEvent.click(within(sezione).getByRole("radio", { name: /sono distinti/i }))
    expect(piede.querySelector(".as-conferma-avverte")).toBeNull()
  })

  it("mentre legge mostra lo scheletro, non una riga di testo", async () => {
    aperta(PAGINA, { "/api/v1/review": { stato: 200, corpo: PAGINA, attesa: new Promise(() => {}) } })
    await apri()
    await waitFor(() => expect(document.querySelector(".as-conferma[aria-busy=true]")).not.toBeNull())
    const pagina = document.querySelector(".as-conferma[aria-busy=true]") as HTMLElement
    expect(pagina.getAttribute("aria-label")).toBe("Caricamento\u2026")
    expect(pagina.querySelectorAll(".as-scheletro").length).toBeGreaterThan(3)
    expect(pagina.querySelector(".as-conferma-indice")?.className).toBe("as-conferma-indice as-solo-largo")
  })

  it("se non si legge lo dice, e si riprova da li'", async () => {
    aperta(PAGINA, { "/api/v1/review": { stato: 500, corpo: {} } })
    await apri()
    const avviso = (await screen.findByText("Da confermare non disponibile")).closest(".as-avviso") as HTMLElement
    const quante = () => chiamate().filter((u) => u.endsWith("/api/v1/review")).length
    const prima = quante()
    fireEvent.click(within(avviso).getByRole("button", { name: "Riprova" }))
    await waitFor(() => expect(quante()).toBeGreaterThan(prima))
  })

  it("senza niente da chiedere lo dice: niente indice e niente piede", async () => {
    // Lo stato in cui la pagina sta quasi sempre: prima restavano un conto e un piede vuoto.
    aperta(VUOTA)
    await apri()
    const avviso = (await screen.findByText("Niente da confermare")).closest(".as-avviso") as HTMLElement
    expect(avviso.className).toContain("as-avviso--buono")
    expect(document.querySelector(".as-conferma__conta")?.textContent).toBe("0 da confermare")
    expect(screen.queryByRole("navigation", { name: "Sezioni" })).toBeNull()
    expect(screen.queryByRole("region", { name: "Modifiche da applicare" })).toBeNull()
  })

  it("senza nessun frame dice da dove si comincia: niente conto e niente piede", async () => {
    // "Niente da confermare" a chi non ha ancora scelto le cartelle sarebbe vero e inutile.
    aperta({ ...VUOTA, empty: true })
    await apri()
    const testo = await screen.findByText("Nessun frame in archivio. Le domande compaiono dopo la lettura delle cartelle.")
    const vuoto = testo.closest(".as-vuoto") as HTMLElement
    expect(within(vuoto).getByRole("link", { name: "Aggiungi cartelle" }).getAttribute("href")).toBe("/impostazioni/cartelle")
    expect(screen.queryByText("Niente da confermare")).toBeNull()
    expect(document.querySelector(".as-conferma__conta")).toBeNull()
    expect(screen.queryByRole("region", { name: "Modifiche da applicare" })).toBeNull()
  })

  it("senza frame ma con una domanda, la domanda si vede: le risposte ripristinate ne portano", async () => {
    aperta({ ...PAGINA, empty: true })
    await apri()
    expect(await screen.findByRole("region", { name: "Strumenti duplicati" })).toBeDefined()
    expect(document.querySelector(".as-vuoto")).toBeNull()
  })

  it("con sole domande di sezioni non ancora disegnate non dice che non c'e' niente", async () => {
    // Il conto in cima conta anche Oggetti e Attrezzatura da completare: negarle sarebbe falso.
    aperta({ ...VUOTA, to_confirm: 5 })
    await apri()
    await waitFor(() => expect(document.querySelector(".as-conferma__conta")?.textContent).toBe("5 da confermare"))
    expect(screen.queryByText("Niente da confermare")).toBeNull()
    expect(screen.queryByRole("region", { name: "Modifiche da applicare" })).toBeNull()
  })

  it("l'esito si legge anche quando l'Applica ha svuotato la pagina", async () => {
    // Strumenti duplicati e Filtri escono dall'API appena hanno risposta: l'ultima svuota la pagina.
    let finisci: () => void = () => {}
    const mappa = (pagina: unknown) => ({
      ...STANOTTE,
      "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
      "/api/v1/review/apply": {
        stato: 200,
        corpo: { changed: 1, requeued: 38, run_started: true },
        attesa: new Promise<void>((fatto) => (finisci = fatto)),
      },
      "/api/v1/review": { stato: 200, corpo: pagina },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    rispondi(mappa({ ...PAGINA, to_confirm: 1, typeless: [] }))
    await apri()
    const sezione = await screen.findByRole("region", { name: "Strumenti duplicati" })
    fireEvent.click(within(sezione).getByRole("radio", { name: /unisci a ATR2600M/i }))
    fireEvent.click(screen.getByRole("button", { name: "Applica" }))
    await waitFor(() => expect(document.querySelector(".as-conferma--ferma")).not.toBeNull())
    const libera = finisci
    cambia(mappa(VUOTA))
    libera()

    const esito = (await screen.findByText("1 modifica applicata, 38 frame da rielaborare")).closest(".as-avviso") as HTMLElement
    expect(screen.getByText("Niente da confermare")).toBeDefined()
    fireEvent.click(within(esito).getByRole("button", { name: "Chiudi" }))
    expect(screen.queryByText("1 modifica applicata, 38 frame da rielaborare")).toBeNull()
  })

  it("mentre applica la pagina si ferma e il comando lo dice; applicato, l'esito si chiude", async () => {
    let finisci: () => void = () => {}
    aperta(PAGINA, {
      "/api/v1/review/apply": {
        stato: 200,
        corpo: { changed: 1, requeued: 320, run_started: true },
        attesa: new Promise<void>((fatto) => (finisci = fatto)),
      },
    })
    await apri()
    fireEvent.click(await screen.findByRole("button", { name: "Rispondi: D:/Astro/dark" }))
    fireEvent.click(screen.getByRole("radio", { name: "Light" }))
    fireEvent.click(screen.getByRole("button", { name: "Applica" }))

    // al lavoro: una risposta data adesso si perderebbe, quindi le sezioni non si toccano
    const pagina = document.querySelector(".as-conferma") as HTMLElement
    await waitFor(() => expect(pagina.className).toContain("as-conferma--ferma"))
    const comando = within(screen.getByRole("region", { name: "Modifiche da applicare" })).getByRole("button")
    expect(comando.getAttribute("aria-busy")).toBe("true")
    expect(comando.textContent).toBe("Applicazione in corso\u2026")
    expect(pagina.querySelector(".as-conferma__colonna")?.hasAttribute("inert")).toBe(true)

    finisci()
    const esito = (await screen.findByText("1 modifica applicata, 320 frame da rielaborare")).closest(".as-avviso") as HTMLElement
    expect(pagina.className).not.toContain("as-conferma--ferma")
    fireEvent.click(within(esito).getByRole("button", { name: "Chiudi" }))
    expect(screen.queryByText("1 modifica applicata, 320 frame da rielaborare")).toBeNull()
  })
})
