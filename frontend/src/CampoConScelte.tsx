import type { ReactNode } from "react"
import { Campo } from "./Campo"

/**
 * Un campo di testo con le **scelte suggerite** sotto: si sceglie fra quelle, o si scrive un nome
 * che non c'e'. Lo usano le domande che accettano tutti e due -- di cosa e' un mosaico, quale ottica
 * era -- e scritto in ogni sezione sarebbe lo stesso pezzo in due forme.
 *
 * La lista si lega al campo con il suo `id`: due campi uguali nella stessa pagina hanno bisogno di
 * due `id` diversi, e li sceglie chi chiama.
 */
export function CampoConScelte({
  id,
  etichetta,
  valore,
  scelte,
  onScrivi,
}: {
  id: string
  etichetta: ReactNode
  valore: string
  scelte: string[]
  onScrivi: (scritto: string) => void
}) {
  return (
    <Campo id={id} etichetta={etichetta}>
      <input
        className="as-campo-modulo__input"
        id={id}
        list={`${id}-scelte`}
        value={valore}
        onChange={(e) => onScrivi(e.target.value)}
      />
      <datalist id={`${id}-scelte`}>
        {scelte.map((s) => (
          <option key={s} value={s} />
        ))}
      </datalist>
    </Campo>
  )
}
