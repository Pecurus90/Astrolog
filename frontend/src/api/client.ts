import createClient from "openapi-fetch"

import type { paths } from "./schema"
import { tokenFromPage } from "./token"

/**
 * Il client dell'API, tipizzato sullo schema **generato** dal backend.
 *
 * `paths` viene da `schema.d.ts`, che nessuno scrive a mano: lo produce `tools/tipi.py` dallo
 * schema OpenAPI, e il cancello si accorge se ha smesso di corrispondere. Chiedere una rotta che
 * non esiste, o leggere un campo che l'API non manda, non compila.
 *
 * Vincolo non ovvio: il nome dell'intestazione e' scritto **anche** nel backend
 * (`astrolog/api/app.py`, `TOKEN_HEADER`) e nessuna macchina tiene insieme le due case -- non
 * viaggia nello schema, quindi non si puo' generare. Se una cambia, l'altra tace.
 */
const CHIAVE_HEADER = "X-AstroLog-Token"

const chiave = tokenFromPage(document)

export const api = createClient<paths>({
  baseUrl: "/",
  // Senza chiave NON si manda l'intestazione: e' il caso del NAS, e una intestazione vuota
  // sarebbe una chiave sbagliata, cioe' un 401 su ogni richiesta.
  ...(chiave === null ? {} : { headers: { [CHIAVE_HEADER]: chiave } }),
})

/** Un rifiuto con un corpo che dice perche', come quelli del backend. */
function rifiuto(status: number, code: string): Response {
  return new Response(JSON.stringify({ detail: { code } }), { status, headers: { "Content-Type": "application/json" } })
}

// Un errore senza corpo (il 502 di un proxy) darebbe `error` vuoto, e chi chiama `if (error)` non
// se ne accorgerebbe; una rete caduta lancerebbe l'errore del browser. Tutti e due diventano rifiuti.
api.use({
  async onResponse({ response }) {
    if (response.ok || (await response.clone().text()) !== "") return undefined
    return rifiuto(response.status, "no_body")
  },
  onError({ error }) {
    // un annullamento non e' un guasto: resta un'eccezione, che chi annulla scarta
    if (error instanceof DOMException && error.name === "AbortError") return undefined
    return rifiuto(503, "unreachable")
  },
})
