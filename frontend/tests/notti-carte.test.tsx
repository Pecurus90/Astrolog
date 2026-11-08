// @vitest-environment jsdom
/**
 * Le carte delle Notti (`src/NottiCarte.tsx`), disegnate da sole: la protagonista sul desktop e
 * sul telefono, le righe di *A confronto*, *Tutto l'archivio*. Classi della consegna, testi da
 * t(), ruoli e aria; il colore no, jsdom non ha la cascata.
 */
import { fireEvent, render, screen, within } from "@testing-library/react"
import type { ReactElement } from "react"
import { MemoryRouter } from "react-router"
import { afterEach, describe, expect, it, vi } from "vitest"

import type { Formato } from "../src/componenti/Tema"
import { t } from "../src/i18n"
import { AConfronto, Protagonista, TuttoLArchivio, type VoceFuori } from "../src/NottiCarte"
import type { Elenco, Notte } from "../src/NottiDati"
import { pulisci } from "./banco"

afterEach(pulisci)

const METEO: Notte["weather"] = {
  state: "ok",
  arrives_on: null,
  verdict: "go",
  cloud_total_pct: 8,
  usable_hours: 7,
  window: "dark",
  window_hours: 9,
  transparency: 88,
  exposure_hours: 2.2,
  dark_hours: 4,
  without_aerosol: false,
  sky_word: "scattered",
}

const oggetto = (key: string, integration_s: number, bar_pct: number) => ({
  key,
  name: key.toUpperCase(),
  frames: 1,
  integration_s,
  untimed: 0,
  bar_pct,
})

const PIENA: Notte = {
  id: 7,
  night_date: "2026-09-30",
  site: "Cima Ekar",
  site_source: "detected",
  site_from: "frames",
  shooting: { kind: "mixed", broadband_hours: 3.5, dark_hours: 7.5 },
  frames: 3,
  integration_s: 10800,
  untimed: 0,
  objects: [
    oggetto("m-51", 7200, 100),
    oggetto("m-101", 3600, 50),
    oggetto("m-13", 1800, 25),
    oggetto("m-27", 600, 5),
  ],
  filters: [
    { name: "Ha", passband: "HA", frames: 2, integration_s: 7200 },
    { name: "OIII", passband: "OIII", frames: 1, integration_s: 3600 },
  ],
  moon: { phase_key: "waxing_gibbous", illumination_pct: 69, lit_side: "right" },
  weather: METEO,
}

// Una notte di un sito senza fuso: niente ripresa, Luna, tacche; il cielo porta al sito.
const SENZA_FUSO: Notte = {
  ...PIENA,
  id: 6,
  night_date: "2026-09-28",
  site: "Casa",
  site_from: "home",
  shooting: null,
  integration_s: 0,
  objects: [oggetto("m-31", 0, 0)],
  filters: [],
  moon: null,
  weather: { ...METEO, state: "unknown", verdict: null, exposure_hours: null },
}

const conRouter = (ui: ReactElement) => render(<MemoryRouter>{ui}</MemoryRouter>)

function protagonista(
  notte: Notte,
  formato: Formato,
  extra: Partial<{ sola: boolean; onPrima: () => void; onDopo: () => void }> = {},
) {
  conRouter(
    <Protagonista
      notte={notte}
      formato={formato}
      sola={extra.sola ?? false}
      onPrima={extra.onPrima}
      onDopo={extra.onDopo}
    />,
  )
  return screen.getByRole("region", { name: "La notte" })
}

const una = (dentro: Element, selettore: string): HTMLElement => {
  const el = dentro.querySelector<HTMLElement>(selettore)
  if (!el) throw new Error(`manca ${selettore}`)
  return el
}

const testi = (dentro: Element, selettore: string): string[] =>
  [...dentro.querySelectorAll(selettore)].map((e) => e.textContent ?? "")

describe("la protagonista sul desktop", () => {
  it("occupa otto colonne accanto alla striscia, dodici da sola", () => {
    expect(protagonista(PIENA, "desktop").style.gridColumn).toBe("span 8")
    pulisci()
    expect(protagonista(PIENA, "desktop", { sola: true }).style.gridColumn).toBe("span 12")
  })

  it("il sito porta il segno della misura del desktop e dice da dove viene", () => {
    const carta = protagonista(PIENA, "desktop")
    const sito = una(carta, ".al-notti__riga-5")
    expect(carta.querySelector(".al-notti__riga-27")).toBeNull()
    expect(sito.querySelector("svg")?.getAttribute("width")).toBe("14")
    expect(sito.querySelector("path")?.getAttribute("d")).toMatch(/^M12 21s7-6\.3 7-11\.5/)
    expect(sito.textContent).toBe("Cima Ekar· dalle coordinate nei frame")
    expect(una(sito, ".al-notti__sito-fonte").textContent).toBe("· dalle coordinate nei frame")
  })

  it("titolo, ore grandi, parola e frame nei loro posti", () => {
    const carta = protagonista(PIENA, "desktop")
    expect(una(carta, ".al-notti__testo-3").textContent).toBe("Mercoledì 30 settembre 2026")
    expect(una(carta, '.al-notti__testo-4[data-an="big"]').textContent).toBe("3 h")
    expect(una(carta, ".al-notti__testo-5").textContent).toBe("ore")
    expect(una(carta, ".al-notti__colonna-1 .al-notti__testo-2").textContent).toBe("3 frame")
  })

  it("una notte buona porta la pillola buona, con le nuvole e la posa accanto", () => {
    const carta = protagonista(PIENA, "desktop")
    const pillola = una(carta, ".al-pillola")
    expect(pillola.className).toContain("al-pillola--buona")
    expect(pillola.className).toContain("al-pillola--piccola")
    expect(pillola.textContent).toContain("buona")
    expect(una(carta, ".al-notti__testo-6").textContent).toBe("Nuvole sparse, in media 8%")
    expect(una(carta, ".al-notti__colonna-2 .al-notti__testo-2").textContent).toBe(
      "2,2 ore di posa su 4 di buio",
    )
  })

  it("le tacche, nella loro barra: una per ora di buio, piene quante le ore di posa, nel colore dell'esito", () => {
    const carta = protagonista(PIENA, "desktop")
    const barra = una(carta, ".al-notti__barra-posa")
    const tacche = una(barra, ".al-notti__riga-9")
    expect(tacche.getAttribute("aria-hidden")).toBe("true")
    const sfondi = [...tacche.querySelectorAll<HTMLElement>(".al-notti__pillola-1")].map(
      (s) => s.style.background,
    )
    expect(sfondi).toEqual([
      "var(--buono-testo)",
      "var(--buono-testo)",
      "var(--barretta-spenta)",
      "var(--barretta-spenta)",
    ])
    expect(una(barra, ".al-notti__testo-2").textContent).toBe(t("nights.ticks"))
  })

  it("le tacche piene di una notte incerta prendono il colore dell'incerta", () => {
    const incerta = { ...PIENA, weather: { ...METEO, verdict: "marginal" as const } }
    const carta = protagonista(incerta, "desktop")
    expect(una(carta, ".al-notti__pillola-1").style.background).toBe("var(--incerto-testo)")
  })

  it("le tacche piene di una notte non adatta prendono il colore della non adatta", () => {
    const no = { ...PIENA, weather: { ...METEO, verdict: "nogo" as const } }
    const carta = protagonista(no, "desktop")
    expect(una(carta, ".al-notti__pillola-1").style.background).toBe("var(--non-adatto-testo)")
  })

  it("la ripresa sta nella sua riga, la Luna nella sua", () => {
    const carta = protagonista(PIENA, "desktop")
    expect(
      within(una(carta, ".al-notti__riga-8")).getByRole("img").getAttribute("aria-label"),
    ).toBe("Ripresa: 3 h 30 di banda larga")
    const luna = una(carta, ".al-notti__riga-10")
    expect(luna.textContent).toContain("Gibbosa crescente")
    expect(luna.textContent).toContain("illuminata al 69%")
  })

  it("gli oggetti: etichetta, nome, barra e ore, poi quanti altri", () => {
    const carta = protagonista(PIENA, "desktop")
    const colonne = carta.querySelectorAll(".al-notti__griglia-3 > .al-notti__colonna-3")
    expect(colonne).toHaveLength(2)
    const og = colonne[0] as HTMLElement
    expect(testi(og, ":scope > .al-notti__testo-2")).toEqual(["oggetti", "e 1 altro"])
    const righe = og.querySelectorAll(".al-notti__griglia-4")
    expect(righe).toHaveLength(3)
    expect(testi(og, ".al-notti__blocco-3")).toEqual(["M-51", "M-101", "M-13"])
    expect(testi(og, ".al-notti__testo-7")).toEqual(["2 h", "1 h", "30 min"])
    expect(
      og.querySelector(".al-notti__riga-11 .al-notti__pillola-2")?.getAttribute("data-an"),
    ).toBe("barra")
  })

  it("i filtri: etichetta e barra con una riga per filtro", () => {
    const carta = protagonista(PIENA, "desktop")
    const fi = carta.querySelectorAll(
      ".al-notti__griglia-3 > .al-notti__colonna-3",
    )[1] as HTMLElement
    expect(una(fi, ":scope > .al-notti__testo-2").textContent).toBe("filtri")
    expect(within(fi).getByRole("img").getAttribute("aria-label")).toBe("Filtri: Ha 2 h, OIII 1 h")
  })

  it("un sito senza fuso: pillola mancante, il bottone piccolo verso il sito, niente tacche, ripresa, Luna", () => {
    const carta = protagonista(SENZA_FUSO, "desktop")
    expect(una(carta, ".al-pillola").className).toContain("al-pillola--mancante")
    const link = within(carta).getByRole("link", { name: "Modifica sito" })
    expect(link.getAttribute("href")).toBe("/impostazioni/sito")
    expect(link.className).toBe("al-bottone al-bottone--pieno al-bottone--piccolo")
    expect(carta.querySelector(".al-notti__barra-posa")).toBeNull()
    expect(carta.querySelector(".al-notti__riga-8")).toBeNull()
    expect(carta.querySelector(".al-notti__riga-10")).toBeNull()
  })

  it("tre oggetti o meno non scrivono altri", () => {
    const carta = protagonista({ ...PIENA, objects: PIENA.objects.slice(0, 2) }, "desktop")
    const og = una(carta, ".al-notti__colonna-3")
    expect(testi(og, ":scope > .al-notti__testo-2")).toEqual(["oggetti"])
  })

  it("una notte senza meteo ha la pillola mancante e niente link al sito", () => {
    const carta = protagonista({ ...PIENA, weather: { ...METEO, verdict: null } }, "desktop")
    expect(una(carta, ".al-pillola").className).toContain("al-pillola--mancante")
    expect(within(carta).queryByRole("link")).toBeNull()
  })
})

describe("la protagonista sul telefono", () => {
  it("il sito porta il segno piu' piccolo, nella riga del telefono", () => {
    const carta = protagonista(PIENA, "telefono")
    expect(carta.querySelector(".al-notti__riga-5")).toBeNull()
    expect(una(carta, ".al-notti__riga-27 svg").getAttribute("width")).toBe("13")
    expect(una(carta, ".al-notti__testo-24").textContent).toBe("Mercoledì 30 settembre 2026")
    expect(carta.style.gridColumn).toBe("")
  })

  it("le frecce vanno alla notte prima e dopo; una che non c'e' e' spenta", () => {
    const prima = vi.fn()
    const carta = protagonista(PIENA, "telefono", { onPrima: prima })
    const indietro = within(carta).getByLabelText("La notte prima")
    const avanti = within(carta).getByLabelText("La notte dopo")
    expect(indietro.textContent).toBe("‹")
    expect(avanti.textContent).toBe("›")
    expect(indietro.className).toBe("al-notti__tondo-1")
    expect(indietro.getAttribute("aria-disabled")).toBeNull()
    expect(indietro.style.opacity).toBe("1")
    expect(avanti.getAttribute("aria-disabled")).toBe("true")
    expect(avanti.style.opacity).toBe("0.35")
    fireEvent.click(indietro)
    expect(prima).toHaveBeenCalledTimes(1)
  })

  it("la freccia dopo, quando c'e', e' accesa e chiama", () => {
    const dopo = vi.fn()
    const carta = protagonista(PIENA, "telefono", { onDopo: dopo })
    const avanti = within(carta).getByLabelText("La notte dopo")
    expect(avanti.getAttribute("aria-disabled")).toBeNull()
    expect(avanti.style.opacity).toBe("1")
    const indietro = within(carta).getByLabelText("La notte prima")
    expect(indietro.style.opacity).toBe("0.35")
    expect(indietro.getAttribute("aria-disabled")).toBe("true")
    fireEvent.click(avanti)
    expect(dopo).toHaveBeenCalledTimes(1)
  })

  it("da sola non ha frecce", () => {
    const carta = protagonista(PIENA, "telefono", { sola: true })
    expect(within(carta).queryByLabelText("La notte prima")).toBeNull()
    expect(carta.querySelector(".al-notti__riga-28")).toBeNull()
  })

  it("ore, cielo, ripresa, tacche e Luna nei posti del telefono", () => {
    const carta = protagonista(PIENA, "telefono")
    expect(una(carta, '.al-notti__testo-25[data-an="big"]').textContent).toBe("3 h")
    expect(una(carta, ".al-notti__colonna-15 .al-notti__testo-26").textContent).toBe("ore")
    expect(una(carta, ".al-notti__colonna-15 .al-notti__testo-11").textContent).toBe("3 frame")
    expect(una(carta, ".al-notti__riga-30 .al-notti__testo-11").textContent).toBe("cielo")
    expect(una(carta, ".al-notti__riga-30 .al-pillola").className).toContain("al-pillola--buona")
    expect(una(carta, ".al-notti__testo-23").textContent).toBe("Nuvole sparse, in media 8%")
    expect(una(carta, ".al-notti__testo-27").textContent).toBe("2,2 ore di posa su 4 di buio")
    expect(
      within(una(carta, ".al-notti__colonna-16"))
        .getAllByRole("img")[0]
        ?.getAttribute("aria-label"),
    ).toBe("Ripresa: 3 h 30 di banda larga")
    const tacche = una(carta, ".al-notti__riga-31")
    expect(tacche.querySelectorAll(".al-notti__pillola-1")).toHaveLength(4)
    expect(carta.querySelector(".al-notti__riga-9")).toBeNull()
    expect(carta.querySelector(".al-notti__barra-posa")).toBeNull()
    expect(una(carta, ".al-notti__colonna-16 > .al-notti__testo-11").textContent).toBe(
      t("nights.ticks"),
    )
    expect(una(carta, ".al-notti__riga-32").textContent).toContain("illuminata al 69%")
  })

  it("oggetti e filtri nelle colonne del telefono", () => {
    const carta = protagonista(PIENA, "telefono")
    const og = una(carta, ".al-notti__colonna-17")
    expect(testi(og, ":scope > .al-notti__testo-11")).toEqual(["oggetti", "e 1 altro"])
    expect(og.querySelectorAll(".al-notti__griglia-8")).toHaveLength(3)
    expect(testi(og, ".al-notti__blocco-11")).toEqual(["M-51", "M-101", "M-13"])
    expect(testi(og, ".al-notti__testo-29")).toEqual(["2 h", "1 h", "30 min"])
    expect(carta.querySelector(".al-notti__griglia-4")).toBeNull()
    const fi = una(carta, ".al-notti__colonna-18")
    expect(una(fi, ":scope > .al-notti__testo-11").textContent).toBe("filtri")
  })

  it("un sito senza fuso: bottone a tutta riga verso il sito, niente ripresa, tacche, Luna", () => {
    const carta = protagonista(SENZA_FUSO, "telefono")
    const link = within(carta).getByRole("link", { name: "Modifica sito" })
    expect(link.className).toBe(
      "al-bottone al-bottone--pieno al-bottone--blocco al-notti__testo-28",
    )
    expect(una(carta, ".al-pillola").className).toContain("al-pillola--mancante")
    expect(within(una(carta, ".al-notti__colonna-16")).queryByRole("img")).toBeNull()
    expect(carta.querySelector(".al-notti__riga-31")).toBeNull()
    expect(carta.querySelector(".al-notti__riga-32")).toBeNull()
  })
})

const MESI: Elenco["months"] = [{ month: "2026-09", nights: 2, integration_s: 10800, untimed: 0 }]

const AGOSTO: Notte = { ...PIENA, id: 3, night_date: "2026-08-15", shooting: null, moon: null }

type Altre = Parameters<typeof AConfronto>[0]["altre"]

function confronto(
  notti: Notte[],
  extra: { scelta?: number; onScegli?: (id: number) => void; altre?: Altre } = {},
) {
  conRouter(
    <AConfronto
      notti={notti}
      mesi={MESI}
      colonne={8}
      sotto="dalla piu' recente"
      conta="2 di 30"
      scelta={extra.scelta}
      onScegli={extra.onScegli ?? (() => undefined)}
      altre={extra.altre ?? null}
    />,
  )
  return screen.getByRole("region", { name: "A confronto" })
}

const riga = (carta: HTMLElement, i: number): HTMLElement =>
  carta.querySelectorAll<HTMLElement>('[data-an="riga"]')[i] as HTMLElement

describe("A confronto", () => {
  it("il titolo, la riga sotto, le colonne e il conto", () => {
    const carta = confronto([PIENA])
    expect(una(carta, ".al-notti__riga-15 .al-notti__testo-1").textContent).toBe("A confronto")
    expect(una(carta, ".al-notti__riga-15 .al-notti__testo-2").textContent).toBe(
      "dalla piu' recente",
    )
    const teste = una(carta, ".al-notti__griglia-5")
    expect(teste.getAttribute("aria-hidden")).toBe("true")
    expect(testi(teste, "span")).toEqual([
      "giorno",
      "sito e oggetti",
      "integrazione",
      "filtri",
      "cielo",
      "Luna",
    ])
    expect(una(carta, ".al-notti__testo-16").textContent).toBe("2 di 30")
    expect(carta.style.gridColumn).toBe("span 8")
  })

  it("le notti si raggruppano per mese, il mese col nome maiuscolo e la sua somma", () => {
    const carta = confronto([PIENA, SENZA_FUSO, AGOSTO])
    const mesi = carta.querySelectorAll(".al-notti__riga-16")
    expect([...mesi].map((m) => m.querySelector("b")?.textContent)).toEqual([
      "Settembre 2026",
      "Agosto 2026",
    ])
    expect([...mesi].map((m) => m.querySelector("span")?.textContent)).toEqual([
      "2 notti · 3 h",
      "",
    ])
    expect(carta.querySelectorAll('[data-an="riga"]')).toHaveLength(3)
  })

  it("ogni riga dice giorno, sito, oggetti, ore, frame, filtri, cielo e Luna", () => {
    const r = riga(confronto([PIENA]), 0)
    expect(r.getAttribute("role")).toBe("button")
    expect(r.getAttribute("aria-label")).toBe(
      "Mercoledì 30 settembre 2026, Cima Ekar, 3 h, cielo: buona",
    )
    expect(una(r, ".al-notti__testo-10").textContent).toBe("30")
    expect(una(r, ".al-notti__testo-11").textContent).toBe("mer")
    expect(una(r, ".al-notti__blocco-5").textContent).toBe("Cima Ekar")
    expect(una(r, ".al-notti__blocco-6").textContent).toBe("M-51 · M-101 · M-13 e 1 altro")
    expect(una(r, ".al-notti__testo-12").textContent).toBe("3 h")
    expect(testi(r, ".al-notti__testo-13")).toEqual(["3 frame", "2,2 di posa su 4 ore"])
    expect(una(r, ".al-notti__blocco-7").textContent).toBe("Ha · OIII")
    expect(una(r, ".al-pillola").className).toContain("al-pillola--buona")
    expect(una(r, ".al-pillola").className).toContain("al-pillola--minima")
    expect(within(una(r, ".al-notti__colonna-8")).getByRole("img").getAttribute("aria-label")).toBe(
      "Ripresa: 3 h 30 di banda larga",
    )
    const luna = una(r, ".al-notti__riga-17")
    expect(luna.textContent).toBe("69%")
    expect(luna.querySelector("svg")).not.toBeNull()
  })

  it("una riga senza tempo, meteo, ripresa e Luna lo dice senza buchi", () => {
    const r = riga(confronto([SENZA_FUSO]), 0)
    expect(una(r, ".al-notti__testo-12").textContent).toBe("senza durata")
    expect(r.getAttribute("aria-label")).toContain(", senza durata, cielo: non disponibile")
    expect(una(r, ".al-pillola").className).toContain("al-pillola--mancante")
    expect(within(una(r, ".al-notti__colonna-8")).queryByRole("img")).toBeNull()
    const luna = una(r, ".al-notti__riga-17")
    expect(luna.textContent).toBe("")
    expect(luna.querySelector("svg")).toBeNull()
  })

  it("la riga scelta e' premuta e accesa, le altre no", () => {
    const carta = confronto([PIENA, SENZA_FUSO], { scelta: 6 })
    const [a, b] = [riga(carta, 0), riga(carta, 1)]
    expect(a.getAttribute("aria-pressed")).toBe("false")
    expect(b.getAttribute("aria-pressed")).toBe("true")
    expect(a.style.background).toBe("transparent")
    expect(b.style.background).toBe("var(--carta-2)")
    expect(a.style.boxShadow).toBe("inset 0 0 0 2px transparent")
    expect(b.style.boxShadow).toBe("inset 0 0 0 2px var(--accento)")
    expect(una(b, ".al-pillola").className).toContain("al-pillola--su-carta")
    expect(una(a, ".al-pillola").className).not.toContain("al-pillola--su-carta")
  })

  it("toccare una riga sceglie quella notte", () => {
    const scegli = vi.fn()
    const carta = confronto([PIENA, SENZA_FUSO], { onScegli: scegli })
    fireEvent.click(riga(carta, 1))
    expect(scegli).toHaveBeenCalledWith(6)
  })

  it("senza notti dice di togliere un criterio", () => {
    const carta = confronto([])
    expect(una(carta, ".al-notti__colonna-9 .al-notti__testo-14").textContent).toBe(
      "Nessuna notte con questi criteri",
    )
    expect(una(carta, ".al-notti__colonna-9 .al-notti__testo-2").textContent).toBe(
      t("nights.list.empty.why"),
    )
    pulisci()
    expect(confronto([PIENA]).querySelector(".al-notti__colonna-9")).toBeNull()
  })

  it("Carica altre chiama, ed e' ne' spento ne' occupato", () => {
    const altre = vi.fn()
    const carta = confronto([PIENA], {
      altre: {
        testo: "Carica altre",
        spento: false,
        occupato: false,
        errore: false,
        onAltre: altre,
      },
    })
    const bottone = within(carta).getByText("Carica altre")
    expect(bottone.getAttribute("aria-disabled")).toBe("false")
    expect(bottone.getAttribute("aria-busy")).toBe("false")
    fireEvent.click(bottone)
    expect(altre).toHaveBeenCalledTimes(1)
    expect(within(carta).queryByText(t("nights.more.failed"))).toBeNull()
  })

  it("Carica altre spento e occupato non chiama; un errore lo dice sotto", () => {
    const altre = vi.fn()
    const carta = confronto([PIENA], {
      altre: { testo: "Carico altre", spento: true, occupato: true, errore: true, onAltre: altre },
    })
    const bottone = within(carta).getByText("Carico altre")
    expect(bottone.getAttribute("aria-disabled")).toBe("true")
    expect(bottone.getAttribute("aria-busy")).toBe("true")
    fireEvent.click(bottone)
    expect(altre).not.toHaveBeenCalled()
    expect(within(carta).getByText(t("nights.more.failed"))).toBeTruthy()
  })
})

const TOTALI: NonNullable<Elenco["totals"]> = {
  nights: 12,
  frames: 400,
  integration_s: 36000,
  untimed: 0,
  objects: 5,
}

const FUORI: VoceFuori[] = [
  { chiave: "review", n: 37, a: "/da-confermare" },
  { chiave: "site", n: 112, a: "/impostazioni/sito" },
  { chiave: "date", n: 9, a: null },
]

function archivio(formato: Formato, tot = TOTALI, fuori = FUORI) {
  conRouter(<TuttoLArchivio tot={tot} fuori={fuori} formato={formato} />)
  return screen.getByRole("region", { name: "Tutto l’archivio" })
}

describe("Tutto l'archivio", () => {
  it("sul desktop: le notti, i totali, le copie e le voci fuori", () => {
    const carta = archivio("desktop")
    expect(carta.style.gridColumn).toBe("span 12")
    expect(una(carta, ".al-notti__colonna-10 > .al-notti__testo-2").textContent).toBe(
      "tutto l’archivio",
    )
    expect(una(carta, ".al-notti__riga-19 .al-notti__testo-17").textContent).toBe("12")
    expect(una(carta, ".al-notti__riga-19 .al-notti__testo-5").textContent).toBe("notti")
    expect(una(carta, ".al-notti__blocco-8").textContent).toBe("5 oggetti · 400 frame · 10 ore")
    expect(una(carta, ".al-notti__blocco-9").textContent).toBe(
      "Le copie calibrate non sono contate.",
    )
    expect(una(carta, ".al-notti__colonna-11 > .al-notti__testo-2").textContent).toBe(
      "fuori da ogni notte",
    )
    expect(una(carta, ".al-notti__griglia-7").children).toHaveLength(3)
  })

  it("ogni voce dice cosa e perche', e una con indirizzo e' un link con la freccia", () => {
    const carta = archivio("desktop")
    const voci = [...una(carta, ".al-notti__griglia-7").children] as HTMLElement[]
    expect(voci.map((v) => v.querySelector(".al-notti__testo-18")?.textContent)).toEqual([
      "da confermare",
      "senza sito",
      "senza data",
    ])
    expect(
      voci.map((v) => v.querySelector(".al-notti__fuori-voce .al-notti__testo-2")?.textContent),
    ).toEqual([
      "aspettano una risposta",
      "scegli il sito: entrano nelle notti",
      "scrivi la data o la notte della cartella",
    ])
    expect(voci.map((v) => v.querySelector(".al-notti__testo-19")?.textContent)).toEqual([
      "37",
      "112",
      "9",
    ])
    expect(voci.map((v) => v.tagName)).toEqual(["A", "A", "SPAN"])
    expect(voci.map((v) => v.className)).toEqual([
      "al-notti__riga-20",
      "al-notti__riga-20",
      "al-notti__riga-20",
    ])
    expect(voci[0]?.getAttribute("aria-label")).toBe(
      "Apri Da confermare: 37 da confermare, aspettano una risposta",
    )
    expect(voci[1]?.getAttribute("href")).toBe("/impostazioni/sito")
    const freccia = una(voci[0] as HTMLElement, ".al-notti__tondo-1")
    expect(freccia.textContent).toBe("↗")
    expect(freccia.getAttribute("aria-hidden")).toBe("true")
    expect(voci[2]?.querySelector(".al-notti__tondo-1")).toBeNull()
    for (const v of voci) {
      expect(v.style.display).toBe("flex")
      expect(v.style.alignItems).toBe("center")
      expect(v.style.gap).toBe("10px")
    }
  })

  it("senza ore non scrive zero ore; i frame senza durata si contano", () => {
    const carta = archivio("desktop", { ...TOTALI, integration_s: 0, untimed: 4 })
    expect(una(carta, ".al-notti__blocco-8").textContent).toBe(
      "5 oggetti · 400 frame · 4 frame senza durata",
    )
  })

  it("senza voci fuori non c'e' la sezione", () => {
    const carta = archivio("desktop", TOTALI, [])
    expect(carta.querySelector(".al-notti__colonna-11")).toBeNull()
    expect(within(carta).queryByText("fuori da ogni notte")).toBeNull()
  })

  it("sul telefono: le stesse cose nei posti del telefono", () => {
    const carta = archivio("telefono")
    expect(carta.style.gridColumn).toBe("")
    expect(carta.querySelector(".al-notti__blocco-8")).toBeNull()
    const piccoli = testi(carta, ":scope > .al-notti__testo-11")
    expect(piccoli).toEqual(["tutto l’archivio", "Le copie calibrate non sono contate."])
    expect(una(carta, ".al-notti__riga-33 .al-notti__testo-30").textContent).toBe("12")
    expect(una(carta, ".al-notti__riga-33 .al-notti__testo-26").textContent).toBe("notti")
    expect(una(carta, ":scope > .al-notti__testo-18").textContent).toBe(
      "5 oggetti · 400 frame · 10 ore",
    )
    expect(una(carta, ".al-notti__testo-31").textContent).toBe("fuori da ogni notte")
    const voci = [...carta.querySelectorAll<HTMLElement>(".al-notti__riga-34")]
    expect(voci.map((v) => v.tagName)).toEqual(["A", "A", "SPAN"])
    expect(voci[2]?.style.display).toBe("flex")
    expect(voci[2]?.style.alignItems).toBe("center")
    expect(voci[2]?.style.gap).toBe("10px")
  })

  it("sul telefono, senza voci fuori, niente titolo delle voci", () => {
    const carta = archivio("telefono", TOTALI, [])
    expect(carta.querySelector(".al-notti__testo-31")).toBeNull()
  })

  it("una voce sola fuori basta per la sezione", () => {
    const carta = archivio("telefono", TOTALI, [{ chiave: "date", n: 1, a: null }])
    expect(una(carta, ".al-notti__testo-31").textContent).toBe("fuori da ogni notte")
  })
})
