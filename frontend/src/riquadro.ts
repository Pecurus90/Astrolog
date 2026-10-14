import { type KeyboardEvent, type RefObject, useEffect, useRef } from "react"

/** Tab dentro un riquadro aperto: dall'ultimo comando al primo e, con Maiusc, all'indietro. */
export function giraIlFuoco(ev: KeyboardEvent<HTMLElement>) {
  const comandi = [...ev.currentTarget.querySelectorAll<HTMLElement>("button:not([disabled]), a[href], [tabindex='0']")]
  const primo = comandi[0]
  const ultimo = comandi[comandi.length - 1]
  const qui = document.activeElement
  if (!primo || !ultimo) ev.preventDefault()
  else if (ev.shiftKey && (qui === primo || qui === ev.currentTarget)) {
    ev.preventDefault()
    ultimo.focus()
  } else if (!ev.shiftKey && qui === ultimo) {
    ev.preventDefault()
    primo.focus()
  }
}

/**
 * Un riquadro aperto sopra la pagina si chiude toccando fuori da `dentro` o con Esc (`chiudi(true)`:
 * il fuoco torna al comando). Sul documento: dopo un clic, o su Safari, il fuoco e' sul body.
 */
export function useRiquadro(aperto: boolean, dentro: RefObject<HTMLElement | null>[], chiudi: (esc: boolean) => void) {
  // l'ultimo `dentro` e `chiudi`: gli ascoltatori si attaccano una volta per apertura
  const ultimi = useRef({ dentro, chiudi })
  useEffect(() => {
    ultimi.current = { dentro, chiudi }
  })
  useEffect(() => {
    if (!aperto) return
    const fuori = (e: MouseEvent) => {
      if (!ultimi.current.dentro.some((r) => r.current?.contains(e.target as Node))) ultimi.current.chiudi(false)
    }
    const esc = (e: globalThis.KeyboardEvent) => {
      if (e.key === "Escape") ultimi.current.chiudi(true)
    }
    document.addEventListener("mousedown", fuori)
    document.addEventListener("keydown", esc)
    return () => {
      document.removeEventListener("mousedown", fuori)
      document.removeEventListener("keydown", esc)
    }
  }, [aperto])
}
