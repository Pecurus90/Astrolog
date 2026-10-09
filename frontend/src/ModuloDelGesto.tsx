import { useMutation, useQueryClient } from "@tanstack/react-query"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Campo } from "./Campo"
import { motivo } from "./api/motivo"
import { type Chiave, t } from "./i18n"
import { testo } from "./scritto"

/**
 * I mattoni dei moduli dell'Attrezzatura: la scrittura, il modulo, il nome e il perche' di un
 * rifiuto. Li usano i gesti che fanno nascere qualcosa e quelli che correggono una riga.
 *
 * **Un rifiuto si legge**: il backend manda un codice, qui diventa una frase -- un nome che possiedi
 * gia' non e' un errore dell'app, e' una cosa che devi sapere.
 */

const RIFIUTI: Record<string, Chiave> = {
  name_taken: "gear.write.nameTaken",
  worker_busy: "gear.write.busy",
  merge_refused: "gear.write.mergeRefused",
  not_found: "gear.write.notFound",
  rig_exists: "gear.write.rigExists",
  wrong_kind: "gear.write.wrongKind",
  spelling_taken: "gear.write.spellingTaken",
}

/** Manda la scrittura, rilegge la pagina e chiude. La pagina si rilegge **dall'API**: cio' che si
 *  vede dopo e' cio' che il backend ha scritto davvero, non cio' che abbiamo mandato. */
export function useScrittura(manda: () => Promise<void>, onFatto: () => void) {
  const coda = useQueryClient()
  return useMutation({
    mutationFn: manda,
    onSuccess: async () => {
      // Anche `review`: una camera scritta senza pixel **alza** il conto delle domande aperte, e
      // quel numero sta nella barra di sinistra. Senza questa riga resterebbe fermo finche' non
      // si cambia pagina.
      await Promise.all([
        coda.invalidateQueries({ queryKey: ["gear"] }),
        coda.invalidateQueries({ queryKey: ["review"] }),
      ])
      onFatto()
    },
  })
}

/** Un campo scritto entra nella scritta, uno che non dice niente ne' **esce**: mandare un
 *  campo vuoto vorrebbe dire "cancellalo", e non toccarlo vuol dire lasciarlo com'e'. */
export function con<S extends object>(scritta: S, campo: string, valore: unknown): S {
  const dopo: Record<string, unknown> = { ...(scritta as Record<string, unknown>) }
  if (valore === undefined) delete dopo[campo]
  else dopo[campo] = valore
  return dopo as S
}

function Rifiuto({ errore }: { errore: unknown }) {
  if (!errore) return null
  return <Avviso esito="allarme">{t(motivo(errore, RIFIUTI, "gear.write.failed"))}</Avviso>
}

/** **Senza nome non si salva.** Un nome vuoto l'API lo rifiuta, e mandarlo vorrebbe dire far
 *  scrivere all'utente un errore generico per una cosa che si vede prima di premere -- la stessa
 *  scelta della scheda di un sito. */
function Azioni({
  onManda,
  onAnnulla,
  salvando,
  valido,
}: {
  onManda: () => void
  onAnnulla: () => void
  salvando: boolean
  valido: boolean
}) {
  return (
    // `as-comparsa__azioni` e non `as-carta__azioni`: la seconda nel foglio esiste solo come
    // figlia dell'intestazione di una carta, e qui dentro non prenderebbe ne' la disposizione
    // ne' lo spazio fra i bottoni. La guardia sulle classi inventate non lo vede, perche' quel
    // nome nel foglio c'e' -- dentro un selettore composto.
    <div className="as-comparsa__azioni">
      <Bottone verso="primario" disabled={salvando || !valido} onClick={onManda}>
        {t("gear.write.save")}
      </Bottone>{" "}
      <Bottone onClick={onAnnulla}>{t("gear.write.cancel")}</Bottone>
    </div>
  )
}

export function NomeDelPezzo({
  id,
  cheCera,
  onNome,
}: {
  id: string
  cheCera?: string
  onNome: (n: string | undefined) => void
}) {
  return (
    <Campo id={id} etichetta={t("gear.write.name")}>
      <input
        className="as-campo-modulo__input"
        id={id}
        defaultValue={cheCera ?? ""}
        onChange={(e) => onNome(testo(e.target.value, cheCera))}
      />
    </Campo>
  )
}

/** Un modulo di scrittura: la scheda dentro la sua comparsa, il perche' di un rifiuto, e i due
 *  bottoni.
 *
 *  La comparsa e' una **regione col suo nome**, cosi' chi ascolta la raggiunge e sa di chi e':
 *  con due schede aperte ci sono due campi "Marca", e chi legge con uno schermo deve sapere in
 *  quale sta scrivendo. Il nome lo porta il `legend`, e la regione lo indica invece di ripeterlo.
 *  Non e' l'unica comparsa dell'app: quella delle letture (`LettureFuori`) non e' un modulo e non
 *  vuole ne' `fieldset` ne' `legend`. */
export function Modulo({
  base,
  titolo,
  onManda,
  onAnnulla,
  salvando,
  valido,
  errore,
  children,
}: {
  base: string
  titolo: string
  onManda: () => void
  onAnnulla: () => void
  salvando: boolean
  /** Se si puo' mandare: un nome vuoto l'API lo rifiuta, e si vede prima di premere. */
  valido: boolean
  errore: unknown
  children: React.ReactNode
}) {
  return (
    <div className="as-comparsa as-comparsa--accanto" role="region" aria-labelledby={`${base}-nome`}>
      <fieldset>
        <legend className="as-comparsa__titolo" id={`${base}-nome`}>
          {titolo}
        </legend>
        {children}
        <Rifiuto errore={errore} />
        <Azioni onManda={onManda} onAnnulla={onAnnulla} salvando={salvando} valido={valido} />
      </fieldset>
    </div>
  )
}
