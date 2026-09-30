import { Bottone } from "./Bottone"
import { type Chiave, t } from "./i18n"

/**
 * I due pezzi che ogni elenco impaginato dell'app ripete: **dove comincia la pagina dopo**, e il
 * bottone che la chiede.
 *
 * Nasce quando il secondo elenco arriva (l'Archivio e le Notti): le cinque righe di
 * `getNextPageParam` erano identiche byte per byte, e il bottone lo era a meno della parola.
 *
 * Vincolo non ovvio: **il totale lo dichiara il backend**, e la pagina dopo comincia dove
 * l'ultima e' finita. Contare le righe gia' viste sul client darebbe un numero diverso appena una
 * riga nasce o muore fra due chiamate.
 */

/** La forma che una pagina qualunque ha: cio' che serve per sapere se ce n'e' un'altra. */
type Pagina = { items: unknown[]; total: number; offset: number }

/** L'inizio della pagina dopo, o `undefined` quando si e' arrivati in fondo. */
export function paginaDopo(ultima: Pagina): number | undefined {
  const dopo = ultima.offset + ultima.items.length
  return dopo < ultima.total ? dopo : undefined
}

/** Il bottone che allunga l'elenco. Compare solo se c'e' dell'altro, e si spegne mentre chiede:
 *  due clic di fila chiederebbero due volte la stessa pagina. */
export function Altre({
  elenco,
  testo,
}: {
  elenco: { hasNextPage: boolean; isFetchingNextPage: boolean; fetchNextPage: () => unknown }
  testo: Chiave
}) {
  if (!elenco.hasNextPage) return null
  return (
    <div>
      <Bottone onClick={() => void elenco.fetchNextPage()} disabled={elenco.isFetchingNextPage}>
        {t(testo)}
      </Bottone>
    </div>
  )
}
