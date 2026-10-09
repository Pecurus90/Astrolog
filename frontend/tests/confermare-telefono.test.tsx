// @vitest-environment jsdom
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { SALUTE, STANOTTE, disegna, impostazioni, pulisci, rispondi } from "./banco"

afterEach(pulisci)

/**
 * *Da confermare* sul telefono (colonna sotto i 900): prima i **tipi** di domanda, poi **un caso
 * alla volta**. Le domande e le risposte sono le stesse della pagina larga: cambia come ci si arriva.
 */

const PAGINA = {
  to_confirm: 3,
  lookalikes: [{ id: 4, name: "ATR2600M(USB2.0)", frames: 38, into_id: 1, into_name: "ATR2600M", into_frames: 412 }],
  filters: [],
  filter_choices: [],
  objects: [],
  gear: [],
  rig_choices: [],
  optics_choices: [],
  settled_objects: 0,
  unclear: [],
  mosaics: [],
  typeless: [
    { key: "D:/Astro/dark", frames: 120, answer: null },
    { key: "D:/Astro/M51", frames: 30, answer: "light" },
  ],
}

/** La colonna misurata stretta: jsdom non impagina, quindi la misura la da' la prova. */
function colonna(larga: number) {
  vi.stubGlobal(
    "ResizeObserver",
    class {
      constructor(private dice: (v: { contentRect: { width: number } }[]) => void) {}
      observe() {
        this.dice([{ contentRect: { width: larga } }])
      }
      disconnect() {}
    },
  )
}

async function aperta(larga = 390) {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review/apply": { stato: 200, corpo: { changed: 1, requeued: 320, run_started: true } },
    "/api/v1/review": { stato: 200, corpo: PAGINA },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
  // dopo `rispondi`: il banco non deve togliere la misura
  colonna(larga)
  await disegna()
  fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
  await screen.findByRole("region", { name: "Modifiche da applicare" })
}

const tipi = () =>
  within(screen.getByRole("list", { name: "Tipi di domanda" }))
    .getAllByRole("button")
    .map((b) => [b.querySelector(".as-conferma-tipo__nome")?.textContent, ...[...b.querySelectorAll(".as-risposta")].map((s) => s.textContent)])
const tipo = (nome: string) =>
  fireEvent.click(within(screen.getByRole("list", { name: "Tipi di domanda" })).getByRole("button", { name: new RegExp(`^${nome}`) }))
const dove = () => document.querySelector(".as-conferma-caso__quale")?.textContent
const vai = () => [...document.querySelectorAll(".as-conferma-caso__vai button")].map((b) => b.textContent)

describe("Da confermare -- il telefono", () => {
  it("prima i tipi: ognuno dice quante risposte ha, e in che stato", async () => {
    await aperta()
    expect(document.querySelector(".as-conferma__conta")?.textContent).toBe("3 da confermare")
    expect(tipi()).toEqual([
      ["Strumenti duplicati", "1 senza risposta"],
      ["Frame senza tipo", "1 senza risposta", "1 salvata"],
    ])
    // nessuna domanda a schermo finche' non si sceglie un tipo
    expect(document.querySelector(".as-domanda, .as-domanda-riga")).toBeNull()
    expect(screen.queryByRole("navigation", { name: "Sezioni" })).toBeNull()
  })

  it("scelto un tipo si vede un caso solo, aperto, col nome del tipo e il suo perche'", async () => {
    await aperta()
    tipo("Frame senza tipo")
    expect(dove()).toBe("caso 1 di 2")
    expect(screen.getByRole("heading", { level: 2, name: "Frame senza tipo" }).className).toBe("as-conferma-caso__nome")
    expect(document.querySelector(".as-conferma-caso .as-conferma__regola")?.textContent).toMatch(/tipo/i)
    const aperte = document.querySelectorAll("article.as-domanda")
    expect(aperte).toHaveLength(1)
    expect(aperte[0]?.className).toBe("as-domanda as-domanda--prima")
    expect(aperte[0]?.getAttribute("aria-label")).toBe("D:/Astro/dark")
    expect(document.querySelector(".as-domanda-riga")).toBeNull()
    expect(screen.queryByRole("list", { name: "Tipi di domanda" })).toBeNull()
  })

  it("si va di caso in caso, e ai due capi di tipo in tipo", async () => {
    await aperta()
    tipo("Frame senza tipo")
    expect(vai()).toEqual(["Tipo prima: Strumenti duplicati", "Caso dopo"])
    fireEvent.click(screen.getByRole("button", { name: "Caso dopo" }))
    expect(dove()).toBe("caso 2 di 2")
    expect(document.querySelector("article.as-domanda")?.getAttribute("aria-label")).toBe("D:/Astro/M51")
    // l'ultimo caso dell'ultimo tipo: avanti non c'e'
    expect(vai()).toEqual(["Caso prima"])
    fireEvent.click(screen.getByRole("button", { name: "Caso prima" }))
    fireEvent.click(screen.getByRole("button", { name: "Tipo prima: Strumenti duplicati" }))
    expect(screen.getByRole("heading", { level: 2, name: "Strumenti duplicati" })).toBeDefined()
    expect(dove()).toBe("caso 1 di 1")
    expect(vai()).toEqual(["Tipo dopo: Frame senza tipo"])
  })

  it("una risposta data in un caso si legge tornando ai tipi, e il piede la conta", async () => {
    await aperta()
    tipo("Strumenti duplicati")
    fireEvent.click(screen.getByRole("radio", { name: /unisci a ATR2600M/i }))
    expect(document.querySelector(".as-conferma-tutto__conta")?.textContent).toBe("1 modifica da applicare")
    fireEvent.click(screen.getByRole("button", { name: /Tutti i tipi/ }))
    expect(tipi()[0]).toEqual(["Strumenti duplicati", "1 da applicare"])
    // e tornando sul caso la risposta e' ancora li'
    tipo("Strumenti duplicati")
    expect(screen.getByRole("radio", { name: /unisci a ATR2600M/i })).toHaveProperty("checked", true)
  })

  it("sopra i 900 la pagina resta quella larga: sezioni e indice", async () => {
    await aperta(1200)
    expect(screen.getByRole("navigation", { name: "Sezioni" })).toBeDefined()
    expect(screen.queryByRole("list", { name: "Tipi di domanda" })).toBeNull()
    expect(screen.getByRole("region", { name: "Strumenti duplicati" })).toBeDefined()
  })
})
