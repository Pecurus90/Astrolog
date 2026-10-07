import { useQuery } from "@tanstack/react-query"
import { useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Campo } from "./Campo"
import { api } from "./api/client"
import { motivo } from "./api/motivo"
import type { components } from "./api/schema"
import { type Chiave, numero, t } from "./i18n"
import { CAMPO_E_BOTTONE } from "./inLinea"

type Probe = components["schemas"]["ProbeOut"]

const RIFIUTI_SPOSTA: Record<string, Chiave> = {
  not_the_same_folder: "folders.move.notSame",
  folder_exists: "folders.move.exists",
  root_unreachable: "folders.move.unreachable",
}

/** La cartella registrata `id` ora sta in `percorso`. Torna il perche' del rifiuto, o niente. */
export async function sposta(id: number, percorso: string): Promise<Chiave | undefined> {
  const { error } = await api.POST("/api/v1/folders/{folder_id}/move", {
    params: { path: { folder_id: id } },
    body: { root_path: percorso },
  })
  return error ? motivo(error, RIFIUTI_SPOSTA, "folders.move.failed") : undefined
}

/**
 * Le cartelle che l'app legge: chiederle, guardarci dentro, registrarle.
 *
 * Sta in un modulo suo perche' lo fanno in due -- il primo avvio e la sezione Cartelle delle
 * Impostazioni -- e la sostanza e' la stessa. Scritta due volte, i **perche'** qui sotto
 * sarebbero rimasti in una casa sola, e chi tocca l'altra non li vedrebbe.
 *
 * - **Si guarda prima di registrare.** La sonda dice quanti FITS ci sono senza scrivere niente:
 *   e' cosi' che si capisce di aver puntato la cartella giusta, invece di scoprirlo a scansione
 *   finita. E una cartella che non si raggiunge **non si puo' nemmeno aggiungere**: offrire il
 *   tasto sarebbe un invito a sbagliare.
 * - **Si registra il percorso su cui si e' guardato**, non quello che torna dalla sonda: in DB
 *   finirebbe la stessa stringa -- `POST /folders` canonicalizza da se' -- ma cosi' la scrittura
 *   non dipende da un campo della risposta, che domani potrebbe sparire in silenzio.
 * - **Durante la registrazione il tasto e' bloccato**: un doppio clic manderebbe due richieste, e
 *   la seconda tornerebbe 409 -- cioe' un avviso di fallimento su una scrittura riuscita.
 * - **L'elenco arriva dall'API**, non da una lista tenuta qui: due verita' sulle stesse cartelle
 *   divergerebbero al primo errore di rete.
 * - **Una cartella spostata non si registra di nuovo**: se la sonda la riconosce, il tasto la
 *   sposta, e le risposte date sulle sue cartelle la seguono. Registrata di nuovo, ogni frame
 *   avrebbe due posti e le risposte resterebbero sul percorso vecchio.
 */
export function useCartelle(chiaveErrore: "wizard.folders.failed" | "settings.folders.failed") {
  const [vista, setVista] = useState<Probe>()
  const [scelto, setScelto] = useState("")
  const [rotto, setRotto] = useState<"guarda" | "aggiungi">()
  const [inCorso, setInCorso] = useState(false)
  const [nonSpostata, setNonSpostata] = useState<Chiave>()

  const elenco = useQuery({
    queryKey: ["folders"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/folders")
      if (error) throw new Error(t(chiaveErrore))
      return data
    },
  })

  return {
    elenco,
    vista,
    rotto,
    inCorso,
    nonSpostata,
    guarda: async (quale: string) => {
      const { data, error } = await api.POST("/api/v1/folders/probe", {
        body: { root_path: quale },
      })
      setRotto(error ? "guarda" : undefined)
      setNonSpostata(undefined)
      setScelto(quale)
      setVista(data)
    },
    aggiungi: async () => {
      setInCorso(true)
      const { error } = await api.POST("/api/v1/folders", { body: { root_path: scelto } })
      setInCorso(false)
      setRotto(error ? "aggiungi" : undefined)
      if (error) return
      setVista(undefined)
      void elenco.refetch()
    },
    spostaQui: async (id: number) => {
      setInCorso(true)
      const perche = await sposta(id, scelto)
      setInCorso(false)
      setNonSpostata(perche)
      if (perche) return
      setVista(undefined)
      void elenco.refetch()
    },
  }
}

/** Il campo dove si scrive un percorso, col tasto che ci guarda dentro.
 *
 * E' la via del desktop, e il ripiego del NAS quando l'elenco non si legge. */
export function ScriviPercorso({
  id,
  prefisso,
  valore,
  onScrivi,
  onGuarda,
}: {
  id: string
  prefisso: "wizard.folders" | "settings.folders" | "settings.folders.move"
  valore: string
  onScrivi: (v: string) => void
  onGuarda: () => void
}) {
  // A form so that Enter in the field does what the button does; the button stays `type=button`,
  // a single field submits on its own.
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onGuarda()
      }}
      style={CAMPO_E_BOTTONE}
    >
      <Campo cresce="var(--misura-cerca)" etichetta={t(`${prefisso}.label`)} id={id}>
        <input
          className="as-campo__input as-cifre"
          id={id}
          onChange={(e) => onScrivi(e.target.value)}
          spellCheck={false}
          value={valore}
        />
      </Campo>
      <Bottone onClick={onGuarda}>{t(`${prefisso}.look`)}</Bottone>
    </form>
  )
}

/** Cosa la sonda ha visto, e il tasto che registra.
 *
 * L'esito e' un avviso che **aspetta** (`status`): nessuno lo sta ancora leggendo, e interrompere
 * chi scrive un percorso per dirgli quanti file ha trovato e' rumore. Un conteggio fermato al suo
 * tetto di tempo e' un **pavimento**, e lo dice col tono d'attesa: mostrarlo come totale su un
 * archivio lento e' una bugia tranquillizzante. */
export function VistaDellaSonda({
  vista,
  inCorso,
  onAggiungi,
  onSposta,
  nonSpostata,
  prefisso,
}: {
  vista: Probe
  inCorso: boolean
  onAggiungi: () => void
  /** Al posto di Aggiungi, quando la sonda dice da quale cartella registrata vengono questi file. */
  onSposta: (id: number) => void
  nonSpostata: Chiave | undefined
  /** Le due superfici hanno le stesse chiavi con due radici diverse. Passando la radice, il tipo
   *  di `t()` restringe da se': una chiave che una delle due non ha non compila. */
  prefisso: "wizard.folders" | "settings.folders"
}) {
  if (!vista.reachable) {
    return (
      <Avviso esito="allarme" ruolo="status" titolo={t(`${prefisso}.unreachableTitle`)}>
        {t(`${prefisso}.unreachableHelp`)}
      </Avviso>
    )
  }
  const alTetto = vista.complete === false
  return (
    <>
      {vista.fits_count !== null && (
        <Avviso
          esito={alTetto ? "attesa" : "buono"}
          ruolo="status"
          titolo={t(alTetto ? `${prefisso}.atLeastTitle` : `${prefisso}.foundTitle`)}
        >
          {t(alTetto ? `${prefisso}.atLeast` : `${prefisso}.found`, {
            n: numero(vista.fits_count),
          })}
        </Avviso>
      )}
      {vista.moved_from ? (
        <Spostata
          da={vista.moved_from}
          inCorso={inCorso}
          nonSpostata={nonSpostata}
          onSposta={onSposta}
        />
      ) : (
        <div className="as-pagina__azioni">
          <Bottone disabled={inCorso} verso="primario" onClick={onAggiungi}>
            {t(`${prefisso}.add`)}
          </Bottone>
        </div>
      )}
    </>
  )
}

function Spostata({
  da,
  inCorso,
  nonSpostata,
  onSposta,
}: {
  da: components["schemas"]["MovedFrom"]
  inCorso: boolean
  nonSpostata: Chiave | undefined
  onSposta: (id: number) => void
}) {
  return (
    <>
      <Avviso esito="buono" ruolo="status" titolo={t("folders.move.foundTitle")}>
        {t("folders.move.found", { percorso: da.root_path })}
      </Avviso>
      <div className="as-pagina__azioni">
        <Bottone disabled={inCorso} verso="primario" onClick={() => onSposta(da.id)}>
          {t("folders.move.here")}
        </Bottone>
      </div>
      {nonSpostata && <Avviso esito="allarme">{t(nonSpostata)}</Avviso>}
    </>
  )
}
