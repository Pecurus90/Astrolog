// @vitest-environment jsdom
/**
 * Le parole della **Dashboard** (`src/DashboardDati.ts`): ogni ramo di cio' che `/tonight` e
 * `/weather` scrivono diventa la frase esatta della tavola v79. Le soglie dei 0,05 h sono della
 * tavola (`posaOre`): sotto non si scrive niente.
 */
import { describe, expect, it } from "vitest"

import {
  type Breve,
  type NotteMeteo,
  type Stanotte,
  bandeDellaPosa,
  cieloDellaNotte,
  esitoDellaNotte,
  latiDellaRipresa,
  nomeDellaBanda,
  orePosa,
  oreDellaNotte,
  pillolaDellaNotte,
  ripresaDellaNotte,
  ripresaDiStanotte,
  sottoDellaNotte,
} from "../src/DashboardDati"
import { STANOTTE_PIENA } from "./dashboard-banco"
import { misura } from "./meteo-banco"

const s = (campi: Record<string, unknown> = {}) =>
  ({ ...STANOTTE_PIENA, ...campi }) as unknown as Stanotte
const w = (campi: Record<string, unknown> = {}) =>
  ({ ...STANOTTE_PIENA.weather, ...campi }) as unknown as Breve
const n = (campi: Record<string, unknown> = {}) =>
  ({
    trend: false,
    dark_hours: 9,
    exposure_hours: 4,
    sky_word: "clear",
    cloud_total_pct: 12,
    measures: [],
    usable_since: null,
    usable_until: null,
    ...campi,
  }) as unknown as NotteMeteo

describe("la testa della notte", () => {
  it("la pillola: segno e parola per ogni verdetto", () => {
    expect(pillolaDellaNotte("go")).toEqual({ esito: 0, testo: "✓ notte buona" })
    expect(pillolaDellaNotte("marginal")).toEqual({ esito: 1, testo: "! notte incerta" })
    expect(pillolaDellaNotte("nogo")).toEqual({ esito: 2, testo: "✕ notte non adatta" })
  })

  it("le ore di posa: sotto 0,05 nessuna", () => {
    expect(orePosa(0.049)).toBe("Nessuna ora")
    expect(orePosa(0.05)).toBe("0,1 ore")
    expect(orePosa(4.64)).toBe("4,6 ore")
  })

  it("le bande: tutte e due, solo stretta, o niente", () => {
    const b = (
      exposure_hours: number | null,
      broadband_exposure_hours: number | null,
      narrowband_exposure_hours: number | null,
    ) => bandeDellaPosa({ exposure_hours, broadband_exposure_hours, narrowband_exposure_hours })
    expect(b(4.6, 3.1, 1.5)).toBe("3,1 in banda larga, 1,5 solo banda stretta")
    expect(b(0.1, 0.05, 0.05)).toBe("0,1 in banda larga, 0,1 solo banda stretta")
    expect(b(1.5, 0.04, 1.5)).toBe("solo banda stretta")
    expect(b(1.5, null, 1.5)).toBe("solo banda stretta")
    expect(b(0.04, 0, 0.05)).toBe("")
    expect(b(3, 3, 0.04)).toBe("")
    expect(b(null, null, null)).toBe("")
  })

  it("sotto il numero: bande, buio, trasparenza, aerosol, modelli e vento in quota", () => {
    expect(sottoDellaNotte(s(), w())).toBe(
      "3,1 in banda larga, 1,5 solo banda stretta · buio 20:48–05:48 · senza Luna 20:48–23:40 · trasparenza media 78/100 · 3 modelli d'accordo su 4 · vento a 700 hPa 15 km/h, meno vento in 2 notti su 10 dell'ultimo anno",
    )
    expect(
      sottoDellaNotte(
        s({ chart: null, moonless_dark: [] }),
        w({
          exposure_hours: 0,
          broadband_exposure_hours: 0,
          narrowband_exposure_hours: 0,
          transparency: 77.5,
          without_aerosol: true,
          verdict: "marginal",
          wind_700hpa_tenths: null,
        }),
      ),
    ).toBe(
      "trasparenza media 78/100 · senza aerosol · 1 modello d'accordo su 4 · vento a 700 hPa 15 km/h",
    )
    expect(
      sottoDellaNotte(
        s({ chart: null, moonless_dark: [] }),
        w({
          exposure_hours: 0,
          broadband_exposure_hours: 0,
          narrowband_exposure_hours: 0,
          transparency: null,
          verdict: null,
          wind_700hpa_kmh: null,
        }),
      ),
    ).toBe("")
  })
})

describe("la ripresa", () => {
  it("stanotte: larga senza Luna, stretta da capo a fine, mista se la Luna arriva", () => {
    const su = (level: string, from_start: boolean, to_end: boolean) =>
      ripresaDiStanotte(
        s({ moon_in_dark: { ...STANOTTE_PIENA.moon_in_dark, level, from_start, to_end } }),
      )?.tipo
    expect(su("go", true, true)).toBe("larga")
    expect(su("marginal", true, true)).toBe("larga")
    expect(su("nogo", true, true)).toBe("stretta")
    expect(su("nogo", false, true)).toBe("mista")
    expect(su("nogo", true, false)).toBe("mista")
    expect(ripresaDiStanotte(s({ moon_in_dark: null }))).toBeNull()
    expect(ripresaDiStanotte(s())?.testo).toBe("dopo le 23:40 consigliata banda stretta")
  })

  it("il nome della banda", () => {
    expect(nomeDellaBanda("broadband")).toBe("banda larga")
    expect(nomeDellaBanda("narrowband")).toBe("solo banda stretta")
  })

  it("le due tessere: ore e tratti di ogni banda, o nessuna ora", () => {
    expect(latiDellaRipresa(s())).toEqual([
      { tipo: "larga", nome: "banda larga", v: "2 h 52", sotto: "20:48–23:40" },
      { tipo: "stretta", nome: "solo banda stretta", v: "6 h 08", sotto: "23:40–05:48" },
    ])
    const due = s({
      shooting: [
        {
          band: "broadband",
          starts_at: "2026-09-30T20:48:00+02:00",
          ends_at: "2026-09-30T21:00:00+02:00",
          seconds: 720,
        },
        {
          band: "broadband",
          starts_at: "2026-10-01T04:00:00+02:00",
          ends_at: "2026-10-01T05:48:00+02:00",
          seconds: 6480,
        },
      ],
      broadband_dark_s: 7200,
      narrowband_dark_s: 0,
    })
    expect(latiDellaRipresa(due)).toEqual([
      { tipo: "larga", nome: "banda larga", v: "2 h", sotto: "20:48–21:00 · 04:00–05:48" },
      { tipo: "stretta", nome: "solo banda stretta", v: "nessuna ora", sotto: "nessuna ora" },
    ])
    expect(
      latiDellaRipresa(s({ shooting: null, broadband_dark_s: null, narrowband_dark_s: null }))[0]
        ?.sotto,
    ).toBe("nessuna ora")
  })

  it("le prossime notti: dalla divisione delle ore di posa", () => {
    const r = (exposure_hours: number | null, larga: number | null, stretta: number | null) =>
      ripresaDellaNotte(
        w({ exposure_hours, broadband_exposure_hours: larga, narrowband_exposure_hours: stretta }),
      )
    expect(r(8.4, 8.4, 0.04)).toEqual({ tipo: "larga", testo: "banda larga tutta la notte" })
    expect(r(2, 0.04, 2)).toEqual({ tipo: "stretta", testo: "solo banda stretta" })
    expect(r(4, 2.5, 1.5)).toEqual({ tipo: "mista", testo: "2,5 in banda larga, 1,5 stretta" })
    expect(r(0.05, 0.05, 0.05)?.tipo).toBe("mista")
    expect(r(0.04, 0.04, 0)).toBeNull()
    expect(r(null, 1, 1)).toBeNull()
    expect(r(4, null, 1)).toBeNull()
    expect(r(4, 1, null)).toBeNull()
  })
})

describe("le prossime notti in parole", () => {
  it("l'esito: la parola del verdetto, o senza meteo", () => {
    expect(esitoDellaNotte(w({ verdict: "go" }))).toEqual({ esito: 0, testo: "buona" })
    expect(esitoDellaNotte(w({ verdict: "marginal" }))).toEqual({ esito: 1, testo: "incerta" })
    expect(esitoDellaNotte(w({ verdict: "nogo" }))).toEqual({ esito: 2, testo: "non adatta" })
    expect(esitoDellaNotte(w({ verdict: null }))).toEqual({
      esito: "mancante",
      testo: "senza meteo",
    })
  })

  it("le ore: tendenza, nessuna, o le ore col tratto", () => {
    expect(oreDellaNotte(n({ trend: true, dark_hours: 9 }))).toBe("9 ore di buio · tendenza")
    expect(oreDellaNotte(n({ exposure_hours: 0.04 }))).toBe("nessuna ora di posa")
    expect(oreDellaNotte(n({ exposure_hours: null }))).toBe("nessuna ora di posa")
    expect(oreDellaNotte(n({ exposure_hours: 0.05 }))).toBe("0,1 ore di posa")
    expect(
      oreDellaNotte(
        n({
          exposure_hours: 8.4,
          usable_since: "2026-10-02T21:00:00+02:00",
          usable_until: "2026-10-03T06:00:00+02:00",
        }),
      ),
    ).toBe("8,4 ore di posa · 21–06")
    expect(
      oreDellaNotte(n({ exposure_hours: 8.4, usable_since: "2026-10-02T21:00:00+02:00" })),
    ).toBe("8,4 ore di posa")
  })

  it("il cielo: la parola, la copertura e la pioggia che arriva", () => {
    expect(cieloDellaNotte(n({ sky_word: null }))).toBe("Nuvole non disponibili")
    expect(cieloDellaNotte(n({ sky_word: "overcast", cloud_total_pct: 95.6 }))).toBe(
      "Coperto · 96%",
    )
    expect(cieloDellaNotte(n({ cloud_total_pct: null }))).toBe("Sereno")
    expect(
      cieloDellaNotte(
        n({
          sky_word: "overcast",
          cloud_total_pct: 96,
          measures: [
            misura("rain", { level: "marginal", since: "2026-10-01T20:00:00+02:00" }),
            misura("rain", { level: "nogo", since: "2026-10-01T23:00:00+02:00" }),
          ],
        }),
      ),
    ).toBe("Coperto · 96%, pioggia dalle 23")
    expect(
      cieloDellaNotte(
        n({ measures: [misura("wind", { level: "nogo", since: "2026-10-01T23:00:00+02:00" })] }),
      ),
    ).toBe("Sereno · 12%")
  })
})
