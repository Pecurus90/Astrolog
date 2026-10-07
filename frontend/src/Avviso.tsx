import type { ReactNode } from "react"

/**
 * Un avviso: com'e' andata, e cosa puoi farci.
 *
 * - **Il segno viene prima della parola, e non e' un colore.** WCAG 2.2, 1.4.1: chi non distingue
 *   verde e rosso deve capire lo stesso, quindi ogni tono porta il suo -- e sono quattro segni
 *   diversi, o due toni si leggerebbero uguali. Il segno e' `aria-hidden`: chi ascolta sente gia'
 *   l'urgenza dal ruolo, e sentirla due volte sarebbe rumore.
 * - **Il ruolo dice l'urgenza, e di solito lo decide il tono**: solo l'allarme interrompe chi sta
 *   leggendo (`alert`), gli altri aspettano una pausa (`status`). Un esito che non e' un guasto
 *   non ha diritto di tagliare la parola a nessuno. Chi chiama puo' **scavalcarlo**, e serve: la
 *   cartella che non si raggiunge e' un allarme, ma compare dopo un gesto di chi sta guardando
 *   quel punto -- interromperlo per dirgli cio' che sta gia' leggendo e' rumore.
 * - **Cio' che si puo' fare sta DENTRO l'avviso che lo motiva.** Un *Riprova* staccato costringe
 *   chi legge "la ricerca non ha risposto" a cercare altrove il rimedio, e il legame fra il
 *   guasto e cosa farci si perde per strada.
 * - **Il titolo e le azioni sono facoltativi, e senza non lasciano un posto vuoto**: un avviso di
 *   una riga resta di una riga.
 * - I segni sono scritti col loro codice e non incollati: il repo e' ASCII, e un glifo incollato
 *   in un file sorgente si rompe in silenzio su un terminale che non lo conosce.
 */
// Il neutro e' una `i` e non il glifo dell'informazione: quello, senza selettore di
// variazione, molti sistemi lo rendono come **emoji colorata** -- cioe' un segno che torna a
// dire le cose col colore, e per giunta senza prendere il carattere delle cifre che il foglio
// gli mette.
const SEGNI = { neutro: "i", attesa: "\u2026", buono: "\u2713", allarme: "\u26A0" }

// Solo il **modificatore**: il blocco si scrive dove la classe si monta, o la guardia del
// cancello non saprebbe leggere cio' che esce da qui e lo direbbe -- giustamente, perche' una
// classe che nessuno sa leggere e' una classe che nessuno controlla.
const TONI: Record<keyof typeof SEGNI, string> = {
  neutro: "",
  attesa: "as-avviso--attesa",
  // il v26 ha tolto il tono buono: resta il segno, la spunta, che lo dice da solo
  buono: "",
  allarme: "as-avviso--allarme",
}

export function Avviso({
  esito,
  titolo,
  azioni,
  ruolo,
  pagina,
  children,
}: {
  esito: keyof typeof SEGNI
  /** Cosa e' successo, in poche parole. Il testo sotto dice il resto. */
  titolo?: ReactNode
  /** Cosa si puo' fare adesso: bottoni piccoli, dentro l'avviso. */
  azioni?: ReactNode
  /** L'urgenza, quando non e' quella del tono. */
  ruolo?: "alert" | "status"
  /** In testa alla parte che manca, su carta: la riga di stato di pagina del foglio (v21). */
  pagina?: boolean
  children: ReactNode
}) {
  return (
    <div className={["as-avviso", TONI[esito], pagina ? "as-avviso--pagina" : ""].filter(Boolean).join(" ")}>
      <span className="as-avviso__segno" aria-hidden="true">
        {SEGNI[esito]}
      </span>
      <div className="as-avviso__corpo">
        {titolo && <p className="as-avviso__titolo">{titolo}</p>}
        <p className="as-avviso__testo" role={ruolo ?? (esito === "allarme" ? "alert" : "status")}>
          {children}
        </p>
      </div>
      {azioni && <div className="as-avviso__azioni">{azioni}</div>}
    </div>
  )
}
