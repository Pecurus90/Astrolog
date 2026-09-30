// @vitest-environment jsdom
/**
 * Il piede della barra: da dove osservi, e che luna fa.
 *
 * Qui si provano le regole che una lettura del codice non prende: che ogni vuoto diventi una
 * frase, che l'ora sia quella del sito e non del browser, e che non si prometta una pagina che
 * non esiste.
 */
// Il fuso della macchina si fissa **prima** che qualcuno legga una data. Senza, la prova
// sull'ora non protegge niente su un computer a +02:00 -- cioe' proprio quello dove il cancello
// gira -- perche' l'ora del sito e quella del browser sarebbero lo stesso numero, e il difetto
// passerebbe verde. Visto: sabotato, con il fuso di casa restava verde; con questa riga cade.
process.env.TZ = "UTC"

import { screen } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { rileggiOgni } from "../src/Stanotte"
import { FERMO, SALUTE, disegna, impostazioni, pulisci, rispondi } from "./banco"

afterEach(pulisci)

const LUNA = {
  phase_key: "waxing_gibbous",
  illumination_pct: 60,
  rise: "2026-09-19T15:49:26.241398+02:00",
  set: "2026-09-19T23:48:58.203956+02:00",
  highest: { at: "2026-09-19T19:48:00+02:00", altitude_deg: 16.1 },
  track: [
    { at: "2026-09-19T12:00:00+02:00", altitude_deg: -35.8 },
    { at: "2026-09-19T19:48:00+02:00", altitude_deg: 16.1 },
    { at: "2026-09-20T12:00:00+02:00", altitude_deg: -43.4 },
  ],
  ceiling_deg: 75,
  lit_side: "right",
}

/** Le fasce come le manda la rotta: **sempre**, anche vuote. Il banco le porta perche' l'API le
 *  porta -- una finta che le omette fa provare una tela che nessun utente vedra' mai. */
const FASCE = [
  { starts_at: "2026-09-19T12:00:00+02:00", ends_at: "2026-09-19T19:00:00+02:00", kind: "day" },
  { starts_at: "2026-09-19T19:00:00+02:00", ends_at: "2026-09-19T20:30:00+02:00", kind: "civil" },
  { starts_at: "2026-09-19T20:30:00+02:00", ends_at: "2026-09-20T05:00:00+02:00", kind: "dark" },
  { starts_at: "2026-09-20T05:00:00+02:00", ends_at: "2026-09-20T12:00:00+02:00", kind: "day" },
]

function app(stanotte: Record<string, unknown>) {
  rispondi({
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": {
      stato: 200,
      corpo: { to_confirm: 0, seen: { instruments: 0, rigs: 0, objects: 0 } },
    },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/pipeline/status": { stato: 200, corpo: FERMO },
    "/api/v1/tonight": { stato: 200, corpo: { sky_bands: FASCE, weather: null, ...stanotte } },
  })
  return disegna()
}

describe("il piede della barra", () => {
  it("dice da dove osservi, che cielo hai e che luna fa", async () => {
    await app({
      night: "2026-09-19",
      site: { name: "Vicenza", sky_sqm: 20.8, bortle: 4 },
      moon: LUNA,
    })

    expect(await screen.findByText("Vicenza")).toBeDefined()
    // sito e classe stanno in una riga sola: "Vicenza - Bortle 4"
    expect(screen.getByText(/Bortle 4/)).toBeDefined()
    expect(screen.getByText(/Gibbosa crescente/)).toBeDefined()
    expect(screen.getByText(/illuminata al 60%/)).toBeDefined()
  })

  it("l ora e quella del sito, non quella del browser", async () => {
    // L'istante arriva con lo scarto del posto (+02:00). Passando da `new Date` l'ora verrebbe
    // rimostrata nel fuso di chi guarda: chi apre l'archivio dagli Stati Uniti leggerebbe un
    // sorgere alle nove del mattino. Questa prova e' l'unica che cade se qualcuno ci mette un
    // `toLocaleTimeString`.
    await app({
      night: "2026-09-19",
      site: { name: "Vicenza", sky_sqm: 20.8, bortle: 4 },
      moon: LUNA,
    })

    // 15:49 e' l'ora **a Vicenza**. Questa macchina sta su UTC (vedi in testa), quindi un'ora
    // ricavata passando da Date direbbe 13:49 e la prova cadrebbe.
    expect(await screen.findByText("15:49")).toBeDefined()
    expect(screen.getByText("23:48")).toBeDefined()
  })

  it("una luna che non sorge lo dice a parole", async () => {
    await app({
      night: "2026-09-19",
      site: { name: "Longyearbyen", sky_sqm: null, bortle: null },
      moon: { ...LUNA, rise: null },
    })

    expect(await screen.findByText(/non sorge stanotte/)).toBeDefined()
    expect(screen.queryByText("15:49")).toBeNull()
  })

  it("un sito col fuso irriconoscibile si legge lo stesso, e dice cosa manca", async () => {
    // E' il ramo che il backend produce apposta quando il fuso salvato non esiste piu': il sito
    // c'e', la Luna no. Senza questa riga il piede poteva restare muto e la suite verde.
    await app({ night: null, site: { name: "Vicenza", sky_sqm: 20.8, bortle: 4 }, moon: null })

    expect(await screen.findByText("Vicenza")).toBeDefined()
    expect(screen.getByText(/il fuso di questo sito non si riconosce/i)).toBeDefined()
  })

  it("senza sito dice cosa manca, e non promette una pagina che non c e", async () => {
    await app({ night: null, site: null, moon: null })

    expect(await screen.findByText(/Non so da dove osservi/)).toBeDefined()
    expect(screen.getByRole("link", { name: /scegli il sito/i })).toBeDefined()
    // E adesso ci porta davvero: la sezione del sito esiste, quindi il rimando si accende e va
    // **li'**, non sulla pagina generica.
    const piede = document.querySelector(".as-lato__coda")
    expect(piede?.querySelector("a")?.getAttribute("href")).toBe("/impostazioni/sito")
  })

  it("un cielo mai dichiarato si legge, non sparisce", async () => {
    await app({
      night: "2026-09-19",
      site: { name: "Passo Giau", sky_sqm: null, bortle: null },
      moon: LUNA,
    })

    expect(await screen.findByText("Passo Giau")).toBeDefined()
    expect(screen.getByText(/cielo non dichiarato/)).toBeDefined()
    // e la Luna arriva lo stesso: non dipende da quanto e' buio
    expect(screen.getByText(/Gibbosa crescente/)).toBeDefined()
  })

  it("una luna che non tramonta lo dice a parole", async () => {
    await app({
      night: "2026-09-19",
      site: { name: "Longyearbyen", sky_sqm: null, bortle: null },
      moon: { ...LUNA, set: null },
    })

    expect(await screen.findByText(/non tramonta stanotte/)).toBeDefined()
    expect(screen.queryByText("23:48")).toBeNull()
  })

  it("se il cielo non si legge lo dice, invece di restare vuoto", async () => {
    rispondi({
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": {
        stato: 200,
        corpo: { to_confirm: 0, seen: { instruments: 0, rigs: 0, objects: 0 } },
      },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/pipeline/status": { stato: 200, corpo: FERMO },
      "/api/v1/tonight": { stato: 500, corpo: {} },
    })
    await disegna()

    expect((await screen.findByRole("alert")).textContent).toMatch(/Non riesco a leggere il cielo/)
  })
  it("il lembo illuminato e quello che dice il backend, non uno a caso", async () => {
    // Sabotare `lit_side === "right"` a `true` lasciava tutta la suite verde: si poteva
    // cancellare l'unico consumatore del campo e mezzo mondo avrebbe visto la Luna specchiata.
    await app({
      night: "2026-09-19",
      site: { name: "Auckland", sky_sqm: null, bortle: null },
      moon: { ...LUNA, lit_side: "left" },
    })

    await screen.findByText(/Gibbosa crescente/)
    const illuminata = document.querySelector(".as-luna__illuminata")
    expect(illuminata?.getAttribute("d")).toBe("M 0 -10 A 10 10 0 0 0 0 10 A 2.00 10 0 0 0 0 -10 Z")
  })

  it("il grafico porta il suo dato per chi non lo vede", async () => {
    // La tela non ha assi ne' etichette, e il numero di quanto sale non e' scritto da nessuna
    // parte in barra: senza questa etichetta, chi ascolta non avrebbe niente al suo posto.
    await app({
      night: "2026-09-19",
      site: { name: "Vicenza", sky_sqm: 20.8, bortle: 4 },
      moon: LUNA,
    })

    // "fino a", non "al massimo": il glossario tiene "massimo" per il **tetto del sito**, che e'
    // un'altra cosa e sta scritta a due centimetri, sull'asse della tela grande
    expect(await screen.findByRole("img", { name: /fino a 16,1 gradi, alle 19:48/ })).toBeDefined()
  })

  it("un cielo non dichiarato spegne le tinte della rampa, invece di fingerne una", async () => {
    // Nove bande a colori piene si leggono come se una classe ci fosse. Il foglio ha lo stato
    // apposta, ed e' il caso di chi apre l'app la prima volta.
    await app({
      night: "2026-09-19",
      site: { name: "Passo Giau", sky_sqm: null, bortle: null },
      moon: LUNA,
    })

    await screen.findByText("Passo Giau")
    expect(document.querySelector(".as-bortle-scala--ignota")).not.toBeNull()
    expect(document.querySelector(".as-bortle-scala__voce--4")).toBeNull()
  })
})

describe("il meteo di stanotte, sotto la Luna", () => {
  const METEO = {
    verdict: "marginal",
    cloud_total_pct: 40,
    usable_hours: 3,
    window: "dark",
    window_hours: 8,
    agreement: { go: 1, marginal: 3, nogo: 0, unknown: 0, total: 4 },
    wind_700hpa_kmh: 42,
    wind_700hpa_tenths: 8,
  }

  it("dice il verdetto, le ore utili, l'accordo e il vento in quota, e porta al Meteo", async () => {
    await app({ night: "2026-09-19", site: { name: "Vicenza", sky_sqm: 20.8, bortle: 4 }, moon: LUNA, weather: METEO })

    expect(await screen.findByText(/3 modelli su 4/)).toBeDefined()
    expect(screen.getByText(/Nuvole in media al 40%/)).toBeDefined()
    expect(screen.getByText(/3 ore utili su 8 di buio/)).toBeDefined()
    expect(screen.getByText(/piu' forte di 8 notti su 10/)).toBeDefined()
    expect(screen.getByRole("link", { name: "Apri il Meteo" }).getAttribute("href")).toBe("/meteo")
  })

  it("senza la previsione di stanotte lo dice, e porta al Meteo che spiega perche'", async () => {
    await app({ night: "2026-09-19", site: { name: "Vicenza", sky_sqm: 20.8, bortle: 4 }, moon: LUNA })

    expect(await screen.findByText("Non c'e' ancora una previsione di stanotte: il Meteo ti dice perche'.")).toBeDefined()
    expect(screen.getByRole("link", { name: "Apri il Meteo" })).toBeDefined()
  })
})

describe("il meteo di stanotte, senza fuso", () => {
  it("non promette una previsione che senza fuso non arrivera' mai", async () => {
    await app({ night: null, site: { name: "Al largo", sky_sqm: null, bortle: null }, moon: null })

    expect(await screen.findByText(/fuso/i)).toBeDefined()
    expect(screen.queryByText("Non c'e' ancora una previsione di stanotte: il Meteo ti dice perche'.")).toBeNull()
  })
})

describe("quando Stanotte si rilegge da sola", () => {
  it("spesso solo mentre la previsione di una notte che si divide non e' arrivata", () => {
    expect(rileggiOgni({ moon: LUNA, weather: null })).toBe(5 * 60 * 1000)
    expect(rileggiOgni({ moon: LUNA, weather: { verdict: "go" } })).toBe(false)
    expect(rileggiOgni({ moon: null, weather: null })).toBe(false)
    expect(rileggiOgni(undefined)).toBe(false)
  })
})
