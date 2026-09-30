/**
 * Cosa vuol dire, come risposta, cio' che l'utente ha scritto in un campo.
 *
 * Una casa sola perche' lo fanno tutte le sezioni che hanno un campo, e il vincolo e' lo stesso:
 * **l'Applica e' una transazione sola**, quindi un valore che l'API rifiuterebbe (un nome vuoto,
 * una misura a zero) non deve partire -- tornerebbe un 422 che annulla anche le risposte buone.
 * Qui non si valida al posto del backend: si decide solo se c'e' una risposta o no.
 */

/** Un testo che dice qualcosa, o niente: vuoto, o uguale a cio' che c'era, non e' una risposta. */
export function testo(scritto: string, cheCera?: string | null) {
  return scritto.trim() && scritto !== cheCera ? scritto : undefined
}

/** Una misura vale solo positiva -- uno zero e' un vuoto scritto male -- e un conto solo intero. */
export function misura(scritto: string, intero: boolean) {
  const n = Number(scritto)
  return scritto !== "" && n > 0 && (!intero || Number.isInteger(n)) ? n : undefined
}
