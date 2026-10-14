import { type RefObject, useEffect } from "react"

/**
 * Un riquadro aperto sopra la pagina si chiude toccando fuori da `dentro` o con Esc (`chiudi(true)`:
 * il fuoco torna al comando). Sul documento: dopo un clic, o su Safari, il fuoco e' sul body.
 */
export function useRiquadro(aperto: boolean, dentro: RefObject<HTMLElement | null>[], chiudi: (esc: boolean) => void) {
  useEffect(() => {
    if (!aperto) return
    const fuori = (e: MouseEvent) => {
      if (!dentro.some((r) => r.current?.contains(e.target as Node))) chiudi(false)
    }
    const esc = (e: KeyboardEvent) => {
      if (e.key === "Escape") chiudi(true)
    }
    document.addEventListener("mousedown", fuori)
    document.addEventListener("keydown", esc)
    return () => {
      document.removeEventListener("mousedown", fuori)
      document.removeEventListener("keydown", esc)
    }
  }, [aperto, dentro, chiudi])
}
