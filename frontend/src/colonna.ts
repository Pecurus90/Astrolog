import { useCallback, useState } from "react"

// The sheet's own threshold: `@container colonna (max-width: 899px)`, "soglia = telefono".
const SOGLIA_TELEFONO = 900

/** La colonna della pagina si misura: sotto la soglia del foglio la pagina ha un'altra forma, non
 *  un'altra veste. Torna se e' stretta e il `ref` da dare al contenitore che si misura. */
export function useColonnaStretta(): [boolean, (el: HTMLDivElement | null) => (() => void) | undefined] {
  const [stretta, setStretta] = useState(false)
  const misura = useCallback((el: HTMLDivElement | null) => {
    if (!el || typeof ResizeObserver === "undefined") return
    const occhio = new ResizeObserver((voci) => {
      const larga = voci[0]?.contentRect.width
      if (larga !== undefined) setStretta(larga < SOGLIA_TELEFONO)
    })
    occhio.observe(el)
    return () => occhio.disconnect()
  }, [])
  return [stretta, misura]
}
