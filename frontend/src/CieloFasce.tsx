import { oraDelSito } from "./i18n"

/**
 * The sky's background shared by the Dashboard's and the Weather's charts (boards v79 and v82):
 * the Sun's bands to the minute, their edges with the time over the chart, the grid and the
 * left scale. Only placed: the bands arrive written by the backend.
 */

export type Fascia = {
  starts_at: string
  ends_at: string
  kind: "day" | "civil" | "nautical" | "astronomical" | "dark"
}
export type Confine = { x: number; l: string; forte: boolean }

/** The band's step of darkness, as the sheet's `--banda-N`. */
export const LIVELLO = { day: 0, civil: 1, nautical: 2, astronomical: 3, dark: 4 } as const

/** Every edge between two bands, strong where the dark begins or ends. */
export function confiniDi(fasce: readonly Fascia[], x: (iso: string) => number): Confine[] {
  return fasce.slice(1).map((b, k) => ({
    x: x(b.starts_at),
    l: oraDelSito(b.starts_at),
    forte: b.kind === "dark" || fasce[k]?.kind === "dark",
  }))
}

/** The edges' times over the chart, on two rows so neighbours do not overlap. */
export function OreDeiConfini({
  confini,
  sinistra,
  destra = 0,
}: {
  confini: readonly Confine[]
  sinistra: number
  destra?: number
}) {
  return (
    <div
      style={{
        position: "absolute",
        left: sinistra,
        right: destra,
        top: 0,
        height: 34,
        pointerEvents: "none",
      }}
    >
      {confini.map((b, k) => (
        <span
          key={b.x}
          style={{
            position: "absolute",
            left: `${b.x / 10}%`,
            top: k % 2 ? 17 : 0,
            transform: "translateX(-50%)",
            fontSize: 11,
            color: "var(--prot-tenue)",
            whiteSpace: "nowrap",
            fontWeight: b.forte ? 600 : 400,
          }}
        >
          {b.l}
        </span>
      ))}
    </div>
  )
}

/** The left scale: top, middle and floor. */
export function ScalaDelCielo({ etichette }: { etichette: readonly string[] }) {
  return (
    <>
      {etichette.map((l, k) => (
        <span
          key={l}
          style={{
            position: "absolute",
            left: 0,
            top: `${[5, 51.25, 97.5][k]}%`,
            transform: "translateY(-50%)",
            fontSize: 11,
            color: "var(--prot-tenue)",
          }}
        >
          {l}
        </span>
      ))}
    </>
  )
}

/** Inside the chart's svg (1000 x 200): the bands, their edges and the grid. */
export function FasceDelCielo({
  fasce,
  confini,
  x,
}: {
  fasce: readonly Fascia[]
  confini: readonly Confine[]
  x: (iso: string) => number
}) {
  return (
    <>
      {fasce.map((b) => (
        <rect
          key={b.starts_at}
          x={x(b.starts_at)}
          y={0}
          width={Math.max(0, x(b.ends_at) - x(b.starts_at))}
          height={200}
          fill="var(--banda-colore)"
          style={{ fillOpacity: `var(--banda-${LIVELLO[b.kind]})` }}
        />
      ))}
      {confini.map((b) => (
        <line
          key={b.x}
          x1={b.x}
          x2={b.x}
          y1={0}
          y2={200}
          stroke="var(--prot-tenue)"
          strokeOpacity={0.45}
          vectorEffect="non-scaling-stroke"
          strokeDasharray="1 3"
        />
      ))}
      {[10, 102.5, 195].map((yy) => (
        <line
          key={yy}
          x1={0}
          x2={1000}
          y1={yy}
          y2={yy}
          stroke="var(--prot-tenue)"
          strokeOpacity={0.25}
          vectorEffect="non-scaling-stroke"
          strokeDasharray="2 4"
        />
      ))}
    </>
  )
}
