import { useEffect, useState } from "react"
import { useSearchParams } from "react-router"

import type { Formato } from "./Tema"

// [T] the delivery's switch (tema.js `telefono`): under 700 px the phone form
const SOTTO_PX = 700

/** Desktop or phone, as the delivery picks it: `?formato=` first, else the window's width. */
export function useFormato(): Formato {
  const [indirizzo] = useSearchParams()
  const scelto = indirizzo.get("formato")
  const [largo, setLargo] = useState(() => window.innerWidth)
  useEffect(() => {
    const segui = () => setLargo(window.innerWidth)
    window.addEventListener("resize", segui)
    return () => window.removeEventListener("resize", segui)
  }, [])
  if (scelto === "telefono" || scelto === "desktop") return scelto
  return largo < SOTTO_PX ? "telefono" : "desktop"
}
