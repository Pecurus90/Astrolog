/**
 * Le Notti in parole (`src/NottiDati.ts`): ogni ramo di cio' che l'API manda diventa il testo
 * esatto della tavola v76. Si formatta e basta, ma ogni ramo sbagliato e' una parola sbagliata.
 */
import { describe, expect, it } from "vitest"

import { t } from "../src/i18n"
import {
  type Notte,
  cielo,
  esitoDi,
  filtri,
  fonteDelSito,
  giornoBreve,
  luna,
  numeri,
  oggetti,
  oggettiInFila,
  oreDi,
  parolaDi,
  ripresa,
  segnoDi,
  sommaDelMese,
  titoloDi,
} from "../src/NottiDati"

type Meteo = Notte["weather"]

const METEO: Meteo = {
  state: "ok",
  arrives_on: null,
  verdict: "go",
  cloud_total_pct: 8.4,
  usable_hours: 7,
  window: "dark",
  window_hours: 9,
  transparency: 88,
  exposure_hours: 7.9,
  dark_hours: 9.4,
  without_aerosol: false,
  sky_word: "scattered",
}

const NOTTE: Notte = {
  id: 7,
  night_date: "2026-09-30",
  site: "Cima Ekar",
  site_source: "detected",
  site_from: "frames",
  shooting: null,
  frames: 3,
  integration_s: 10800,
  untimed: 0,
  objects: [],
  filters: [],
  moon: null,
  weather: METEO,
}

const conMeteo = (m: Partial<Meteo>): Notte => ({ ...NOTTE, weather: { ...METEO, ...m } })

const oggetto = (key: string, integration_s = 3600, name: string | null = key.toUpperCase()) => ({
  key,
  name,
  frames: 1,
  integration_s,
  untimed: 0,
  bar_pct: 40,
})

const SILENZIO = {
  esito: -1,
  pillola: "senza meteo",
  titolo: "Il meteo non è ancora arrivato",
  sotto: "Il servizio del meteo non ha ancora risposto per questa notte.",
  corto: "non ancora arrivato",
  striscia: "senza meteo",
  tacche: null,
  modificaSito: false,
}

describe("esito, segno e parola", () => {
  it("ogni verdetto ha il suo esito, uno ignoto o assente e' -1", () => {
    expect(esitoDi("go")).toBe(0)
    expect(esitoDi("marginal")).toBe(1)
    expect(esitoDi("nogo")).toBe(2)
    expect(esitoDi("strano")).toBe(-1)
    expect(esitoDi(null)).toBe(-1)
    expect(esitoDi(undefined)).toBe(-1)
    expect(esitoDi("")).toBe(-1)
  })

  it("ogni esito ha il suo segno e la sua parola", () => {
    expect([0, 1, 2, -1].map((e) => segnoDi(e as 0 | 1 | 2 | -1))).toEqual(["✓", "!", "✕", "?"])
    expect([0, 1, 2, -1].map((e) => parolaDi(e as 0 | 1 | 2 | -1))).toEqual([
      "buona",
      "incerta",
      "non adatta",
      "senza meteo",
    ])
  })
})

describe("data e sito", () => {
  it("il titolo e' la data lunga, il giorno della striscia e' breve", () => {
    expect(titoloDi(NOTTE)).toBe("Mercoledì 30 settembre 2026")
    expect(giornoBreve(NOTTE)).toBe("mer 30")
  })

  it("il sito dice da dove viene", () => {
    expect(fonteDelSito(NOTTE)).toBe("dalle coordinate nei frame")
    expect(fonteDelSito({ ...NOTTE, site_from: "home" })).toBe(
      "il sito di casa, dalle Impostazioni",
    )
    expect(fonteDelSito({ ...NOTTE, site_from: "answer" })).toBe(
      "dalla tua risposta in Da confermare",
    )
  })

  it("zero secondi non sono ore", () => {
    expect(oreDi(0)).toBeNull()
    expect(oreDi(5400)).toBe("1 h 30")
  })
})

describe("il cielo di una notte", () => {
  it("un sito senza fuso: non disponibile, e porta a modificare il sito", () => {
    expect(cielo(conMeteo({ state: "unknown" }))).toEqual({
      esito: -1,
      pillola: "non disponibile",
      titolo: "Non disponibile",
      sotto: "Fuso orario del sito non riconosciuto.",
      corto: "sito senza fuso",
      striscia: "senza fuso",
      tacche: null,
      modificaSito: true,
    })
  })

  it("una notte giovane dice il giorno in cui il meteo arriva, anche se ha gia' un verdetto", () => {
    expect(cielo(conMeteo({ state: "waiting", arrives_on: "2026-10-05" }))).toEqual({
      esito: -1,
      pillola: "meteo in arrivo",
      titolo: "Il meteo arriva il 5 ott 2026",
      sotto: "L’archivio del meteo è definitivo dopo 5 giorni.",
      corto: "arriva il 5 ott 2026",
      striscia: "in arrivo",
      tacche: null,
      modificaSito: false,
    })
  })

  it("una notte in attesa senza giorno d'arrivo e' senza meteo", () => {
    expect(cielo(conMeteo({ state: "waiting", arrives_on: null }))).toEqual(SILENZIO)
  })

  it("un giorno d'arrivo conta solo se la notte e' in attesa", () => {
    expect(cielo(conMeteo({ verdict: null, arrives_on: "2026-10-05" }))).toEqual(SILENZIO)
    expect(cielo(conMeteo({ exposure_hours: null, arrives_on: "2026-10-05" }))).toEqual(SILENZIO)
  })

  it("senza verdetto, o senza ore di posa, e' senza meteo", () => {
    expect(cielo(conMeteo({ verdict: null }))).toEqual(SILENZIO)
    expect(cielo(conMeteo({ exposure_hours: null }))).toEqual(SILENZIO)
    const senzaPosa: Meteo = { ...METEO }
    delete senzaPosa.exposure_hours
    expect(cielo({ ...NOTTE, weather: senzaPosa })).toEqual(SILENZIO)
  })

  it("una notte buia con verdetto dice nuvole, posa su buio e le tacche", () => {
    expect(cielo(NOTTE)).toEqual({
      esito: 0,
      pillola: "buona",
      titolo: "Nuvole sparse, in media 8%",
      sotto: "7,9 ore di posa su 9 di buio",
      corto: "7,9 di posa su 9 ore",
      striscia: "buona",
      tacche: { tutte: 9, piene: 8 },
      modificaSito: false,
    })
  })

  it("senza aerosol lo dice dopo la posa, non nella riga corta", () => {
    const c = cielo(conMeteo({ verdict: "nogo", without_aerosol: true }))
    expect(c.esito).toBe(2)
    expect(c.pillola).toBe("non adatta")
    expect(c.sotto).toBe("7,9 ore di posa su 9 di buio · senza aerosol")
    expect(c.corto).toBe("7,9 di posa su 9 ore")
  })

  it("senza parola del cielo il titolo e' vuoto; senza nuvole la media e' zero", () => {
    expect(cielo(conMeteo({ sky_word: null })).titolo).toBe("")
    expect(cielo(conMeteo({ sky_word: "clear", cloud_total_pct: null })).titolo).toBe(
      "Sereno, in media 0%",
    )
  })

  it("col Sole solo sotto l'orizzonte dice le ore visibili e niente tacche", () => {
    const c = cielo(conMeteo({ verdict: "marginal", window: "sun_down", dark_hours: 2.4 }))
    expect(c).toEqual({
      esito: 1,
      pillola: "incerta",
      titolo: "Nuvole sparse, in media 8%",
      sotto: "2 ore visibili col Sole sotto l’orizzonte",
      corto: "2 ore visibili, senza buio",
      striscia: "incerta",
      tacche: null,
      modificaSito: false,
    })
    expect(cielo(conMeteo({ window: "sun_down", dark_hours: 1 })).sotto).toBe(
      "1 ora visibile col Sole sotto l’orizzonte",
    )
  })
})

describe("la ripresa e la Luna", () => {
  it("senza ripresa non c'e' riga", () => {
    expect(ripresa(NOTTE)).toBeNull()
  })

  it("le ore di banda larga, o solo banda stretta", () => {
    const larga = { kind: "broadband" as const, broadband_hours: 3.5, dark_hours: 7 }
    expect(ripresa({ ...NOTTE, shooting: larga })).toEqual({
      tipo: "larga",
      testo: "3 h 30 di banda larga",
    })
    expect(
      ripresa({ ...NOTTE, shooting: { ...larga, kind: "narrowband", broadband_hours: 0 } }),
    ).toEqual({
      tipo: "stretta",
      testo: "solo banda stretta",
    })
    expect(ripresa({ ...NOTTE, shooting: { ...larga, kind: "mixed" } })?.tipo).toBe("mista")
  })

  it("la Luna dice la fase, la luce e il lato illuminato", () => {
    const moon = {
      phase_key: "waxing_gibbous" as const,
      illumination_pct: 69,
      lit_side: "right" as const,
    }
    expect(luna(NOTTE)).toBeNull()
    expect(luna({ ...NOTTE, moon })).toEqual({
      pct: 69,
      lato: "destra",
      titolo: "Gibbosa crescente",
      testo: "illuminata al 69%",
    })
    expect(luna({ ...NOTTE, moon: { ...moon, lit_side: "left" } })?.lato).toBe("sinistra")
  })
})

describe("gli oggetti", () => {
  it("se ne nominano tre, gli altri si contano", () => {
    const n = { ...NOTTE, objects: ["a", "b", "c", "d", "e"].map((k) => oggetto(k)) }
    const { primi, altri } = oggetti(n)
    expect(primi.map((o) => o.nome)).toEqual(["A", "B", "C"])
    expect(altri).toBe("e 2 altri")
    expect(oggetti({ ...NOTTE, objects: ["a", "b", "c", "d"].map((k) => oggetto(k)) }).altri).toBe(
      "e 1 altro",
    )
  })

  it("tre oggetti o meno non portano altri", () => {
    expect(oggetti({ ...NOTTE, objects: ["a", "b", "c"].map((k) => oggetto(k)) }).altri).toBeNull()
    expect(oggetti(NOTTE)).toEqual({ primi: [], altri: null })
  })

  it("ogni oggetto dice nome, ore e larghezza della barra; senza nome la chiave, senza tempo senza durata", () => {
    const n = { ...NOTTE, objects: [oggetto("m-31", 5400, "M 31"), oggetto("ngc-7000", 0, null)] }
    expect(oggetti(n).primi).toEqual([
      { nome: "M 31", ore: "1 h 30", larghezza: "40%" },
      { nome: "ngc-7000", ore: "senza durata", larghezza: "40%" },
    ])
  })

  it("in fila i nomi si separano col punto, e gli altri si aggiungono dopo", () => {
    const quattro = { ...NOTTE, objects: ["a", "b", "c", "d"].map((k) => oggetto(k)) }
    expect(oggettiInFila(quattro)).toBe("A · B · C e 1 altro")
    expect(oggettiInFila({ ...NOTTE, objects: [oggetto("a"), oggetto("b")] })).toBe("A · B")
    expect(oggettiInFila(NOTTE)).toBe("")
  })
})

describe("i filtri", () => {
  it("frame senza filtro diventano un pezzo solo, ignoto, col tempo della notte", () => {
    expect(filtri(NOTTE)).toEqual([
      { banda: "UNKNOWN", nome: "Filtro non indicato", frame: 3, secondi: 10800, peso: 1 },
    ])
    expect(filtri({ ...NOTTE, integration_s: 0 })[0]?.secondi).toBeNull()
  })

  it("una notte senza frame non ha pezzi", () => {
    expect(filtri({ ...NOTTE, frames: 0 })).toEqual([])
  })

  it("ogni filtro pesa coi secondi, o senza tempo un minuto a frame", () => {
    const n = {
      ...NOTTE,
      filters: [
        { name: "Ha", passband: "HA", frames: 2, integration_s: 7200 },
        { name: "OIII", passband: "OIII", frames: 3, integration_s: 0 },
      ],
    }
    expect(filtri(n)).toEqual([
      { banda: "HA", nome: "Ha", frame: 2, secondi: 7200, peso: 7200 },
      { banda: "OIII", nome: "OIII", frame: 3, secondi: null, peso: 180 },
    ])
  })
})

describe("i numeri della protagonista", () => {
  it("con le ore: le ore grandi e i frame sotto", () => {
    expect(numeri(NOTTE)).toEqual({ grande: "3 h", parola: "ore", sotto: "3 frame" })
  })

  it("i frame senza durata si aggiungono sotto", () => {
    expect(numeri({ ...NOTTE, untimed: 2 }).sotto).toBe("3 frame · 2 senza durata")
  })

  it("senza ore: i frame grandi e il perche'", () => {
    expect(numeri({ ...NOTTE, integration_s: 0, frames: 1 })).toEqual({
      grande: "1 frame",
      parola: "senza durata",
      sotto: t("nights.notime"),
    })
  })
})

describe("la somma del mese", () => {
  it("nessuna notte, notti senza ore, notti con le ore", () => {
    expect(sommaDelMese(0, 3600)).toBe("nessuna notte")
    expect(sommaDelMese(1, 0)).toBe("1 notte")
    expect(sommaDelMese(2, 18600)).toBe("2 notti · 5 h 10")
  })
})
