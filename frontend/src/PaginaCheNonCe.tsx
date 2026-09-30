import { Bottone } from "./Bottone"
import { t } from "./i18n"

/** La pagina di un indirizzo che non esiste -- scritto a mano, o tenuto nei preferiti da una pagina
 *  che non c'e' piu': dice cos'e' successo e riporta a Casa, invece di un vuoto senza uscita. */
export function PaginaCheNonCe() {
  return (
    <main className="as-pagina">
      <h1 className="as-testata__titolo">{t("notFound.title")}</h1>
      <p>{t("notFound.why")}</p>
      <div className="as-pagina__azioni">
        <Bottone a="/">{t("notFound.home")}</Bottone>
      </div>
    </main>
  )
}
