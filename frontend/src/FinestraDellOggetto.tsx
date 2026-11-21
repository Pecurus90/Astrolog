import { type ReactNode, useCallback, useEffect, useState } from "react"
import { useLocation } from "react-router"

import { ApriOggettoContesto } from "./apriOggetto"
import { useFormato } from "./componenti/formato"
import { Pigre } from "./Pigre"
import { pigra } from "./pigra"

// downloaded the first time a window opens: the frame does not carry it
const TuttoDellOggetto = pigra(() => import("./TuttoDellOggetto"), "TuttoDellOggetto")

type Aperto = { chiave: string; nome: string }

/**
 * The object window the shell holds, for who opens it outside the Archive: the search and the
 * Nights' objects. The Archive keeps its own, with the arrows of its order.
 */
export function FinestraDellOggetto({ children }: { children: ReactNode }) {
  const [aperto, setAperto] = useState<Aperto | null>(null)
  const apri = useCallback((chiave: string, nome: string) => setAperto({ chiave, nome }), [])
  const chiudi = useCallback(() => setAperto(null), [])
  const dove = useLocation()
  const formato = useFormato()
  // a new page under the window: left open, it would cover the page asked for
  useEffect(() => setAperto(null), [dove.key])

  return (
    <ApriOggettoContesto.Provider value={apri}>
      {children}
      {aperto && (
        // the file not arriving is a window too, above the page and closable
        <Pigre onChiudi={chiudi}>
          <TuttoDellOggetto
            key={aperto.chiave}
            chiave={aperto.chiave}
            nome={aperto.nome}
            formato={formato}
            onChiudi={chiudi}
          />
        </Pigre>
      )}
    </ApriOggettoContesto.Provider>
  )
}
