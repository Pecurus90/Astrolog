/**
 * Nei test le pagine a richiesta arrivano prima del primo test. Senza, React 19 trattiene 300 ms
 * ogni pagina che compare dopo un'attesa (FALLBACK_THROTTLE_MS, react-dom), e la suite passava da
 * 103 a 307 s: la prova iniziale di Stryker sforava i 5 minuti (Issue #103).
 *
 * Si usa `pigra` vera: si ricorda ogni componente e lo si fa partire con `_init`, il campo interno
 * di React.lazy (react 19.3). Un aggiornamento di React che lo cambia fa rosso `a-richiesta`.
 */
import { beforeEach, vi } from "vitest"

type Pigro = { _init: (payload: unknown) => unknown; _payload: unknown }

const { pigri } = vi.hoisted(() => ({ pigri: [] as Pigro[] }))

vi.mock("../src/pigra", async (originale) => {
  const modulo = await originale<typeof import("../src/pigra")>()
  const pigra: typeof modulo.pigra = (carica, nome) => {
    const componente = modulo.pigra(carica, nome)
    pigri.push(componente as unknown as Pigro)
    return componente
  }
  return { ...modulo, pigra }
})

async function arriva(pigro: Pigro): Promise<void> {
  try {
    pigro._init(pigro._payload)
  } catch (attesa) {
    // a file that does not arrive stays rejected: the page shows its box, as in the browser
    if (!(attesa instanceof Promise)) throw attesa
    await attesa.then(undefined, () => undefined)
  }
}

/** Le pagine nate finora arrivano: la chiama chi importa l'App dentro un test (`banco`). */
export async function pagineArrivate(): Promise<void> {
  await Promise.all(pigri.splice(0).map(arriva))
}

// before each test too: a test file imports its pages after this file's own hooks
beforeEach(pagineArrivate)
