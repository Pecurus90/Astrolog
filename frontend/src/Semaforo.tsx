import type { ReactNode } from "react"

import type { components } from "./api/schema"

type Livello = components["schemas"]["WeatherMeasureOut"]["level"]

// La posizione della lampada accesa dice il giudizio anche senza colore (WCAG 1.4.1); senza
// giudizio nessuna e' accesa, tre anelli vuoti: un quarto stato, non un colore di un altro.
const TONI: Record<NonNullable<Livello> | "ignoto", string> = {
  go: "as-semaforo--buona",
  marginal: "as-semaforo--incerta",
  nogo: "as-semaforo--niente",
  ignoto: "as-semaforo--ignoto",
}

/**
 * Il semaforo del foglio (v21): tre lampade e la parola. Lo usa il Meteo per il verdetto della
 * notte e per il giudizio di ogni misura; la parola la scrive chi chiama, gia' tradotta.
 */
export function Semaforo({
  livello,
  grande,
  children,
}: {
  livello: Livello
  grande?: boolean
  children: ReactNode
}) {
  return (
    <span className={["as-semaforo", TONI[livello ?? "ignoto"], grande ? "as-semaforo--grande" : ""].filter(Boolean).join(" ")}>
      <span className="as-semaforo__lampade" aria-hidden="true">
        <i />
        <i />
        <i />
      </span>
      {children}
    </span>
  )
}
