// @vitest-environment jsdom
/**
 * Il backup delle risposte (ADR 0017): su un database nuovo con il file accanto, prima del primo
 * avvio l'app chiede se rimettere le risposte; in Impostazioni si vede dove sta il file.
 */
import { fireEvent, screen, waitFor } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, SPINA, STANOTTE, cambia, chiamate, disegna, impostazioni, pulisci, rispondi, scritture } from "./banco"

afterEach(pulisci)

const CONTI = {
  written_at: "2026-10-06T20:15:00Z",
  sites: 1,
  folders: 2,
  instruments: 3,
  filters: 1,
  answers: 42,
}

// written today: the page says «oggi» from `written_day`, the clock of the home site
const STATO = {
  offer: "none",
  last: CONTI,
  unreadable: false,
  path: "C:\\dati\\risposte.json",
  size_bytes: 47104,
  written_day: "today",
}

function app(offer: "found" | "none", fatto: boolean) {
  rispondi({
    ...STANOTTE,
    ...SPINA,
    "POST /api/v1/backup/restore": { stato: 200, corpo: { offer: "none", last: CONTI, unreadable: false, path: "x" } },
    "POST /api/v1/scan": { stato: 202, corpo: {} },
    "/api/v1/backup": {
      stato: 200,
      corpo: { ...STATO, offer },
    },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(fatto) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
  return disegna()
}

describe("Il backup", () => {
  it("su un database nuovo chiede di rimetterle, prima del primo avvio", async () => {
    await app("found", false)
    expect(await screen.findByText(/^backup trovato$/i)).toBeDefined()
    // tavola v82 `Primo avvio`, passo backup: dentro il primo avvio, senza i passi di lato,
    // i quattro conti in tessere, Ripristina pieno per primo
    expect(screen.getByRole("main").className).toBe("al-avvio__centro-1")
    expect(screen.queryByRole("list", { name: /passi del primo avvio/i })).toBeNull()
    const carta = screen.getByRole("region", { name: /^backup trovato$/i })
    expect(carta.className).toBe("al-avvio__colonna-8")
    const conti = [...carta.querySelectorAll(".al-avvio__colonna-9")].map(
      (v) => `${v.querySelector(".al-avvio__testo-9")?.textContent}=${v.querySelector(".al-avvio__testo-8")?.textContent}`,
    )
    expect(conti).toEqual(["conferme=42", "siti=1", "cartelle=2", "strumenti e filtri=4"])
    const azioni = [...carta.querySelectorAll(".al-avvio__riga-5 > *")]
    expect(azioni.map((a) => a.textContent)).toEqual(["Ripristina", "Inizia da zero"])
    expect(azioni[0]?.className).toContain("al-bottone--pieno")

    fireEvent.click(screen.getByRole("button", { name: /^ripristina$/i }))

    await waitFor(() => {
      const fatte = scritture().map((s) => `${s.metodo} ${new URL(s.url).pathname}`)
      expect(fatte).toContain("POST /api/v1/backup/restore")
      expect(fatte).toContain("POST /api/v1/scan")
    })
  })

  it("un backup senza cartelle si rimette senza chiedere una lettura (collaudo 18/11)", async () => {
    // la lettura di nessuna cartella e' un 409 `no_folders` nella console, a ogni ripristino
    rispondi({
      ...STANOTTE,
      ...SPINA,
      "POST /api/v1/backup/restore": { stato: 200, corpo: { offer: "none", last: CONTI, unreadable: false, path: "x" } },
      "POST /api/v1/scan": { stato: 409, corpo: { detail: { code: "no_folders" } } },
      "/api/v1/backup": { stato: 200, corpo: { ...STATO, offer: "found", last: { ...CONTI, folders: 0 } } },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(false) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    await disegna()
    fireEvent.click(await screen.findByRole("button", { name: /^ripristina$/i }))
    const fatte = () => scritture().map((s) => `${s.metodo} ${new URL(s.url).pathname}`)
    await waitFor(() => expect(fatte()).toContain("POST /api/v1/backup/restore"))
    await new Promise((r) => setTimeout(r, 50))
    expect(fatte()).not.toContain("POST /api/v1/scan")
  })

  it("ripristinato un backup che porta il timbro, si entra nell'app e non nel primo avvio", async () => {
    // Il backup rimette anche il timbro: il primo avvio, mai mostrato, non deve comparire dopo.
    await app("found", false)
    await screen.findByText(/^backup trovato$/i)
    rispondi({
      ...STANOTTE,
      ...SPINA,
      "POST /api/v1/backup/restore": { stato: 200, corpo: { offer: "none", last: CONTI, unreadable: false, path: "x" } },
      "POST /api/v1/scan": { stato: 202, corpo: {} },
      "/api/v1/backup": { stato: 200, corpo: { ...STATO, path: "x" } },
      // le impostazioni arrivano dopo il backup, come dal vivo: per un attimo l'app sa che non
      // c'e' piu' niente da proporre e ha ancora in mano il timbro vecchio
      "/api/v1/settings": {
        stato: 200,
        corpo: impostazioni(true),
        attesa: new Promise((fatto) => setTimeout(fatto, 60)),
      },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    fireEvent.click(screen.getByRole("button", { name: /^ripristina$/i }))
    expect(await screen.findByRole("navigation", { name: "Navigazione principale" })).toBeDefined()
    expect(screen.queryByRole("button", { name: /^salta$/i })).toBeNull()
  })

  it("senza nulla da proporre non chiede niente", async () => {
    await app("none", true)
    await screen.findByRole("navigation", { name: "Navigazione principale" })
    expect(screen.queryByText(/^backup trovato$/i)).toBeNull()
  })

  it("in Impostazioni dice dove sta il file, quando e' stato scritto e quanto pesa", async () => {
    window.history.pushState({}, "", "/impostazioni/backup")
    await app("none", true)
    expect(await screen.findByText("C:\\dati\\risposte.json")).toBeDefined()
    // 47 104 byte: «46 KB», come la tavola
    expect(await screen.findByText(/^oggi, \d\d:\d\d · 46 KB$/)).toBeDefined()
    expect(screen.getByRole("button", { name: /^esporta$/i }).getAttribute("aria-disabled")).toBeNull()
  })

  it("un file mai scritto lo dice, ed Esporta e' spento", async () => {
    window.history.pushState({}, "", "/impostazioni/backup")
    rispondi({
      ...STANOTTE,
      ...SPINA,
      "/api/v1/backup": { stato: 200, corpo: { ...STATO, last: null, size_bytes: null, written_day: null } },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    await disegna()
    expect(await screen.findByText("non ancora: si scrive alla prima risposta")).toBeDefined()
    expect(screen.getByRole("button", { name: /^esporta$/i }).getAttribute("aria-disabled")).toBe("true")
  })

  it("un file che non si legge lo dice, e il database non cambia", async () => {
    window.history.pushState({}, "", "/impostazioni/backup")
    rispondi({
      ...STANOTTE,
      ...SPINA,
      "/api/v1/backup": {
        stato: 200,
        corpo: { ...STATO, last: null, unreadable: true, size_bytes: null, written_day: null },
      },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    await disegna()
    expect(await screen.findByText("Il file delle risposte non si legge")).toBeDefined()
    // un file c'e': non «non ancora», ed Esporta legge il database
    expect(screen.queryByText("non ancora: si scrive alla prima risposta")).toBeNull()
    expect(screen.getByRole("button", { name: /^esporta$/i }).getAttribute("aria-disabled")).toBeNull()
  })

  it("un'importazione senza risposta dice che niente e' cambiato, e Riprova rimanda lo stesso file", async () => {
    window.history.pushState({}, "", "/impostazioni/backup")
    rispondi({
      ...STANOTTE,
      ...SPINA,
      "POST /api/v1/backup/import": { stato: 503, corpo: {} },
      "/api/v1/backup": { stato: 200, corpo: STATO },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    const { container } = await disegna()
    await screen.findByRole("button", { name: /^importa$/i })
    const scelta = container.querySelector<HTMLInputElement>('input[type="file"]')!
    const file = new File(['{"version": 1}'], "risposte.json", { type: "application/json" })
    fireEvent.change(scelta, { target: { files: [file] } })
    expect(await screen.findByText("Ripristino non riuscito")).toBeDefined()
    fireEvent.click(screen.getByText("Riprova"))
    await waitFor(() =>
      expect(scritture().filter((s) => s.url.includes("/backup/import"))).toHaveLength(2),
    )
  })

  it("una cartella del file che qui non si puo' usare si nomina: il file non e' guasto", async () => {
    window.history.pushState({}, "", "/impostazioni/backup")
    rispondi({
      ...STANOTTE,
      ...SPINA,
      "POST /api/v1/backup/import": {
        stato: 422,
        corpo: { detail: { code: "path_outside_data_root", path: "/home/marco/privata" } },
      },
      "/api/v1/backup": { stato: 200, corpo: { ...STATO, path: "x" } },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    const { container } = await disegna()
    await screen.findByRole("button", { name: /^importa$/i })
    const scelta = container.querySelector<HTMLInputElement>('input[type="file"]')!
    const file = new File(['{"version": 1}'], "risposte.json", { type: "application/json" })
    fireEvent.change(scelta, { target: { files: [file] } })
    expect(
      await screen.findByText(
        "Nel file c'è una cartella che qui non si può usare: /home/marco/privata. Non ho importato niente.",
      ),
    ).toBeDefined()
    expect(screen.queryByText(/file di backup non valido/i)).toBeNull()
  })

  it("uno stato del backup che non arriva, aperto sulla sua sezione, lo dice una volta e non gira (#90)", async () => {
    window.history.pushState({}, "", "/impostazioni/backup")
    const mappa = {
      ...STANOTTE,
      ...SPINA,
      "/api/v1/backup": { stato: 500, corpo: {} },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
    }
    rispondi(mappa)
    await disegna()
    expect(await screen.findByText("Stato del backup non disponibile.")).toBeDefined()
    await new Promise((r) => setTimeout(r, 300))
    expect(chiamate().filter((u) => new URL(u).pathname === "/api/v1/backup").length).toBeLessThan(4)
    expect(screen.queryByText("Leggo le impostazioni…")).toBeNull()
    // Riprova rilegge, e mentre legge la pagina delle Impostazioni resta a schermo (#91)
    let lascia: (v?: unknown) => void = () => {}
    const attesa = new Promise((r) => (lascia = r))
    cambia({ ...mappa, "/api/v1/backup": { stato: 500, corpo: {}, attesa } })
    const prima = chiamate().length
    fireEvent.click(screen.getByRole("button", { name: "Riprova" }))
    await waitFor(() => expect(chiamate().length).toBeGreaterThan(prima))
    expect(screen.queryByText("Leggo le impostazioni…")).toBeNull()
    expect(screen.getByRole("heading", { name: "Impostazioni", level: 1 })).toBeDefined()
    lascia()
    expect(await screen.findByText("Stato del backup non disponibile.")).toBeDefined()
  })

  it("se il backup non dice quando e' stato scritto, la domanda non comincia con un punto", async () => {
    rispondi({
      ...STANOTTE,
      ...SPINA,
      "/api/v1/backup": {
        stato: 200,
        corpo: { offer: "found", last: { ...CONTI, written_at: null }, unreadable: false, path: "x" },
      },
      "/api/v1/settings": { stato: 200, corpo: impostazioni(false) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
    })
    await disegna()
    const domanda = await screen.findByText(/ripristinare i dati salvati/i)
    expect(domanda.textContent).toMatch(/^Ripristinare/)
  })
})
