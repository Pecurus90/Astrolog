import { type ComponentType, type LazyExoticComponent, lazy } from "react"

/** A page's file that did not arrive: `Pigre` tells it apart from a fault of the page itself. */
export class PaginaNonArrivata extends Error {
  constructor(causa: unknown) {
    super("il file della pagina non e' arrivato", { cause: causa })
    this.name = "PaginaNonArrivata"
  }
}

/**
 * Un componente che si scarica la prima volta che va a schermo (React.lazy, react.dev/reference/
 * react/lazy): il suo modulo esce dal primo caricamento. Chi lo monta sta sotto `Pigre`.
 *
 * Il modulo esporta per nome, e `lazy` vuole il `default`: qui lo si prende per nome, cosi' il
 * modulo resta com'e' e un nome sbagliato non compila.
 */
// `any` as React.lazy itself: a page's props are its own, never inferred from here
export function pigra<M extends Record<K, ComponentType<any>>, K extends keyof M & string>(
  carica: () => Promise<M>,
  nome: K,
): Pigra<M[K]> {
  const componente = lazy(async () => {
    let modulo: M
    try {
      modulo = await carica()
    } catch (e) {
      throw new PaginaNonArrivata(e)
    }
    return { default: modulo[nome] }
  })
  // the browser keeps one download per module: asking it early is not asking it twice
  return Object.assign(componente, { precarica: () => void carica().catch(() => undefined) })
}

// a failed early download stays silent: the page asks again when it mounts, and Pigre tells it
export type Pigra<C extends ComponentType<any>> = LazyExoticComponent<C> & { precarica: () => void }
