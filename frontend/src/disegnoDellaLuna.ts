/**
 * La geometria della Luna: il disco della fase, nella pastiglia e in Stanotte.
 *
 * Non e' derivazione di dati -- quella sta nel backend -- e' **disegno**: numeri che diventano
 * un tracciato SVG. Sta in un file suo perche' e' la parte che si puo' provare senza montare
 * niente.
 */

/** Il raggio del disco nel suo `viewBox`, che e' `-12 -12 24 24` come nel foglio. */
const RAGGIO = 10

/**
 * Il tracciato della parte illuminata, o `null` quando non c'e' niente da illuminare.
 *
 * Due archi: il bordo del disco, e il **terminatore**, che e' una mezza ellisse la cui larghezza
 * viene dalla frazione illuminata -- piatta al quarto, larga come il disco alla piena.
 *
 * **Da che parte sta il lembo illuminato lo dice il backend** (`lit_side`), che conosce la fase
 * **e** l'emisfero: una crescente e' illuminata a destra da noi e a sinistra in Australia.
 */
export function tracciatoDellaLuna(illuminazionePct: number, aDestra: boolean): string | null {
  if (illuminazionePct <= 0) return null
  const frazione = illuminazionePct / 100
  const bordo = aDestra ? 1 : 0
  // Il terminatore curva dalla parte del lembo quando e' gibbosa, dall'altra quando e' falce.
  const terminatore = frazione > 0.5 ? bordo : 1 - bordo
  const larghezza = (RAGGIO * Math.abs(1 - 2 * frazione)).toFixed(2)
  return (
    `M 0 ${-RAGGIO} A ${RAGGIO} ${RAGGIO} 0 0 ${bordo} 0 ${RAGGIO}` +
    ` A ${larghezza} ${RAGGIO} 0 0 ${terminatore} 0 ${-RAGGIO} Z`
  )
}
