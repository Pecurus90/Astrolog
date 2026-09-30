import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { api } from "./api/client"
import { motivo } from "./api/motivo"
import { type Chiave, numero, t } from "./i18n"

/**
 * Il pulsante che fa leggere le cartelle, e cosa sta facendo l'app mentre lo fa.
 *
 * - **Il verbo non lo decide questa pagina**: `action` arriva dal backend (`start` / `stop` /
 *   `resume`), che e' l'unico a sapere se un lavoro gira o se ne resta uno a meta'. Deciderlo
 *   qui sarebbe lo stesso fatto in due case, e il vecchio ci era cascato.
 * - **Sta in barra e non dentro una pagina** perche' il lavoro **sopravvive alla pagina**:
 *   cambiando schermata deve restare fermabile, o diventa un lavoro che nessuno puo' fermare.
 * - **Il ritmo lo dichiara il contratto della spina**: ogni 1,5 s mentre gira, ogni 60 s da
 *   fermo, e **niente a scheda nascosta** -- un portatile chiuso in borsa non deve interrogare
 *   il NAS ogni secondo.
 * - **Le cartelle che non si sono potute leggere si dicono**: il backend le manda in `skipped`
 *   col loro perche', e tacerle farebbe sembrare completa una scansione che non lo e' -- con un
 *   NAS spento fra tre cartelle, l'utente crederebbe di aver letto tutto.
 * - **Quando il lavoro finisce, cio' che l'app mostra e' vecchio**: la scansione ha appena
 *   aggiunto dei frame, e il conto delle cose da confermare e' di prima. Trovato dal vivo:
 *   18 frame entrati e la Casa che diceva ancora "0 da confermare" finche' non si ricaricava.
 * - Qui non si calcola niente: fase, numeri e verbo arrivano fatti.
 */

const MENTRE_GIRA_MS = 1500
const DA_FERMO_MS = 60000

/** Il verbo del backend e la parola che l'utente legge. Il backend ne manda tre e basta: se
 *  ne comparisse un quarto, qui non compilerebbe invece di finire a schermo come chiave nuda. */
const VERBI: Record<"start" | "stop" | "resume", Chiave> = {
  start: "scan.start",
  stop: "scan.stop",
  resume: "scan.resume",
}

/** Perche' una cartella e' stata saltata, nelle parole di chi legge. Chiusa come i verbi: un
 *  motivo nuovo del backend (`folder_retired`, domani) qui non compilerebbe, invece di uscire a
 *  schermo come "non si riesce a leggerla" -- che non e' una parola mancante, e' una **ragione
 *  sbagliata**, e manderebbe a controllare un cavo che sta benissimo. */
const SALTI: Record<"root_unreachable" | "scan_running", Chiave> = {
  root_unreachable: "scan.skipped.unreachable",
  scan_running: "scan.skipped.running",
}

/** I rifiuti che il backend puo' mandare a questo gesto, con la loro frase. */
const RIFIUTI: Record<string, Chiave> = {
  no_folders: "scan.error.no_folders",
  no_readable_folders: "scan.error.no_readable_folders",
  worker_busy: "scan.error.worker_busy",
}

/** Le cinque fasi della catena, nelle parole di chi guarda. Qui la mappa resta aperta: una fase
 *  che non conosciamo si scrive com'e' (`measure`, il giorno che si accodera'), che e' un degrado
 *  onesto -- una parola inglese a schermo, non una riga che sparisce. */
const FASI: Record<string, Chiave> = {
  scan: "scan.stage.scan",
  normalize: "scan.stage.normalize",
  solve: "scan.stage.solve",
  identify: "scan.stage.identify",
  group: "scan.stage.group",
}

export function Scansiona() {
  const cache = useQueryClient()
  const stato = useQuery({
    queryKey: ["pipeline"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/pipeline/status")
      if (error) throw new Error(t("scan.failed"))
      return data
    },
    refetchInterval: (q) =>
      q.state.data?.worker.state === "running" ? MENTRE_GIRA_MS : DA_FERMO_MS,
    refetchIntervalInBackground: false,
  })

  const gesto = useMutation({
    mutationFn: async (azione: "start" | "stop" | "resume") => {
      const { data, error } =
        azione === "stop"
          ? await api.POST("/api/v1/pipeline/stop")
          : azione === "resume"
            ? await api.POST("/api/v1/pipeline/run")
            : await api.POST("/api/v1/scan")
      if (error) throw new Error(t(motivo(error, RIFIUTI, "scan.failed")))
      return data
    },
    // Il primo giro subito dopo il gesto: aspettare il prossimo battito farebbe sembrare che
    // il pulsante non abbia fatto niente.
    onSettled: () => void cache.invalidateQueries({ queryKey: ["pipeline"] }),
  })

  // Le cartelle che l'ultimo gesto non ha potuto leggere: restano a schermo finche' non se ne
  // chiede un altro. Ognuna porta gia' il suo percorso, quindi qui non si ricuce niente.
  const risposta = gesto.data
  const saltate = risposta && "skipped" in risposta ? risposta.skipped : []

  // Il timbro di fine corsa: cambia una volta per corsa, quindi quando cambia il lavoro e'
  // finito davvero -- e cio' che le pagine mostrano va riletto. Non e' uno stato derivato: e'
  // un valore dell'API che fa da innesco, e la copia non esiste.
  const finita = stato.data?.worker.ended_at ?? null
  useEffect(() => {
    if (finita === null) return
    void cache.invalidateQueries({ queryKey: ["review"] })
    // E le ricevute: *Le letture* e' la pagina che risponde a "ha funzionato?", e la ricevuta
    // della corsa appena finita e' l'unica che si sta aspettando.
    void cache.invalidateQueries({ queryKey: ["scan-runs"] })
  }, [finita, cache])

  const azione = stato.data?.action ?? "start"
  const fase = stato.data?.worker.stage
  const corrente = fase ? stato.data?.worker.stages.find((s) => s.name === fase) : undefined
  const nomeFase = corrente ? (FASI[corrente.name] ?? null) : null

  return (
    <div className="as-alto__lavoro">
      <Bottone
        verso="primario"
        piccolo
        onClick={() => gesto.mutate(azione)}
        disabled={gesto.isPending}
      >
        {t(VERBI[azione])}
      </Bottone>
      {corrente && (
        <span className="as-alto__fase">
          {nomeFase === null ? corrente.name : t(nomeFase)}
          {corrente.total !== null && corrente.current !== null && (
            <> {t("scan.progress", { fatti: numero(corrente.current), su: numero(corrente.total) })}</>
          )}
        </span>
      )}
      {gesto.error && <Avviso esito="allarme">{gesto.error.message}</Avviso>}
      {/* Una cartella caduta MENTRE la si leggeva non sta fra le saltate -- il pre-controllo
          l'aveva passata -- e la sua ricevuta si va a leggere in Impostazioni / Le letture. Senza
          questa riga l'utente leggerebbe "fatto" con una cartella non letta. */}
      {stato.data?.scan?.state === "error" && (
        <Avviso esito="allarme">{t("scan.lostFolder")}</Avviso>
      )}
      {saltate.length > 0 && (
        <ul className="as-elenco">
          {saltate.map((c) => (
            <li key={c.folder_id}>{t(SALTI[c.reason], { cartella: c.root_path })}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
