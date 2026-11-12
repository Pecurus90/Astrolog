// @vitest-environment jsdom
/**
 * La domanda **quando**: i frame che non dicono quando sono stati ripresi, una per cartella
 * (Marco, 6/11/2026). Si risponde con la sera della ripresa, scritta o scelta fra le notti con lo
 * stesso setup.
 *
 * - **La data del file sul disco e' una prova, mai una risposta**: e' quella della copia.
 * - **Una data scritta parte solo se e' un giorno vero**: il 30 febbraio il backend lo rifiuta, e
 *   con lui tutto l'Applica.
 * - **Ridare la data salvata non manda niente**: rimetterebbe in coda frame che non cambiano.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  STANOTTE,
  cartellaSenzaData,
  cartellaSenzaTipo,
  daConfermare,
  disegna,
  domande,
  impostazioni,
  prove,
  pulisci,
  riga,
  rispondi,
  scelta,
  scelto,
  scritture,
  spento,
  vai,
  vaiASezione,
  voci,
} from "./banco"

afterEach(pulisci)

const CARTELLA = "D:/Astro/vecchie/M27"

const SENZA = cartellaSenzaData({
  key: CARTELLA,
  frames: 24,
  integration_s: 7200,
  site: "Vicenza",
  file_nights: ["2025-09-03"],
  rig_nights: ["2025-08-12", "2025-08-14"],
})

const PAGINA = daConfermare({ to_confirm: 1, undated: [SENZA] })

function aperta(pagina: unknown = PAGINA) {
  rispondi({
    ...STANOTTE,
    "/api/v1/vocab/filter-models": { stato: 200, corpo: { items: [] } },
    "/api/v1/review/apply": { stato: 200, corpo: { changed: 1, requeued: 24, run_started: true } },
    "/api/v1/review": { stato: 200, corpo: pagina },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/health": { stato: 200, corpo: SALUTE },
  })
}

async function mandate() {
  fireEvent.click(screen.getByRole("button", { name: /applica/i }))
  let corpo: { undated: unknown[] } | undefined
  await waitFor(() => {
    corpo = scritture().find((s) => s.url.includes("/api/v1/review/apply"))?.corpo as typeof corpo
    expect(corpo).toBeDefined()
  })
  return corpo?.undated
}

const applicaSpento = () =>
  expect(screen.getByRole("button", { name: /applica/i }).getAttribute("aria-disabled")).toBe(
    "true",
  )
const applicaAcceso = () =>
  expect(screen.getByRole("button", { name: /applica/i }).getAttribute("aria-disabled")).toBeNull()
const cartella = async () => riga(await vaiASezione(/frame senza data/i), CARTELLA)
const data = (dove: HTMLElement) => within(dove).getByLabelText("Data della sera")

describe("Da confermare -- i frame senza data", () => {
  it("una cartella senza risposta: i file non dicono la data, quella sul disco e' della copia", async () => {
    aperta()
    const dove = await cartella()
    expect(dove.querySelector("h3")?.textContent).toBe(CARTELLA)
    expect(prove(dove)).toEqual([
      "Data nei file=Non indicata",
      "Data del file sul disco=3 set 2025: \u00e8 quella della copia, non della ripresa",
    ])
    expect(voci(dove)).toEqual([
      "Scrivo la data / la sera della ripresa",
      "Scelgo una notte / fra le notti con lo stesso setup",
    ])
    applicaSpento()
  })

  it("chiusa e senza risposta, la riga dice fra cosa si sceglie", async () => {
    aperta(daConfermare({ to_confirm: 2, undated: [SENZA, { ...SENZA, key: "D:/Astro/altra" }] }))
    const sezione = await vaiASezione(/frame senza data/i)
    expect(domande(sezione)[1]?.querySelector(".al-conf__blocco-9")?.textContent).toBe(
      "Scrivo la data \u00b7 Scelgo una notte",
    )
  })

  it("la data scritta parte come la notte di quella sera", async () => {
    aperta()
    const dove = await cartella()
    expect(within(dove).queryByLabelText("Data della sera")).toBeNull()
    fireEvent.click(scelta(dove, "Scrivo la data"))
    // la notte comincia la sera, sul sito della cartella
    expect(
      within(dove).getByText("La notte comincia la sera di quel giorno, sul sito di Vicenza."),
    ).toBeDefined()
    expect(data(dove).getAttribute("placeholder")).toBe("gg/mm/aaaa")
    applicaSpento()
    fireEvent.change(data(dove), { target: { value: "12/08/2025" } })
    expect(await mandate()).toEqual([{ key: CARTELLA, night: "2025-08-12" }])
  })

  it("un giorno che il calendario non ha non parte", async () => {
    aperta()
    const dove = await cartella()
    fireEvent.click(scelta(dove, "Scrivo la data"))
    fireEvent.change(data(dove), { target: { value: "30/02/2025" } })
    applicaSpento()
    fireEvent.change(data(dove), { target: { value: "2025-08-12" } })
    applicaSpento()
    // l'ultimo giorno del calendario: il backend lo rifiuta, e con lui tutto l'Applica
    fireEvent.change(data(dove), { target: { value: "31/12/9999" } })
    applicaSpento()
    fireEvent.change(data(dove), { target: { value: "1/3/2025" } })
    applicaAcceso()
  })

  it("si sceglie fra le notti con lo stesso setup, ognuna col suo sito", async () => {
    aperta()
    const dove = await cartella()
    fireEvent.click(scelta(dove, "Scelgo una notte"))
    // scelta la strada e nessuna notte, non e' ancora una risposta
    applicaSpento()
    const notti = within(dove).getByRole("radiogroup", { name: "Notte" })
    expect(voci(notti)).toEqual(["12 ago 2025, Vicenza", "14 ago 2025, Vicenza"])
    fireEvent.click(scelta(notti, "14 ago 2025"))
    expect(scelto(scelta(notti, "14 ago 2025"))).toBe(true)
    expect(await mandate()).toEqual([{ key: CARTELLA, night: "2025-08-14" }])
  })

  it("senza notti con lo stesso setup la strada della scelta e' spenta", async () => {
    aperta(daConfermare({ to_confirm: 1, undated: [{ ...SENZA, rig_nights: [], site: null }] }))
    const dove = await cartella()
    expect(spento(scelta(dove, "Scelgo una notte"))).toBe(true)
    fireEvent.click(scelta(dove, "Scrivo la data"))
    // senza sito la notte comincia la sera, e basta
    expect(within(dove).getByText("La notte comincia la sera di quel giorno.")).toBeDefined()
  })

  it("cambiando strada parte la risposta della strada scelta", async () => {
    aperta()
    const dove = await cartella()
    fireEvent.click(scelta(dove, "Scrivo la data"))
    fireEvent.change(data(dove), { target: { value: "01/08/2025" } })
    fireEvent.click(scelta(dove, "Scelgo una notte"))
    applicaSpento()
    fireEvent.click(scelta(dove, "12 ago 2025"))
    fireEvent.click(scelta(dove, "Scrivo la data"))
    // la data scritta prima e' ancora li', e torna
    expect(data(dove)).toHaveProperty("value", "01/08/2025")
    expect(await mandate()).toEqual([{ key: CARTELLA, night: "2025-08-01" }])
  })

  it("una risposta salvata si legge, e ridarla uguale non manda niente", async () => {
    aperta(daConfermare({ to_confirm: 0, undated: [{ ...SENZA, answer: "2025-08-12" }] }))
    const dove = await cartella()
    expect(scelto(scelta(dove, "Scelgo una notte"))).toBe(true)
    expect(scelto(scelta(dove, "12 ago 2025"))).toBe(true)
    // la stessa notte, scritta invece che scelta: non e' un cambio
    fireEvent.click(scelta(dove, "Scrivo la data"))
    fireEvent.change(data(dove), { target: { value: "12/08/2025" } })
    applicaSpento()
    fireEvent.change(data(dove), { target: { value: "13/08/2025" } })
    applicaAcceso()
    expect(dove.querySelector(".al-conf__riga-12 > .al-conf__testo-10")?.textContent).toBe(
      "era Notte del 12 ago 2025",
    )
    fireEvent.click(scelta(dove, "Scelgo una notte"))
    applicaSpento()
  })

  it("una data salvata che non e' fra le notti del setup si riapre scritta", async () => {
    aperta(daConfermare({ to_confirm: 0, undated: [{ ...SENZA, answer: "2025-07-30" }] }))
    const sezione = await vaiASezione(/frame senza data/i)
    expect(domande(sezione)[0]?.querySelector(".al-conf__blocco-9")?.textContent).toBe(
      "Notte del 30 lug 2025",
    )
    const dove = riga(sezione, CARTELLA)
    expect(scelto(scelta(dove, "Scrivo la data"))).toBe(true)
    expect(data(dove)).toHaveProperty("value", "30/07/2025")
  })

  it("dall'indirizzo si entra nella sezione: ?sezione=senza-data", async () => {
    // senza indirizzo si aprirebbe la prima che aspetta, che sta in un'altra sezione
    aperta(
      daConfermare({
        to_confirm: 2,
        typeless: [cartellaSenzaTipo({ key: "D:/Astro/dark", frames: 3 })],
        undated: [SENZA],
      }),
    )
    await disegna()
    vai("/da-confermare?sezione=senza-data")
    const sezione = await screen.findByRole("region", { name: /frame senza data/i })
    expect(sezione.querySelector("article.al-conf__colonna-16 h3")?.textContent).toBe(CARTELLA)
    expect(document.querySelectorAll("article.al-conf__colonna-16")).toHaveLength(1)
  })
})
