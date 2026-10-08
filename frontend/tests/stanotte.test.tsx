// @vitest-environment jsdom
/**
 * Stanotte nel telaio (ADR 0018): la pastiglia in alto dice il sito e apre il pannello col sito
 * da scegliere, la Luna e il meteo della notte.
 *
 * Qui si provano le regole che una lettura del codice non prende: che ogni vuoto diventi una
 * frase, che l'ora sia quella del sito e non del browser, che il sito si scelga scrivendolo al
 * backend, e che non si prometta una pagina che non esiste.
 */
// Il fuso della macchina si fissa **prima** che qualcuno legga una data. Senza, la prova
// sull'ora non protegge niente su un computer a +02:00 -- cioe' proprio quello dove il cancello
// gira -- perche' l'ora del sito e quella del browser sarebbero lo stesso numero, e il difetto
// passerebbe verde. Visto: sabotato, con il fuso di casa restava verde; con questa riga cade.
process.env.TZ = "UTC"

import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { rileggiOgni } from "../src/Stanotte"
import { FERMO, SALUTE, SITO_DI_CASA, STANOTTE, disegna, impostazioni, pulisci, rispondi, scritture } from "./banco"

// Stanotte ricorda in questo browser se era aperta: senza pulire, una prova aprirebbe la
// successiva gia' aperta.
afterEach(() => {
  pulisci()
  localStorage.clear()
})

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
 *  porta -- una finta che le omette prova una risposta che nessun utente vedra' mai. */
const FASCE = [
  { starts_at: "2026-09-19T12:00:00+02:00", ends_at: "2026-09-19T19:00:00+02:00", kind: "day" },
  { starts_at: "2026-09-19T19:00:00+02:00", ends_at: "2026-09-19T20:30:00+02:00", kind: "civil" },
  { starts_at: "2026-09-19T20:30:00+02:00", ends_at: "2026-09-20T05:00:00+02:00", kind: "dark" },
  { starts_at: "2026-09-20T05:00:00+02:00", ends_at: "2026-09-20T12:00:00+02:00", kind: "day" },
]

const VICENZA = { name: "Vicenza", sky_sqm: 20.8, bortle: 4 }
const GIAU = { ...SITO_DI_CASA, id: 2, name: "Passo Giau", sky_sqm: null, bortle: null, is_default: false }

function app(stanotte: Record<string, unknown>, siti: unknown[] = [SITO_DI_CASA]) {
  rispondi({
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": {
      stato: 200,
      corpo: { to_confirm: 0 },
    },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/pipeline/status": { stato: 200, corpo: FERMO },
    "/api/v1/tonight": { stato: 200, corpo: { sky_bands: FASCE, weather: null, ...stanotte } },
    "POST /api/v1/sites": { stato: 200, corpo: { ...GIAU, is_default: true } },
    "/api/v1/sites": { stato: 200, corpo: { items: siti, total: siti.length, limit: 50, offset: 0 } },
  })
  return disegna()
}

/** Apre Stanotte dalla pastiglia, come chi usa l'app, e torna il pannello. */
async function apri(pastiglia: RegExp) {
  fireEvent.click(await screen.findByRole("button", { name: pastiglia }))
  return screen.findByRole("complementary", { name: "Stanotte" })
}

describe("la pastiglia", () => {
  it("dice il sito, e apre Stanotte", async () => {
    await app({ night: "2026-09-19", site: VICENZA, moon: LUNA })
    const pastiglia = await screen.findByRole("button", { name: "Stanotte a Vicenza" })
    expect(pastiglia.textContent).toContain("Vicenza")
    const telaio = document.querySelector(".as-telaio")
    expect(pastiglia.getAttribute("aria-expanded")).toBe("false")
    expect(telaio?.getAttribute("data-stanotte")).toBe("chiusa")
    expect(screen.queryByRole("complementary", { name: "Stanotte" })).toBeNull()

    fireEvent.click(pastiglia)
    expect(pastiglia.getAttribute("aria-expanded")).toBe("true")
    expect(telaio?.getAttribute("data-stanotte")).toBe("aperta")
    expect(await screen.findByRole("complementary", { name: "Stanotte" })).toBeDefined()
  })

  it("senza sito chiede di sceglierlo", async () => {
    await app({ night: null, site: null, moon: null })
    const pastiglia = await screen.findByRole("button", { name: "Seleziona sito" })
    expect(pastiglia.textContent).toContain("Seleziona sito")
  })

  it("Esc chiude Stanotte, e il fuoco torna alla pastiglia", async () => {
    // Chi apre da tastiera deve poter richiudere senza cercare il bottone, e ritrovarsi dove era.
    await app({ night: "2026-09-19", site: VICENZA, moon: LUNA })
    const pannello = await apri(/stanotte a vicenza/i)
    const pastiglia = screen.getByRole("button", { name: "Stanotte a Vicenza" })
    // il fuoco entra nel pannello, sul suo titolo
    await waitFor(() => expect(document.activeElement?.id).toBe("stanotte-titolo"))

    fireEvent.keyDown(within(pannello).getByRole("heading", { name: "Stanotte" }), { key: "Escape" })
    expect(pastiglia.getAttribute("aria-expanded")).toBe("false")
    expect(screen.queryByRole("complementary", { name: "Stanotte" })).toBeNull()
    await waitFor(() => expect(document.activeElement).toBe(pastiglia))
  })
})

describe("il pannello di Stanotte", () => {
  it("dice da dove osservi, che cielo hai e che luna fa", async () => {
    await app({ night: "2026-09-19", site: VICENZA, moon: LUNA })
    const pannello = await apri(/stanotte a vicenza/i)

    expect(await within(pannello).findByText("Bortle 4")).toBeDefined()
    expect(within(pannello).getByText(/Gibbosa crescente/)).toBeDefined()
    expect(within(pannello).getByText(/illuminata al 60%/)).toBeDefined()
  })

  it("l ora e quella del sito, non quella del browser", async () => {
    // L'istante arriva con lo scarto del posto (+02:00). Passando da `new Date` l'ora verrebbe
    // rimostrata nel fuso di chi guarda: chi apre l'archivio dagli Stati Uniti leggerebbe un
    // sorgere alle nove del mattino. Questa prova e' l'unica che cade se qualcuno ci mette un
    // `toLocaleTimeString`.
    await app({ night: "2026-09-19", site: VICENZA, moon: LUNA })
    const pannello = await apri(/stanotte a vicenza/i)

    // 15:49 e' l'ora **a Vicenza**. Questa macchina sta su UTC (vedi in testa), quindi un'ora
    // ricavata passando da Date direbbe 13:49 e la prova cadrebbe.
    expect(await within(pannello).findByText("15:49")).toBeDefined()
    expect(within(pannello).getByText("23:48")).toBeDefined()
  })

  it("una luna che non sorge lo dice a parole", async () => {
    await app({
      night: "2026-09-19",
      site: { name: "Longyearbyen", sky_sqm: null, bortle: null },
      moon: { ...LUNA, rise: null },
    })
    const pannello = await apri(/stanotte a longyearbyen/i)

    expect(await within(pannello).findByText("non sorge")).toBeDefined()
    expect(within(pannello).queryByText("15:49")).toBeNull()
  })

  it("una luna che non tramonta lo dice a parole", async () => {
    await app({
      night: "2026-09-19",
      site: { name: "Longyearbyen", sky_sqm: null, bortle: null },
      moon: { ...LUNA, set: null },
    })
    const pannello = await apri(/stanotte a longyearbyen/i)

    expect(await within(pannello).findByText("non tramonta")).toBeDefined()
    expect(within(pannello).queryByText("23:48")).toBeNull()
  })

  it("un sito col fuso irriconoscibile si legge lo stesso, e dice cosa manca", async () => {
    // E' il ramo che il backend produce apposta quando il fuso salvato non esiste piu': il sito
    // c'e', la Luna no. Senza questa riga il pannello poteva restare muto e la suite verde.
    await app({ night: null, site: VICENZA, moon: null })
    const pannello = await apri(/stanotte a vicenza/i)

    expect(await within(pannello).findByText(/fuso orario del sito non riconosciuto/i)).toBeDefined()
  })

  it("senza sito dice cosa manca, e non promette una pagina che non c e", async () => {
    await app({ night: null, site: null, moon: null })
    const pannello = await apri(/^seleziona sito$/i)

    expect(await within(pannello).findByText(/Nessun sito selezionato/)).toBeDefined()
    // E ci porta davvero: la sezione del sito esiste, quindi il rimando va **li'**, non sulla
    // pagina generica.
    const rimando = within(pannello).getByRole("link", { name: /^seleziona sito$/i })
    expect(rimando.getAttribute("href")).toBe("/impostazioni/sito")
  })

  it("un cielo mai dichiarato si legge, non sparisce", async () => {
    await app({
      night: "2026-09-19",
      site: { name: "Passo Giau", sky_sqm: null, bortle: null },
      moon: LUNA,
    })
    const pannello = await apri(/stanotte a passo giau/i)

    expect(await within(pannello).findByText("non dichiarato")).toBeDefined()
    // e la Luna arriva lo stesso: non dipende da quanto e' buio
    expect(within(pannello).getByText(/Gibbosa crescente/)).toBeDefined()
  })

  it("un cielo non dichiarato spegne le tinte della rampa, invece di fingerne una", async () => {
    // Una tinta piena si legge come se una classe ci fosse. Il foglio ha lo stato apposta, ed e'
    // il caso di chi apre l'app la prima volta.
    await app({
      night: "2026-09-19",
      site: { name: "Passo Giau", sky_sqm: null, bortle: null },
      moon: LUNA,
    })
    const pannello = await apri(/stanotte a passo giau/i)

    await within(pannello).findByText("non dichiarato")
    expect(pannello.querySelector(".as-bortle-letta__fascia--ignota")).not.toBeNull()
    expect(pannello.querySelector(".as-bortle-letta__fascia--4")).toBeNull()
  })

  it("se il cielo non si legge lo dice, invece di restare vuoto", async () => {
    rispondi({
      ...STANOTTE,
      "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
      "/api/v1/review": {
        stato: 200,
        corpo: { to_confirm: 0 },
      },
      "/api/health": { stato: 200, corpo: SALUTE },
      "/api/v1/pipeline/status": { stato: 200, corpo: FERMO },
      "/api/v1/tonight": { stato: 500, corpo: {} },
    })
    await disegna()
    const pannello = await apri(/^seleziona sito$/i)

    expect((await within(pannello).findByRole("alert")).textContent).toMatch(/Dati di stanotte non disponibili/)
  })

  it("il lembo illuminato e quello che dice il backend, non uno a caso", async () => {
    // Sabotare `lit_side === "right"` a `true` lasciava tutta la suite verde: si poteva
    // cancellare l'unico consumatore del campo e mezzo mondo avrebbe visto la Luna specchiata.
    await app({
      night: "2026-09-19",
      site: { name: "Auckland", sky_sqm: null, bortle: null },
      moon: { ...LUNA, lit_side: "left" },
    })
    const pannello = await apri(/stanotte a auckland/i)

    await within(pannello).findByText(/Gibbosa crescente/)
    const illuminata = pannello.querySelector(".as-luna__illuminata")
    expect(illuminata?.getAttribute("d")).toBe("M 0 -10 A 10 10 0 0 0 0 10 A 2.00 10 0 0 0 0 -10 Z")
  })
})

describe("la scelta del sito", () => {
  it("fra piu' siti, sceglierne un altro lo scrive al backend", async () => {
    // Il sito di casa e' un dato del backend: Stanotte lo chiede, non lo tiene per se'.
    await app({ night: "2026-09-19", site: VICENZA, moon: LUNA }, [SITO_DI_CASA, GIAU])
    const pannello = await apri(/stanotte a vicenza/i)

    const casa = await within(pannello).findByRole("radio", { name: /vicenza/i })
    expect(casa.getAttribute("aria-checked")).toBe("true")
    fireEvent.click(within(pannello).getByRole("radio", { name: /passo giau/i }))
    await waitFor(() =>
      expect(scritture().map((s) => `${s.metodo} ${new URL(s.url).pathname}`)).toContain(
        "POST /api/v1/sites/2/default",
      ),
    )
  })

  it("un sito solo non apre una scelta che non c e", async () => {
    await app({ night: "2026-09-19", site: VICENZA, moon: LUNA }, [SITO_DI_CASA])
    const pannello = await apri(/stanotte a vicenza/i)

    await within(pannello).findByText("Bortle 4")
    expect(within(pannello).queryByRole("radiogroup")).toBeNull()
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
    await app({ night: "2026-09-19", site: VICENZA, moon: LUNA, weather: METEO })
    const pannello = await apri(/stanotte a vicenza/i)

    expect(await within(pannello).findByText(/3 modelli su 4/)).toBeDefined()
    expect(within(pannello).getByText(/Nuvole in media al 40%/)).toBeDefined()
    expect(within(pannello).getByText(/3 ore utili su 8 di buio/)).toBeDefined()
    expect(within(pannello).getByText(/superiore a 8 notti su 10/)).toBeDefined()
    expect(within(pannello).getByRole("link", { name: "Apri il Meteo" }).getAttribute("href")).toBe("/meteo")
  })

  it("senza la previsione di stanotte lo dice, e porta al Meteo che spiega perche'", async () => {
    await app({ night: "2026-09-19", site: VICENZA, moon: LUNA })
    const pannello = await apri(/stanotte a vicenza/i)

    expect(
      await within(pannello).findByText("Previsione non disponibile. Dettagli nella pagina Meteo."),
    ).toBeDefined()
    expect(within(pannello).getByRole("link", { name: "Apri il Meteo" })).toBeDefined()
  })
})

describe("il meteo di stanotte, senza fuso", () => {
  it("non promette una previsione che senza fuso non arrivera' mai", async () => {
    await app({ night: null, site: { name: "Al largo", sky_sqm: null, bortle: null }, moon: null })
    const pannello = await apri(/stanotte a al largo/i)

    expect(await within(pannello).findByText(/fuso/i)).toBeDefined()
    expect(
      within(pannello).queryByText("Previsione non disponibile. Dettagli nella pagina Meteo."),
    ).toBeNull()
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
