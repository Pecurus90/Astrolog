import { type ReactNode, createContext, useContext, useMemo } from "react"

/** The two modes of the v58 sheet (`data-modo`). */
export type Modo = "scuro" | "chiaro"
/** What the user picks: a mode, or Automatico, which wears the one the API says is in force. */
export type ModoScelto = Modo | "automatico"
/** The five accents of the v58 sheet (`data-accento`); the sheet's default is amber. */
export type Accento = "originale" | "ambra" | "turchese" | "corallo" | "ghiaccio"
/** Desktop or phone: the delivery's components take it as a parameter, never guess it. */
export type Formato = "desktop" | "telefono"

export interface Veste {
  modo: Modo
  accento: Accento
}

const PARTENZA: Veste = { modo: "scuro", accento: "ambra" }

const Contesto = createContext<Veste>(PARTENZA)
// The user's saved choice (Impostazioni, Tema): what a `Tema` without props wears.
const Salvata = createContext<Veste>(PARTENZA)

const SCELTE: readonly ModoScelto[] = ["scuro", "chiaro", "automatico"]
export const ACCENTI: readonly Accento[] = ["originale", "ambra", "turchese", "corallo", "ghiaccio"]

/** What the user saved: Automatico stays itself, unlike the `Veste` worn. */
export interface Scelta {
  modo: ModoScelto
  accento: Accento
}

/** The saved values; an unknown one stays the sheet's default. */
export function sceltaDa(modo: unknown, accento: unknown): Scelta {
  return {
    modo: SCELTE.find((m) => m === modo) ?? PARTENZA.modo,
    accento: ACCENTI.find((a) => a === accento) ?? PARTENZA.accento,
  }
}

/**
 * The saved values as the `Veste` worn. Automatico wears `ora`, the mode in force from the API
 * (`theme_now`), and scuro while it is not known (board v82).
 */
export function vesteDa(modo: unknown, accento: unknown, ora?: Modo | null): Veste {
  const scelta = sceltaDa(modo, accento)
  return {
    modo: scelta.modo === "automatico" ? (ora ?? PARTENZA.modo) : scelta.modo,
    accento: scelta.accento,
  }
}

/** The saved mode and accent, for every `Tema` below that does not name its own. */
export function VesteSalvata({ veste, children }: { veste: Veste; children: ReactNode }) {
  return <Salvata.Provider value={veste}>{children}</Salvata.Provider>
}

/** Mode and accent of the nearest `Tema`; dark and amber without one. */
export function useTema(): Veste {
  return useContext(Contesto)
}

/**
 * The wrapper of a v58 page: the sheet's tokens hang from `data-modo` / `data-accento`, and its
 * :root is the old sheet's while both live together (step 33). No box of its own.
 */
export function Tema({
  modo,
  accento,
  children,
}: {
  modo?: Modo
  accento?: Accento
  children: ReactNode
}) {
  const salvata = useContext(Salvata)
  const veste = useMemo(
    () => ({ modo: modo ?? salvata.modo, accento: accento ?? salvata.accento }),
    [modo, accento, salvata],
  )
  return (
    <Contesto.Provider value={veste}>
      <div style={{ display: "contents" }} data-modo={veste.modo} data-accento={veste.accento}>
        {children}
      </div>
    </Contesto.Provider>
  )
}
