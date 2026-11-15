// @vitest-environment jsdom
/**
 * **SceltaTema** (componente v58): il modo e i cinque accenti, ciascuno col campione nel modo in
 * uso. Automatico spento fino al passo Tema (Marco 15/11/2026).
 */
import { fireEvent, render, screen, within } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { SceltaTema } from "../src/componenti/SceltaTema"
import { pulisci } from "./banco"
import { impronta } from "./impronta"

afterEach(pulisci)

function monta(formato: "desktop" | "telefono") {
  const modi: string[] = []
  const accenti: string[] = []
  const { container } = render(
    <SceltaTema
      modo="scuro"
      accento="turchese"
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

  it("automatico e' spento: non si sceglie e lo segna ai lettori di schermo", () => {
    const { modi } = monta("desktop")
    const auto = screen.getByRole("radio", { name: "Automatico" })
    expect(auto.getAttribute("aria-disabled")).toBe("true")
    expect(screen.getByRole("radio", { name: "Chiaro" }).getAttribute("aria-disabled")).toBeNull()
    fireEvent.click(auto)
    fireEvent.click(screen.getByRole("radio", { name: "Chiaro" }))
    expect(modi).toEqual(["chiaro"])
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
    expect(visti).toEqual(["d9208174", "c2acebbc"])
  })
})
