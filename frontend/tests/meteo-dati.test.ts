// @vitest-environment jsdom
/**
 * Le parole del **Meteo** (`src/MeteoDati.ts`, tavola v82): ogni ramo di cio' che `/weather`
 * scrive diventa la frase esatta della carta, della fila o della testa. La pagina le mostra; qui
 * si prova che la frase scelta e' quella giusta, caso per caso.
 */
import { describe, expect, it } from "vitest"

import {
  type Meteo,
  type Misura,
  type Notte,
  type Ora,
  type Scala,
  ALTRE,
  CARTE,
  arrivo,
  avvisoDellaPagina,
  buioDellaNotte,
  conUnita,
  giornoDellaNotte,
  giudizioDi,
  intervalli,
  livelloDellOra,
  lunaDellaNotte,
  nelBuio,
  nomeDellaNotte,
  parola,
  picco,
  protagonista,
  quandoDellaMisura,
  quota,
  rigaDelServizio,
  senzaPrevisione,
  sotto,
  tessera,
  tondo,
} from "../src/MeteoDati"
import { GIUDIZI, NOTTE, TENDENZA, banda, misura, ora } from "./meteo-banco"

const notte = (campi: Record<string, unknown> = {}) => ({ ...NOTTE, ...campi }) as unknown as Notte
const m = (code: string, campi: Record<string, unknown> = {}) =>
  misura(code, campi) as unknown as Misura
const h = (at: string, sky: string, campi: Record<string, unknown> = {}) =>
  ora(at, sky, campi) as unknown as Ora
const scala = (...bound: number[]) =>
  ({
    code: "wind",
    steps: bound.map((b) => ({ level: "nogo", bound: b, strict: false })),
  }) as unknown as Scala
const meteo = (campi: Record<string, unknown> = {}) =>
  ({
    site: "Casa",
    missing: null,
    fetched_at: "2026-09-25T15:00:00.000Z",
    last_request: null,
    sources: [],
    nights: [NOTTE],
    ...campi,
  }) as unknown as Meteo
const T = (ore: string) => `2026-09-26T${ore}:00+02:00`

describe("quota: dove sta un valore sulla scala del backend", () => {
  it("lineare fra fondo e cima, anche fuori", () => {
    const s = { axis_min: 10, axis_max: 30, axis_curve: "linear" } as const
    expect(quota(s, 15)).toBe(0.25)
    expect(quota(s, 40)).toBe(1.5)
  })
  it("senza scala: da 0 a 1", () => {
    expect(quota(undefined, 0.4)).toBe(0.4)
  })
  it("fondo e cima uguali non dividono per zero", () => {
    expect(quota({ axis_min: 5, axis_max: 5, axis_curve: "linear" }, 7)).toBe(2)
  })
  it("con la radice, tagliata fra 0 e 1", () => {
    const s = { axis_min: 0, axis_max: 100, axis_curve: "sqrt" } as const
    expect(quota(s, 25)).toBe(0.5)
    expect(quota(s, 400)).toBe(1)
    expect(quota(s, -50)).toBe(0)
  })
})

describe("parola, tondo, conUnita", () => {
  it("Luna e aerosol hanno parole loro, le altre quelle del verdetto", () => {
    expect(parola("moon", "nogo")).toBe("consigliata banda stretta")
    expect(parola("aerosol", "go")).toBe("limpido")
    expect(parola("cloud", "marginal")).toBe("incerta")
  })
  it("la visibilita' da 10 km si dice intera, sotto no; le altre mai", () => {
    expect(tondo("visibility", 12.6)).toBe(13)
    expect(tondo("visibility", 10)).toBe(10)
    expect(tondo("visibility", 9.6)).toBe(9.6)
    expect(tondo("wind", 12.6)).toBe(12.6)
  })
  it("il valore con l'unita' della sua carta, o la parola che manca", () => {
    expect(conUnita("cloud", 40)).toBe("40%")
    expect(conUnita("wind", 12)).toBe("12 km/h")
    expect(conUnita("visibility", 12.6)).toBe("13 km")
    expect(conUnita("seeing", 1.5)).toBe("1,5 ″")
    expect(conUnita("dust", 3)).toBe("3 µg/m³")
    expect(conUnita("aerosol", 0.12)).toBe("0,12")
    expect(conUnita("wind", null)).toBe("Non disponibile")
  })
  it("le carte stanno sempre al loro posto", () => {
    expect(CARTE).toEqual([
      "cloud",
      "cloud_low",
      "condensation",
      "rain",
      "visibility",
      "wind",
      "seeing",
      "jet",
      "aerosol",
    ])
    expect(ALTRE).toEqual(["temperature", "dust", "wind_700"])
  })
})

describe("sotto: la riga sotto il valore", () => {
  it("ogni carta dice cosa vuol dire il suo numero", () => {
    const n = notte()
    const righe = Object.fromEntries(
      [
        "cloud",
        "cloud_low",
        "rain",
        "wind",
        "condensation",
        "seeing",
        "jet",
        "aerosol",
        "visibility",
        "dust",
        "gust",
      ].map((c) => [c, sotto(m(c), n)]),
    )
    expect(righe).toEqual({
      cloud: "media nel buio",
      cloud_low: "media nel buio",
      rain: "totale nel buio",
      wind: "media nel buio · a 10 m",
      condensation: "minimo di temperatura meno punto di rugiada",
      seeing: "media nel buio · Meteoblue",
      jet: "media nel buio · a 250 hPa",
      aerosol: "media nel buio · spessore ottico",
      visibility: "minima nel buio",
      dust: "media nel buio",
      gust: "",
    })
  })
  it("il seeing dato solo per una parte del buio dice fino a quando", () => {
    const n = notte({ window_hours: 8 })
    expect(sotto(m("seeing", { known_until: T("23:00"), known_hours: 2 }), n)).toBe(
      "media fino alle 23:00 · Meteoblue",
    )
    expect(sotto(m("seeing", { known_until: T("23:00"), known_hours: 8 }), n)).toBe(
      "media nel buio · Meteoblue",
    )
    expect(sotto(m("seeing", { known_until: null, known_hours: 2 }), n)).toBe(
      "media nel buio · Meteoblue",
    )
    expect(
      sotto(
        m("seeing", { known_until: T("23:00"), known_hours: 2 }),
        notte({ window_hours: null }),
      ),
    ).toBe("media nel buio · Meteoblue")
  })
  // without dew point the line reads "Non disponibile °C": Issue #107, not frozen here
  it("la temperatura porta il punto di rugiada", () => {
    expect(sotto(m("temperature"), notte())).toBe("minima nel buio · punto di rugiada 4 °C")
  })
  it("il vento a 700 hPa si confronta con l'anno del sito", () => {
    const w = (d: number | null) => sotto(m("wind_700"), notte({ wind_700hpa_tenths: d }))
    expect(w(null)).toBe("confronto con lo storico non ancora disponibile")
    expect(w(0)).toBe("fra i più deboli dell'anno in questo sito")
    expect(w(10)).toBe("fra i più forti dell'anno in questo sito")
    expect(w(8)).toBe("meno vento in 8 notti su 10 dell'ultimo anno, in questo sito")
  })
})

describe("picco: il picco con le sue ore, o cio' che la carta dice al suo posto", () => {
  const n = notte()
  const conPicco = { peak: 80, peak_at: T("22:00"), peak_until: T("23:00") }
  it("nessuna ora data: nessun fatto inventato", () => {
    expect(picco(m("rain", { known_hours: 0 }), n, undefined)).toBe("")
    expect(picco(m("cloud", { ...conPicco, known_hours: 0 }), n, undefined)).toBe("")
  })
  it("il vento dice le raffiche, se ci sono tutte", () => {
    expect(picco(m("wind"), n, undefined)).toBe("raffiche fino a 35 km/h tra le 22:00 e le 23:00")
    const raffica = (campi: Record<string, unknown>) =>
      picco(m("wind"), notte({ measures: [m("gust", { ...conPicco, ...campi })] }), undefined)
    expect(raffica({})).toBe("raffiche fino a 80 km/h tra le 22:00 e le 23:00")
    expect(raffica({ peak: null })).toBe("")
    expect(raffica({ peak_at: null })).toBe("")
    expect(raffica({ peak_until: null })).toBe("")
    expect(picco(m("wind", conPicco), notte({ measures: [] }), undefined)).toBe("")
  })
  it("la condensa dice da quando si scende sotto la soglia, o che non succede", () => {
    const tratto = { level: "marginal", since: T("21:00"), until: T("23:00"), hours: 2 }
    expect(picco(m("condensation", { spans: [tratto] }), n, scala(3))).toBe(
      "sotto 3 °C dalle 21:00",
    )
    expect(picco(m("condensation"), n, scala(3, 1))).toBe("mai sotto 3 °C")
    expect(picco(m("condensation"), n, undefined)).toBe("mai sotto 0 °C")
  })
  it("la pioggia senza picco: nessuna ora con pioggia; con picco, il picco", () => {
    expect(picco(m("rain", { peak: 0 }), n, undefined)).toBe("nessuna ora con pioggia")
    expect(picco(m("rain", { ...conPicco, peak: 0.4 }), n, undefined)).toBe(
      "picco 0,4 mm tra le 22:00 e le 23:00",
    )
  })
  it("la visibilita' dice da quando c'e' nebbia, o che non ce n'e'", () => {
    const nebbia = { level: "nogo", since: T("22:00"), until: T("23:00"), hours: 1 }
    const foschia = { level: "marginal", since: T("21:00"), until: T("22:00"), hours: 1 }
    expect(picco(m("visibility", { spans: [foschia, nebbia] }), n, undefined)).toBe(
      "nebbia dalle 22:00",
    )
    expect(picco(m("visibility", { spans: [foschia] }), n, undefined)).toBe("nessuna ora di nebbia")
  })
  it("le altre il picco, se ha valore e ore", () => {
    expect(picco(m("cloud", conPicco), n, undefined)).toBe("picco 80% tra le 22:00 e le 23:00")
    expect(picco(m("cloud", { ...conPicco, peak: null }), n, undefined)).toBe("")
    expect(picco(m("cloud", { ...conPicco, peak_at: null }), n, undefined)).toBe("")
    expect(picco(m("cloud", { ...conPicco, peak_until: null }), n, undefined)).toBe("")
  })
  it("il seeing dato solo in parte dice da quando manca", () => {
    const s = { ...conPicco, peak: 2, known_until: T("23:00") }
    expect(
      picco(m("seeing", { ...s, known_hours: 2 }), notte({ window_hours: 8 }), undefined),
    ).toBe("picco 2 ″ tra le 22:00 e le 23:00 · dalle 23:00 non disponibile")
    expect(
      picco(m("seeing", { ...s, known_hours: 8 }), notte({ window_hours: 8 }), undefined),
    ).toBe("picco 2 ″ tra le 22:00 e le 23:00")
    expect(
      picco(m("seeing", { ...s, known_hours: 2 }), notte({ window_hours: null }), undefined),
    ).toBe("picco 2 ″ tra le 22:00 e le 23:00")
    expect(picco(m("cloud", { ...s, known_hours: 2 }), notte({ window_hours: 8 }), undefined)).toBe(
      "picco 2% tra le 22:00 e le 23:00",
    )
  })
})

describe("nelBuio, intervalli, quandoDellaMisura", () => {
  it("l'ora giudicata dipende dalla finestra della notte", () => {
    const cieli = ["day", "civil", "nautical", "astronomical", "dark"]
    const dentro = (w: string | null) =>
      cieli.filter((c) => nelBuio(h(T("22:00"), c), notte({ window: w })))
    expect(dentro("dark")).toEqual(["dark"])
    expect(dentro("nautical")).toEqual(["astronomical", "dark"])
    expect(dentro("sun_down")).toEqual(["civil", "nautical", "astronomical", "dark"])
    expect(dentro(null)).toEqual([])
  })
  it("i tratti uniti, le ore contate; tutta la notte quando coprono la finestra", () => {
    const a = { since: T("21:00"), until: T("22:00"), hours: 1 }
    const b = { since: T("23:00"), until: T("01:00"), hours: 2 }
    const n = notte({ window_hours: 8 })
    expect(intervalli([], n)).toBe("")
    expect(intervalli([a], n)).toBe("dalle 21:00 alle 22:00, 1 ora")
    expect(intervalli([a, b], n)).toBe("dalle 21:00 alle 22:00 e dalle 23:00 alle 01:00, 3 ore")
    expect(intervalli([a, b], notte({ window_hours: 3 }))).toBe("tutta la notte")
    expect(intervalli([a, b], notte({ window_hours: 4 }))).toBe(
      "dalle 21:00 alle 22:00 e dalle 23:00 alle 01:00, 3 ore",
    )
    expect(intervalli([a, b], notte({ window_hours: null }))).toBe(
      "dalle 21:00 alle 22:00 e dalle 23:00 alle 01:00, 3 ore",
    )
  })
  it("le ore che portano la parola della misura", () => {
    const n = notte({ window_hours: 8 })
    const vento = NOTTE.measures.find((x) => x.code === "wind") as unknown as Misura
    expect(quandoDellaMisura(vento, n)).toBe("dalle 21:00 alle 23:00, 2 ore")
    expect(quandoDellaMisura(m("cloud"), n)).toBe("")
    const senzaTratti = { level: "go", since: T("21:00"), until: T("22:00"), hours: 1 }
    expect(quandoDellaMisura(m("cloud", senzaTratti), n)).toBe("dalle 21:00 alle 22:00, 1 ora")
    expect(quandoDellaMisura(m("cloud", { ...senzaTratti, since: null }), n)).toBe("tutta la notte")
    expect(quandoDellaMisura(m("cloud", { ...senzaTratti, until: null }), n)).toBe("tutta la notte")
  })
})

describe("giudizioDi: la pillola di una misura", () => {
  it("la parola del backend", () => {
    expect(giudizioDi(m("wind", { level: "nogo" }), undefined)).toEqual({
      esito: 2,
      parola: "non adatta",
    })
  })
  it("senza parola: fra i capi della scala, ordinati", () => {
    expect(giudizioDi(m("wind", { value: 10 }), scala(29, 20))).toEqual({
      esito: "neutra",
      parola: "fra 20 e 29",
    })
  })
  it("senza valore o senza una scala con due capi: non disponibile", () => {
    const manca = { esito: "mancante", parola: "non disponibile" }
    expect(giudizioDi(m("wind", { value: null }), scala(29, 20))).toEqual(manca)
    expect(giudizioDi(m("wind", { value: 10 }), undefined)).toEqual(manca)
    expect(giudizioDi(m("wind", { value: 10 }), scala(20))).toEqual(manca)
    expect(giudizioDi(m("wind", { value: 10 }), scala(20, 20))).toEqual(manca)
  })
})

describe("il nome della notte", () => {
  it("stanotte, tendenza, o solo il giorno", () => {
    expect(nomeDellaNotte(notte(), true)).toBe("Notte di sabato 26 · stanotte")
    expect(nomeDellaNotte(notte(), false)).toBe("Notte di sabato 26")
    expect(nomeDellaNotte(notte({ trend: true }), false)).toBe("Notte di sabato 26 · tendenza")
    expect(giornoDellaNotte(notte(), true)).toBe("stanotte")
    expect(giornoDellaNotte(notte(), false)).toBe("sabato 26")
  })
})

describe("protagonista: il numero grande della notte", () => {
  it("una notte giudicata: le Ore di posa con le bande e l'accordo", () => {
    expect(protagonista(notte(), true)).toEqual({
      top: "Ore di posa · notte di sabato 26 · stanotte",
      valore: "3,0 ore",
      pillola: { esito: 1, testo: "incerta" },
      ripresa: null,
      sotto: "tutte in banda larga · 3 modelli d'accordo su 4",
      grande: true,
      grafico: true,
    })
  })
  it("niente posa, senza aerosol, finestra nautica", () => {
    const p = protagonista(
      notte({
        window: "nautical",
        exposure_hours: 0.04,
        broadband_exposure_hours: 0,
        without_aerosol: true,
        verdict: "go",
        agreement: { go: 1, marginal: 0, nogo: 0, unknown: 0, total: 4 },
      }),
      false,
    )
    expect(p.top).toBe("Ore di posa nel buio nautico · notte di sabato 26")
    expect(p.sotto).toBe("nessuna ora di posa nel buio · 1 modello d'accordo su 4 · senza aerosol")
  })
  it("posa sulla soglia dei 0,05 ore", () => {
    const p = protagonista(notte({ exposure_hours: 0.05, broadband_exposure_hours: 0 }), false)
    expect(p.sotto).toBe("tutte in banda larga · 3 modelli d'accordo su 4")
    expect(
      protagonista(notte({ exposure_hours: null, broadband_exposure_hours: 0 }), false).sotto,
    ).toBe("nessuna ora di posa nel buio · 3 modelli d'accordo su 4")
  })
  it("senza buio", () => {
    expect(protagonista(notte({ window: null }), false)).toEqual({
      top: "Notte di sabato 26",
      valore: "Nessun buio",
      pillola: null,
      ripresa: null,
      sotto: "Il Sole non tramonta: nessuna ora di buio.",
      grande: false,
      grafico: false,
    })
  })
  it("senza verdetto", () => {
    expect(protagonista(notte({ verdict: null }), false)).toEqual({
      top: "Notte di sabato 26",
      valore: "Non disponibile",
      pillola: null,
      ripresa: null,
      sotto: "Non valutabile: copertura nuvolosa incompleta per le ore di buio.",
      grande: false,
      grafico: true,
    })
  })
  it("una tendenza: il buio, il cielo e l'accordo dei senza parola", () => {
    const n = { ...TENDENZA, dark_hours: 9.6, cloud_total_pct: 32.6 } as unknown as Notte
    expect(protagonista(n, false)).toEqual({
      top: "Buio · notte di martedì 29 · tendenza",
      valore: "10 ore",
      pillola: { esito: 0, testo: "buona" },
      ripresa: null,
      sotto:
        "Nuvole sparse nel buio, 33% · 2 modelli d'accordo su 4. Dalla quarta notte la previsione è una tendenza, meno affidabile e senza dettaglio orario.",
      grande: true,
      grafico: true,
    })
    // without clouds the line reads "Non disponibile nel buio, %": Issue #107, not frozen here
    const senza = { ...n, verdict: null } as unknown as Notte
    expect(protagonista(senza, false).pillola).toBeNull()
    expect(protagonista(senza, false).sotto).toContain("0 modelli d'accordo su 4")
  })
})

describe("lunaDellaNotte: la Luna per la banda larga", () => {
  const luna = (campi: Record<string, unknown>) =>
    lunaDellaNotte(
      notte({
        measures: [
          m("moon", {
            level: "nogo",
            value: 61.6,
            known_hours: 3,
            known_since: T("21:00"),
            known_until: T("23:40"),
            ...campi,
          }),
        ],
      }),
    )
  it("senza giudizio, senza ore o senza capi: niente", () => {
    expect(lunaDellaNotte(notte({ measures: [] }))).toBeNull()
    expect(luna({ level: null })).toBeNull()
    expect(luna({ known_hours: 0 })).toBeNull()
    expect(luna({ known_since: null })).toBeNull()
    expect(luna({ known_until: null })).toBeNull()
  })
  it("tutta la notte: banda stretta", () => {
    expect(luna({ known_from_start: true, known_to_end: true })).toEqual({
      tipo: "stretta",
      testo: "Luna al 62% tutta la notte",
      breve: "Luna al 62%",
    })
  })
  it("dall'inizio: banda larga dopo", () => {
    expect(luna({ known_from_start: true })).toEqual({
      tipo: "mista",
      testo: "Luna al 62% fino alle 23:40 · banda larga dalle 23:40",
      breve: "banda larga dalle 23",
    })
  })
  it("fino alla fine: banda larga prima", () => {
    expect(luna({ known_to_end: true })).toEqual({
      tipo: "mista",
      testo: "Luna al 62% dalle 21:00 · banda larga fino alle 21:00",
      breve: "banda larga fino alle 21",
    })
  })
  it("in mezzo: banda larga prima e dopo", () => {
    expect(luna({})).toEqual({
      tipo: "mista",
      testo: "Luna al 62% dalle 21:00 alle 23:40 · banda larga fino alle 21:00 e dalle 23:40",
      breve: "banda larga fino alle 21 e dalle 23",
    })
  })
  it("Luna al limite: banda larga, e senza Luna fuori dalle sue ore", () => {
    expect(luna({ level: "marginal", known_from_start: true })).toEqual({
      tipo: "larga",
      testo: "Luna al 62% fino alle 23:40 · senza Luna dalle 23:40",
      breve: "Luna al 62%",
    })
  })
  it("Luna buona: la sola Luna, senza il resto", () => {
    expect(luna({ level: "go", value: null })).toEqual({
      tipo: "larga",
      testo: "Luna al 0% dalle 21:00 alle 23:40",
      breve: "Luna al 0%",
    })
  })
  it("la ripresa del protagonista e della fila vengono dalla Luna", () => {
    const n = notte({
      measures: [
        m("moon", {
          level: "nogo",
          value: 50,
          known_hours: 3,
          known_since: T("21:00"),
          known_until: T("23:40"),
          known_from_start: true,
          known_to_end: true,
        }),
      ],
    })
    expect(protagonista(n, false).ripresa).toEqual({
      tipo: "stretta",
      testo: "Luna al 50% tutta la notte",
    })
    expect(tessera(n, false, false, () => {}).rip).toEqual({
      tipo: "stretta",
      testo: "Luna al 50%",
    })
  })
})

describe("tessera: una notte nella fila", () => {
  const on = () => {}
  it("una notte giudicata", () => {
    const t = tessera(notte(), true, true, on)
    expect(t).toMatchObject({
      day: "sab 26",
      tag: "stanotte",
      tagS: "stanotte",
      tend: false,
      sel: true,
      esito: 1,
      hours: "3,0 ore",
      range: "23–02",
      on,
    })
    expect(t).not.toHaveProperty("pillT")
    expect(t).not.toHaveProperty("rip")
    expect(t.cells).toEqual([
      { h: 20, esito: null },
      { h: 20, esito: 0 },
      { h: 20, esito: 0 },
    ])
  })
  it("le celle: l'altezza dalle nubi, il colore solo nel buio giudicato", () => {
    const n = notte({
      hours: [
        h(T("20:00"), "dark", { cloud_total_pct: 50 }),
        h(T("21:00"), "dark", { cloud_total_pct: null }),
        h(T("22:00"), "dark", { cloud_total_pct: 10, levels: { ...GIUDIZI, cloud: null } }),
        h(T("23:00"), "dark", { cloud_total_pct: 10, levels: { ...GIUDIZI, cloud: "nogo" } }),
        h(T("23:00"), "nautical", { cloud_total_pct: 10, levels: { ...GIUDIZI, cloud: "nogo" } }),
      ],
    })
    expect(tessera(n, false, false, on).cells).toEqual([
      { h: 60, esito: 0 },
      { h: 100, esito: null },
      { h: 28, esito: null },
      { h: 28, esito: 2 },
      { h: 28, esito: null },
    ])
    expect(tessera(notte({ measures: [] }), false, false, on).cells).toEqual([])
  })
  it("le ore: posa, nessuna ora, o non so", () => {
    expect(tessera(notte({ exposure_hours: 0.04 }), false, false, on).hours).toBe("nessuna ora")
    expect(tessera(notte({ exposure_hours: 0.05 }), false, false, on).hours).toBe("0,1 ore")
    expect(tessera(notte({ exposure_hours: null }), false, false, on).hours).toBe("nessuna ora")
    const ignota = tessera(notte({ verdict: null }), false, false, on)
    expect(ignota).toMatchObject({
      hours: "?",
      esito: "mancante",
      pillT: "non disponibile",
      tag: "",
      tagS: "",
    })
  })
  it("la finestra: due bande, l'intervallo usabile, o la parola del cielo", () => {
    const r = (campi: Record<string, unknown>) => tessera(notte(campi), false, false, on).range
    expect(r({ broadband_exposure_hours: 2.04, narrowband_exposure_hours: 1.5 })).toBe(
      "2,0 larga · 1,5 stretta",
    )
    expect(r({ broadband_exposure_hours: 0.05, narrowband_exposure_hours: 0.05 })).toBe(
      "0,1 larga · 0,1 stretta",
    )
    expect(r({ broadband_exposure_hours: 0.04, narrowband_exposure_hours: 1 })).toBe("23–02")
    expect(r({ broadband_exposure_hours: 1, narrowband_exposure_hours: 0.04 })).toBe("23–02")
    expect(r({ broadband_exposure_hours: null, narrowband_exposure_hours: null })).toBe("23–02")
    expect(r({ usable_since: null, sky_word: "broken" })).toBe("nuvoloso")
    expect(r({ usable_until: null, sky_word: "broken" })).toBe("nuvoloso")
    expect(r({ usable_until: null, sky_word: null })).toBe("")
  })
  it("una tendenza: il buio e il cielo", () => {
    const n = { ...TENDENZA, dark_hours: 9.6, cloud_total_pct: 32.6 } as unknown as Notte
    expect(tessera(n, false, false, on)).toMatchObject({
      tag: "",
      tagS: "tendenza",
      tend: true,
      esito: 0,
      hours: "10 ore di buio",
      range: "Nuvole sparse · 33%",
      cells: [],
    })
    const senza = { ...n, sky_word: null } as unknown as Notte
    expect(tessera(senza, false, false, on).range).toBe("")
    const senzaPct = { ...n, cloud_total_pct: null } as unknown as Notte
    expect(tessera(senzaPct, false, false, on).range).toBe("Nuvole sparse · 0%")
  })
})

describe("la testa: arrivo, avviso, riga del servizio", () => {
  it("senza previsione: niente", () => {
    expect(arrivo(meteo({ fetched_at: null }))).toEqual({ lungo: "", corto: "" })
  })
  it("Open-Meteo, poi Meteoblue se c'e', e l'ora del sito", () => {
    const solo = arrivo(
      meteo({ sources: [{ source: "cams", fetched_at: "2026-09-25T15:00:00.000Z" }] }),
    )
    expect(solo.lungo).toMatch(/^Previsione Open-Meteo del .+ · ora locale del sito$/)
    expect(solo.lungo).not.toContain("Meteoblue")
    expect(solo.corto).toMatch(/^Open-Meteo [^·]+$/)
    const due = arrivo(
      meteo({ sources: [{ source: "meteoblue", fetched_at: "2026-09-25T03:00:00.000Z" }] }),
    )
    expect(due.lungo).toMatch(
      /^Previsione Open-Meteo del .+ · Seeing Meteoblue del .+ · ora locale del sito$/,
    )
    expect(due.corto).toMatch(/^Open-Meteo .+ · Meteoblue .+$/)
  })
  it("senza previsione valida", () => {
    expect(senzaPrevisione(meteo({ fetched_at: null }))).toBe(true)
    expect(senzaPrevisione(meteo({ nights: [] }))).toBe(true)
    expect(senzaPrevisione(meteo())).toBe(false)
  })
  it("l'avviso di pagina, uno per stato", () => {
    expect(avvisoDellaPagina(meteo())).toBeNull()
    expect(avvisoDellaPagina(meteo({ site: null }))).toEqual({
      segno: "?",
      titolo: "Sito predefinito mancante",
      testo: "La previsione richiede un sito predefinito.",
      azione: { l: "Aggiungi sito", a: "/impostazioni/siti" },
    })
    expect(avvisoDellaPagina(meteo({ missing: "no_timezone" }))).toEqual({
      segno: "!",
      titolo: "Fuso orario del sito non riconosciuto: le notti non si possono calcolare.",
      azione: { l: "Modifica sito", a: "/impostazioni/siti" },
    })
    const tace = { status: "unreachable", at: "2026-09-25T15:00:00.000Z" }
    const muto = avvisoDellaPagina(meteo({ last_request: tace, nights: [] }))
    expect(muto).toMatchObject({
      segno: "!",
      testo: "Le notti dell'ultima previsione sono passate tutte.",
      azione: { l: "Aggiorna", aggiorna: true },
    })
    expect(muto?.titolo).toMatch(
      /^Aggiornamento delle .+ non riuscito\. Nessuna previsione disponibile\.$/,
    )
    expect(
      avvisoDellaPagina(meteo({ last_request: tace, fetched_at: null }))?.testo,
    ).toBeUndefined()
    expect(avvisoDellaPagina(meteo({ last_request: tace }))).toBeNull()
    expect(
      avvisoDellaPagina(meteo({ last_request: { ...tace, status: "ok" }, nights: [] })),
    ).toEqual({
      segno: "?",
      titolo: "Nessuna notte disponibile per questo modello.",
      testo: "Gli altri modelli si scelgono qui sopra.",
    })
    expect(avvisoDellaPagina(meteo({ fetched_at: null }))).toEqual({
      segno: "?",
      titolo: "Nessuna previsione disponibile.",
      testo: "La previsione si aggiorna ogni tre ore.",
    })
  })
  it("la riga del servizio: solo se tace e la previsione regge", () => {
    const tace = { status: "bad_answer", at: "2026-09-25T15:00:00.000Z" }
    expect(rigaDelServizio(meteo({ last_request: tace }))).toMatch(
      /^Risposta non valida dal servizio alle .+\. Previsione delle .+\.$/,
    )
    expect(rigaDelServizio(meteo())).toBeNull()
    expect(rigaDelServizio(meteo({ last_request: { ...tace, status: "ok" } }))).toBeNull()
    expect(rigaDelServizio(meteo({ last_request: tace, nights: [] }))).toBeNull()
    expect(rigaDelServizio(meteo({ last_request: tace, fetched_at: null }))).toBeNull()
  })
})

describe("buioDellaNotte: i capi della finestra giudicata", () => {
  const fasce = [
    banda("day", T("19:00"), T("19:20")),
    banda("civil", T("19:20"), T("19:50")),
    banda("nautical", T("19:50"), T("20:25")),
    banda("astronomical", T("20:25"), T("21:00")),
    banda("dark", T("21:00"), T("23:00")),
    banda("astronomical", T("23:00"), T("23:30")),
    banda("day", T("23:30"), T("23:59")),
  ]
  it("dal buio, dal nautico o dal Sole sotto l'orizzonte", () => {
    const b = (w: string | null, s: unknown = fasce) =>
      buioDellaNotte(notte({ window: w, sky_bands: s }))
    expect(b("dark")).toBe("21:00–23:00")
    expect(b("nautical")).toBe("20:25–23:30")
    expect(b("sun_down")).toBe("19:20–23:30")
    expect(b("dark", [])).toBeNull()
    expect(b("dark", null)).toBeNull()
    expect(b("dark", [banda("day", T("19:00"), T("23:00"))])).toBeNull()
  })
})

describe("livelloDellOra", () => {
  it("la parola del backend, o niente dove la misura non ne ha", () => {
    const o = h(T("22:00"), "dark", { levels: { ...GIUDIZI, wind: null } })
    expect(livelloDellOra(o, "cloud")).toBe("go")
    expect(livelloDellOra(o, "wind")).toBeNull()
    expect(livelloDellOra(o, "temperature")).toBeNull()
  })
})
