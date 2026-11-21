// @vitest-environment jsdom
/**
 * Una pagina il cui file non arriva (rete caduta, app aggiornata nel frattempo) lo dice con un
 * riquadro e un Riprova, invece di lasciare la pagina bianca (passo 6.17.1).
 */
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react"
import { Component, type ReactNode } from "react"
import { Link, MemoryRouter, Route, Routes } from "react-router"
import { afterEach, describe, expect, it as prova, vi } from "vitest"

import { Pigre } from "../src/Pigre"
import { pigra } from "../src/pigra"

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

function Ciao() {
  return <p>arrivata</p>
}

const NonArriva = pigra(
  () =>
    Promise.reject<{ Ciao: typeof Ciao }>(
      new TypeError("Failed to fetch dynamically imported module"),
    ),
  "Ciao",
)
const Arriva = pigra(() => Promise.resolve({ Ciao }), "Ciao")

function Rotta(): never {
  throw new Error("un difetto della pagina")
}

/** Catches what the box lets through: a page's own fault is not a download that failed. */
class Sopra extends Component<{ children: ReactNode }, { errore: string | null }> {
  override state = { errore: null as string | null }
  static getDerivedStateFromError(e: Error) {
    return { errore: e.message }
  }
  override render() {
    return this.state.errore ?? this.props.children
  }
}

async function apri(pagina: ReactNode, altra: ReactNode = <Arriva />) {
  await act(async () => {
    render(
      <MemoryRouter initialEntries={["/rotta"]}>
        <Link to="/altra">altra</Link>
        <Sopra>
          <Pigre>
            <Routes>
              <Route path="/rotta" element={pagina} />
              <Route path="/altra" element={altra} />
            </Routes>
          </Pigre>
        </Sopra>
      </MemoryRouter>,
    )
  })
}

describe("una pagina che non si carica", () => {
  prova("dice cosa e' successo e offre Riprova, che ricarica l'app", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {})
    const ricarica = vi.fn()
    vi.spyOn(window, "location", "get").mockReturnValue({ ...window.location, reload: ricarica })
    await apri(<NonArriva />)
    expect(await screen.findByText("Questa pagina non si è caricata")).toBeDefined()
    expect(
      screen.getByText("Può succedere se la rete si è interrotta o l'app è stata aggiornata."),
    ).toBeDefined()
    fireEvent.click(screen.getByRole("button", { name: "Riprova" }))
    expect(ricarica).toHaveBeenCalledOnce()
  })

  prova("andando su un'altra pagina il riquadro se ne va", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {})
    await apri(<NonArriva />)
    await screen.findByText("Questa pagina non si è caricata")
    await act(async () => fireEvent.click(screen.getByRole("link", { name: "altra" })))
    expect(await screen.findByText("arrivata")).toBeDefined()
    expect(screen.queryByText("Questa pagina non si è caricata")).toBeNull()
  })

  prova(
    "chiesto da una finestra, il riquadro e' una finestra sopra la pagina, e si chiude",
    async () => {
      vi.spyOn(console, "error").mockImplementation(() => {})
      const chiudi = vi.fn()
      await act(async () => {
        render(
          <MemoryRouter>
            <Pigre onChiudi={chiudi}>
              <NonArriva />
            </Pigre>
          </MemoryRouter>,
        )
      })
      const finestra = await screen.findByRole("dialog", {
        name: "Questa pagina non si è caricata",
      })
      expect(finestra.closest(".al-finestra")).not.toBeNull()
      expect(screen.getByRole("button", { name: "Riprova" })).toBeDefined()
      fireEvent.click(screen.getByRole("link", { name: "Chiudi" }))
      expect(chiudi).toHaveBeenCalledOnce()
    },
  )

  prova("al primo avvio, senza telaio, il riquadro sta nei margini del primo avvio", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {})
    await act(async () => {
      render(
        <MemoryRouter>
          <Pigre fuoriDalTelaio>
            <NonArriva />
          </Pigre>
        </MemoryRouter>,
      )
    })
    const titolo = await screen.findByText("Questa pagina non si è caricata")
    // inside the first start's frame and column (PrimoAvvioCornice, Fondo), not the window's edges
    expect(titolo.closest(".al-avvio__colonna-1")).not.toBeNull()
    expect(screen.getByRole("button", { name: "Riprova" })).toBeDefined()
  })

  prova("un difetto della pagina non si traveste da rete", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {})
    await apri(<Rotta />)
    expect(await screen.findByText("un difetto della pagina")).toBeDefined()
    expect(screen.queryByText("Questa pagina non si è caricata")).toBeNull()
  })
})
