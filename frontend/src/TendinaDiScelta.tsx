import { Campo } from "./Campo"

/** Una tendina di scelta fra righe dell'archivio, con la voce vuota in cima, che torna
 *  `undefined`: cosa voglia dire lo decide chi la usa. Una casa sola per "e' lo stesso di" (pezzi e
 *  filtri, nell'Attrezzatura) e per "uno dei miei filtri" (in *Da confermare*). */
export function TendinaDiScelta({
  id,
  etichetta,
  altri,
  valore,
  onScelta,
}: {
  id: string
  etichetta: string
  altri: { id: number; name: string }[]
  valore: number | undefined
  onScelta: (id: number | undefined) => void
}) {
  return (
    <Campo id={id} etichetta={etichetta}>
      <select
        className="as-campo-modulo__input"
        id={id}
        value={valore ?? ""}
        onChange={(e) => onScelta(e.target.value ? Number(e.target.value) : undefined)}
      >
        <option value="">--</option>
        {altri.map((a) => (
          <option key={a.id} value={a.id}>
            {a.name}
          </option>
        ))}
      </select>
    </Campo>
  )
}
