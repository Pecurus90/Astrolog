// @vitest-environment jsdom
/**
 * Impostazioni, la sezione *Siti* (tavola v82): le pillole dei siti, *Il sito*, *Il cielo del
 * sito* e *Nuovo sito*. Si prova cio' che una lettura del codice non prende: da dove viene ogni
 * numero, che Elimina si spegne col suo perche', che una via scrive solo col gesto che dice un
 * cielo, e che il nuovo sito non manda come «scritta a mano» l'altitudine del modello.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import type { components } from "../src/api/schema"
import { SALUTE, SITO_DI_CASA, SPINA, STANOTTE, chiamate, disegna, impostazioni, pulisci, rispondi, scritture, vai } from "./banco"

afterEach(pulisci)

type Sito = components["schemas"]["SiteOut"]

const CASA: Sito = { ...SITO_DI_CASA, name: "Cima Ekar", coords_source: "place", elevation_m: 1366, elevation_source: "service", nights: 112 }
const USCITA: Sito = { ...SITO_DI_CASA, id: 2, name: "Monte Grappa", is_default: false, nights: 0, sky_sqm: null, sky_source: null, bortle: null }

const MESI = Array.from({ length: 12 }, (_, i) => ({
  year: i < 2 ? 2025 : 2026,
  month: ((10 + i) % 12) + 1,
  measured: i % 3 !== 2,
}))

function app(siti: Sito[], piu: Record<string, { stato: number; corpo: unknown }> = {}, chiave: string | null = null) {
  const valori = impostazioni(true)
  rispondi({
    ...STANOTTE,
    ...piu,
    "/api/v1/settings": { stato: 200, corpo: { ...valori, values: { ...valori.values, sky_service_key: chiave } } },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/sites": { stato: 200, corpo: { items: siti, total: siti.length, limit: 100, offset: 0, sqm_range: { min: 7, max: 23 } } },
    ...SPINA,
  })
}

async function apri(siti: Sito[], indirizzo = "/impostazioni/siti", piu = {}, chiave: string | null = null) {
  app(siti, piu, chiave)
  await disegna()
  vai(indirizzo)
  return screen.findByRole("group", { name: "Siti" })
}

const carta = (nome: string) => screen.findByRole("region", { name: nome })

describe("Impostazioni / Siti", () => {
  it("le pillole dei siti, il predefinito acceso, e ogni numero con la sua provenienza", async () => {
    const pillole = await apri([CASA, USCITA])
    expect((await within(pillole).findByText("Cima Ekar")).getAttribute("aria-pressed")).toBe("true")
    expect(await screen.findByText("dalla ricerca per nome")).toBeTruthy()
    expect(screen.getByText("1366 m")).toBeTruthy()
    expect(screen.getByText("dal modello del terreno")).toBeTruthy()
    expect(screen.getByText("Europe/Rome · UTC+1")).toBeTruthy()
    expect(screen.getByText("112 notti")).toBeTruthy()
    expect(screen.getByText("sì")).toBeTruthy()
  })

  it("Elimina si spegne su un sito con notti, e dice perche'", async () => {
    await apri([CASA, USCITA])
    const elimina = await screen.findByText("Elimina il sito")
    expect(elimina.getAttribute("aria-disabled")).toBe("true")
    expect(screen.getByText("Ha 112 notti: non si elimina. Le notti restano col loro sito.")).toBeTruthy()
  })

  it("un sito senza notti si elimina dopo la conferma", async () => {
    await apri([CASA, USCITA], "/impostazioni/siti?sito=2", { "DELETE /api/v1/sites/2": { stato: 200, corpo: { site_id: 2, deleted: true } } })
    fireEvent.click(await screen.findByText("Elimina il sito"))
    fireEvent.click(await screen.findByText("Elimina", { selector: "a" }))
    await waitFor(() => expect(scritture().some((s) => s.metodo === "DELETE" && s.url.endsWith("/api/v1/sites/2"))).toBe(true))
  })

  it("Rinomina: un nome gia' preso si dice sotto il campo, e non si salva", async () => {
    await apri([CASA, USCITA])
    fireEvent.click(await screen.findByText("Rinomina"))
    fireEvent.change(screen.getByRole("textbox", { name: "Nome del sito" }), { target: { value: "Monte Grappa" } })
    expect(screen.getByText("✕ C'è già un sito con questo nome.")).toBeTruthy()
    fireEvent.click(screen.getByText("Salva"))
    expect(scritture().filter((s) => s.metodo === "PATCH")).toEqual([])
  })

  it("il cielo di ora con la sua fonte, e Bortle a mano scrive la classe scelta", async () => {
    await apri([CASA], "/impostazioni/siti", { "PATCH /api/v1/sites/1": { stato: 200, corpo: CASA } })
    expect(await screen.findByText("Bortle 5 – cielo di periferia")).toBeTruthy()
    expect(screen.getByText("SQM 20,8 scritto a mano")).toBeTruthy()
    // aprire una via non scrive
    fireEvent.click(screen.getByText("Bortle a mano"))
    expect(scritture()).toEqual([])
    fireEvent.click(within(screen.getByRole("group", { name: "Classe di Bortle" })).getByText("3"))
    await waitFor(() => expect(scritture()).toContainEqual(expect.objectContaining({ metodo: "PATCH", corpo: { bortle: 3 } })))
  })

  it("Dalla mappa senza chiave porta a Servizi, e non chiede niente", async () => {
    await apri([CASA])
    fireEvent.click(await screen.findByText("Dalla mappa"))
    expect(screen.getByText("Serve la chiave del servizio del cielo, in Servizi.")).toBeTruthy()
    expect(screen.getByText("Apri Servizi")).toBeTruthy()
    expect(scritture()).toEqual([])
  })

  it("le misure propongono una classe, e Usa la scrive", async () => {
    const misurato: Sito = {
      ...CASA,
      measured: { status: "enough", nights: 38, months: 10, sqm: 21.4, bortle: 4, first_night: "2025-11-02", last_night: "2026-10-28", propose: true, month_marks: MESI },
    }
    await apri([misurato], "/impostazioni/siti", { "POST /api/v1/sites/1/sky/use": { stato: 200, corpo: misurato } })
    expect(await screen.findByText(/Le misure di Cima Ekar dicono Bortle 4 – campagna più chiara \(SQM 21,4, 38 notti in 10 mesi\)\. Nel sito c'è Bortle 5\./)).toBeTruthy()
    const mesi = screen.getByRole("img", { name: "8 mesi misurati sugli ultimi 12" })
    expect(mesi.children).toHaveLength(12)
    expect(mesi.children[0]?.getAttribute("title")).toBe("novembre 2025: misurato")
    expect(mesi.children[2]?.getAttribute("title")).toBe("gennaio 2026: nessuna notte")
    fireEvent.click(screen.getByText("Usa Bortle 4"))
    expect(await screen.findByText("✓ Bortle 4 nel sito, dalle misure.")).toBeTruthy()
    // la via segue cio' che si e' scritto: «Dalle misure», non la via di prima
    expect(screen.getByText("Dalle misure").getAttribute("aria-pressed")).toBe("true")
    expect(screen.getByText("SQM a mano").getAttribute("aria-pressed")).toBe("false")
  })

  it("il sito predefinito che cambia fa rileggere Stanotte; rinominare un sito d'uscita no", async () => {
    await apri([CASA, USCITA], "/impostazioni/siti?sito=2", {
      "POST /api/v1/sites/2/default": { stato: 200, corpo: { ...USCITA, is_default: true } },
      "PATCH /api/v1/sites/2": { stato: 200, corpo: { ...USCITA, name: "Grappa" } },
    })
    await screen.findByText("Usa come predefinito")
    const stanotte = () => chiamate().filter((u) => u.includes("/api/v1/tonight")).length
    await waitFor(() => expect(stanotte()).toBeGreaterThan(0))
    const prima = stanotte()
    fireEvent.click(screen.getByText("Rinomina"))
    fireEvent.change(screen.getByRole("textbox", { name: "Nome del sito" }), { target: { value: "Grappa" } })
    fireEvent.click(screen.getByText("Salva"))
    await waitFor(() => expect(scritture().some((s) => s.metodo === "PATCH")).toBe(true))
    await new Promise((r) => setTimeout(r, 50))
    expect(stanotte()).toBe(prima)
    fireEvent.click(screen.getByText("Usa come predefinito"))
    await waitFor(() => expect(stanotte()).toBeGreaterThan(prima))
  })

  it("senza siti si apre Nuovo sito; per coordinate l'anteprima, e l'altitudine del modello non va come scritta a mano", async () => {
    await apri([], "/impostazioni/siti", {
      "/api/v1/places/point": { stato: 200, corpo: { timezone: "Europe/Rome", utc_offset_minutes: 60, elevation_m: 1775 } },
      "POST /api/v1/sites": { stato: 201, corpo: USCITA },
    })
    const nuovo = await carta("Nuovo sito")
    expect(within(nuovo).queryByText("Annulla")).toBeNull()
    fireEvent.click(within(nuovo).getByRole("radio", { name: "Per coordinate" }))
    fireEvent.change(within(nuovo).getByRole("textbox", { name: "Latitudine" }), { target: { value: "45,87 N" } })
    fireEvent.change(within(nuovo).getByRole("textbox", { name: "Longitudine" }), { target: { value: "11,80 E" } })
    expect(await within(nuovo).findByText("dal modello del terreno: si cambia")).toBeTruthy()
    expect(within(nuovo).getByRole("textbox", { name: "Altitudine, in metri" })).toHaveProperty("value", "1775")
    fireEvent.change(within(nuovo).getByRole("textbox", { name: "Nome del sito" }), { target: { value: "Monte Grappa" } })
    fireEvent.click(within(nuovo).getByText("Salva sito"))
    await waitFor(() =>
      expect(scritture()).toContainEqual(
        expect.objectContaining({ metodo: "POST", corpo: { name: "Monte Grappa", latitude: 45.87, longitude: 11.8, coords_source: "declared", is_default: false } }),
      ),
    )
  })
})
