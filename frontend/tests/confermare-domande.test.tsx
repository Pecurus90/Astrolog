// @vitest-environment jsdom
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SALUTE, STANOTTE, disegna, impostazioni, pulisci, rispondi } from "./banco"

afterEach(pulisci)

/**
 * La domanda di *Da confermare* nel foglio v34: una sola aperta in tutta la pagina, le altre
 * chiuse in una riga che dice la risposta in breve e il suo stato. Cosa chiede ogni sezione lo
 * provano i file delle sezioni.
 */

const PAGINA = {
  to_confirm: 2,
  lookalikes: [
    { id: 4, name: "ATR2600M(USB2.0)", frames: 38, into_id: 1, into_name: "ATR2600M", into_frames: 412 },
  ],
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

async function apri(pagina: unknown = PAGINA) {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review/apply": { stato: 200, corpo: { changed: 1, requeued: 0, run_started: false } },
    "/api/v1/review": { stato: 200, corpo: pagina },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
  await disegna()
  fireEvent.click(await screen.findByRole("link", { name: /da confermare/i }))
  await screen.findByRole("region", { name: "Modifiche da applicare" })
}

const aperte = () => [...document.querySelectorAll("article.as-domanda")]
const chiuse = () => [...document.querySelectorAll(".as-domanda-riga")]
/** La riga chiusa che comincia con quel nome. */
const chiusa = (nome: string) => {
  const trovata = chiuse().find((r) => r.textContent?.startsWith(nome))
  if (!trovata) throw new Error(`nessuna riga chiusa "${nome}"`)
  return trovata as HTMLElement
}
const stato = (dove: Element) => dove.querySelector(".as-risposta") as HTMLElement

describe("Da confermare -- una domanda aperta alla volta", () => {
  it("si apre la prima senza risposta, e le altre sono righe chiuse col loro gesto", async () => {
    await apri()
    expect(aperte()).toHaveLength(1)
    expect(aperte()[0]?.getAttribute("aria-label")).toBe("ATR2600M(USB2.0)")
    expect(aperte()[0]?.querySelector("h3.as-domanda__nome")?.textContent).toBe("ATR2600M(USB2.0)")

    expect(chiuse().map((r) => r.querySelector(".as-domanda-riga__nome")?.textContent)).toEqual([
      "D:/Astro/dark",
      "D:/Astro/M51",
    ])
    // senza risposta si risponde, con una risposta si cambia: e il bottone dice di quale riga
    expect(within(chiusa("D:/Astro/dark")).getByRole("button", { name: "Rispondi: D:/Astro/dark" }).textContent).toBe("Rispondi")
    expect(within(chiusa("D:/Astro/M51")).getByRole("button", { name: "Cambia: D:/Astro/M51" }).textContent).toBe("Cambia")
    // i controlli stanno solo nella domanda aperta
    expect(screen.getAllByRole("radio")).toHaveLength(2)
  })

  it("aprendone un'altra, quella di prima si chiude", async () => {
    await apri()
    fireEvent.click(screen.getByRole("button", { name: "Rispondi: D:/Astro/dark" }))
    expect(aperte().map((a) => a.getAttribute("aria-label"))).toEqual(["D:/Astro/dark"])
    expect(chiusa("ATR2600M(USB2.0)")).toBeDefined()
    expect(screen.getByRole("radio", { name: "Light" })).toBeDefined()
  })

  it("lo stato di una risposta ha quattro forme, ognuna con la sua parola", async () => {
    await apri()
    // senza risposta, e salvata
    expect(stato(chiusa("D:/Astro/dark")).className).toBe("as-risposta as-risposta--dare")
    expect(stato(chiusa("D:/Astro/dark")).textContent).toBe("senza risposta")
    expect(stato(chiusa("D:/Astro/M51")).className).toBe("as-risposta as-risposta--salvata")
    expect(stato(chiusa("D:/Astro/M51")).textContent).toBe("salvata")

    // data ora: da applicare
    fireEvent.click(screen.getByRole("button", { name: "Rispondi: D:/Astro/dark" }))
    fireEvent.click(screen.getByRole("radio", { name: "Calibrazione" }))
    expect(stato(aperte()[0]!).className).toBe("as-risposta as-risposta--ora")
    expect(stato(aperte()[0]!).textContent).toBe("da applicare")

    // una salvata che cambio: dice anche cos'era
    fireEvent.click(screen.getByRole("button", { name: "Cambia: D:/Astro/M51" }))
    fireEvent.click(screen.getByRole("radio", { name: "Calibrazione" }))
    expect(stato(aperte()[0]!).className).toBe("as-risposta as-risposta--cambiata")
    expect(stato(aperte()[0]!).textContent).toBe("cambiata, da applicare \u00b7 era Light")
  })

  it("la riga chiusa dice la risposta in breve, o fra cosa si sceglie", async () => {
    await apri()
    const breve = (nome: string) => chiusa(nome).querySelector(".as-domanda-riga__breve") as HTMLElement
    expect(breve("D:/Astro/dark").textContent).toBe("Light \u00b7 Calibrazione")
    expect(breve("D:/Astro/dark").querySelector("b")).toBeNull()
    // la risposta e' in evidenza, non una parola fra le altre
    expect(breve("D:/Astro/M51").querySelector("b")?.textContent).toBe("Light")
    // la coppia di strumenti, chiusa senza risposta: le due scelte e nient'altro
    fireEvent.click(screen.getByRole("button", { name: "Rispondi: D:/Astro/dark" }))
    expect(breve("ATR2600M(USB2.0)").textContent).toBe("S\u00ec, unisci a ATR2600M \u00b7 No, sono distinti")
  })

  it("le scelte fisse sono il mattone del foglio, e la domanda resta per chi ascolta", async () => {
    await apri()
    const gruppo = screen.getByRole("group", { name: /sono lo stesso strumento/i })
    expect(gruppo.className).toBe("as-scelta-fissa")
    expect(gruppo.querySelector("legend")?.className).toBe("as-scelta-fissa__domanda as-solo-lettori")
    expect(gruppo.querySelectorAll(".as-scelta-fissa__voci > label.as-scelta-fissa__voce > input[type=radio]")).toHaveLength(2)
    expect(gruppo.querySelector(".as-scelta-fissa__nome")?.textContent).toMatch(/unisci a ATR2600M/)
  })

  it("il perche' si legge solo nella sezione su cui si sta lavorando", async () => {
    await apri()
    const perche = (nome: string) =>
      screen.getByRole("region", { name: nome }).querySelector(".as-conferma-sezione__perche")
    expect(perche("Strumenti duplicati")).not.toBeNull()
    expect(perche("Frame senza tipo")).toBeNull()
    fireEvent.click(screen.getByRole("button", { name: "Rispondi: D:/Astro/dark" }))
    expect(perche("Strumenti duplicati")).toBeNull()
    expect(perche("Frame senza tipo")).not.toBeNull()
  })

  it("una sezione con tutte le risposte si chiude in una riga, al suo posto, e si riapre", async () => {
    await apri()
    fireEvent.click(screen.getByRole("radio", { name: /sono distinti/i }))
    // finche' ci si lavora resta aperta: non si chiude sotto le mani
    expect(screen.getByRole("region", { name: "Strumenti duplicati" })).toBeDefined()

    fireEvent.click(screen.getByRole("button", { name: "Rispondi: D:/Astro/dark" }))
    expect(screen.queryByRole("region", { name: "Strumenti duplicati" })).toBeNull()
    const riga = document.querySelector(".as-conferma-chiusa") as HTMLElement
    expect(riga.querySelector(".as-conferma-chiusa__nome")?.textContent).toBe("Strumenti duplicati")
    expect(stato(riga).className).toBe("as-risposta as-risposta--ora")
    expect(stato(riga).textContent).toBe("1 risposta da applicare")
    // resta prima di Frame senza tipo: non sale e non scende
    expect(riga.nextElementSibling?.getAttribute("aria-labelledby")).toBe("frame-senza-tipo-nome")
    // la voce dell'indice porta ancora qui: l'ancora della sezione sta sulla riga chiusa
    expect(document.getElementById("strumenti-duplicati")).toBe(riga)

    fireEvent.click(within(riga).getByRole("button", { name: "Riapri: Strumenti duplicati" }))
    expect(screen.getByRole("region", { name: "Strumenti duplicati" })).toBeDefined()
    expect(document.querySelector(".as-conferma-chiusa")).toBeNull()
  })

  it("una sezione chiusa con sole risposte salvate lo dice", async () => {
    await apri({ ...PAGINA, typeless: [{ key: "D:/Astro/M51", frames: 30, answer: "light" }] })
    const riga = document.querySelector(".as-conferma-chiusa") as HTMLElement
    expect(riga.querySelector(".as-conferma-chiusa__nome")?.textContent).toBe("Frame senza tipo")
    expect(stato(riga).className).toBe("as-risposta as-risposta--salvata")
    expect(stato(riga).textContent).toBe("1 risposta salvata")
  })
})
