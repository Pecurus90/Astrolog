// @vitest-environment jsdom
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  STANOTTE,
  cambia,
  cartellaSenzaData,
  cartellaSenzaTipo,
  chiamate,
  daConfermare,
  disegna,
  doppione,
  impostazioni,
  postoIgnoto,
  pulisci,
  rispondi,
  vai,
} from "./banco"

afterEach(pulisci)

/**
 * Il guscio di *Da confermare* sulla tavola v82: il conto vivo con le tacche, l'indice, le sezioni,
 * il piede e l'esito. Cio' che una sezione chiede lo provano i file delle sezioni.
 */

const PAGINA = daConfermare({
  to_confirm: 2,
  lookalikes: [doppione({ id: 4, name: "ATR2600M(USB2.0)", frames: 38, into_id: 1, into_name: "ATR2600M", into_frames: 412 })],
  typeless: [
    cartellaSenzaTipo({ key: "D:/Astro/dark", frames: 120 }),
    cartellaSenzaTipo({ key: "D:/Astro/M51", frames: 30, answer: "light" }),
  ],
})

const VUOTA = { ...PAGINA, to_confirm: 0, lookalikes: [], typeless: [] }
const APPLICATO = { changed: 1, requeued: 320, run_started: true, none_filter_existed: false }

function aperta(pagina: unknown = PAGINA, extra: Parameters<typeof rispondi>[0] = {}) {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review/apply": { stato: 200, corpo: APPLICATO },
    "/api/v1/review": { stato: 200, corpo: pagina },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
    // per ultimo: una voce gia' scritta sopra tiene il suo posto e prende questo valore
    ...extra,
  })
}

async function apri(dove = "/da-confermare") {
  await disegna()
  vai(dove)
}

const conto = () => screen.queryByRole("region", { name: "Il conto" })
const numeroDelConto = () => conto()?.querySelector(".al-conf__testo-1")?.textContent
const tacche = () => screen.getByRole("img", { name: /^Con risposta: / })
const piede = () => screen.queryByRole("region", { name: "Le modifiche da applicare" })
const applica = () => within(piede() as HTMLElement).getByRole("button")
const nav = () => screen.queryByRole("navigation", { name: "Sezioni" })
/** Le voci dell'indice come si leggono: il nome, la riga sotto, e il tondo. */
const indice = () =>
  within(nav() as HTMLElement)
    .getAllByRole("link")
    .map((v) => [
      v.querySelector(".al-conf__testo-4")?.textContent,
      v.querySelector(".al-conf__testo-5")?.textContent,
      v.querySelector(".al-conf__tondo-1")?.textContent,
    ])
const rispondiLight = () => {
  fireEvent.click(screen.getByRole("button", { name: "Rispondi: D:/Astro/dark" }))
  fireEvent.click(screen.getByRole("radio", { name: "Light" }))
}

describe("Da confermare -- il guscio della pagina", () => {
  it("a sinistra il conto e l'indice, a destra le sezioni e il piede, con le misure della tavola", async () => {
    aperta()
    await apri()
    await screen.findByRole("region", { name: "Le modifiche da applicare" })
    const griglia = document.querySelector(".al-conf__blocco-1 > .al-conf__centro-1") as HTMLElement
    expect(griglia.style.gridTemplateColumns).toBe("300px minmax(0px, 1fr)")
    expect(griglia.style.gap).toBe("16px")
    const sinistra = griglia.querySelector(":scope > .al-conf__colonna-1") as HTMLElement
    expect(sinistra.style.position).toBe("sticky")
    expect(sinistra.contains(conto())).toBe(true)
    expect(sinistra.contains(nav())).toBe(true)

    // il conto: le domande senza risposta, grande; la regola sotto
    expect((conto()?.querySelector(".al-conf__testo-1") as HTMLElement).style.fontSize).toBe("64px")
    expect(conto()?.querySelector(".al-conf__riga-1")?.textContent).toBe("2da confermare")
    expect(conto()?.querySelector(".al-conf__testo-3")?.textContent).toBe(
      "Le risposte si salvano tutte insieme con Applica. Rispondere \u00e8 facoltativo: senza risposta i frame restano invariati.",
    )
    // una tacca per domanda, anche quella gia' salvata
    expect(tacche().getAttribute("aria-label")).toBe("Con risposta: 1 su 3")
    expect(tacche().querySelectorAll(".al-conf__blocco-2")).toHaveLength(3)

    // l'indice ha le sole sezioni che ci sono, nell'ordine della pagina
    expect(indice()).toEqual([
      ["Strumenti duplicati", "1 senza risposta", "1"],
      ["Frame senza tipo", "1 senza risposta", "1"],
    ])
    const sezioni = document.querySelector(".al-conf__colonna-11") as HTMLElement
    const senzaTipo = screen.getByRole("region", { name: "Frame senza tipo" })
    expect(sezioni.contains(senzaTipo)).toBe(true)
    // accanto al titolo quante domande ha la sezione
    const quante = (s: HTMLElement) => s.querySelector("header .al-conf__riga-11 > .al-conf__testo-10")?.textContent
    expect(quante(senzaTipo)).toBe("2 domande")
    expect(quante(screen.getByRole("region", { name: "Strumenti duplicati" }))).toBe("1 domanda")

    // il piede: niente in mano, e Applica spento
    expect(piede()?.className).toBe("al-conf__riga-17")
    expect(piede()?.querySelector(".al-conf__riga-18")?.textContent).toBe("0modifiche da applicare")
    expect(applica().textContent).toBe("Applica")
    expect(applica().getAttribute("aria-disabled")).toBe("true")
  })

  it("rispondendo il conto scende, la tacca si accende e il piede conta la risposta in mano", async () => {
    aperta()
    await apri()
    await screen.findByRole("region", { name: "Il conto" })
    const segni = () => [...tacche().querySelectorAll<HTMLElement>(".al-conf__blocco-2")].map((x) => x.style.border)
    expect(segni()).toEqual(["1.5px solid var(--tenue)", "1.5px solid var(--tenue)", "0px"])
    rispondiLight()
    expect(numeroDelConto()).toBe("1")
    expect(tacche().getAttribute("aria-label")).toBe("Con risposta: 2 su 3")
    expect(segni()).toEqual(["1.5px solid var(--tenue)", "0px", "0px"])
    expect(piede()?.querySelector(".al-conf__riga-18")?.textContent).toBe("1modifica da applicare")
    expect(applica().getAttribute("aria-disabled")).toBeNull()
  })

  it("rispondendo, l'indice conta una domanda in meno, e a zero mette la spunta", async () => {
    aperta()
    await apri()
    await screen.findByRole("navigation", { name: "Sezioni" })
    rispondiLight()
    expect(indice()).toEqual([
      ["Strumenti duplicati", "1 senza risposta", "1"],
      ["Frame senza tipo", "tutte con risposta", "\u2713"],
    ])
  })

  it("la sezione corrente e' segnata nell'indice; una voce apre la sua sezione, anche chiusa", async () => {
    aperta()
    await apri()
    const voce = (nome: string) => within(nav() as HTMLElement).getByRole("link", { name: new RegExp(`^${nome}`) })
    await screen.findByRole("navigation", { name: "Sezioni" })
    // aperta e' la prima senza risposta: lo strumento duplicato
    expect(voce("Strumenti duplicati").getAttribute("aria-current")).toBe("true")
    expect(voce("Frame senza tipo").hasAttribute("aria-current")).toBe(false)
    expect(voce("Frame senza tipo").getAttribute("href")).toBe("#frame-senza-tipo")

    // risposto allo strumento e passati alla cartella, la sezione si chiude in una riga
    fireEvent.click(screen.getByRole("radio", { name: /sono distinti/i }))
    fireEvent.click(voce("Frame senza tipo"))
    expect(voce("Frame senza tipo").getAttribute("aria-current")).toBe("true")
    expect(document.querySelector("article.al-conf__colonna-16")?.getAttribute("aria-label")).toBe("D:/Astro/dark, senza risposta")
    expect(screen.queryByRole("region", { name: "Strumenti duplicati" })).toBeNull()
    // dall'indice si riapre
    fireEvent.click(voce("Strumenti duplicati"))
    expect(screen.getByRole("region", { name: "Strumenti duplicati" })).toBeDefined()
    expect(voce("Strumenti duplicati").getAttribute("aria-current")).toBe("true")
  })

  it("un'unione di strumenti in mano si dice accanto ad Applica, prima di premerlo", async () => {
    // Unire non si annulla: e' l'unica risposta della pagina che non torna indietro.
    aperta()
    await apri()
    await screen.findByRole("region", { name: "Le modifiche da applicare" })
    expect(piede()?.querySelector(".al-conf__riga-19")).toBeNull()
    const sezione = screen.getByRole("region", { name: "Strumenti duplicati" })
    fireEvent.click(within(sezione).getByRole("radio", { name: /unisci a ATR2600M/i }))
    expect(piede()?.querySelector(".al-conf__riga-19")?.textContent).toBe(
      "!Include un'unione di strumenti: non \u00e8 reversibile.",
    )
    fireEvent.click(within(sezione).getByRole("radio", { name: /sono distinti/i }))
    expect(piede()?.querySelector(".al-conf__riga-19")).toBeNull()
  })

  it("mentre legge mostra lo scheletro della pagina, e dice Caricamento", async () => {
    aperta(PAGINA, { "/api/v1/review": { stato: 200, corpo: PAGINA, attesa: new Promise(() => {}) } })
    await apri()
    const scheletro = await screen.findByRole("status", { name: "Caricamento\u2026" })
    expect(scheletro.closest(".al-conf__colonna-6")).not.toBeNull()
    expect(scheletro.textContent).toBe("Caricamento\u2026")
    expect(nav()).toBeNull()
    expect(conto()).toBeNull()
  })

  it("se non si legge lo dice, e si riprova da li'", async () => {
    aperta(PAGINA, { "/api/v1/review": { stato: 500, corpo: {} } })
    await apri()
    const avviso = (await screen.findByText("Da confermare non disponibile")).closest(".al-c-avviso__blocco-1") as HTMLElement
    const quante = () => chiamate().filter((u) => u.endsWith("/api/v1/review")).length
    const prima = quante()
    fireEvent.click(within(avviso).getByRole("button", { name: "Riprova" }))
    await waitFor(() => expect(quante()).toBeGreaterThan(prima))
  })

  it("senza niente da chiedere lo dice: niente conto, niente indice e niente piede", async () => {
    aperta(VUOTA)
    await apri()
    expect(await screen.findByText("Niente da confermare")).toBeDefined()
    expect(screen.getByText("Nessuna domanda aperta.")).toBeDefined()
    expect(conto()).toBeNull()
    expect(nav()).toBeNull()
    expect(piede()).toBeNull()
  })

  it("senza nessun frame dice da dove si comincia, e porta alle cartelle", async () => {
    // "Niente da confermare" a chi non ha ancora scelto le cartelle sarebbe vero e inutile.
    aperta({ ...VUOTA, empty: true })
    await apri()
    expect(await screen.findByText("Nessun frame in archivio.")).toBeDefined()
    expect(screen.getByText("Le domande compaiono dopo la scansione.")).toBeDefined()
    expect(screen.queryByText("Niente da confermare")).toBeNull()
    expect(conto()).toBeNull()
    expect(piede()).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: "Aggiungi cartelle" }))
    await waitFor(() => expect(window.location.pathname).toBe("/impostazioni/cartelle"))
  })

  it("senza frame ma con una domanda, la domanda si vede: le risposte ripristinate ne portano", async () => {
    aperta({ ...PAGINA, empty: true })
    await apri()
    expect(await screen.findByRole("region", { name: "Strumenti duplicati" })).toBeDefined()
    expect(screen.queryByText("Nessun frame in archivio.")).toBeNull()
  })

  it("le domande di sezioni non ancora disegnate stanno nel conto, senza indice ne' piede", async () => {
    // Il conto conta anche cio' che la pagina non disegna ancora: negarlo sarebbe falso.
    aperta({ ...VUOTA, to_confirm: 5, sections: [{ key: "undated", count: 5 }] })
    await apri()
    await waitFor(() => expect(numeroDelConto()).toBe("5"))
    expect(screen.queryByText("Niente da confermare")).toBeNull()
    expect(nav()).toBeNull()
    expect(piede()).toBeNull()
  })

  it("l'esito si legge anche quando l'Applica ha svuotato la pagina, e si chiude", async () => {
    // Strumenti duplicati e Filtri escono dall'API appena hanno risposta: l'ultima svuota la pagina.
    let finisci: () => void = () => {}
    const mappa = (pagina: unknown) => ({
      ...STANOTTE,
      "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
      "/api/v1/review/apply": {
        stato: 200,
        corpo: { ...APPLICATO, requeued: 38 },
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
    fireEvent.click(applica())
    await waitFor(() => expect(applica().getAttribute("aria-busy")).toBe("true"))
    const libera = finisci
    cambia(mappa(VUOTA))
    libera()

    const esito = (await screen.findByText("1 modifica applicata, 38 frame da rielaborare")).closest(".al-conf__riga-4") as HTMLElement
    expect(esito.getAttribute("role")).toBe("status")
    // il lavoro e' partito: niente riga sulla coda
    expect(esito.querySelector(".al-conf__testo-7")).toBeNull()
    expect(screen.getByText("Niente da confermare")).toBeDefined()
    fireEvent.click(within(esito).getByRole("button", { name: "Chiudi" }))
    expect(screen.queryByText("1 modifica applicata, 38 frame da rielaborare")).toBeNull()
  })

  it("senza frame da rielaborare l'esito non li nomina, e dice del Nessun filtro che c'era", async () => {
    aperta(PAGINA, {
      "/api/v1/review/apply": { stato: 200, corpo: { changed: 2, requeued: 0, run_started: false, none_filter_existed: true } },
    })
    await apri()
    await screen.findByRole("navigation", { name: "Sezioni" })
    rispondiLight()
    fireEvent.click(applica())
    const esito = (await screen.findByText("2 modifiche applicate")).closest(".al-conf__riga-4") as HTMLElement
    expect(esito.querySelector(".al-conf__testo-7")?.textContent).toBe(
      "\u00abNessun filtro\u00bb c'era gi\u00e0 in Attrezzatura: i frame usano quello.",
    )
  })

  it("con frame da rielaborare e il lavoro non partito, l'esito dice che sono in coda", async () => {
    aperta(PAGINA, {
      "/api/v1/review/apply": { stato: 200, corpo: { changed: 1, requeued: 12, run_started: false, none_filter_existed: false } },
    })
    await apri()
    await screen.findByRole("navigation", { name: "Sezioni" })
    rispondiLight()
    fireEvent.click(applica())
    const esito = (await screen.findByText("1 modifica applicata, 12 frame da rielaborare")).closest(".al-conf__riga-4") as HTMLElement
    expect(esito.querySelector(".al-conf__testo-7")?.textContent).toBe(
      "La rielaborazione \u00e8 in coda: parte dopo, i numeri si aggiornano da soli.",
    )
  })

  it("un rifiuto dice che niente e' stato applicato, e perche'", async () => {
    aperta(PAGINA, { "/api/v1/review/apply": { stato: 422, corpo: { detail: { code: "model_contradicts_bands" } } } })
    await apri()
    await screen.findByRole("navigation", { name: "Sezioni" })
    rispondiLight()
    fireEvent.click(applica())
    const esito = await screen.findByRole("alert")
    expect(esito.querySelector(".al-conf__testo-6")?.textContent).toBe("Modifiche non applicate")
    expect(esito.querySelector(".al-conf__testo-7")?.textContent).toMatch(/bande indicate.*Nessuna modifica salvata\.$/)
    expect(within(esito).queryByRole("button", { name: "Chiudi" })).toBeNull()
  })

  it("mentre applica indice e sezioni si spengono e il comando lo dice; applicato, l'esito si chiude", async () => {
    let finisci: () => void = () => {}
    aperta(PAGINA, {
      "/api/v1/review/apply": { stato: 200, corpo: APPLICATO, attesa: new Promise<void>((fatto) => (finisci = fatto)) },
    })
    await apri()
    await screen.findByRole("navigation", { name: "Sezioni" })
    rispondiLight()
    fireEvent.click(applica())

    // al lavoro: una risposta data adesso si perderebbe, quindi le sezioni non si toccano
    await waitFor(() => expect(applica().getAttribute("aria-busy")).toBe("true"))
    expect(applica().textContent).toBe("Applicazione in corso\u2026")
    expect(applica().querySelector(".al-conf__tondo-6")).not.toBeNull()
    const sezioni = document.querySelector(".al-conf__colonna-11") as HTMLElement
    expect(sezioni.hasAttribute("inert")).toBe(true)
    expect(sezioni.getAttribute("aria-disabled")).toBe("true")
    const indiceSpento = nav() as HTMLElement
    expect(indiceSpento.getAttribute("aria-disabled")).toBe("true")
    expect(indiceSpento.style.opacity).toBe("0.45")
    expect(indiceSpento.style.pointerEvents).toBe("none")

    finisci()
    const esito = (await screen.findByText("1 modifica applicata, 320 frame da rielaborare")).closest(".al-conf__riga-4") as HTMLElement
    expect(applica().hasAttribute("aria-busy")).toBe(false)
    fireEvent.click(within(esito).getByRole("button", { name: "Chiudi" }))
    expect(screen.queryByText("1 modifica applicata, 320 frame da rielaborare")).toBeNull()
  })

  it("dall'indirizzo si entra in una sezione: ?sezione=siti apre i frame senza sito", async () => {
    aperta({
      ...PAGINA,
      unclear: [
        postoIgnoto({ key: "45.85,11.58", latitude: 45.85, longitude: 11.58, distance_km: 16.2, frames: 391, nights: ["2024-05-17"], candidates: [{ id: 1, name: "Casa", distance_km: 16.2 }] }),
      ],
    })
    await apri("/da-confermare?sezione=siti")
    const voce = within(await screen.findByRole("navigation", { name: "Sezioni" })).getByRole("link", { name: /^Frame senza sito/ })
    expect(voce.getAttribute("aria-current")).toBe("true")
    expect(document.querySelector("article.al-conf__colonna-16")?.closest("section")?.id).toBe("frame-senza-sito")
  })

  it("dall'indirizzo si entra nei frame senza data: ?sezione=senza-data", async () => {
    aperta({ ...PAGINA, undated: [cartellaSenzaData({ key: "D:/Astro/senza-data", frames: 12 })] })
    await apri("/da-confermare?sezione=senza-data")
    const voce = within(await screen.findByRole("navigation", { name: "Sezioni" })).getByRole("link", { name: /^Frame senza data/ })
    expect(voce.getAttribute("aria-current")).toBe("true")
    expect(document.querySelector("article.al-conf__colonna-16")?.closest("section")?.id).toBe(voce.getAttribute("href")?.slice(1))
  })
})
