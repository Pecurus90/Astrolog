// @vitest-environment jsdom
/**
 * I **mosaici nell'Archivio**: l'etichetta nelle due viste, la tendina che li isola, una conta
 * che non chiama "oggetto" un mosaico, e i pannelli che si aprono dalla sua carta.
 *
 * Il mosaico arriva dalla rotta gia' fatto -- una riga sola, coi suoi pannelli -- e qui si
 * prova che la pagina lo **dice**, a chi guarda e a chi ascolta. Il banco e' `archivio-banco.tsx`.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { chiamate, pulisci } from "./banco"
import { M31, MOSAICO, SCELTE, apriArchivio, apriArchivioSu, archivio, vaiAll } from "./archivio-banco"

afterEach(pulisci)

const CON_MOSAICI = { choices: { ...SCELTE, mosaics: true }, found: { objects: 1, mosaics: 1 } }

describe("i mosaici nell'Archivio", () => {
  it("la carta di un mosaico dice mosaico e quanti pannelli, e si sente", async () => {
    archivio([MOSAICO, M31], CON_MOSAICI)
    await apriArchivio()

    const carta = (await screen.findByRole("heading", { name: "IC 405" })).closest("article")
    // l'etichetta sta su un'anteprima che, vuota, si tace: qui non deve tacere con lei
    const etichetta = within(carta as HTMLElement).getByText(/mosaico/i)
    expect(etichetta.textContent).toMatch(/mosaico 4 pannelli/)
    expect(etichetta.closest('[aria-hidden="true"]')).toBeNull()
    const altra = screen.getByRole("heading", { name: "M 31" }).closest("article")
    expect((altra as HTMLElement).textContent).not.toMatch(/mosaico/i)
  })

  it("anche nell'elenco la riga del mosaico porta la sua etichetta", async () => {
    archivio([MOSAICO, M31], CON_MOSAICI)
    await apriArchivio()
    await vaiAll(/elenco/i)

    const righe = screen.getAllByRole("row")
    const delMosaico = righe.find((r) => r.textContent?.includes("IC 405"))
    expect(delMosaico?.textContent).toMatch(/mosaico 4 pannelli/)
    expect(righe.find((r) => r.textContent?.includes("M 31"))?.textContent).not.toMatch(/mosaico/)
  })

  it("la conta dice quanti oggetti e quanti mosaici", async () => {
    archivio([MOSAICO, M31], CON_MOSAICI)
    await apriArchivio()

    expect(await screen.findByText("1 oggetto e 1 mosaico")).toBeDefined()
  })

  it("solo mosaici: la conta non parla di oggetti", async () => {
    archivio([MOSAICO], { ...CON_MOSAICI, found: { objects: 0, mosaics: 1 } })
    await apriArchivio()

    expect(await screen.findByText("1 mosaico")).toBeDefined()
  })

  it("la tendina dei mosaici compare solo a chi ne ha, e stringe nel backend", async () => {
    archivio([MOSAICO, M31], CON_MOSAICI)
    await apriArchivio()

    fireEvent.change(await screen.findByLabelText(/^mosaici$/i), { target: { value: "1" } })

    await waitFor(() => expect(window.location.search).toContain("mosaic=1"))
    await waitFor(() =>
      expect(chiamate().some((u) => u.includes("/archive") && u.includes("mosaic=true"))).toBe(true),
    )
  })

  it("chi non ha mosaici non vede la tendina", async () => {
    archivio([M31])
    await apriArchivio()

    await screen.findByLabelText(/catalogo/i)
    expect(screen.queryByLabelText(/^mosaici$/i)).toBeNull()
  })

  it("un indirizzo scritto male non stringe", async () => {
    archivio([M31])
    await apriArchivioSu("/archivio?mosaic=pippo")

    await screen.findByRole("heading", { name: "M 31" })
    expect(chiamate().some((u) => u.includes("mosaic="))).toBe(false)
  })
})

/** Il testo di un pannello come lo legge chi ascolta: gli spazi fra i pezzi contano uno. */
function testoDi(el: HTMLElement) {
  return (el.textContent ?? "").replace(/\s+/g, " ").trim()
}

describe("l'Archivio, i pannelli del mosaico", () => {
  it("la carta del mosaico si apre e dice ogni pannello, con oggetto, frame, ore e dove sta", async () => {
    archivio([MOSAICO])
    await apriArchivio()

    const carta = await screen.findByRole("article")
    const apri = within(carta).getByText(/ogni pannello/i)
    const cassetto = apri.closest("details") as HTMLDetailsElement
    // chiusa di suo: la carta resta alla misura delle altre finche' non la apri tu
    expect(cassetto.open).toBe(false)
    fireEvent.click(apri)
    expect(cassetto.open).toBe(true)

    const pannelli = within(cassetto).getAllByRole("listitem").map(testoDi)
    expect(pannelli).toHaveLength(4)
    // nell'ordine in cui arrivano: dal backend, dal pannello a cui e' andato piu' tempo
    expect(pannelli[0]).toMatch(/^IC 405 40 frame 4 h a RA 79,1 Dec 34,3$/)
    expect(pannelli[1]).toMatch(/^LBN 796, Sh2 230 /)
  })

  it("un pannello di cui il cielo non ha legato l'oggetto lo dice, e le pose senza tempo a parte", async () => {
    archivio([MOSAICO])
    await apriArchivio()

    const cassetto = (await screen.findByRole("article")).querySelector("details") as HTMLElement
    const ultimo = testoDi(within(cassetto).getAllByRole("listitem")[3] as HTMLElement)
    expect(ultimo).toMatch(/^nessun oggetto riconosciuto 20 frame 2 h 2 senza tempo a RA 79,9 Dec 33,1$/)
  })

  it("un oggetto non ha pannelli da aprire", async () => {
    archivio([M31])
    await apriArchivio()

    expect((await screen.findByRole("article")).querySelector("details")).toBeNull()
  })
})
