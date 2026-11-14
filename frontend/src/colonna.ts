import { useCallback, useState } from "react"

// The sheet's own threshold: `@container colonna (max-width: 899px)`, "soglia = telefono".
const SOGLIA_TELEFONO = 900

type Misura = (el: HTMLDivElement | null) => (() => void) | undefined

/** La larghezza misurata di un contenitore, e il `ref` da dargli. Sotto `tolleranza` px di
 *  scarto resta la misura di prima (una barra che compare non ridisegna). */
export function useLarghezza(tolleranza = 0): [number | undefined, Misura] {
  const [larga, setLarga] = useState<number>()
  const misura = useCallback<Misura>(
    (el) => {
      if (!el || typeof ResizeObserver === "undefined") return
      const occhio = new ResizeObserver((voci) => {
        const w = voci[0]?.contentRect.width
        if (w === undefined) return
        setLarga((prima) => (prima !== undefined && Math.abs(w - prima) <= tolleranza ? prima : w))
      })
      occhio.observe(el)
      return () => occhio.disconnect()
    },
    [tolleranza],
  )
  return [larga, misura]
}

/** La colonna della pagina si misura: sotto la soglia del foglio la pagina ha un'altra forma, non
 *  un'altra veste. Torna se e' stretta e il `ref` da dare al contenitore che si misura. */
export function useColonnaStretta(): [boolean, Misura] {
  const [larga, misura] = useLarghezza()
  return [larga !== undefined && larga < SOGLIA_TELEFONO, misura]
}
