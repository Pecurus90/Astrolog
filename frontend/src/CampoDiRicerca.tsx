import type { InputHTMLAttributes, ReactNode, Ref } from "react"

import { Icon } from "./Icons"
import { t } from "./i18n"

/**
 * Il campo di ricerca del foglio (v32, `53-campo-cerca`): un pozzo con la lente, e in coda cio' che lo
 * accompagna (il tasto, o il segno dell'attesa).
 *
 * E' un mattone perche' lo usano la ricerca nella barra in alto e la barra dell'Archivio: la sua
 * classe si scrive qui e basta (`tools/controlli_veste.py`, `MATTONI`). Non e' `Campo`, che e' il
 * campo dei moduli: quello ha un'etichetta a vista e un errore sotto.
 *
 * - **Il nome lo porta l'input** (`aria-label`): la tavola non ha un'etichetta a vista, e la lente
 *   da sola non dice niente a chi ascolta.
 * - `nellaBarra` e' il posto del campo nella barra dell'Archivio, che lo fa crescere.
 */
export function CampoDiRicerca({
  etichetta,
  nellaBarra = false,
  coda,
  ref,
  ...input
}: {
  etichetta: string
  nellaBarra?: boolean
  coda?: ReactNode
  ref?: Ref<HTMLInputElement>
} & Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "className" | "aria-label">) {
  return (
    <label className={nellaBarra ? "as-campo-cerca as-restringi__cerca" : "as-campo-cerca"}>
      <Icon name="cerca" className="as-campo-cerca__icona" />
      <input type="search" aria-label={etichetta} autoComplete="off" ref={ref} {...input} />
      {coda}
    </label>
  )
}

/** Il segno dell'attesa con la parola: cio' che hai scritto e' partito e la risposta non c'e'. */
export function Cerco() {
  return (
    <span className="as-campo-cerca__attesa">
      <span className="as-attesa" aria-hidden="true" />
      {t("search.busy")}
    </span>
  )
}
