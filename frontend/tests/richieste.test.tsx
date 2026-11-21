// @vitest-environment jsdom
/**
 * Le richieste di un caricamento (passo 6.18): nessuna due volte, nessuna che aspetta un'altra
 * senza bisogno, e una pagina riaperta entro `FRESCHI_MS` non rilegge cio' che ha gia'.
 */
import { screen, waitFor } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { attrezzatura } from "./attrezzatura-banco"
import {
  FERMO,
  adesso,
  apriImpostazioni,
  chiamate,
  impostazioni,
  pulisci,
  rispondi,
  vai,
} from "./banco"
import { montaDashboard } from "./dashboard-banco"
import { DICIOTTO, apri, cartaDelMese, mai, pagina, rotte } from "./notti-banco"

afterEach(pulisci)

const quiete = () => new Promise((r) => setTimeout(r, 200))
const senzaOrigine = (u: string) => u.replace(/^https?:\/\/[^/]+/, "")

/** Gli indirizzi chiesti piu' di una volta, con quante. */
function doppie(): Record<string, number> {
  const conta: Record<string, number> = {}
  for (const u of chiamate().map(senzaOrigine)) conta[u] = (conta[u] ?? 0) + 1
  return Object.fromEntries(Object.entries(conta).filter(([, n]) => n > 1))
}

// a run already finished when the app opens: its stamp is not news
const FINITA = { ...FERMO, worker: { ...FERMO.worker, ended_at: "2026-09-30T05:00:00Z" } }

describe("le richieste di un caricamento", () => {
  it("la Dashboard chiede ogni cosa una volta, anche con una corsa gia' finita", async () => {
    await montaDashboard({ altre: { "/api/v1/pipeline/status": { stato: 200, corpo: FINITA } } })
    await screen.findByRole("link", { name: /da confermare/i })
    await quiete()
    expect(doppie()).toEqual({})
  })

  it("tornando sulle pagine entro il minuto non si rilegge niente", async () => {
    await montaDashboard()
    await screen.findByRole("link", { name: /da confermare/i })
    const dashboard = adesso()
    attrezzatura()
    rispondi({ ...dashboard, ...adesso() })
    vai("/attrezzatura")
    await screen.findByRole("heading", { name: /attrezzatura/i })
    await apriImpostazioni()
    await screen.findByRole("heading", { name: /impostazioni/i })
    vai("/")
    vai("/attrezzatura")
    await quiete()
    expect(doppie()).toEqual({})
  })

  it("le domande del telaio partono mentre il cancello aspetta le impostazioni", async () => {
    await montaDashboard({
      altre: { "/api/v1/settings": { stato: 200, corpo: impostazioni(true), attesa: mai } },
    })
    await waitFor(() => {
      const chieste = chiamate().map(senzaOrigine)
      for (const r of ["/api/v1/review", "/api/v1/tonight", "/api/v1/pipeline/status"])
        expect(chieste).toContain(r)
    })
  })
})

describe("il file della pagina", () => {
  it("si chiede prima di montarla, e un fallimento resta zitto", async () => {
    const { pigra } = await import("../src/pigra")
    const carica = vi.fn(() => Promise.reject(new Error("rete giu'")))
    pigra(carica, "Pagina" as never).precarica()
    await Promise.resolve()
    expect(carica).toHaveBeenCalledOnce()
  })
})

describe("le Notti", () => {
  it("il calendario parte insieme alle notti, senza aspettarle", async () => {
    // the key keeps its place after the calendar's: the nights only are held
    await apri({
      ...rotte(pagina([DICIOTTO])),
      "/api/v1/nights": { stato: 200, corpo: pagina([DICIOTTO]), attesa: mai },
    })
    await waitFor(() => expect(chiamate().map(senzaOrigine)).toContain("/api/v1/nights/calendar"))
  })

  it("il mese dell'ultima notte non si chiede una seconda volta col suo nome", async () => {
    await apri(rotte(pagina([DICIOTTO])))
    await cartaDelMese()
    await quiete()
    expect(chiamate().filter((u) => u.includes("/nights/calendar"))).toHaveLength(1)
    expect(doppie()).toEqual({})
  })
})
