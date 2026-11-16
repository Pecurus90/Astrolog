// @vitest-environment jsdom
/**
 * Impostazioni, la sezione *Scansioni* (tavola v82, `SezioneServizi`): una carta per gesto, coi
 * suoi esiti, cio' che e' rimasto fuori e i gesti del menu dell'ingranaggio.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  SCANSIONE,
  SPINA,
  STANOTTE,
  type Voce,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  scritture,
} from "./banco"

afterEach(pulisci)

function app(scansioni: unknown[], altre: Record<string, Voce> = {}) {
  window.history.pushState({}, "", "/impostazioni/scansioni")
  rispondi({
    ...altre,
    ...STANOTTE,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/scans": {
      stato: 200,
      corpo: { items: scansioni, total: scansioni.length, limit: 20, offset: 0 },
    },
    ...SPINA,
  })
  return disegna()
}

describe("Impostazioni / Scansioni", () => {
  it("senza scansioni dice come nasce la prima", async () => {
    await app([])
    expect(await screen.findByText("Nessuna scansione ancora")).toBeDefined()
    expect(
      screen.getByText("Aggiungi una cartella in «Cartelle e scansione» e avvia la prima."),
    ).toBeDefined()
  })

  it("una scansione dice quando, quanto, le cartelle, i frame entrati e cosa e' rimasto fuori", async () => {
    await app([
      {
        ...SCANSIONE,
        started_day: "yesterday",
        started_at: "2026-11-15T22:05:00+01:00",
        duration_s: 220,
        folders: ["D:\\Astro\\2026", "E:\\Sole"],
        new: 186,
        left_out: [
          { reason: "unchanged", count: 3 },
          { reason: "duplicates", count: 1 },
        ],
      },
    ])
    const carta = await screen.findByRole("region", { name: /^ieri, 22:05/ })
    expect(within(carta).getByText("3 min 40 s")).toBeDefined()
    expect(within(carta).getByText("✓ completata")).toBeDefined()
    expect(within(carta).getByText("E:\\Sole")).toBeDefined()
    expect(within(carta).getByText("186 frame")).toBeDefined()
    expect(within(carta).getByText("3 già in archivio")).toBeDefined()
    expect(within(carta).getByText("1 duplicato")).toBeDefined()
    // una sola scansione: niente da mostrare prima
    expect(screen.queryByRole("button", { name: /^mostra le scansioni precedenti$/i })).toBeNull()
  })

  it("una bloccata dice perche' e su quale cartella, e Riprova e' il gesto dell'ingranaggio", async () => {
    await app(
      [
        {
          ...SCANSIONE,
          outcome: "blocked",
          reason: "root_unreachable",
          reason_folder: "E:\\Sole",
          can_retry: true,
        },
      ],
      { "POST /api/v1/scan": { stato: 202, corpo: { started: [], skipped: [] } } },
    )
    expect(await screen.findByText(/^La cartella E:\\Sole non risponde/)).toBeDefined()
    fireEvent.click(screen.getByRole("button", { name: /^riprova$/i }))
    await waitFor(() =>
      expect(scritture()).toContainEqual(
        expect.objectContaining({ url: expect.stringContaining("/api/v1/scan"), metodo: "POST" }),
      ),
    )
  })

  it("una in corso ha la barra e Interrompi", async () => {
    await app(
      [
        {
          ...SCANSIONE,
          outcome: "running",
          duration_s: null,
          progress: { read: 7740, total: 18430, pct: 42 },
        },
      ],
      { "POST /api/v1/pipeline/stop": { stato: 200, corpo: {} } },
    )
    expect(await screen.findByRole("progressbar")).toBeDefined()
    expect(screen.getByText(/^7\D?740 file letti su 18\D?430$/)).toBeDefined()
    fireEvent.click(screen.getByRole("button", { name: /^interrompi$/i }))
    await waitFor(() =>
      expect(scritture()).toContainEqual(
        expect.objectContaining({ url: expect.stringContaining("/pipeline/stop"), metodo: "POST" }),
      ),
    )
  })

  it("un elenco di file non piu' conservato lo dice, e non promette di mostrarli", async () => {
    await app([{ ...SCANSIONE, unread: 3, unread_kept: false }])
    expect(await screen.findByText("Non leggibili · 3")).toBeDefined()
    expect(screen.getByText(/conservato solo per l'ultima scansione/)).toBeDefined()
    expect(screen.queryByRole("button", { name: /^mostra tutti/i })).toBeNull()
  })

  it("Mostra tutti porta tutti i file anche oltre la pagina della rotta", async () => {
    const file = (da: number, n: number) =>
      Array.from({ length: n }, (_, i) => ({ file: `F${da + i}.fit`, reason: "file_unreadable" }))
    const pagina = (da: number, n: number) => ({
      stato: 200,
      corpo: { items: file(da, n), total: 1500, limit: 1000, offset: da },
    })
    await app([{ ...SCANSIONE, unread: 1500, unread_kept: true, unread_files: file(0, 5) }], {
      "unread?limit=1000&offset=0": pagina(0, 1000),
      "unread?limit=1000&offset=1000": pagina(1000, 500),
    })
    fireEvent.click(await screen.findByRole("button", { name: /^mostra tutti/i }))
    expect(await screen.findByText("F1499.fit")).toBeDefined()
    expect(screen.getByText("F999.fit")).toBeDefined()
  })

  it("Mostra le precedenti va oltre la pagina della rotta senza perdere le carte", async () => {
    const carte = (da: number, n: number) =>
      Array.from({ length: n }, (_, i) => ({
        ...SCANSIONE,
        id: 1000 - da - i,
        folders: [`S${da + i}`],
      }))
    const pagina = (da: number, n: number): Voce => ({
      stato: 200,
      corpo: { items: carte(da, n), total: 250, limit: n, offset: da },
    })
    const pagine: Record<string, Voce> = { "scans?limit=20&offset=200": pagina(200, 20) }
    for (let n = 20; n <= 200; n += 20) pagine[`scans?limit=${n}&offset=0`] = pagina(0, n)
    await app([], pagine)
    for (let n = 40; n <= 220; n += 20) {
      fireEvent.click(
        await screen.findByRole("button", { name: /^mostra le scansioni precedenti$/i }),
      )
      expect(await screen.findByText(`S${n - 1}`)).toBeDefined()
    }
    expect(screen.queryByText("Scansioni non disponibili.")).toBeNull()
    expect(screen.getByText("S0")).toBeDefined()
  })
})
