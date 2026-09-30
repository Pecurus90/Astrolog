import { useQuery } from "@tanstack/react-query"
import type { ReactNode } from "react"
import { Link, useLocation } from "react-router"

import { Scansiona } from "./Scansiona"
import { Stanotte } from "./Stanotte"
import { api } from "./api/client"
import { numero, t } from "./i18n"
import { APERTE, GRUPPI, TITOLI, paginaDi } from "./pagine"

/**
 * Lo scheletro: la barra con le pagine, la barra in alto, e dentro la pagina che stai guardando.
 * Il contratto sta in `docs/domini/navigazione.md`.
 *
 * - **Qui non si calcola niente**: il conto delle cose da confermare arriva fatto da
 *   `GET /review`, ed e' la stessa query della Casa -- una chiave sola, quindi una chiamata
 *   sola anche quando tutte e due sono a schermo.
 * - **Il nome della pagina in alto** serve al telefono, dove la barra sara' chiusa; sul desktop
 *   ripete la voce accesa, e va bene: e' l'unico posto che lo dira' sempre.
 * - **Il pannello a scomparsa non e' qui**: nasce col mobile, quando si puo' aprire e
 *   collaudare (`navigazione.md`).
 * - **Le voci sono link dentro il loro gruppo, non un elenco**: e' la forma su cui il design
 *   system ha messo i suoi mattoni -- `.as-gruppo` e' il contenitore **diretto** delle voci, e in
 *   colonna stretta e' lui a diventare una fila. Il legame fra il nome del gruppo e le sue voci
 *   resta, detto con `role="group"`; cio' che si perde e' l'annuncio "elenco di N voci", e non e'
 *   un pareggio: si guadagna una barra che si comporta come il design l'ha disegnata e si perde
 *   una comodita' per chi ascolta. Se un giorno pesa piu' quella, la si chiede alla fonte -- una
 *   classe che tolga i pallini senza separare -- invece di rimetterla qui.
 */
export function Layout({ children }: { children: ReactNode }) {
  const dove = useLocation()
  const pagina = useQuery({
    queryKey: ["review"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/review")
      if (error) throw new Error(t("review.failed"))
      return data
    },
  })
  const qui = paginaDi(dove.pathname)

  return (
    // Due contenitori, e l'ordine conta: la misura sta **sopra** la griglia, perche' un elemento
    // non si stila dalla propria container query -- il guscio che si misurasse da se' non
    // vedrebbe mai la colonna stretta.
    <div className="as-guscio-misura">
      <div className="as-guscio">
        <nav className="as-lato" aria-label={t("nav.label")}>
          <p className="as-lato__marchio">{t("app.title")}</p>
          {GRUPPI.map((gruppo) => {
            const voci = APERTE.filter((p) => p.gruppo === gruppo)
            if (voci.length === 0) return null
            const titolo = TITOLI[gruppo]
            return (
              <div
                className="as-gruppo"
                key={gruppo}
                // `group` **solo** dove c'e' un nome da dargli: un gruppo senza nome non raccoglie
                // niente per chi ascolta, aggiunge solo un livello da attraversare. `cima` e
                // `fondo` sono contenitori di posizione, e restano dei semplici contenitori.
                role={titolo ? "group" : undefined}
                aria-labelledby={titolo ? `gruppo-${gruppo}` : undefined}
              >
                {titolo && (
                  <p className="as-gruppo__nome" id={`gruppo-${gruppo}`}>
                    {t(titolo)}
                  </p>
                )}
                {voci.map((p) => (
                  <Link
                    className="as-voce"
                    key={p.a}
                    to={p.a}
                    aria-current={p.a === qui?.a ? "page" : undefined}
                  >
                    {t(p.chiave)}
                    {p.a === "/da-confermare" && pagina.data && pagina.data.to_confirm > 0 && (
                      // lo spazio e' per chi ascolta: senza, il nome del link e' "Da confermare12".
                      // A vedersi non cambia niente, il conteggio si allinea comunque a destra.
                      <>
                        {" "}
                        <span className="as-voce__conteggio">{numero(pagina.data.to_confirm)}</span>
                      </>
                    )}
                  </Link>
                ))}
              </div>
            )
          })}
          <Stanotte />
        </nav>
        <header className="as-alto">
          <p className="as-alto__titolo">{qui ? t(qui.chiave) : t("nav.unknown")}</p>
          <div className="as-alto__strumenti">
            <Scansiona />
          </div>
        </header>
        <div className="as-principale">{children}</div>
      </div>
    </div>
  )
}
