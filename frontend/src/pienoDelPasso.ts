import { useEffect } from "react"

/**
 * Un passo dice al guscio che **ora ha un comando pieno suo** (aggiungi, verifica e salva): il
 * guscio fa scendere a tenue quello che manda avanti, cosi' il pieno a schermo resta uno solo.
 * Uscendo dal passo lo ritira. Fuori dal primo avvio nessuno ascolta, e non fa niente.
 */
export function usePienoDelPasso(onOffre: ((offre: boolean) => void) | undefined, offre: boolean) {
  useEffect(() => {
    onOffre?.(offre)
    return () => onOffre?.(false)
  }, [offre, onOffre])
}
