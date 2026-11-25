// @vitest-environment jsdom
/**
 * I gesti del backup (ADR 0017, tavola v82): Inizia da zero e Ripristina nel primo avvio, Esporta
 * e Importa nelle Impostazioni, con l'attesa e gli errori di ognuno. Il resto in `backup.test.tsx`.
 */
import { fireEvent, screen, waitFor } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import {
  SALUTE,
  SPINA,
  STANOTTE,
  type Voce,
  chiamate,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  scritture,
  tornaSullaScheda,
} from "./banco"

afterEach(pulisci)

const CONTI = {
  written_at: "2026-10-06T20:15:00Z",
  sites: 1,
  folders: 2,
  instruments: 3,
  filters: 1,
  answers: 42,
}
const STATO = {
  offer: "none",
  last: CONTI,
  unreadable: false,
  path: "C:\\dati\\risposte.json",
  size_bytes: 47104,
  written_day: "today",
}

function app(fatto: boolean, voci: Record<string, Voce>) {
  rispondi({
    ...voci,
    ...STANOTTE,
    ...SPINA,
    "GET /api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
    "GET /api/v1/folders": { stato: 200, corpo: { items: [], total: 0 } },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(fatto) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
  return disegna()
}

const letture = () => chiamate().filter((u) => new URL(u).pathname === "/api/v1/backup").length
const fatte = () => scritture().map((s) => `${s.metodo} ${new URL(s.url).pathname}`)

describe("il backup trovato al primo avvio", () => {
  it("Inizia da zero lo rifiuta, rilegge lo stato e apre il primo avvio", async () => {
    const stato: Voce = { stato: 200, corpo: { ...STATO, offer: "found" } }
    await app(false, {
      "POST /api/v1/backup/decline": { stato: 200, corpo: {} },
      "/api/v1/backup": stato,
    })
    await screen.findByText(/^backup trovato$/i)
    const prima = letture()
    stato.corpo = { ...STATO, offer: "none" }
    fireEvent.click(screen.getByRole("button", { name: /^inizia da zero$/i }))
    await waitFor(() => expect(fatte()).toContain("POST /api/v1/backup/decline"))
    await waitFor(() => expect(letture()).toBeGreaterThan(prima))
    expect(await screen.findByRole("button", { name: /salta/i })).toBeDefined()
    expect(fatte()).not.toContain("POST /api/v1/backup/restore")
  })

  it("un rifiuto che non arriva lo dice e resta sulla domanda", async () => {
    await app(false, {
      "POST /api/v1/backup/decline": { stato: 500, corpo: {} },
      "/api/v1/backup": { stato: 200, corpo: { ...STATO, offer: "found" } },
    })
    fireEvent.click(await screen.findByRole("button", { name: /^inizia da zero$/i }))
    expect(await screen.findByText("Stato del backup non disponibile.")).toBeDefined()
    expect(screen.getByText(/^backup trovato$/i)).toBeDefined()
  })

  it("un ripristino che non riesce lo dice e non rilegge le cartelle", async () => {
    await app(false, {
      "POST /api/v1/backup/restore": { stato: 500, corpo: {} },
      "POST /api/v1/scan": { stato: 202, corpo: {} },
      "/api/v1/backup": { stato: 200, corpo: { ...STATO, offer: "found" } },
    })
    fireEvent.click(await screen.findByRole("button", { name: /^ripristina$/i }))
    expect(await screen.findByText("Ripristino non riuscito.")).toBeDefined()
    expect(fatte()).not.toContain("POST /api/v1/scan")
  })

  it("mentre ripristina lo dice, e Inizia da zero e' spento", async () => {
    await app(false, {
      "POST /api/v1/backup/restore": { stato: 200, corpo: {}, attesa: new Promise(() => {}) },
      "POST /api/v1/backup/decline": { stato: 200, corpo: {} },
      "/api/v1/backup": { stato: 200, corpo: { ...STATO, offer: "found" } },
    })
    fireEvent.click(await screen.findByRole("button", { name: /^ripristina$/i }))
    const occupato = await screen.findByRole("button", { name: "Ripristino\u2026" })
    expect(occupato.getAttribute("aria-busy")).toBe("true")
    const zero = screen.getByRole("button", { name: /^inizia da zero$/i })
    expect(zero.getAttribute("aria-disabled")).toBe("true")
    fireEvent.click(zero)
    await new Promise((r) => setTimeout(r, 20))
    expect(fatte()).not.toContain("POST /api/v1/backup/decline")
  })
})

describe("il backup nelle Impostazioni", () => {
  function impostazioniBackup(voci: Record<string, Voce>) {
    window.history.pushState({}, "", "/impostazioni/backup")
    return app(true, voci)
  }

  it("Esporta scarica risposte.json dal database", async () => {
    const crea = vi.fn(() => "blob:risposte")
    const togli = vi.fn()
    Object.assign(URL, { createObjectURL: crea, revokeObjectURL: togli })
    const clic = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {})
    try {
      await impostazioniBackup({
        "/api/v1/backup/export": { stato: 200, corpo: { version: 1 } },
        "/api/v1/backup": { stato: 200, corpo: STATO },
      })
      fireEvent.click(await screen.findByRole("button", { name: /^esporta$/i }))
      await waitFor(() => expect(clic).toHaveBeenCalled())
      const link = clic.mock.contexts.at(-1) as HTMLAnchorElement
      expect(link.download).toBe("risposte.json")
      expect(link.href).toBe("blob:risposte")
      expect(crea).toHaveBeenCalledWith(expect.any(Blob))
      expect(togli).toHaveBeenCalledWith("blob:risposte")
    } finally {
      clic.mockRestore()
    }
  })

  it("un Esporta che non riesce lo dice", async () => {
    await impostazioniBackup({
      "/api/v1/backup/export": { stato: 500, corpo: {} },
      "/api/v1/backup": { stato: 200, corpo: STATO },
    })
    fireEvent.click(await screen.findByRole("button", { name: /^esporta$/i }))
    expect(await screen.findByText("Esportazione non riuscita.")).toBeDefined()
  })

  it("un file mai scritto non si esporta nemmeno cliccando", async () => {
    await impostazioniBackup({
      "/api/v1/backup/export": { stato: 200, corpo: {} },
      "/api/v1/backup": {
        stato: 200,
        corpo: { ...STATO, last: null, size_bytes: null, written_day: null },
      },
    })
    fireEvent.click(await screen.findByRole("button", { name: /^esporta$/i }))
    await new Promise((r) => setTimeout(r, 20))
    expect(chiamate().some((u) => u.includes("/backup/export"))).toBe(false)
  })

  it("Importa apre la scelta del file, e un file buono entra e fa rileggere le cartelle", async () => {
    const { container } = await impostazioniBackup({
      "POST /api/v1/backup/import": { stato: 200, corpo: {} },
      "POST /api/v1/scan": { stato: 202, corpo: {} },
      "/api/v1/backup": { stato: 200, corpo: STATO },
    })
    const importa = await screen.findByRole("button", { name: /^importa$/i })
    const scelta = container.querySelector<HTMLInputElement>('input[type="file"]')!
    const apre = vi.spyOn(scelta, "click").mockImplementation(() => {})
    fireEvent.click(importa)
    expect(apre).toHaveBeenCalledTimes(1)

    const file = new File(
      ['{"version": 1, "folders": [{"root_path": "D:/Astro"}]}'],
      "risposte.json",
      {
        type: "application/json",
      },
    )
    fireEvent.change(scelta, { target: { files: [file] } })
    expect(await screen.findByText("Risposte importate: le cartelle si rileggono.")).toBeDefined()
    expect(scritture().find((s) => s.url.includes("/backup/import"))?.corpo).toEqual({
      version: 1,
      folders: [{ root_path: "D:/Astro" }],
    })
    await waitFor(() => expect(fatte()).toContain("POST /api/v1/scan"))
    expect(screen.queryByText("Ripristino non riuscito")).toBeNull()
  })

  it("un file senza cartelle entra senza chiedere una scansione (collaudo 18/11)", async () => {
    const { container } = await impostazioniBackup({
      "POST /api/v1/backup/import": { stato: 200, corpo: {} },
      "POST /api/v1/scan": { stato: 409, corpo: { detail: { code: "no_folders" } } },
      "/api/v1/backup": { stato: 200, corpo: STATO },
    })
    await screen.findByRole("button", { name: /^importa$/i })
    const scelta = container.querySelector<HTMLInputElement>('input[type="file"]')!
    const file = new File(['{"version": 1, "answers": []}'], "risposte.json", {
      type: "application/json",
    })
    fireEvent.change(scelta, { target: { files: [file] } })
    await waitFor(() => expect(fatte()).toContain("POST /api/v1/backup/import"))
    await new Promise((r) => setTimeout(r, 50))
    expect(fatte()).not.toContain("POST /api/v1/scan")
  })

  it("un file che non e' JSON non parte, e lo dice sotto i gesti", async () => {
    const { container } = await impostazioniBackup({
      "/api/v1/backup": { stato: 200, corpo: STATO },
    })
    await screen.findByRole("button", { name: /^importa$/i })
    const scelta = container.querySelector<HTMLInputElement>('input[type="file"]')!
    fireEvent.change(scelta, { target: { files: [new File(["non json"], "x.json")] } })
    expect(await screen.findByText("File di backup non valido.")).toBeDefined()
    expect(screen.queryByText("Ripristino non riuscito")).toBeNull()
    expect(fatte()).not.toContain("POST /api/v1/backup/import")
  })

  it("un 422 senza cartella e' un file non valido, e non si rilegge niente", async () => {
    const { container } = await impostazioniBackup({
      "POST /api/v1/backup/import": { stato: 422, corpo: { detail: [{ msg: "bad" }] } },
      "POST /api/v1/scan": { stato: 202, corpo: {} },
      "/api/v1/backup": { stato: 200, corpo: STATO },
    })
    await screen.findByRole("button", { name: /^importa$/i })
    const scelta = container.querySelector<HTMLInputElement>('input[type="file"]')!
    fireEvent.change(scelta, { target: { files: [new File(['{"version": 1}'], "x.json")] } })
    expect(await screen.findByText("File di backup non valido.")).toBeDefined()
    expect(fatte()).not.toContain("POST /api/v1/scan")
  })

  it("una rilettura dello stato che non arriva lo dice, e Riprova lo richiede", async () => {
    const stato: Voce = { stato: 200, corpo: STATO }
    await impostazioniBackup({ "/api/v1/backup": stato })
    await screen.findByRole("region", { name: "il file delle risposte" })
    expect(screen.queryByText("Stato del backup non disponibile.")).toBeNull()
    stato.stato = 500
    tornaSullaScheda()
    expect(await screen.findByText("Stato del backup non disponibile.")).toBeDefined()
    const prima = letture()
    fireEvent.click(screen.getByRole("button", { name: "Riprova" }))
    await waitFor(() => expect(letture()).toBeGreaterThan(prima))
  })
})
