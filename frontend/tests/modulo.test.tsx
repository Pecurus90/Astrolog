// @vitest-environment jsdom
/**
 * Il **Modulo** della consegna (`src/componenti/Modulo.tsx`, v82 `componenti/Modulo`): le misure
 * dei due contesti e del telefono, l'errore, Salva acceso spento e occupato, il perche' accanto.
 */
import { fireEvent, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { CampoDelModulo, Modulo, TendinaDelModulo } from "../src/componenti/Modulo"
import type { Formato } from "../src/componenti/Tema"
import { Tema } from "../src/componenti/Tema"
import { pulisci } from "./banco"

afterEach(pulisci)

type Prove = Partial<Parameters<typeof Modulo>[0]>

function modulo(prove: Prove = {}) {
  const props = {
    titolo: "Nome di Il grande",
    formato: "desktop" as Formato,
    salva: { onSalva: vi.fn(), occupato: false, spento: false },
    onAnnulla: vi.fn(),
    children: <span>campi</span>,
    ...prove,
  }
  render(<Modulo {...props} />)
  const gruppo = screen.getByRole("group", { name: "Nome di Il grande" })
  const piede = gruppo.querySelector<HTMLElement>(".al-c-modulo__riga-9")
  const griglia = gruppo.querySelector<HTMLElement>(".al-c-modulo__centro-3")
  const titolo = gruppo.querySelector<HTMLElement>("h2")
  return { props, gruppo, piede, griglia, titolo }
}

describe("il Modulo", () => {
  it("in testa alla pagina, sul desktop", () => {
    const { gruppo, piede, griglia, titolo } = modulo()
    expect(gruppo.style).toMatchObject({
      borderRadius: "28px",
      padding: "28px",
      colorScheme: "dark",
    })
    expect(gruppo.style.background).toBe("var(--carta)")
    expect(gruppo.style.boxShadow).toBe("none")
    expect(titolo?.textContent).toBe("Nome di Il grande")
    expect(titolo?.style.fontSize).toBe("30px")
    expect(griglia?.style.gridTemplateColumns).toBe("repeat(2, minmax(0px, 1fr))")
    expect(piede?.style).toMatchObject({ position: "static", boxShadow: "none" })
    expect(piede?.style.padding).toBe("0px")
    expect(piede?.style.margin).toBe("0px")
    const dentro = gruppo.querySelector<HTMLElement>(".al-c-modulo__colonna-4")
    expect(dentro?.style.gridColumn).toBe("1 / -1")
    expect(dentro?.textContent).toBe("campi")
  })

  it("in testa alla pagina, sul telefono, coi bottoni attaccati al fondo", () => {
    const { gruppo, piede, griglia, titolo } = modulo({ formato: "telefono" })
    expect(gruppo.style).toMatchObject({ borderRadius: "24px", padding: "20px" })
    expect(titolo?.style.fontSize).toBe("24px")
    expect(griglia?.style.gridTemplateColumns).toBe("minmax(0px, 1fr)")
    expect(piede?.style).toMatchObject({
      position: "sticky",
      padding: "10px",
      margin: "0px -6px",
    })
    // jsdom riscrive l'ombra col colore in testa
    expect(piede?.style.boxShadow).toBe("rgba(0, 0, 0, 0.18) 0px 8px 24px")
    expect(piede?.getAttribute("style")).toContain(
      "color-mix(in srgb, var(--carta) 92%, transparent)",
    )
  })

  it("dentro una carta, con l'anello nell'accento", () => {
    const { gruppo, titolo, piede } = modulo({ dentro: true })
    expect(gruppo.style).toMatchObject({
      borderRadius: "20px",
      padding: "22px",
      boxShadow: "inset 0 0 0 2px var(--accento)",
    })
    expect(gruppo.style.background).toBe("var(--carta-2)")
    expect(titolo?.style.fontSize).toBe("17px")
    expect(piede?.getAttribute("style")).not.toContain("color-mix")
    pulisci()
    const tel = modulo({ dentro: true, formato: "telefono" })
    expect(tel.gruppo.style.padding).toBe("16px")
    expect(tel.gruppo.style.borderRadius).toBe("20px")
    expect(tel.piede?.getAttribute("style")).toContain(
      "color-mix(in srgb, var(--carta-2) 92%, transparent)",
    )
  })

  it("in modo chiaro i controlli sono chiari", () => {
    render(
      <Tema modo="chiaro">
        <Modulo titolo="T" formato="desktop" salva={null} onAnnulla={() => {}}>
          x
        </Modulo>
      </Tema>,
    )
    expect(screen.getByRole("group", { name: "T" }).style.colorScheme).toBe("light")
  })

  it("Salva salva e Annulla annulla", () => {
    const { props } = modulo()
    const salva = screen.getByRole("button", { name: "Salva" })
    expect(salva.getAttribute("aria-disabled")).toBeNull()
    expect(salva.getAttribute("aria-busy")).toBeNull()
    expect(salva.style).toMatchObject({ opacity: "1", cursor: "pointer" })
    expect(salva.querySelector(".al-c-modulo__tondo-4")).toBeNull()
    fireEvent.click(salva)
    expect(props.salva?.onSalva).toHaveBeenCalledTimes(1)
    fireEvent.click(screen.getByRole("button", { name: "Annulla" }))
    expect(props.onAnnulla).toHaveBeenCalledTimes(1)
  })

  it("Salva spento non salva e dice perche'", () => {
    const onSalva = vi.fn()
    modulo({
      salva: { onSalva, occupato: false, spento: true },
      perche: "Per salvare serve il nome.",
    })
    const salva = screen.getByRole("button", { name: "Salva" })
    expect(salva.getAttribute("aria-disabled")).toBe("true")
    expect(salva.style).toMatchObject({ opacity: "0.45", cursor: "not-allowed" })
    fireEvent.click(salva)
    expect(onSalva).not.toHaveBeenCalled()
    const perche = screen.getByText("Per salvare serve il nome.")
    expect(perche.getAttribute("aria-live")).toBe("polite")
  })

  it("Salva occupato gira, non salva due volte e non sbiadisce", () => {
    const onSalva = vi.fn()
    modulo({ salva: { onSalva, occupato: true, spento: false } })
    const salva = screen.getByRole("button", { name: /salvataggio/i })
    expect(salva.getAttribute("aria-busy")).toBe("true")
    expect(salva.getAttribute("aria-disabled")).toBe("true")
    expect(salva.style).toMatchObject({ opacity: "1", cursor: "progress" })
    expect(salva.querySelector(".al-c-modulo__tondo-4")).not.toBeNull()
    fireEvent.click(salva)
    expect(onSalva).not.toHaveBeenCalled()
  })

  it("senza Salva c'e' solo Annulla; senza errore nessun avviso", () => {
    modulo({ salva: null })
    expect(screen.queryByRole("button", { name: /salva/i })).toBeNull()
    expect(screen.getByRole("button", { name: "Annulla" })).toBeTruthy()
    expect(screen.queryByRole("alert")).toBeNull()
  })

  it("l'errore e' un avviso col punto esclamativo", () => {
    modulo({ errore: "Nome gia' usato." })
    expect(screen.getByRole("alert").textContent).toBe("!Nome gia' usato.")
  })
})

describe("i campi del Modulo", () => {
  it("un campo largo prende la riga, uno stretto no; l'etichetta nomina il controllo", () => {
    render(
      <>
        <CampoDelModulo id="a" etichetta="Nome" largo>
          <input id="a" />
        </CampoDelModulo>
        <CampoDelModulo id="b" etichetta="Marca">
          <input id="b" />
        </CampoDelModulo>
        <CampoDelModulo id="c" etichetta="">
          <input id="c" />
        </CampoDelModulo>
      </>,
    )
    const largo = screen.getByRole("textbox", { name: "Nome" })
    expect(largo.parentElement?.style.gridColumn).toBe("1 / -1")
    expect(screen.getByRole("textbox", { name: "Marca" }).parentElement?.style.gridColumn).toBe(
      "auto",
    )
    expect(document.getElementById("a-l")?.textContent).toBe("Nome")
    expect(document.querySelectorAll("label")).toHaveLength(2)
  })

  it("la tendina scrive la voce scelta", () => {
    const onValore = vi.fn()
    render(
      <TendinaDelModulo
        id="t"
        valore=""
        voci={[
          { valore: "", l: "--" },
          { valore: "2", l: "EQ6-R" },
        ]}
        onValore={onValore}
      />,
    )
    const tendina = screen.getByRole("combobox")
    expect([...tendina.querySelectorAll("option")].map((o) => o.textContent)).toEqual([
      "--",
      "EQ6-R",
    ])
    fireEvent.change(tendina, { target: { value: "2" } })
    expect(onValore).toHaveBeenCalledWith("2")
  })
})
