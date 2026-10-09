// @vitest-environment jsdom
/**
 * Impostazioni: la pagina a sezioni, e la sezione Cartelle.
 *
 * Qui si provano le regole che una lettura del codice non prende: che un **sotto-indirizzo** sia
 * una pagina vera e non un buco, che una sezione non ancora nata non si mostri, e che togliere
 * una cartella passi da un dialogo che dice cosa succede davvero.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SEZIONI } from "../src/Impostazioni"
import { t } from "../src/i18n"
import { sezioniAperte } from "../src/pagine"

import {
  SALUTE,
  cambia,
  SPINA,
  STANOTTE,
  chiamate,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  scritture,
} from "./banco"

afterEach(pulisci)

const CARTELLE = {
  items: [
    {
      id: 1,
      name: "2025",
      root_path: "D:\\Astro\\2025",
      created_at: "2026-09-16T10:00:00Z",
      reachable: true,
      frames: 3180,
      reactivated: false,
    },
    {
      id: 2,
      name: "astro",
      root_path: "\\\\NAS\\foto\\astro",
      created_at: "2026-09-16T10:00:00Z",
      reachable: false,
      frames: 1412,
      reactivated: false,
    },
  ],
  total: 2,
  limit: 50,
  offset: 0,
}

function app(cartelle: unknown = CARTELLE) {
  rispondi({
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": {
      stato: 200,
      corpo: { to_confirm: 0 },
    },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
    "/api/v1/folders": { stato: 200, corpo: cartelle },
    ...SPINA,
  })
  return disegna()
}

/** Apre Impostazioni dalla barra, come fa chi usa l'app. */
async function vaiAImpostazioni() {
  const barra = await screen.findByRole("navigation", { name: /pagine/i })
  fireEvent.click(within(barra).getByRole("link", { name: /impostazioni/i }))
}

describe("Impostazioni", () => {
  it("si apre dalla barra, e l indirizzo diventa suo", async () => {
    await app()
    await vaiAImpostazioni()

    expect(window.location.pathname).toBe("/impostazioni")
    expect(await screen.findByRole("heading", { level: 2, name: /^cartelle$/i })).toBeDefined()
  })

  it("un sotto-indirizzo e una pagina vera, non un buco", async () => {
    // E' la regressione che i sotto-indirizzi aprono: col router piatto,
    // `/impostazioni/cartelle` dava pagina vuota e titolo "Pagina sconosciuta", perche' la barra
    // confrontava l'indirizzo **esatto**.
    window.history.pushState({}, "", "/impostazioni/cartelle")
    await app()

    expect(await screen.findByRole("heading", { level: 2, name: /^cartelle$/i })).toBeDefined()
    const barra = await screen.findByRole("navigation", { name: /pagine/i })
    expect(
      within(barra).getByRole("link", { name: /impostazioni/i }).getAttribute("aria-current"),
    ).toBe("page")
  })

  it("nell elenco ci sono le sezioni che esistono, e solo quelle", async () => {
    await app()
    await vaiAImpostazioni()

    const sezioni = await screen.findByRole("navigation", { name: /sezioni/i })
    const voci = within(sezioni).getAllByRole("link")
    // L'elenco e' **quello dichiarato**, non un sottoinsieme a caso: contarle e' cio' che fa
    // cadere questa prova il giorno che una sezione compare senza passare da SEZIONI.
    expect(voci.map((v) => v.textContent)).toEqual(
      SEZIONI.filter((s) => s.elemento !== undefined).map((s) => t(s.chiave)),
    )
  })

  it("una sezione non ancora nata non si mostra", () => {
    // Stessa regola delle voci di barra: una sezione che si apre su niente e' una promessa che
    // l'app non mantiene. Si prova sul **meccanismo** e non su quali sezioni esistono oggi:
    // legata a quelle, la regola smetteva di essere provata il giorno che nascevano tutte -- ed
    // e' esattamente cio' che e' successo quando il riconoscitore e' nato.
    const nate = sezioniAperte([
      { a: "/impostazioni/c", chiave: "settings.folders", elemento: <p /> },
      { a: "/impostazioni/x", chiave: "settings.site" },
    ])
    expect(nate.map((s) => s.a)).toEqual(["/impostazioni/c"])
  })

  it("ogni cartella dice dove sta, se si raggiunge e cosa ne e entrato", async () => {
    await app()
    await vaiAImpostazioni()

    expect(await screen.findByText("D:\\Astro\\2025")).toBeDefined()
    // il separatore delle migliaia dipende dall'ambiente: qui si guarda la frase, non la
    // formattazione, che ha gia' la sua prova in formati.test.ts
    expect(screen.getByText(/180 frame in archivio/)).toBeDefined()
    // esatto: "Non raggiungibile" contiene "raggiungibile", e senza l ancora la prova
    // sarebbe verde anche con due righe irraggiungibili
    expect(screen.getByText(/^Raggiungibile$/)).toBeDefined()
  })

  it("una cartella che non si raggiunge lo dice, e le altre restano", async () => {
    // Il disco staccato non ferma il resto, e i frame gia' letti non spariscono: e' la differenza
    // fra un guasto e una cosa da sapere.
    await app()
    await vaiAImpostazioni()

    expect(await screen.findByText(/^Non raggiungibile$/)).toBeDefined()
    expect(screen.getByText(/412 frame restano in archivio/)).toBeDefined()
    expect(screen.getByText("D:\\Astro\\2025")).toBeDefined()
  })

  it("togliere chiede conferma e dice cosa resta, prima di toccare niente", async () => {
    await app()
    await vaiAImpostazioni()
    const righe = await screen.findAllByRole("button", { name: /^rimuovi$/i })
    fireEvent.click(righe[0]!)

    const dialogo = await screen.findByRole("dialog")
    expect(within(dialogo).getByText(/frame restano in archivio/)).toBeDefined()
    expect(within(dialogo).getByText(/180/)).toBeDefined()
    expect(within(dialogo).getByText(/^i file su disco non vengono modificati$/)).toBeDefined()
    // il paragrafo introduce l'elenco e non lo ripete: ogni effetto si legge una volta sola
    expect(within(dialogo).getByText("Effetti della rimozione:")).toBeDefined()
    expect(within(dialogo).getAllByText(/non vengono modificati/)).toHaveLength(1)
    expect(within(dialogo).getAllByText(/restano in archivio|vengono conservati/)).toHaveLength(1)
    // e finche' non si conferma, la rotta non e' stata chiamata
    expect(scritture().some((s) => s.metodo === "DELETE")).toBe(false)
  })

  it("Esc chiude il dialogo e non toglie niente", async () => {
    // Un dialogo da cui non si esce con Esc e' una trappola: si apre per sbaglio e non si chiude.
    await app()
    await vaiAImpostazioni()
    fireEvent.click((await screen.findAllByRole("button", { name: /^rimuovi$/i }))[0]!)
    await screen.findByRole("dialog")

    fireEvent.keyDown(document, { key: "Escape" })

    expect(screen.queryByRole("dialog")).toBeNull()
    expect(chiamate().some((u) => u.includes("/folders/1"))).toBe(false)
  })

  it("aprendo il dialogo il fuoco ci entra", async () => {
    // Senza, chi ascolta resta fuori dal dialogo che ha appena chiesto qualcosa, e la prova sul
    // **ritorno** del fuoco resterebbe verde per caso: il fuoco non si sarebbe mai mosso.
    await app()
    await vaiAImpostazioni()
    const togli = (await screen.findAllByRole("button", { name: /^rimuovi$/i }))[0]!
    togli.focus()
    fireEvent.click(togli)

    const dialogo = await screen.findByRole("dialog")
    expect(dialogo.contains(document.activeElement)).toBe(true)
    expect(document.activeElement).not.toBe(togli)
  })

  it("il dialogo si dichiara modale, e ha un nome", async () => {
    // Senza aria-modal chi ascolta continua a camminare sulla pagina dietro senza sapere che c e
    // qualcosa davanti; senza nome, il dialogo si annuncia come "dialogo" e basta.
    await app()
    await vaiAImpostazioni()
    fireEvent.click((await screen.findAllByRole("button", { name: /^rimuovi$/i }))[0]!)

    const dialogo = await screen.findByRole("dialog")
    expect(dialogo.getAttribute("aria-modal")).toBe("true")
    expect(dialogo.getAttribute("aria-labelledby")).not.toBeNull()
  })

  it("se il ritiro non riesce il dialogo resta aperto, e lo dice li dentro", async () => {
    // Chiuderlo direbbe che e andata: la cartella invece e ancora nell elenco.
    await app()
    await vaiAImpostazioni()
    cambia({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": {
        stato: 200,
        corpo: { to_confirm: 0 },
      },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
      "DELETE /api/v1/folders": { stato: 500, corpo: { detail: { code: "rotto" } } },
      "/api/v1/folders": { stato: 200, corpo: CARTELLE },
      ...SPINA,
    })
    fireEvent.click((await screen.findAllByRole("button", { name: /^rimuovi$/i }))[0]!)
    const dialogo = await screen.findByRole("dialog")
    fireEvent.click(within(dialogo).getByRole("button", { name: /^rimuovi cartella$/i }))

    expect(await within(dialogo).findByRole("alert")).toBeDefined()
    expect(screen.getByRole("dialog")).toBeDefined()
  })

  it("chiudendo il dialogo il fuoco torna al bottone che l ha aperto", async () => {
    // Senza, chi naviga da tastiera riparte dall'inizio della pagina ogni volta che annulla: il
    // dialogo lo ha portato via e non glielo ha restituito.
    await app()
    await vaiAImpostazioni()
    const togli = (await screen.findAllByRole("button", { name: /^rimuovi$/i }))[0]!
    togli.focus()
    fireEvent.click(togli)
    const dialogo = await screen.findByRole("dialog")

    fireEvent.click(within(dialogo).getByRole("button", { name: /annulla/i }))

    expect(screen.queryByRole("dialog")).toBeNull()
    expect(document.activeElement).toBe(togli)
  })

  it("confermando si smette di leggerla", async () => {
    await app()
    await vaiAImpostazioni()
    fireEvent.click((await screen.findAllByRole("button", { name: /^rimuovi$/i }))[0]!)
    const dialogo = await screen.findByRole("dialog")

    fireEvent.click(within(dialogo).getByRole("button", { name: /^rimuovi cartella$/i }))

    await screen.findByRole("heading", { level: 2, name: /^cartelle$/i })
    expect(scritture().some((s) => s.metodo === "DELETE" && s.url.includes("/folders/1"))).toBe(
      true,
    )
  })

  it("Cambia percorso sposta la cartella dove stanno ora i suoi file", async () => {
    // Chi cambia lettera al disco o passa al NAS: stessa cartella, posto nuovo, e le risposte
    // date restano. Registrarla di nuovo le avrebbe lasciate sul percorso vecchio.
    await app()
    await vaiAImpostazioni()
    fireEvent.click((await screen.findAllByRole("button", { name: /cambia percorso/i }))[0]!)
    const dialogo = await screen.findByRole("dialog")

    fireEvent.change(within(dialogo).getByLabelText(/^nuovo percorso/i), {
      target: { value: "E:/Astro/2025" },
    })
    fireEvent.click(within(dialogo).getByRole("button", { name: /^verifica$/i }))

    await waitFor(() =>
      expect(
        scritture().some(
          (s) =>
            s.metodo === "POST" &&
            s.url.endsWith("/api/v1/folders/1/move") &&
            (s.corpo as { root_path: string }).root_path === "E:/Astro/2025",
        ),
      ).toBe(true),
    )
  })

  it("Invio nel percorso nuovo sposta, come il tasto", async () => {
    await app()
    await vaiAImpostazioni()
    fireEvent.click((await screen.findAllByRole("button", { name: /cambia percorso/i }))[0]!)
    const dialogo = await screen.findByRole("dialog")
    const campo = within(dialogo).getByLabelText(/^nuovo percorso/i)

    fireEvent.change(campo, { target: { value: "E:/Astro/2025" } })
    fireEvent.submit(campo)

    await waitFor(() =>
      expect(
        scritture().some(
          (s) =>
            s.metodo === "POST" &&
            s.url.endsWith("/api/v1/folders/1/move") &&
            (s.corpo as { root_path: string }).root_path === "E:/Astro/2025",
        ),
      ).toBe(true),
    )
  })

  it("sul NAS il tasto del selettore dice che sposta, non che usa", async () => {
    // Qui il clic sposta subito: "Usa questa cartella" e' il testo del primo avvio, dove dopo
    // c'e' ancora Aggiungi.
    rispondi({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/folders/path-info": { stato: 200, corpo: { family: "posix", data_root: "/data" } },
      "/api/v1/folders/browse": {
        stato: 200,
        corpo: { path: "/data", parent: null, folders: [] },
      },
      "/api/v1/folders": { stato: 200, corpo: CARTELLE },
      ...SPINA,
    })
    await disegna()
    await vaiAImpostazioni()
    fireEvent.click((await screen.findAllByRole("button", { name: /cambia percorso/i }))[0]!)
    const dialogo = await screen.findByRole("dialog")

    expect(await within(dialogo).findByRole("button", { name: /^verifica$/i })).toBeDefined()
    expect(within(dialogo).queryByRole("button", { name: /seleziona cartella/i })).toBeNull()
  })

  it("se li non ci sono gli stessi file lo dice, e il dialogo resta aperto", async () => {
    await app()
    await vaiAImpostazioni()
    cambia({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
      "POST /api/v1/folders/1/move": {
        stato: 409,
        corpo: { detail: { code: "not_the_same_folder" } },
      },
      "/api/v1/folders": { stato: 200, corpo: CARTELLE },
      ...SPINA,
    })
    fireEvent.click((await screen.findAllByRole("button", { name: /cambia percorso/i }))[0]!)
    const dialogo = await screen.findByRole("dialog")
    fireEvent.change(within(dialogo).getByLabelText(/^nuovo percorso/i), {
      target: { value: "E:/Altro" },
    })
    fireEvent.click(within(dialogo).getByRole("button", { name: /^verifica$/i }))

    expect(await within(dialogo).findByText(/i file non corrispondono/i)).toBeDefined()
    expect(screen.getByRole("dialog")).toBeDefined()
  })

  it("senza cartelle dice cosa manca, invece di un elenco vuoto", async () => {
    // E' lo stato di chi ha saltato il primo avvio, ed e' il buco che questa pagina ripara.
    await app({ items: [], total: 0, limit: 50, offset: 0 })
    await vaiAImpostazioni()

    const vuoto = await screen.findByText(/^nessuna cartella$/i)
    const dentro = vuoto.closest(".as-vuoto")
    expect(dentro).not.toBeNull()
    expect(within(dentro as HTMLElement).getByText(/i file non vengono spostati/i)).toBeDefined()
  })
})
