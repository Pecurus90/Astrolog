// @vitest-environment jsdom
/**
 * La pagina **Meteo** nel disegno v27/v28: le prossime notti del sito di casa, una alla volta.
 *
 * La pagina non decide niente (`docs/domini/meteo.md`): verdetto, giudizi, ore serene, ordine
 * delle misure e scale arrivano scritti. Qui si prova che li mostra senza tradirli, che un numero
 * che manca si dice con una parola, e che lo switch e il pulsante chiedono al backend invece di
 * rifare conti.
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

const GIUDIZI = {
  cloud: "go", cloud_low: "go", rain: "go", gust: "go", wind: "go", condensation: "go",
  jet: "go", seeing: null, aerosol: null, moon: null,
}

function ora(at: string, sky: string, campi: Record<string, unknown> = {}) {
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
    dew_spread_c: 8,
    levels: GIUDIZI,
    shown: true,
    ...campi,
  }
}

function misura(code: string, campi: Record<string, unknown> = {}) {
  return {
    code, level: null, weighs: false, value: null, peak: null, peak_at: null, peak_until: null,
    spans: [], axis_min: 0, axis_max: 100, since: null, until: null, hours: 0, known_hours: 3,
    known_since: null, known_until: null, ...campi,
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
  shown_from: "2026-09-26T19:00:00+02:00",
  shown_until: "2026-09-26T23:00:00+02:00",
  measures: [
    misura("cloud", { level: "marginal", value: 40, peak: 80, peak_at: "2026-09-26T22:00:00+02:00", peak_until: "2026-09-26T23:00:00+02:00" }),
    misura("cloud_low", { level: "go", value: 5 }),
    misura("wind", {
      level: "nogo",
      weighs: true,
      value: 20,
      axis_max: 45,
      spans: [
        { level: "marginal", since: "2026-09-26T20:00:00+02:00", until: "2026-09-26T21:00:00+02:00", hours: 1 },
        { level: "nogo", since: "2026-09-26T21:00:00+02:00", until: "2026-09-26T23:00:00+02:00", hours: 2 },
      ],
      since: "2026-09-26T21:00:00+02:00",
      until: "2026-09-26T23:00:00+02:00",
      hours: 2,
    }),
    misura("gust", { level: "go", peak: 35, peak_at: "2026-09-26T22:00:00+02:00", peak_until: "2026-09-26T23:00:00+02:00" }),
    misura("rain", { level: "go", value: 0, peak: 0, axis_max: 1.5 }),
    misura("seeing", { known_hours: 0 }),
    misura("aerosol", { level: "go", value: 0.05, axis_max: 0.2 }),
    misura("temperature", { value: 5, axis_min: 4, axis_max: 12 }),
    misura("dew_point", { value: 4 }),
    misura("humidity", { value: 90 }),
    misura("wind_700", { value: 42 }),
  ],
  hours: [
    ora("2026-09-26T12:00:00+02:00", "day", { shown: false }),
    ora("2026-09-26T19:00:00+02:00", "civil"),
    ora("2026-09-26T22:00:00+02:00", "dark", { wind_kmh: null, wind_gust_kmh: 35 }),
    ora("2026-09-26T23:00:00+02:00", "dark"),
  ],
}

const TENDENZA = {
  ...NOTTE,
  night: "2026-09-29",
  trend: true,
  usable_hours: null,
  usable_since: null,
  usable_until: null,
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
        last_request: null,
        full_nights: 3,
        seeing: { key: false, source: null, meteoblue: null },
        sources: [{ source: "cams", fetched_at: "2026-09-25T15:00:00.000Z" }],
        scales: [
          { code: "wind", steps: [{ level: "nogo", bound: 29, strict: false }, { level: "marginal", bound: 20, strict: false }], lower_is_worse: false },
          { code: "condensation", steps: [{ level: "nogo", bound: 3, strict: true }], lower_is_worse: true },
        ],
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

const conNotti = (...notti: unknown[]) => meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: notti })
const scheda = () => screen.findByRole("tabpanel")

function carta(nome: RegExp) {
  const titolo = screen.getAllByRole("heading", { level: 3 }).find((h) => nome.test(h.textContent ?? ""))
  return titolo?.closest("article") as HTMLElement
}

describe("il Meteo, la notte", () => {
  it("in testa le ore serene col semaforo, da che ora a che ora e l'accordo, con l'ora del posto", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    const testo = (await scheda()).textContent ?? ""
    expect(testo).toContain("Notte di sabato 26 \u00b7 stanotte")
    expect(testo).toContain("3 ore di buio sereno")
    expect(testo).toContain("incerta")
    expect(testo).toContain("dalle 23:00 alle 02:00, 3 ore")
    expect(testo).toContain("accordo dei modelli 3 su 4")
  })

  it("accanto al semaforo pesa solo cio' che il backend dice incerto o niente, con la parola e le ore", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    const pesano = (await scheda()).querySelector(".as-pesano") as HTMLElement
    const voci = within(pesano).getAllByRole("listitem")
    expect(voci).toHaveLength(1)
    expect(voci[0]?.textContent).toContain("niente")
    expect(voci[0]?.textContent).toContain("Vento dalle 21:00 alle 23:00 \u00b7 2 ore")
  })

  it("se non pesa niente lo dice", async () => {
    conNotti({ ...NOTTE, measures: NOTTE.measures.map((m) => ({ ...m, weighs: false })) })
    await apriMeteo()

    expect((await scheda()).textContent).toContain("Nient'altro pesa sulla notte.")
  })

  it("la fila dice il giorno, il semaforo e le ore serene di ogni notte, e ne apre una alla volta", async () => {
    conNotti(NOTTE, TENDENZA)
    await apriMeteo()

    const voci = await screen.findAllByRole("tab")
    expect(voci[0]?.textContent).toContain("sab 26")
    expect(voci[0]?.textContent).toContain("3 ore \u00b7 23\u201302")
    expect(voci[0]?.getAttribute("aria-selected")).toBe("true")
    expect(voci[1]?.textContent).toContain("8 ore di buio")
    expect(screen.getAllByRole("tabpanel")).toHaveLength(1)
  })

  it("dalla quarta notte mostra la tendenza, senza ore serene ne' carte, e lo dice", async () => {
    conNotti(NOTTE, TENDENZA)
    await apriMeteo()

    fireEvent.click((await screen.findAllByRole("tab"))[1] as HTMLElement)
    const tendenza = await scheda()
    expect(tendenza.textContent).toMatch(/Notte di \S+ 29 \u00b7 tendenza/)
    expect(tendenza.textContent).toContain("8 ore di buio")
    expect(tendenza.textContent).toContain("nuvole al 40% nel buio")
    expect(tendenza.textContent).toContain("accordo dei modelli 2 su 4")
    expect(tendenza.textContent).toContain("Dalla quarta notte la previsione e' una tendenza")
    expect(within(tendenza).queryAllByRole("article")).toHaveLength(0)
  })

  it("dove il buio non arriva conta le ore col Sole sotto l'orizzonte, e dove il Sole non tramonta non da' un verdetto finto", async () => {
    conNotti({ ...NOTTE, window: "sun_down" })
    await apriMeteo()
    expect((await scheda()).textContent).toContain("serene col Sole sotto l'orizzonte")
    pulisci()

    conNotti({ ...NOTTE, verdict: null, usable_hours: null, usable_since: null, usable_until: null, window: null, window_hours: 0 })
    await apriMeteo()
    const polo = await scheda()
    expect(polo.textContent).toContain("Sole sempre su")
    expect(polo.querySelector(".as-semaforo--grande")).toBeNull()
    expect(within(polo).queryAllByRole("article")).toHaveLength(0)
  })

  it("senza le nuvole di tutte le ore il verdetto non si sa, e non si inventa", async () => {
    conNotti({ ...NOTTE, verdict: null })
    await apriMeteo()

    expect((await scheda()).textContent).toContain("non si sa")
  })
})

describe("il Meteo, le carte", () => {
  it("vengono nell'ordine del backend, prima le grandi e poi le piccole", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    const nomi = screen.getAllByRole("heading", { level: 3 }).map((h) => h.textContent)
    expect(nomi).toEqual([
      "Nuvole", "Nuvole basse", "Vento", "Pioggia", "Seeing", "Aerosol",
      "Temperatura e rugiada", "Umidita'", "Vento a 700 hPa",
    ])
  })

  it("una carta dice il valore, cosa vuol dire, ogni parola con la sua ora e il picco", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    const vento = carta(/^Vento$/)
    expect(vento.textContent).toContain("20")
    expect(vento.textContent).toContain("media nel buio, a 10 m")
    expect(vento.textContent).toContain("incerta dalle 20:00, niente dalle 21:00")
    expect(vento.textContent).toContain("raffiche fino a 35 km/h tra le 22:00 e le 23:00")
  })

  it("un'ora che il servizio non da' si disegna a tratteggio, mai come uno zero", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    const barre = carta(/^Vento$/).querySelectorAll("rect")
    const tratteggiate = [...barre].filter((r) => r.getAttribute("fill")?.startsWith("url("))
    expect(tratteggiate).toHaveLength(1)
  })

  it("le barre prendono il colore del giudizio di ogni ora, e le ore non disegnate restano fuori", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    const barre = carta(/^Nuvole$/).querySelectorAll(".as-parametro__barra")
    expect(barre).toHaveLength(3) // l'ora di mezzogiorno non e' fra quelle da disegnare
    expect([...barre].every((b) => b.classList.contains("as-parametro__tinta--buona"))).toBe(true)
  })

  it("la pioggia che non c'e' lo dice, invece di un picco a zero", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    expect(carta(/^Pioggia$/).textContent).toContain("nessuna ora con pioggia")
  })

  it("senza nessuna ora data, pioggia e condensa non dicono che non ce n'e'", async () => {
    const muta = { level: null, value: null, peak: null, known_hours: 0 }
    conNotti({
      ...NOTTE,
      measures: [...NOTTE.measures.filter((m) => m.code !== "rain"), misura("rain", muta), misura("condensation", muta)],
    })
    await apriMeteo()

    await scheda()
    expect(carta(/^Pioggia$/).textContent).not.toContain("nessuna ora con pioggia")
    expect(carta(/^Condensa$/).textContent).not.toContain("mai sotto")
  })

  it("una linea si spezza dove il servizio non da' il valore, invece di unire i due lati", async () => {
    const buco = NOTTE.hours.map((o, i) => (i === 2 ? { ...o, humidity_pct: null } : o))
    conNotti({ ...NOTTE, hours: buco })
    await apriMeteo()

    await scheda()
    expect(carta(/^Umidit/).querySelectorAll("polyline")).toHaveLength(2)
  })

  it("la temperatura dice la minima e la rugiada accanto", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    expect(carta(/^Temperatura/).textContent).toContain("minima nel buio \u00b7 rugiada 4 \u00b0C")
  })

  it.each([
    [8, "piu' forte di 8 notti su 10, qui"],
    [0, "fra i piu' deboli dell'anno, qui"],
    [1, "piu' forte di 1 notte su 10, qui"],
    [10, "fra i piu' forti dell'anno, qui"],
    [null, "il confronto col solito del sito arriva con piu' notti"],
  ])("il vento a 700 hPa si legge accanto al solito del sito (%s)", async (decimi, frase) => {
    conNotti({ ...NOTTE, wind_700hpa_tenths: decimi })
    await apriMeteo()

    await scheda()
    expect(carta(/700 hPa/).textContent).toContain(frase)
  })
})

describe("il Meteo, il seeing", () => {
  it("senza chiave la carta dice che serve una chiave Meteoblue, e porta alle Impostazioni", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    const seeing = carta(/^Seeing$/)
    expect(seeing.textContent).toContain("Per il seeing serve una chiave Meteoblue, gratuita.")
    expect(within(seeing).getByRole("link", { name: /apri le impostazioni/i }).getAttribute("href")).toBe("/impostazioni/servizi")
  })

  it("se Meteoblue non accetta la chiave la carta lo dice", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], seeing: { key: true, source: null, meteoblue: "refused" } })
    await apriMeteo()

    await scheda()
    expect(carta(/^Seeing$/).textContent).toContain("Meteoblue non accetta la chiave")
  })

  it("con la chiave appena messa e Meteoblue non ancora chiesto non chiede la chiave", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], seeing: { key: true, source: null, meteoblue: null } })
    await apriMeteo()

    await scheda()
    expect(screen.queryByText(/serve una chiave Meteoblue/)).toBeNull()
  })

  it("Meteoblue che tace la prima volta non promette un seeing di prima che non c'e'", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], seeing: { key: true, source: null, meteoblue: "unreachable" } })
    await apriMeteo()

    await scheda()
    expect(screen.queryByText(/resta il seeing di prima/)).toBeNull()
  })

  it("Meteoblue che tace lascia il seeing di prima, e lo dice", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], seeing: { key: true, source: "meteoblue", meteoblue: "unreachable" } })
    await apriMeteo()

    expect(await screen.findByText(/resta il seeing di prima/)).toBeDefined()
  })

  it("un seeing che copre solo parte della notte lo dice nella media e nel picco", async () => {
    const seeing = misura("seeing", {
      level: "go", value: 1.2, axis_max: 5, peak: 1.5, peak_at: "2026-09-26T22:00:00+02:00",
      peak_until: "2026-09-26T23:00:00+02:00", known_hours: 2, known_until: "2026-09-27T02:00:00+02:00",
    })
    conNotti({ ...NOTTE, measures: [...NOTTE.measures.filter((m) => m.code !== "seeing"), seeing] })
    await apriMeteo()

    await scheda()
    const testo = carta(/^Seeing$/).textContent
    expect(testo).toContain("media fino alle 02:00, Meteoblue")
    expect(testo).toContain("dalle 02:00 non fornito")
  })
})

describe("il Meteo, la testa", () => {
  it("dice dove, quando e' arrivata la previsione e che le ore sono del sito", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    const testa = document.querySelector(".as-meteo__testa") as HTMLElement
    expect(testa.textContent).toContain("meteo a Casa")
    expect(testa.textContent).toContain("Previsione arrivata il")
    expect(testa.textContent).toContain("ore del sito")
  })

  it("lo switch salva il modello scelto e rilegge, anche Stanotte", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] }, {
      "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(true) },
    })
    await apriMeteo()

    fireEvent.click(await screen.findByRole("button", { name: "ICON", pressed: false }))
    await waitFor(() =>
      expect(scritture()).toContainEqual({
        url: expect.stringContaining("/api/v1/settings"),
        metodo: "PATCH",
        corpo: { values: { weather_model: "icon_seamless" } },
      }),
    )
    await waitFor(() => expect(chiamate().filter((u) => u.includes("/api/v1/tonight")).length).toBeGreaterThan(1))
  })

  it("sul telefono il modello si sceglie da un elenco che dice cos'e' ogni voce", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    const apri = (await screen.findAllByRole("button", { name: /modello/i }))[0] as HTMLElement
    fireEvent.click(apri)
    expect(apri.getAttribute("aria-expanded")).toBe("true")
    expect(screen.getByRole("menuitemradio", { name: /ECMWF/ }).textContent).toContain("centro europeo")
  })

  it("se l'ultima richiesta non ha avuto risposta lo dice, con l'ora della previsione che resta", async () => {
    meteo({
      fetched_at: "2026-09-25T06:00:00.000Z",
      last_request: { at: "2026-09-25T12:00:00.000Z", status: "unreachable" },
      nights: [NOTTE],
    })
    await apriMeteo()

    const riga = await screen.findByText(/senza risposta: questa e' la previsione delle/)
    expect(riga.closest(".as-avviso")?.querySelector(".as-bottone--tenue")?.textContent).toMatch(/aggiorna/i)
  })

  it("anche senza nessuna previsione, una richiesta senza risposta lo dice", async () => {
    meteo({ last_request: { at: "2026-09-25T12:00:00.000Z", status: "unreachable" } })
    await apriMeteo()

    expect(await screen.findByText(/senza risposta: non c'e' ancora nessuna previsione/)).toBeDefined()
  })

  it("dopo Aggiorna senza risposta la pagina rilegge e la riga compare", async () => {
    meteo({ fetched_at: "2026-09-25T06:00:00.000Z", last_request: { at: "2026-09-25T06:00:00.000Z", status: "ok" }, nights: [NOTTE] }, {
      "POST /api/v1/weather/refresh": { stato: 200, corpo: { status: "unreachable" } },
    })
    await apriMeteo()
    await scheda()
    expect(screen.queryByText(/senza risposta/)).toBeNull()

    meteo({ fetched_at: "2026-09-25T06:00:00.000Z", last_request: { at: "2026-09-25T12:00:00.000Z", status: "unreachable" }, nights: [NOTTE] }, {
      "POST /api/v1/weather/refresh": { stato: 200, corpo: { status: "unreachable" } },
    })
    fireEvent.click(screen.getAllByRole("button", { name: /^aggiorna$/i })[0] as HTMLElement)
    expect(await screen.findByText(/senza risposta: questa e' la previsione delle/)).toBeDefined()
  })

  it("se l'ultima richiesta e' andata bene non dice niente", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", last_request: { at: "2026-09-25T15:00:00.000Z", status: "ok" }, nights: [NOTTE] })
    await apriMeteo()

    await scheda()
    expect(screen.queryByText(/senza risposta/)).toBeNull()
  })

  it("dopo il pulsante anche Stanotte rilegge la notte in corso", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE] }, {
      "POST /api/v1/weather/refresh": { stato: 200, corpo: { status: "ok" } },
    })
    await apriMeteo()
    await waitFor(() => expect(chiamate().filter((u) => u.includes("/api/v1/tonight"))).toHaveLength(1))

    fireEvent.click(await screen.findByRole("button", { name: /^aggiorna$/i }))
    await waitFor(() => expect(chiamate().filter((u) => u.includes("/api/v1/tonight"))).toHaveLength(2))
  })
})

describe("il Meteo, quando manca qualcosa", () => {
  it("senza sito di casa manda a dichiararlo", async () => {
    meteo({ site: null })
    await apriMeteo()

    expect(await screen.findByText(/manca il sito di casa/i)).toBeDefined()
    expect(within(screen.getByRole("main")).getByRole("link", { name: /aggiungi il sito/i })).toBeDefined()
  })

  it("prima della prima previsione lo dice, invece di un elenco vuoto muto", async () => {
    meteo({})
    await apriMeteo()

    expect(await screen.findByText(/non e' ancora arrivata nessuna previsione/i)).toBeDefined()
    // nessuna fonte ha ancora scritto niente: nessuna si cita
    expect(screen.queryByRole("link", { name: "Weather data by Open-Meteo.com" })).toBeNull()
    expect(screen.queryByRole("tablist", { name: /notti/i })).toBeNull()
  })

  it("un modello senza notti lo dice, anche se la previsione e' arrivata", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [] })
    await apriMeteo()

    expect(await screen.findByText(/questo modello non ha notti/i)).toBeDefined()
  })

  it("un sito di casa senza fuso orario lo dice, e porta a sistemarlo", async () => {
    meteo({ missing: "no_timezone" })
    await apriMeteo()

    expect(await screen.findByText(/non ha un fuso orario/i)).toBeDefined()
    expect(within(screen.getByRole("main")).getByRole("link", { name: /sistema il sito/i })).toBeDefined()
    expect(screen.queryByText(/non e' ancora arrivata/i)).toBeNull()
  })
})

describe("il Meteo, le fonti citate", () => {
  it("cita Open-Meteo e i dati Copernicus con l'anno; 7Timer non c'e' piu'", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    expect(await screen.findByRole("link", { name: "Weather data by Open-Meteo.com" })).toBeDefined()
    expect(screen.getByText(/Copernicus Atmosphere Monitoring Service information 2026/)).toBeDefined()
    expect(screen.queryByText(/7Timer/)).toBeNull()
  })

  it("cita solo le fonti del cielo che hanno scritto qualcosa, e nessuna che non conosce", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], sources: [{ source: "altra", fetched_at: "2026-09-25T15:00:00.000Z" }] })
    await apriMeteo()

    await screen.findByRole("link", { name: "Weather data by Open-Meteo.com" })
    expect(screen.queryByText(/Copernicus/)).toBeNull()
    expect(screen.queryByRole("link", { name: /meteoblue/i })).toBeNull()
  })

  it("cita Meteoblue quando il seeing viene da li'", async () => {
    meteo({ fetched_at: "2026-09-25T15:00:00.000Z", nights: [NOTTE], sources: [{ source: "meteoblue", fetched_at: "2026-09-25T15:00:00.000Z" }] })
    await apriMeteo()

    expect(await screen.findByRole("link", { name: /meteoblue/i })).toBeDefined()
  })
})

describe("il Meteo, il cielo", () => {
  const cielo = () => document.querySelector(".as-cielo") as HTMLElement

  it("disegna le nubi basse, medie e alte ognuna dal suo zero, e l'umidita' che si spegne", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    expect(cielo().querySelector(".as-cielo__basse")).not.toBeNull()
    expect(cielo().querySelector(".as-cielo__medie")).not.toBeNull()
    expect(cielo().querySelector(".as-cielo__alte")).not.toBeNull()
    const umidita = within(cielo()).getByRole("button", { name: /umidit/i })
    expect(cielo().querySelector(".as-cielo__umidita")).not.toBeNull()
    fireEvent.click(umidita)
    expect(umidita.getAttribute("aria-pressed")).toBe("false")
    expect(cielo().querySelector(".as-cielo__umidita")).toBeNull()
  })

  it("a destra si apre la metrica che pesa di piu', con la sua parola dove cambia; un'altra si sceglie", async () => {
    const ventoso = NOTTE.hours.map((o, i) => (i >= 2 ? { ...o, wind_kmh: 30, levels: { ...o.levels, wind: "nogo" } } : o))
    conNotti({ ...NOTTE, hours: ventoso })
    await apriMeteo()

    await scheda()
    const vento = within(cielo()).getByRole("button", { name: "vento" })
    expect(vento.getAttribute("aria-pressed")).toBe("true")
    expect(cielo().querySelector("svg")?.hasAttribute("data-dx-acceso")).toBe(true)
    expect(cielo().querySelector(".as-scala__parola--niente")?.textContent).toBe("niente dalle 22")
    fireEvent.click(within(cielo()).getByRole("button", { name: "pioggia" }))
    expect(within(cielo()).getByRole("button", { name: "pioggia" }).getAttribute("aria-pressed")).toBe("true")
    expect(cielo().querySelector(".as-scala__parola--niente")).toBeNull()
  })

  it("la parola della prima ora si scrive anche lei, all'inizio della scala", async () => {
    const ventoso = NOTTE.hours.map((o) => ({ ...o, wind_kmh: 30, levels: { ...o.levels, wind: "nogo" } }))
    conNotti({ ...NOTTE, hours: ventoso })
    await apriMeteo()

    await scheda()
    expect(cielo().querySelector(".as-scala__parola--niente")?.textContent).toBe("niente")
  })

  it("il seeing senza chiave c'e' fra le metriche ma non si sceglie, e dice perche'", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    const seeing = within(cielo()).getAllByRole("button", { name: "seeing" })[0] as HTMLElement
    expect(seeing.getAttribute("aria-disabled")).toBe("true")
    fireEvent.click(within(cielo()).getByRole("button", { name: /a destra/i }))
    expect(within(cielo()).getByRole("menuitemradio", { name: /seeing/ }).textContent).toContain("serve una chiave Meteoblue")
  })

  it("un'ora che il servizio non da' sulla scala di destra e' un tratteggio con \"non fornito\"", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    // il vento delle 22 manca nella notte di prova
    expect(within(cielo().querySelector("svg") as unknown as HTMLElement).getByText("non fornito")).toBeDefined()
  })

  it("la pioggia a destra: barre col colore dell'ora, e l'ora non data a tratteggio, non come uno zero", async () => {
    const piovosa = NOTTE.hours.map((o, i) =>
      i === 2 ? { ...o, precip_mm: null } : i === 3 ? { ...o, precip_mm: 0.5, levels: { ...o.levels, rain: "marginal" } } : o)
    conNotti({ ...NOTTE, hours: piovosa })
    await apriMeteo()

    await scheda()
    fireEvent.click(within(cielo()).getByRole("button", { name: "pioggia" }))
    const svg = cielo().querySelector("svg") as SVGElement
    expect(svg.querySelectorAll(".as-scala__barra.as-scala__tinta--incerta")).toHaveLength(1)
    expect(within(svg as unknown as HTMLElement).getByText("non fornito")).toBeDefined()
  })

  it("la condensa a destra e' sull'asse della temperatura: la soglia dello scarto non vi si disegna", async () => {
    // un asse da 0 a 12 °C contiene il 3 della soglia, che li' sarebbe 3 °C d'aria
    const misure = NOTTE.measures.map((m) => (m.code === "temperature" ? { ...m, axis_min: 0 } : m))
    conNotti({ ...NOTTE, measures: [...misure, misura("condensation", { level: "go" })] })
    await apriMeteo()

    await scheda()
    fireEvent.click(within(cielo()).getByRole("button", { name: /condensa/i }))
    expect(cielo().querySelector(".as-scala__soglia")).toBeNull()
  })

  it("cambiando notte le carte tornano alla notte e a destra si riapre la metrica che pesa di piu'", async () => {
    const altra = {
      ...NOTTE,
      night: "2026-09-27",
      measures: NOTTE.measures.map((m) => ({ ...m, weighs: m.code === "rain" })),
    }
    conNotti(NOTTE, altra)
    await apriMeteo()

    await scheda()
    fireEvent.keyDown(within(carta(/^Vento$/)).getByRole("slider"), { key: "End" })
    expect(carta(/^Vento$/).hasAttribute("data-a-ora")).toBe(true)
    fireEvent.click((await screen.findAllByRole("tab"))[1] as HTMLElement)
    expect(carta(/^Vento$/).hasAttribute("data-a-ora")).toBe(false)
    expect(within(cielo()).getByRole("button", { name: "pioggia" }).getAttribute("aria-pressed")).toBe("true")
  })

  it("dice le ore di buio sereno sul tratto sereno", async () => {
    const serena = NOTTE.hours.map((o, i) => (i === 3 ? { ...o, clear: true } : { ...o, clear: false }))
    conNotti({ ...NOTTE, hours: serena })
    await apriMeteo()

    await scheda()
    expect(cielo().querySelectorAll(".as-cielo__sereno")).toHaveLength(1)
    expect(cielo().textContent).toContain("buio sereno, 3 ore")
  })

  it("con le frecce il filo va a un'ora, il lettore la dice e tutte le carte la seguono; Esc torna alla notte", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    const tela = cielo().querySelector(".as-cielo__tela") as HTMLElement
    fireEvent.keyDown(tela, { key: "ArrowRight" })
    expect(tela.getAttribute("aria-valuetext")).toContain("alle 19:00")
    expect(cielo().querySelector(".as-volta__lettore")?.textContent).toContain("nubi basse")
    expect(screen.getByText("alle 19:00", { selector: ".as-soprattitolo" })).toBeDefined()
    expect(carta(/^Nuvole$/).textContent).toContain("alle 19:00")
    fireEvent.keyDown(tela, { key: "Escape" })
    expect(cielo().querySelector(".as-volta__lettore")).toBeNull()
    expect(carta(/^Nuvole$/).textContent).toContain("media nel buio")
  })
})

describe("il Meteo, una carta a un'ora", () => {
  it("le frecce sulle barrette portano la carta a un'ora e ce la lasciano; × notte la riporta", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    const vento = carta(/^Vento$/)
    const barre = within(vento).getByRole("slider")
    fireEvent.keyDown(barre, { key: "End" })
    expect(vento.textContent).toContain("alle 23:00")
    expect(vento.hasAttribute("data-a-ora")).toBe(true)
    expect(vento.querySelector(".as-parametro__mira")).not.toBeNull()
    expect(vento.querySelectorAll(".as-parametro__barra[data-spento]").length).toBeGreaterThan(0)
    // le altre carte restano sulla notte
    expect(carta(/^Nuvole$/).textContent).toContain("media nel buio")
    fireEvent.click(within(vento).getByRole("button", { name: /torna alla notte/i }))
    expect(vento.textContent).toContain("media nel buio, a 10 m")
    expect(vento.hasAttribute("data-a-ora")).toBe(false)
  })

  it("a un'ora la carta dice il valore, la parola di quell'ora e cio' che porta accanto", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    const temperatura = carta(/^Temperatura/)
    fireEvent.keyDown(within(temperatura).getByRole("slider"), { key: "Home" })
    expect(temperatura.textContent).toContain("alle 19:00 · rugiada 4 °C")
    const vento = carta(/^Vento$/)
    fireEvent.keyDown(within(vento).getByRole("slider"), { key: "ArrowRight" })
    expect(vento.textContent).toContain("raffiche 10 km/h")
    expect(vento.textContent).toContain("buona")
  })
})

describe("il Meteo, rifiniture del cielo e delle carte", () => {
  const cielo = () => document.querySelector(".as-cielo") as HTMLElement

  it("l'aerosol non ha unita': il lettore dice il numero e basta", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    fireEvent.click(within(cielo()).getAllByRole("button", { name: "aerosol" })[0] as HTMLElement)
    fireEvent.keyDown(cielo().querySelector(".as-cielo__tela") as HTMLElement, { key: "Home" })
    const riga = [...cielo().querySelectorAll(".as-volta__lettore-riga")].at(-1)
    expect(riga?.textContent).toBe("aerosol0,12")
  })

  it("col dito il filo resta dove l'hai lasciato, finche' non tocchi altrove", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    const tela = cielo().querySelector(".as-cielo__tela") as HTMLElement
    fireEvent.keyDown(tela, { key: "Home" })
    fireEvent.pointerLeave(tela, { pointerType: "touch" })
    expect(cielo().querySelector(".as-volta__lettore")).not.toBeNull()
  })

  it("le barrette di una carta sono il piano che il foglio veste", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    expect(within(carta(/^Vento$/)).getByRole("slider").hasAttribute("data-meteo-carta-piano")).toBe(true)
  })

  it("un'ora senza valore dice \"non fornito\" senza l'unita' accanto", async () => {
    conNotti(NOTTE)
    await apriMeteo()

    await scheda()
    const vento = carta(/^Vento$/)
    fireEvent.keyDown(within(vento).getByRole("slider"), { key: "Home" })
    fireEvent.keyDown(within(vento).getByRole("slider"), { key: "ArrowRight" })
    expect(vento.querySelector(".as-parametro__valore")?.textContent).toBe("non fornito")
  })
})
