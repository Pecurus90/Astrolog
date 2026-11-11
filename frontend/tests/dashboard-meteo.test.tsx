// @vitest-environment jsdom
/**
 * Il **meteo della Dashboard** (tavola v79): le sei carte coi numeri che il backend ha scritto,
 * le barre delle ore mostrate, il seeing senza chiave, la previsione che manca e perche', e la
 * curva piccola di ognuna delle prossime notti.
 */
import { fireEvent, screen } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { type Meteo } from "../src/DashboardDati"
import { mancanzaDelMeteo } from "../src/DashboardMeteo"
import { pulisci } from "./banco"
import { NOTTE, PROSSIME, SCALA_DELLA_LUNA, montaDashboard } from "./dashboard-banco"
import { GIUDIZI, misura, ora } from "./meteo-banco"

afterEach(pulisci)

const H = (h: string) => `2026-09-30T${h}:00+02:00`
const D = (h: string) => `2026-10-01T${h}:00+02:00`
const meteo = (campi: Record<string, unknown>) =>
  ({
    missing: null,
    fetched_at: "2026-09-30T16:05:00.000Z",
    last_request: null,
    retry_s: 900,
    nights: [NOTTE],
    ...campi,
  }) as unknown as Meteo

/** La carta del meteo col suo nome: numero, unita', barre, nota e pillola. */
function carta(nome: string) {
  const c = [
    ...document.querySelectorAll(".al-c-card-meteo__colonna-1, .al-c-card-meteo__colonna-6"),
  ].find(
    (x) =>
      x.firstElementChild?.textContent?.startsWith(nome) ||
      x.querySelector(".al-c-card-meteo__testo-1, .al-c-card-meteo__testo-6")?.textContent === nome,
  )
  if (!c) throw new Error(`nessuna carta ${nome}`)
  const barre = [
    ...c.querySelectorAll(".al-c-card-meteo__pillola-2, .al-c-card-meteo__pillola-3"),
  ] as HTMLElement[]
  return {
    valore:
      c.querySelector(".al-c-card-meteo__testo-2, .al-c-card-meteo__testo-7")?.textContent ?? "",
    unita:
      c.querySelector(
        ".al-c-card-meteo__riga-2 .al-c-card-meteo__testo-3, .al-c-card-meteo__testo-8",
      )?.textContent ?? "",
    altezze: barre.map((b) => b.style.height),
    colori: barre.map((b) => b.style.background),
    nota: c.querySelector(".al-c-card-meteo__colonna-3")?.textContent ?? "",
    testo: c.textContent ?? "",
  }
}

describe("quando la previsione manca", () => {
  it("senza fuso, prima previsione, o il servizio che non risponde", () => {
    expect(mancanzaDelMeteo(meteo({ missing: "no_timezone" }))).toMatchObject({
      segno: "?",
      titolo: "Notti non calcolabili",
      riprova: false,
    })
    expect(mancanzaDelMeteo(meteo({ fetched_at: null }))).toMatchObject({
      segno: "?",
      titolo: "Prima previsione in arrivo",
      riprova: false,
    })
    expect(
      mancanzaDelMeteo(
        meteo({ fetched_at: null, last_request: { at: "2026-09-30T16:05:00.000Z", status: "ok" } }),
      )?.titolo,
    ).toBe("Prima previsione in arrivo")
    const giu = mancanzaDelMeteo(
      meteo({
        fetched_at: null,
        last_request: { at: "2026-09-30T16:05:00.000Z", status: "error" },
        retry_s: 1800,
      }),
    )
    expect(giu).toMatchObject({ segno: "!", titolo: "Meteo non raggiungibile", riprova: true })
    expect(giu?.testo).toMatch(
      /^Open-Meteo non risponde dalle \d\d:\d\d\. Nuovo tentativo ogni 30 minuti;/,
    )
    expect(mancanzaDelMeteo(meteo({ nights: [], retry_s: 600 }))?.testo).toMatch(
      /^Open-Meteo non risponde\. Nuovo tentativo ogni 10 minuti;/,
    )
    expect(mancanzaDelMeteo(meteo({}))).toBeNull()
  })

  it("senza previsione le sei carte sono i riquadri vuoti, coi loro nomi", async () => {
    await montaDashboard({ previsione: { fetched_at: null, nights: [] } })
    expect(await screen.findByText("Prima previsione in arrivo")).toBeDefined()
    expect(screen.getByText("Nessuna previsione ancora")).toBeDefined()
    const vuote = [...document.querySelectorAll(".al-c-card-meteo__colonna-8")].map(
      (c) => c.firstElementChild?.textContent,
    )
    expect(vuote).toEqual(["Nuvole", "Seeing", "Jet stream", "Vento", "Condensa", "Aerosol"])
    expect(screen.queryByText("Le prossime 3 notti")).toBeNull()
  })

  it("una previsione vecchia dice l'ultima valida", async () => {
    await montaDashboard({
      previsione: { last_request: { at: "2026-09-30T17:05:00.000Z", status: "error" }, nights: [] },
    })
    expect(await screen.findByText(/^Ultima previsione valida: 30 settembre/)).toBeDefined()
    expect(screen.getByRole("button", { name: "Riprova ora" })).toBeDefined()
  })

  it("senza fuso lo dice in testa", async () => {
    await montaDashboard({ previsione: { missing: "no_timezone" } })
    expect(await screen.findByText("Serve il fuso orario del sito")).toBeDefined()
  })
})

describe("le sei carte", () => {
  const ORE = [
    ora(H("12:00"), "day", { shown: false, cloud_total_pct: 99 }),
    ora(H("19:00"), "civil", { cloud_total_pct: 50 }),
    ora(H("21:00"), "dark", { cloud_total_pct: null, levels: { ...GIUDIZI, cloud: "nogo" } }),
    ora(H("23:00"), "dark", { cloud_total_pct: 150, levels: { ...GIUDIZI, cloud: "marginal" } }),
    ora(D("01:00"), "dark", { cloud_total_pct: -20, levels: { ...GIUDIZI, cloud: null } }),
    ora(D("03:00"), "dark", { cloud_total_pct: 20 }),
  ]

  it("le barre sono le ore mostrate: dal quarto in su, col colore del giudizio solo nel buio", async () => {
    await montaDashboard({ previsione: { nights: [{ ...NOTTE, hours: ORE }] } })
    await screen.findByText("Meteo della notte")
    const c = carta("Nuvole")
    expect(c.valore).toBe("40")
    expect(c.unita).toBe("%")
    expect(c.altezze).toEqual(["62.5%", "25%", "100%", "25%", "40%"])
    expect(c.colori).toEqual([
      "var(--barretta-spenta)",
      "var(--non-adatto-testo)",
      "var(--incerto-testo)",
      "var(--barretta-spenta)",
      "var(--buono-testo)",
    ])
    expect(c.nota).toBe("media nel buio \u00b7 picco 80% tra le 22:00 e le 23:00")
    expect(c.testo).toContain("incerta")
  })

  it("il seeing senza chiave con un jet forte e' la stima di Meteoblue", async () => {
    await montaDashboard({
      previsione: {
        nights: [
          {
            ...NOTTE,
            measures: [
              ...NOTTE.measures.filter((m) => m.code !== "jet"),
              misura("jet", { level: "nogo", value: 150, axis_max: 200 }),
            ],
          },
        ],
      },
    })
    await screen.findByText("Meteo della notte")
    const c = carta("Seeing")
    expect(c.valore).toBe("scarso")
    expect(c.nota).toBe("stima dal vento in quota \u00b7 serve una chiave Meteoblue")
    expect(c.testo).toContain("stima")
  })

  it("una chiave rifiutata lo dice, e senza jet forte il seeing non c'e'", async () => {
    await montaDashboard({
      previsione: { seeing: { key: true, source: "meteoblue", meteoblue: "refused" } },
    })
    await screen.findByText("Meteo della notte")
    const c = carta("Seeing")
    expect(c.valore).toBe("?")
    expect(c.nota).toBe("chiave Meteoblue non valida: controllala nelle Impostazioni")
    expect(c.testo).toContain("Non disponibile")
  })

  it("sotto un cielo coperto seeing e aerosol non si misurano; il resto senza ore non c'e'", async () => {
    const coperto = [
      misura("cloud", { level: "nogo", value: 96 }),
      misura("seeing", { known_hours: 0 }),
      misura("aerosol", { known_hours: 0 }),
      misura("jet", { known_hours: 0 }),
    ]
    await montaDashboard({
      previsione: {
        seeing: { key: true, source: "meteoblue", meteoblue: "ok" },
        nights: [{ ...NOTTE, measures: coperto }],
      },
    })
    await screen.findByText("Meteo della notte")
    expect(carta("Seeing").testo).toContain("non si misura")
    expect(carta("Aerosol").testo).toContain("non si misura")
    expect(carta("Jet stream").testo).toContain("Non disponibile")
    expect(carta("Vento").testo).toContain("Non disponibile")
  })

  it("un valore che manca e' un punto di domanda; un giudizio senza soglie non c'e'", async () => {
    const misure = [
      ...NOTTE.measures.filter((m) => m.code !== "jet" && m.code !== "aerosol"),
      misura("jet", { level: null, value: null }),
      misura("aerosol", { level: null, value: 0.14, axis_max: 0.2 }),
    ]
    await montaDashboard({
      previsione: {
        nights: [{ ...NOTTE, measures: misure }],
        scales: [
          SCALA_DELLA_LUNA,
          {
            code: "aerosol",
            steps: [{ level: "nogo", bound: 1, strict: false }],
            lower_is_worse: false,
          },
        ],
      },
    })
    await screen.findByText("Meteo della notte")
    expect(carta("Jet stream").valore).toBe("?")
    expect(carta("Jet stream").testo).toContain("Non disponibile")
    expect(carta("Aerosol").testo).toContain("Non disponibile")
    expect(carta("Aerosol").unita).toBe("")
  })

  it("sul telefono le carte sono piccole, senza nota", async () => {
    await montaDashboard({ larga: 390 })
    await screen.findByText("Meteo della notte")
    const c = carta("Nuvole")
    expect(c.valore).toBe("40")
    expect(c.unita).toBe("%")
    expect(c.nota).toBe("")
  })
})

describe("la curva delle prossime notti", () => {
  const curve = () => [...document.querySelectorAll("svg[viewBox='0 0 1000 48']")]

  it("la trasparenza ora per ora al centro della sua ora, le fasce del cielo e i confini del buio", async () => {
    await montaDashboard()
    await screen.findByText("Le prossime 3 notti")
    const [prima] = curve()
    const tracce = [...(prima?.querySelectorAll("path") ?? [])]
    expect(tracce[1]?.getAttribute("d")).toBe("M166.7 20.8 L500.0 11.6 L833.3 14.9")
    expect(tracce[0]?.getAttribute("d")).toMatch(
      /^M166\.66\d* 46 L166\.7 20\.8 L500\.0 11\.6 L833\.3 14\.9 L833\.33\d* 46 Z$/,
    )
    expect(tracce[0]?.getAttribute("fill")).toBe("url(#dash-mq-2026-10-01)")
    const rett = [...(prima?.querySelectorAll("rect") ?? [])] as SVGElement[]
    expect(rett.map((r) => r.style.fillOpacity)).toEqual([
      "var(--banda-1)",
      "var(--banda-4)",
      "var(--banda-4)",
    ])
    expect(rett.map((r) => Number(r.getAttribute("x")).toFixed(1))).toEqual([
      "0.0",
      "333.3",
      "666.7",
    ])
    const confini = [...(prima?.querySelectorAll("line") ?? [])].map((l) =>
      Number(l.getAttribute("x1")).toFixed(1),
    )
    expect(confini).toEqual(["333.3", "1000.0"])
    const ore = [...(prima?.parentElement?.nextElementSibling?.children ?? [])] as HTMLElement[]
    expect(ore.map((o) => [o.textContent, o.style.left, o.style.transform])).toEqual([
      ["19", "0%", "none"],
      ["23", "100%", "translateX(-100%)"],
    ])
    expect(document.body.textContent).toContain("trasparenza media nel buio 78/100")
    expect(document.body.textContent).toContain("3 h di buio senza Luna")
  })

  it("la mezzanotte sta al suo posto; un'ora sola non fa curva", async () => {
    const ore = [
      ora(H("22:00"), "nautical", { transparency: 40 }),
      ora(D("00:00"), "dark", { transparency: null }),
      ora(D("02:00"), "dark", { transparency: 70 }),
      ora(D("04:00"), "astronomical"),
    ]
    await montaDashboard({
      previsione: {
        nights: [
          NOTTE,
          { ...PROSSIME[0], hours: ore, transparency: null, moonless_dark_hours: null },
          { ...PROSSIME[1], hours: [ora(D("23:00"), "dark", { transparency: 50 })] },
          PROSSIME[2],
        ],
      },
    })
    await screen.findByText("Le prossime 3 notti")
    const [prima, seconda] = curve()
    const etichette = [
      ...(prima?.parentElement?.nextElementSibling?.children ?? []),
    ] as HTMLElement[]
    expect(etichette.map((o) => [o.textContent, o.style.left, o.style.transform])).toEqual([
      ["22", "0%", "none"],
      ["00", "25%", "translateX(-50%)"],
      ["04", "100%", "translateX(-100%)"],
    ])
    expect(prima?.querySelectorAll("path")[1]?.getAttribute("d")).toBe("M125.0 29.2 L625.0 16.6")
    expect(
      [...(prima?.querySelectorAll("line") ?? [])].map((l) =>
        Number(l.getAttribute("x1")).toFixed(1),
      ),
    ).toEqual(["250.0", "750.0"])
    expect(seconda?.querySelectorAll("path")).toHaveLength(0)
    expect(curve()).toHaveLength(2)
  })

  it("sul telefono con due notti dopo la prima: l'altra, e si richiude", async () => {
    await montaDashboard({ larga: 390, previsione: { nights: [NOTTE, PROSSIME[0], PROSSIME[1]] } })
    const piu = await screen.findByRole("button", { name: /L'altra notte/ })
    expect(piu.getAttribute("aria-expanded")).toBe("false")
    fireEvent.click(piu)
    expect(await screen.findByText("Venerdì 2")).toBeDefined()
    const meno = screen.getByRole("button", { name: /Mostra meno/ })
    expect(meno.getAttribute("aria-expanded")).toBe("true")
    fireEvent.click(meno)
    expect(screen.queryByText("Venerdì 2")).toBeNull()
  })

  it("sul telefono con una notte sola niente bottone", async () => {
    await montaDashboard({ larga: 390, previsione: { nights: [NOTTE, PROSSIME[0]] } })
    expect(await screen.findByText("Giovedì 1")).toBeDefined()
    expect(screen.queryByRole("button", { name: /altr/ })).toBeNull()
  })
})
