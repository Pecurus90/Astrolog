// @vitest-environment jsdom
/**
 * The six v76 bricks of the Nights page (Striscia, CalendarioNotti, Filtri, BarraFiltri, Ripresa,
 * Luna): delivery classes, words from t(), roles and aria. Colour is not tested: jsdom has no cascade.
 */
import { fireEvent, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { BarraFiltri } from "../src/componenti/BarraFiltri"
import { CalendarioNotti } from "../src/componenti/CalendarioNotti"
import { Filtri } from "../src/componenti/Filtri"
import { Luna } from "../src/componenti/Luna"
import { Ripresa } from "../src/componenti/Ripresa"
import { Striscia } from "../src/componenti/Striscia"
import { t } from "../src/i18n"
import { pulisci } from "./banco"

afterEach(pulisci)

describe("Ripresa", () => {
  it("says the shooting in words, the sign hidden", () => {
    render(<Ripresa tipo="larga" testo="Tutta la notte banda larga" />)
    const ripresa = screen.getByRole("img")
    expect(ripresa.className).toBe("al-c-ripresa__riga-1")
    expect(ripresa.getAttribute("aria-label")).toBe("Ripresa: Tutta la notte banda larga")
    expect(ripresa.querySelector('[aria-hidden="true"]')?.querySelectorAll("svg")).toHaveLength(1)
    expect(ripresa.querySelector(".al-c-ripresa__blocco-1")?.textContent).toBe(
      "Tutta la notte banda larga",
    )
  })

  it("mixed draws both signs, narrow only the narrow one", () => {
    const { container, rerender } = render(<Ripresa tipo="mista" testo="x" />)
    expect(container.querySelectorAll("svg")).toHaveLength(2)
    rerender(<Ripresa tipo="stretta" testo="x" />)
    expect(container.querySelectorAll("svg rect")).toHaveLength(2)
  })
})

describe("Luna", () => {
  it("draws the lit limb on the side the app sends", () => {
    const { container, rerender } = render(<Luna percento={60} lato="destra" />)
    expect(container.querySelector("path")?.getAttribute("d")).toBe(
      "M 0 -10 A 10 10 0 0 1 0 10 A 2.00 10 0 0 1 0 -10 Z",
    )
    rerender(<Luna percento={60} lato="sinistra" />)
    expect(container.querySelector("path")?.getAttribute("d")).toContain("A 10 10 0 0 0 0 10")
  })

  it("names the fraction, with the elided article, and the title first", () => {
    render(<Luna percento={83} lato="destra" titolo="Luna 83%" testo="sorge 21:40" misura={30} />)
    const disco = screen.getByRole("img")
    expect(disco.getAttribute("aria-label")).toBe("Luna 83%, Luna illuminata all'83%")
    expect(disco.getAttribute("width")).toBe("30")
    expect(disco.getAttribute("viewBox")).toBe("-12 -12 24 24")
    expect(document.querySelector(".al-c-luna__testo-1")?.textContent).toBe("Luna 83%")
    expect(document.querySelector(".al-c-luna__testo-2")?.textContent).toBe("sorge 21:40")
  })

  it("a new Moon keeps the dark disc and draws nothing lit", () => {
    const { container } = render(<Luna percento={0} lato="destra" misura={22} />)
    expect(container.querySelector("circle")).not.toBeNull()
    expect(container.querySelector("path")).toBeNull()
    expect(container.querySelector(".al-c-luna__riga-1")).toBeNull()
  })
})

describe("BarraFiltri", () => {
  const filtri = [
    { banda: "HA", nome: "Ha 3nm", frame: 70, secondi: 8280, peso: 8280 },
    { banda: "MISTERO", nome: "Boh", frame: 1, secondi: null, peso: 1 },
  ]

  it("colours by passband, an unknown one dashed, and says it all to who listens", () => {
    render(<BarraFiltri filtri={filtri} />)
    const barra = screen.getByRole("img")
    expect(barra.className).toBe("al-c-barra-filtri__riga-2")
    expect(barra.style.height).toBe("12px")
    expect(barra.getAttribute("aria-label")).toBe("Filtri: Ha 3nm 2 h 18, Boh senza durata")
    const pezzi = barra.querySelectorAll(".al-c-barra-filtri__blocco-2")
    expect(pezzi[0]?.classList.contains("as-filtro--ha")).toBe(true)
    expect(pezzi[1]?.classList.contains("as-filtro--ignoto")).toBe(true)
    expect((pezzi[0] as HTMLElement).style.flexGrow).toBe("8280")
    expect(document.querySelector(".al-c-barra-filtri__centro-1")).toBeNull()
  })

  it("with rows, a line per filter; animated, the growing bar", () => {
    render(<BarraFiltri filtri={filtri} righe anima altezza={8} />)
    const barra = screen.getByRole("img")
    expect(barra.className).toBe("al-c-barra-filtri__riga-1")
    expect(barra.dataset["an"]).toBe("barra")
    expect(barra.style.height).toBe("8px")
    const righe = document.querySelectorAll(".al-c-barra-filtri__centro-1")
    expect(righe).toHaveLength(2)
    expect(righe[0]?.textContent).toBe("Ha 3nm70 frame2 h 18")
    expect(righe[1]?.textContent).toBe("Boh1 framesenza durata")
  })
})

describe("Filtri", () => {
  it("the button says how many criteria are on, and whether it is open", () => {
    const apri = vi.fn()
    render(<Filtri parte="bottone" attivi={2} aperto onApri={apri} formato="telefono" />)
    const bottone = screen.getByText(t("ui.filters.criteria")).closest("a") as HTMLElement
    expect(bottone.className).toBe("al-c-filtri__riga-1")
    expect(bottone.getAttribute("aria-expanded")).toBe("true")
    expect(bottone.style.minHeight).toBe("44px")
    expect(bottone.querySelector(".al-c-filtri__pillola-1")?.textContent).toBe("2")
    expect(bottone.querySelector('[aria-hidden="true"]')?.textContent).toBe("\u25B4")
    fireEvent.click(bottone)
    expect(apri).toHaveBeenCalledOnce()
  })

  it("clear shows only with criteria on", () => {
    const togli = vi.fn()
    const { rerender } = render(<Filtri parte="togli" attivi={0} onTogli={togli} />)
    expect(screen.queryByText("Togli i criteri")).toBeNull()
    rerender(<Filtri parte="togli" attivi={1} onTogli={togli} />)
    const link = screen.getByText("Togli i criteri")
    expect(link.className).toBe("al-c-filtri__riga-3")
    fireEvent.click(link)
    expect(togli).toHaveBeenCalledOnce()
  })

  it("the body holds field and named groups, and on the phone the show button", () => {
    const cerca = vi.fn()
    const mostra = vi.fn()
    render(
      <Filtri
        gruppi={[{ l: "Anno", opz: [{ l: "2026", c: "11", sel: true }] }]}
        campo="per esempio M 31 o Velo"
        q="M 3"
        onCerca={cerca}
        attivi={1}
        mostra="Mostra 6 notti"
        onMostra={mostra}
        formato="telefono"
      />,
    )
    const campo = screen.getByLabelText("oggetto")
    expect(campo.getAttribute("placeholder")).toBe("per esempio M 31 o Velo")
    fireEvent.change(campo, { target: { value: "M 31" } })
    expect(cerca).toHaveBeenCalledWith("M 31")
    const gruppo = screen.getAllByRole("group", { name: "Anno" })[0] as HTMLElement
    expect(gruppo.className).toBe("al-c-filtri__colonna-3")
    expect(screen.getByText("2026").getAttribute("aria-pressed")).toBe("true")
    fireEvent.click(screen.getByText("Mostra 6 notti"))
    expect(mostra).toHaveBeenCalledOnce()
    expect(screen.getByText("Togli i criteri").className).toContain("al-bottone--testo")
    expect(document.querySelector(".al-c-filtri__blocco-1")?.getAttribute("data-formato")).toBe(
      "telefono",
    )
  })

  it("on desktop there is no show button, and no field without a placeholder", () => {
    render(<Filtri gruppi={[]} mostra="Mostra 6 notti" colonne={3} />)
    expect(screen.queryByText("Mostra 6 notti")).toBeNull()
    expect(screen.queryByRole("textbox")).toBeNull()
    const griglia = document.querySelector(".al-c-filtri__centro-1") as HTMLElement
    expect(griglia.style.gridTemplateColumns).toBe("repeat(3, minmax(0px, 1fr))")
  })
})

describe("CalendarioNotti", () => {
  it("lays September 2026 from Tuesday, with the month as title and weekdays from t()", () => {
    render(<CalendarioNotti anno={2026} mese={8} />)
    expect(screen.getByText("Settembre 2026").className).toBe("al-c-calendario-notti__testo-1")
    const intestazioni = document.querySelectorAll(".al-c-calendario-notti__testo-6")
    expect([...intestazioni].map((d) => d.textContent)).toEqual([
      "lu",
      "ma",
      "me",
      "gi",
      "ve",
      "sa",
      "do",
    ])
    const celle = document.querySelectorAll(".al-c-calendario-notti__colonna-4")
    // 1 September 2026 is a Tuesday: one blank, then 30 days
    expect(celle).toHaveLength(31)
    expect((celle[0] as HTMLElement).style.visibility).toBe("hidden")
    expect(celle[1]?.textContent).toBe("1")
  })

  it("a day with nights is a button with its signs, coloured by the app's outcome", () => {
    const scegli = vi.fn()
    render(
      <CalendarioNotti
        anno={2026}
        mese={8}
        giorni={[
          { d: 16, esiti: [2, -1], esito: 2, aria: "16 settembre: non adatta" },
          { d: 24, esiti: [0], esito: 0, sel: true, on: scegli },
        ]}
      />,
    )
    const sedici = screen.getByRole("button", { name: "16 settembre: non adatta" })
    expect(sedici.getAttribute("aria-pressed")).toBe("false")
    expect(sedici.querySelector(".al-c-calendario-notti__blocco-2")?.textContent).toBe("\u2715?")
    expect(sedici.style.background).toBe("var(--non-adatto-fondo)")
    const ventiquattro = screen.getByRole("button", { pressed: true })
    expect(ventiquattro.style.background).toBe("var(--scelta)")
    fireEvent.click(ventiquattro)
    expect(scegli).toHaveBeenCalledOnce()
  })

  it("in the current month the grid stops at today's week, and today is said", () => {
    // 16 September 2026 is a Wednesday: the week ends on Sunday 20
    render(<CalendarioNotti anno={2026} mese={8} oggi={16} />)
    const celle = document.querySelectorAll(".al-c-calendario-notti__colonna-4")
    expect(celle).toHaveLength(1 + 20)
    expect((celle[17] as HTMLElement).style.visibility).toBe("hidden")
    expect(screen.getByText("16 settembre, oggi").className).toBe("al-solo-voce")
  })

  it("the arrows go back and forth, and a closed one does not answer", () => {
    const prima = vi.fn()
    const dopo = vi.fn()
    render(
      <CalendarioNotti
        anno={2026}
        mese={8}
        onPrima={prima}
        onDopo={dopo}
        dopoNo
        formato="telefono"
      />,
    )
    const indietro = screen.getByLabelText("Mese prima")
    expect(indietro.style.width).toBe("44px")
    fireEvent.click(indietro)
    expect(prima).toHaveBeenCalledOnce()
    const avanti = screen.getByLabelText("Mese dopo")
    expect(avanti.getAttribute("aria-disabled")).toBe("true")
    fireEvent.click(avanti)
    expect(dopo).not.toHaveBeenCalled()
  })

  it("the legend gives the four outcomes, and the big number when sent", () => {
    render(<CalendarioNotti anno={2026} mese={8} numero="31" numeroL="ore" conta="6 notti" />)
    const legenda = document.querySelector(".al-c-calendario-notti__riga-3") as HTMLElement
    expect([...legenda.children].map((v) => v.textContent)).toEqual([
      "\u2713buona",
      "!incerta",
      "\u2715non adatta",
      "?senza meteo",
    ])
    expect(screen.getByText("31").className).toBe("al-c-calendario-notti__testo-3")
    expect(screen.getByText("6 notti").className).toBe("al-c-calendario-notti__testo-5")
  })
})

describe("Striscia", () => {
  const notti = [
    {
      day: "mer 30",
      tag: "settembre",
      tagS: "set",
      esito: 0 as const,
      hours: "9 h",
      range: "Cima Ekar",
      rip: { tipo: "larga" as const, testo: "Tutta la notte banda larga" },
      cells: [
        { h: 30, esito: null },
        { h: 60, esito: 0 as const },
      ],
    },
    {
      day: "gio 1",
      esito: "ignoto" as const,
      pillT: "in arrivo",
      hours: "4 h",
      range: "x",
      sel: true,
    },
  ]

  it("on desktop, a tab per night with pill, shooting, hours and spark cells", () => {
    const scegli = vi.fn()
    render(<Striscia notti={notti.map((n) => ({ ...n, on: scegli }))} etichetta="Le notti" />)
    const lista = screen.getByRole("tablist", { name: "Le notti" })
    expect(lista.className).toBe("al-c-striscia__blocco-2")
    expect(lista.style.gridTemplateColumns).toBe("repeat(2, minmax(0px, 1fr))")
    // v78: under 1000 px the sheet keeps 150 px tiles from --n and scrolls inside the card
    expect(lista.style.getPropertyValue("--n")).toBe("2")
    expect(lista.querySelector(".al-c-striscia__testo-4")?.getAttribute("title")).toBe("Cima Ekar")
    const schede = screen.getAllByRole("tab")
    expect(schede[0]?.className).toBe("al-c-striscia__colonna-1")
    expect(schede[0]?.getAttribute("aria-selected")).toBe("false")
    expect(schede[1]?.getAttribute("aria-selected")).toBe("true")
    expect(schede[1]?.style.boxShadow).toBe("inset 0 0 0 2px var(--accento)")
    expect(schede[0]?.querySelector(".al-c-striscia__testo-1")?.textContent).toBe("mer 30")
    expect(schede[0]?.querySelector(".al-c-striscia__testo-2")?.textContent).toBe("settembre")
    expect(schede[0]?.querySelector(".al-pillola--piccola")?.textContent).toBe("\u2713 buona")
    expect(schede[1]?.querySelector(".al-pillola--mancante")?.textContent).toBe("? in arrivo")
    expect(screen.getByRole("img", { name: "Ripresa: Tutta la notte banda larga" })).toBeTruthy()
    const celle = schede[0]?.querySelectorAll(".al-c-striscia__pillola-1") ?? []
    expect((celle[0] as HTMLElement).style.background).toBe("var(--barretta-spenta)")
    expect((celle[1] as HTMLElement).style.height).toBe("60%")
    fireEvent.click(schede[0] as HTMLElement)
    expect(scegli).toHaveBeenCalledOnce()
  })

  it("a trend night not chosen is dashed and bare", () => {
    render(<Striscia notti={[{ ...notti[0]!, tend: true }]} />)
    const scheda = screen.getByRole("tab")
    expect(scheda.style.backgroundColor).toBe("transparent")
    expect(scheda.style.border).toBe("1.5px dashed var(--linea)")
    expect(screen.getByRole("tablist").getAttribute("aria-label")).toBe("le sette notti")
  })

  it("on the phone, the scrolling row with the short tag and the micro pill", () => {
    render(<Striscia notti={notti} formato="telefono" rientro={16} />)
    const lista = screen.getByRole("tablist")
    expect(lista.className).toBe("al-c-striscia__riga-3")
    expect(lista.style.padding).toBe("0px 16px 2px")
    const scheda = screen.getAllByRole("tab")[0] as HTMLElement
    expect(scheda.className).toBe("al-c-striscia__colonna-3")
    expect(scheda.querySelector(".al-c-striscia__testo-6")?.textContent).toBe("set")
    expect(scheda.querySelector(".al-pillola--micro")).not.toBeNull()
    expect(scheda.querySelector(".al-c-striscia__blocco-4 .al-c-ripresa__riga-1")).not.toBeNull()
    expect(scheda.querySelector(".al-c-striscia__testo-7")?.textContent).toBe("9 h")
  })

  it("more than eight nights on desktop scroll instead of squeezing", () => {
    const molte = Array.from({ length: 9 }, (_, i) => ({ ...notti[0]!, day: `g ${i}` }))
    render(<Striscia notti={molte} />)
    const lista = screen.getByRole("tablist")
    expect(lista.style.display).toBe("flex")
    expect(lista.style.overflowX).toBe("auto")
    expect((screen.getAllByRole("tab")[0] as HTMLElement).style.width).toBe("164px")
  })
})
