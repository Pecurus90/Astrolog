import { useMutation, useMutationState, useQuery, useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { motivo } from "./api/motivo"
import { type Chiave, giorno, numero, orario, t } from "./i18n"

/**
 * La scansione nel telaio (disegno v26): nella barra in alto in quattro stati -- a riposo, al
 * lavoro, fermata, bloccata -- nel foglio "Altro" sul telefono, e i suoi avvisi in testa al corpo.
 *
 * - **Il verbo non lo decide il frontend**: `action` arriva dal backend (`start` / `stop` /
 *   `resume`), l'unico a sapere se un lavoro gira o se ne resta uno a meta'.
 * - **Sta nel telaio e non in una pagina** perche' il lavoro sopravvive alla pagina: cambiando
 *   schermata deve restare fermabile.
 * - **Il ritmo lo dichiara il contratto della spina**: ogni 1,5 s mentre gira, ogni 60 s da
 *   fermo, niente a scheda nascosta.
 * - **Le cartelle che non si sono potute leggere si dicono**, in testa alla pagina (Marco,
 *   7/10/2026): tacerle farebbe sembrare completa una scansione che non lo e'.
 * - **Quando il lavoro finisce, cio' che l'app mostra e' vecchio**: si rilegge.
 */

const MENTRE_GIRA_MS = 1500
const DA_FERMO_MS = 60000
const GESTO = ["scan-gesto"]

type Azione = "start" | "stop" | "resume"
type Stato = components["schemas"]["PipelineStatus"]

/** Il verbo del backend e la parola che l'utente legge: un quarto verbo non compilerebbe. */
const VERBI: Record<Azione, Chiave> = {
  start: "scan.start",
  stop: "scan.stop",
  resume: "scan.resume",
}

/** Perche' una cartella e' stata saltata. Chiusa: un motivo nuovo qui non compilerebbe, invece
 *  di uscire a schermo con una ragione sbagliata. */
const SALTI: Record<components["schemas"]["FolderSkipped"]["reason"], Chiave> = {
  root_unreachable: "scan.skipped.unreachable",
  scan_running: "scan.skipped.running",
}

/** I rifiuti che si riparano nelle Cartelle: solo questi portano li' con *Vedi*. */
const DI_CARTELLE: ReadonlySet<Chiave> = new Set(["scan.error.no_folders", "scan.error.no_readable_folders"])

/** Un rifiuto del gesto, con la chiave della sua frase: serve a sapere dove porta *Vedi*. */
class Rifiuto extends Error {
  constructor(readonly chiave: Chiave) {
    super(t(chiave))
  }
}

/** I rifiuti che il backend puo' mandare a questo gesto, con la loro frase. */
const RIFIUTI: Record<string, Chiave> = {
  no_folders: "scan.error.no_folders",
  no_readable_folders: "scan.error.no_readable_folders",
  worker_busy: "scan.error.worker_busy",
}

/** Le fasi nelle parole di chi guarda. Aperta: una fase nuova si scrive com'e', un degrado onesto. */
const FASI: Record<string, Chiave> = {
  scan: "scan.stage.scan",
  normalize: "scan.stage.normalize",
  solve: "scan.stage.solve",
  identify: "scan.stage.identify",
  group: "scan.stage.group",
}

function useStato() {
  return useQuery({
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
}

function useGesto() {
  const cache = useQueryClient()
  return useMutation({
    mutationKey: GESTO,
    mutationFn: async (azione: Azione) => {
      const { data, error } =
        azione === "stop"
          ? await api.POST("/api/v1/pipeline/stop")
          : azione === "resume"
            ? await api.POST("/api/v1/pipeline/run")
            : await api.POST("/api/v1/scan")
      if (error) throw new Rifiuto(motivo(error, RIFIUTI, "scan.failed"))
      return data
    },
    // Il primo giro subito dopo il gesto: aspettare il prossimo battito farebbe sembrare che
    // il pulsante non abbia fatto niente.
    onSettled: () => void cache.invalidateQueries({ queryKey: ["pipeline"] }),
  })
}

/** La fase in corso, con la parola e i numeri, o niente se non ce n'e' una. */
function faseDi(stato: Stato | undefined) {
  const nome = stato?.worker.stage
  const corrente = nome ? stato?.worker.stages.find((s) => s.name === nome) : undefined
  if (!corrente) return null
  const parola = FASI[corrente.name]
  const conti = corrente.total !== null && corrente.current !== null
  return {
    parola: parola ? t(parola) : corrente.name,
    conto: conti ? t("scan.progress", { fatti: numero(corrente.current ?? 0), su: numero(corrente.total ?? 0) }) : null,
    // la larghezza della pista e' un dato, l'unico `style` che il foglio ammette
    quanto: conti && corrente.total ? `${Math.round(((corrente.current ?? 0) / corrente.total) * 100)}%` : null,
  }
}

/** La scansione nella barra in alto. */
export function Scansiona() {
  const cache = useQueryClient()
  const stato = useStato()
  const gesto = useGesto()

  // Il timbro di fine corsa: cambia una volta per corsa, quindi quando cambia il lavoro e'
  // finito davvero -- e cio' che le pagine mostrano va riletto.
  const finita = stato.data?.worker.ended_at ?? null
  useEffect(() => {
    if (finita === null) return
    void cache.invalidateQueries({ queryKey: ["review"] })
    void cache.invalidateQueries({ queryKey: ["scan-runs"] })
  }, [finita, cache])

  const azione = stato.data?.action ?? "start"
  const fase = faseDi(stato.data)
  const bottone = (verso: "tenue" | "nudo") => (
    <Bottone verso={verso} piccolo onClick={() => gesto.mutate(azione)} disabled={gesto.isPending}>
      {t(VERBI[azione])}
    </Bottone>
  )

  if (stato.data?.worker.state === "error") {
    return (
      <div className="as-telaio__lavoro">
        <span className="as-stato as-stato--allarme">{t("scan.blocked")}</span>
        <span className="as-telaio__motivo">{stato.data.worker.error ?? t("scan.blocked.why")}</span>
        <Bottone verso="tenue" piccolo a="/impostazioni/letture">
          {t("scan.blocked.see")}
        </Bottone>
        {/* bloccata non e' finita: il backend chiede di ripartire, e il desktop non ha altro posto */}
        {bottone("tenue")}
      </div>
    )
  }
  if (azione === "stop") {
    return (
      <div className="as-telaio__lavoro">
        <span className="as-telaio__fase">{fase?.parola ?? t("scan.working")}</span>
        {fase?.quanto && <Pista quanto={fase.quanto} />}
        {fase?.conto && <span className="as-telaio__conta-lavoro">{fase.conto}</span>}
        {bottone("nudo")}
      </div>
    )
  }
  if (azione === "resume") {
    return (
      <div className="as-telaio__lavoro">
        <span className="as-telaio__fase">{t("scan.stopped")}</span>
        {fase?.quanto && <Pista quanto={fase.quanto} ferma />}
        {fase?.conto && <span className="as-telaio__conta-lavoro">{fase.conto}</span>}
        {bottone("tenue")}
      </div>
    )
  }
  return (
    <div className="as-telaio__lavoro">
      {finita && (
        <span className="as-telaio__ultima">
          {t("scan.last", { giorno: giorno(finita), ora: orario(finita) })}
        </span>
      )}
      {bottone("tenue")}
    </div>
  )
}

function Pista({ quanto, ferma = false }: { quanto: string; ferma?: boolean }) {
  return (
    <span className={ferma ? "as-telaio__pista as-telaio__pista--ferma" : "as-telaio__pista"}>
      <span className="as-telaio__riempi" style={{ width: quanto }} />
    </span>
  )
}

/** La scansione nel foglio "Altro" del telefono: la fase, i numeri e il gesto. Sul telefono la
 *  barra non la porta: bloccata, il motivo e Vedi stanno qui o in nessun posto. */
export function ScansioneNelFoglio() {
  const stato = useStato()
  const gesto = useGesto()
  const azione = stato.data?.action ?? "start"
  const fase = faseDi(stato.data)
  const bloccata = stato.data?.worker.state === "error"
  return (
    <div className="as-foglio__lavoro">
      <span className="as-stanotte__etichetta">{t("scan.label")}</span>
      {bloccata && (
        <div className="as-foglio__lavoro-riga">
          <span className="as-stato as-stato--allarme">{t("scan.blocked")}</span>
          <Bottone verso="tenue" piccolo a="/impostazioni/letture">
            {t("scan.blocked.see")}
          </Bottone>
        </div>
      )}
      <div className="as-foglio__lavoro-riga">
        <span>
          {bloccata
            ? (stato.data?.worker.error ?? t("scan.blocked.why"))
            : fase
              ? [fase.parola, fase.conto].filter(Boolean).join(" \u00B7 ")
              : t("scan.idle")}
        </span>
        <Bottone verso="nudo" piccolo onClick={() => gesto.mutate(azione)} disabled={gesto.isPending}>
          {t(VERBI[azione])}
        </Bottone>
      </div>
      {fase?.quanto && (
        <span className="as-stanotte__pista">
          <span className="as-telaio__riempi" style={{ width: fase.quanto }} />
        </span>
      )}
    </div>
  )
}

function isAvvio(dati: unknown): dati is components["schemas"]["ScanAllStarted"] {
  return typeof dati === "object" && dati !== null && "skipped" in dati
}

/** Cio' che la scansione non ha potuto fare, come riga di stato in testa alla pagina: un rifiuto,
 *  una cartella caduta mentre la si leggeva, le cartelle saltate. Ognuno porta dove si ripara. */
export function AvvisiDellaScansione() {
  const stato = useStato()
  const gesti = useMutationState({
    filters: { mutationKey: GESTO },
    select: (m) => ({ errore: m.state.error, dati: m.state.data }),
  })
  const ultimo = gesti.at(-1)
  // Solo "avvia tutte" risponde con le saltate; fermare e riprendere no.
  const dati = ultimo?.dati
  const saltate = isAvvio(dati) ? dati.skipped : []
  const errore = ultimo?.errore
  const vedi = (a: string) => (
    <Bottone verso="tenue" piccolo a={a}>
      {t("scan.blocked.see")}
    </Bottone>
  )
  return (
    <>
      {errore && (
        <Avviso
          esito="allarme"
          pagina
          azioni={errore instanceof Rifiuto && DI_CARTELLE.has(errore.chiave) ? vedi("/impostazioni/cartelle") : undefined}
        >
          {errore.message}
        </Avviso>
      )}
      {/* Una cartella caduta MENTRE la si leggeva non sta fra le saltate: senza questa riga
          l'utente leggerebbe "fatto" con una cartella non letta. */}
      {stato.data?.scan?.state === "error" && (
        <Avviso esito="allarme" pagina ruolo="status" azioni={vedi("/impostazioni/letture")}>
          {t("scan.lostFolder")}
        </Avviso>
      )}
      {saltate.map((c) => (
        <Avviso esito="attesa" pagina key={c.folder_id} azioni={vedi("/impostazioni/cartelle")}>
          {t(SALTI[c.reason], { cartella: c.root_path })}
        </Avviso>
      ))}
    </>
  )
}
