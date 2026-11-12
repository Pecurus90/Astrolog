import { Fragment, type ReactNode, useContext } from "react"

import { FormatoConf, MISURE } from "./ConfermareGuscio"
import { DomandaAperta, UnCaso } from "./Domanda"
import { numero, t } from "./i18n"
import { type QualeSezione, SEZIONI } from "./sezioniDaConfermare"

/** Cio' che una sezione per gruppo riceve: le voci, le risposte in mano, chi le scrive. */
export type PerGruppo<G, R> = {
  gruppi: G[]
  risposte: Record<string, R>
  onRisposta: (chiave: string, r: R | null) => void
}

/**
 * Una sezione aperta di *Da confermare* (tavola v82, 47-48): titolo, quante domande, il perche'
 * e le domande in fila.
 *
 * - **Il titolo nomina la sezione** (`aria-labelledby`); nome e ancora vengono da
 *   `sezioniDaConfermare`, dove li legge anche l'indice.
 * - **Il perche' si legge dove si lavora**: la sezione con la domanda aperta, e sul telefono il caso.
 * - **Sul telefono una voce sola**, quella del caso: dove si e' e come si va avanti li disegna la
 *   pagina, sopra e sotto la colonna delle sezioni.
 */
export function Sezione<V>({
  quale,
  domanda,
  voci,
  chiave,
  riga,
  piede,
}: {
  quale: QualeSezione
  domanda?: string
  /** Cio' su cui si risponde, nell'ordine in cui l'API lo manda: questa pagina non riordina. */
  voci: V[]
  /** La chiave di React di una voce. */
  chiave: (v: V) => string | number
  /** L'indice serve a comporre l'id di un campo: un percorso di cartella non e' un id valido. */
  riga: (v: V, indice: number) => ReactNode
  /** Cio' che sta sotto le domande: gli oggetti gia' riconosciuti. */
  piede?: ReactNode
}) {
  const { ancora, titolo } = SEZIONI[quale]
  const m = MISURE[useContext(FormatoConf)]
  const caso = useContext(UnCaso)
  const { aperta } = useContext(DomandaAperta)
  // `quale:` da solo e' un elenco aperto senza domanda (gli oggetti identificati): niente perche'
  const quiSiLavora =
    caso !== null || ((aperta?.startsWith(`${quale}:`) ?? false) && aperta !== `${quale}:`)
  const sola = caso === null ? null : voci[caso]
  return (
    <section
      className="al-conf__colonna-12"
      id={ancora}
      aria-labelledby={`${ancora}-nome`}
      style={{ borderRadius: m.angolo, padding: m.dentro }}
    >
      <header className="al-conf__colonna-13">
        <span className="al-conf__riga-11">
          <h2 className="al-conf__testo-9" id={`${ancora}-nome`} style={{ fontSize: m.titolo }}>
            {t(titolo)}
          </h2>
          {/* senza domande la sezione c'e' per il suo piede: "0 domande" non direbbe niente */}
          {voci.length > 0 && (
            <span className="al-conf__testo-10">
              {t("review.questions", { n: numero(voci.length) })}
            </span>
          )}
        </span>
        {domanda && quiSiLavora && <p className="al-conf__blocco-8">{domanda}</p>}
      </header>
      {caso === null
        ? voci.map((v, indice) => <Fragment key={chiave(v)}>{riga(v, indice)}</Fragment>)
        : sola !== undefined && sola !== null && riga(sola, caso)}
      {/* sul telefono un caso solo: il piede c'e' solo se la sezione non ha casi */}
      {(caso === null || voci.length === 0) && piede}
    </section>
  )
}
