import { useMutation, useQuery } from "@tanstack/react-query"
import { useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Prova } from "./Riga"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { t } from "./i18n"
import { CampoDelPercorso, DoveSiPrende, IlCatalogo, useDoveStaASTAP } from "./riconoscitore"

type Solver = components["schemas"]["SolverOut"]

/**
 * La sezione **Il riconoscitore**: se l'app trova ASTAP, dove, e da cosa l'ha dedotto.
 *
 * Il campo del percorso e il "dove si prende" stanno in `riconoscitore.tsx`, insieme al primo
 * avvio. Qui c'e' cio' che e' della sezione:
 *
 * - **"Trovato" senza "da dove" non si puo' smentire**: la ricerca automatica sbaglia proprio
 *   quando trova qualcosa -- un ASTAP vecchio rimasto nel PATH, o quello di un altro utente -- e
 *   chi guarda deve poter dire "no, non quello".
 * - **Un percorso scritto e sbagliato resta a schermo**: e' l'unica cosa che si puo' correggere.
 * - **La ricerca propone, non scrive**: adottarla e' un gesto, perche' sovrascrivere di nascosto
 *   toglierebbe l'unica via d'uscita quando la ricerca prende il programma sbagliato.
 */
export function Riconoscitore() {
  const solver = useQuery({
    queryKey: ["solver"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/solver")
      if (error) throw new Error(t("settings.solver.failed"))
      return data
    },
  })
  return (
    <section className="as-carta">
      <div className="as-carta__intestazione">
        <div>
          <h2 className="as-carta__titolo">{t("settings.solver.title")}</h2>
          <p className="as-carta__domanda">{t("settings.solver.what")}</p>
        </div>
      </div>
      <div className="as-carta__corpo as-carta__corpo--colonna">
        {solver.isError && <Avviso esito="allarme">{t("settings.solver.failed")}</Avviso>}
        {solver.data && <Stato solver={solver.data} />}
        {solver.data?.path === null && (
          <Avviso esito="neutro" titolo={t("solver.withoutTitle")}>
            {t("solver.without")}
          </Avviso>
        )}
        {/* Il catalogo **solo a chi ha il programma**: e' il suo catalogo, e a chi non ha ASTAP
            direbbe che gli manca la seconda meta' di una cosa che non ha. */}
        {solver.data?.path != null && <IlCatalogo quali={solver.data.databases} />}

        {/* **Si monta quando il percorso dichiarato e' arrivato**: il campo lo legge una volta
            sola, alla nascita, e montandolo prima resterebbe vuoto sopra un percorso scritto che
            la sezione sta mostrando due centimetri piu' su. */}
        {solver.data && <Scrivilo dichiarato={solver.data.declared} />}
      </div>
    </section>
  )
}

/** Cercarlo, o dire dove sta. */
function Scrivilo({ dichiarato }: { dichiarato: string | null }) {
  // Il campo parte da cio' che l'**utente** aveva scritto, non da cio' che l'app ha trovato: sono
  // due cose diverse, e riempirlo con un percorso che nessuno ha dichiarato lo trasformerebbe in
  // una dichiarazione al primo salvataggio.
  const dove = useDoveStaASTAP(dichiarato ?? "")
  return (
    <>
      <Cercalo onAdotta={dove.adotta} />

      <DoveSiPrende />

      <p className="as-soprattitolo">{t("solver.haveItGroup")}</p>
      <CampoDelPercorso dove={dove} id="solver-path" />
    </>
  )
}

/** Dove l'app lo sta prendendo, e da quale canale. Il canale si scrive a parole: "trovato in
 *  C:\\..." da solo non dice se qualcuno l'ha dichiarato o se l'app ha indovinato. */
function Stato({ solver }: { solver: Solver }) {
  if (solver.path === null) {
    return (
      <p className="as-carta__domanda">
        {t("settings.solver.none")}{" "}
        {solver.declared !== null && (
          <>
            {t("settings.solver.declaredNotThere")} <Prova>{solver.declared}</Prova>
          </>
        )}
      </p>
    )
  }
  return (
    <p className="as-carta__domanda">
      <span className="as-stato as-stato--buono">{t("settings.solver.here")}</span>{" "}
      <Prova>{solver.path}</Prova>
      {/* il percorso e la sua origine sono due cose: un separatore, non uno spazio */}
      {solver.source !== null && ` \u00b7 ${t(`settings.solver.from.${solver.source}`)}`}
    </p>
  )
}

/** *Cercalo tu*: l'app guarda il PATH e i posti noti, ignorando cio' che e' dichiarato, e
 *  **propone**. Adottare e' un gesto in piu' apposta. */
function Cercalo({ onAdotta }: { onAdotta: (path: string) => void }) {
  const [proposto, setProposto] = useState<Solver>()
  const cerca = useMutation({
    mutationFn: async () => {
      const { data, error } = await api.POST("/api/v1/solver/search", {})
      if (error) throw new Error(t("settings.solver.searchFailed"))
      return data
    },
    onSuccess: setProposto,
  })

  return (
    <>
      {/* Avvolto, e non figlio diretto della colonna: li' un bottone si stira per tutta la carta
          e la sua parola finisce a destra, lontana da tutto. Visto dal vivo. */}
      <div>
        <Bottone disabled={cerca.isPending} onClick={() => cerca.mutate()}>
          {t("settings.solver.search")}
        </Bottone>
      </div>
      {cerca.error && <Avviso esito="allarme">{cerca.error.message}</Avviso>}
      {proposto?.path === null && (
        <Avviso esito="neutro" ruolo="status">
          {t("settings.solver.searchedNothing")}
        </Avviso>
      )}
      {proposto?.path != null && (
        <Avviso
          azioni={
            <Bottone
              piccolo
              onClick={() => {
                onAdotta(proposto.path as string)
                // La proposta se ne va: adottata, non e' piu' una proposta -- e lasciarla
                // lascerebbe due volte a schermo lo stesso percorso, una come domanda.
                setProposto(undefined)
              }}
            >
              {t("settings.solver.adopt")}
            </Bottone>
          }
          esito="neutro"
          ruolo="status"
          titolo={t("settings.solver.searchedFound")}
        >
          <Prova>{proposto.path}</Prova>
        </Avviso>
      )}
    </>
  )
}
