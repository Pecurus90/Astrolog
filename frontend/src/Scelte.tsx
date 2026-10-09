import type { ReactNode } from "react"

/**
 * Una domanda a scelta singola: un gruppo che la nomina e una scelta per ogni risposta possibile.
 *
 * Una casa sola perche' le sezioni che chiedono "quale di queste" sono tante -- il filtro di una
 * camera, il luogo di un posto, il mosaico -- e il vincolo e' lo stesso per tutte:
 * **il gruppo nomina la riga**, perche' con due righe aperte ci sono due terne di scelte uguali e
 * chi legge con uno schermo deve sapere di quale sta rispondendo. Cosa voglia dire scegliere, e se
 * ridare la risposta gia' data mandi qualcosa, lo decide chi la usa.
 */
export function Scelte<V extends string | number>({
  domanda,
  nome,
  opzioni,
  scelta,
  onScelta,
  children,
}: {
  domanda: string
  nome: string
  opzioni: readonly { valore: V; etichetta: string }[]
  scelta: V | null | undefined
  onScelta: (valore: V) => void
  /** Cio' che la scelta apre (un campo, una tendina): sotto le voci. */
  children?: ReactNode
}) {
  return (
    <fieldset className="as-scelta-fissa">
      {/* La scheda dice gia' di cosa si parla: la domanda resta per chi legge con la voce. */}
      <legend className="as-scelta-fissa__domanda as-solo-lettori">{domanda}</legend>
      <div className="as-scelta-fissa__voci">
        {opzioni.map((o) => (
          <label key={String(o.valore)} className="as-scelta-fissa__voce">
            <input
              type="radio"
              name={nome}
              value={String(o.valore)}
              checked={scelta === o.valore}
              onChange={() => onScelta(o.valore)}
            />
            <span className="as-scelta-fissa__testo">
              <span className="as-scelta-fissa__nome">{o.etichetta}</span>
            </span>
          </label>
        ))}
      </div>
      {children && <div className="as-scelta-fissa__dopo">{children}</div>}
    </fieldset>
  )
}
