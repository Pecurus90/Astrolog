import { type ReactNode, Suspense, useCallback, useEffect, useState } from "react"
import { useLocation } from "react-router"

import { ApriOggettoContesto } from "./apriOggetto"
import { useFormato } from "./componenti/formato"
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
  const dove = useLocation()
  const formato = useFormato()
  // a new page under the window: left open, it would cover the page asked for
  useEffect(() => setAperto(null), [dove.key])

  return (
    <ApriOggettoContesto.Provider value={apri}>
      {children}
      {aperto && (
        <Suspense>
          <TuttoDellOggetto
            key={aperto.chiave}
            chiave={aperto.chiave}
            nome={aperto.nome}
            formato={formato}
            onChiudi={() => setAperto(null)}
          />
        </Suspense>
      )}
    </ApriOggettoContesto.Provider>
  )
}
