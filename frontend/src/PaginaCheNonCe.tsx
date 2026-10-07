import { Bottone } from "./Bottone"
import { t } from "./i18n"

/** La pagina di un indirizzo che non esiste -- scritto a mano, o tenuto nei preferiti da una pagina
 *  che non c'e' piu': dice cos'e' successo e riporta alla Dashboard, invece di un vuoto senza uscita. */
export function PaginaCheNonCe() {
  return (
    <div className="as-pagina">
      <div className="as-vuoto">
        <p className="as-vuoto__testo">{t("notFound.title")}</p>
        <p className="as-vuoto__testo">{t("notFound.why")}</p>
        <div className="as-vuoto__azioni">
          <Bottone a="/">{t("notFound.home")}</Bottone>
        </div>
      </div>
    </div>
  )
}
