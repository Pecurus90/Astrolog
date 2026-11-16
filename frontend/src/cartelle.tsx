import { useQuery } from "@tanstack/react-query"
import { useState } from "react"

import type { SegnoAvviso } from "./componenti/Avviso"
import { api } from "./api/client"
import { motivo } from "./api/motivo"
import type { components } from "./api/schema"
import { type Chiave, t } from "./i18n"

type Probe = components["schemas"]["ProbeOut"]

export const RIFIUTI_SPOSTA: Record<string, Chiave> = {
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

/** A probe's notice, as `Avviso` takes it. */
export interface EsitoSonda {
  segno: SegnoAvviso
  titolo: string
  testo?: string
  azione?: string
  onAzione?: () => void
}

/** The probe's move notices, same on both pages: a refused move says why; a registered folder's
 *  files found here offer to move it. `fatto` hears whether it moved. */
export function esitoDelloSpostamento(
  c: ReturnType<typeof useCartelle>,
  fatto: (spostata: boolean) => void,
): EsitoSonda | null {
  if (c.nonSpostata) return { segno: "!", titolo: t(c.nonSpostata) }
  const da = c.vista?.moved_from
  if (!da) return null
  return {
    segno: "!",
    titolo: t("folders.move.foundTitle"),
    testo: t("folders.move.found", { percorso: da.root_path }),
    azione: t("folders.move.here"),
    onAzione: () => {
      if (!c.inCorso) void c.spostaQui(da.id).then(fatto)
    },
  }
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
  const [rotto, setRotto] = useState<"guarda" | "aggiungi" | "registrata">()
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
    /** True when registered. */
    aggiungi: async (): Promise<boolean> => {
      setInCorso(true)
      const { error } = await api.POST("/api/v1/folders", { body: { root_path: scelto } })
      setInCorso(false)
      // 409 folder_exists: the path is already in the list, not a failure
      const codice = (error as { detail?: { code?: string } } | undefined)?.detail?.code
      setRotto(!error ? undefined : codice === "folder_exists" ? "registrata" : "aggiungi")
      if (error) return false
      setVista(undefined)
      void elenco.refetch()
      return true
    },
    /** True when moved. */
    spostaQui: async (id: number): Promise<boolean> => {
      setInCorso(true)
      const perche = await sposta(id, scelto)
      setInCorso(false)
      setNonSpostata(perche)
      if (perche) return false
      setVista(undefined)
      void elenco.refetch()
      return true
    },
  }
}
