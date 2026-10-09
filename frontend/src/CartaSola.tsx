import { type ReactNode, useId } from "react"

/**
 * Una carta sola al centro dello schermo, fuori dal telaio: le risposte ritrovate prima del primo
 * avvio, e la sua chiusura. Un titolo, una riga sotto, i conti (la parola a sinistra, il dato a
 * destra) e i comandi, col pieno per ultimo.
 */
export function CartaSola({
  titolo,
  sotto,
  conti,
  azioni,
  children,
}: {
  titolo: string
  sotto?: ReactNode
  conti: readonly { nome: string; dato: ReactNode }[]
  azioni: ReactNode
  /** Cio' che e' andato storto, sotto i comandi che l'hanno provocato. */
  children?: ReactNode
}) {
  const id = useId()
  return (
    <main className="as-entra">
      <div className="as-entra__colonna as-entra__colonna--sola">
        <p className="as-soprattitolo as-soprattitolo--nudo">AstroLog</p>
        <section className="as-carta as-ritrovate" aria-labelledby={id}>
          <div className="as-passo__capo">
            <h1 className="as-ritrovate__titolo" id={id}>
              {titolo}
            </h1>
            {sotto && <p className="as-ritrovate__quando">{sotto}</p>}
          </div>
          <ul className="as-conti">
            {conti.map((c) => (
              <li key={c.nome} className="as-conti__voce">
                <span className="as-conti__nome">{c.nome}</span>
                <span className="as-conti__dato">{c.dato}</span>
              </li>
            ))}
          </ul>
          <div className="as-ritrovate__azioni">{azioni}</div>
          {children}
        </section>
      </div>
    </main>
  )
}

/** Mentre l'app si apre: una riga sola, col segno dell'attesa. Non e' ancora la pagina: niente
 *  `main`, o chi la cerca troverebbe questa e la perderebbe un attimo dopo. */
export function SiApre({ children }: { children: ReactNode }) {
  return (
    <div className="as-entra">
      <div className="as-entra__colonna as-entra__colonna--sola">
        <p className="as-soprattitolo as-soprattitolo--nudo">AstroLog</p>
        <p className="as-entra__attesa" role="status">
          <span className="as-attesa" aria-hidden="true" />
          {children}
        </p>
      </div>
    </div>
  )
}
