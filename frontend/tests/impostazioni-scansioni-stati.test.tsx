// @vitest-environment jsdom
/**
 * Impostazioni, *Scansioni* (tavola v82, `SezioneServizi`): gli stati della sezione (attesa,
 * errore, vuota), la carta di una in corso che si rilegge da sola, cio' che resta fuori e i gesti
 * che ci sono solo quando servono. Le carte complete in `impostazioni-scansioni.test.tsx`.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  FERMO,
  SALUTE,
  SCANSIONE,
  STANOTTE,
  type Voce,
  chiamate,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  scritture,
} from "./banco"

afterEach(pulisci)

function app(elenco: Voce, altre: Record<string, Voce> = {}, stato: unknown = FERMO) {
  window.history.pushState({}, "", "/impostazioni/scansioni")
  rispondi({
    ...altre,
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/scans": elenco,
    "/api/v1/pipeline/status": { stato: 200, corpo: stato },
  })
  return disegna()
}

const pagina = (items: unknown[]): Voce => ({
  stato: 200,
  corpo: { items, total: items.length, limit: 20, offset: 0 },
})
const letture = () => chiamate().filter((u) => new URL(u).pathname === "/api/v1/scans").length
/** Le righe di una carta: «etichetta=valore». */
const righe = (carta: HTMLElement) =>
  [...carta.querySelectorAll(".al-imp-riga")].map(
    (r) =>
      `${r.querySelector(".al-imp-etichetta")?.textContent}=${r.querySelector(".al-imp-valore")?.textContent}`,
  )

describe("Impostazioni / Scansioni, gli stati della sezione", () => {
  it("mentre l'elenco arriva ci sono due carte d'attesa, e niente 'nessuna'", async () => {
    await app({ ...pagina([]), attesa: new Promise(() => {}) })
    await screen.findByText(/^Le scansioni passate/)
    const carte = [...document.querySelectorAll(".al-imp-sezione .al-c-scheletro__blocco-4")]
    expect(carte.map((c) => (c as HTMLElement).style.height)).toEqual(["220px", "220px"])
    const primo = carte[0]!.querySelector<HTMLElement>(".al-c-scheletro__blocco-3")!
    expect([primo.style.height, primo.style.width]).toEqual(["24px", "180px"])
    expect(screen.queryByText("Nessuna scansione ancora")).toBeNull()
  })

  it("un elenco che non arriva lo dice, e Riprova lo richiede", async () => {
    await app({ stato: 500, corpo: {} })
    expect(await screen.findByText("Scansioni non disponibili.")).toBeDefined()
    expect(screen.queryByText("Nessuna scansione ancora")).toBeNull()
    expect(document.querySelector(".al-imp-sezione .al-c-scheletro__blocco-4")).toBeNull()
    const prima = letture()
    fireEvent.click(screen.getByRole("button", { name: "Riprova" }))
    await waitFor(() => expect(letture()).toBeGreaterThan(prima))
  })

  it("con delle scansioni la sezione non dice 'nessuna'", async () => {
    await app(pagina([SCANSIONE]))
    await screen.findByRole("region", { name: /completata$/ })
    expect(screen.queryByText("Nessuna scansione ancora")).toBeNull()
  })

  it("una in corso si rilegge da sola", async () => {
    await app(
      pagina([
        {
          ...SCANSIONE,
          outcome: "running",
          duration_s: null,
          progress: { read: 1, total: 4, pct: 25 },
        },
      ]),
    )
    await screen.findByRole("progressbar")
    const prima = letture()
    await waitFor(() => expect(letture()).toBeGreaterThan(prima), { timeout: 2500 })
  })

  it("una finita non si rilegge", async () => {
    await app(pagina([SCANSIONE]))
    await screen.findByRole("region", { name: /completata$/ })
    const ferme = letture()
    await new Promise((r) => setTimeout(r, 1800))
    expect(letture()).toBe(ferme)
  })
})

describe("Impostazioni / Scansioni, la carta", () => {
  it("una in corso si chiama 'adesso', dice la percentuale e la barra la segue", async () => {
    await app(
      pagina([
        {
          ...SCANSIONE,
          outcome: "running",
          duration_s: null,
          progress: { read: 7, total: 20, pct: 35 },
        },
      ]),
      { "POST /api/v1/pipeline/stop": { stato: 200, corpo: {} } },
    )
    const carta = await screen.findByRole("region", { name: "adesso · in corso · 35%" })
    expect(within(carta).getByRole("progressbar").getAttribute("aria-valuenow")).toBe("35")
    expect(carta.querySelector<HTMLElement>(".al-imp-barra > span")?.style.width).toBe("35%")
    // durata non ancora nota: niente riga sotto il titolo
    expect(carta.querySelector(".al-imp-sotto")).toBeNull()
    const ferma = within(carta).getByRole("button", { name: /^interrompi$/i })
    expect(ferma.className).toContain("al-bottone--contorno")
  })

  it("in corso senza avanzamento dice solo 'in corso', e niente barra", async () => {
    await app(pagina([{ ...SCANSIONE, outcome: "running", duration_s: null, progress: null }]))
    const carta = await screen.findByRole("region", { name: "adesso · in corso" })
    expect(within(carta).queryByRole("progressbar")).toBeNull()
  })

  it("una interrotta che non riparte ha il suo nome e il giorno, e nessun gesto", async () => {
    await app(pagina([{ ...SCANSIONE, outcome: "stopped", can_retry: false, progress: null }]))
    const carta = await screen.findByRole("region", { name: /interrotta a mano$/ })
    expect(carta.getAttribute("aria-label")).not.toMatch(/^adesso/)
    expect(within(carta).queryByRole("button")).toBeNull()
    expect(carta.querySelector(".al-imp-gesti")).toBeNull()
  })

  it("le righe hanno le etichette della tavola, e le cartelle stanno in colonna", async () => {
    await app(
      pagina([
        { ...SCANSIONE, new: 4, reason: "internal_error", reason_folder: "D:\\Astro\\2025" },
      ]),
    )
    const carta = await screen.findByRole("region", { name: /completata$/ })
    expect(righe(carta)).toEqual([
      "Cartelle=D:\\Astro\\2025",
      "Entrati=4 frame",
      "Motivo=Errore interno durante la lettura di D:\\Astro\\2025: dettagli nel log.",
    ])
    const valori = [...carta.querySelectorAll(".al-imp-valore")].map((v) => v.className)
    expect(valori).toEqual([
      "al-imp-valore al-imp-valore--colonna",
      "al-imp-valore",
      "al-imp-valore",
    ])
  })

  it("niente rimasto fuori: la riga non c'e'; solo cartelle saltate: la riga le nomina", async () => {
    await app(
      pagina([
        { ...SCANSIONE, id: 2, folders: ["A"] },
        {
          ...SCANSIONE,
          id: 1,
          folders: ["B"],
          dirs_left_out: [
            { why: "hidden", path: "B\\.cache" },
            { why: "linked", path: "B\\link" },
          ],
        },
      ]),
    )
    const [vuota, saltate] = await screen.findAllByRole("region", { name: /completata$/ })
    expect(righe(vuota!).map((r) => r.split("=")[0])).toEqual(["Cartelle", "Entrati"])
    expect(righe(saltate!).at(-1)).toBe(
      "Rimasti fuori=B\\.cache: cartella nascosta, ignorataB\\link: collegamento, non seguito",
    )
  })

  it("i non leggibili dicono il perche' di ogni file; senza file la riga non c'e'", async () => {
    await app(
      pagina([
        {
          ...SCANSIONE,
          unread: 2,
          unread_files: [
            { file: "a.fit", reason: "file_unreadable" },
            { file: "b.fit", reason: "header_unreadable" },
          ],
        },
      ]),
    )
    const carta = await screen.findByRole("region", { name: /completata$/ })
    const file = [...carta.querySelectorAll(".al-imp-file")].map((f) => f.textContent)
    expect(file).toEqual([
      "a.fitfile non apribile",
      "b.fitnon è un FITS o l'intestazione è rovinata",
    ])
    // tutti i file sono gia' qui: niente da mostrare in piu'
    expect(within(carta).queryByRole("button", { name: /^mostra tutti/i })).toBeNull()
  })

  it("un elenco dei non leggibili che non arriva lo dice", async () => {
    await app(
      pagina([
        { ...SCANSIONE, unread: 9, unread_files: [{ file: "a.fit", reason: "file_unreadable" }] },
      ]),
      { "unread?limit=1000": { stato: 500, corpo: {} } },
    )
    fireEvent.click(await screen.findByRole("button", { name: "Mostra tutti i 9" }))
    expect(await screen.findByText("Elenco dei file non disponibile.")).toBeDefined()
    expect(screen.getByText("a.fit")).toBeDefined()
  })
})

describe("Impostazioni / Scansioni, i gesti", () => {
  const bloccata = {
    ...SCANSIONE,
    outcome: "blocked",
    reason: "root_unreachable",
    reason_folder: "E:",
    can_retry: true,
  }

  it("Riprova e' pieno e manda il gesto dello stato del lavoro", async () => {
    await app(
      pagina([bloccata]),
      { "POST /api/v1/pipeline/run": { stato: 202, corpo: {} } },
      { ...FERMO, action: "resume" },
    )
    const riprova = await screen.findByRole("button", { name: /^riprova$/i })
    expect(riprova.className).toContain("al-bottone--pieno")
    await waitFor(() => expect(riprova.getAttribute("aria-disabled")).toBeNull())
    fireEvent.click(riprova)
    await waitFor(() =>
      expect(scritture().map((s) => new URL(s.url).pathname)).toEqual(["/api/v1/pipeline/run"]),
    )
  })

  it("un gesto rifiutato lo dice accanto al bottone", async () => {
    await app(pagina([bloccata]), { "POST /api/v1/scan": { stato: 500, corpo: {} } })
    const riprova = await screen.findByRole("button", { name: /^riprova$/i })
    await waitFor(() => expect(riprova.getAttribute("aria-disabled")).toBeNull())
    fireEvent.click(riprova)
    const carta = screen.getByRole("region", { name: /bloccata$/ })
    expect(await within(carta).findByText("Stato della scansione non disponibile")).toBeDefined()
  })

  it("mentre il gesto parte, il bottone e' spento e non riparte", async () => {
    await app(pagina([bloccata]), {
      "POST /api/v1/scan": { stato: 202, corpo: {}, attesa: new Promise(() => {}) },
    })
    const riprova = await screen.findByRole("button", { name: /^riprova$/i })
    await waitFor(() => expect(riprova.getAttribute("aria-disabled")).toBeNull())
    fireEvent.click(riprova)
    await waitFor(() => expect(riprova.getAttribute("aria-disabled")).toBe("true"))
    fireEvent.click(riprova)
    await new Promise((r) => setTimeout(r, 20))
    expect(scritture().filter((s) => s.url.includes("/api/v1/scan"))).toHaveLength(1)
  })

  it("senza lo stato del lavoro Riprova e' spento e non manda niente", async () => {
    window.history.pushState({}, "", "/impostazioni/scansioni")
    rispondi({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/scans": pagina([bloccata]),
      "/api/v1/pipeline/status": { stato: 500, corpo: {} },
    })
    await disegna()
    const riprova = await screen.findByRole("button", { name: /^riprova$/i })
    expect(riprova.getAttribute("aria-disabled")).toBe("true")
    fireEvent.click(riprova)
    await new Promise((r) => setTimeout(r, 20))
    expect(scritture()).toEqual([])
  })
})
