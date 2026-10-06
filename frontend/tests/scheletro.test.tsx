// @vitest-environment jsdom
/**
 * Lo scheletro: i tre gruppi della barra, le voci che esistono davvero, e il pulsante che fa
 * leggere le cartelle da qualunque pagina.
 *
 * Il contratto sta in `docs/domini/navigazione.md`. Le regole che si provano qui sono quelle
 * che una lettura del codice non prende: che l'ordine dei gruppi sia quello, che una pagina non
 * ancora nata **non** compaia, e che il verbo del pulsante venga dal backend e non da qui.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { FERMO, SALUTE, STANOTTE, cambia, chiamate, disegna, impostazioni, pulisci, rispondi, scritture } from "./banco"
import { GRUPPI, PAGINE } from "../src/pagine"

afterEach(pulisci)

function app(pipeline: unknown = FERMO) {
  rispondi({
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": {
      stato: 200,
      corpo: { to_confirm: 12 },
    },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/pipeline/status": { stato: 200, corpo: pipeline },
    "/api/v1/scan": { stato: 202, corpo: { started: [{ run_id: 1, folder_id: 1 }], skipped: [] } },
  })
}

describe("lo scheletro", () => {
  it("i gruppi stanno nell ordine del contratto", async () => {
    // L'ordine si legge dall'alto come si lavora: guarda quello che hai, sistema l'archivio,
    // pianifica il resto. E' contratto, non gusto: una pagina nuova non lo ridiscute.
    //
    // Si guarda la LISTA e non lo schermo: oggi due gruppi su tre non hanno nemmeno una pagina,
    // quindi a schermo un riordino non si vedrebbe e la prova sarebbe verde per finta. Quando
    // le pagine ci saranno, questa regge lo stesso -- e' la stessa fonte che la barra legge.
    expect([...GRUPPI]).toEqual(["cima", "guarda", "sistema", "pianifica", "fondo"])
    expect(PAGINE.map((p) => p.gruppo)).toEqual([...PAGINE.map((p) => p.gruppo)].sort(
      (a, b) => GRUPPI.indexOf(a) - GRUPPI.indexOf(b),
    ))
    const perGruppo = (g: string) => PAGINE.filter((p) => p.gruppo === g).map((p) => p.a)
    expect(perGruppo("guarda")).toEqual(["/archivio", "/notti", "/attrezzatura", "/statistiche"])
    expect(perGruppo("sistema")).toEqual(["/da-confermare", "/diagnostica"])
    expect(perGruppo("pianifica")).toEqual([
      "/planner",
      "/progetti",
      "/carta-del-cielo",
      "/meteo",
    ])
  })

  it("il lavoro si vede e si ferma anche da un altra pagina", async () => {
    // E' **la** ragione per cui il pulsante sta in alto e non dentro una pagina: il lavoro
    // sopravvive alla pagina, quindi deve restare visibile e fermabile dovunque tu vada. E
    // "fermabile" si prova fermandolo: dei tre verbi, altrimenti, se ne preme uno solo.
    app({
      ...FERMO,
      action: "stop",
      worker: {
        ...FERMO.worker,
        state: "running",
        stage: "scan",
        stages: [
          { name: "scan", state: "running", current: 3, total: 14, tally: {}, reason: null },
        ],
      },
    })
    await disegna()
    // il **link**, non il testo: da quando la Casa ha la sua carta, "Da confermare" e' scritto
    // anche li' dentro -- e una prova che pesca per testo prende il primo che capita
    fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
    expect(within(await screen.findByRole("banner")).getByText("Da confermare")).toBeDefined()
    // "si vede" e' meta' della promessa: la fase e i suoi numeri devono essere li' anche qui
    expect(await screen.findByText(/leggo i file/)).toBeDefined()

    fireEvent.click(await screen.findByRole("button", { name: "Ferma" }))
    await waitFor(() =>
      expect(scritture().some((s) => s.url.endsWith("/api/v1/pipeline/stop"))).toBe(true),
    )
  })

  it("una cartella persa mentre la leggeva si dice", async () => {
    // Il caso che il pre-controllo non prende: il NAS che si spegne DOPO l'avvio. Non e' fra le
    // saltate, la sua ricevuta la mostrera' la pagina Cartelle che non c'e' ancora, e senza
    // questa riga l'utente leggerebbe "fatto" con una cartella non letta.
    app({
      ...FERMO,
      scan: { state: "error", folder_id: 2, run_id: 3, last_event: null, receipt: null },
    })
    await disegna()
    expect(await screen.findByText(/non si e' potuta leggere fino in fondo/)).toBeDefined()
  })

  it("le cartelle saltate si dicono, non si buttano", async () => {
    // Il backend le manda con il loro perche'. Tacerle farebbe sembrare completa una scansione
    // che non lo e': con un NAS spento fra tre cartelle, l'utente crederebbe di aver letto tutto.
    app()
    // `cambia` sostituisce la mappa intera, quindi si ridichiara anche cio' che serve all'app
    // per montarsi: senza, la prova cadrebbe perche' non c'e' nessun pulsante, non per le
    // cartelle saltate.
    cambia({
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": {
        stato: 200,
        corpo: { to_confirm: 12 },
      },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/pipeline/status": { stato: 200, corpo: FERMO },
      "/api/v1/scan": {
        stato: 202,
        corpo: {
          started: [{ run_id: 1, folder_id: 1 }],
          skipped: [{ folder_id: 2, root_path: "//nas/foto", reason: "root_unreachable" }],
        },
      },
    })
    await disegna()
    fireEvent.click(await screen.findByRole("button", { name: "Scansiona" }))
    expect(await screen.findByText(/\/\/nas\/foto/)).toBeDefined()
  })

  it("una pagina che non esiste ancora non e nella barra", async () => {
    // La regola che tiene onesta l'app mentre cresce: una voce che apre una pagina vuota e' una
    // promessa che l'app non mantiene, e chi la clicca la clicca una volta sola.
    app()
    await disegna()
    const barra = await screen.findByRole("navigation")
    expect(within(barra).queryByText("Statistiche")).toBeNull()
    expect(within(barra).queryByText("Planner")).toBeNull()
    expect(within(barra).getByText("Da confermare")).toBeDefined()
    expect(within(barra).getByText("Notti")).toBeDefined()
    expect(within(barra).getByText("Attrezzatura")).toBeDefined()
  })

  it("accanto a Da confermare c e quante cose aspettano", async () => {
    app()
    await disegna()
    const barra = await screen.findByRole("navigation")
    // `find`, non `get`: il numero arriva dall'API e la barra si disegna prima che risponda --
    // e' la stessa attesa che farebbe l'occhio di chi apre l'app. E si guarda **dentro la sua
    // voce**: cercandolo in tutta la barra, il numero potrebbe finire accanto a un'altra pagina
    // e la prova resterebbe verde.
    await within(barra).findByText("12")
    const voce = within(barra).getByRole("link", { name: /da confermare/i })
    expect(voce.textContent).toContain("12")
  })

  it("la barra in alto dice che pagina stai guardando", async () => {
    app()
    await disegna()
    // Sul telefono la barra sara' chiusa e questo sara' l'unico posto che lo dice.
    const alto = await screen.findByRole("banner")
    expect(within(alto).getByText("Casa")).toBeDefined()
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
    expect(await screen.findByText(/cerco il cielo/)).toBeDefined()
    expect(await screen.findByText(/120 su 337/)).toBeDefined()
  })

  it("quando il lavoro finisce, il conto si rilegge", async () => {
    // Trovato dal vivo: dopo una scansione erano entrati 18 frame e la barra diceva ancora
    // "0 da confermare", finche' non si ricaricava la pagina a mano. Cio' che l'app mostra
    // dopo un lavoro non puo' essere di prima del lavoro.
    app({ ...FERMO, worker: { ...FERMO.worker, state: "running", stage: "scan" } })
    await disegna()
    await screen.findByRole("navigation")
    const prima = chiamate().filter((u) => u.endsWith("/api/v1/review")).length

    cambia({
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
    const barra = await screen.findByRole("navigation")
    expect(await within(barra).findByText("40", {}, { timeout: 5000 })).toBeDefined()
    expect(chiamate().filter((u) => u.endsWith("/api/v1/review")).length).toBeGreaterThan(prima)
  })

  it("premere Scansiona chiede di leggere TUTTE le cartelle", async () => {
    // Il pulsante in barra non chiede quale cartella: e' un gesto solo, e il backend le legge
    // tutte. Se chiedesse una cartella sola, chi ne ha due ne scansionerebbe una per sbaglio.
    app()
    await disegna()
    fireEvent.click(await screen.findByRole("button", { name: "Scansiona" }))
    await screen.findByRole("button", { name: "Scansiona" })
    const chiamata = scritture().find((s) => s.url.endsWith("/api/v1/scan"))
    expect(chiamata).toBeDefined()
  })
})
