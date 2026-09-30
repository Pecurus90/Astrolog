import { useQuery } from "@tanstack/react-query"
import { useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Fuori, qualcosaERimastoFuori } from "./LettureFuori"
import { Prova, Riga } from "./Riga"
import { Vuoto } from "./Vuoto"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { durata, giorno, numero, orario, t } from "./i18n"

/**
 * La sezione **Le letture**: le ricevute delle scansioni passate.
 *
 * - **Risponde alla domanda che viene dopo una scansione**: ha funzionato? Finora quei numeri si
 *   vedevano mentre l'app lavorava e poi sparivano, e "l'archivio non ha quello che mi aspettavo"
 *   non aveva nessun posto dove andare a guardare.
 * - **Uno zero non e' una riga**: si scrive solo cio' che e' successo, tranne i **nuovi**, che
 *   sono la domanda -- "0 nuovi" e' una risposta, "0 doppioni" e' rumore.
 * - **Cosa e' rimasto fuori** ha il suo pannello, in `LettureFuori.tsx`.
 */
type Lettura = components["schemas"]["ScanRunOut"]

/** Quante ricevute si chiedono per volta. Venti coprono piu' di un mese di scansioni quotidiane,
 *  e chi vuole indietro preme una volta. */
const A_PAGINA = 20

/** L'elenco delle ricevute, dalla piu' recente. */
export function Letture() {
  const [quante, setQuante] = useState(A_PAGINA)
  const letture = useQuery({
    queryKey: ["scan-runs", quante],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/scan-runs", {
        params: { query: { limit: quante } },
      })
      if (error) throw new Error(t("settings.readings.failed"))
      return data
    },
  })
  const quanteCe = letture.data?.items.length ?? 0

  return (
    <section className="as-carta">
      <div className="as-carta__intestazione">
        <div>
          <h2 className="as-carta__titolo">{t("settings.readings.title")}</h2>
          <p className="as-carta__domanda">{t("settings.readings.what")}</p>
        </div>
      </div>
      <div className="as-carta__corpo as-carta__corpo--stretto">
        {letture.isError && <Avviso esito="allarme">{t("settings.readings.failed")}</Avviso>}
        {quanteCe === 0 && !letture.isPending && !letture.isError && <Nessuna />}
        {quanteCe > 0 && (
          <ul className="as-elenco">
            {letture.data?.items.map((l) => (
              <li key={l.id}>
                <Voce lettura={l} />
              </li>
            ))}
          </ul>
        )}
      </div>
      {/* Si chiede di piu' solo se ce n'e' di piu': un tasto che non porta niente e' una promessa
          che l'app non mantiene. */}
      {(letture.data?.total ?? 0) > quanteCe && (
        <div className="as-carta__piede">
          <Bottone piccolo onClick={() => setQuante((n) => n + A_PAGINA)}>
            {t("settings.readings.more")}
          </Bottone>
        </div>
      )}
    </section>
  )
}

/** Una lettura: quando, quanto, di quale cartella, com'e' andata, e cosa ha lasciato fuori. */
function Voce({ lettura }: { lettura: Lettura }) {
  const quanto = durata(lettura.duration_s)
  const [aperto, setAperto] = useState(false)
  const fuori = qualcosaERimastoFuori(lettura)
  const id = `lettura-${lettura.id}-fuori`
  return (
    <Riga
      comparsa={aperto && <Fuori id={id} lettura={lettura} />}
      dettagli={<Esito lettura={lettura} />}
      nome={lettura.folder_path}
      perche={
        <>
          <Prova>
            {giorno(lettura.started_at)} {orario(lettura.started_at)}
          </Prova>{" "}
          {/* Una corsa aperta **non dura zero**: sta ancora leggendo, e uno zero direbbe che e'
              finita in un istante. */}
          {quanto === undefined ? t("settings.readings.running") : quanto}
          <Conti lettura={lettura} />
        </>
      }
    >
      {fuori && (
        <Bottone aperto={aperto} governa={id} piccolo onClick={() => setAperto((c) => !c)}>
          {t("settings.readings.leftOut")}
        </Bottone>
      )}
    </Riga>
  )
}

/** Com'e' andata, e -- se si e' fermata -- perche'.
 *
 * **Il motivo di una fermata chiesta dall'utente non si scrive**: lo dice gia' l'esito, e
 * "fermata da te perche' l'hai fermata tu" non porta niente. A tenerlo fermo e' il **tipo**:
 * `stop_requested` non ha una sua frase nel dizionario, quindi togliere questa esclusione non
 * compila -- e' un rosso di `tsc`, non un test. */
function Esito({ lettura }: { lettura: Lettura }) {
  if (lettura.status === null) return null
  const male = lettura.status === "aborted" || lettura.status === "error"
  const perche =
    lettura.reason !== null && lettura.reason !== "stop_requested"
      ? t(`settings.readings.why.${lettura.reason}`)
      : undefined
  return (
    <>
      <span className={`as-stato ${male ? "as-stato--allarme" : "as-stato--buono"}`}>
        {t(`settings.readings.${lettura.status}`)}
      </span>
      {perche !== undefined && <span className="as-dato as-dato--ignoto"> {perche}</span>}
    </>
  )
}

// I conti di una lettura, nell'ordine in cui si leggono; i **nuovi** stanno a parte (la regola e'
// in testa al file).
const CONTI = [
  "found",
  "unchanged",
  "duplicates",
  "missing",
  "skipped",
  "errors",
  "online_only",
] as const

function Conti({ lettura }: { lettura: Lettura }) {
  const detti = CONTI.filter((c) => lettura[c] > 0)
  return (
    <>
      {" \u00B7 "}
      {t("settings.readings.new", { n: numero(lettura.new) })}
      {detti.map((c) => (
        <span key={c}>
          {", "}
          {t(`settings.readings.${c}`, { n: numero(lettura[c]) })}
        </span>
      ))}
    </>
  )
}

/** Chi non ha ancora letto niente: non un elenco vuoto, ma cosa fare perche' ne nasca una. */
function Nessuna() {
  return <Vuoto perche="settings.readings.none.why" titolo="settings.readings.none" />
}
