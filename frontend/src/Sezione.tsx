import type { ReactNode } from "react"

/**
 * Come si presenta una sezione che chiede **per gruppo**: le voci, le risposte gia' in mano e il
 * modo di darne una. Nove sezioni su dodici hanno questa identica firma, e riscriverla ogni volta
 * l'aveva resa il pezzo piu' copiato della pagina -- due sezioni erano diventate cosi' uguali da
 * far scattare il rilevatore di doppioni.
 *
 * La chiave del gruppo e' una stringa: e' il percorso di una cartella, una sigla, un fuso. Chi
 * risponde per numero (i filtri, gli strumenti) ha la sua firma, e non entra qui dentro.
 *
 * **Non lo usano tutte, e va bene cosi'**: cinque sezioni chiamano le loro voci col nome del
 * dominio -- `posti`, `mosaici`, `oggetti`, `scarti` -- e piegarle a dire `gruppi` toglierebbe
 * significato per far quadrare un tipo. Un posto non e' un gruppo.
 */
export type PerGruppo<G, R> = {
  gruppi: G[]
  risposte: Record<string, R>
  onRisposta: (chiave: string, r: R | null) => void
}

/**
 * Una sezione di *Da confermare*: una domanda, e sotto le righe su cui si risponde.
 *
 * Esiste per la stessa ragione di `Riga`: dodici sezioni scrivevano dodici volte lo stesso
 * involucro (`section` > `h2` > `p` > `ul`), e la veste l'avrebbe fatto scrivere dodici volte
 * ancora.
 *
 * - **Il titolo nomina la sezione** (`aria-label`): e' cosi' che le prove la trovano e che chi
 *   ascolta sa dove si trova, e i due devono restare la stessa cosa.
 * - **La domanda e' prosa e sta in cima**, non accanto alle righe: dice *perche'* l'app chiede, e
 *   si legge una volta sola.
 * - **L'elenco sta nel CORPO della carta**, non attaccato alla carta: il corpo e' un contenitore
 *   misurato, ed e' su di lui che le righe capiscono di essere in colonna stretta. Saltarlo non si
 *   vede finche' qualcuno non stringe la finestra -- e allora la soglia scatta sulla larghezza
 *   della pagina invece che su quella della carta. Lo avvisa il foglio stesso, con un commento
 *   scritto apposta (`stili/astrolog.css`, `.as-carta__corpo`).
 * - **L'elenco lo monta lei**: le dodici sezioni scrivevano lo stesso `map` con lo stesso `<li>`,
 *   e due di loro erano diventate abbastanza uguali da far scattare il rilevatore di doppioni. Chi
 *   la usa passa le **voci** e dice come si disegna una riga, non come si fa un elenco.
 * - **Niente conti qui dentro**: se un giorno accanto al titolo va "4 da risolvere", quel numero
 *   arriva dall'API come tutti gli altri. Un `voci.length` sarebbe un conto nel frontend.
 */
export function Sezione<V>({
  titolo,
  domanda,
  voci,
  chiave,
  riga,
  piede,
}: {
  titolo: string
  domanda?: ReactNode
  /** Cio' su cui si risponde, nell'ordine in cui l'API lo manda: questa pagina non riordina. */
  voci: V[]
  /** Come si chiama una voce: la chiave di React, e la stessa con cui la sezione la ritrova. */
  chiave: (v: V) => string | number
  /** L'indice serve a tre sezioni per comporre l'id di un campo: un percorso di cartella porta
   *  spazi e barre, e un id con dentro uno spazio non e' un id valido. */
  riga: (v: V, indice: number) => ReactNode
  /** Cio' che sta sotto le righe: il bottone che allunga un elenco a pagine. */
  piede?: ReactNode
}) {
  return (
    <section className="as-carta" aria-label={titolo}>
      <div className="as-carta__intestazione">
        <div>
          <h2 className="as-carta__titolo">{titolo}</h2>
          {domanda && <p className="as-carta__domanda">{domanda}</p>}
        </div>
      </div>
      {/* `--stretto` toglie il padding: le righe hanno gia' il loro, e sommarli le staccherebbe
          dal bordo della carta */}
      <div className="as-carta__corpo as-carta__corpo--stretto">
        <ul className="as-elenco">
          {voci.map((v, indice) => (
            <li key={chiave(v)}>{riga(v, indice)}</li>
          ))}
        </ul>
        {piede}
      </div>
    </section>
  )
}
