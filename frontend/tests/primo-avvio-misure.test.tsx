// @vitest-environment jsdom
/**
 * Il primo avvio porta le misure della tavola v82 (`Primo avvio.dc.html`, `L` e `sg`) col suo
 * `style=`: la cornice, i segni delle tappe, la pastiglia di ASTAP, l'attesa. Le classi e i testi
 * stanno in `wizard.test.tsx`; qui cio' che il foglio non porta e il componente si'.
 */
import { fireEvent, screen } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import {
  SALUTE,
  SPINA,
  STANOTTE,
  type Voce,
  disegna,
  impostazioni,
  pulisci,
  rispondi,
} from "./banco"

afterEach(pulisci)

function primoAvvio(manca: string[] = [], extra: Record<string, Voce> = {}) {
  rispondi({
    ...STANOTTE,
    "GET /api/v1/folders/path-info": { stato: 200, corpo: { family: "windows", data_root: null } },
    "GET /api/v1/folders": { stato: 200, corpo: { items: [], total: 0 } },
    "/api/v1/settings/wizard-done": { stato: 200, corpo: impostazioni(true) },
    "/api/v1/settings": { stato: 200, corpo: { ...impostazioni(false), missing: manca } },
    "/api/health": { stato: 200, corpo: SALUTE },
    "/api/v1/review": { stato: 200, corpo: { to_confirm: 0 } },
    ...SPINA,
    // per ultime: una voce gia' dichiarata sopra la sostituisce restando al suo posto
    ...extra,
  })
}

const stile = (selettore: string) => document.querySelector<HTMLElement>(selettore)!.style
const avanti = () => fireEvent.click(screen.getByRole("button", { name: /avanti/i }))

describe("la cornice del primo avvio con le misure della tavola", () => {
  it.each([
    [
      "desktop",
      "/",
      {
        largo: "1160px",
        dentro: "64px 40px 80px",
        colonne: "300px minmax(0px, 1fr)",
        stacco: "56px",
        posizione: "sticky",
        staccoLato: "28px",
        titolo: "34px",
        angolo: "28px",
        dentroCarta: "32px",
        titoloPasso: "28px",
      },
    ],
    [
      "telefono",
      "/?formato=telefono",
      {
        largo: "none",
        dentro: "20px 16px 28px",
        colonne: "minmax(0px, 1fr)",
        stacco: "18px",
        posizione: "static",
        staccoLato: "16px",
        titolo: "24px",
        angolo: "24px",
        dentroCarta: "20px",
        titoloPasso: "24px",
      },
    ],
  ])("%s", async (_, indirizzo, m) => {
    window.history.pushState({}, "", indirizzo)
    primoAvvio()
    await disegna()
    await screen.findAllByRole("button", { name: /salta/i })
    const pagina = stile("main.al-avvio__centro-1")
    expect([pagina.maxWidth, pagina.padding, pagina.gridTemplateColumns, pagina.gap]).toEqual([
      m.largo,
      m.dentro,
      m.colonne,
      m.stacco,
    ])
    const lato = stile(".al-avvio__colonna-2")
    expect([lato.position, lato.gap]).toEqual([m.posizione, m.staccoLato])
    expect(stile("h1.al-avvio__testo-1").fontSize).toBe(m.titolo)
    const carta = stile("section.al-avvio__colonna-8")
    expect([carta.borderRadius, carta.padding]).toEqual([m.angolo, m.dentroCarta])
    expect(stile("h2.al-avvio__riga-4").fontSize).toBe(m.titoloPasso)
    expect(document.querySelector(".al-avvio__colonna-1")?.getAttribute("data-screen-label")).toBe(
      "Primo avvio",
    )
  })

  it("mentre legge le impostazioni l'attesa ha la forma della tavola (`appSk`)", async () => {
    primoAvvio([], {
      "/api/v1/settings": { stato: 200, corpo: impostazioni(false), attesa: new Promise(() => {}) },
    })
    await disegna()
    const cornice = document.querySelector<HTMLElement>(".al-avvio__colonna-1 > div")!.style
    expect([
      cornice.maxWidth,
      cornice.width,
      cornice.margin,
      cornice.padding,
      cornice.boxSizing,
    ]).toEqual(["1160px", "100%", "0px auto", "64px 40px 80px", "border-box"])
    const carte = [...document.querySelectorAll<HTMLElement>(".al-c-scheletro__blocco-4")]
    expect(carte.map((c) => c.style.height)).toEqual(["120px", "280px"])
    const primi = carte.map((c) => c.querySelector<HTMLElement>(".al-c-scheletro__blocco-3")!.style)
    expect(primi.map((s) => [s.height, s.width])).toEqual([
      ["32px", "50%"],
      ["28px", "40%"],
    ])
    expect(carte[0]?.textContent).toBe("Leggo le impostazioni…")
    expect(carte[1]?.querySelectorAll(".al-c-scheletro__blocco-3")).toHaveLength(2)
  })

  it("se le impostazioni non rispondono l'avviso sta nella stessa cornice", async () => {
    primoAvvio([], { "/api/v1/settings": { stato: 500, corpo: {} } })
    await disegna()
    await screen.findByText("AstroLog non risponde, riprova")
    const cornice = document.querySelector<HTMLElement>(".al-avvio__colonna-1 > div")!.style
    expect([cornice.maxWidth, cornice.width, cornice.margin, cornice.boxSizing]).toEqual([
      "1160px",
      "100%",
      "0px auto",
      "border-box",
    ])
  })
})

describe("i segni delle tappe (`sg`)", () => {
  const tondi = () =>
    [...document.querySelectorAll<HTMLElement>(".al-avvio__riga-1 .al-avvio__tondo-1")].map((s) => [
      s.textContent,
      s.style.background,
      s.style.color,
      s.style.border,
    ])

  it("ora, dopo, fatto e saltato hanno fondo, colore e bordo loro", async () => {
    primoAvvio([], { "PATCH /api/v1/settings": { stato: 200, corpo: impostazioni(false) } })
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    expect(tondi().slice(0, 2)).toEqual([
      ["1", "var(--accento)", "var(--scelta-testo)", "1.5px solid transparent"],
      ["2", "none", "var(--tenue)", "1.5px solid var(--linea)"],
    ])
    fireEvent.change(screen.getByLabelText(/^nome$/i), { target: { value: "Ada" } })
    avanti()
    await screen.findByRole("region", { name: "Sito di osservazione" })
    avanti()
    await screen.findByRole("region", { name: "Tema" })
    expect(tondi().slice(0, 3)).toEqual([
      ["\u2713", "var(--buono-fondo)", "var(--buono-testo)", "1.5px solid transparent"],
      ["\u2013", "none", "var(--tenue)", "1.5px dashed var(--tenue)"],
      ["3", "var(--accento)", "var(--scelta-testo)", "1.5px solid transparent"],
    ])
  })

  it("il passo di adesso ha il fondo della carta e il nome in grassetto; quelli dopo sono tenui", async () => {
    primoAvvio()
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    const voci = [...document.querySelectorAll<HTMLElement>(".al-avvio__riga-1")]
    expect(voci.map((v) => v.style.background)).toEqual(["var(--carta)", ...Array(4).fill("none")])
    const nomi = voci.map((v) => v.querySelector<HTMLElement>(".al-avvio__testo-3")!.style)
    expect(nomi.map((s) => [s.fontWeight, s.color])).toEqual([
      ["600", "var(--testo)"],
      ...Array(4).fill(["400", "var(--tenue)"]),
    ])
    avanti()
    const nome = document.querySelector<HTMLElement>(".al-avvio__riga-1 .al-avvio__testo-3")!.style
    expect([nome.fontWeight, nome.color]).toEqual(["400", "var(--testo)"])
    expect(document.querySelector("ol.al-avvio__colonna-5")?.getAttribute("aria-label")).toBe(
      "I passi del primo avvio",
    )
  })

  it("sul telefono i cerchi dicono il passo di adesso, e solo il primo non allunga il filo", async () => {
    window.history.pushState({}, "", "/?formato=telefono")
    primoAvvio()
    await disegna()
    await screen.findAllByRole("button", { name: /salta/i })
    const lista = document.querySelector("ol.al-avvio__riga-2")!
    expect(lista.getAttribute("aria-label")).toBe("I passi del primo avvio")
    const cerchi = [...lista.querySelectorAll<HTMLElement>(":scope > li")]
    expect(cerchi.map((c) => c.getAttribute("aria-current"))).toEqual([
      "step",
      null,
      null,
      null,
      null,
    ])
    expect(cerchi.map((c) => c.style.flex)).toEqual([
      "0 0 auto",
      "1 1 0%",
      "1 1 0%",
      "1 1 0%",
      "1 1 0%",
    ])
    expect(cerchi.map((c) => c.querySelector(".al-avvio__tondo-2")?.textContent)).toEqual([
      "1",
      "2",
      "3",
      "4",
      "5",
    ])
  })
})

describe("la pastiglia di ASTAP e i comandi", () => {
  async function alSolver(extra: Record<string, Voce> = {}) {
    primoAvvio(["no_solver"], extra)
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    for (let i = 0; i < 5; i++) avanti()
  }

  it("non trovato: la pastiglia ha i colori dell'incerto", async () => {
    await alSolver()
    const p = stile("h2.al-avvio__riga-4 > .al-avvio__pillola-1")
    expect([p.background, p.color]).toEqual(["var(--incerto-fondo)", "var(--incerto-testo)"])
  })

  it("trovato: la pastiglia ha i colori del buono, e mentre verifica il comando gira e non riparte", async () => {
    let lascia: (v?: unknown) => void = () => {}
    await alSolver({
      "PATCH /api/v1/settings": {
        stato: 200,
        corpo: { ...impostazioni(false), missing: [] },
        attesa: new Promise((r) => (lascia = r)),
      },
    })
    fireEvent.change(screen.getByLabelText(/percorso di astap/i), {
      target: { value: "C:/astap/astap_cli.exe" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^verifica percorso$/i }))
    const occupato = await screen.findByRole("button", { name: "Verifica\u2026" })
    expect(occupato.getAttribute("aria-busy")).toBe("true")
    expect(occupato.querySelector(".al-avvio__tondo-3[aria-hidden=true]")).not.toBeNull()
    lascia()
    await screen.findByText("ASTAP trovato")
    const p = stile("h2.al-avvio__riga-4 > .al-avvio__pillola-1")
    expect([p.background, p.color]).toEqual(["var(--buono-fondo)", "var(--buono-testo)"])
    expect(
      screen.getByRole("button", { name: /^verifica percorso$/i }).getAttribute("aria-busy"),
    ).toBeNull()
  })

  it("un comando spento non fa niente: Verifica e salva vuoto al passo Seeing", async () => {
    primoAvvio()
    await disegna()
    await screen.findByRole("button", { name: /salta/i })
    for (let i = 0; i < 4; i++) avanti()
    const salva = screen.getByRole("button", { name: /^verifica e salva$/i })
    expect(salva.getAttribute("aria-busy")).toBeNull()
    expect(salva.querySelector(".al-avvio__tondo-3")).toBeNull()
  })
})
