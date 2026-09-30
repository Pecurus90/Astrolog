import { useQuery } from "@tanstack/react-query"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { api } from "./api/client"
import { numero, t } from "./i18n"

/**
 * La casa: quante cose ci sono da confermare, e lo stato dell'app.
 *
 * Era dentro `App.tsx` quando l'app era una pagina sola. Adesso `App` fa il portiere -- il
 * cancelletto del primo avvio e la navigazione -- e questa e' una pagina come le altre.
 *
 * Qui non si calcola niente: `to_confirm` lo conta il backend e arriva gia' fatto. E' la regola
 * che rende la veste finale un cambio d'abito invece di una riscrittura.
 */
export function Home() {
  const pagina = useQuery({
    queryKey: ["review"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/review")
      // Un errore non si inghiotte: senza questa riga la pagina mostrerebbe "0 da confermare"
      // su un archivio che non ha risposto, che e' peggio di un messaggio brutto.
      if (error) throw new Error(t("review.failed"))
      return data
    },
  })
  const salute = useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/health")
      if (error) throw new Error(t("health.failed"))
      return data
    },
  })

  const ricarica = () => {
    void pagina.refetch()
    void salute.refetch()
  }

  return (
    <main className="as-pagina">
      <div className="as-testata">
        <h1 className="as-testata__titolo">{t("app.title")}</h1>
      </div>

      <section className="as-carta">
        <div className="as-carta__intestazione">
          <div>
            {/* il titolo della **cosa**, non la voce di menu: la carta parla della pagina Da
                confermare, e la voce di menu e' un'altra cosa che per caso si chiama uguale */}
            <p className="as-soprattitolo">{t("review.title")}</p>
            {pagina.isPending && <p className="as-carta__domanda">{t("review.loading")}</p>}
            {pagina.error && <Avviso esito="allarme">{pagina.error.message}</Avviso>}
            {pagina.data && (
              <p className="as-numero">
                {numero(pagina.data.to_confirm)}{" "}
                <span className="as-numero__unita">{t("review.toConfirm")}</span>
              </p>
            )}
          </div>
          <div className="as-carta__azioni">
            <Bottone onClick={ricarica}>{t("action.reload")}</Bottone>
          </div>
        </div>
        {salute.data && (
          <div className="as-carta__corpo">
            <ul className="as-elenco">
              <li className="as-riga">{t("health.version", { v: salute.data.api_version })}</li>
              <li className="as-riga">
                {t("health.tables", { n: numero(salute.data.schema_tables) })}
              </li>
              <li className="as-riga">
                {t("health.catalogEntries", { n: numero(salute.data.catalog_entries) })}
              </li>
            </ul>
          </div>
        )}
        {salute.error && (
          <div className="as-carta__corpo">
            <Avviso esito="allarme">{salute.error.message}</Avviso>
          </div>
        )}
      </section>
    </main>
  )
}
