// @vitest-environment jsdom
/**
 * Impostazioni, *Nuovo sito* (tavola v82, 91-105): la ricerca per nome coi suoi stati, le
 * coordinate scritte a mano, l'anteprima di fuso e altitudine, il nome gia' preso (anche dal 409),
 * e cosa va nel corpo di `POST /sites`.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import type { components } from "../src/api/schema"
import {
  SALUTE,
  SITO_DI_CASA,
  SPINA,
  STANOTTE,
  chiamate,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  scritture,
  vai,
  type Voce,
} from "./banco"
import { impronta } from "./impronta"

afterEach(pulisci)

type Sito = components["schemas"]["SiteOut"]

const CASA: Sito = { ...SITO_DI_CASA, name: "Cima Ekar" }
const PUNTO = {
  "/api/v1/places/point": {
    stato: 200,
    corpo: { timezone: "Europe/Rome", utc_offset_minutes: 60, elevation_m: 1775.4 },
  },
}
const POSTI = [
  { name: "Monte Grappa", latitude: 45.87, longitude: 11.8 },
  { name: "Grappa, Bassano", latitude: 45.76, longitude: 11.73 },
]

async function apri(
  siti: Sito[],
  piu: Record<string, Voce> = {},
  indirizzo = "/impostazioni/siti?sito=nuovo",
) {
  rispondi({
    ...STANOTTE,
    ...piu,
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/sites": {
      stato: 200,
      corpo: {
        items: siti,
        total: siti.length,
        limit: 100,
        offset: 0,
        sqm_range: { min: 7, max: 23 },
      },
    },
    ...SPINA,
  })
  await disegna()
  vai(siti.length ? indirizzo : "/impostazioni/siti")
  return screen.findByRole("region", { name: "Nuovo sito" })
}

const salva = (carta: HTMLElement) => within(carta).getByText("Salva sito")
const spento = (el: HTMLElement) => el.getAttribute("aria-disabled") === "true"
const posta = () =>
  scritture().filter((s) => s.metodo === "POST" && s.url.endsWith("/api/v1/sites"))
const attendi = () => new Promise((r) => setTimeout(r, 30))

async function perCoordinate(carta: HTMLElement, lat = "45,87 N", lon = "11,80 E") {
  fireEvent.click(within(carta).getByRole("radio", { name: "Per coordinate" }))
  fireEvent.change(within(carta).getByRole("textbox", { name: "Latitudine" }), {
    target: { value: lat },
  })
  fireEvent.change(within(carta).getByRole("textbox", { name: "Longitudine" }), {
    target: { value: lon },
  })
}

describe("Impostazioni / Nuovo sito", () => {
  it("per nome: Cerca col campo vuoto non chiede; i luoghi trovati si scelgono, e il nome li segue", async () => {
    const carta = await apri([CASA], {
      ...PUNTO,
      "/api/v1/places?": { stato: 200, corpo: { items: POSTI } },
    })
    expect(
      within(carta).getByRole("radio", { name: "Per nome" }).getAttribute("aria-checked"),
    ).toBe("true")
    expect(
      within(carta).getByRole("radio", { name: "Per coordinate" }).getAttribute("aria-checked"),
    ).toBe("false")
    const campo = within(carta).getByRole("textbox", { name: "Nome del luogo" })
    expect(campo.getAttribute("placeholder")).toBe("per esempio Monte Grappa")
    fireEvent.change(campo, { target: { value: "   " } })
    fireEvent.click(within(carta).getByText("Cerca"))
    await attendi()
    expect(chiamate().filter((u) => u.includes("/api/v1/places?"))).toEqual([])
    expect(spento(salva(carta))).toBe(true)

    fireEvent.change(campo, { target: { value: " Grappa " } })
    fireEvent.keyDown(campo, { key: "Enter" })
    const trovati = await within(carta).findByRole("group", { name: "Risultati della ricerca" })
    expect(chiamate().filter((u) => u.includes("/api/v1/places?"))).toEqual([
      expect.stringContaining("q=Grappa"),
    ])
    expect(
      within(trovati)
        .getAllByRole("button")
        .map((b) => `${b.textContent}|${b.getAttribute("aria-pressed")}`),
    ).toEqual(["Monte Grappa›|false", "Grappa, Bassano›|false"])
    fireEvent.click(within(trovati).getByText("Grappa, Bassano"))
    await within(carta).findByText("dalle coordinate")
    expect(
      within(trovati)
        .getAllByRole("button")
        .map((b) => `${b.textContent}|${b.getAttribute("aria-pressed")}`),
    ).toEqual(["Monte Grappa›|false", "Grappa, Bassano✓ scelto|true"])
    expect(
      (within(carta).getByRole("textbox", { name: "Nome del sito" }) as HTMLInputElement).value,
    ).toBe("Grappa, Bassano")
    expect(within(carta).getByText("dalla ricerca per nome")).toBeTruthy()
    expect(within(carta).getByText("Europe/Rome · UTC+1")).toBeTruthy()
    expect(spento(salva(carta))).toBe(false)
    // un tasto che non e' Invio non cerca; scrivere toglie i risultati
    fireEvent.keyDown(campo, { key: "a" })
    fireEvent.change(campo, { target: { value: "Grappa!" } })
    expect(within(carta).queryByRole("group", { name: "Risultati della ricerca" })).toBeNull()
    expect(chiamate().filter((u) => u.includes("/api/v1/places?"))).toHaveLength(1)
  })

  it("per nome: nessun luogo, e un servizio rotto non e' «nessun luogo»", async () => {
    const carta = await apri([CASA], { "/api/v1/places?": { stato: 200, corpo: { items: [] } } })
    fireEvent.change(within(carta).getByRole("textbox", { name: "Nome del luogo" }), {
      target: { value: "Zzz" },
    })
    fireEvent.click(within(carta).getByText("Cerca"))
    expect(
      await within(carta).findByText(
        "Nessun luogo con questo nome: prova un altro nome o scrivi le coordinate.",
      ),
    ).toBeTruthy()
    expect(within(carta).queryByText("Ricerca non riuscita")).toBeNull()
    pulisci()

    const rotta = await apri([CASA], {
      "/api/v1/places?": { stato: 502, corpo: { detail: "giu'" } },
    })
    fireEvent.change(within(rotta).getByRole("textbox", { name: "Nome del luogo" }), {
      target: { value: "Zzz" },
    })
    fireEvent.click(within(rotta).getByText("Cerca"))
    expect(await within(rotta).findByText("Ricerca non riuscita")).toBeTruthy()
    expect(within(rotta).queryByText(/^Nessun luogo/)).toBeNull()
  })

  it("Cerca dice Cerco… mentre aspetta, e non chiede due volte", async () => {
    let lascia = () => {}
    const attesa = new Promise<void>((r) => (lascia = r))
    const carta = await apri([CASA], {
      "/api/v1/places?": { stato: 200, corpo: { items: POSTI }, attesa } as Voce,
    })
    fireEvent.change(within(carta).getByRole("textbox", { name: "Nome del luogo" }), {
      target: { value: "Grappa" },
    })
    fireEvent.click(within(carta).getByText("Cerca"))
    fireEvent.click(await within(carta).findByText("Cerco…"))
    lascia()
    await within(carta).findByRole("group", { name: "Risultati della ricerca" })
    expect(within(carta).getByText("Cerca")).toBeTruthy()
    expect(chiamate().filter((u) => u.includes("/api/v1/places?"))).toHaveLength(1)
  })

  it("per coordinate: solo un punto sulla Terra chiede l'anteprima", async () => {
    const carta = await apri([CASA], PUNTO)
    await perCoordinate(carta, "95 N", "11,80 E")
    expect(
      within(carta).getByText("Virgola o punto, e la lettera del verso: N, S, E, O."),
    ).toBeTruthy()
    expect(
      within(carta).getByRole("textbox", { name: "Latitudine" }).getAttribute("placeholder"),
    ).toBe("45,87 N")
    expect(
      within(carta).getByRole("textbox", { name: "Longitudine" }).getAttribute("placeholder"),
    ).toBe("11,80 E")
    const scrivi = (nome: string, v: string) =>
      fireEvent.change(within(carta).getByRole("textbox", { name: nome }), { target: { value: v } })
    scrivi("Longitudine", "181 E")
    scrivi("Latitudine", "45 N")
    scrivi("Longitudine", "boh")
    scrivi("Latitudine", "boh")
    scrivi("Longitudine", "11 E")
    await attendi()
    expect(chiamate().filter((u) => u.includes("/places/point"))).toEqual([])
    expect(within(carta).queryByRole("textbox", { name: "Nome del sito" })).toBeNull()
    // il bordo e' ancora sulla Terra
    scrivi("Longitudine", "180 O")
    scrivi("Latitudine", "90 S")
    await waitFor(() =>
      expect(chiamate().filter((u) => u.includes("/places/point"))).toEqual([
        expect.stringContaining("latitude=-90&longitude=-180"),
      ]),
    )
    scrivi("Latitudine", "boh")
    scrivi("Longitudine", "180")
    scrivi("Latitudine", "90")
    await waitFor(() =>
      expect(chiamate().filter((u) => u.includes("/places/point"))).toHaveLength(2),
    )
    expect(chiamate().filter((u) => u.includes("/places/point"))[1]).toContain(
      "latitude=90&longitude=180",
    )
  })

  it("l'altitudine del modello si cambia; solo un numero diverso va come scritta a mano", async () => {
    const carta = await apri([CASA], {
      ...PUNTO,
      "POST /api/v1/sites": { stato: 201, corpo: { ...CASA, id: 7 } },
    })
    await perCoordinate(carta)
    const alt = (await within(carta).findByRole("textbox", {
      name: "Altitudine, in metri",
    })) as HTMLInputElement
    expect(alt.value).toBe("1775")
    expect(within(carta).getByText("dal modello del terreno: si cambia")).toBeTruthy()
    expect(within(carta).getByText("scritte a mano")).toBeTruthy()
    fireEvent.change(alt, { target: { value: "1a8x2034" } })
    expect(alt.value).toBe("1820")
    expect(
      within(carta).getByText("scritta a mano · il modello del terreno dice 1775 m"),
    ).toBeTruthy()
    // senza nome non si salva
    expect(spento(salva(carta))).toBe(true)
    fireEvent.click(salva(carta))
    fireEvent.change(within(carta).getByRole("textbox", { name: "Nome del sito" }), {
      target: { value: "  Grappa  " },
    })
    fireEvent.click(salva(carta))
    await waitFor(() =>
      expect(posta().map((s) => s.corpo)).toEqual([
        {
          name: "Grappa",
          latitude: 45.87,
          longitude: 11.8,
          coords_source: "declared",
          is_default: false,
          elevation_m: 1820,
        },
      ]),
    )
    await waitFor(() => expect(window.location.search).toBe("?sito=7"))
  })

  it("l'altitudine svuotata non va; tornare per nome riporta quella del modello", async () => {
    const carta = await apri([CASA], {
      ...PUNTO,
      "/api/v1/places?": { stato: 200, corpo: { items: POSTI } },
      "POST /api/v1/sites": { stato: 500, corpo: { detail: "no" } },
    })
    await perCoordinate(carta)
    const alt = (await within(carta).findByRole("textbox", {
      name: "Altitudine, in metri",
    })) as HTMLInputElement
    fireEvent.change(alt, { target: { value: "" } })
    expect(within(carta).getByText(/^scritta a mano · il modello/)).toBeTruthy()
    fireEvent.change(within(carta).getByRole("textbox", { name: "Nome del sito" }), {
      target: { value: "Grappa" },
    })
    fireEvent.click(salva(carta))
    await waitFor(() =>
      expect(posta().map((s) => s.corpo)).toEqual([
        {
          name: "Grappa",
          latitude: 45.87,
          longitude: 11.8,
          coords_source: "declared",
          is_default: false,
        },
      ]),
    )

    fireEvent.change(alt, { target: { value: "12" } })
    fireEvent.click(within(carta).getByRole("radio", { name: "Per nome" }))
    fireEvent.change(within(carta).getByRole("textbox", { name: "Nome del luogo" }), {
      target: { value: "Grappa" },
    })
    fireEvent.click(within(carta).getByText("Cerca"))
    fireEvent.click(await within(carta).findByText("Monte Grappa"))
    expect(
      (
        (await within(carta).findByRole("textbox", {
          name: "Altitudine, in metri",
        })) as HTMLInputElement
      ).value,
    ).toBe("1775")
  })

  it("il modello del terreno muto: altitudine vuota e il perche'", async () => {
    const carta = await apri([CASA], {
      "/api/v1/places/point": {
        stato: 200,
        corpo: { timezone: null, utc_offset_minutes: null, elevation_m: null },
      },
    })
    await perCoordinate(carta)
    expect(await within(carta).findByText("il modello del terreno non ha risposto")).toBeTruthy()
    expect(
      (within(carta).getByRole("textbox", { name: "Altitudine, in metri" }) as HTMLInputElement)
        .value,
    ).toBe("")
    expect(within(carta).getByText("non riconosciuto")).toBeTruthy()
    expect(within(carta).queryByText("dalle coordinate")).toBeNull()
  })

  it("l'anteprima non letta si dice, e Riprova la richiede", async () => {
    const carta = await apri([CASA], {
      "/api/v1/places/point": { stato: 500, corpo: { detail: "no" } },
    })
    await perCoordinate(carta)
    expect(
      await within(carta).findByText(
        "Fuso e altitudine non letti: AstroLog non risponde, riprova.",
      ),
    ).toBeTruthy()
    expect(spento(salva(carta))).toBe(true)
    const prima = chiamate().filter((u) => u.includes("/places/point")).length
    fireEvent.click(within(carta).getByText("Riprova"))
    await waitFor(() =>
      expect(chiamate().filter((u) => u.includes("/places/point")).length).toBeGreaterThan(prima),
    )
  })

  it("un nome gia' preso, nell'elenco o dal 409, si dice e spegne Salva finche' non cambia", async () => {
    const carta = await apri([CASA], {
      ...PUNTO,
      "POST /api/v1/sites": { stato: 409, corpo: { detail: "preso" } },
    })
    await perCoordinate(carta)
    const nome = await within(carta).findByRole("textbox", { name: "Nome del sito" })
    fireEvent.change(nome, { target: { value: "Cima Ekar " } })
    expect(within(carta).getByText("✕ C'è già un sito con questo nome.")).toBeTruthy()
    expect(nome.getAttribute("aria-invalid")).toBe("true")
    expect(spento(salva(carta))).toBe(true)
    fireEvent.click(salva(carta))
    await attendi()
    expect(posta()).toEqual([])

    fireEvent.change(nome, { target: { value: "Altro" } })
    expect(nome.getAttribute("aria-invalid")).toBe("false")
    fireEvent.click(salva(carta))
    expect(await within(carta).findByText("✕ C'è già un sito con questo nome.")).toBeTruthy()
    expect(spento(salva(carta))).toBe(true)
    expect(window.location.search).toBe("?sito=nuovo")
    fireEvent.change(nome, { target: { value: "Altro 2" } })
    expect(within(carta).queryByText(/C'è già un sito/)).toBeNull()
  })

  it("un salvataggio fallito resta nella carta; Annulla c'e' solo con altri siti", async () => {
    const carta = await apri([CASA], {
      ...PUNTO,
      "POST /api/v1/sites": { stato: 500, corpo: { detail: "no" } },
    })
    await perCoordinate(carta)
    fireEvent.change(await within(carta).findByRole("textbox", { name: "Nome del sito" }), {
      target: { value: "Grappa" },
    })
    fireEvent.click(salva(carta))
    await waitFor(() => expect(posta()).toHaveLength(1))
    await attendi()
    expect(window.location.search).toBe("?sito=nuovo")
    expect(within(carta).queryByText(/C'è già un sito/)).toBeNull()
    fireEvent.click(within(carta).getByText("Annulla"))
    await waitFor(() => expect(screen.queryByRole("region", { name: "Nuovo sito" })).toBeNull())
  })

  it("il primo sito nasce di casa: salvarlo fa rileggere Stanotte", async () => {
    const carta = await apri([], { ...PUNTO, "POST /api/v1/sites": { stato: 201, corpo: CASA } })
    await perCoordinate(carta)
    fireEvent.change(await within(carta).findByRole("textbox", { name: "Nome del sito" }), {
      target: { value: "Grappa" },
    })
    const stanotte = () => chiamate().filter((u) => u.includes("/api/v1/tonight")).length
    const prima = stanotte()
    fireEvent.click(salva(carta))
    await waitFor(() => expect(stanotte()).toBeGreaterThan(prima))
  })

  it("resta come nella consegna, su desktop e telefono", async () => {
    // impronta del markup della carta: vuota, coi risultati, e con l'anteprima
    const visti: string[] = []
    for (const indirizzo of [
      "/impostazioni/siti?sito=nuovo",
      "/impostazioni/siti?sito=nuovo&formato=telefono",
    ]) {
      const carta = await apri(
        [CASA],
        { ...PUNTO, "/api/v1/places?": { stato: 200, corpo: { items: POSTI } } },
        indirizzo,
      )
      visti.push(impronta(carta.outerHTML))
      fireEvent.change(within(carta).getByRole("textbox", { name: "Nome del luogo" }), {
        target: { value: "Grappa" },
      })
      fireEvent.click(within(carta).getByText("Cerca"))
      fireEvent.click(await within(carta).findByText("Monte Grappa"))
      await within(carta).findByText("dalle coordinate")
      visti.push(impronta(carta.outerHTML))
      pulisci()
    }
    expect(visti).toEqual(["57761044", "da2a9f54", "cdc7de87", "5ae93441"])
  })
})
