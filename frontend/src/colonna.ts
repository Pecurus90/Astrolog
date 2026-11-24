import { useCallback, useState } from "react"

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
