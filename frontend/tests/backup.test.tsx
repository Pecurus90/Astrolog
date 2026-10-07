// @vitest-environment jsdom
/**
 * Il backup delle risposte (ADR 0017): su un database nuovo con il file accanto, prima del primo
 * avvio l'app chiede se rimettere le risposte; in Impostazioni si vede dove sta il file.
 */
import { fireEvent, screen, waitFor } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, SPINA, STANOTTE, disegna, impostazioni, pulisci, rispondi, scritture } from "./banco"

afterEach(pulisci)

const CONTI = {
  written_at: "2026-10-06T20:15:00Z",
  sites: 1,
  folders: 2,
  instruments: 3,
  filters: 1,
  answers: 42,
}

function app(offer: "found" | "none", fatto: boolean) {
  rispondi({
    ...STANOTTE,
    ...SPINA,
    "POST /api/v1/backup/restore": { stato: 200, corpo: { offer: "none", last: CONTI, unreadable: false, path: "x" } },
    "POST /api/v1/scan": { stato: 202, corpo: {} },
    "/api/v1/backup": {
      stato: 200,
      corpo: { offer, last: CONTI, unreadable: false, path: "C:\\dati\\risposte.json" },
    },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(fatto) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
  return disegna()
}

describe("Il backup delle risposte", () => {
  it("su un database nuovo chiede di rimetterle, prima del primo avvio", async () => {
    await app("found", false)
    expect(await screen.findByText(/ho trovato le tue risposte/i)).toBeDefined()
    expect(screen.getByText(/42 risposte, 1 siti, 2 cartelle, 4 pezzi/i)).toBeDefined()

    fireEvent.click(screen.getByRole("button", { name: /rimettile/i }))

    await waitFor(() => {
      const fatte = scritture().map((s) => `${s.metodo} ${new URL(s.url).pathname}`)
      expect(fatte).toContain("POST /api/v1/backup/restore")
      expect(fatte).toContain("POST /api/v1/scan")
    })
  })

  it("senza nulla da proporre non chiede niente", async () => {
    await app("none", true)
    await screen.findByRole("navigation", { name: /pagine/i })
    expect(screen.queryByText(/ho trovato le tue risposte/i)).toBeNull()
  })

  it("in Impostazioni dice dove sta il file e quando e' stato scritto", async () => {
    window.history.pushState({}, "", "/impostazioni/backup")
    await app("none", true)
    expect(await screen.findByText(/il backup delle risposte/i)).toBeDefined()
    expect(await screen.findByText("C:\\dati\\risposte.json")).toBeDefined()
  })
})
