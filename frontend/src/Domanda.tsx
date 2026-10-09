import { type ReactNode, createContext, useContext } from "react"

import { Bottone } from "./Bottone"
import { Soggetti } from "./Soggetti"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"

type CosaHaiRipreso = components["schemas"]["Subjects"]

/**
 * Quale domanda e' aperta: **una sola in tutta la pagina**. Lo tiene la pagina e lo leggono le
 * domande e le sezioni, senza passarlo di mano in mano per cinque file.
 */
export const DomandaAperta = createContext<{ aperta: string | null; apri: (id: string) => void }>({
  aperta: null,
  apri: () => {},
})

/** Lo stato di una risposta: segno e parola, mai il colore da solo. `era` dice cosa c'era prima. */
export function Risposta({
  salvata,
  inMano,
  era,
  children,
}: {
  salvata: boolean
  inMano: boolean
  era?: string | undefined
  /** Al posto della parola dello stato: il conto di una sezione chiusa. */
  children?: ReactNode
}) {
  if (inMano && salvata) {
    return (
      <span className="as-risposta as-risposta--cambiata">
        {children ?? t("review.state.changed")}
        {era && <span className="as-risposta__era">{` \u00b7 ${t("review.state.was", { era })}`}</span>}
      </span>
    )
  }
  if (inMano) return <span className="as-risposta as-risposta--ora">{children ?? t("review.state.inHand")}</span>
  if (salvata) return <span className="as-risposta as-risposta--salvata">{children ?? t("review.state.saved")}</span>
  return <span className="as-risposta as-risposta--dare">{children ?? t("review.state.open")}</span>
}

/**
 * Una domanda di *Da confermare*: **chiusa** e' una riga (di cosa si parla, la risposta in breve,
 * lo stato, il gesto che la apre); **aperta** e' la scheda coi suoi controlli.
 *
 * - **I controlli esistono solo da aperta**: cio' che la sezione tiene in mano (una scelta, un
 *   nome scritto) vive nella sezione, e riparte dalla risposta in mano: una sezione chiusa si smonta.
 * - **Il nome viene per primo**: le prove e chi ascolta riconoscono la domanda da come comincia.
 * - **Il gesto dice di quale riga**: a vista tutti i bottoni si chiamano "Rispondi" o "Cambia".
 */
export function Domanda({
  id,
  voce,
  nome,
  cifre = false,
  frames,
  ripreso,
  dettagli,
  salvata,
  inMano,
  era,
  breve,
  children,
}: {
  /** Quale domanda e', in tutta la pagina: `sezione:chiave`. */
  id: string
  /** Il nome a parole, per chi ascolta e per il gesto. */
  voce: string
  nome: ReactNode
  /** Un percorso, una sigla, due coordinate: col carattere delle cifre. */
  cifre?: boolean
  frames: number
  ripreso?: CosaHaiRipreso | undefined
  /** Cio' che quella domanda ha di suo, dopo i frame. */
  dettagli?: ReactNode
  salvata: boolean
  inMano: boolean
  era?: string | undefined
  /** La risposta in breve, o fra cosa si sceglie: si legge da chiusa. */
  breve: ReactNode
  children: ReactNode
}) {
  const { aperta, apri } = useContext(DomandaAperta)
  const quanti = t("review.frames", { n: numero(frames) })
  const stato = <Risposta era={era} inMano={inMano} salvata={salvata} />

  if (aperta !== id) {
    const gesto = t(salvata || inMano ? "review.change" : "review.answer")
    return (
      <div className="as-domanda-riga">
        <div className="as-domanda-riga__chi">
          <span className={cifre ? "as-domanda-riga__nome as-conferma__cifre" : "as-domanda-riga__nome"}>{nome}</span>{" "}
          <span className="as-domanda-riga__frame">{quanti}</span>
        </div>
        <p className="as-domanda-riga__breve">{breve}</p>
        {stato}
        <Bottone nome={`${gesto}: ${voce}`} piccolo onClick={() => apri(id)}>
          {gesto}
        </Bottone>
      </div>
    )
  }
  return (
    <article className="as-domanda" aria-label={voce}>
      <div className="as-domanda__testa">
        <div className="as-domanda__capo">
          {/* Dopo il nome uno spazio scritto: nel testo non si attacca a cio' che lo segue. */}
          <h3 className={cifre ? "as-domanda__nome as-conferma__cifre" : "as-domanda__nome"}>{nome}</h3>{" "}
          {stato}
        </div>
        {/* Fra un dato e l'altro c'e' uno spazio scritto: nel testo, che e' cio' che leggono le
            prove e chi ascolta, senza di lui si attaccano. */}
        <p className="as-domanda__frame">
          {quanti} {ripreso && <Soggetti soggetti={ripreso} />} {dettagli}
        </p>
      </div>
      <div className="as-domanda__corpo">{children}</div>
    </article>
  )
}
