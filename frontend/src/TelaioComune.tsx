import type { CSSProperties, MouseEvent } from "react"

import { numero, t } from "./i18n"
import { paginaDi } from "./pagine"

/** Cio' che il telaio v76 apre, uno alla volta. */
export type Aperto = "altro" | "imp" | "todo" | "notte" | "cerca"

/** Il telaio condiviso fra desktop e telefono: cosa e' aperto, come si apre, a chi torna il fuoco. */
export type Comandi = {
  aperto: Aperto | null
  tocca: (quale: Aperto) => (e: MouseEvent) => void
  segna: (quale: Aperto) => (e: HTMLElement | null) => void
  chiudiCerca: (riportaIlFuoco: boolean) => void
  apri: (quale: Aperto | null) => void
}

export const LENTE = "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM20 20l-4-4"

/** Un'icona a tratto della testa o di un menu (`menu`), come nella tavola. */
export function Tratto({
  d,
  lato,
  spessore = 1.6,
  menu = false,
}: {
  d: string
  lato: number
  spessore?: number
  menu?: boolean
}) {
  return (
    <svg
      className={menu ? "al-c-menu__grafico-1" : "al-c-telaio__grafico-1"}
      width={lato}
      height={lato}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={spessore}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={d} />
    </svg>
  )
}

/** Il conto di Da confermare, col battito e l'alone della tavola (`alPulse`, `alHalo`). */
export function Conto({ n }: { n: number }) {
  const alone = {
    position: "absolute",
    inset: 0,
    borderRadius: 999,
    "--h": "var(--da-confermare-fondo)",
    animation: "alHalo 1.6s ease-out infinite",
  }
  return (
    <span style={{ position: "relative", display: "inline-grid", placeItems: "center" }}>
      <span style={alone as CSSProperties} />
      <span
        style={{
          position: "relative",
          background: "var(--da-confermare-fondo)",
          color: "var(--da-confermare-testo)",
          borderRadius: 999,
          padding: "1px 8px",
          fontWeight: 600,
          fontSize: 13,
          animation: "alPulse 1.6s ease-in-out infinite",
        }}
      >
        {numero(n)}
      </span>
    </span>
  )
}

/** Il titolo della pagina aperta; sul telefono i nomi lunghi si accorciano come nella tavola. */
export function titoloDi(pathname: string, telefono: boolean): string {
  const qui = paginaDi(pathname)
  if (!qui) return t("nav.unknown")
  return telefono && qui.a === "/selezione-dei-frame" ? t("frame.title.selection") : t(qui.chiave)
}
