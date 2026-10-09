import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useRef, useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Campo } from "./Campo"
import { usePienoDelPasso } from "./pienoDelPasso"
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
const DOVE_SI_SCARICA = "https://www.hnsky.org/astap.htm"

// E dove si prende il **catalogo stellare**, che e' un download a parte e senza il quale ASTAP
// parte e non riconosce niente. E' la cartella dei cataloghi dell'autore, non un file: quale
// scaricare dipende dal sistema, e mandarlo su un file solo darebbe il pacchetto sbagliato ai
// due bersagli su tre che non sono Windows.
const DOVE_SI_SCARICA_IL_CATALOGO =
  "https://sourceforge.net/projects/astap-program/files/star_databases/"

export type DoveStaASTAP = ReturnType<typeof useDoveStaASTAP>

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

/** Il campo del percorso e il suo bottone: un gesto solo, quindi sulla stessa riga. */
export function CampoDelPercorso({
  id,
  dove,
  onOffre,
}: {
  id: string
  dove: DoveStaASTAP
  /** Il primo avvio ascolta: scritto un percorso, il comando pieno e' quello che lo verifica. */
  onOffre?: (offre: boolean) => void
}) {
  const scritto = Boolean(dove.path)
  // Pieno finche' c'e' qualcosa da verificare: a percorso trovato il gesto che resta e' chiudere.
  const daVerificare = scritto && (dove.esito === undefined || dove.esito === "notThere")
  usePienoDelPasso(onOffre, daVerificare)
  return (
    <>
      <div className="as-campo-riga">
        <Campo
          id={id}
          etichetta={t("solver.label")}
          errore={dove.esito === "notThere" ? t("solver.notThere") : undefined}
        >
          <input
            className="as-campo-modulo__input as-campo-modulo__input--cifre"
            id={id}
            placeholder={t("solver.placeholder")}
            value={dove.path}
            onChange={(e) => {
              dove.setPath(e.target.value)
              // L'esito e' di cio' che si e' scritto PRIMA: lasciarlo sopra un campo che ora dice
              // un'altra cosa sarebbe un "Trovato" attaccato a un percorso mai provato. E si
              // dimentica anche cosa si era mandato, o chi cancella e riscrive lo stesso percorso
              // resterebbe senza risposta.
              dove.dimentica()
            }}
            onBlur={dove.manda}
          />
        </Campo>
        <Bottone
          verso={daVerificare ? "primario" : "tenue"}
          onClick={dove.manda}
          disabled={dove.salva.isPending || !scritto}
        >
          {t("solver.use")}
        </Bottone>
      </div>
      <p className="as-campo-modulo__aiuto">{t("solver.pathHelp")}</p>
      <p className="as-campo-modulo__aiuto">{t("solver.checkNow")}</p>

      {/* **Il percorso sbagliato lo dice il campo**, non un avviso staccato: chi sta correggendo
          quello che ha scritto guarda li'. Qui resta solo la conferma di quando va bene --
          `status`, perche' chi sta ancora battendo il percorso non va interrotto. */}
      {dove.esito !== undefined && dove.esito !== "notThere" && (
        <Avviso esito="buono" ruolo="status" titolo={t("solver.foundTitle")}>
          {t(dove.esito === "found" ? "solver.found" : "solver.foundNoDatabase")}
        </Avviso>
      )}
      {dove.salva.error && (
        <Avviso esito="allarme" titolo={t("wizard.savedFailedTitle")}>
          {dove.salva.error.message}
        </Avviso>
      )}
    </>
  )
}

/** Il catalogo stellare: quali ci sono, o che manca e dove si prende.
 *
 * **Vuoto qui vuol dire "manca"**, non "non lo so": chi non ha ASTAP non vede questo pezzo
 * affatto, perche' e' il catalogo di un programma che non ha -- e due allarmi per un problema
 * solo mandano a cercare due cose. Chi decide se mostrarlo e' chi sa se il programma c'e'.
 *
 * Non e' un allarme: manca un download, non si e' rotto niente. */
export function IlCatalogo({ quali }: { quali: readonly string[] }) {
  if (quali.length > 0) {
    return (
      <p className="as-carta__domanda">
        <span className="as-stato as-stato--buono">
          {t("solver.databaseHere", { quali: quali.join(", ") })}
        </span>
      </p>
    )
  }
  return (
    <Avviso esito="attesa" titolo={t("solver.databaseTitle")}>
      {t("solver.databaseWhy")}
      <p className="as-campo-modulo__aiuto">
        <a href={DOVE_SI_SCARICA_IL_CATALOGO} rel="noopener noreferrer" target="_blank">
          {t("solver.databaseGet")}
        </a>
      </p>
      <p className="as-campo-modulo__aiuto">{t("solver.databaseWhich")}</p>
    </Avviso>
  )
}

/** Dove si prende, e la riga che dice che l'app non lo scarica.
 *
 * L'app **non scarica ne' esegue niente da sola**: da' l'indirizzo, e decide l'utente. E' l'unica
 * riga di questa schermata che non si negozia. Il collegamento resta un collegamento e non prende
 * la veste di un bottone: porta via, non fa qualcosa qui. */
export function DoveSiPrende() {
  return (
    <>
      <p className="as-soprattitolo as-soprattitolo--nudo">{t("solver.whereGroup")}</p>
      <a href={DOVE_SI_SCARICA} target="_blank" rel="noopener noreferrer">
        {t("solver.download")}
      </a>
      <p className="as-campo-modulo__aiuto">{t("solver.noDownload")}</p>
    </>
  )
}
