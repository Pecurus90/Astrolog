import type { ReactNode } from "react"

import { type Chiave, t } from "./i18n"

/**
 * Uno **stato vuoto**: non un elenco senza righe, ma cosa fare perche' una riga nasca.
 *
 * Stessa ragione di `Bottone` e `Campo`: le classi `as-vuoto*` erano scritte a mano in tre
 * sezioni, quattro righe identiche ognuna, e il giorno che il design ne rinomina una sarebbero
 * state tre correzioni di cui nessuna macchina avrebbe segnalato le dimenticate.
 *
 * Il **titolo** e il **perche'** sono chiavi, non testo: un letterale qui non passerebbe dal
 * dizionario e resterebbe italiano in ogni lingua. Cio' che cambia da una sezione all'altra --
 * un gesto da proporre, una nota che rassicura -- si passa come figli, e va **dopo** il perche',
 * che e' l'ordine che il foglio disegna.
 */
export function Vuoto({
  titolo,
  perche,
  sotto = 2,
  children,
}: {
  titolo: Chiave
  perche: Chiave
  /** Sotto quale livello di titolo sta: il suo e' quello **dopo**. Un titolo che salta un livello
   *  e' una violazione vera (axe, `heading-order`), e chi la vede e' chi naviga per titoli -- non
   *  si accorge di aver perso una sezione, crede che non ci sia. Di fabbrica sotto il titolo di
   *  una **sezione**; chi sta direttamente sotto quello della pagina passa `sotto={1}`. */
  sotto?: 1 | 2
  children?: ReactNode
}) {
  const Titolo = sotto === 1 ? "h2" : "h3"
  return (
    <div className="as-vuoto">
      <div className="as-vuoto__disegno" aria-hidden="true" />
      <Titolo className="as-vuoto__titolo">{t(titolo)}</Titolo>
      <p className="as-vuoto__testo">{t(perche)}</p>
      {children}
    </div>
  )
}

/** La riga tenue sotto lo stato vuoto: quella che toglie la paura invece di chiedere qualcosa
 *  ("non cancella niente", "l'app funziona lo stesso"). */
export function NotaDelVuoto({ children }: { children: ReactNode }) {
  return <p className="as-vuoto__nota">{children}</p>
}

/** I gesti di uno stato vuoto, nella loro riga. */
export function AzioniDelVuoto({ children }: { children: ReactNode }) {
  return <div className="as-vuoto__azioni">{children}</div>
}
