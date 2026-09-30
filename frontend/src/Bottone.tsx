import type { ReactNode } from "react"
import { Link } from "react-router"

/**
 * Un bottone: cosa si puo' fare, e con quanta forza lo si propone.
 *
 * Stessa ragione di `Campo`: `as-bottone*` era scritta a mano in **dodici file**. Qui la classe sta
 * in un posto solo, e chi la usa sceglie il **verso** -- non il nome della classe.
 *
 * - **primario**: l'azione che la riga propone (unisci, applica). Uno per riga, o non e' primario.
 * - **tenue**: l'alternativa, o cio' che apre un pannello.
 * - **nudo**: cio' che si fa raramente e non deve tirare l'occhio ("non e' in elenco").
 * - **errore**: l'azione che **non e' andata**, e che si puo' riprovare. Porta il triangolo e il
 *   bordo d'allarme, ma la parola dice da se' cos'e' successo ("Non salvato -- riprova"): il
 *   colore da solo non dice niente (WCAG 2.2, 1.4.1), e qui non deve, perche' un bottone rosso
 *   somiglia a un bottone che cancella.
 * - **distruttivo**: il gesto che toglie qualcosa. Non si preme per sbaglio, perche' sta in un
 *   dialogo che ha gia' detto cosa succede -- e la parola e' il gesto, non "Conferma".
 *
 * Il tipo e' sempre `button`: dentro una pagina che non ha `<form>`, un bottone senza tipo e' un
 * `submit` che ricarica la pagina. **Con `a` diventa un collegamento** e non un bottone: un gesto
 * che porta altrove e' un indirizzo -- si apre in una scheda nuova, si copia, il tasto indietro
 * funziona -- e il foglio lo prevede (`.as-bottone` dichiara `text-decoration: none` apposta).
 * `a` e `onClick` si escludono a vicenda, e lo dice il tipo: scriverli insieme non compila.
 */
const VERSI = {
  primario: "as-bottone as-bottone--primario",
  tenue: "as-bottone as-bottone--tenue",
  nudo: "as-bottone as-bottone--nudo",
  errore: "as-bottone as-bottone--errore",
  distruttivo: "as-bottone as-bottone--distruttivo",
}

type Comune = {
  verso?: keyof typeof VERSI
  /** Dentro una riga i bottoni sono piccoli: la riga e' alta quanto una riga. */
  piccolo?: boolean
  /** Il nome per chi ascolta, quando quello che si legge si ripete su ogni riga ("Cambia").
   *  Comincia con la parola che si vede, cosi' chi lo pronuncia a voce lo ritrova. */
  nome?: string | undefined
  /** Cio' che il bottone **fa**, quando la sua parola da sola non basta: "Usa questa cartella"
   *  ha senso solo insieme a quale cartella sia, che sta scritta accanto. E' l'id di quel
   *  testo, non una sua copia: due verita' sullo stesso percorso divergerebbero. */
  descrittoDa?: string | undefined
  children: ReactNode
}

/** Un gesto che si preme, oppure uno che porta a un indirizzo: mai tutti e due, e lo dice il tipo.
 *  **`disabled` e l'interruttore stanno solo da una parte**: un collegamento spento non esiste --
 *  l'attributo su un `<a>` non fa niente, e il gesto resterebbe premibile mentre sembra spento --
 *  e un collegamento non apre un pannello, ci porta. */
type Premuto = Comune & {
  onClick: () => void
  disabled?: boolean
  a?: never
  /** L'id del pannello che questo bottone apre e chiude, se **resta** mentre il pannello e'
   *  aperto: allora e' un interruttore, e chi ascolta deve sapere se ora e' aperto o chiuso.
   *  Un bottone che al primo tocco sparisce non lo e' -- direbbe `false` per sempre, e
   *  nominerebbe un id che esiste solo quando lui non c'e'. */
  governa?: string | undefined
  aperto?: boolean
}
type Portato = Comune & {
  a: string
  onClick?: never
  disabled?: never
  governa?: never
  aperto?: never
}

export function Bottone({
  verso = "tenue",
  piccolo = false,
  onClick,
  a,
  disabled = false,
  nome,
  descrittoDa,
  governa,
  aperto,
  children,
}: Premuto | Portato) {
  // La veste e' scritta **per esteso in tutti e due i rami**, e non messa in una variabile:
  // `classi_inventate` (tools/controlli_veste.py) legge i letterali scritti nell'attributo della
  // classe, e da una variabile non esce nessuna classe -- e' proprio la forma in cui una classe
  // sbagliata sfugge alla guardia. Due righe uguali sono il prezzo, e lo si paga volentieri.
  if (a !== undefined) {
    return (
      <Link
        aria-describedby={descrittoDa}
        aria-label={nome}
        className={`${VERSI[verso]}${piccolo ? " as-bottone--piccolo" : ""}`}
        to={a}
      >
        {children}
      </Link>
    )
  }
  return (
    <button
      className={`${VERSI[verso]}${piccolo ? " as-bottone--piccolo" : ""}`}
      type="button"
      aria-label={nome}
      aria-describedby={descrittoDa}
      aria-controls={governa}
      aria-expanded={governa === undefined ? undefined : aperto === true}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  )
}
