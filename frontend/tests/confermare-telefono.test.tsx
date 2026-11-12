// @vitest-environment jsdom
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  STANOTTE,
  vai as apriPagina,
  cartellaSenzaTipo,
  daConfermare,
  disegna,
  doppione,
  impostazioni,
  pulisci,
  rispondi,
  scelta,
  scelto,
} from "./banco"

afterEach(pulisci)

/**
 * *Da confermare* sul telefono (tavola v82, sotto 700 o `?formato=telefono`): prima i **tipi** di
 * domanda, poi **un caso alla volta**. Le domande sono le stesse della pagina larga.
 */

const PAGINA = daConfermare({
  to_confirm: 2,
  lookalikes: [doppione({ id: 4, name: "ATR2600M(USB2.0)", frames: 38, into_id: 1, into_name: "ATR2600M", into_frames: 412 })],
  typeless: [
    cartellaSenzaTipo({ key: "D:/Astro/dark", frames: 120 }),
    cartellaSenzaTipo({ key: "D:/Astro/M51", frames: 30, answer: "light" }),
  ],
})

async function aperta(dove = "/da-confermare?formato=telefono", pagina: unknown = PAGINA) {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review/apply": { stato: 200, corpo: { changed: 1, requeued: 320, run_started: true, none_filter_existed: false } },
    "/api/v1/review": { stato: 200, corpo: pagina },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
  await disegna()
  apriPagina(dove)
  await screen.findByRole("region", { name: "Le modifiche da applicare" })
}

const elenco = () => screen.queryByRole("region", { name: "Tipi di domanda" })
const tipi = () =>
  within(elenco() as HTMLElement)
    .getAllByRole("link")
    .map((b) => [b.querySelector(".al-conf__blocco-5")?.textContent, ...[...b.querySelectorAll(".al-conf__riga-7")].map((s) => s.textContent)])
const tipo = (nome: string) =>
  fireEvent.click(within(elenco() as HTMLElement).getByRole("link", { name: new RegExp(`^${nome}`) }))
// dove si e' sta sopra la colonna delle sezioni (tavola 42), fuori dalla sezione
const dove = () => document.querySelector(".al-conf__riga-8 > .al-conf__blocco-6")?.textContent
const aperte = () => document.querySelectorAll("article.al-conf__colonna-16")
const gesto = (nome: string) => screen.getByRole("button", { name: nome })
const spento = (nome: string) => gesto(nome).getAttribute("aria-disabled") === "true"
const piede = () => screen.getByRole("region", { name: "Le modifiche da applicare" })

describe("Da confermare -- il telefono", () => {
  it("prima i tipi: ognuno dice quante risposte ha, e in che stato; sopra il conto con la regola", async () => {
    await aperta()
    const griglia = document.querySelector(".al-conf__centro-1") as HTMLElement
    expect(griglia.style.gridTemplateColumns).toBe("minmax(0,1fr)")
    expect(griglia.style.gap).toBe("12px")
    const conto = screen.getByRole("region", { name: "Il conto" })
    expect((conto.querySelector(".al-conf__testo-1") as HTMLElement).style.fontSize).toBe("48px")
    expect(conto.querySelector(".al-conf__testo-3")).not.toBeNull()
    expect(tipi()).toEqual([
      ["Strumenti duplicati", "\u25CB1 senza risposta"],
      ["Frame senza tipo", "\u25CB1 senza risposta", "\u27131 salvata"],
    ])
    // nessuna domanda a schermo finche' non si sceglie un tipo, e niente indice
    expect(document.querySelector(".al-conf__colonna-16, .al-conf__centro-2")).toBeNull()
    expect(screen.queryByRole("navigation", { name: "Sezioni" })).toBeNull()
  })

  it("il piede e' una bolla di 64 px staccata a sinistra, e dice solo da applicare", async () => {
    await aperta()
    const bolla = piede()
    expect(bolla.style.minHeight).toBe("64px")
    expect(bolla.style.marginLeft).toBe("76px")
    expect(bolla.style.borderRadius).toBe("32px")
    expect(bolla.querySelector(".al-conf__riga-18")?.textContent).toBe("0da applicare")
  })

  it("scelto un tipo si vede un caso solo, aperto, col nome del tipo e il suo perche'; il conto resta, senza la regola", async () => {
    await aperta()
    tipo("Frame senza tipo")
    expect(dove()).toBe("caso 1 di 2")
    expect(screen.getByRole("heading", { level: 2, name: "Frame senza tipo" })).toBeDefined()
    const sezione = screen.getByRole("region", { name: "Frame senza tipo" })
    expect(sezione.querySelector("p.al-conf__blocco-8")?.textContent).toMatch(/^Tipo di frame non indicato nei file/)
    expect(aperte()).toHaveLength(1)
    expect(aperte()[0]?.getAttribute("aria-label")).toBe("D:/Astro/dark, senza risposta")
    expect(document.querySelector(".al-conf__centro-2")).toBeNull()
    // dove si e' sta sopra la colonna, come si va avanti sotto: fuori dalla sezione
    const colonna = document.querySelector(".al-conf__colonna-11") as HTMLElement
    expect(colonna.previousElementSibling?.className).toBe("al-conf__riga-8")
    expect(colonna.nextElementSibling?.className).toBe("al-conf__griglia-1")
    expect(sezione.contains(gesto("Caso dopo"))).toBe(false)
    expect(elenco()).toBeNull()
    expect(screen.getByRole("region", { name: "Il conto" }).querySelector(".al-conf__testo-3")).toBeNull()
  })

  it("un tipo si apre sulla prima domanda senza risposta, non sempre sul caso 1", async () => {
    await aperta(
      "/da-confermare?formato=telefono",
      daConfermare({
        ...PAGINA,
        typeless: [
          cartellaSenzaTipo({ key: "D:/Astro/M51", frames: 30, answer: "light" }),
          cartellaSenzaTipo({ key: "D:/Astro/dark", frames: 120 }),
        ],
      }),
    )
    tipo("Frame senza tipo")
    expect(dove()).toBe("caso 2 di 2")
    expect(aperte()[0]?.getAttribute("aria-label")).toBe("D:/Astro/dark, senza risposta")
  })

  it("si va di caso in caso, e ai bordi Caso prima e Caso dopo sono spenti", async () => {
    await aperta()
    tipo("Frame senza tipo")
    expect(spento("Caso prima")).toBe(true)
    expect(spento("Caso dopo")).toBe(false)
    // spento non fa niente
    fireEvent.click(gesto("Caso prima"))
    expect(dove()).toBe("caso 1 di 2")
    fireEvent.click(gesto("Caso dopo"))
    expect(dove()).toBe("caso 2 di 2")
    expect(aperte()[0]?.getAttribute("aria-label")).toBe("D:/Astro/M51, salvata")
    expect(spento("Caso prima")).toBe(false)
    expect(spento("Caso dopo")).toBe(true)
    fireEvent.click(gesto("Caso prima"))
    expect(dove()).toBe("caso 1 di 2")
    // niente salto di tipo: si torna ai tipi
    expect(screen.queryByRole("button", { name: /^Tipo (prima|dopo)/ })).toBeNull()
  })

  it("un tipo con un caso solo ha tutti e due i gesti spenti", async () => {
    await aperta()
    tipo("Strumenti duplicati")
    expect(dove()).toBe("caso 1 di 1")
    expect(spento("Caso prima")).toBe(true)
    expect(spento("Caso dopo")).toBe(true)
  })

  it("una risposta data in un caso si legge tornando ai tipi, e il piede la conta", async () => {
    await aperta()
    tipo("Strumenti duplicati")
    fireEvent.click(scelta(document.body, /unisci a ATR2600M/i))
    expect(piede().querySelector(".al-conf__riga-18")?.textContent).toBe("1da applicare")
    // l'unione si dice col tondo, che apre il testo
    const tondo = within(piede()).getByRole("button", { name: /unione di strumenti: mostra l'avviso/ })
    expect(piede().querySelector(".al-conf__blocco-18")).toBeNull()
    fireEvent.click(tondo)
    expect(tondo.getAttribute("aria-expanded")).toBe("true")
    expect(piede().querySelector(".al-conf__blocco-18")?.textContent).toBe("Include un'unione di strumenti: non \u00e8 reversibile.")

    fireEvent.click(screen.getByRole("button", { name: /Tutti i tipi/ }))
    expect(tipi()[0]).toEqual(["Strumenti duplicati", "\u25CF1 da applicare"])
    // e tornando sul caso la risposta e' ancora li'
    tipo("Strumenti duplicati")
    expect(scelto(scelta(document.body, /unisci a ATR2600M/i))).toBe(true)
  })

  it("dall'indirizzo si entra nel caso di una sezione", async () => {
    await aperta("/da-confermare?formato=telefono#frame-senza-tipo")
    expect(dove()).toBe("caso 1 di 2")
    expect(screen.getByRole("heading", { level: 2, name: "Frame senza tipo" })).toBeDefined()
  })

  it("sul desktop la pagina resta quella larga: sezioni e indice", async () => {
    await aperta("/da-confermare?formato=desktop")
    expect(screen.getByRole("navigation", { name: "Sezioni" })).toBeDefined()
    expect(elenco()).toBeNull()
    expect(screen.getByRole("region", { name: "Strumenti duplicati" })).toBeDefined()
  })
})
