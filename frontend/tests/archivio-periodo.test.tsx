// @vitest-environment jsdom
/**
 * La barra dell'Archivio stringe anche per **periodo, sito, ottica e camera**. Le ore ristrette le
 * conta il backend (`backend/tests/test_spine_archive_scope.py`); qui si prova che le scelte
 * arrivano alla rotta, e che si leggono col nome e non con un numero.
 */
import { fireEvent, screen, waitFor } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { cambia, chiamate, pulisci } from "./banco"
import {
  M31,
  SCELTE,
  apriArchivio,
  apriArchivioSu,
  archivio,
  conArchivio,
  laTendina,
  scegli,
  vociDi,
} from "./archivio-banco"

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

    expect(await vociDi(/periodo/i)).toEqual(["Sempre", ...SCELTE.years, "Scegli le date"])
    fireEvent.click(screen.getByRole("menuitemradio", { name: "2025" }))

    await waitFor(() => expect(window.location.search).toContain("period=2025"))
    await allaRotta("since=2025-01-01&until=2025-12-31")
  })

  it("scegliere le date apre dal e al, e una stagione a cavallo d'anno arriva intera", async () => {
    archivio([M31])
    await apriArchivio()
    expect(screen.queryByLabelText(/^dal$/i)).toBeNull()

    await scegli(/periodo/i, "Scegli le date")
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

    // con le date a schermo la tendina non c'e': si torna a "sempre", e da li' all'anno
    fireEvent.click(await screen.findByRole("button", { name: /togli il periodo/i }))
    await scegli(/periodo/i, "2024")

    await waitFor(() => expect(window.location.search).toContain("period=2024"))
    expect(window.location.search).not.toContain("since=")
    expect(window.location.search).not.toContain("until=")
    // e alla rotta arriva l'anno intero, non le date di prima
    await allaRotta("since=2024-01-01&until=2024-12-31")
  })

  it("cambiata una data, il segno dell'attesa sta sul periodo finche' la risposta non arriva", async () => {
    // Le righe possono essere zero, ed e' li' che il segno serve: senza, sotto resterebbe il
    // "niente trovato" della domanda vecchia e nessuno direbbe che ne e' partita una nuova.
    archivio([M31])
    await apriArchivioSu("/archivio?period=date&since=2026-08-01")
    const al = await screen.findByLabelText(/^al$/i)
    const periodo = al.closest(".as-dal-al")
    expect(periodo?.querySelector(".as-attesa")).toBeNull()

    let liberala = () => {}
    cambia(
      conArchivio({
        stato: 200,
        corpo: { items: [], total: 0, limit: 100, offset: 0, choices: SCELTE },
        attesa: new Promise<unknown>((r) => (liberala = () => r(null))),
      }),
    )
    fireEvent.change(al, { target: { value: "2026-08-20" } })

    await waitFor(() => expect(periodo?.querySelector(".as-attesa")).not.toBeNull())
    // uno solo, su chi ha chiesto
    expect(periodo?.closest(".as-restringi")?.querySelectorAll(".as-attesa")).toHaveLength(1)
    liberala()
    await waitFor(() => expect(periodo?.querySelector(".as-attesa")).toBeNull())
  })

  it("Togli il periodo riporta a sempre", async () => {
    archivio([M31])
    await apriArchivioSu("/archivio?period=date&since=2026-08-01")
    await screen.findByRole("group", { name: /periodo/i })
    // con le date, la tendina del periodo non c'e': di quel nome resta solo la x
    const diNome = screen.getAllByRole("button", { name: /periodo/i })
    expect(diNome.filter((b) => b.classList.contains("as-tendina"))).toEqual([])

    fireEvent.click(await screen.findByRole("button", { name: /togli il periodo/i }))

    await waitFor(() => expect(window.location.search).not.toContain("period="))
    expect(window.location.search).not.toContain("since=")
    expect((await laTendina(/periodo/i)).querySelector("b")?.textContent).toBe("sempre")
    expect(screen.queryByRole("group", { name: /periodo/i })).toBeNull()
    expect(screen.queryByLabelText(/^dal$/i)).toBeNull()
  })

  it("se al viene prima di dal lo dice, e il campo e' segnato", async () => {
    // Due date scambiate non trovano niente: senza un motivo sembrerebbe un archivio vuoto.
    archivio([M31])
    await apriArchivioSu("/archivio?period=date&since=2026-08-01&until=2026-07-15")

    const errore = await screen.findByText(/viene prima di/i)
    expect(errore.closest(".as-dal-al__errore")).not.toBeNull()
    const al = screen.getByLabelText(/^al$/i)
    expect(al.getAttribute("aria-invalid")).toBe("true")
    // il solo campo segnato e' quello sbagliato
    expect(screen.getByLabelText(/^dal$/i).hasAttribute("aria-invalid")).toBe(false)

    // con le date in ordine non lo dice piu'
    fireEvent.change(al, { target: { value: "2026-08-20" } })

    await waitFor(() => expect(window.location.search).toContain("until=2026-08-20"))
    await waitFor(() => expect(screen.queryByText(/viene prima di/i)).toBeNull())
    expect(screen.getByLabelText(/^al$/i).hasAttribute("aria-invalid")).toBe(false)
  })

  it("sito, ottica e camera si leggono col nome e stringono per quello", async () => {
    archivio([M31], { choices: CORREDO })
    await apriArchivio()

    expect(await vociDi(/^ottica/i)).toEqual(["Tutte le ottiche", "Newton", "Rifrattore"])
    fireEvent.click(screen.getByRole("menuitemradio", { name: "Newton" }))
    await allaRotta("optics=5")
    await scegli(/^camera/i, "ASI533")
    await allaRotta("camera=8")
    await scegli(/^sito/i, "Deserto")
    await allaRotta("site=2")
  })

  it("con un sito solo, o una camera sola, la tendina non c'e'", async () => {
    // Il backend manda vuoto quando la scelta e' una sola: sceglierla non stringerebbe niente.
    archivio([M31])
    await apriArchivio()
    await screen.findByRole("button", { name: /periodo/i })

    expect(screen.queryByRole("button", { name: /^sito/i })).toBeNull()
    expect(screen.queryByRole("button", { name: /^ottica/i })).toBeNull()
    expect(screen.queryByRole("button", { name: /^camera/i })).toBeNull()
  })

  it("una data o un id storti nell'indirizzo non stringono e non rompono la pagina", async () => {
    // Un indirizzo scritto a mano: mandato alla rotta sarebbe un 422, e alla prima risposta la
    // barra non comparirebbe. Come un ordine inventato, non stringe.
    archivio([M31], { choices: CORREDO })
    await apriArchivioSu("/archivio?period=date&since=pippo&until=2025-02-28&site=abc&optics=5x")

    await allaRotta("until=2025-02-28")
    const sbagliate = chiamate().filter((u) => /since=|site=|optics=/.test(u))
    expect(sbagliate).toEqual([])
    // la barra c'e', col periodo a giorni: la tendina del periodo ha lasciato il posto alle date
    expect(await screen.findByRole("group", { name: /periodo/i })).toBeDefined()
    expect(screen.getByLabelText(/^al$/i)).toHaveProperty("value", "2025-02-28")
  })

  it("togli i filtri toglie anche il periodo e il corredo", async () => {
    archivio([], { choices: CORREDO, found: { objects: 0, mosaics: 0 }, total: 0 })
    await apriArchivioSu("/archivio?period=date&since=2030-01-01&optics=5&camera=7&site=1")

    // due bottoni lo dicono, quello della barra e quello del vuoto: tolgono le stesse cose
    const togli = await screen.findAllByRole("button", { name: /togli i filtri/i })
    expect(togli).toHaveLength(2)
    fireEvent.click(togli[1] as HTMLElement)

    await waitFor(() => expect(window.location.search).toBe(""))
  })
})
