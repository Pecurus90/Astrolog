import { Campo } from "./Campo"
import type { components } from "./api/schema"

type Banda = components["schemas"]["BandIn"]["band"]

/**
 * La tendina della banda di un filtro, con la voce vuota in cima: la usano la strada "a mano" di
 * *Da confermare* e il filtro scritto nell'Attrezzatura, che sono la stessa domanda.
 *
 * Le bande sono il dominio chiuso di `backend/astrolog/vocab/filters.py`, che arriva qui nel tipo
 * generato: l'elenco sotto lo ripete per l'ordine in cui si leggono, e il compilatore controlla che
 * non ne manchi nessuna e che non ce ne sia una in piu'.
 */
const BANDE = ["L", "R", "G", "B", "HA", "HB", "OIII", "SII"] as const satisfies readonly Banda[]
type Mancanti = Exclude<Banda, (typeof BANDE)[number]>
// se il backend aggiunge una banda, questa riga non compila finche' non entra nell'elenco
const _tutte: [Mancanti] extends [never] ? true : Mancanti = true
void _tutte


export function TendinaDellaBanda({
  id,
  etichetta,
  valore,
  onBanda,
}: {
  id: string
  etichetta: string
  valore: Banda | undefined
  onBanda: (b: Banda) => void
}) {
  return (
    <Campo id={id} etichetta={etichetta}>
      <select
        className="as-scelta"
        id={id}
        value={valore ?? ""}
        onChange={(e) => onBanda(e.target.value as Banda)}
      >
        <option value="">--</option>
        {BANDE.map((b) => (
          <option key={b} value={b}>
            {b}
          </option>
        ))}
      </select>
    </Campo>
  )
}
