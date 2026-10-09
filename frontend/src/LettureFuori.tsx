import { useQuery } from "@tanstack/react-query"
import { useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Prova } from "./Riga"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"

/**
 * Il pannello **cosa e' rimasto fuori** di una lettura: i file saltati apposta, le cartelle non
 * guardate, e i file che non si sono potuti leggere.
 *
 * - **Un motivo si scrive a parole**: i codici del backend a schermo non ci arrivano mai.
 * - **I file non letti si chiedono solo aprendo**, perche' possono essere migliaia e di venti
 *   ricevute ne interessa una.
 */
type Lettura = components["schemas"]["ScanRunOut"]

/** Quanti file non letti si chiedono per volta. Sono l'unica cosa qui dentro che puo' essere
 *  migliaia: le cartelle lasciate fuori e i motivi dei saltati arrivano gia' con la ricevuta. */
const PER_VOLTA = 100

// Le cartelle lasciate fuori. Il nome del campo **e'** la chiave del suo testo, e a tenerlo fermo
// e' `t()`: aggiungerne uno che non ha la sua frase nel dizionario non compila.
const CARTELLE = ["unreadable_dirs", "hidden_dirs", "linked_dirs"] as const

/** Se c'e' davvero qualcosa da aprire: un pannello che si apre sul vuoto e' un tasto che promette
 *  e non mantiene. */
export function qualcosaERimastoFuori(lettura: Lettura): boolean {
  return (
    lettura.errors > 0 ||
    lettura.skipped_by_reason.length > 0 ||
    CARTELLE.some((c) => lettura[c].length > 0)
  )
}

/** Il pannello, con dentro tutto cio' che questa lettura non ha preso. */
export function Fuori({ lettura, id }: { lettura: Lettura; id: string }) {
  return (
    <div
      aria-labelledby={`${id}-name`}
      className="as-apertura as-apertura--accanto"
      id={id}
      role="region"
    >
      {/* `h3`, non `h4`: il titolo della carta e' un `h2`, e un livello saltato e' un capitolo
          che manca per chi si muove fra le intestazioni. */}
      <h3 className="as-apertura__titolo" id={`${id}-name`}>
        {t("settings.readings.leftOut")}
      </h3>
      <ul className="as-apertura__righe">
        {lettura.skipped_by_reason.map((s) => (
          <li className="as-apertura__voce" key={s.reason}>
            {t(`settings.readings.skip.${s.reason}`, { n: numero(s.count) })}
          </li>
        ))}
        {CARTELLE.map((campo) =>
          lettura[campo].map((cartella) => (
            <li className="as-apertura__voce" key={`${campo}-${cartella}`}>
              <Prova>{cartella}</Prova> {t(`settings.readings.${campo}`)}
            </li>
          )),
        )}
      </ul>
      {lettura.errors > 0 && <NonLetti lettura={lettura.id} />}
    </div>
  )
}

/** I file che la lettura non ha letto, ognuno col suo motivo.
 *
 * Quali letture lo tengono lo decide il backend (`api/scan.scan_run_errors`): sulle altre la rotta
 * lo dice col suo codice, e qui si scrive che **non c'e' piu'** invece di un elenco vuoto -- che
 * sarebbe una bugia, visto che la riga sopra i file non letti li ha contati. */
function NonLetti({ lettura }: { lettura: number }) {
  const [quanti, setQuanti] = useState(PER_VOLTA)
  const file = useQuery({
    queryKey: ["scan-run-errors", lettura, quanti],
    queryFn: async () => {
      const { data, error, response } = await api.GET("/api/v1/scan-runs/{run_id}/errors", {
        params: { path: { run_id: lettura }, query: { limit: quanti } },
      })
      if (response.status === 410) return null
      if (error) throw new Error(t("settings.readings.filesFailed"))
      return data
    },
  })
  const presi = file.data?.items.length ?? 0

  return (
    <>
      <h4 className="as-apertura__titolo">{t("settings.readings.files")}</h4>
      {file.isError && <Avviso esito="allarme">{t("settings.readings.filesFailed")}</Avviso>}
      {file.data === null && (
        <p className="as-apertura__testo">{t("settings.readings.filesGone")}</p>
      )}
      {presi > 0 && (
        <ul className="as-apertura__righe">
          {file.data?.items.map((f) => (
            <li className="as-apertura__voce" key={f.file}>
              <Prova>{f.file}</Prova> {t(`settings.readings.error.${f.reason}`)}
            </li>
          ))}
        </ul>
      )}
      {(file.data?.total ?? 0) > presi && (
        <div className="as-apertura__azioni">
          <Bottone piccolo onClick={() => setQuanti((n) => n + PER_VOLTA)}>
            {t("settings.readings.filesMore")}
          </Bottone>
        </div>
      )}
    </>
  )
}
