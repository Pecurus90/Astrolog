/**
 * La chiave di avvio, letta dalla pagina che il backend ha servito.
 *
 * "L'app si apre e basta" (Marco, 13/9/2026): e' il backend a mettere la chiave dentro la
 * pagina, in un `<meta>`, a ogni richiesta. Qui si legge e basta -- nessuno la incolla, nessuno
 * la salva, e non deve finire in un indirizzo ne' in una memoria del browser: vale per un avvio
 * solo, e al prossimo la pagina ne ricevera' un'altra.
 *
 * Sul NAS la chiave non c'e' (la rete di casa e' fidata) e la pagina non ne porta nessuna:
 * `null` vuol dire "non serve", non "non l'ho trovata" -- chi chiama non deve inventare
 * un'intestazione vuota, che il backend rifiuterebbe.
 */
export function tokenFromPage(doc: Pick<Document, "querySelector">): string | null {
  const valore = doc.querySelector('meta[name="astrolog-token"]')?.getAttribute("content") ?? ""
  return valore === "" ? null : valore
}
