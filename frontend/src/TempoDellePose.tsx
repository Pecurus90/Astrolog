import { numero, ore, t } from "./i18n"

/**
 * Il tempo di un gruppo di pose: **le ore solo se ci sono, e le pose senza tempo a parte**.
 *
 * Con tutte le pose mute "0 h" sarebbe un dato, e invece il tempo c'e': e' l'header che non lo dice.
 * Una casa sola perche' lo mostrano gli oggetti e i mosaici, e la stessa regola scritta due volte
 * divergerebbe alla prima correzione.
 */
export function TempoDellePose({
  secondi,
  senzaTempo,
  stacco = " ",
}: {
  secondi: number
  senzaTempo: number
  /** Cio' che separa le ore dai frame senza durata: uno spazio in un elenco, un punto in un dato. */
  stacco?: string
}) {
  // Lo spazio sta **fra** i due pezzi, non dopo: emesso sempre, lascia uno spazio in coda a chi
  // scrive il tempo dentro un elenco, e a schermo diventa "0,1 h , R 2 h".
  return (
    <>
      {secondi > 0 && <span>{t("review.objects.hours", { h: ore(secondi) })}</span>}
      {secondi > 0 && senzaTempo > 0 && stacco}
      {senzaTempo > 0 && <span>{t("review.objects.untimed", { n: numero(senzaTempo) })}</span>}
    </>
  )
}
