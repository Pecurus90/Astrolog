/**
 * Le poche disposizioni che il foglio del design **non ha come mattone**, scritte una volta.
 *
 * Il disegno del fornitore le scrive in linea coi suoi token, e noi lo seguiamo alla lettera: qui
 * non nasce una veste nostra, nasce la **casa** di cio' che il disegno ripete. Nel montaggio lo
 * stesso blocco era finito in tre file, e il giorno che la spaziatura cambia sarebbero tre
 * correzioni di cui nessuna macchina segnala le dimenticate.
 *
 * Una riga entra qui quando la usano **due schermate**: una sola la tiene dove sta, con accanto il
 * commento che dice perche'.
 */
import type { CSSProperties } from "react"

/** Un campo e il suo bottone **sulla stessa riga**: sono un gesto solo, e incolonnati sembrano
 *  due cose da fare. `flex-end` li allinea sul fondo, perche' il campo ha l'etichetta sopra e il
 *  bottone no; `wrap` li incolonna da se' quando lo schermo si stringe. */
export const CAMPO_E_BOTTONE: CSSProperties = {
  display: "flex",
  gap: "var(--spazio-2)",
  alignItems: "flex-end",
  flexWrap: "wrap",
}
