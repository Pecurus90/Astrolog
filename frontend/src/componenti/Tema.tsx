import { type ReactNode, createContext, useContext, useMemo } from "react"

/** The two modes of the v58 sheet (`data-modo`). */
export type Modo = "scuro" | "chiaro"
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

/** Mode and accent of the nearest `Tema`; dark and amber without one. */
export function useTema(): Veste {
  return useContext(Contesto)
}

/**
 * The wrapper of a v58 page: the sheet's tokens hang from `data-modo` / `data-accento`, and its
 * :root is the old sheet's while both live together (step 33). No box of its own.
 */
export function Tema({
  modo = PARTENZA.modo,
  accento = PARTENZA.accento,
  children,
}: {
  modo?: Modo
  accento?: Accento
  children: ReactNode
}) {
  const veste = useMemo(() => ({ modo, accento }), [modo, accento])
  return (
    <Contesto.Provider value={veste}>
      <div style={{ display: "contents" }} data-modo={modo} data-accento={accento}>
        {children}
      </div>
    </Contesto.Provider>
  )
}
