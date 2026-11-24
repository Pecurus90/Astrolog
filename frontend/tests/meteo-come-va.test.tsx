// @vitest-environment jsdom
/**
 * La carta **Come va** del Meteo (`src/MeteoMisure.tsx`, tavola v82) disegnata da sola: perche'
 * una carta non ha il suo numero, gli altri fattori con la loro parola e le loro ore, la Luna,
 * le carte che mancano in fondo, il bottone degli altri e i fatti della notte.
 */
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import type { Sguardo } from "../src/Meteo"
import type { Accesa } from "../src/MeteoCielo"
import type { Meteo, Misura, Notte } from "../src/MeteoDati"
import { ComeVa, statoDellaCarta } from "../src/MeteoMisure"
import { NOTTE, TENDENZA, misura } from "./meteo-banco"

afterEach(cleanup)

const notte = (campi: Record<string, unknown> = {}) => ({ ...NOTTE, ...campi }) as unknown as Notte
const detto = (seeing: Record<string, unknown> = {}) =>
  ({ seeing: { key: false, source: null, meteoblue: null, ...seeing } }) as unknown as Meteo
const m = (code: string, campi: Record<string, unknown> = {}) =>
  misura(code, campi) as unknown as Misura
const T = (ore: string) => `2026-09-26T${ore}:00+02:00`

describe("statoDellaCarta: perche' una carta non ha il suo numero", () => {
  const n = notte()
  const manca = {
    stato: "non disponibile",
    parole: {
      testo:
        "Il servizio non ha mandato questa misura per la notte: torna col prossimo aggiornamento.",
    },
  }
  const stima = {
    titolo: "Seeing scarso · stima dal vento in quota",
    pillola: "scarso · stima dal vento in quota",
  }
  it("con ore date la carta e' normale, seeing compreso", () => {
    expect(statoDellaCarta(m("wind", { known_hours: 1 }), "wind", n, detto())).toEqual({
      stato: "normale",
    })
    expect(statoDellaCarta(m("seeing", { known_hours: 1 }), "seeing", n, detto())).toEqual({
      stato: "normale",
    })
  })
  it("il seeing senza chiave: la chiave, con la stima dal jet se c'e'", () => {
    const vuoto = m("seeing", { known_hours: 0 })
    expect(statoDellaCarta(vuoto, "seeing", n, detto())).toEqual({ stato: "chiave" })
    expect(statoDellaCarta(undefined, "seeing", n, detto())).toEqual({ stato: "chiave" })
    const jet = m("seeing", { known_hours: 0, estimated_from: "jet" })
    expect(statoDellaCarta(jet, "seeing", n, detto())).toEqual({
      stato: "chiave",
      parole: { ...stima, testo: "Con una chiave Meteoblue, il numero in secondi d'arco." },
    })
  })
  it("il seeing con la chiave: rifiutata, non ancora chiesto, crediti finiti, stima dal jet", () => {
    const vuoto = m("seeing", { known_hours: 0 })
    const jet = m("seeing", { known_hours: 0, estimated_from: "jet" })
    const con = (meteoblue: string | null) => detto({ key: true, meteoblue })
    expect(statoDellaCarta(vuoto, "seeing", n, con("refused"))).toEqual({
      stato: "chiave non valida",
    })
    expect(statoDellaCarta(vuoto, "seeing", n, con(null))).toEqual({ stato: "in arrivo" })
    expect(statoDellaCarta(vuoto, "seeing", n, con("limited"))).toEqual({
      stato: "non disponibile",
      parole: {
        titolo:
          "Meteoblue non risponde per ora: crediti o richieste esauriti. La chiave è buona, riprovo più tardi.",
        testo: "",
        pillola: "si riprova più tardi",
      },
    })
    expect(statoDellaCarta(jet, "seeing", n, con("ok"))).toEqual({
      stato: "non disponibile",
      parole: { ...stima, testo: "" },
    })
    expect(statoDellaCarta(vuoto, "seeing", n, con("ok"))).toEqual(manca)
  })
  it("sotto le nuvole seeing e aerosol non si misurano; le altre mancano", () => {
    const coperta = notte({ measures: [m("cloud", { level: "nogo" })] })
    const ok = detto({ key: true, meteoblue: "ok" })
    expect(statoDellaCarta(undefined, "seeing", coperta, ok)).toEqual({ stato: "non si misura" })
    expect(statoDellaCarta(undefined, "aerosol", coperta, ok)).toEqual({ stato: "non si misura" })
    expect(statoDellaCarta(undefined, "wind", coperta, ok)).toEqual(manca)
    const incerta = notte({ measures: [m("cloud", { level: "marginal" })] })
    expect(statoDellaCarta(undefined, "aerosol", incerta, ok)).toEqual(manca)
    const vento = notte({ measures: [m("wind", { level: "nogo" })] })
    expect(statoDellaCarta(undefined, "aerosol", vento, ok)).toEqual(manca)
  })
})

function disegnaComeVa(
  n: Notte,
  p: { detto?: Meteo; telefono?: boolean; prima?: boolean; accese?: Accesa[] } = {},
) {
  const sguardo = {
    ora: null,
    scegliOra: vi.fn(),
    accese: p.accese ?? [],
    accendi: vi.fn(),
    fisse: {},
    fissa: vi.fn(),
    aperta: null,
    apri: vi.fn(),
  } satisfies Sguardo
  render(
    <ComeVa
      detto={p.detto ?? detto()}
      notte={n}
      prima={p.prima ?? true}
      formato={p.telefono ? "telefono" : "largo"}
      sguardo={sguardo}
    />,
  )
  return { sguardo, carta: screen.getByRole("region", { name: "Come va" }) }
}

/** Le righe dei fattori: nome, pillola e testo. */
const righe = (c: HTMLElement) =>
  [...c.querySelectorAll<HTMLElement>(".al-meteo__riga-12")].map((r) => {
    const fila = r.parentElement as HTMLElement
    return [
      r.querySelector("b")?.textContent,
      r.querySelector(".al-pillola")?.textContent,
      fila.lastElementChild?.textContent,
    ]
  })
const pillole = (c: HTMLElement) =>
  [...c.querySelectorAll<HTMLElement>(".al-meteo__riga-12 .al-pillola")].map((p) => p.className)

// una notte con solo cio' che serve: le carte senza misura vanno in fondo
const misureDi = (...ms: Misura[]) => notte({ measures: ms })

describe("Come va: gli altri fattori", () => {
  it("il valore detto come la carta lo misura: totale, minima, media; le raffiche senza", () => {
    const n = misureDi(
      m("rain", { level: "go", value: 0.4 }),
      m("visibility", { level: "go", value: 12 }),
      m("condensation", { level: "go", value: 5 }),
      m("wind", { level: "marginal", value: 20 }),
      m("gust", { level: "go", value: 35 }),
      m("jet", { level: "go", value: null }),
    )
    const r = righe(disegnaComeVa(n).carta)
    expect(r.slice(0, 2)).toEqual([
      ["Pioggia", "✓ buona", "tutta la notte · 0,4 mm totale nel buio"],
      ["Visibilità", "✓ buona", "tutta la notte · 12 km minima nel buio"],
    ])
  })
  it("tutti i fattori, aperti col bottone: nell'ordine del backend, le carte senza numero in fondo", () => {
    const n = misureDi(
      m("cloud", { level: "nogo", value: 90 }),
      m("rain", { level: "go", value: 0.4 }),
      m("visibility", { level: "go", value: 12 }),
      m("condensation", { level: "go", value: 5 }),
      m("wind", { level: "marginal", value: 20 }),
      m("gust", { level: "go", value: 35 }),
      m("jet", { level: "go", value: null }),
      m("dust", { level: null, value: 3 }),
      m("aerosol", { level: "go", value: 0.1, estimated_from: "jet", known_hours: 0 }),
    )
    const { carta } = disegnaComeVa(n)
    const bottone = within(carta).getByRole("button", { name: /Altri 7 fattori/ })
    expect(bottone.getAttribute("aria-expanded")).toBe("false")
    expect(bottone.textContent).toContain("▾")
    fireEvent.click(bottone)
    expect(bottone.getAttribute("aria-expanded")).toBe("true")
    expect(bottone.textContent).toContain("▴")
    expect(righe(carta)).toEqual([
      ["Pioggia", "✓ buona", "tutta la notte · 0,4 mm totale nel buio"],
      ["Visibilità", "✓ buona", "tutta la notte · 12 km minima nel buio"],
      ["Condensa", "✓ buona", "tutta la notte · 5 °C minima nel buio"],
      ["Vento", "! incerta", "tutta la notte · 20 km/h media nel buio"],
      ["Raffiche", "✓ buona", "tutta la notte"],
      ["Jet stream", "✓ buona", "tutta la notte"],
      ["Nuvole basse", "? non disponibile", "Non disponibile"],
      ["Seeing", "? serve una chiave", "Il seeing richiede una chiave Meteoblue."],
      ["Aerosol", "? non si misura", "Sotto le nuvole non si misura."],
    ])
    expect(carta.textContent).toContain(
      "pesano accanto al verdetto, senza cambiarlo · 9 fattori, i più gravi prima",
    )
  })
  it("la chiave rifiutata e' rossa; i crediti finiti dicono le loro parole", () => {
    const rifiutata = disegnaComeVa(misureDi(), {
      detto: detto({ key: true, meteoblue: "refused" }),
    })
    fireEvent.click(within(rifiutata.carta).getByRole("button", { name: /Altri/ }))
    const seeing = righe(rifiutata.carta).findIndex((r) => r[0] === "Seeing")
    expect(righe(rifiutata.carta)[seeing]).toEqual([
      "Seeing",
      "✕ chiave non valida",
      "Chiave Meteoblue non valida o scaduta.",
    ])
    expect(pillole(rifiutata.carta)[seeing]).toContain("al-pillola--non-adatta")
    cleanup()
    const finiti = disegnaComeVa(misureDi(), { detto: detto({ key: true, meteoblue: "limited" }) })
    fireEvent.click(within(finiti.carta).getByRole("button", { name: /Altri/ }))
    expect(righe(finiti.carta).find((r) => r[0] === "Seeing")).toEqual([
      "Seeing",
      "? si riprova più tardi",
      "Meteoblue non risponde per ora: crediti o richieste esauriti. La chiave è buona, riprovo più tardi.",
    ])
  })
  it("una misura che va sul grafico si accende toccandola; una accesa resta com'e'", () => {
    const n = misureDi(
      m("rain", { level: "go", value: 0.4 }),
      m("gust", { level: "go", value: 35 }),
      ...["cloud_low", "condensation", "visibility", "wind", "seeing", "jet", "aerosol"].map((c) =>
        m(c, { level: "go", value: 1 }),
      ),
    )
    const { carta, sguardo } = disegnaComeVa(n)
    const [pioggia, raffiche] = [...carta.querySelectorAll<HTMLElement>(".al-meteo__colonna-7")]
    expect(pioggia?.getAttribute("role")).toBe("button")
    expect(pioggia?.getAttribute("title")).toBe("Metti sul grafico")
    expect(raffiche?.getAttribute("role")).toBeNull()
    fireEvent.click(pioggia as HTMLElement)
    expect(sguardo.accendi).toHaveBeenCalledWith("rain")
    cleanup()
    const accesa = disegnaComeVa(n, { accese: ["rain"] })
    fireEvent.click(accesa.carta.querySelector(".al-meteo__colonna-7") as HTMLElement)
    expect(accesa.sguardo.accendi).not.toHaveBeenCalled()
  })
  it("un fattore solo: niente bottone, l'etichetta al singolare", () => {
    const tutte = [
      "cloud_low",
      "condensation",
      "visibility",
      "wind",
      "seeing",
      "jet",
      "aerosol",
      "rain",
    ]
    const n = misureDi(...tutte.map((c) => m(c, { level: c === "rain" ? "go" : null, value: 1 })))
    const { carta } = disegnaComeVa(n)
    expect(carta.textContent).toContain("pesa accanto al verdetto, senza cambiarlo · 1 fattore")
    expect(within(carta).queryByRole("button", { name: /Altr/ })).toBeNull()
  })
  it("tre fattori: il bottone dice Altro fattore", () => {
    const tutte = [
      "cloud_low",
      "condensation",
      "visibility",
      "wind",
      "seeing",
      "jet",
      "aerosol",
      "rain",
    ]
    const n = misureDi(
      ...tutte.map((c) =>
        m(c, { level: ["wind", "jet", "aerosol"].includes(c) ? "go" : null, value: 1 }),
      ),
    )
    expect(
      within(disegnaComeVa(n).carta).getByRole("button", { name: /Altro fattore/ }),
    ).toBeTruthy()
  })
  it("nessun fattore: lo dice", () => {
    const tutte = [
      "cloud_low",
      "condensation",
      "visibility",
      "wind",
      "seeing",
      "jet",
      "aerosol",
      "rain",
    ]
    const n = misureDi(...tutte.map((c) => m(c, { value: 1 })))
    const { carta } = disegnaComeVa(n)
    expect(carta.querySelector(".al-meteo__blocco-6")?.textContent).toBe("Nessun altro fattore.")
    expect(righe(carta)).toEqual([])
  })
})

describe("Come va: la Luna", () => {
  const luna = (campi: Record<string, unknown>) =>
    m("moon", {
      level: "nogo",
      value: 55,
      known_hours: 2,
      known_since: T("23:00"),
      known_until: T("02:00"),
      ...campi,
    })
  const detta = (campi: Record<string, unknown>) =>
    righe(disegnaComeVa(misureDi(luna(campi))).carta)[0]
  it("dice quando sorge, quando tramonta, in mezzo o tutta la notte", () => {
    expect(detta({ known_to_end: true })).toEqual([
      "Luna",
      "! consigliata banda stretta",
      "al 55% dalle 23:00 · banda larga fino alle 23:00",
    ])
    cleanup()
    expect(detta({ known_from_start: true, level: "marginal" })?.[2]).toBe(
      "al 55% fino alle 02:00 · senza Luna dalle 02:00",
    )
    cleanup()
    expect(detta({})?.[2]).toBe("al 55% dalle 23:00 alle 02:00 · banda larga prima e dopo")
    cleanup()
    expect(detta({ known_from_start: true, known_to_end: true })?.[2]).toBe("al 55% tutta la notte")
  })
  it("una Luna buona o senza ore non dice quando; senza ore date non c'e'", () => {
    expect(detta({ level: "go" })).toEqual(["Luna", "✓ buona per la banda larga", ""])
    cleanup()
    expect(detta({ known_since: null })?.[2]).toBe("")
    cleanup()
    expect(detta({ known_until: null })?.[2]).toBe("")
    cleanup()
    expect(detta({ known_hours: 0 })?.[0]).not.toBe("Luna")
  })
  it("in una tendenza resta la sola Luna, e la frase della tendenza", () => {
    const t = { ...TENDENZA, measures: [luna({ known_to_end: true })] } as unknown as Notte
    const { carta } = disegnaComeVa(t)
    expect(righe(carta)).toEqual([
      ["Luna", "! consigliata banda stretta", "al 55% dalle 23:00 · banda larga fino alle 23:00"],
    ])
    expect(carta.textContent).toContain(
      "Per le notti di tendenza non ci sono le misure ora per ora",
    )
    expect(carta.textContent).not.toContain("pesa")
    cleanup()
    const senza = disegnaComeVa(TENDENZA as unknown as Notte).carta
    expect(righe(senza)).toEqual([])
  })
})

describe("Come va: i fatti della notte", () => {
  const fatti = (c: HTMLElement) =>
    [...c.querySelectorAll<HTMLElement>(".al-meteo__colonna-10, .al-meteo__colonna-22")].map((f) =>
      [...f.children].map((x) => x.textContent),
    )
  it("il buio con le sue ore e la Trasparenza", () => {
    expect(fatti(disegnaComeVa(notte()).carta)).toEqual([
      ["Buio", "21:00–23:00", "8 ore"],
      ["Trasparenza della notte", "64/100", "media nel buio · decide il verdetto"],
    ])
  })
  it("una finestra nautica dice che non c'e' buio astronomico; senza trasparenza non la dice", () => {
    expect(fatti(disegnaComeVa(notte({ window: "nautical", transparency: null })).carta)).toEqual([
      ["Buio nautico", "20:25–23:00", "mai buio astronomico"],
    ])
  })
  it("senza finestra niente buio; una tendenza tiene il buio solo", () => {
    expect(fatti(disegnaComeVa(notte({ window: null })).carta)).toEqual([
      ["Trasparenza della notte", "64/100", "media nel buio · decide il verdetto"],
    ])
    cleanup()
    expect(fatti(disegnaComeVa(TENDENZA as unknown as Notte).carta)).toEqual([
      ["Buio", "19:20–06:40", "8 ore"],
    ])
  })
  it("col racconto della notte i fatti si fanno da parte", () => {
    const evento = { kind: "sunset", at: T("19:20"), until: null, body: null }
    const { carta } = disegnaComeVa(notte({ events: [evento] }))
    expect(fatti(carta)).toEqual([])
  })
  it("il titolo dice di che notte si parla; sul telefono anche", () => {
    expect(disegnaComeVa(notte()).carta.textContent).toContain("Gli altri fattoristanotte")
    cleanup()
    const tel = disegnaComeVa(notte(), { telefono: true, prima: false }).carta
    expect(tel.textContent).toContain("Gli altri fattorisabato 26")
    expect(fatti(tel)).toHaveLength(2)
  })
})
