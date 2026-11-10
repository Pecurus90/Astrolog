// @vitest-environment jsdom
/**
 * La ricerca e i nove criteri dell'**Archivio** (tavola v78, `Filtri`): le voci arrivano con
 * quante righe darebbero, una scelta va nell'indirizzo e alla rotta, una voce a zero e' spenta.
 * La pagina non filtra niente: stringe il backend (`docs/domini/archivio.md`).
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { chiamate, pulisci, rispondi } from "./banco"
import { INTERO, M31, apriArchivio, apriArchivioSu, archivio, conArchivio } from "./archivio-banco"

afterEach(pulisci)

const chiesteArchivio = () => chiamate().filter((u) => u.includes("/api/v1/archive"))

async function apriCriteri() {
  fireEvent.click(await screen.findByText(/^criteri$/i))
  return (await screen.findAllByRole("group", { name: "Periodo" }))[0] as HTMLElement
}

describe("i criteri dell'Archivio", () => {
  it("i criteri offrono le voci con quante righe darebbero, nell'ordine della tavola", async () => {
    archivio([M31])
    await apriArchivio()
    await apriCriteri()

    const gruppi = screen.getAllByRole("group").map((g) => g.getAttribute("aria-label"))
    expect(
      [...new Set(gruppi)].filter((g) =>
        ["Periodo", "Costellazione", "Filtri", "Sito"].includes(g ?? ""),
      ),
    ).toEqual(["Periodo", "Costellazione", "Filtri", "Sito"])
    const sito = screen.getAllByRole("group", { name: "Sito" })[0] as HTMLElement
    expect(within(sito).getByText("Cima Ekar")).toBeDefined()
    expect(screen.getAllByRole("group", { name: "Costellazione" })[0]?.textContent).toContain(
      "Andromeda",
    )
  })

  it("scegliere una voce la scrive nell'indirizzo e la chiede alla rotta", async () => {
    archivio([M31])
    await apriArchivio()
    const periodo = await apriCriteri()

    fireEvent.click(within(periodo).getByText("2024"))

    await waitFor(() => expect(window.location.search).toContain("year=2024"))
    await waitFor(() => expect(chiesteArchivio().some((u) => u.includes("year=2024"))).toBe(true))
  })

  it("due voci dello stesso criterio vanno insieme, e la rotta le riceve tutte e due", async () => {
    archivio([M31])
    await apriArchivioSu("/archivio?year=2025&year=2024")

    await waitFor(() =>
      expect(
        chiesteArchivio().some((u) => u.includes("year=2025") && u.includes("year=2024")),
      ).toBe(true),
    )
    expect(
      await screen.findByText(/1 oggetto con questi criteri|oggetti con questi criteri/),
    ).toBeDefined()
  })

  it("una voce a zero e' spenta e non si sceglie", async () => {
    archivio([M31])
    await apriArchivio()
    await apriCriteri()

    const costellazione = screen.getAllByRole("group", { name: "Costellazione" })[0] as HTMLElement
    const cygnus = within(costellazione).getByText("Cygnus").closest("a")
    expect(cygnus?.getAttribute("aria-disabled")).toBe("true")
    fireEvent.click(cygnus as HTMLElement)
    expect(window.location.search).not.toContain("constellation=Cyg")
  })

  it("togli i criteri toglie anche il periodo e il setup", async () => {
    archivio([M31])
    await apriArchivioSu("/archivio?year=2024&site=1&q=m31&sort=hours")

    fireEvent.click(await screen.findByText(/^togli i criteri$/i))

    await waitFor(() => expect(window.location.search).toBe("?sort=hours"))
  })

  it("cercare stringe l'elenco nel backend, non a schermo", async () => {
    archivio([M31])
    await apriArchivio()

    fireEvent.change(await screen.findByLabelText(/cerca un oggetto/i), {
      target: { value: "m31" },
    })

    await waitFor(() => expect(chiesteArchivio().some((u) => u.includes("q=m31"))).toBe(true))
    expect(window.location.search).toContain("q=m31")
  })

  it("l'ordine lo sceglie l'utente e lo fa il backend", async () => {
    archivio([M31])
    await apriArchivio()

    fireEvent.change(await screen.findByRole("combobox", { name: /^ordine$/i }), {
      target: { value: "recent" },
    })

    await waitFor(() => expect(chiesteArchivio().some((u) => u.includes("sort=recent"))).toBe(true))
  })

  it("quando un criterio non trova niente lo dice, e lascia il modo di toglierlo", async () => {
    archivio([], { whole: INTERO })
    await apriArchivioSu("/archivio?year=2024")

    expect(await screen.findByText(/^nessun oggetto con questi criteri$/i)).toBeDefined()
    expect(screen.getByText(/^togli i criteri$/i)).toBeDefined()
  })

  it("dice quanti ne ha trovati, non quanti ne stai vedendo", async () => {
    archivio([M31], { total: 600 })
    await apriArchivioSu("/archivio?year=2024")

    expect(await screen.findByText("600 oggetti con questi criteri")).toBeDefined()
  })

  it("un oggetto solo non prende il plurale", async () => {
    archivio([M31], { total: 1 })
    await apriArchivioSu("/archivio?year=2024")

    expect(await screen.findByText("1 oggetto con questi criteri")).toBeDefined()
  })

  it("scrivere non riempie la cronologia, e una parola sola e' una domanda sola", async () => {
    archivio([M31])
    await apriArchivio()
    const prima = window.history.length
    const campo = await screen.findByLabelText(/cerca un oggetto/i)

    for (const parziale of ["m", "m3", "m31"])
      fireEvent.change(campo, { target: { value: parziale } })

    await waitFor(() => expect(window.location.search).toContain("q=m31"))
    expect(window.history.length).toBe(prima)
    expect(chiesteArchivio().filter((u) => /q=m3?(&|$)/.test(u))).toEqual([])
  })

  it("una tendina lascia la sua traccia, e il tasto indietro torna al filtro di prima", async () => {
    archivio([M31])
    await apriArchivio()
    const prima = window.history.length
    const periodo = await apriCriteri()

    fireEvent.click(within(periodo).getByText("2024"))

    await waitFor(() => expect(window.history.length).toBe(prima + 1))
  })

  it("se la rete cade dopo un filtro, la barra resta e il filtro si puo' togliere", async () => {
    archivio([M31])
    await apriArchivio()
    await screen.findByLabelText(/cerca un oggetto/i)
    rispondi(conArchivio({ stato: 500, corpo: { detail: "giu'" } }))

    window.history.pushState(null, "", "/archivio?year=2024")
    fireEvent.popState(window)

    expect(await screen.findByText(/^archivio non disponibile$/i)).toBeDefined()
    expect(screen.getByText(/^togli i criteri$/i)).toBeDefined()
    expect(screen.getByLabelText(/cerca un oggetto/i)).toBeDefined()
  })

  it("un indirizzo scritto male non stringe", async () => {
    archivio([M31])
    await apriArchivioSu("/archivio?site=casa")

    await screen.findByLabelText(/cerca un oggetto/i)
    expect(chiesteArchivio().some((u) => u.includes("site="))).toBe(false)
  })
})
