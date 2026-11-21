import { QueryClient, type DefaultOptions } from "@tanstack/react-query"

/**
 * Quanto un dato letto resta buono: una pagina riaperta entro questo tempo non lo richiede.
 *
 * Chi scrive dall'app invalida cio' che ha cambiato, e la fine di ogni corsa del lavoro di
 * sottofondo invalida cio' che la corsa riscrive (`useFineDelLavoro`). Resta cio' che cambia da
 * fuori, un'altra scheda o un altro dispositivo: lo stesso minuto del battito da fermo dello stato.
 */
export const FRESCHI_MS = 60_000

/** La casa dei dati che arrivano dall'API: l'app ne ha una, ogni prova la sua con le stesse regole. */
export function nuoviDati(queries: DefaultOptions["queries"] = {}): QueryClient {
  return new QueryClient({ defaultOptions: { queries: { staleTime: FRESCHI_MS, ...queries } } })
}
