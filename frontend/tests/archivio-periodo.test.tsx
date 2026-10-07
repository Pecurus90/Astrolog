// @vitest-environment jsdom
/**
 * La barra dell'Archivio stringe anche per **periodo, sito, ottica e camera**. Le ore ristrette le
 * conta il backend (`backend/tests/test_spine_archive_scope.py`); qui si prova che le scelte
 * arrivano alla rotta, e che si leggono col nome e non con un numero.
 */
import { fireEvent, screen, waitFor } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { chiamate, pulisci } from "./banco"
import { M31, SCELTE, apriArchivio, apriArchivioSu, archivio } from "./archivio-banco"

afterEach(pulisci)

const CORREDO = {
  ...SCELTE,
  sites: [
    { id: 1, name: "Casa" },
    { id: 2, name: "Deserto" },
  ],
  optics: [
    { id: 5, name: "Newton" },
    { id: 6, name: "Rifrattore" },
  ],
  cameras: [
    { id: 7, name: "ASI2600" },
    { id: 8, name: "ASI533" },
  ],
}

const allaRotta = (pezzo: string) =>
  waitFor(() =>
    expect(chiamate().some((u) => u.includes("/archive") && u.includes(pezzo))).toBe(true),
  )

describe("l'Archivio per periodo e corredo", () => {
  it("un anno chiede le notti dal primo gennaio al trentuno dicembre", async () => {
    archivio([M31])
    await apriArchivio()

    const periodo = (await screen.findByLabelText(/periodo/i)) as HTMLSelectElement
    expect([...periodo.options].map((o) => o.textContent)).toEqual([
      "Sempre",
      ...SCELTE.years,
      "Scegli le date",
    ])
    fireEvent.change(periodo, { target: { value: "2025" } })

    await waitFor(() => expect(window.location.search).toContain("period=2025"))
    await allaRotta("since=2025-01-01&until=2025-12-31")
  })

  it("scegliere le date apre dal e al, e una stagione a cavallo d'anno arriva intera", async () => {
    archivio([M31])
    await apriArchivio()
    expect(screen.queryByLabelText(/^dal$/i)).toBeNull()

    fireEvent.change(await screen.findByLabelText(/periodo/i), { target: { value: "date" } })
    fireEvent.change(await screen.findByLabelText(/^dal$/i), { target: { value: "2024-11-01" } })
    fireEvent.change(await screen.findByLabelText(/^al$/i), { target: { value: "2025-02-28" } })

    await allaRotta("since=2024-11-01&until=2025-02-28")
  })

  it("una data battuta a tastiera arriva intera, senza fermarsi agli anni a meta'", async () => {
    archivio([M31])
    await apriArchivioSu("/archivio?period=date")

    const al = (await screen.findByLabelText(/^al$/i)) as HTMLInputElement
    for (const passo of ["0002-02-28", "0020-02-28", "0202-02-28"]) {
      fireEvent.change(al, { target: { value: passo } })
      expect(window.location.search).not.toContain("until=")
      expect(al.value).toBe(passo)
    }
    fireEvent.change(al, { target: { value: "2025-02-28" } })

    await allaRotta("until=2025-02-28")
    expect(al.value).toBe("2025-02-28")
  })

  it("tornare a un anno dimentica le date scelte prima", async () => {
    archivio([M31])
    await apriArchivioSu("/archivio?period=date&since=2024-11-01&until=2025-02-28")

    fireEvent.change(await screen.findByLabelText(/periodo/i), { target: { value: "2024" } })

    await waitFor(() => expect(window.location.search).toContain("period=2024"))
    expect(window.location.search).not.toContain("since=")
  })

  it("sito, ottica e camera si leggono col nome e stringono per quello", async () => {
    archivio([M31], { choices: CORREDO })
    await apriArchivio()

    const ottica = (await screen.findByLabelText(/ottica/i)) as HTMLSelectElement
    expect([...ottica.options].map((o) => o.textContent)).toEqual([
      "Tutte le ottiche",
      "Newton",
      "Rifrattore",
    ])
    fireEvent.change(ottica, { target: { value: "5" } })
    await allaRotta("optics=5")
    fireEvent.change(screen.getByLabelText(/^camera$/i), { target: { value: "8" } })
    await allaRotta("camera=8")
    fireEvent.change(screen.getByLabelText(/^sito$/i), { target: { value: "2" } })
    await allaRotta("site=2")
  })

  it("con un sito solo, o una camera sola, la tendina non c'e'", async () => {
    // Il backend manda vuoto quando la scelta e' una sola: sceglierla non stringerebbe niente.
    archivio([M31])
    await apriArchivio()
    await screen.findByLabelText(/periodo/i)

    expect(screen.queryByLabelText(/^sito$/i)).toBeNull()
    expect(screen.queryByLabelText(/ottica/i)).toBeNull()
    expect(screen.queryByLabelText(/^camera$/i)).toBeNull()
  })

  it("una data o un id storti nell'indirizzo non stringono e non rompono la pagina", async () => {
    // Un indirizzo scritto a mano: mandato alla rotta sarebbe un 422, e alla prima risposta la
    // barra non comparirebbe. Come un ordine inventato, non stringe.
    archivio([M31], { choices: CORREDO })
    await apriArchivioSu("/archivio?period=date&since=pippo&until=2025-02-28&site=abc&optics=5x")

    await allaRotta("until=2025-02-28")
    const sbagliate = chiamate().filter((u) => /since=|site=|optics=/.test(u))
    expect(sbagliate).toEqual([])
    expect(await screen.findByLabelText(/periodo/i)).toBeDefined()
  })

  it("togli i filtri toglie anche il periodo e il corredo", async () => {
    archivio([], { choices: CORREDO, found: { objects: 0, mosaics: 0 }, total: 0 })
    await apriArchivioSu("/archivio?period=date&since=2030-01-01&optics=5&camera=7&site=1")

    fireEvent.click(await screen.findByRole("button", { name: /togli i filtri/i }))

    await waitFor(() => expect(window.location.search).toBe(""))
  })
})
