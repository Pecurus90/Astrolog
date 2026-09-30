import { type ReactNode, useEffect, useId, useRef } from "react"

/**
 * Un dialogo che chiede conferma, e dice **cosa succede davvero**.
 *
 * Il foglio da' la veste; il comportamento e' codice, e sono quattro regole:
 *
 * - **Esc chiude**, perche' e' il modo in cui si esce da qualunque cosa che si e' aperta;
 * - **il fuoco entra** quando si apre, o chi ascolta resta fuori dal dialogo che ha appena
 *   chiesto qualcosa;
 * - **il fuoco torna** a cio' che l'ha aperto quando si chiude, o si riparte dall'inizio della
 *   pagina;
 * - **la pagina dietro e' DICHIARATA intoccabile**: `aria-modal` lo dice a chi ascolta e il
 *   fondale a chi vede -- ma il fuoco **non e' trattenuto**, e col tabulatore si esce. E'
 *   dichiarato in `docs/coda.md`, e si chiude con un anello sul primo e sull'ultimo elemento.
 *
 * Quello che il dialogo **non** fa e' decidere: chi lo apre passa le azioni, e la parola sul
 * bottone dice il gesto -- *Smetti di leggerla*, non *Conferma*.
 */
export function Dialogo({
  titolo,
  testa,
  largo = false,
  azioni,
  onChiudi,
  children,
}: {
  /** Come si chiama questa finestra per chi ascolta. Con `testa` resta **solo** il nome: la
   *  scritta a schermo la disegna chi chiama, e ripeterla in un titolo nascosto la farebbe
   *  leggere due volte. */
  titolo: string
  /** Un'intestazione tutta sua, al posto del titolo semplice: il pannello della Luna ci mette la
   *  faccia, la fase e la percentuale, che sono un blocco del foglio e non una riga di testo. */
  testa?: ReactNode
  /** La misura larga (`--colonna-grafico`): la vuole chi ci mette dentro una tela intera, che
   *  nella misura normale si rimpicciolirebbe insieme alle etichette. */
  largo?: boolean
  /** I bottoni, nell'ordine in cui si leggono: prima l'uscita, poi il gesto. */
  azioni: ReactNode
  onChiudi: () => void
  children: ReactNode
}) {
  const nome = useId()
  const dentro = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const prima = document.activeElement
    dentro.current?.focus()
    const allaTastiera = (e: KeyboardEvent) => {
      if (e.key === "Escape") onChiudi()
    }
    document.addEventListener("keydown", allaTastiera)
    return () => {
      document.removeEventListener("keydown", allaTastiera)
      if (prima instanceof HTMLElement) prima.focus()
    }
  }, [onChiudi])

  return (
    <div className="as-dialogo-fondale">
      <div
        aria-label={testa === undefined ? undefined : titolo}
        aria-labelledby={testa === undefined ? nome : undefined}
        aria-modal="true"
        className={largo ? "as-dialogo as-dialogo--largo" : "as-dialogo"}
        ref={dentro}
        role="dialog"
        tabIndex={-1}
      >
        {testa ?? (
          <h2 className="as-dialogo__titolo" id={nome}>
            {titolo}
          </h2>
        )}
        {children}
        <div className="as-dialogo__azioni">{azioni}</div>
      </div>
    </div>
  )
}
