// @vitest-environment jsdom
/**
 * **SceltaTema** (componente v82): il modo e i cinque accenti, ciascuno col campione nel modo in
 * uso. Automatico segue tramonto e alba del sito di casa: senza sito e' spento e la nota dice
 * perche'.
 */
import { fireEvent, render, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SceltaTema } from "../src/componenti/SceltaTema"
import { type ModoScelto, vesteDa } from "../src/componenti/Tema"
import { pulisci } from "./banco"
import { impronta } from "./impronta"

afterEach(pulisci)

function monta(
  formato: "desktop" | "telefono",
  sito: string | null = "Cima Ekar",
  modo: ModoScelto = "scuro",
) {
  const modi: string[] = []
  const accenti: string[] = []
  const { container } = render(
    <SceltaTema
      modo={modo}
      accento="turchese"
      sito={sito}
      formato={formato}
      onModo={(m) => modi.push(m)}
      onAccento={(a) => accenti.push(a)}
    />,
  )
  return { container, modi, accenti }
}

describe("la scelta del tema", () => {
  it("il modo in uso e l'accento in uso sono scelti, gli altri no", () => {
    monta("desktop")
    const modo = screen.getByRole("radiogroup", { name: /modo/i })
    const scelti = (g: HTMLElement) =>
      within(g)
        .getAllByRole("radio")
        .map((r) => `${r.textContent}:${r.getAttribute("aria-checked")}`)
    expect(scelti(modo)).toEqual(["Chiaro:false", "Scuro:true", "Automatico:false"])
    const accento = screen.getByRole("radiogroup", { name: /accento/i })
    expect(
      within(accento)
        .getAllByRole("radio")
        .map((r) => r.getAttribute("aria-checked")),
    ).toEqual(["false", "false", "true", "false", "false"])
  })

  it("senza sito automatico e' spento, lo segna ai lettori di schermo e dice perche'", () => {
    const { modi } = monta("desktop", null)
    const auto = screen.getByRole("radio", { name: "Automatico" })
    expect(auto.getAttribute("aria-disabled")).toBe("true")
    expect(screen.getByRole("radio", { name: "Chiaro" }).getAttribute("aria-disabled")).toBeNull()
    fireEvent.click(auto)
    fireEvent.click(screen.getByRole("radio", { name: "Chiaro" }))
    expect(modi).toEqual(["chiaro"])
    screen.getByText(
      "Automatico ha bisogno di un sito di osservazione: tramonto e alba si calcolano da lì.",
    )
  })

  it("con un sito automatico si sceglie e, scelto, la nota nomina il sito", () => {
    const { modi } = monta("desktop")
    expect(screen.queryByText(/tramonto/)).toBeNull()
    fireEvent.click(screen.getByRole("radio", { name: "Automatico" }))
    expect(modi).toEqual(["automatico"])
    pulisci()
    monta("desktop", "Cima Ekar", "automatico")
    screen.getByText("Scuro dal tramonto all'alba di Cima Ekar, chiaro di giorno.")
  })

  it("automatico gia' scelto resta raggiungibile anche se il sito non c'e' piu'", () => {
    monta("desktop", null, "automatico")
    const auto = screen.getByRole("radio", { name: "Automatico" })
    expect([auto.getAttribute("aria-checked"), auto.getAttribute("aria-disabled")]).toEqual([
      "true",
      null,
    ])
  })

  it("automatico veste il modo che l'API dice in vigore, scuro finche' non lo sa", () => {
    expect(vesteDa("automatico", "corallo", "chiaro")).toEqual({
      modo: "chiaro",
      accento: "corallo",
    })
    expect(vesteDa("automatico", "corallo", null).modo).toBe("scuro")
    expect(vesteDa("chiaro", "corallo", "scuro").modo).toBe("chiaro")
  })

  it("toccare un accento lo chiede", () => {
    const { accenti } = monta("telefono")
    const accento = screen.getByRole("radiogroup", { name: /accento/i })
    fireEvent.click(within(accento).getAllByRole("radio")[4]!)
    expect(accenti).toEqual(["ghiaccio"])
  })

  it("classi, misure e campioni restano quelli della consegna, su desktop e telefono", () => {
    const visti = (["desktop", "telefono"] as const).map((f) => {
      const { container } = monta(f)
      const html = container.innerHTML
      pulisci()
      return impronta(html)
    })
    expect(visti).toEqual(["ade1506", "2b609e2e"])
  })
})
