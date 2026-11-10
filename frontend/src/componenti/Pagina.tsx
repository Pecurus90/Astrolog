import type { ReactNode } from "react"

import { type Formato, Tema } from "./Tema"

/**
 * A ported page inside the v76 frame: the sheet's tokens (`Tema`) and the format for its
 * `[data-formato]` rules. The column is the frame's (desktop `colonna-1`, phone `colonna-3`):
 * no box of its own, the cards sit in the frame's gap.
 */
export function Pagina({ formato, children }: { formato: Formato; children: ReactNode }) {
  return (
    <Tema>
      <div className="app-cornice app-pagina" data-formato={formato}>
        {children}
      </div>
    </Tema>
  )
}
