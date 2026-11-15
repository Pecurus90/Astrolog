// @vitest-environment jsdom
/**
 * Impostazioni: la pagina a sezioni, e la sezione Cartelle e scansione (tavola v82).
 *
 * Qui si provano le regole che una lettura del codice non prende: che un **sotto-indirizzo** sia
 * una pagina vera e non un buco, che una sezione non ancora nata non si mostri, che togliere una
 * cartella chieda prima, e che Verifica guardi senza scrivere.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SEZIONI } from "../src/Impostazioni"
import { t } from "../src/i18n"
import { sezioniAperte } from "../src/pagine"

import {
  FERMO,
  cambia,
  SALUTE,
  apriImpostazioni,
  SPINA,
  STANOTTE,
  chiamate,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  scritture,
  type Voce,
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

const VUOTE = { items: [], total: 0, limit: 50, offset: 0 }

function app(altre: Record<string, Voce> = {}, cartelle: unknown = CARTELLE, radice: string | null = null) {
  rispondi({
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/folders/path-info": {
      stato: 200,
      corpo: { family: radice ? "posix" : "windows", data_root: radice },
    },
    "/api/v1/folders": { stato: 200, corpo: cartelle },
    ...SPINA,
    ...altre,
  })
  return disegna()
}

/** Apre Impostazioni dalla barra, poi la linguetta Cartelle, come fa chi usa l'app. */
async function vaiAlleCartelle() {
  await apriImpostazioni()
  fireEvent.click(await screen.findByRole("tab", { name: /^cartelle e scansione$/i }))
  return screen.findByRole("region", { name: "Cartelle" })
}

const scritta = (metodo: string, fine: string) =>
  scritture().some((s) => s.metodo === metodo && s.url.endsWith(fine))

describe("Impostazioni", () => {
  it("si apre dalla barra, e l indirizzo diventa suo", async () => {
    await app()
    await apriImpostazioni()

    expect(window.location.pathname).toBe("/impostazioni")
    // sul desktop l'indirizzo della pagina apre Generale (tavola v82)
    expect((await screen.findByRole("tab", { name: "Generale" })).getAttribute("aria-selected")).toBe("true")
    expect(screen.getByRole("textbox", { name: "Nome utente" })).toBeDefined()
  })

  it("un sotto-indirizzo e una pagina vera, non un buco", async () => {
    // col router piatto `/impostazioni/cartelle` dava pagina vuota e "Pagina sconosciuta"
    window.history.pushState({}, "", "/impostazioni/cartelle")
    await app()

    expect(await screen.findByRole("region", { name: "Cartelle" })).toBeDefined()
    // l'ingranaggio non e' una pillola: nessuna pillola si accende su una pagina che non e' sua
    const pillole = await screen.findByRole("navigation", { name: "Navigazione principale" })
    expect(within(pillole).getAllByRole("link").filter((a) => a.getAttribute("aria-current") === "page")).toEqual([])
  })

  it("nell elenco ci sono le sezioni che esistono, e solo quelle", async () => {
    await app()
    await vaiAlleCartelle()

    const sezioni = await screen.findByRole("tablist", { name: /sezioni/i })
    const voci = within(sezioni).getAllByRole("tab")
    // contarle fa cadere la prova il giorno che una sezione compare senza passare da SEZIONI
    expect(voci.map((v) => v.textContent)).toEqual(
      SEZIONI.filter((s) => s.elemento !== undefined).map((s) => t(s.chiave)),
    )
  })

  it("una sezione non ancora nata non si mostra", () => {
    // si prova sul meccanismo, non su quali sezioni esistono oggi
    const nate = sezioniAperte([
      { a: "/impostazioni/c", chiave: "settings.folders", elemento: <p /> },
      { a: "/impostazioni/x", chiave: "settings.site" },
    ])
    expect(nate.map((s) => s.a)).toEqual(["/impostazioni/c"])
  })
})

describe("Cartelle", () => {
  it("ogni cartella dice dove sta, se si raggiunge e cosa ne e entrato", async () => {
    await app()
    const carta = await vaiAlleCartelle()

    expect(await within(carta).findByText("D:\\Astro\\2025")).toBeDefined()
    expect(within(carta).getByText("2 cartelle")).toBeDefined()
    // il separatore delle migliaia dipende dall'ambiente: qui si guarda la frase
    expect(within(carta).getByText(/180 frame in archivio$/)).toBeDefined()
  })

  it("una cartella che non si raggiunge lo dice, e i suoi frame restano", async () => {
    await app()
    const carta = await vaiAlleCartelle()

    expect(await within(carta).findByText(/^non raggiungibile · 1.?412 frame restano in archivio$/)).toBeDefined()
    expect(within(carta).getByText("D:\\Astro\\2025")).toBeDefined()
  })

  it("Togli chiede nella riga e dice cosa resta, prima di toccare niente", async () => {
    await app()
    const carta = await vaiAlleCartelle()
    fireEvent.click((await within(carta).findAllByRole("button", { name: "Togli" }))[0]!)

    const chiede = await within(carta).findByRole("alertdialog")
    expect(chiede.textContent).toContain("Togliere D:\\Astro\\2025? I frame restano nell'archivio")
    expect(scritture().some((s) => s.metodo === "DELETE")).toBe(false)
    fireEvent.click(within(chiede).getByRole("button", { name: "Annulla" }))
    expect(within(carta).queryByRole("alertdialog")).toBeNull()
    expect(chiamate().some((u) => u.includes("/folders/1"))).toBe(false)
  })

  it("confermando si smette di leggerla", async () => {
    await app({ "DELETE /api/v1/folders/1": { stato: 200, corpo: { folder_id: 1, retired: true, kept_frames: 3180 } } })
    const carta = await vaiAlleCartelle()
    fireEvent.click((await within(carta).findAllByRole("button", { name: "Togli" }))[0]!)
    fireEvent.click(await within(carta).findByRole("button", { name: "Togli la cartella" }))

    await waitFor(() => expect(scritta("DELETE", "/api/v1/folders/1")).toBe(true))
  })

  it("se il ritiro non riesce la domanda resta, e lo dice li dentro", async () => {
    await app({ "DELETE /api/v1/folders": { stato: 500, corpo: { detail: { code: "rotto" } } } })
    const carta = await vaiAlleCartelle()
    fireEvent.click((await within(carta).findAllByRole("button", { name: "Togli" }))[0]!)
    const chiede = await within(carta).findByRole("alertdialog")
    fireEvent.click(within(chiede).getByRole("button", { name: "Togli la cartella" }))

    expect(await within(chiede).findByText(/la cartella non si è tolta/i)).toBeDefined()
  })

  it("Verifica di Sposta guarda senza spostare, e Usa questo percorso sposta", async () => {
    // Chi cambia lettera al disco o passa al NAS: stessa cartella, posto nuovo, risposte che restano.
    await app({
      "POST /api/v1/folders/1/move/check": { stato: 200, corpo: { root_path: "E:\\Astro\\2025" } },
      "POST /api/v1/folders/1/move": { stato: 200, corpo: CARTELLE.items[0] },
    })
    const carta = await vaiAlleCartelle()
    fireEvent.click((await within(carta).findAllByRole("button", { name: "Sposta" }))[0]!)
    fireEvent.change(within(carta).getByRole("textbox", { name: "Nuovo percorso" }), {
      target: { value: "E:/Astro/2025" },
    })
    fireEvent.click(within(carta).getAllByRole("button", { name: "Verifica" })[0]!)

    expect(await within(carta).findByText("Stessi file in E:\\Astro\\2025")).toBeDefined()
    expect(scritta("POST", "/api/v1/folders/1/move")).toBe(false)
    fireEvent.click(within(carta).getByRole("button", { name: "Usa questo percorso" }))
    await waitFor(() =>
      expect(
        scritture().some(
          (s) =>
            s.url.endsWith("/api/v1/folders/1/move") &&
            (s.corpo as { root_path: string }).root_path === "E:\\Astro\\2025",
        ),
      ).toBe(true),
    )
  })

  it("se li non ci sono gli stessi file lo dice, e non sposta", async () => {
    await app({
      "POST /api/v1/folders/1/move/check": { stato: 409, corpo: { detail: { code: "not_the_same_folder" } } },
    })
    const carta = await vaiAlleCartelle()
    fireEvent.click((await within(carta).findAllByRole("button", { name: "Sposta" }))[0]!)
    const campo = within(carta).getByRole("textbox", { name: "Nuovo percorso" })
    fireEvent.change(campo, { target: { value: "E:/Altro" } })
    fireEvent.submit(campo)

    expect(await within(carta).findByText(/i file non corrispondono/i)).toBeDefined()
    expect(scritta("POST", "/api/v1/folders/1/move")).toBe(false)
  })

  it("Aggiungi guarda dentro, poi registra dal suo esito", async () => {
    await app({
      "POST /api/v1/folders/probe": {
        stato: 200,
        corpo: { root_path: "E:\\Nuova", reachable: true, fits_count: 12, complete: true, moved_from: null, moved_check: "none" },
      },
      "POST /api/v1/folders": { stato: 201, corpo: CARTELLE.items[0] },
    })
    const carta = await vaiAlleCartelle()
    fireEvent.change(within(carta).getByRole("textbox", { name: "Percorso della cartella" }), {
      target: { value: "E:\\Nuova" },
    })
    fireEvent.click(within(carta).getAllByRole("button", { name: "Verifica" }).at(-1)!)

    expect(await within(carta).findByText("12 file FITS · E:\\Nuova")).toBeDefined()
    expect(scritta("POST", "/api/v1/folders")).toBe(false)
    fireEvent.click(within(carta).getByRole("button", { name: "Aggiungi cartella" }))
    await waitFor(() => expect(scritta("POST", "/api/v1/folders")).toBe(true))
  })

  it("una cartella gia nell elenco lo dice, invece di un errore", async () => {
    await app({
      "POST /api/v1/folders/probe": {
        stato: 200,
        corpo: { root_path: "D:\\Astro\\2025", reachable: true, fits_count: 3, complete: true, moved_from: null, moved_check: "none" },
      },
      "POST /api/v1/folders": { stato: 409, corpo: { detail: { code: "folder_exists", folder_id: 1 } } },
    })
    const carta = await vaiAlleCartelle()
    const campo = within(carta).getByRole("textbox", { name: "Percorso della cartella" })
    fireEvent.change(campo, { target: { value: "D:\\Astro\\2025" } })
    fireEvent.keyDown(campo, { key: "Enter" })
    fireEvent.click(await within(carta).findByRole("button", { name: "Aggiungi cartella" }))

    expect(await within(carta).findByText("Cartella già registrata")).toBeDefined()
    expect(within(carta).queryByText("Aggiunta non riuscita.")).toBeNull()
  })

  it("Sposta si chiude con Annulla, senza scrivere", async () => {
    await app()
    const carta = await vaiAlleCartelle()
    fireEvent.click((await within(carta).findAllByRole("button", { name: "Sposta" }))[0]!)
    fireEvent.click(within(carta).getByRole("button", { name: "Annulla" }))

    expect(within(carta).queryByRole("textbox", { name: "Nuovo percorso" })).toBeNull()
    expect(scritture()).toEqual([])
  })

  it("una cartella che non si raggiunge non offre di aggiungerla", async () => {
    await app({
      "POST /api/v1/folders/probe": {
        stato: 200,
        corpo: { root_path: "F:\\", reachable: false, fits_count: null, complete: true, moved_from: null, moved_check: "place_unreachable" },
      },
    })
    const carta = await vaiAlleCartelle()
    fireEvent.change(within(carta).getByRole("textbox", { name: "Percorso della cartella" }), {
      target: { value: "F:\\" },
    })
    fireEvent.keyDown(within(carta).getByRole("textbox", { name: "Percorso della cartella" }), { key: "Enter" })

    expect(await within(carta).findByText("Cartella non raggiungibile")).toBeDefined()
    expect(within(carta).queryByRole("button", { name: "Aggiungi cartella" })).toBeNull()
  })

  it("sul NAS le cartelle si sfogliano, e si sceglie quella dove sei", async () => {
    await app(
      {
        "GET /api/v1/folders/browse": {
          stato: 200,
          corpo: { path: "/data", parent: null, folders: [{ name: "astro", path: "/data/astro" }] },
        },
        "POST /api/v1/folders/probe": {
          stato: 200,
          corpo: { root_path: "/data", reachable: true, fits_count: 3, complete: true, moved_from: null, moved_check: "none" },
        },
      },
      CARTELLE,
      "/data",
    )
    const carta = await vaiAlleCartelle()

    expect(await within(carta).findByRole("button", { name: /astro/ })).toBeDefined()
    expect(within(carta).getByText(/percorso interno al container/i)).toBeDefined()
    fireEvent.click(within(carta).getByRole("button", { name: "Seleziona questa cartella" }))
    await waitFor(() =>
      expect(scritture().some((s) => s.url.endsWith("/folders/probe") && (s.corpo as { root_path: string }).root_path === "/data")).toBe(true),
    )
  })

  it("senza cartelle lo dice, invece di un elenco vuoto", async () => {
    await app({}, VUOTE)
    const carta = await vaiAlleCartelle()

    expect(await within(carta).findByText("Nessuna cartella: l'archivio è vuoto.")).toBeDefined()
    expect(within(carta).getByText("0 cartelle")).toBeDefined()
  })
})

describe("Scansione", () => {
  const scansione = () => screen.findByRole("region", { name: "Scansione" })

  it("mai scansionato: lo dice, e Scansiona avvia", async () => {
    await app({ "POST /api/v1/scan": { stato: 202, corpo: { started: [], skipped: [] } } })
    await vaiAlleCartelle()
    const carta = await scansione()

    expect(within(carta).getByText("Nessuna scansione finora")).toBeDefined()
    fireEvent.click(within(carta).getByRole("button", { name: "Scansiona" }))
    await waitFor(() => expect(scritta("POST", "/api/v1/scan")).toBe(true))
  })

  it("a scansione finita il conto della cartella si rilegge", async () => {
    await app({
      "/api/v1/pipeline/status": {
        stato: 200,
        corpo: { ...FERMO, worker: { ...FERMO.worker, state: "running", stage: "scan" } },
      },
    })
    const carta = await vaiAlleCartelle()
    await within(carta).findByText(/180 frame in archivio$/)

    cambia({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
      "/api/v1/pipeline/status": {
        stato: 200,
        corpo: { ...FERMO, worker: { ...FERMO.worker, state: "completed", ended_at: "2026-11-15T15:48:00Z" } },
      },
      "/api/v1/folders": {
        stato: 200,
        corpo: { ...CARTELLE, items: [{ ...CARTELLE.items[0]!, frames: 3194 }, CARTELLE.items[1]!] },
      },
    })

    // il battito dello stato mentre gira e' 1,5 s
    expect(await within(carta).findByText(/194 frame in archivio$/, {}, { timeout: 5000 })).toBeDefined()
  })

  it("l ultima scansione dice quando e cosa ha trovato", async () => {
    await app({
      "/api/v1/pipeline/status": {
        stato: 200,
        corpo: { ...FERMO, last_scan: { ended_at: "2026-11-15T06:12:00Z", ended_day: "today", new: 214, not_read: 0 } },
      },
    })
    await vaiAlleCartelle()
    const carta = await scansione()

    expect(within(carta).getByText(/^Ultima scansione oggi, /)).toBeDefined()
    expect(within(carta).getByText("214 file nuovi, nessun problema")).toBeDefined()
  })
})
