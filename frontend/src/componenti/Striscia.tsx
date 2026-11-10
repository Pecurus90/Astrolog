import { type MouseEvent, useEffect, useRef } from "react"

import { t } from "../i18n"
import { type Esito, Pillola } from "./Pillola"
import { Ripresa, type TipoRipresa } from "./Ripresa"
import { type Formato, useTema } from "./Tema"

/** One hour of the night's spark line: height in %, and the outcome; null outside the dark. */
export interface CellaStriscia {
  h: number
  esito: 0 | 1 | 2 | null
}

/** A night of the strip, written by the app; the keys are the delivery's. */
export interface NotteStriscia {
  /** The day, as "mer 30". */
  day: string
  /** Desktop tag beside the day (the month, "stanotte"). */
  tag?: string
  /** Phone tag beside the day. */
  tagS?: string
  /** A trend night: dashed, less reliable. */
  tend?: boolean
  sel?: boolean
  esito: Esito
  /** Word of the pill; without it, the outcome's word. */
  pillT?: string
  rip?: { tipo: TipoRipresa; testo: string }
  /** Hours, already written. */
  hours: string
  /** The line below the hours (time span, site). */
  range: string
  cells?: CellaStriscia[]
  on?: () => void
}

const BARRETTE: Record<0 | 1 | 2, string> = {
  0: "var(--buono-testo)",
  1: "var(--incerto-testo)",
  2: "var(--non-adatto-testo)",
}

/**
 * The strip of nights (v76 `Striscia`, without the header): one tab per night, the chosen one
 * ringed and brought into view when it changes.
 */
export function Striscia({
  notti,
  etichetta,
  rientro = 20,
  formato = "desktop",
}: {
  notti: NotteStriscia[]
  /** The tab list's name; without it, the dictionary's. */
  etichetta?: string
  /** Phone side margin in px. */
  rientro?: number
  formato?: Formato
}) {
  const { modo, accento } = useTema()
  const fila = useRef<HTMLDivElement>(null)
  const ultima = useRef(-1)
  const scelta = notti.findIndex((n) => n.sel)

  useEffect(() => {
    const c = fila.current
    if (!c || c.scrollWidth <= c.clientWidth + 1 || scelta < 0 || scelta === ultima.current) return
    ultima.current = scelta
    // scrollLeft, never scrollIntoView: the page itself must not move
    const s = c.querySelectorAll("[role=tab]")[scelta]?.getBoundingClientRect()
    const r = c.getBoundingClientRect()
    if (s && (s.left < r.left + 8 || s.right > r.right - 8)) c.scrollLeft += s.left - r.left - 16
  }, [scelta])

  const telefono = formato === "telefono"
  const scorre = !telefono && notti.length > 8
  const nome = etichetta || t("ui.strip.label")
  const tessere = notti.map((n) => {
    const vuota = n.tend && !n.sel
    return {
      n,
      clic: (e: MouseEvent) => {
        e.preventDefault()
        n.on?.()
      },
      stile: {
        background: vuota ? "transparent" : "var(--carta-2)",
        color: "var(--testo)",
        border: `1.5px dashed ${vuota ? "var(--linea)" : "transparent"}`,
        boxShadow: n.sel ? "inset 0 0 0 2px var(--accento)" : "none",
      },
    }
  })

  const corpo = telefono ? (
    <div
      ref={fila}
      className="al-c-striscia__riga-3"
      role="tablist"
      aria-label={nome}
      style={{ padding: `0 ${rientro}px 2px`, scrollPadding: `0 ${rientro}px` }}
    >
      {tessere.map(({ n, clic, stile }, i) => (
        <a
          key={i}
          className="al-c-striscia__colonna-3"
          href="#"
          role="tab"
          aria-selected={n.sel ? "true" : "false"}
          onClick={clic}
          style={stile}
        >
          <span className="al-c-striscia__riga-4">
            <b className="al-c-striscia__testo-5">{n.day}</b>
            <span className="al-c-striscia__testo-6" style={{ color: "var(--tenue)" }}>
              {n.tagS}
            </span>
          </span>
          <Pillola
            esito={n.esito}
            {...(n.pillT === undefined ? {} : { testo: n.pillT })}
            dimensione="micro"
            allinea="flex-start"
          />
          {n.rip && (
            <span className="al-c-striscia__blocco-4">
              <Ripresa
                tipo={n.rip.tipo}
                testo={n.rip.testo}
                colore="var(--testo)"
                tenue="var(--tenue)"
              />
            </span>
          )}
          <span className="al-c-striscia__testo-7">{n.hours}</span>
          <span className="al-c-striscia__testo-8" style={{ color: "var(--tenue)" }}>
            {n.range}
          </span>
        </a>
      ))}
    </div>
  ) : (
    <div
      ref={fila}
      className="al-c-striscia__blocco-2"
      role="tablist"
      aria-label={nome}
      // v78: --n lets the sheet keep 150 px tiles under 1000 px
      style={{
        ["--n" as string]: notti.length,
        display: scorre ? "flex" : "grid",
        gridTemplateColumns: `repeat(${notti.length},minmax(0,1fr))`,
        overflowX: scorre ? "auto" : "visible",
        paddingBottom: scorre ? "4px" : "0",
      }}
    >
      {tessere.map(({ n, clic, stile }, i) => (
        <a
          key={i}
          className="al-c-striscia__colonna-1"
          href="#"
          role="tab"
          aria-selected={n.sel ? "true" : "false"}
          onClick={clic}
          style={{ ...stile, width: scorre ? "164px" : "auto", flex: scorre ? "none" : "0 1 auto" }}
        >
          <span className="al-c-striscia__riga-1">
            <b className="al-c-striscia__testo-1">{n.day}</b>
            <span className="al-c-striscia__testo-2" style={{ color: "var(--tenue)" }}>
              {n.tag}
            </span>
          </span>
          <Pillola
            esito={n.esito}
            {...(n.pillT === undefined ? {} : { testo: n.pillT })}
            dimensione="piccola"
            allinea="flex-start"
          />
          {n.rip && (
            <Ripresa
              tipo={n.rip.tipo}
              testo={n.rip.testo}
              colore="var(--testo)"
              tenue="var(--tenue)"
            />
          )}
          <span className="al-c-striscia__colonna-2">
            <span className="al-c-striscia__testo-3">{n.hours}</span>
            <span
              className="al-c-striscia__testo-4"
              title={n.range}
              style={{ color: "var(--tenue)" }}
            >
              {n.range}
            </span>
          </span>
          <span className="al-c-striscia__riga-2">
            {(n.cells ?? []).map((c, j) => (
              <span
                key={j}
                className="al-c-striscia__pillola-1"
                style={{
                  height: `${c.h}%`,
                  background: c.esito === null ? "var(--barretta-spenta)" : BARRETTE[c.esito],
                }}
              />
            ))}
          </span>
        </a>
      ))}
    </div>
  )

  return (
    <div className="al-c-striscia__blocco-1" data-modo={modo} data-accento={accento}>
      {corpo}
    </div>
  )
}
