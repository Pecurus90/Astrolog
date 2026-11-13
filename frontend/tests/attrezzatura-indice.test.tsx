// @vitest-environment jsdom
/**
 * L'indice della pagina **Attrezzatura** (tavola v82), da solo: i setup a carte e i componenti a
 * pillole. Cosa si apre per primo, cosa resta scelto quando la pagina cambia, cosa dice ogni carta.
 */
import { fireEvent, render, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import type { components } from "../src/api/schema"
import { Indice, esiste, gruppiDi, primaScelta } from "../src/AttrezzaturaIndice"
import { CORREDO, FILTRO, MONTATURA, OTTICA } from "./attrezzatura-banco"
import { pulisci } from "./banco"

type Pagina = components["schemas"]["GearList"]

afterEach(pulisci)

const ALTRO = { ...CORREDO, id: 11, name: "Il piccolo", title: "Il piccolo" }

function pagina(corpo: Partial<Record<keyof Pagina, unknown>> = {}): Pagina {
  return {
    instruments: [OTTICA, MONTATURA],
    rigs: [CORREDO],
    filters: [FILTRO],
    cards: {},
    moon_deg: 0.527,
    fields: [],
    moon_pct: null,
    ...corpo,
  } as unknown as Pagina
}

function indice(
  p: Pagina,
  scelta: Parameters<typeof Indice>[0]["scelta"] = null,
  formato: "desktop" | "telefono" = "desktop",
) {
  const onScegli = vi.fn()
  render(<Indice pagina={p} scelta={scelta} formato={formato} onScegli={onScegli} />)
  return { nav: screen.getByRole("navigation", { name: /indice dell'attrezzatura/i }), onScegli }
}

const cartaDi = (nav: HTMLElement, nome: RegExp) => within(nav).getByRole("link", { name: nome })

describe("cosa sceglie l indice", () => {
  it("i gruppi sono quelli che hanno qualcosa, nell'ordine della tavola, coi filtri in fondo", () => {
    const due = { ...OTTICA, id: 5, name: "RedCat 51" }
    expect(
      gruppiDi(pagina({ instruments: [MONTATURA, OTTICA, due] })).map((g) => [g.kind, g.quanti]),
    ).toEqual([
      ["optics", 2],
      ["mount", 1],
      ["filter", 1],
    ])
    expect(gruppiDi(pagina({ instruments: [], filters: [] }))).toEqual([])
  })

  it("si apre il primo setup; senza setup il primo gruppo; senza niente nulla", () => {
    expect(primaScelta(pagina({ rigs: [ALTRO, CORREDO] }))).toEqual({ setup: ALTRO.id })
    expect(primaScelta(pagina({ rigs: [] }))).toEqual({ gruppo: "optics" })
    expect(primaScelta(pagina({ rigs: [], instruments: [] }))).toEqual({ gruppo: "filter" })
    expect(primaScelta(pagina({ rigs: [], instruments: [], filters: [] }))).toBeNull()
  })

  it("una scelta resta finche' il suo setup o il suo gruppo e' ancora sulla pagina", () => {
    const p = pagina({ rigs: [ALTRO, CORREDO] })
    expect(esiste(p, { setup: CORREDO.id })).toBe(true)
    expect(esiste(p, { setup: ALTRO.id })).toBe(true)
    expect(esiste(p, { setup: 99 })).toBe(false)
    expect(esiste(pagina({ rigs: [] }), { setup: CORREDO.id })).toBe(false)
    expect(esiste(p, { gruppo: "mount" })).toBe(true)
    expect(esiste(p, { gruppo: "focuser" })).toBe(false)
    expect(esiste(pagina({ filters: [] }), { gruppo: "filter" })).toBe(false)
  })
})

describe("l indice dell Attrezzatura", () => {
  it("una sezione senza niente non compare, e i componenti si contano tutti, filtri compresi", () => {
    const { nav } = indice(pagina({ rigs: [] }))
    expect(within(nav).queryByRole("heading", { name: /^setup$/i })).toBeNull()
    const componenti = within(nav).getByRole("region", { name: /componenti/i })
    expect(within(componenti).getByRole("heading").parentElement?.textContent).toContain("3")
    pulisci()

    const { nav: vuoto } = indice(pagina({ instruments: [], filters: [] }))
    expect(within(vuoto).getByRole("heading", { name: /^setup$/i })).toBeDefined()
    expect(within(vuoto).queryByRole("region", { name: /componenti/i })).toBeNull()
  })

  it("un clic su una carta o su una pillola dice cosa si e' scelto", () => {
    const { nav, onScegli } = indice(pagina({ rigs: [ALTRO, CORREDO] }))
    fireEvent.click(cartaDi(nav, /il grande/i))
    expect(onScegli).toHaveBeenLastCalledWith({ setup: CORREDO.id })
    fireEvent.click(within(nav).getByRole("link", { name: /montature/i }))
    expect(onScegli).toHaveBeenLastCalledWith({ gruppo: "mount" })
  })

  it("e' segnata solo la scelta, con l anello; sul telefono niente", () => {
    const { nav } = indice(pagina({ rigs: [ALTRO, CORREDO] }), { setup: CORREDO.id })
    const scelta = cartaDi(nav, /il grande/i)
    expect(scelta.getAttribute("aria-current")).toBe("true")
    expect(scelta.style.boxShadow).toBe("inset 0 0 0 2px var(--accento)")
    expect(cartaDi(nav, /il piccolo/i).getAttribute("aria-current")).toBeNull()
    expect(cartaDi(nav, /il piccolo/i).style.boxShadow).toBe("none")
    pulisci()

    const { nav: gruppo } = indice(pagina(), { gruppo: "mount" })
    const pillola = within(gruppo).getByRole("link", { name: /montature/i })
    expect(pillola.getAttribute("aria-current")).toBe("true")
    expect(pillola.style.boxShadow).toBe("inset 0 0 0 2px var(--accento)")
    expect(cartaDi(gruppo, /il grande/i).getAttribute("aria-current")).toBeNull()
    pulisci()

    const { nav: tel } = indice(pagina(), { setup: CORREDO.id }, "telefono")
    expect(tel.querySelectorAll('[aria-current="true"]')).toHaveLength(0)
  })

  it("le misure della carta vengono dalla tavola, diverse sul telefono", () => {
    const { nav } = indice(pagina())
    expect(cartaDi(nav, /il grande/i).style.minHeight).toBe("220px")
    expect(nav.style.gap).toBe("16px")
    pulisci()
    const { nav: tel } = indice(pagina(), null, "telefono")
    const carta = cartaDi(tel, /il grande/i)
    expect([carta.style.minHeight, carta.style.padding, carta.style.borderRadius]).toEqual([
      "200px",
      "16px",
      "24px",
    ])
    expect(tel.style.gap).toBe("12px")
  })
})

describe("la carta di un setup", () => {
  it("un setup contato ha le sue ore e la barra; uno da contare lo dice, senza barra", () => {
    const { nav } = indice(
      pagina({
        rigs: [
          { ...CORREDO, bar_pct: 40 },
          { ...ALTRO, counted: false },
        ],
      }),
    )
    const contato = cartaDi(nav, /il grande/i)
    expect(contato.textContent).toContain("10 h")
    expect((contato.querySelector('[data-an="barra"]') as HTMLElement).style.width).toBe("40%")
    const daContare = cartaDi(nav, /il piccolo/i)
    expect(daContare.textContent).toContain("conteggio in corso")
    expect(daContare.textContent).not.toContain("10 h")
    expect(daContare.querySelector('[data-an="barra"]')).toBeNull()
  })

  it("senza ore o senza barra non si disegna la barra", () => {
    const { nav } = indice(
      pagina({
        rigs: [
          { ...CORREDO, integration_s: null },
          { ...ALTRO, bar_pct: null },
        ],
      }),
    )
    expect(cartaDi(nav, /il grande/i).textContent).toContain("conteggio in corso")
    expect(cartaDi(nav, /il grande/i).querySelector('[data-an="barra"]')).toBeNull()
    expect(cartaDi(nav, /il piccolo/i).textContent).toContain("10 h")
    expect(cartaDi(nav, /il piccolo/i).querySelector('[data-an="barra"]')).toBeNull()
  })

  it("ottica e camera per nome, o che non sono indicate", () => {
    const { nav } = indice(pagina({ rigs: [CORREDO, { ...ALTRO, optics: null, camera: null }] }))
    const pieno = within(cartaDi(nav, /il grande/i))
      .getAllByRole("listitem")
      .map((x) => x.title)
    expect(pieno).toEqual(["TS 130 APO", "ASI2600MM"])
    const vuoto = within(cartaDi(nav, /il piccolo/i))
      .getAllByRole("listitem")
      .map((x) => x.textContent)
    expect(vuoto).toEqual(["ottica non indicata", "camera non indicata"])
  })

  it("la focale solo se c'e', le parti da indicare solo se mancano", () => {
    const tutte = CORREDO.slots.map((s) => ({ ...s, filled: true }))
    const { nav } = indice(
      pagina({ rigs: [CORREDO, { ...ALTRO, focal_mm: null, slots: tutte, slots_missing: 0 }] }),
    )
    const grande = cartaDi(nav, /il grande/i)
    expect(grande.textContent).toContain("910 mm")
    expect(grande.textContent).toContain("8 da indicare")
    const piccolo = cartaDi(nav, /il piccolo/i)
    expect(piccolo.textContent).not.toContain("mm")
    expect(piccolo.textContent).not.toContain("da indicare")
    expect(piccolo.querySelectorAll('[data-pieno="false"]')).toHaveLength(0)
    expect(grande.querySelectorAll('[data-pieno="false"]')).toHaveLength(8)
  })
})
