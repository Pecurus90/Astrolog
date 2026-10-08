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

/** La conta come si legge: i numeri stanno in un `<b>`, quindi il testo e' su piu' nodi. */
const laConta = () => document.querySelector(".as-archivio__conta")?.textContent

describe("i mosaici nell'Archivio", () => {
  it("la carta di un mosaico dice mosaico e quanti pannelli, e si sente", async () => {
    archivio([MOSAICO, M31], CON_MOSAICI)
    await apriArchivio()

    const carta = (await screen.findByRole("heading", { name: "IC 405" })).closest("article")
    // l'etichetta sta su un'anteprima che, vuota, si tace: qui non deve tacere con lei
    const etichetta = within(carta as HTMLElement).getByText(/mosaico/i)
    expect(etichetta.textContent).toMatch(/mosaico \u00b7 4 pannelli/)
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
    expect(delMosaico?.textContent).toMatch(/mosaico \u00b7 4 pannelli/)
    expect(righe.find((r) => r.textContent?.includes("M 31"))?.textContent).not.toMatch(/mosaico/)
  })

  it("la conta dice quanti oggetti e quanti mosaici", async () => {
    archivio([MOSAICO, M31], CON_MOSAICI)
    await apriArchivio()

    await waitFor(() => expect(laConta()).toBe("1 oggetto e 1 mosaico"))
  })

  it("solo mosaici: la conta non parla di oggetti", async () => {
    archivio([MOSAICO], { ...CON_MOSAICI, found: { objects: 0, mosaics: 1 } })
    await apriArchivio()

    await waitFor(() => expect(laConta()).toBe("1 mosaico"))
  })

  it("la tendina dei mosaici compare solo a chi ne ha, e stringe nel backend", async () => {
    archivio([MOSAICO, M31], CON_MOSAICI)
    await apriArchivio()

    // dal v31 e' un interruttore, non una tendina con due voci
    const solo = await screen.findByRole("button", { name: /^solo mosaici$/i })
    expect(solo.getAttribute("aria-pressed")).toBe("false")
    fireEvent.click(solo)

    await waitFor(() => expect(window.location.search).toContain("mosaic=1"))
    expect(solo.getAttribute("aria-pressed")).toBe("true")
    await waitFor(() =>
      expect(chiamate().some((u) => u.includes("/archive") && u.includes("mosaic=true"))).toBe(true),
    )
  })

  it("chi non ha mosaici non vede la tendina", async () => {
    archivio([M31])
    await apriArchivio()

    await screen.findByRole("button", { name: /catalogo/i })
    expect(screen.queryByRole("button", { name: /mosaici/i })).toBeNull()
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
  it("la carta del mosaico dice ogni pannello, con oggetto, frame e ore", async () => {
    archivio([MOSAICO])
    await apriArchivio()

    const carta = await screen.findByRole("article")
    const elenco = within(carta).getByRole("list", { name: /i pannelli/i })
    const pannelli = within(elenco).getAllByRole("listitem").map(testoDi)
    expect(pannelli).toHaveLength(4)
    // nell'ordine in cui arrivano: dal backend, dal pannello a cui e' andato piu' tempo
    expect(pannelli[0]).toMatch(/^1\s*IC 405\s*40 \u00b7 4 h$/)
    expect(pannelli[1]).toMatch(/^2\s*LBN 796, Sh2 230\s*30 \u00b7 3 h$/)
  })

  it("un pannello di cui il cielo non ha legato l'oggetto lo dice, e le pose senza tempo a parte", async () => {
    archivio([MOSAICO])
    await apriArchivio()

    const elenco = within(await screen.findByRole("article")).getByRole("list", { name: /i pannelli/i })
    const ultimo = testoDi(within(elenco).getAllByRole("listitem")[3] as HTMLElement)
    expect(ultimo).toMatch(/^4\s*Nessun oggetto identificato\s*20 \u00b7 2 h 2 senza durata$/)
  })

  it("un oggetto non ha pannelli da aprire", async () => {
    archivio([M31])
    await apriArchivio()

    expect(within(await screen.findByRole("article")).queryByRole("list", { name: /i pannelli/i })).toBeNull()
  })
})
