// @vitest-environment jsdom
/**
 * Il **grafico della carta grande** (tavola v79): ogni ora, fascia e curva sta al suo posto sul
 * tempo della notte, 18:30-07:30 del banco, cioe' 1000 unita' per 13 ore. Il cursore si muove
 * con tastiera, mouse e dito; la vista del Sistema solare mette i pianeti sulla stessa scala.
 */
import { fireEvent, screen } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { quandoDellaLuna, quandoDellEvento } from "../src/DashboardNotte"
import type { Stanotte } from "../src/DashboardDati"
import { pulisci } from "./banco"
import { NOTTE, STANOTTE_PIENA, montaDashboard } from "./dashboard-banco"
import { ora } from "./meteo-banco"

afterEach(pulisci)

const H = (h: string) => `2026-09-30T${h}:00+02:00`
const D = (h: string) => `2026-10-01T${h}:00+02:00`
const notte = (moon: Record<string, unknown> | null, night: string | null = "2026-09-30") =>
  ({
    ...STANOTTE_PIENA,
    night,
    moon: moon && { ...STANOTTE_PIENA.moon, ...moon },
  }) as unknown as Stanotte

// due ore con la Trasparenza dentro il grafico, una fuori e una senza
const ORE = [
  ora(H("12:00"), "day", { transparency: 90 }),
  ora(H("21:00"), "dark", { transparency: null }),
  ora(H("22:00"), "dark", { transparency: 70.4 }),
  ora(D("00:00"), "dark", { transparency: 50 }),
]
const conOre = (o: unknown[] = ORE) => ({ previsione: { nights: [{ ...NOTTE, hours: o }] } })

const cursore = () => screen.findByRole("slider")
const riquadro = () => screen.queryByRole("tooltip")
const tracciati = () => [...document.querySelectorAll("svg[viewBox='0 0 1000 200'] path")]
const linee = () => tracciati().filter((p) => p.getAttribute("fill") === "none")
const stile = (el: Element | null | undefined) =>
  (el as HTMLElement | null)?.getAttribute("style") ?? ""
// una percentuale di posto, a due decimali
const posto = (v: string | undefined) => Number.parseFloat(v ?? "").toFixed(2)

describe("la Luna in parole", () => {
  it("dopo la data della notte e' domani, nello stesso giorno no", () => {
    const s = notte({})
    expect(quandoDellEvento(s, "rise", H("23:40"))).toBe("sorge 23:40")
    expect(quandoDellEvento(s, "set", D("00:10"))).toBe("tramonta domani 00:10")
    expect(quandoDellEvento(s, "at", D("05:30"))).toBe("domani alle 05:30")
    expect(quandoDellEvento(notte({}, null), "rise", D("00:10"))).toBe("sorge 00:10")
  })

  it("senza levata ne' tramonto dice se resta sotto o sopra, lo zero e' sopra", () => {
    expect(
      quandoDellaLuna(
        notte({ rise: null, set: null, highest: { at: D("01:00"), altitude_deg: -0.5 } }),
      ),
    ).toBe("non sorge stanotte")
    expect(
      quandoDellaLuna(
        notte({ rise: null, set: null, highest: { at: D("01:00"), altitude_deg: 0 } }),
      ),
    ).toBe("sopra l'orizzonte tutta la notte")
  })

  it("un evento solo dice anche quello che manca", () => {
    expect(quandoDellaLuna(notte({ set: null }))).toBe("sorge 23:40 \u00b7 non tramonta stanotte")
    expect(quandoDellaLuna(notte({ rise: null, set: H("22:15") }))).toBe(
      "tramonta 22:15 \u00b7 non sorge stanotte",
    )
    expect(quandoDellaLuna(notte(null))).toBe("")
  })
})

describe("il grafico della Notte", () => {
  it("i confini delle fasce: l'ora al suo posto, a righe alterne, il buio in grassetto", async () => {
    await montaDashboard()
    await cursore()
    const testa = [...document.querySelectorAll("span")].filter(
      (s) => /^\d\d:\d\d$/.test(s.textContent ?? "") && stile(s).includes("translateX(-50%)"),
    )
    expect(testa.map((s) => s.textContent)).toEqual([
      "19:11",
      "19:41",
      "20:15",
      "20:48",
      "05:48",
      "06:21",
      "06:55",
      "07:25",
    ])
    expect(testa.map((s) => posto((s as HTMLElement).style.left))).toEqual([
      "5.26",
      "9.10",
      "13.46",
      "17.69",
      "86.92",
      "91.15",
      "95.51",
      "99.36",
    ])
    expect(testa.map((s) => (s as HTMLElement).style.top)).toEqual([
      "0px",
      "17px",
      "0px",
      "17px",
      "0px",
      "17px",
      "0px",
      "17px",
    ])
    expect(testa.map((s) => (s as HTMLElement).style.fontWeight)).toEqual([
      "400",
      "400",
      "400",
      "600",
      "600",
      "400",
      "400",
      "400",
    ])
  })

  it("le fasce del cielo coprono il grafico, ognuna col suo grado di buio", async () => {
    await montaDashboard()
    await cursore()
    const rett = [...document.querySelectorAll("svg[viewBox='0 0 1000 200'] rect")]
    expect(rett.map((r) => (r as SVGElement).style.fillOpacity)).toEqual([
      "var(--banda-0)",
      "var(--banda-1)",
      "var(--banda-2)",
      "var(--banda-3)",
      "var(--banda-4)",
      "var(--banda-3)",
      "var(--banda-2)",
      "var(--banda-1)",
      "var(--banda-0)",
    ])
    expect(Number(rett[4]?.getAttribute("x"))).toBeCloseTo(176.92, 1)
    expect(Number(rett[4]?.getAttribute("width"))).toBeCloseTo(692.31, 1)
    expect(Number(rett[8]?.getAttribute("width"))).toBeCloseTo(6.41, 1)
    const righe = [...document.querySelectorAll("svg[viewBox='0 0 1000 200'] line")]
    expect(
      righe
        .filter((l) => l.getAttribute("stroke-dasharray") === "1 3")
        .map((l) => Number(l.getAttribute("x1")).toFixed(1)),
    ).toEqual(["52.6", "91.0", "134.6", "176.9", "869.2", "911.5", "955.1", "993.6"])
    expect(
      righe
        .filter((l) => l.getAttribute("stroke-dasharray") === "2 4")
        .map((l) => l.getAttribute("y1")),
    ).toEqual(["10", "102.5", "195"])
  })

  it("la Trasparenza sta a mezz'ora, la Luna sotto l'orizzonte spezza la sua curva", async () => {
    await montaDashboard({
      ...conOre(),
      stanotte: {
        moon: {
          ...STANOTTE_PIENA.moon,
          track: [
            { at: H("20:00"), altitude_deg: 9, moonless_dark_left_s: 0 },
            { at: H("22:00"), altitude_deg: -3, moonless_dark_left_s: 0 },
            { at: D("00:00"), altitude_deg: 18, moonless_dark_left_s: 0 },
            { at: D("02:00"), altitude_deg: 36, moonless_dark_left_s: 0 },
            { at: D("09:00"), altitude_deg: 40, moonless_dark_left_s: 0 },
          ],
        },
      },
    })
    await cursore()
    const [alone, aloneLuna, tr, lu] = linee()
    expect(tr?.getAttribute("d")).toBe("M307.7 64.8 L461.5 102.5 ")
    expect(lu?.getAttribute("d")).toBe("M115.4 176.5 M423.1 158.0 L576.9 121.0 ")
    expect(alone?.getAttribute("d")).toBe(tr?.getAttribute("d"))
    expect(aloneLuna?.getAttribute("d")).toBe(lu?.getAttribute("d"))
    expect([alone, aloneLuna, tr, lu].map((p) => p?.getAttribute("stroke-width"))).toEqual([
      "6",
      "4",
      "1.75",
      "1.25",
    ])
    expect([alone, aloneLuna, tr, lu].map((p) => p?.getAttribute("stroke"))).toEqual([
      "var(--prot-barra)",
      "var(--luna-linea)",
      "var(--prot-barra)",
      "var(--luna-linea)",
    ])
    expect(tr?.getAttribute("stroke-dasharray")).toBeNull()
    expect(lu?.getAttribute("stroke-dasharray")).toBe("4 4")
    const area = tracciati().find((p) => p.getAttribute("fill") === "url(#dash-area)")
    expect(area?.getAttribute("d")).toMatch(
      /^M307\.69\d* 195 L307\.7 64\.8 L461\.5 102\.5 L461\.53\d* 195 Z$/,
    )
  })

  it("senza le ore della previsione niente area, e la legenda dice che serve", async () => {
    await montaDashboard(conOre([]))
    await cursore()
    expect(tracciati().find((p) => p.getAttribute("fill") === "url(#dash-area)")).toBeUndefined()
    expect(linee()).toHaveLength(2)
    expect(document.querySelector(".al-dash__riga-8")?.textContent).toContain(
      "Trasparenza della notteserve la previsione",
    )
  })

  it("il cursore parte dal buio e dice ogni curva in quel momento", async () => {
    await montaDashboard(conOre())
    const c = await cursore()
    expect(c.getAttribute("aria-valuemin")).toBe("0")
    expect(c.getAttribute("aria-valuemax")).toBe("7")
    expect(c.getAttribute("aria-valuenow")).toBe("2")
    expect(c.getAttribute("aria-valuetext")).toBe(
      "alle 22:00: Trasparenza 70, Luna sotto l'orizzonte \u00b7 banda larga",
    )
    expect(c.getAttribute("aria-label")).toMatch(
      /^Grafico della notte\. Ore di posa stanotte: 4,6 ore\. 3,1 in banda larga, 1,5 solo banda stretta \u00b7 buio 20:48/,
    )
    const r = riquadro()
    expect(r?.textContent).toBe("alle 22:00Trasparenza70Lunasotto l'orizzonte \u00b7 banda larga")
    expect(posto((r as HTMLElement).style.left)).toBe("26.92")
    expect(stile(r)).toContain("translateX(14px)")
    expect(stile(r)).toContain("top: 4px")
    const tratto = [...c.querySelectorAll("span")].find((s) => stile(s).includes("dashed"))
    expect(posto((tratto as HTMLElement).style.left)).toBe("26.92")
  })

  it("le frecce, Maiuscolo, Inizio e Fine spostano il cursore senza uscire dalla notte", async () => {
    await montaDashboard(conOre())
    const c = await cursore()
    const premi = (key: string, shiftKey = false) => fireEvent.keyDown(c, { key, shiftKey })
    const ora = () => c.getAttribute("aria-valuenow")
    expect(premi("ArrowUp")).toBe(false)
    expect(ora()).toBe("3")
    expect(c.getAttribute("aria-valuetext")).toBe(
      "alle 00:00: Trasparenza 50, Luna 15\u00b0 \u00b7 illuminata al 62% \u00b7 solo banda stretta",
    )
    premi("ArrowRight", true)
    expect(ora()).toBe("7")
    expect(c.getAttribute("aria-valuetext")).toBe(
      "alle 07:30: Trasparenza non disponibile, Luna 48\u00b0 \u00b7 illuminata al 62%",
    )
    expect(stile(riquadro())).toContain("translateX(calc(-100% - 14px))")
    premi("ArrowRight")
    expect(ora()).toBe("7")
    premi("Home")
    expect(ora()).toBe("0")
    premi("ArrowLeft")
    expect(ora()).toBe("0")
    premi("End")
    expect(ora()).toBe("7")
    premi("ArrowDown")
    expect(ora()).toBe("6")
    premi("ArrowLeft", true)
    expect(ora()).toBe("2")
    expect(premi("a")).toBe(true)
    expect(ora()).toBe("2")
  })

  it("il mouse e il dito portano il cursore al passo piu' vicino", async () => {
    await montaDashboard(conOre())
    const c = await cursore()
    c.getBoundingClientRect = () => ({
      left: 100,
      width: 1000,
      top: 0,
      height: 200,
      right: 1100,
      bottom: 200,
      x: 100,
      y: 0,
      toJSON: () => ({}),
    })
    fireEvent.mouseMove(c, { clientX: 530 })
    expect(c.getAttribute("aria-valuenow")).toBe("3")
    fireEvent.mouseMove(c, { clientX: 1090 })
    expect(c.getAttribute("aria-valuenow")).toBe("7")
    fireEvent.touchStart(c, { touches: [{ clientX: 210 }] })
    expect(c.getAttribute("aria-valuenow")).toBe("1")
    fireEvent.touchMove(c, { touches: [{ clientX: 100 }] })
    expect(c.getAttribute("aria-valuenow")).toBe("0")
  })

  it("il fuoco si vede", async () => {
    await montaDashboard()
    const c = await cursore()
    expect(c.style.outlineStyle).toBe("none")
    fireEvent.focus(c)
    expect(c.style.outline).toBe("2px solid var(--prot-testo)")
    fireEvent.blur(c)
    expect(c.style.outlineStyle).toBe("none")
  })

  it("la striscia della ripresa: ogni tratto al suo posto, il nome corto se non ci sta", async () => {
    await montaDashboard({
      stanotte: {
        shooting: [
          { band: "broadband", starts_at: H("20:48"), ends_at: H("21:30"), seconds: 2520 },
          { band: "narrowband", starts_at: H("21:30"), ends_at: D("05:48"), seconds: 29880 },
        ],
      },
    })
    await cursore()
    const tratti = [...document.querySelectorAll("div[aria-hidden='true'] > span")].filter((s) =>
      stile(s).includes("border-radius: 6px"),
    )
    expect(tratti.map((s) => s.textContent)).toEqual(["larga", "solo banda stretta"])
    expect((tratti[0] as HTMLElement).style.left).toBe("calc(17.6923% + 0px)")
    expect((tratti[0] as HTMLElement).style.width).toBe("calc(5.38462% + 0px)")
    expect((tratti[1] as HTMLElement).style.left).toBe("calc(23.0769% + 2px)")
    expect((tratti[0] as HTMLElement).style.background).toBe("var(--prot-traccia)")
    expect((tratti[1] as HTMLElement).style.background).toContain("repeating-linear-gradient")
    expect(stile(tratti[1]?.firstElementChild)).toContain("background: var(--prot-fondo)")
    expect((tratti[0]?.firstElementChild as HTMLElement).style.backgroundColor).toBe("transparent")
  })

  it("senza tratti di ripresa la striscia non c'e'", async () => {
    await montaDashboard({ stanotte: { shooting: [] } })
    await cursore()
    expect(
      [...document.querySelectorAll("span")].filter((s) => stile(s).includes("border-radius: 6px")),
    ).toHaveLength(0)
  })

  it("sotto il grafico le ore pari intere, e la chiave delle fasce col tramonto e l'alba", async () => {
    await montaDashboard()
    await cursore()
    const asse = document.querySelector(".al-dash__riga-5 span")
    const tacchi = [...(asse?.children ?? [])] as HTMLElement[]
    expect(tacchi.map((h) => h.textContent)).toEqual(["20", "22", "00", "02", "04", "06"])
    expect(tacchi.map((h) => posto(h.style.left))).toEqual([
      "11.54",
      "26.92",
      "42.31",
      "57.69",
      "73.08",
      "88.46",
    ])
    const chiave = [...document.querySelectorAll(".al-dash__riga-7")]
    expect(chiave.map((k) => k.textContent)).toEqual([
      "giorno \u00b7 tramonto 19:11",
      "crepuscolo civile",
      "nautico",
      "astronomico",
      "buio 20:48\u201305:48",
      "alba 07:25",
    ])
    expect(chiave.map((k) => stile(k.firstElementChild).match(/--banda-(\d)/)?.[1])).toEqual([
      "0",
      "1",
      "2",
      "3",
      "4",
      "0",
    ])
    const legenda = [...document.querySelectorAll(".al-dash__riga-9")].map((l) => l.textContent)
    expect(legenda).toEqual([
      "Trasparenza della notte",
      "Lunasorge 23:40 \u00b7 tramonta domani 15:17",
      "Buio20:48\u201305:48 \u00b7 senza Luna 20:48\u201323:40",
    ])
  })

  it("senza il buio nel grafico la chiave dice giorno e buio senza ore", async () => {
    await montaDashboard({
      stanotte: {
        sky_bands: [{ starts_at: H("18:00"), ends_at: D("08:00"), kind: "civil" }],
        chart: { ...STANOTTE_PIENA.chart, dark_from: null, dark_until: null },
        moonless_dark: [],
      },
    })
    await cursore()
    expect([...document.querySelectorAll(".al-dash__riga-7")].map((k) => k.textContent)).toEqual([
      "giorno",
      "crepuscolo civile",
      "nautico",
      "astronomico",
      "buio",
    ])
    expect(document.querySelectorAll(".al-dash__riga-9")[2]?.textContent).toBe("Buio")
  })
})

describe("la vista del Sistema solare", () => {
  it("ogni pianeta e la Luna in gradi, sulla scala dei 90", async () => {
    await montaDashboard()
    fireEvent.click(await screen.findByRole("tab", { name: "Sistema solare" }))
    await screen.findByText("Più alto stanotte, nel Sistema solare")
    const d = linee()
      .slice(5)
      .map((p) => p.getAttribute("d"))
    expect(d).toEqual([
      "M115.4 153.9 L346.2 110.7 L653.8 174.4 ",
      "M653.8 133.3 ",
      "M807.7 153.9 ",
      "M38.5 184.7 ",
      "M423.1 164.2 L576.9 123.1 L730.8 92.2 L884.6 88.1 L1000.0 96.3 ",
    ])
    expect(
      linee()
        .slice(5)
        .map((p) => p.getAttribute("stroke")),
    ).toEqual([
      "var(--pianeta-0)",
      "var(--pianeta-1)",
      "var(--pianeta-2)",
      "var(--pianeta-3)",
      "var(--luna-linea)",
    ])
    const scala = [...document.querySelectorAll("span")]
      .filter((s) => stile(s).includes("translateY(-50%)"))
      .map((s) => s.textContent)
    expect(scala).toEqual(["90\u00b0", "45\u00b0", "0\u00b0"])
    expect(document.querySelector(".al-dash__riga-6")).toBeNull()
    expect([...document.querySelectorAll(".al-dash__riga-9")].map((l) => l.textContent)).toEqual([
      "Saturnotramonta 04:10",
      "Giovesorge 23:05",
      "Martesorge 01:10",
      "Veneretramonta 19:40",
      "Lunasorge 23:40 \u00b7 tramonta domani 15:17",
    ])
    expect(document.querySelector(".al-dash__blocco-2")?.textContent).toBe(
      "Giove sorge alle 23:05 \u00b7 Marte sorge alle 01:10 \u00b7 Venere tramonta alle 19:40",
    )
    fireEvent.click(screen.getByRole("tab", { name: "Notte" }))
    expect(await screen.findByText("Ore di posa stanotte")).toBeDefined()
  })

  it("un pianeta che non sorge ne' tramonta dice il suo massimo; senza massimo tace", async () => {
    await montaDashboard({
      stanotte: {
        planets: [
          STANOTTE_PIENA.planets[0],
          {
            key: "jupiter",
            track: [],
            rise: null,
            set: null,
            highest: { at: D("01:00"), altitude_deg: 33.6 },
          },
          { key: "mars", track: [], rise: null, set: null, highest: null },
        ],
      },
    })
    fireEvent.click(await screen.findByRole("tab", { name: "Sistema solare" }))
    await screen.findByText("Più alto stanotte, nel Sistema solare")
    expect(document.querySelector(".al-dash__blocco-2")?.textContent).toBe(
      "Giove al massimo a 34\u00b0",
    )
    expect(
      [...document.querySelectorAll(".al-dash__riga-9")].map((l) => l.textContent).slice(0, 3),
    ).toEqual(["Saturnotramonta 04:10", "Giovemassimo 34\u00b0", "Marte"])
  })

  it("il cursore legge ogni pianeta alla sua ora, non al passo della Luna (Issue #58)", async () => {
    await montaDashboard()
    fireEvent.click(await screen.findByRole("tab", { name: "Sistema solare" }))
    const c = await cursore()
    expect(c.getAttribute("aria-valuetext")).toBe(
      "alle 22:00: Saturno non disponibile, Giove non disponibile, Marte non disponibile, " +
        "Venere non disponibile, Luna sotto l'orizzonte · banda larga",
    )
    fireEvent.keyDown(c, { key: "ArrowLeft" })
    expect(c.getAttribute("aria-valuetext")).toBe(
      "alle 20:00: Saturno 20°, Giove sotto l'orizzonte, Marte sotto l'orizzonte, " +
        "Venere sotto l'orizzonte, Luna sotto l'orizzonte",
    )
  })

  it("senza il pianeta piu' alto la vista non c'e'", async () => {
    await montaDashboard({ stanotte: { highest_planet: null } })
    await cursore()
    expect(screen.queryByRole("tab", { name: "Sistema solare" })).toBeNull()
  })
})

describe("la testa della carta senza previsione", () => {
  it("senza meteo: il buio calcolato, grigio, e perche'", async () => {
    await montaDashboard({ stanotte: { weather: null } })
    expect(await screen.findByText("Buio stanotte, calcolato")).toBeDefined()
    expect(screen.getByText("9 h")).toBeDefined()
    const p = screen.getByText("? senza meteo")
    expect(p.getAttribute("style")).toContain("background: var(--carta-2)")
    expect(document.querySelector(".al-dash__blocco-2")?.textContent).toBe(
      "buio 20:48\u201305:48 \u00b7 senza Luna 20:48\u201323:40 \u00b7 nuvole e seeing non disponibili",
    )
  })

  it("una notte da non aprire porta il colore del no", async () => {
    await montaDashboard({ stanotte: { weather: { ...STANOTTE_PIENA.weather, verdict: "nogo" } } })
    await cursore()
    expect(document.querySelector(".al-dash__pillola-2")?.getAttribute("style")).toContain(
      "var(--non-adatto-fondo)",
    )
  })

  it("una notte al limite porta il colore dell'incerto", async () => {
    await montaDashboard({
      stanotte: { weather: { ...STANOTTE_PIENA.weather, verdict: "marginal" } },
    })
    await cursore()
    expect(document.querySelector(".al-dash__pillola-2")?.getAttribute("style")).toContain(
      "var(--incerto-fondo)",
    )
  })
})

describe("la carta grande sul telefono", () => {
  it("solo i confini del buio e gli estremi, il riquadro dopo il tocco, sopra il grafico", async () => {
    await montaDashboard({ larga: 390 })
    const c = await cursore()
    const testa = [...document.querySelectorAll("span")].filter(
      (s) => /^\d\d:\d\d$/.test(s.textContent ?? "") && stile(s).includes("translateX(-50%)"),
    )
    expect(testa.map((s) => s.textContent)).toEqual(["19:11", "20:48", "05:48", "07:25"])
    expect(riquadro()).toBeNull()
    expect(c.style.left).toBe("28px")
    fireEvent.keyDown(c, { key: "ArrowRight" })
    const r = riquadro()
    expect(stile(r)).toContain("top: -38px")
    expect(stile(r)).toContain("translateY(-100%)")
    expect(stile(r)).toContain("left: 0px")
    expect(document.querySelector(".al-dash__riga-32")).not.toBeNull()
    expect(document.querySelector(".al-dash__testo-32")?.textContent).toBe(
      "3,1 in banda larga, 1,5 solo banda stretta",
    )
    const tratti = [...document.querySelectorAll("span")].filter((s) =>
      stile(s).includes("border-radius: 6px"),
    )
    expect(tratti.map((s) => s.textContent)).toEqual(["larga", "solo banda stretta"])
    expect([...document.querySelectorAll(".al-dash__riga-33")].map((l) => l.textContent)[0]).toBe(
      "Trasparenza della notte",
    )
  })
})
