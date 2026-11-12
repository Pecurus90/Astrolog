// @vitest-environment jsdom
import { fireEvent, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  STANOTTE,
  cartellaSenzaTipo,
  daConfermare,
  disegna,
  doppione,
  impostazioni,
  postoIgnoto,
  prove,
  pulisci,
  rispondi,
  statoDellaDomanda,
  vai,
} from "./banco"

afterEach(pulisci)

/**
 * La domanda di *Da confermare* sulla tavola v82: una sola aperta in tutta la pagina, le altre
 * chiuse in una riga che dice la risposta in breve e il suo stato. Cosa chiede ogni sezione lo
 * provano i file delle sezioni.
 */

const PAGINA = daConfermare({
  to_confirm: 2,
  lookalikes: [doppione({ id: 4, name: "ATR2600M(USB2.0)", frames: 38, into_id: 1, into_name: "ATR2600M", into_frames: 412 })],
  typeless: [
    cartellaSenzaTipo({ key: "D:/Astro/dark", frames: 120 }),
    cartellaSenzaTipo({ key: "D:/Astro/M51", frames: 30, answer: "light" }),
  ],
})

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
  vai("/da-confermare")
  await screen.findByRole("region", { name: "Le modifiche da applicare" })
}

const aperte = () => [...document.querySelectorAll<HTMLElement>("article.al-conf__colonna-16")]
const chiuse = () => [...document.querySelectorAll<HTMLElement>(".al-conf__centro-2")]
/** La riga chiusa che comincia con quel nome. */
const chiusa = (nome: string) => {
  const trovata = chiuse().find((r) => r.textContent?.startsWith(nome))
  if (!trovata) throw new Error(`nessuna riga chiusa "${nome}"`)
  return trovata
}
const pillola = (dove: Element) => dove.querySelector(".al-conf__riga-7") as HTMLElement

describe("Da confermare -- una domanda aperta alla volta", () => {
  it("si apre la prima senza risposta, e le altre sono righe chiuse col loro gesto", async () => {
    await apri()
    expect(aperte()).toHaveLength(1)
    expect(aperte()[0]?.getAttribute("aria-label")).toBe("ATR2600M(USB2.0), senza risposta")
    expect(aperte()[0]?.querySelector("h3")?.textContent).toBe("ATR2600M(USB2.0)")

    expect(chiuse().map((r) => r.querySelector(".al-conf__testo-11")?.textContent)).toEqual([
      "D:/Astro/dark",
      "D:/Astro/M51",
    ])
    expect(chiusa("D:/Astro/dark").querySelector(".al-conf__testo-10")?.textContent).toBe("120 frame")
    // senza risposta si risponde, con una risposta si cambia: e il bottone dice di quale riga
    expect(within(chiusa("D:/Astro/dark")).getByRole("button", { name: "Rispondi: D:/Astro/dark" }).textContent).toBe("Rispondi")
    expect(within(chiusa("D:/Astro/M51")).getByRole("button", { name: "Cambia: D:/Astro/M51" }).textContent).toBe("Cambia")
    // i controlli stanno solo nella domanda aperta
    expect(screen.getAllByRole("radio")).toHaveLength(2)
  })

  it("aprendone un'altra, quella di prima si chiude", async () => {
    await apri()
    fireEvent.click(screen.getByRole("button", { name: "Rispondi: D:/Astro/dark" }))
    expect(aperte().map((a) => a.getAttribute("aria-label"))).toEqual(["D:/Astro/dark, senza risposta"])
    expect(chiusa("ATR2600M(USB2.0)")).toBeDefined()
    expect(screen.getByRole("radio", { name: "Light" })).toBeDefined()
  })

  it("lo stato di una risposta ha quattro forme, ognuna col suo segno e la sua parola", async () => {
    await apri()
    // senza risposta, e salvata
    expect(pillola(chiusa("D:/Astro/dark")).textContent).toBe("\u25CBsenza risposta")
    expect(pillola(chiusa("D:/Astro/M51")).textContent).toBe("\u2713salvata")

    // data ora: da applicare
    fireEvent.click(screen.getByRole("button", { name: "Rispondi: D:/Astro/dark" }))
    fireEvent.click(screen.getByRole("radio", { name: "Calibrazione" }))
    expect(pillola(aperte()[0]!).textContent).toBe("\u25CFda applicare")
    expect(aperte()[0]?.getAttribute("aria-label")).toBe("D:/Astro/dark, da applicare")

    // una salvata che cambio: dice anche cos'era
    fireEvent.click(screen.getByRole("button", { name: "Cambia: D:/Astro/M51" }))
    fireEvent.click(screen.getByRole("radio", { name: "Calibrazione" }))
    expect(pillola(aperte()[0]!).textContent).toBe("\u25D0cambiata, da applicare")
    expect(statoDellaDomanda(aperte()[0]!)).toBe("cambiata, da applicare")
    expect(aperte()[0]?.querySelector(".al-conf__riga-12 > .al-conf__testo-10")?.textContent).toBe("era Light")
  })

  it("la riga chiusa dice la risposta in breve, o fra cosa si sceglie", async () => {
    await apri()
    const breve = (nome: string) => chiusa(nome).querySelector(".al-conf__blocco-9") as HTMLElement
    expect(breve("D:/Astro/dark").textContent).toBe("Light \u00b7 Calibrazione")
    expect(breve("D:/Astro/dark").style.fontWeight).toBe("400")
    // la risposta e' in evidenza, non una parola fra le altre
    expect(breve("D:/Astro/M51").textContent).toBe("Light")
    expect(breve("D:/Astro/M51").style.fontWeight).toBe("600")
    // la coppia di strumenti, chiusa senza risposta: le due scelte e nient'altro
    fireEvent.click(screen.getByRole("button", { name: "Rispondi: D:/Astro/dark" }))
    expect(breve("ATR2600M(USB2.0)").textContent).toBe("S\u00ec, unisci a ATR2600M \u00b7 No, sono distinti")
  })

  it("le scelte sono la pillola a risposta, e il gruppo porta la domanda per chi ascolta", async () => {
    await apri()
    const gruppo = screen.getByRole("radiogroup", { name: /sono lo stesso strumento/i })
    expect(gruppo.className).toBe("al-scelta al-scelta--risposta")
    expect(gruppo.querySelectorAll(":scope > a.al-scelta__voce[role=radio]")).toHaveLength(2)
    expect(gruppo.querySelector(".al-scelta__testi > span")?.textContent).toMatch(/unisci a ATR2600M/)
  })

  it("il perche' si legge solo nella sezione su cui si sta lavorando", async () => {
    await apri()
    const perche = (nome: string) => screen.getByRole("region", { name: nome }).querySelector("p.al-conf__blocco-8")
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
    const riga = document.querySelector(".al-conf__riga-9") as HTMLElement
    expect(riga.querySelector(".al-conf__blocco-7")?.textContent).toBe("Strumenti duplicati")
    // la pillola dice lo stato col segno e la parola, non col colore da solo
    expect(riga.querySelector(".al-conf__riga-7")?.textContent).toBe("\u25CF1 risposta da applicare")
    // resta prima di Frame senza tipo: non sale e non scende
    expect(riga.nextElementSibling?.getAttribute("aria-labelledby")).toBe("frame-senza-tipo-nome")
    // la voce dell'indice porta ancora qui: l'ancora della sezione sta sulla riga chiusa
    expect(document.getElementById("strumenti-duplicati")).toBe(riga)

    fireEvent.click(within(riga).getByRole("button", { name: "Riapri: Strumenti duplicati" }))
    expect(screen.getByRole("region", { name: "Strumenti duplicati" })).toBeDefined()
    expect(document.querySelector(".al-conf__riga-9")).toBeNull()
  })

  it("una sezione chiusa con sole risposte salvate lo dice", async () => {
    await apri({ ...PAGINA, typeless: [cartellaSenzaTipo({ key: "D:/Astro/M51", frames: 30, answer: "light" })] })
    const riga = document.querySelector(".al-conf__riga-9") as HTMLElement
    expect(riga.querySelector(".al-conf__blocco-7")?.textContent).toBe("Frame senza tipo")
    expect(riga.querySelector(".al-conf__riga-7")?.textContent).toBe("\u27131 risposta salvata")
  })

  it("i dati che aiutano a rispondere stanno in una tabellina: la parola, e il dato", async () => {
    // In riga, uno dopo l'altro, si leggevano male: "46.10,12.00 52 frame Oggetti: ... notti: ...".
    await apri({
      ...PAGINA,
      lookalikes: [],
      typeless: [],
      unclear: [
        postoIgnoto({
          key: "46.10,12.00",
          latitude: 46.1,
          longitude: 12.0,
          distance_km: 38.2,
          frames: 52,
          nights: ["2025-07-31", "2025-08-12", "2025-08-13"],
          candidates: [{ id: 2, name: "Malga", distance_km: 2.1 }],
          subjects: { found: [{ name: "M 31", frames: 12 }], not_found: 8, not_yet: 5 },
        }),
      ],
    })
    const domanda = aperte()[0] as HTMLElement
    // le coordinate come si scrivono, non la chiave
    expect(domanda.querySelector("h3")?.textContent).toBe("46,1000 N - 12,0000 E")
    // le notti a mesi: il mese una volta, poi i giorni, una riga per mese
    expect(prove(domanda)).toEqual([
      "Oggetti nel campo=M 31 (12 frame)",
      "Altri frame=8 frame senza oggetti identificati · 5 frame non risolti",
      "Distanza=38,2 km dal sito predefinito",
      "Notti=lug 2025: 31 | ago 2025: 12, 13",
    ])
  })
})
