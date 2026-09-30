import type { Chiave } from "../i18n"

/**
 * Il perche' di un rifiuto dell'API, ridotto a un testo che si puo' leggere.
 *
 * Il backend manda un **codice** (`{"detail": {"code": "worker_busy"}}`), non una frase: cosi'
 * la stessa ragione si legge in ogni lingua. Qui il codice diventa una chiave del dizionario.
 *
 * Vincolo non ovvio: un codice che non conosciamo ricade sul messaggio generico invece di
 * finire a schermo com'e'. `worker_busy` non e' una frase che qualcuno debba leggere, e un
 * codice nuovo del backend non deve arrivare all'utente in inglese e in minuscolo.
 */
export function motivo(errore: unknown, codici: Record<string, Chiave>, generico: Chiave): Chiave {
  const dettaglio = (errore as { detail?: unknown } | null)?.detail
  const codice =
    typeof dettaglio === "object" && dettaglio !== null && "code" in dettaglio
      ? (dettaglio as { code?: unknown }).code
      : undefined
  return typeof codice === "string" ? (codici[codice] ?? generico) : generico
}
