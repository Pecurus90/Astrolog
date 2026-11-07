import type { CSSProperties, ReactNode } from "react"

import { type Formato, useTema } from "./Tema"

/** "!" something failed, "?" a datum is missing, check mark: done (first start's outcomes). */
export type SegnoAvviso = "!" | "?" | "\u2713"
export type TipoAvviso = "pagina" | "blocco" | "riga"

// The delivery colours the round inline from tema.js; these are the same values as sheet tokens.
const TONDI: Record<SegnoAvviso, { background: string; color: string; anello: string }> = {
  "!": { background: "var(--avviso)", color: "var(--avviso-testo)", anello: "transparent" },
  "?": { background: "var(--carta)", color: "var(--testo)", anello: "var(--linea)" },
  "\u2713": {
    background: "var(--buono-fondo)",
    color: "var(--buono-testo)",
    anello: "transparent",
  },
}

const misura = (v: number | string): string =>
  typeof v === "number" || /^\d+$/.test(v) ? `${v}px` : v

/**
 * A notice of page, block or row, with its sign and its action (v58 `Avviso`). The sign is
 * aria-hidden: the title says it in words, so colour never speaks alone.
 */
export function Avviso({
  tipo = "blocco",
  formato = "desktop",
  segno = "!",
  titolo,
  testo,
  azione,
  onAzione,
  colonne,
  rientro = 0,
}: {
  tipo?: TipoAvviso
  formato?: Formato
  segno?: SegnoAvviso
  titolo: string
  testo?: string
  azione?: string
  onAzione?: () => void
  /** Grid columns of the page notice on desktop: a number is a span, a string goes as it is. */
  colonne?: number | string
  /** Side margin on the phone. */
  rientro?: number | string
}) {
  const { modo, accento } = useTema()
  const tinta = TONDI[segno]
  const tondo: CSSProperties = {
    background: segno === "?" && tipo === "pagina" ? "var(--carta-2)" : tinta.background,
    color: tinta.color,
    boxShadow: `inset 0 0 0 1.5px ${tinta.anello}`,
  }
  const colonna =
    colonne === undefined
      ? "span 12"
      : typeof colonne === "number" || /^\d+$/.test(colonne)
        ? `span ${colonne}`
        : colonne
  const margine = { margin: `0 ${misura(rientro)}` }
  const telefono = formato === "telefono"
  // classes literal at each call: the template only keeps the sheet guard able to read this one
  const gesto = (classe: string): ReactNode =>
    azione ? (
      <button type="button" className={`${classe}`} onClick={onAzione}>
        {azione}
      </button>
    ) : null

  let corpo: ReactNode
  if (tipo === "pagina" && !telefono) {
    corpo = (
      <div className="al-c-avviso__griglia-1" role="status" style={{ gridColumn: colonna }}>
        <span className="al-c-avviso__tondo-1" aria-hidden="true" style={tondo}>
          {segno}
        </span>
        <span className="al-c-avviso__colonna-1">
          <b className="al-c-avviso__testo-1">{titolo}</b>
          {testo && <span className="al-c-avviso__testo-2">{testo}</span>}
        </span>
        {gesto("al-bottone al-bottone--contorno")}
      </div>
    )
  } else if (tipo === "pagina") {
    corpo = (
      <div className="al-c-avviso__colonna-2" role="status">
        <span className="al-c-avviso__riga-1">
          <span className="al-c-avviso__tondo-2" aria-hidden="true" style={tondo}>
            {segno}
          </span>
          <b className="al-c-avviso__testo-3">{titolo}</b>
        </span>
        {testo && <span className="al-c-avviso__testo-4">{testo}</span>}
        {gesto("al-bottone al-bottone--contorno al-bottone--blocco")}
      </div>
    )
  } else if (tipo === "blocco" && !telefono) {
    corpo = (
      <div className="al-c-avviso__griglia-2" role="status">
        <span className="al-c-avviso__tondo-3" aria-hidden="true" style={tondo}>
          {segno}
        </span>
        <span className="al-c-avviso__colonna-1">
          <b className="al-c-avviso__testo-5">{titolo}</b>
          {testo && <span className="al-c-avviso__testo-2">{testo}</span>}
        </span>
        {gesto("al-bottone al-bottone--contorno")}
      </div>
    )
  } else if (tipo === "blocco") {
    corpo = (
      <div className="al-c-avviso__colonna-3" role="status" style={margine}>
        <span className="al-c-avviso__riga-2">
          <span className="al-c-avviso__tondo-4" aria-hidden="true" style={tondo}>
            {segno}
          </span>
          <b className="al-c-avviso__testo-6">{titolo}</b>
        </span>
        {testo && <span className="al-c-avviso__testo-7">{testo}</span>}
        {gesto("al-bottone al-bottone--contorno al-bottone--blocco")}
      </div>
    )
  } else if (!telefono) {
    corpo = (
      <div className="al-c-avviso__riga-3" role="status">
        <span className="al-c-avviso__tondo-5" aria-hidden="true" style={tondo}>
          {segno}
        </span>
        <span className="al-c-avviso__blocco-2">{titolo}</span>
        {gesto("al-bottone al-bottone--testo al-bottone--piccolo")}
      </div>
    )
  } else {
    corpo = (
      <div className="al-c-avviso__colonna-4" role="status" style={margine}>
        <span className="al-c-avviso__riga-4">
          <span className="al-c-avviso__tondo-6" aria-hidden="true" style={tondo}>
            {segno}
          </span>
          <span className="al-c-avviso__testo-8">{titolo}</span>
        </span>
        {gesto(
          "al-bottone al-bottone--testo al-bottone--blocco al-bottone--a-sinistra al-c-avviso__blocco-3",
        )}
      </div>
    )
  }

  return (
    <div className="al-c-avviso__blocco-1" data-modo={modo} data-accento={accento}>
      {corpo}
    </div>
  )
}
