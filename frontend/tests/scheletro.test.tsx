// @vitest-environment jsdom
/**
 * Il telaio v76 (tavola `Telaio`, `Menu`, `DaConfermare`; contratto in
 * `docs/domini/navigazione.md`): le pillole delle pagine, il menu Altro, Da confermare col suo
 * pannello, l'ingranaggio con la scansione, e sul telefono la testa e la bolla di vetro.
 *
 * Le regole provate qui sono quelle che una lettura del codice non prende: che l'ordine venga da
 * `pagine.tsx`, che una voce senza pagina dica che arriva, che il verbo e la percentuale della
 * scansione vengano dal backend, e che cio' che si apre si chiuda e restituisca il fuoco.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { FERMO, SALUTE, STANOTTE, cambia, chiamate, disegna, impostazioni, pulisci, rispondi, scritture, vai } from "./banco"
import { ALTRO_TELEFONO, PAGINE } from "../src/pagine"
import { t } from "../src/i18n"

afterEach(pulisci)

const SEZIONI = [
  { key: "filters", count: 1 },
  { key: "objects", count: 2 },
]

function mappa(pipeline: unknown = FERMO, scan: unknown = { started: [{ run_id: 1, folder_id: 1 }], skipped: [] }) {
  return {
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 12, sections: SEZIONI } },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/pipeline/status": { stato: 200, corpo: pipeline },
    "/api/v1/scan": { stato: 202, corpo: scan },
    "/api/v1/pipeline/stop": { stato: 200, corpo: { skipped: [] } },
    "/api/v1/pipeline/run": { stato: 202, corpo: { skipped: [] } },
  }
}

function app(pipeline: unknown = FERMO) {
  rispondi(mappa(pipeline))
}

const EVENTO = {
  current: 3412,
  total: 18430,
  file: "x.fits",
  run_id: 1,
  folder_id: 1,
  found: 0,
  new: 0,
  unchanged: 0,
  duplicates: 0,
  missing: 0,
  skipped: 0,
  errors: 0,
  online_only: 0,
}

const AL_LAVORO = {
  ...FERMO,
  action: "stop",
  worker: {
    ...FERMO.worker,
    state: "running",
    stage: "scan",
    stages: [{ name: "scan", state: "running", current: 3412, total: 18430, tally: {}, reason: null, pct: 19 }],
  },
  scan: { state: "running", folder_id: 1, run_id: 1, last_event: EVENTO, receipt: null, remaining_s: 4800, first: false },
}

const INTERROTTA = {
  ...AL_LAVORO,
  action: "resume",
  worker: { ...AL_LAVORO.worker, state: "idle", ended_at: "2026-09-30T07:40:00Z" },
  scan: { ...AL_LAVORO.scan, state: "stopped", remaining_s: null },
}

const BLOCCATA = {
  ...AL_LAVORO,
  action: "start",
  worker: { ...AL_LAVORO.worker, state: "error", ended_at: "2026-09-30T07:52:00Z" },
  scan: { ...AL_LAVORO.scan, state: "completed", remaining_s: null },
}

const pillole = () => screen.findByRole("navigation", { name: "Navigazione principale" })
const ingranaggio = () => screen.findByRole("link", { name: /^impostazioni( · .*)?$/i })

async function apriIngranaggio() {
  fireEvent.click(await ingranaggio())
  return screen.findByRole("menu", { name: "Impostazioni" })
}

describe("le pillole e il menu Altro", () => {
  it("le pillole stanno nell'ordine di pagine.tsx, e la pagina aperta e' accesa", async () => {
    app()
    await disegna()
    const barra = await pillole()
    const voci = within(barra).getAllByRole("link").filter((a) => a.getAttribute("aria-haspopup") === null)
    expect(voci.map((a) => a.getAttribute("href"))).toEqual(PAGINE.filter((p) => p.posto === "pillole").map((p) => p.a))
    expect(voci.map((a) => a.textContent)).toEqual(["Dashboard", "Notti", "Archivio", "Progetti", "Statistiche", "Meteo"])
    expect(voci.filter((a) => a.getAttribute("aria-current") === "page").map((a) => a.getAttribute("href"))).toEqual(["/"])
  })

  it("Altro apre le quattro pagine coi loro sottotitoli, col fuoco sulla prima; le frecce girano", async () => {
    app()
    await disegna()
    const altro = within(await pillole()).getByRole("link", { name: "Altro" })
    expect(altro.getAttribute("aria-haspopup")).toBe("menu")
    expect(altro.getAttribute("aria-expanded")).toBe("false")

    fireEvent.click(altro)
    expect(altro.getAttribute("aria-expanded")).toBe("true")
    const menu = await screen.findByRole("menu", { name: "Altre pagine" })
    const voci = within(menu).getAllByRole("menuitem")
    expect(voci.map((v) => v.getAttribute("href"))).toEqual(["/piano-della-notte", "/planner", "/selezione-dei-frame", "/attrezzatura"])
    expect(voci[0]?.textContent).toBe("Piano della nottecosa si fa stanotte, in che ordine")
    await waitFor(() => expect(document.activeElement).toBe(voci[0]))

    fireEvent.keyDown(document.activeElement as Element, { key: "ArrowDown" })
    expect(document.activeElement).toBe(voci[1])
    fireEvent.keyDown(document.activeElement as Element, { key: "ArrowUp" })
    fireEvent.keyDown(document.activeElement as Element, { key: "ArrowUp" })
    expect(document.activeElement).toBe(voci[3])
  })

  it("Esc chiude il menu e riporta il fuoco su Altro; un clic fuori lo chiude", async () => {
    app()
    await disegna()
    const altro = within(await pillole()).getByRole("link", { name: "Altro" })
    fireEvent.click(altro)
    const menu = await screen.findByRole("menu", { name: "Altre pagine" })
    await waitFor(() => expect(menu.contains(document.activeElement)).toBe(true))
    fireEvent.keyDown(document.activeElement as Element, { key: "Escape" })
    expect(screen.queryByRole("menu")).toBeNull()
    expect(document.activeElement).toBe(altro)

    fireEvent.click(altro)
    await screen.findByRole("menu", { name: "Altre pagine" })
    fireEvent.mouseDown(document.body)
    expect(screen.queryByRole("menu")).toBeNull()
  })

  it("una voce senza pagina apre la pagina che dice che sta arrivando", async () => {
    // Ogni voce del disegno si vede (Marco, 7/10/2026): chi la apre legge che la pagina arriva.
    app()
    await disegna()
    const senza = PAGINE.filter((p) => p.elemento === undefined)
    expect(senza.map((p) => p.a)).toEqual(["/progetti", "/statistiche", "/piano-della-notte", "/planner", "/selezione-dei-frame"])
    for (const p of senza) {
      if (p.posto === "altro") {
        fireEvent.click(within(await pillole()).getByRole("link", { name: "Altro" }))
        fireEvent.click(await screen.findByRole("menuitem", { name: new RegExp(`^${t(p.chiave)}`) }))
      } else {
        fireEvent.click(within(await pillole()).getByRole("link", { name: t(p.chiave) }))
      }
      const corpo = await screen.findByRole("main")
      expect(await within(corpo).findByText(`${t(p.chiave)}: non ancora disponibile`)).toBeDefined()
      expect(window.location.pathname).toBe(p.a)
      // cambiata la pagina, il menu e' chiuso
      expect(screen.queryByRole("menu")).toBeNull()
    }
  })

  it("la Carta del cielo non e' piu' una pagina: vive nel Planner", async () => {
    app()
    await disegna()
    vai("/carta-del-cielo")
    expect(await within(await screen.findByRole("main")).findByText(/^pagina non trovata$/i)).toBeDefined()
  })
})

describe("Da confermare", () => {
  it("la pillola dice quante domande aspettano e apre le sezioni con Rispondi", async () => {
    app()
    await disegna()
    const pillola = await screen.findByRole("link", { name: "Da confermare, 12" })
    expect(pillola.textContent).toBe("Da confermare12")
    expect(pillola.getAttribute("aria-haspopup")).toBe("dialog")

    fireEvent.click(pillola)
    expect(pillola.getAttribute("aria-expanded")).toBe("true")
    const pannello = await screen.findByRole("dialog", { name: "Da confermare" })
    expect(pannello.querySelector(".al-c-da-confermare__riga-1")?.textContent).toBe("12da confermare")
    const sezioni = within(within(pannello).getByRole("list", { name: "Sezioni" })).getAllByRole("listitem")
    expect(sezioni.map((s) => s.querySelector(".al-c-da-confermare__colonna-3")?.textContent)).toEqual(["Filtri1 domanda", "Oggetti2 domande"])
    const rispondi = within(pannello).getByRole("link", { name: "Rispondi: Filtri" })
    expect(rispondi.textContent).toBe("Rispondi")
    expect(rispondi.getAttribute("href")).toBe("/da-confermare#filtri")

    fireEvent.keyDown(rispondi, { key: "Escape" })
    expect(screen.queryByRole("dialog", { name: "Da confermare" })).toBeNull()
    expect(document.activeElement).toBe(pillola)
  })

  it("senza domande la pillola resta, senza numero", async () => {
    rispondi({ ...mappa(), "/api/v1/review": { stato: 200, corpo: { to_confirm: 0, sections: [] } } })
    await disegna()
    const pillola = await screen.findByRole("link", { name: "Da confermare" })
    expect(pillola.textContent).toBe("Da confermare")
  })

  it("quando il lavoro finisce, il conto si rilegge", async () => {
    // Trovato dal vivo: dopo una scansione erano entrati 18 frame e la barra diceva ancora il
    // conto di prima, finche' non si ricaricava la pagina a mano.
    app({ ...FERMO, worker: { ...FERMO.worker, state: "running", stage: "scan" } })
    await disegna()
    await screen.findByRole("link", { name: "Da confermare, 12" })
    const prima = chiamate().filter((u) => u.endsWith("/api/v1/review")).length

    cambia({
      ...mappa({ ...FERMO, worker: { ...FERMO.worker, state: "completed", ended_at: "2026-09-16T10:00:00Z" } }),
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 40, sections: SEZIONI } },
    })

    // il battito dello stato mentre gira e' 1,5 s: si aspetta quello, non un tempo inventato
    expect(await screen.findByRole("link", { name: "Da confermare, 40" }, { timeout: 5000 })).toBeDefined()
    expect(chiamate().filter((u) => u.endsWith("/api/v1/review")).length).toBeGreaterThan(prima)
  })
})

describe("l'ingranaggio e la scansione", () => {
  it("a riposo apre Scansiona con l'ultima scansione, e Tutte le impostazioni", async () => {
    app({ ...FERMO, last_scan: { ended_at: "2026-09-30T05:12:00Z", new: 214, not_read: 0 } })
    await disegna()
    expect((await ingranaggio()).getAttribute("aria-label")).toBe("Impostazioni")
    const menu = await apriIngranaggio()
    expect(within(menu).queryByRole("group", { name: "Scansione" })).toBeNull()
    const [scansiona, tutte] = within(menu).getAllByRole("menuitem")
    expect(scansiona?.textContent).toMatch(/^Scansionaultima scansione .+, .+ · 214 file nuovi, nessun problema$/)
    expect(tutte?.textContent).toBe("Tutte le impostazionisiti, tema, cartelle, servizi")
    expect(tutte?.getAttribute("href")).toBe("/impostazioni")
    expect(within(menu).queryByText(/modo automatico/i)).toBeNull()
  })

  it("l'ultima scansione senza file nuovi e con file non letti lo dice", async () => {
    app({ ...FERMO, last_scan: { ended_at: "2026-09-30T05:12:00Z", new: 0, not_read: 1 } })
    await disegna()
    const menu = await apriIngranaggio()
    expect(within(menu).getAllByRole("menuitem")[0]?.textContent).toMatch(/ · nessun file nuovo · 1 file non letto$/)
  })

  it("premere Scansiona chiede di leggere TUTTE le cartelle", async () => {
    // Il gesto non chiede quale cartella: e' uno solo, e il backend le legge tutte.
    app()
    await disegna()
    const menu = await apriIngranaggio()
    fireEvent.click(within(menu).getByRole("menuitem", { name: /^Scansiona/ }))
    await waitFor(() => expect(scritture().some((s) => s.url.endsWith("/api/v1/scan"))).toBe(true))
    expect(scritture().find((s) => s.url.endsWith("/api/v1/scan"))?.corpo).toBeNull()
  })

  it("in corso l'ingranaggio lo dice, e il menu porta fase, barra, file letti e Interrompi anche da un'altra pagina", async () => {
    // Il lavoro sopravvive alla pagina: deve restare visibile e fermabile dovunque tu vada.
    app(AL_LAVORO)
    await disegna()
    vai("/progetti")
    expect((await screen.findByRole("link", { name: "Impostazioni · scansione in corso" })).querySelector("[aria-hidden]")).not.toBeNull()
    const menu = await apriIngranaggio()
    const riquadro = within(menu).getByRole("group", { name: "Scansione" })
    expect(within(riquadro).getByText("Scansione in corso")).toBeDefined()
    expect(within(riquadro).getByText("Lettura dei file")).toBeDefined()
    // la barra e' un disegno (ARIA non ammette un progressbar in un menu): i numeri li dice la riga
    expect((riquadro.querySelector(".al-c-menu__pillola-1") as HTMLElement).style.width).toBe("19%")
    expect(riquadro.querySelector(".al-c-menu__testo-3")?.textContent).toBe("file letti 3412 su 18 430 · ancora circa 1 h 20")
    // a scansione accesa il riquadro prende il posto di Scansiona
    expect(within(menu).queryByRole("menuitem", { name: /^Scansiona/ })).toBeNull()
    fireEvent.click(within(riquadro).getByRole("menuitem", { name: "Interrompi" }))
    await waitFor(() => expect(scritture().some((s) => s.url.endsWith("/api/v1/pipeline/stop"))).toBe(true))
  })

  it("la percentuale della barra e' quella del backend, non un conto suo", async () => {
    app({ ...AL_LAVORO, worker: { ...AL_LAVORO.worker, stages: [{ ...AL_LAVORO.worker.stages[0], current: 1, total: 2, pct: 37 }] } })
    await disegna()
    const menu = await apriIngranaggio()
    const pieno = menu.querySelector(".al-c-menu__pillola-1") as HTMLElement
    expect(pieno.style.width).toBe("37%")
  })

  it("interrotta: il segno, l'ora, quanto ha letto e Riprendi", async () => {
    app(INTERROTTA)
    await disegna()
    expect(await screen.findByRole("link", { name: "Impostazioni · scansione interrotta" })).toBeDefined()
    const riquadro = within(await apriIngranaggio()).getByRole("group", { name: "Scansione" })
    expect(within(riquadro).getByText("! Scansione interrotta")).toBeDefined()
    expect(riquadro.querySelector(".al-c-menu__testo-3")?.textContent).toBe("Interrotta a mano: 3412 file letti su 18 430. Riprende da dove si era fermata.")
    fireEvent.click(within(riquadro).getByRole("menuitem", { name: "Riprendi" }))
    await waitFor(() => expect(scritture().some((s) => s.url.endsWith("/api/v1/pipeline/run"))).toBe(true))
  })

  it("bloccata: dice perche', porta ai Dettagli e si fa ripartire", async () => {
    app(BLOCCATA)
    await disegna()
    expect(await screen.findByRole("link", { name: "Impostazioni · scansione bloccata" })).toBeDefined()
    const riquadro = within(await apriIngranaggio()).getByRole("group", { name: "Scansione" })
    expect(within(riquadro).getByText("! Scansione bloccata")).toBeDefined()
    expect(riquadro.querySelector(".al-c-menu__riga-2")).toBeNull()
    expect(riquadro.querySelector(".al-c-menu__testo-3")?.textContent).toBe(
      "Scansione interrotta da un errore. 3412 file letti su 18 430.",
    )
    expect(within(riquadro).getByRole("menuitem", { name: "Dettagli" }).getAttribute("href")).toBe("/impostazioni/letture")
    fireEvent.click(within(riquadro).getByRole("menuitem", { name: "Riprova" }))
    await waitFor(() => expect(scritture().some((s) => s.url.endsWith("/api/v1/scan"))).toBe(true))
  })

  it("bloccata da una cartella persa: la colpa va alla cartella solo se la lettura e' caduta", async () => {
    app({ ...BLOCCATA, scan: { ...BLOCCATA.scan, state: "error" } })
    await disegna()
    const riquadro = within(await apriIngranaggio()).getByRole("group", { name: "Scansione" })
    expect(riquadro.querySelector(".al-c-menu__testo-3")?.textContent).toBe(
      "Lettura di una cartella non completata. Controlla il disco e riprova. 3412 file letti su 18 430.",
    )
  })

  it("una cartella persa mentre la leggeva si dice in testa al corpo", async () => {
    // Il NAS che si spegne DOPO l'avvio non sta fra le saltate: senza questa riga l'utente
    // leggerebbe "fatto" con una cartella non letta.
    app({ ...FERMO, scan: { state: "error", folder_id: 2, run_id: 3, last_event: null, receipt: null } })
    await disegna()
    const corpo = await screen.findByRole("main")
    const riga = (await within(corpo).findByText(/Lettura di una cartella non completata/)).closest(".as-avviso") as HTMLElement
    expect(riga.classList.contains("as-avviso--pagina")).toBe(true)
    expect(within(riga).getByRole("link", { name: "Dettagli" }).getAttribute("href")).toBe("/impostazioni/letture")
  })

  it("le cartelle saltate si dicono, non si buttano", async () => {
    rispondi(
      mappa(FERMO, {
        started: [{ run_id: 1, folder_id: 1 }],
        skipped: [{ folder_id: 2, root_path: "//nas/foto", reason: "root_unreachable" }],
      }),
    )
    await disegna()
    fireEvent.click(within(await apriIngranaggio()).getByRole("menuitem", { name: /^Scansiona/ }))
    const corpo = await screen.findByRole("main")
    const riga = (await within(corpo).findByText(/\/\/nas\/foto/)).closest(".as-avviso") as HTMLElement
    expect(riga.classList.contains("as-avviso--pagina")).toBe(true)
    expect(within(riga).getByRole("link", { name: "Dettagli" }).getAttribute("href")).toBe("/impostazioni/cartelle")
  })

  it("Dettagli porta alle Cartelle solo quando il rifiuto e' delle cartelle", async () => {
    // "C'e' gia' un lavoro in corso" non si ripara nelle Cartelle.
    rispondi({ ...mappa(), "/api/v1/scan": { stato: 409, corpo: { detail: { code: "worker_busy" } } } })
    await disegna()
    fireEvent.click(within(await apriIngranaggio()).getByRole("menuitem", { name: /^Scansiona/ }))
    const occupato = (await within(await screen.findByRole("main")).findByText(/Operazione già in corso/)).closest(".as-avviso") as HTMLElement
    expect(within(occupato).queryByRole("link", { name: "Dettagli" })).toBeNull()
    pulisci()

    rispondi({ ...mappa(), "/api/v1/scan": { stato: 409, corpo: { detail: { code: "no_folders" } } } })
    await disegna()
    fireEvent.click(within(await apriIngranaggio()).getByRole("menuitem", { name: /^Scansiona/ }))
    const senza = (await within(await screen.findByRole("main")).findByText(/Nessuna cartella da leggere/)).closest(".as-avviso") as HTMLElement
    expect(within(senza).getByRole("link", { name: "Dettagli" }).getAttribute("href")).toBe("/impostazioni/cartelle")
  })
})

describe("il telaio del telefono", () => {
  function telefono(pipeline: unknown = FERMO, dove = "/") {
    window.history.pushState({}, "", `${dove}?formato=telefono`)
    app(pipeline)
    return disegna()
  }
  const bolla = () => screen.findByRole("navigation", { name: "Pagine dell'app" })

  it("la testa dice la pagina e porta a Da confermare e a Cerca", async () => {
    await telefono()
    const testa = await screen.findByRole("banner")
    expect(testa.querySelector(".al-c-telaio__riga-12 b")?.textContent).toBe("Dashboard")
    const conferma = await within(testa).findByRole("link", { name: "Da confermare, 12" })
    expect(conferma.getAttribute("href")).toBe("/da-confermare")
    expect(within(testa).getByRole("link", { name: "Cerca" }).getAttribute("aria-haspopup")).toBe("dialog")
    expect(screen.queryByRole("navigation", { name: "Navigazione principale" })).toBeNull()
  })

  it("la bolla chiusa mostra la pagina; toccata apre le cinque schede", async () => {
    await telefono()
    const nav = await bolla()
    const qui = within(nav).getByRole("link", { name: "Dashboard: mostra le pagine dell'app" })
    expect(qui.getAttribute("aria-current")).toBe("page")
    expect(qui.getAttribute("aria-expanded")).toBe("false")
    // chiusa, le altre schede non si raggiungono
    expect(within(nav).getAllByRole("link").map((a) => a.getAttribute("aria-label"))).toEqual(["Dashboard: mostra le pagine dell'app"])

    fireEvent.click(qui)
    const schede = within(nav).getAllByRole("link")
    expect(schede.map((a) => a.textContent)).toEqual(["Dashboard", "Notti", "Archivio", "Meteo", "Altro"])
    expect(schede[1]?.getAttribute("href")).toBe("/notti")
    fireEvent.scroll(window)
    expect(within(nav).getAllByRole("link")).toHaveLength(1)
  })

  it("una pagina fuori dalle cinque e' la sesta scheda", async () => {
    await telefono(FERMO, "/progetti")
    const nav = await bolla()
    const qui = within(nav).getByRole("link", { name: "Progetti: mostra le pagine dell'app" })
    expect(qui.getAttribute("aria-current")).toBe("page")
    expect((await screen.findByRole("banner")).querySelector(".al-c-telaio__riga-12 b")?.textContent).toBe("Progetti")
  })

  it("Altro apre le sette pagine e la scansione se c'e'; niente modo chiaro", async () => {
    await telefono(AL_LAVORO)
    const nav = await bolla()
    fireEvent.click(within(nav).getByRole("link", { name: "Dashboard: mostra le pagine dell'app" }))
    const altro = within(nav).getByRole("link", { name: "Altro · scansione in corso" })
    fireEvent.click(altro)
    const menu = await screen.findByRole("menu", { name: "Altre pagine" })
    expect(within(menu).getAllByRole("menuitem").filter((v) => v.getAttribute("href") !== "#").map((v) => v.getAttribute("href"))).toEqual([...ALTRO_TELEFONO])
    expect(within(menu).getByRole("group", { name: "Scansione" })).toBeDefined()
    expect(within(menu).queryByText(/modo chiaro/i)).toBeNull()
    fireEvent.keyDown(document.activeElement ?? document.body, { key: "Escape" })
    expect(screen.queryByRole("menu")).toBeNull()
  })
})
