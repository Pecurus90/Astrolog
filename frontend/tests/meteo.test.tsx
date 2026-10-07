// @vitest-environment jsdom
/**
 * La pagina **Meteo**: le prossime notti del sito di casa, per il modello scelto.
 *
 * La pagina non decide niente (`docs/domini/meteo.md`): verdetto, fattori e ore utili arrivano
 * scritti. Qui si prova che li mostra senza tradirli, che un numero che manca si dice con una
 * parola, e che lo switch e il pulsante chiedono al backend invece di rifare conti.
 */
import { fireEvent, screen, waitFor, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  SPINA,
  STANOTTE,
  type Voce,
  chiamate,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
  scritture,
} from "./banco"

afterEach(pulisci)

const MODELLI = ["best_match", "ecmwf_ifs025", "icon_seamless", "gfs_seamless"]

function ora(at: string, sky: string, campi: Record<string, number | null> = {}) {
  return {
    at,
    sky,
    cloud_total_pct: 0,
    cloud_low_pct: 0,
    cloud_mid_pct: 0,
    cloud_high_pct: 0,
    temperature_c: 12,
    humidity_pct: 60,
    dew_point_c: 4,
    wind_kmh: 5,
    wind_gust_kmh: 10,
    precip_mm: 0,
    wind_700hpa_kmh: 30,
    wind_250hpa_kmh: 120,
    wind_200hpa_kmh: 110,
    seeing_arcsec: null,
    aerosol_optical_depth: 0.12,
    dust_ugm3: null,
    moon_pct: null,
    levels: GIUDIZI,
    ...campi,
  }
}

const GIUDIZI = {
  cloud: "go", cloud_low: "go", rain: "go", gust: "go", wind: "go", condensation: "go",
  jet: "go", seeing: null, aerosol: null, moon: null,
}

function misura(code: string, campi: Record<string, unknown> = {}) {
  return {
    code, level: null, weighs: false, value: null, peak: null, peak_at: null, since: null,
    until: null, hours: 0, known_hours: 0, known_since: null, known_until: null, ...campi,
  }
}

const NOTTE = {
  night: "2026-09-26",
  trend: false,
  agreement: { go: 1, marginal: 3, nogo: 0, unknown: 0, total: 4 },
  wind_700hpa_kmh: 42,
  wind_700hpa_tenths: 8,
  verdict: "marginal",
  cloud_total_pct: 40,
  usable_hours: 3,
  usable_since: "2026-09-26T23:00:00+02:00",
  usable_until: "2026-09-27T02:00:00+02:00",
  window: "dark",
  window_hours: 8,
  shown_from: "2026-09-26T18:00:00+02:00",
  shown_until: "2026-09-27T08:00:00+02:00",
  measures: [
    misura("cloud", { level: "marginal", value: 40 }),
    misura("gust", {
      level: "nogo",
      weighs: true,
      value: 20,
      peak: 35,
      since: "2026-09-26T21:00:00+02:00",
      until: "2026-09-26T23:00:00+02:00",
      hours: 2,
    }),
    misura("humidity", { value: 60 }),
  ],
  hours: [
    ora("2026-09-26T12:00:00+02:00", "day", { seeing_arcsec: 1.25 }),
    ora("2026-09-26T22:00:00+02:00", "dark", { wind_gust_kmh: 35, dew_point_c: null, seeing_arcsec: 2.5 }),
    ora("2026-09-26T23:00:00+02:00", "dark", { wind_200hpa_kmh: 105, dust_ugm3: 7 }),
  ],
}

const TENDENZA = {
  ...NOTTE,
  night: "2026-09-29",
  trend: true,
  usable_hours: null,
  verdict: "go",
  agreement: { go: 2, marginal: 1, nogo: 1, unknown: 0, total: 4 },
  measures: [],
  hours: [],
}

function meteo(corpo: Record<string, unknown>, altre: Record<string, Voce> = {}) {
  rispondi({
    ...STANOTTE,
    ...altre,
    "/api/v1/weather": {
      stato: 200,
      corpo: {
        site: "Casa",
        missing: null,
        model: "best_match",
        models: MODELLI,
        fetched_at: null,
        full_nights: 3,
        seeing: { key: false, source: null, meteoblue: null },
        sources: [
          { source: "cams", fetched_at: "2026-09-25T15:00:00.000Z" },
        ],
        scales: [],
        nights: [],
        ...corpo,
      },
    },
    "/api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    "/api/health": { stato: 200, corpo: SALUTE },
    ...SPINA,
  })
}

/** Dalla barra, come l'utente: prova anche che la voce sia accesa. */
async function apriMeteo() {
  const reso = await disegna()
  fireEvent.click(await screen.findByRole("link", { name: /meteo/i }))
  await screen.findByRole("heading", { level: 1, name: /meteo/i })
  return reso
}

describe("il Meteo", () => {
  it("una notte dice il verdetto, le nuvole, le ore utili e cosa pesa, con l'ora del posto", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] })
    await apriMeteo()

    const notte = await screen.findByRole("region", { name: /notte del/i })
    const testo = notte.textContent ?? ""
    expect(testo).toMatch(/incerta/i)
    expect(testo).toContain("40%")
    expect(testo).toContain("3 ore utili su 8 di buio")
    expect(testo).toContain("Raffiche: niente.")
    // pesa solo cio' che e' incerto o niente: le nuvole sono il verdetto, l'umidita' non ha soglia
    expect(within(notte).getAllByRole("listitem")).toHaveLength(1)
    expect(testo).toContain("Dalle 21:00 alle 23:00, 2 ore")
  })

  it("ora per ora, un numero che il modello non da' si dice, non si scrive zero", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] })
    await apriMeteo()

    const [tabella] = await screen.findAllByRole("table")
    const righe = within(tabella as HTMLElement).getAllByRole("row")
    expect(righe).toHaveLength(4)
    expect(righe[2]?.textContent).toContain("22:00")
    expect(righe[2]?.textContent).toContain("buio")
    expect(righe[2]?.textContent).toContain("non lo dice")
  })

  it("senza sito di casa manda a dichiararlo", async () => {
    meteo({ site: null })
    await apriMeteo()

    expect(await screen.findByText(/manca il sito di casa/i)).toBeDefined()
    const dentro = within(screen.getByRole("main"))
    expect(dentro.getByRole("link", { name: /aggiungi il sito/i })).toBeDefined()
  })

  it("prima della prima previsione lo dice, invece di un elenco vuoto muto", async () => {
    meteo({})
    await apriMeteo()

    expect(await screen.findByText(/non e' ancora arrivata nessuna previsione/i)).toBeDefined()
  })

  it("dove il buio non arriva lo dice, e dove il Sole non tramonta non da' un verdetto finto", async () => {
    const nord = { ...NOTTE, night: "2026-06-21", window: "sun_down", measures: [] }
    const polo = { ...NOTTE, night: "2026-06-22", verdict: null, cloud_total_pct: null, usable_hours: null, window: null, window_hours: 0, measures: [] }
    meteo({ fetched_at: "2026-06-21T10:00:00.000Z", nights: [nord, polo] })
    await apriMeteo()

    const [prima, seconda] = await screen.findAllByRole("region", { name: /notte del/i })
    expect(prima?.textContent).toContain("il buio pieno non arriva")
    expect(seconda?.textContent).toContain("Il Sole non tramonta")
    expect(seconda?.textContent).toMatch(/non so dirlo/i)
  })

  it("lo switch salva il modello scelto e rilegge", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] }, {
      "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    })
    await apriMeteo()

    fireEvent.click(await screen.findByRole("radio", { name: /ICON/ }))
    await waitFor(() =>
      expect(scritture()).toContainEqual({
        url: expect.stringContaining("/api/v1/settings"),
        metodo: "PATCH",
        corpo: { values: { weather_model: "icon_seamless" } },
      }),
    )
    // e Stanotte rilegge la notte in corso dal modello nuovo
    await waitFor(() => expect(chiamate().filter((u) => u.includes("/api/v1/tonight")).length).toBeGreaterThan(1))
  })

  it("il pulsante chiede la previsione, e se il servizio tace dice che resta quella di prima", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] }, {
      "POST /api/v1/weather/refresh": { stato: 200, corpo: { status: "unreachable" } },
    })
    await apriMeteo()

    fireEvent.click(await screen.findByRole("button", { name: /aggiorna adesso/i }))
    expect(await screen.findByText(/resta la previsione di prima/i)).toBeDefined()
  })

  it("dopo il pulsante anche Stanotte rilegge la notte in corso", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] }, {
      "POST /api/v1/weather/refresh": { stato: 200, corpo: { status: "ok" } },
    })
    await apriMeteo()
    await waitFor(() => expect(chiamate().filter((u) => u.includes("/api/v1/tonight"))).toHaveLength(1))

    fireEvent.click(await screen.findByRole("button", { name: /aggiorna adesso/i }))
    await waitFor(() => expect(chiamate().filter((u) => u.includes("/api/v1/tonight"))).toHaveLength(2))
  })

  it("cita il servizio da cui vengono i dati", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] })
    await apriMeteo()

    expect(await screen.findByRole("link", { name: "Weather data by Open-Meteo.com" })).toBeDefined()
  })
})

describe("il Meteo, quando manca qualcosa", () => {
  it("un modello senza notti lo dice, anche se la previsione e' arrivata", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [] })
    await apriMeteo()

    expect(await screen.findByText(/questo modello non ha notti/i)).toBeDefined()
  })

  it("un sito di casa senza fuso orario lo dice, invece di aspettare una previsione", async () => {
    meteo({ missing: "no_timezone" })
    await apriMeteo()

    expect(await screen.findByText(/non ha un fuso orario/i)).toBeDefined()
    expect(screen.queryByText(/non e' ancora arrivata/i)).toBeNull()
  })
})

describe("il Meteo, dopo le prime notti e in quota", () => {
  it("accanto al verdetto dice quanti modelli sono d'accordo", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] })
    await apriMeteo()

    const notte = await screen.findByRole("region", { name: /notte del/i })
    expect(notte.textContent).toContain("3 modelli su 4 dicono che e' incerta")
  })

  it("dalla quarta notte mostra la tendenza, senza ore", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE, TENDENZA] })
    await apriMeteo()

    const [, tendenza] = await screen.findAllByRole("region", { name: /notte del/i })
    expect(tendenza?.textContent).toContain("piu' avanti di 3 notti")
    expect(tendenza?.textContent).not.toMatch(/ore utili/)
    expect(tendenza?.textContent).toContain("8 ore di buio")
    expect(tendenza?.textContent).toContain("Nuvole in media al 40%")
    expect(tendenza?.textContent).toContain("2 modelli su 4 dicono che si fa")
    expect(within(tendenza as HTMLElement).queryByText(/ora per ora/i)).toBeNull()
  })

  it("il cielo in quota scrive il seeing ora per ora, e un'ora senza lo dice", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] })
    await apriMeteo()

    const [, quota] = await screen.findAllByRole("table")
    const righe = within(quota as HTMLElement).getAllByRole("row")
    // le celle nell'ordine delle colonne: 700, 250 e 200 hPa, seeing, aerosol, polveri
    const celle = (r: number) => within(righe[r] as HTMLElement).getAllByRole("cell").map((c) => c.textContent)
    expect(celle(1)).toEqual(["30", "120", "110", "1,25", "0,12", "non lo dice"])
    expect(celle(2)).toEqual(["30", "120", "110", "2,5", "0,12", "non lo dice"])
    expect(celle(3)).toEqual(["30", "120", "105", "non lo dice", "0,12", "7"])
  })

  it("cita i dati Copernicus con l'anno, e 7Timer non c'e' piu'", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] })
    await apriMeteo()

    expect(await screen.findByText(/Copernicus Atmosphere Monitoring Service information 2026/)).toBeDefined()
    expect(screen.queryByText(/7Timer/)).toBeNull()
  })
})

describe("il Meteo, l'accordo al singolare", () => {
  it("un modello solo si dice al singolare", async () => {
    meteo({
      fetched_at: "2026-09-25T15:00:00.000Z",
      nights: [{ ...NOTTE, agreement: { go: 0, marginal: 1, nogo: 3, unknown: 0, total: 4 } }],
    })
    await apriMeteo()

    const notte = await screen.findByRole("region", { name: /notte del/i })
    expect(notte.textContent).toContain("1 modello su 4 dice che e' incerta")
  })
})

describe("il Meteo, le fonti citate", () => {
  it("cita solo le fonti del cielo che hanno scritto qualcosa", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], sources: [] })
    await apriMeteo()

    await screen.findByRole("link", { name: "Weather data by Open-Meteo.com" })
    expect(screen.queryByRole("link", { name: /7Timer/ })).toBeNull()
    expect(screen.queryByText(/Copernicus/)).toBeNull()
  })

  it("una fonte che la pagina non conosce non si cita con le parole di un'altra", async () => {
    meteo({
      fetched_at: "2026-09-25T15:00:00.000Z",
      nights: [NOTTE],
      sources: [{ source: "altra", fetched_at: "2026-09-25T15:00:00.000Z" }],
    })
    await apriMeteo()

    await screen.findByRole("link", { name: "Weather data by Open-Meteo.com" })
    expect(screen.queryByText(/Copernicus/)).toBeNull()
    expect(screen.queryByRole("link", { name: /7Timer/ })).toBeNull()
  })
})

describe("il Meteo, da dove viene il seeing", () => {
  it("dice che il seeing viene da Meteoblue quando c'e' la chiave", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], seeing: { key: true, source: "meteoblue", meteoblue: "ok" } })
    await apriMeteo()

    expect(await screen.findByText(/viene da Meteoblue, ora per ora/)).toBeDefined()
  })

  it("se Meteoblue non accetta la chiave lo dice, e manda alle Impostazioni", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], seeing: { key: true, source: null, meteoblue: "refused" } })
    await apriMeteo()

    const riga = await screen.findByText(/Meteoblue non accetta la chiave/)
    expect(riga.textContent).toMatch(/Impostazioni/)
  })

  it("senza chiave dice che il seeing vuole una chiave Meteoblue", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], seeing: { key: false, source: null, meteoblue: null } })
    await apriMeteo()

    expect(await screen.findByText(/serve una chiave Meteoblue, gratuita/)).toBeDefined()
  })

  it("con la chiave appena messa e Meteoblue non ancora chiesto non chiede la chiave", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], seeing: { key: true, source: null, meteoblue: null } })
    await apriMeteo()

    await screen.findByRole("link", { name: "Weather data by Open-Meteo.com" })
    expect(screen.queryByText(/serve una chiave Meteoblue/)).toBeNull()
  })

  it("cita Meteoblue quando il seeing viene da li'", async () => {
    meteo({
      fetched_at: "2026-09-25T15:00:00.000Z",
      nights: [NOTTE],
      sources: [{ source: "meteoblue", fetched_at: "2026-09-25T15:00:00.000Z" }],
    })
    await apriMeteo()

    expect(await screen.findByRole("link", { name: /meteoblue/i })).toBeDefined()
  })
})

describe("il Meteo, il seeing di Meteoblue", () => {
  it("il seeing si scrive come un numero, in secondi d'arco", async () => {
    const conMeteoblue = { ...NOTTE, hours: [ora("2026-09-26T22:00:00+02:00", "dark", { seeing_arcsec: 0.9 })] }
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [conMeteoblue] })
    await apriMeteo()

    const [, quota_] = await screen.findAllByRole("table")
    const cella = within(quota_ as HTMLElement).getAllByRole("cell")[3]
    expect(cella?.textContent).toBe("0,9")
  })
})

describe("il Meteo, il vento in quota accanto al suo solito", () => {
  it("dice quante notti su dieci dell'ultimo anno, qui, avevano meno vento", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] })
    await apriMeteo()

    const notte = await screen.findByRole("region", { name: /notte del/i })
    expect(notte.textContent).toContain("Vento in quota 42 km/h: piu' forte di 8 notti su 10 dell'ultimo anno, qui.")
  })

  it("senza la storia del sito dice il vento e che il confronto arriva, senza inventarlo", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [{ ...NOTTE, wind_700hpa_tenths: null }] })
    await apriMeteo()

    const notte = await screen.findByRole("region", { name: /notte del/i })
    expect(notte.textContent).toContain("Vento in quota 42 km/h. Il confronto col solito del sito arriva")
    expect(notte.textContent).not.toContain("notti su 10")
  })

  it.each([
    [0, "fra i piu' deboli dell'ultimo anno, qui."],
    [1, "piu' forte di 1 notte su 10 dell'ultimo anno"],
    [10, "fra i piu' forti dell'ultimo anno, qui."],
  ])("agli estremi e con una notte sola si dice come si parla (%i)", async (decimi, frase) => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [{ ...NOTTE, wind_700hpa_tenths: decimi }] })
    await apriMeteo()

    const notte = await screen.findByRole("region", { name: /notte del/i })
    expect(notte.textContent).toContain(frase)
  })

  it("una notte senza il vento in quota non ne parla", async () => {
    meteo({
      fetched_at: "2026-09-25T15:00:00.000Z",
      nights: [{ ...NOTTE, wind_700hpa_kmh: null, wind_700hpa_tenths: null }],
    })
    await apriMeteo()

    const notte = await screen.findByRole("region", { name: /notte del/i })
    expect(notte.textContent).not.toContain("Vento in quota")
  })
})
