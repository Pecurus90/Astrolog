import { type ComponentType, type LazyExoticComponent, lazy } from "react"

/**
 * Un componente che si scarica la prima volta che va a schermo (React.lazy, react.dev/reference/
 * react/lazy): il suo modulo esce dal primo caricamento. Chi lo monta sta sotto un `Suspense`.
 *
 * Il modulo esporta per nome, e `lazy` vuole il `default`: qui lo si prende per nome, cosi' il
 * modulo resta com'e' e un nome sbagliato non compila.
 */
// `any` as React.lazy itself: a page's props are its own, never inferred from here
export function pigra<M extends Record<K, ComponentType<any>>, K extends keyof M & string>(
  carica: () => Promise<M>,
  nome: K,
): LazyExoticComponent<M[K]> {
  return lazy(async () => ({ default: (await carica())[nome] }))
}
