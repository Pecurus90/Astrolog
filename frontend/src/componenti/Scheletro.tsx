import type { ReactNode } from "react"

import { t } from "../i18n"
import { type Formato, useTema } from "./Tema"

/** A grey block; a circle is `{ h, w, r: "50%", flex: "none" }`. */
export interface BloccoScheletro {
  h?: string
  w?: string
  r?: string
  flex?: string
}

/** Blocks side by side (`riga`), stacked (`colonna`) or on a grid (`griglia` with `figli`). */
export interface GruppoScheletro {
  riga?: PezzoScheletro[]
  colonna?: PezzoScheletro[]
  figli?: PezzoScheletro[]
  griglia?: string
  gap?: string
  tra?: boolean
  attorno?: boolean
  al?: string
  flex?: string
  h?: string
}

/** A string is a real word shown while loading (a section title). */
export type PezzoScheletro = string | BloccoScheletro | GruppoScheletro

export interface CartaScheletro {
  col?: string
  h?: string
  pad?: string
  gap?: string
  griglia?: string
  blocchi?: PezzoScheletro[]
}

/** Cards piled in the same column. */
export interface PilaScheletro {
  col?: string
  pila: { h?: string; flex?: string; pad?: string; gap?: string; blocchi?: BloccoScheletro[] }[]
}

const PRIMA: CartaScheletro[] = [{ h: "300px", blocchi: [{ h: "36px", w: "60%" }, { flex: "1" }] }]

const figliDi = (g: GruppoScheletro): PezzoScheletro[] => g.riga ?? g.colonna ?? g.figli ?? []
const gruppo = (p: PezzoScheletro): p is GruppoScheletro =>
  typeof p !== "string" && ("riga" in p || "colonna" in p || "figli" in p)

function Blocco({ b }: { b: BloccoScheletro }) {
  return (
    <span
      className="al-c-scheletro__blocco-3"
      style={{
        height: b.h ?? "auto",
        width: b.w ?? "auto",
        flex: b.flex ?? "0 1 auto",
        borderRadius: b.r ?? "14px",
      }}
    />
  )
}

/** Inside a group: a word, a block, or a stack of blocks (the delivery goes no deeper). */
function Figlio({ f }: { f: PezzoScheletro }) {
  if (typeof f === "string") return <span className="al-c-scheletro__testo-1">{f}</span>
  if (!gruppo(f)) return <Blocco b={f} />
  return (
    <div
      className="al-c-scheletro__colonna-1"
      style={{ gap: f.gap ?? "0", flex: f.flex ?? "0 1 auto" }}
    >
      {figliDi(f).map((g, i) => (
        <Blocco key={i} b={typeof g === "string" ? {} : (g as BloccoScheletro)} />
      ))}
    </div>
  )
}

function Pezzo({ x }: { x: PezzoScheletro }) {
  if (typeof x === "string") return <span className="al-c-scheletro__testo-1">{x}</span>
  if (!gruppo(x)) return <Blocco b={x} />
  return (
    <div
      className="al-c-scheletro__blocco-5"
      style={{
        display: x.griglia ? "grid" : "flex",
        gridTemplateColumns: x.griglia ?? "none",
        flexDirection: x.colonna ? "column" : "row",
        justifyContent: x.tra ? "space-between" : x.attorno ? "space-around" : "flex-start",
        alignItems: x.al ?? (x.griglia || x.colonna ? "stretch" : "center"),
        gap: x.gap ?? "0",
        flex: x.flex ?? "0 1 auto",
        height: x.h ?? "auto",
      }}
    >
      {figliDi(x).map((f, i) => (
        <Figlio key={i} f={f} />
      ))}
    </div>
  )
}

/**
 * The loading skeleton, card by card (v58 `Scheletro`): the page passes the shape of what is
 * coming. It says "Caricamento" to who listens; the blocks are only seen.
 */
export function Scheletro({
  carte = PRIMA,
  griglia,
  gap,
  testo,
  formato = "desktop",
}: {
  carte?: (CartaScheletro | PilaScheletro)[]
  griglia?: string
  gap?: string
  /** The name for who listens; without it, the dictionary's word. */
  testo?: string
  formato?: Formato
}) {
  const { modo, accento } = useTema()
  const telefono = formato === "telefono"
  const angolo = telefono ? "24px" : "28px"
  const dentro = telefono ? "20px" : "28px"
  const stacco = gap ?? (telefono ? "12px" : "16px")
  const carta = (c: CartaScheletro | PilaScheletro, i: number): ReactNode =>
    "pila" in c ? (
      <div
        key={i}
        className="al-c-scheletro__colonna-1"
        style={{ gridColumn: c.col ?? "auto", gap: stacco }}
      >
        {c.pila.map((q, j) => (
          <div
            key={j}
            className="al-c-scheletro__colonna-2"
            style={{
              height: q.h ?? "auto",
              flex: q.flex ?? "0 1 auto",
              borderRadius: angolo,
              padding: q.pad ?? dentro,
              gap: q.gap ?? "0",
            }}
          >
            {(q.blocchi ?? []).map((b, k) => (
              <Blocco key={k} b={b} />
            ))}
          </div>
        ))}
      </div>
    ) : (
      <div
        key={i}
        className="al-c-scheletro__blocco-4"
        style={{
          gridColumn: c.col ?? "auto",
          height: c.h ?? "auto",
          borderRadius: angolo,
          padding: c.pad ?? dentro,
          display: c.griglia ? "grid" : "flex",
          gridTemplateColumns: c.griglia ?? "none",
          gap: c.gap ?? (telefono ? "14px" : "18px"),
        }}
      >
        {(c.blocchi ?? []).map((x, k) => (
          <Pezzo key={k} x={x} />
        ))}
      </div>
    )
  return (
    <div className="al-c-scheletro__blocco-1" data-modo={modo} data-accento={accento}>
      <div
        className="al-c-scheletro__blocco-2"
        role="status"
        aria-live="polite"
        aria-label={testo || t("ui.loading")}
        style={{
          display: telefono && !griglia ? "flex" : "grid",
          gridTemplateColumns: griglia ?? (telefono ? "none" : "repeat(12,minmax(0,1fr))"),
          gap: stacco,
        }}
      >
        {carte.map(carta)}
      </div>
    </div>
  )
}
