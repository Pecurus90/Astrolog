import { Children, type ReactElement, type ReactNode, cloneElement, isValidElement } from "react"

/**
 * Un campo: la sua parola e cio' in cui si scrive.
 *
 * Nasce dal difetto che questa fetta stava riparando, ricreato mentre la si riparava: le classi
 * `as-campo*` erano finite scritte a mano in **sette file, quarantasette righe**, esattamente come
 * `as-riga__conteggio` prima che diventasse `Dettaglio`. Il giorno che il design rinomina una di
 * quelle classi sono settanta correzioni, e nessuna macchina che segnali le dimenticate.
 *
 * - **L'etichetta e il controllo stanno insieme**, in una griglia: separati finiscono affiancati
 *   dentro `.as-riga__risposte`, che e' un flex allineato a destra, e lo stesso campo si dispone
 *   in due modi nella stessa pagina.
 * - **L'etichetta nomina la riga, non solo il campo**: due cartelle aperte sono due campi "Nome",
 *   e due campi che si chiamano uguale non si distinguono -- ne' per chi ascolta, ne' per chi ci
 *   scrive dentro. Per questo `etichetta` e' un testo che chi la usa compone col nome del gruppo.
 * - **L'errore si annuncia da se'** (`role="alert"`): legarlo al controllo basta a chi ha il
 *   fuoco li' dentro, ma un motivo che compare dopo un clic -- il fuoco e' sul bottone -- non lo
 *   sentirebbe nessuno.
 * - **L'errore sta sotto il campo che lo riguarda, non in un avviso staccato.** Un motivo scritto
 *   altrove lo legge chi guarda la pagina intera; chi arriva col tabulatore sente l'etichetta e
 *   basta. Per questo il testo si **lega** al controllo (`aria-describedby`) e il controllo
 *   dichiara di essere quello rotto (`aria-invalid`): due cose che il CSS non puo' fare.
 */
export function Campo({
  id,
  etichetta,
  errore,
  aspetta,
  cresce,
  tetto,
  children,
}: {
  /** Lo stesso che va sul controllo: e' cio' che lega l'etichetta a cio' che si scrive. */
  id: string
  etichetta: ReactNode
  /** Perche' quello che c'e' scritto non va. Assente finche' non c'e' niente da dire. */
  errore?: ReactNode
  /** Cio' che si e' scritto e' gia' partito e la risposta non c'e' ancora. Anima e basta: non
   *  spegne il controllo, perche' cambiare idea mentre si aspetta e' legittimo. Non convive con
   *  l'errore -- un campo o sta aspettando o ha gia' una risposta da dare. */
  aspetta?: boolean
  /** Quanto e' largo **da fermo**, quando il campo deve prendersi lo spazio che avanza accanto
   *  al suo bottone. Un token, non un numero. La misura va **sul campo** e non sul controllo,
   *  come fa il disegno: messa sull'input, l'etichetta resta larga quanto la riga e il campo non
   *  si stringe piu' insieme allo schermo. */
  cresce?: string
  /** La larghezza che il campo non passa, quando cio' che ci si scrive e' corto e un campo largo
   *  mezza pagina prometterebbe una frase. Un token, non un numero. */
  tetto?: string
  /** Il controllo **per primo**, e dopo di lui quello che lo accompagna (l'aiuto, un
   *  suggerimento): l'errore si lega al primo, e scriverlo secondo lo legherebbe all'aiuto. */
  children: ReactNode
}) {
  const detto = `${id}-errore`
  return (
    <div
      // I tre rami stanno **qui**, scritti per esteso: una classe composta dentro una
      // funzione la guardia della veste non la legge, e lo dice -- l'ha detto.
      className={
        errore
          ? "as-campo-modulo as-campo--errore"
          : aspetta
            ? "as-campo-modulo as-campo--caricamento"
            : "as-campo-modulo"
      }
      style={{ flex: cresce && `1 1 ${cresce}`, maxWidth: tetto }}
    >
      <label className="as-campo__etichetta" htmlFor={id}>
        {etichetta}
      </label>
      {/* Gli attributi vanno **sul controllo**, e ce li mette il campo: su un involucro non
          arrivano a chi ascolta -- `aria-describedby` su un `<div>` non descrive l'input che ha
          dentro -- e lasciarli scrivere alle pagine vorrebbe dire dimenticarli proprio dove il
          campo e' rotto.
          **`toArray` e non `map`**: `Children.map` chiama il suo callback anche dove un figlio non
          si rende (gli passa `null`), quindi un pezzo condizionale **spento** prima del controllo
          prenderebbe il posto zero. Il legame finirebbe su niente, in silenzio: nessun errore,
          nessuna prova rossa, e il motivo scritto sotto un campo che non lo nomina. `toArray` i
          figli falsi li scarta, quindi il primo e' il controllo. Oggi nessuna delle ventisette
          chiamate scrive il controllo dietro una condizione -- ma la forma costa una parola e il
          difetto sarebbe muto. Cio' che segue (l'aiuto, un suggerimento) resta com'e'. */}
      {Children.toArray(children).map((figlio, i) =>
        i === 0 && errore && isValidElement(figlio)
          ? cloneElement(figlio as ReactElement<Record<string, unknown>>, {
              "aria-describedby": detto,
              "aria-invalid": true,
            })
          : figlio,
      )}
      {/* **Il motivo si annuncia**, non solo si lega: `aria-describedby` lo fa sentire a chi ha
          il fuoco **sul campo**, e quando l'errore arriva dopo aver premuto un bottone il fuoco
          sta sul bottone -- il motivo compariva in silenzio. Era cosi' per il percorso del
          riconoscitore, che nasce proprio da un clic. Il segno non cromatico ce lo mette il
          foglio (`as-campo--errore`), quindi qui non manca niente di cio' che `Avviso` porta. */}
      {errore && (
        <p className="as-campo__errore" id={detto} role="alert">
          {errore}
        </p>
      )}
    </div>
  )
}

/** L'etichetta di un **gruppo** di controlli -- "Ordina", sopra tre bottoni -- che non e' il
 *  nome di un campo: non c'e' nessun `for` da legare, perche' non c'e' un controllo solo. La
 *  forma pero' e' la stessa, e la sua classe vive qui col resto del mattone: scritta a mano
 *  altrove, il giorno che il design la rinomina non la segnalerebbe niente. */
export function EtichettaDiGruppo({ children }: { children: ReactNode }) {
  return <span className="as-campo__etichetta">{children}</span>
}
