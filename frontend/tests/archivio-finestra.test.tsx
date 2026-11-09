// @vitest-environment jsdom
/**
 * La **finestra dell'oggetto** (`src/TuttoDellOggetto.tsx`, tavola v76 `Riepilogo` tipo oggetto):
 * il tocco su una carta o sul nome nell'elenco la apre sopra l'Archivio. Scrive cio' che manda
 * `GET /api/v1/objects/{key}`: la testa, le produzioni una alla volta, i setup, il catalogo, le
 * notti.
 */
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { type Voce, chiamate, pulisci, rispondi } from "./banco"
import { IGNOTO, M31, apriArchivio, conArchivio, vaiAll, voceArchivio } from "./archivio-banco"
import { DICIASSETTE, DICIOTTO } from "./notti-banco"

afterEach(pulisci)

const FATTI = {
  key: "m-31",
  common_name: "Galassia di Andromeda",
  type_code: "GALAXY",
  constellation: "And",
  distance: { value: 2.5, unit: "million_ly" },
  extent_ly: 220000,
  distance_pc: null,
  size_arcmin: 190,
  moon: { compare: "more", moons: 6 },
}

const VICINA = { ...FATTI, distance: { value: 2400, unit: "ly" }, distance_pc: 740 }

const FUORI = {
  key: "NGC 7000",
  common_name: null,
  type_code: null,
  constellation: null,
  distance: null,
  extent_ly: null,
  distance_pc: null,
  size_arcmin: null,
  moon: null,
}

function scheda(row: unknown, extra: Record<string, unknown> = {}) {
  return {
    row,
    nights: [
      { night: DICIASSETTE, frames: 20, integration_s: 0, untimed: 20 },
      { night: DICIOTTO, frames: 100, integration_s: 36000, untimed: 0 },
    ],
    first_night: "2024-05-17",
    last_night: "2024-05-18",
    sites: ["Casa", "Cima Ekar"],
    rigs: [],
    facts: FATTI,
    ...extra,
  }
}

async function apriCon(righe: unknown[], oggetti: Record<string, Voce>) {
  rispondi({ ...oggetti, ...conArchivio(voceArchivio(righe)) })
  await apriArchivio()
}

const finestra = () => screen.findByRole("dialog")

describe("la finestra dell'oggetto", () => {
  it("il tocco sulla carta la apre: nome, nome comune, periodo, siti, ore e frame", async () => {
    await apriCon([M31], { "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31) } })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))

    const f = await finestra()
    expect(f.getAttribute("aria-label")).toBe("Riepilogo: M 31")
    expect(await within(f).findByText("Galassia di Andromeda")).toBeDefined()
    expect(within(f).getByText("dal 17 al 18 maggio 2024 · 2 notti, 2 siti")).toBeDefined()
    const siti = [...f.querySelectorAll(".al-c-riepilogo__pillola-1")].map((p) => p.textContent)
    expect(siti).toEqual(["Casa", "Cima Ekar"])
    expect(within(f).getByText("12 h")).toBeDefined()
    expect(within(f).getByText("120 frame")).toBeDefined()
  })

  it("in cielo dice tipo, costellazione, distanza e quanto e' grande accanto alla Luna piena", async () => {
    await apriCon([M31], {
      "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31, { facts: VICINA }) },
    })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))

    const cielo = await within(await finestra()).findByRole("region", { name: "In cielo" })
    expect(cielo.textContent).toMatch(/Andromeda/)
    expect(within(cielo).getByText("Galassia")).toBeDefined()
    expect(within(cielo).getByText("2400 anni luce")).toBeDefined()
    expect(within(cielo).getByText("circa 740 parsec")).toBeDefined()
    expect(within(cielo).getByText("190′ in cielo, più di 6 Lune piene")).toBeDefined()
  })

  it("due siti la stessa notte: una data, due notti; poco piu' di una Luna al singolare", async () => {
    const stessa = { ...DICIOTTO, id: 8, site: "Casa" }
    await apriCon([M31], {
      "/api/v1/objects/m-31": {
        stato: 200,
        corpo: scheda(M31, {
          nights: [
            { night: DICIOTTO, frames: 50, integration_s: 18000, untimed: 0 },
            { night: stessa, frames: 70, integration_s: 25200, untimed: 0 },
          ],
          first_night: "2024-05-18",
          last_night: "2024-05-18",
          facts: { ...VICINA, size_arcmin: 50, moon: { compare: "more", moons: 1 } },
        }),
      },
    })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))

    const f = await finestra()
    expect(await within(f).findByText("il 18 maggio 2024 · 2 notti, 2 siti")).toBeDefined()
    expect(within(f).getByText("50′ in cielo, più di una Luna piena")).toBeDefined()
  })

  it("un oggetto fuori catalogo lo dice, senza inventare tipo e costellazione", async () => {
    await apriCon([IGNOTO], {
      "/api/v1/objects/NGC%207000": {
        stato: 200,
        corpo: scheda(IGNOTO, { facts: FUORI }),
      },
    })
    fireEvent.click(
      within(await screen.findByRole("article")).getByRole("link", { name: "NGC 7000" }),
    )

    const f = await finestra()
    expect(await within(f).findByText("fuori catalogo")).toBeDefined()
    expect(within(f).getByText("Tipo non disponibile")).toBeDefined()
    expect(within(f).getByText("Costellazione non disponibile")).toBeDefined()
    expect(within(f).getByText("Filtri non indicati")).toBeDefined()
  })

  it("le notti portano alla loro pagina, con le ore dell'oggetto e il cielo della notte", async () => {
    await apriCon([M31], { "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31) } })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))

    const notti = await within(await finestra()).findByRole("region", { name: "Le notti" })
    const sabato = within(notti).getByRole("link", {
      name: "Apri la notte di Sabato 18 maggio 2024",
    })
    expect(sabato.getAttribute("href")).toBe("/notti?notte=7")
    expect(sabato.textContent).toMatch(/10 h/)
    expect(sabato.textContent).toMatch(/100 frame/)
    expect(sabato.textContent).toMatch(/69%/)
    // solo il disco e la percentuale: il nome della fase non ci sta nella colonna (tavola 64)
    expect(sabato.querySelector(".al-c-luna__colonna-1")).toBeNull()
    const venerdi = within(notti).getByRole("link", { name: /Venerdì 17 maggio 2024/ })
    expect(venerdi.textContent).toMatch(/senza durata/)
  })

  it("con piu' produzioni le mostra una alla volta, e la scelta la chiede all'API", async () => {
    const due = {
      ...M31,
      productions: [
        { ...M31.productions[0], optics_id: 2, camera_id: 1 },
        { ...M31.productions[0], optics: null, optics_id: null, camera: "ASI533", camera_id: 5 },
      ],
    }
    await apriCon([due], {
      "/api/v1/objects/m-31?production=none": {
        stato: 200,
        corpo: scheda(due, { sites: ["Casa"] }),
      },
      "/api/v1/objects/m-31": { stato: 200, corpo: scheda(due) },
    })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))

    const f = await finestra()
    const schede = await within(f).findAllByRole("tab")
    expect(schede.map((s) => s.getAttribute("aria-selected"))).toEqual(["true", "false"])
    expect(chiamate().some((u) => u.includes("production=2%3A1"))).toBe(true)
    expect(schede[1]?.textContent).toMatch(/ottica non indicata.*ASI533/)

    fireEvent.click(schede[1] as HTMLElement)
    expect(chiamate().some((u) => u.includes("production=none%3A5"))).toBe(true)
  })

  it("una produzione sola non ha linguette", async () => {
    await apriCon([M31], { "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31) } })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))
    const f = await finestra()
    await within(f).findByText("Galassia di Andromeda")
    expect(within(f).queryByRole("tab")).toBeNull()
  })

  it("un oggetto che non c'e' piu' lo dice", async () => {
    await apriCon([M31], {
      "/api/v1/objects/m-31": { stato: 404, corpo: { detail: "object_not_found" } },
    })
    fireEvent.click(within(await screen.findByRole("article")).getByRole("link", { name: "M 31" }))
    expect(await within(await finestra()).findByText("Oggetto non trovato")).toBeDefined()
  })

  it("le frecce vanno all'oggetto prima e dopo nell'ordine della pagina, Esc chiude", async () => {
    await apriCon([M31, IGNOTO], {
      "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31) },
      "/api/v1/objects/NGC%207000": { stato: 200, corpo: scheda(IGNOTO, { facts: FUORI }) },
    })
    const [prima] = await screen.findAllByRole("article")
    fireEvent.click(within(prima as HTMLElement).getByRole("link", { name: "M 31" }))

    let f = await finestra()
    expect(
      within(f).getByRole("link", { name: "L’oggetto prima" }).getAttribute("aria-disabled"),
    ).toBe("true")
    fireEvent.click(within(f).getByRole("link", { name: "L’oggetto dopo" }))
    f = await finestra()
    expect(f.getAttribute("aria-label")).toBe("Riepilogo: NGC 7000")

    fireEvent.keyDown(f, { key: "Escape" })
    expect(screen.queryByRole("dialog")).toBeNull()
  })

  it("nell'elenco il nome apre la stessa finestra", async () => {
    await apriCon([M31], { "/api/v1/objects/m-31": { stato: 200, corpo: scheda(M31) } })
    await vaiAll(/elenco/i)
    fireEvent.click(await screen.findByRole("link", { name: "M 31" }))
    expect((await finestra()).getAttribute("aria-label")).toBe("Riepilogo: M 31")
  })
})
