import type { ReactNode } from "react"

import { type Formato, Tema } from "./Tema"

/**
 * The content column of the v76 `Telaio` (desktop `colonna-1`, phone `colonna-2` and `colonna-3`):
 * font, colours and the gap between cards. Bar and menus stay the old shell's until the Telaio port.
 */
export function Pagina({ formato, children }: { formato: Formato; children: ReactNode }) {
  return (
    <Tema>
      {formato === "telefono" ? (
        <div className="al-c-telaio__colonna-2 app-cornice" data-formato="telefono">
          <div className="al-c-telaio__colonna-3">{children}</div>
        </div>
      ) : (
        <div className="al-c-telaio__colonna-1 app-cornice" data-formato="desktop">
          {children}
        </div>
      )}
    </Tema>
  )
}
