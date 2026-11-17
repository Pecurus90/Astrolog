import type { components } from "./api/schema"

type Banda = components["schemas"]["BandIn"]["band"]

/**
 * Le bande di un filtro, nell'ordine in cui si leggono: le usano *Da confermare* e i moduli dei
 * filtri dell'Attrezzatura, che sono la stessa domanda.
 *
 * Sono il dominio chiuso di `backend/astrolog/vocab/filters.py`, che arriva qui nel tipo generato:
 * il compilatore controlla che non ne manchi nessuna e che non ce ne sia una in piu'.
 */
export const BANDE = [
  "L",
  "R",
  "G",
  "B",
  "HA",
  "HB",
  "OIII",
  "SII",
] as const satisfies readonly Banda[]
type Mancanti = Exclude<Banda, (typeof BANDE)[number]>
// se il backend aggiunge una banda, questa riga non compila finche' non entra nell'elenco
const _tutte: [Mancanti] extends [never] ? true : Mancanti = true
void _tutte

// [T] Da confermare.dc.html `BANDE` (349): come si scrivono, uguali in ogni lingua
const SCRITTE: Partial<Record<Banda, string>> = { HA: "Hα", HB: "Hβ" } // glifo-ok: board text

/** Una banda come si legge: H-alfa con la lettera greca, `OIII` com'e'. */
export const nomeDellaBanda = (b: Banda): string => SCRITTE[b] ?? b
