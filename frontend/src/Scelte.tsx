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
}: {
  domanda: string
  nome: string
  opzioni: readonly { valore: V; etichetta: string }[]
  scelta: V | null | undefined
  onScelta: (valore: V) => void
}) {
  return (
    <fieldset>
      <legend>{domanda}</legend>
      {opzioni.map((o) => (
        <label key={String(o.valore)}>
          <input
            type="radio"
            name={nome}
            value={String(o.valore)}
            checked={scelta === o.valore}
            onChange={() => onScelta(o.valore)}
          />
          {o.etichetta}
        </label>
      ))}
    </fieldset>
  )
}
