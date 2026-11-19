import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useRef, useState } from "react"

import { api } from "./api/client"
import { t } from "./i18n"

/**
 * Dire all'app dove sta ASTAP, e sapere subito se li' c'e'.
 *
 * Sta in un modulo suo perche' lo fanno in due -- il primo avvio, che lo chiede **solo** a chi il
 * programma non ce l'ha, e la sezione *Il riconoscitore*, dove si guarda e si corregge sempre.
 *
 * - **Un percorso sbagliato non diventa un ripiego di nascosto**: se quello che scrivi non esiste
 *   il backend continua a dire che il solver manca, e lo dice **qui**, invece di lasciarti
 *   chiedere perche' i frame restano senza cielo.
 * - **Cio' che hai scritto si salva anche lasciando il campo**: un percorso battuto a mano e perso
 *   perche' non si e' premuto il tasto giusto e' lavoro buttato.
 * - **Una scrittura sola per percorso**, da qualunque parte arrivi: premere il tasto toglie il
 *   fuoco dal campo, quindi senza memoria di cosa si e' gia' mandato il clic manderebbe la stessa
 *   preferenza due volte.
 */

// Dove si prende il solver. Sta qui e non nel dizionario: e' un indirizzo, non un testo da
// tradurre, e cambiarlo in una lingua sola vorrebbe dire mandare due utenti in due posti. Lo
// stesso indirizzo e' in `README.md`, dove dice a chi installa da sorgente cosa gli serve.
export const DOVE_SI_SCARICA = "https://www.hnsky.org/astap.htm"

export type DoveStaASTAP = ReturnType<typeof useDoveStaASTAP>

/** Dove l'app prende ASTAP e da quale canale (`GET /solver`): la sezione e il primo avvio. */
export function useSolver() {
  return useQuery({
    queryKey: ["solver"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/solver")
      if (error) throw new Error(t("settings.solver.failed"))
      return data
    },
  })
}

export function useDoveStaASTAP(iniziale = "") {
  const [path, setPath] = useState(iniziale)
  const scritto = useRef<string | undefined>(undefined)
  const cache = useQueryClient()
  const salva = useMutation({
    // Il percorso arriva **come argomento** e non dallo stato: adottando una proposta si scrive
    // nello stesso momento in cui il campo cambia, e leggendo lo stato si manderebbe quello di
    // prima -- cioe' niente, la prima volta.
    mutationFn: async (quale: string) => {
      const { data, error } = await api.PATCH("/api/v1/settings", {
        body: { values: { astap_path: quale } },
      })
      if (error) throw new Error(t("settings.failed"))
      return data
    },
    onSuccess: (data) => {
      // Le impostazioni sono **quelle** che la scrittura ha appena restituito: lasciare in cache
      // le vecchie vorrebbe dire due verita' su cosa manca, e la piu' vecchia che vince al
      // prossimo render. Dove sta il solver invece si richiede, perche' la risposta della
      // scrittura non porta il canale.
      cache.setQueryData(["settings"], data)
      void cache.invalidateQueries({ queryKey: ["solver"] })
    },
    // Se la scrittura cade, il percorso torna da mandare: senza, il tasto non riproverebbe piu'.
    onError: () => {
      scritto.current = undefined
    },
  })

  return {
    path,
    setPath,
    salva,
    /** Com'e' andata l'ultima scrittura, o niente finche' non si e' mandato nulla.
     *
     * **Tre esiti, non due**: il percorso puo' essere giusto e mancare comunque il catalogo, e
     * dire "l'app riconoscera' cosa hai ripreso" a chi non ce l'ha promette il contrario di quello
     * che succedera'. La risposta della scrittura porta gia' tutte e due le cose che mancano. */
    esito:
      salva.data &&
      (salva.data.missing.includes("no_solver")
        ? "notThere"
        : salva.data.missing.includes("no_star_database")
          ? "foundNoDatabase"
          : "found"),
    manda: () => {
      if (!path || path === scritto.current) return
      scritto.current = path
      salva.mutate(path)
    },
    /** Quando il percorso arriva da fuori (la ricerca automatica lo propone): il campo lo mostra
     *  e la scrittura parte, senza far ribattere a mano cio' che l'app ha appena trovato. */
    adotta: (proposto: string) => {
      setPath(proposto)
      scritto.current = proposto
      salva.mutate(proposto)
    },
    dimentica: () => {
      salva.reset()
      scritto.current = undefined
    },
  }
}
