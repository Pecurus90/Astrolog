// @vitest-environment jsdom
/**
 * Lo scheletro nel telaio (ADR 0018): il binario delle pagine, la barra in alto col titolo e la
 * scansione, e il foglio "Altro" del telefono.
 *
 * Il contratto sta in `docs/domini/navigazione.md`. Le regole che si provano qui sono quelle
 * che una lettura del codice non prende: che l'ordine delle voci sia quello di `pagine.tsx`, che
 * una voce senza pagina dica che arriva invece di sparire, e che il verbo del pulsante venga dal
 * backend e non da qui.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { FERMO, SALUTE, STANOTTE, cambia, chiamate, disegna, impostazioni, pulisci, rispondi, scritture } from "./banco"
import { PAGINE } from "../src/pagine"
import { t } from "../src/i18n"

afterEach(pulisci)

function mappa(pipeline: unknown = FERMO, scan: unknown = { started: [{ run_id: 1, folder_id: 1 }], skipped: [] }) {
  return {
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": {
      stato: 200,
      corpo: { to_confirm: 12 },
    },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/pipeline/status": { stato: 200, corpo: pipeline },
    "/api/v1/scan": { stato: 202, corpo: scan },
  }
}

function app(pipeline: unknown = FERMO) {
  rispondi(mappa(pipeline))
}

const AL_LAVORO = {
  ...FERMO,
  action: "stop",
  worker: {
    ...FERMO.worker,
    state: "running",
    stage: "scan",
    stages: [{ name: "scan", state: "running", current: 3, total: 14, tally: {}, reason: null }],
  },
}

describe("lo scheletro", () => {
  it("le voci del binario stanno nell ordine di pagine.tsx", async () => {
    // L'ordine e' quello del disegno, e il binario lo legge da una fonte sola: se ne avesse una
    // sua, un riordino in `pagine.tsx` non arriverebbe a schermo e questa cadrebbe.
    app()
    await disegna()
    const binario = await screen.findByRole("navigation", { name: /pagine/i })
    const voci = within(binario)
      .getAllByRole("link")
      .map((a) => a.getAttribute("href"))
    // prima il binario, poi la coda: e' l'ordine in cui `PAGINE` le dichiara
    const attese = [...PAGINE.filter((p) => !p.coda), ...PAGINE.filter((p) => p.coda)].map((p) => p.a)
    expect(voci).toEqual(attese)
    expect(attese).toEqual([
      "/",
      "/notti",
      "/archivio",
      "/progetti",
      "/statistiche",
      "/attrezzatura",
      "/planner",
      "/carta-del-cielo",
      "/meteo",
      "/da-confermare",
      "/impostazioni",
    ])
  })

  it("la voce della pagina aperta e' accesa, e solo lei", async () => {
    // `aria-current` e' cio' che dice a chi ascolta dove si trova, e cio' su cui il foglio accende
    // la voce: un sotto-indirizzo deve accendere la pagina che lo contiene.
    window.history.pushState({}, "", "/impostazioni/cartelle")
    rispondi({ ...mappa(), "/api/v1/folders": { stato: 200, corpo: { items: [], total: 0 } } })
    await disegna()
    const binario = await screen.findByRole("navigation", { name: /pagine/i })
    const accese = within(binario)
      .getAllByRole("link")
      .filter((a) => a.getAttribute("aria-current") === "page")
    expect(accese.map((a) => a.getAttribute("href"))).toEqual(["/impostazioni"])
  })

  it("il lavoro si vede e si ferma anche da un altra pagina", async () => {
    // E' **la** ragione per cui il pulsante sta in alto e non dentro una pagina: il lavoro
    // sopravvive alla pagina, quindi deve restare visibile e fermabile dovunque tu vada. E
    // "fermabile" si prova fermandolo: dei tre verbi, altrimenti, se ne preme uno solo.
    app(AL_LAVORO)
    await disegna()
    fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
    const alto = await screen.findByRole("banner")
    expect(await within(alto).findByRole("heading", { level: 1, name: "Da confermare" })).toBeDefined()
    // "si vede" e' meta' della promessa: la fase e i suoi numeri devono essere li' anche qui
    expect(await within(alto).findByText(/leggo i file/)).toBeDefined()
    expect(within(alto).getByText(/3 su 14/)).toBeDefined()

    fireEvent.click(within(alto).getByRole("button", { name: "Ferma" }))
    await waitFor(() =>
      expect(scritture().some((s) => s.url.endsWith("/api/v1/pipeline/stop"))).toBe(true),
    )
  })

  it("bloccata, la scansione dice perche' e si fa ripartire dalla barra", async () => {
    // Dopo un errore il backend chiede `start`: senza il verbo in barra, sul desktop non resta
    // nessun punto da cui far ripartire il lavoro.
    app({ ...FERMO, action: "start", worker: { ...FERMO.worker, state: "error", error: "solver assente" } })
    await disegna()
    const alto = await screen.findByRole("banner")
    expect(await within(alto).findByText("solver assente")).toBeDefined()
    expect(within(alto).getByRole("link", { name: "Vedi" }).getAttribute("href")).toBe("/impostazioni/letture")
    fireEvent.click(within(alto).getByRole("button", { name: "Scansiona" }))
    await waitFor(() => expect(scritture().some((s) => s.url.endsWith("/api/v1/scan"))).toBe(true))
  })

  it("una cartella persa mentre la leggeva si dice", async () => {
    // Il caso che il pre-controllo non prende: il NAS che si spegne DOPO l'avvio. Non e' fra le
    // saltate, e senza questa riga l'utente leggerebbe "fatto" con una cartella non letta. La
    // riga porta dove si guarda la ricevuta.
    app({
      ...FERMO,
      scan: { state: "error", folder_id: 2, run_id: 3, last_event: null, receipt: null },
    })
    await disegna()
    const corpo = await screen.findByRole("main")
    const testo = await within(corpo).findByText(/non si e' potuta leggere fino in fondo/)
    const riga = testo.closest(".as-avviso") as HTMLElement
    expect(riga.classList.contains("as-avviso--pagina")).toBe(true)
    expect(within(riga).getByRole("link", { name: "Vedi" }).getAttribute("href")).toBe("/impostazioni/letture")
  })

  it("le cartelle saltate si dicono, non si buttano", async () => {
    // Il backend le manda con il loro perche'. Tacerle farebbe sembrare completa una scansione
    // che non lo e': con un NAS spento fra tre cartelle, l'utente crederebbe di aver letto tutto.
    rispondi(
      mappa(FERMO, {
        started: [{ run_id: 1, folder_id: 1 }],
        skipped: [{ folder_id: 2, root_path: "//nas/foto", reason: "root_unreachable" }],
      }),
    )
    await disegna()
    fireEvent.click(await screen.findByRole("button", { name: "Scansiona" }))
    const corpo = await screen.findByRole("main")
    const testo = await within(corpo).findByText(/\/\/nas\/foto/)
    const riga = testo.closest(".as-avviso") as HTMLElement
    expect(riga.classList.contains("as-avviso--pagina")).toBe(true)
    expect(within(riga).getByRole("link", { name: "Vedi" }).getAttribute("href")).toBe("/impostazioni/cartelle")
  })

  it("Vedi porta alle Cartelle solo quando il rifiuto e' delle cartelle", async () => {
    // "C'e' gia' un lavoro in corso" non si ripara nelle Cartelle: mandarci l'utente vorrebbe
    // dire fargli cercare un guasto dove non c'e'.
    rispondi({ ...mappa(), "/api/v1/scan": { stato: 409, corpo: { detail: { code: "worker_busy" } } } })
    await disegna()
    fireEvent.click(await screen.findByRole("button", { name: "Scansiona" }))
    const corpo = await screen.findByRole("main")
    const occupato = (await within(corpo).findByText(/gia' un lavoro in corso/)).closest(".as-avviso") as HTMLElement
    expect(within(occupato).queryByRole("link", { name: "Vedi" })).toBeNull()
    pulisci()

    rispondi({ ...mappa(), "/api/v1/scan": { stato: 409, corpo: { detail: { code: "no_folders" } } } })
    await disegna()
    fireEvent.click(await screen.findByRole("button", { name: "Scansiona" }))
    const senza = (await within(await screen.findByRole("main")).findByText(/nessuna cartella da leggere/)).closest(
      ".as-avviso",
    ) as HTMLElement
    expect(within(senza).getByRole("link", { name: "Vedi" }).getAttribute("href")).toBe("/impostazioni/cartelle")
  })

  it("una voce senza pagina apre la pagina che dice che sta arrivando", async () => {
    // Ogni voce del disegno si vede (Marco, 7/10/2026): chi la apre legge che la pagina arriva,
    // invece di un vuoto muto o di una voce che sparisce.
    app()
    await disegna()
    const binario = await screen.findByRole("navigation", { name: /pagine/i })
    const senza = PAGINE.filter((p) => p.elemento === undefined)
    expect(senza.length).toBeGreaterThan(0)
    for (const p of senza) {
      fireEvent.click(within(binario).getByRole("link", { name: t(p.chiave) }))
      const corpo = await screen.findByRole("main")
      expect(
        await within(corpo).findByText(`${t(p.chiave)} sta arrivando`),
      ).toBeDefined()
      expect(window.location.pathname).toBe(p.a)
    }
  })

  it("accanto a Da confermare c e quante cose aspettano", async () => {
    app()
    await disegna()
    const binario = await screen.findByRole("navigation", { name: /pagine/i })
    // `find`, non `get`: il numero arriva dall'API e il binario si disegna prima che risponda.
    // E si guarda **dentro la sua voce**: cercandolo in tutto il binario, il numero potrebbe
    // finire accanto a un'altra pagina e la prova resterebbe verde.
    const voce = await within(binario).findByRole("link", { name: /12 casi da confermare/ })
    expect(voce.getAttribute("href")).toBe("/da-confermare")
    // il numero si vede, e chi ascolta lo sente per intero
    expect(within(voce).getByLabelText("12 casi da confermare").textContent).toBe("12")
  })

  it("la barra in alto dice che pagina stai guardando", async () => {
    app()
    await disegna()
    // Sul telefono il binario e' in basso e senza nomi lunghi: questo e' il posto che lo dice.
    const alto = await screen.findByRole("banner")
    expect(within(alto).getByRole("heading", { level: 1 }).textContent).toBe("Dashboard")
  })

  it("il verbo del pulsante lo decide il backend, non la pagina", async () => {
    // `action` arriva dallo stato: se lo decidesse il frontend sarebbe lo stesso fatto in due
    // case, ed e' l'errore che il vecchio aveva fatto.
    app({ ...FERMO, action: "stop", worker: { ...FERMO.worker, state: "running", stage: "solve" } })
    await disegna()
    expect(await screen.findByRole("button", { name: "Ferma" })).toBeDefined()
    expect(screen.queryByRole("button", { name: "Scansiona" })).toBeNull()
  })

  it("mentre gira si legge cosa sta facendo, coi numeri veri", async () => {
    app({
      ...FERMO,
      action: "stop",
      worker: {
        ...FERMO.worker,
        state: "running",
        stage: "solve",
        stages: [
          { name: "solve", state: "running", current: 120, total: 337, tally: {}, reason: null },
        ],
      },
    })
    await disegna()
    const alto = await screen.findByRole("banner")
    expect(await within(alto).findByText(/cerco il cielo/)).toBeDefined()
    expect(await within(alto).findByText(/120 su 337/)).toBeDefined()
  })

  it("quando il lavoro finisce, il conto si rilegge", async () => {
    // Trovato dal vivo: dopo una scansione erano entrati 18 frame e la barra diceva ancora
    // "0 da confermare", finche' non si ricaricava la pagina a mano. Cio' che l'app mostra
    // dopo un lavoro non puo' essere di prima del lavoro.
    app({ ...FERMO, worker: { ...FERMO.worker, state: "running", stage: "scan" } })
    await disegna()
    const binario = await screen.findByRole("navigation", { name: /pagine/i })
    await within(binario).findByRole("link", { name: /12 casi da confermare/ })
    const prima = chiamate().filter((u) => u.endsWith("/api/v1/review")).length

    cambia({
      ...STANOTTE,
      "/api/v1/pipeline/status": {
        stato: 200,
        corpo: { ...FERMO, worker: { ...FERMO.worker, state: "completed", ended_at: "2026-09-16T10:00:00Z" } },
      },
      "/api/v1/review": {
        stato: 200,
        corpo: { to_confirm: 40 },
      },
    })

    // il battito dello stato mentre gira e' 1,5 s: si aspetta quello, non un tempo inventato
    expect(
      await within(binario).findByRole("link", { name: /40 casi da confermare/ }, { timeout: 5000 }),
    ).toBeDefined()
    expect(chiamate().filter((u) => u.endsWith("/api/v1/review")).length).toBeGreaterThan(prima)
  })

  it("premere Scansiona chiede di leggere TUTTE le cartelle", async () => {
    // Il pulsante in barra non chiede quale cartella: e' un gesto solo, e il backend le legge
    // tutte. Se chiedesse una cartella sola, chi ne ha due ne scansionerebbe una per sbaglio.
    app()
    await disegna()
    fireEvent.click(await screen.findByRole("button", { name: "Scansiona" }))
    await waitFor(() => expect(scritture().some((s) => s.url.endsWith("/api/v1/scan"))).toBe(true))
    const chiamata = scritture().find((s) => s.url.endsWith("/api/v1/scan"))
    // nessun corpo che scelga una cartella
    expect(chiamata?.corpo).toBeNull()
  })
})

describe("il foglio Altro", () => {
  it("Altro apre le voci che non stanno fra le schede del telefono, ed Esc lo chiude", async () => {
    // Sul telefono il binario tiene cinque schede; le altre pagine stanno qui. Una voce che non
    // fosse ne' fra le schede ne' nel foglio sarebbe irraggiungibile da telefono.
    app()
    await disegna()
    const altro = await screen.findByRole("button", { name: /^altro/i })
    expect(altro.getAttribute("aria-expanded")).toBe("false")
    expect(screen.queryByRole("dialog", { name: "Altro" })).toBeNull()

    fireEvent.click(altro)
    expect(altro.getAttribute("aria-expanded")).toBe("true")
    const foglio = await screen.findByRole("dialog", { name: "Altro" })
    const voci = within(foglio)
      .getAllByRole("link")
      .map((a) => a.getAttribute("href"))
    expect(voci).toEqual(PAGINE.filter((p) => !p.telefono).map((p) => p.a))
    expect(voci).not.toContain("/")

    fireEvent.keyDown(foglio, { key: "Escape" })
    expect(altro.getAttribute("aria-expanded")).toBe("false")
    expect(screen.queryByRole("dialog", { name: "Altro" })).toBeNull()
  })

  it("il foglio Altro trattiene il fuoco: Tab non esce dietro il velo", async () => {
    // Si dichiara modale: chi usa un lettore di schermo sente che il resto e' inerte, quindi il
    // fuoco non deve poterci finire.
    app()
    await disegna()
    fireEvent.click(await screen.findByRole("button", { name: /^altro/i }))
    const foglio = await screen.findByRole("dialog", { name: "Altro" })
    const controlli = [...foglio.querySelectorAll<HTMLElement>("a[href], button:not([disabled])")]
    const primo = controlli[0] as HTMLElement
    const ultimo = controlli[controlli.length - 1] as HTMLElement

    ultimo.focus()
    fireEvent.keyDown(ultimo, { key: "Tab" })
    expect(document.activeElement).toBe(primo)

    // dal titolo, dove il fuoco arriva aprendo, Maiuscolo+Tab gira all'ultimo
    const titolo = within(foglio).getByRole("heading", { name: "Altro" })
    titolo.focus()
    fireEvent.keyDown(titolo, { key: "Tab", shiftKey: true })
    expect(document.activeElement).toBe(ultimo)
  })

  it("bloccata, la scansione nel foglio dice perche' e porta dove si guarda", async () => {
    // Sul telefono la barra non porta la scansione: il foglio e' l'unico posto. Senza, una
    // scansione bloccata si leggeva "ferma", senza motivo e senza Vedi.
    app({ ...FERMO, action: "start", worker: { ...FERMO.worker, state: "error", error: "solver assente" } })
    await disegna()
    fireEvent.click(await screen.findByRole("button", { name: /^altro/i }))
    const foglio = await screen.findByRole("dialog", { name: "Altro" })
    expect(await within(foglio).findByText("solver assente")).toBeDefined()
    expect(within(foglio).getByText("bloccata")).toBeDefined()
    expect(within(foglio).getByRole("link", { name: "Vedi" }).getAttribute("href")).toBe("/impostazioni/letture")
  })
})
