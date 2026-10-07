import { type Chiave, t } from "./i18n"

/** La pagina di una voce che c'e' nel telaio e non ancora nell'app (Marco, 7/10/2026): la voce
 *  resta al suo posto, e chi la apre legge che la pagina arriva, invece di un vuoto muto. */
export function ComingSoon({ pagina }: { pagina: Chiave }) {
  return (
    <div className="as-pagina">
      <div className="as-vuoto">
        <p className="as-vuoto__testo">{t("soon.title", { pagina: t(pagina) })}</p>
        <p className="as-vuoto__testo">{t("soon.why")}</p>
      </div>
    </div>
  )
}
