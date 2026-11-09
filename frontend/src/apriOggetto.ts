import { createContext, useContext } from "react"

/** Opens the object window over the page you are on: there is no object route (Marco, 9/11). */
export type ApriOggetto = (chiave: string, nome: string) => void

export const ApriOggettoContesto = createContext<ApriOggetto | null>(null)

/** Null outside the shell: there the object stays a name, not a link. */
export function useApriOggetto(): ApriOggetto | null {
  return useContext(ApriOggettoContesto)
}
