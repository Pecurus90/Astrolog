import { useMutation, useMutationState, useQuery, useQueryClient } from "@tanstack/react-query"
import { type CSSProperties, type ReactNode, useEffect } from "react"
import { Link } from "react-router"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { motivo } from "./api/motivo"
import { gesto } from "./componenti/gesto"
import type { Formato } from "./componenti/Tema"
import { type Chiave, giorno, numero, orario, oreEMinuti, t } from "./i18n"

/**
 * La scansione nel telaio v76: il segno sull'ingranaggio (e su Altro del telefono), il riquadro
 * nel menu dell'ingranaggio e nel menu Altro del telefono, la riga dell'ultima scansione a riposo,
 * e i suoi avvisi in testa al corpo.
 *
 * - **Il verbo lo decide il backend**: `action` (`start` / `stop` / `resume`) e' cio' che il
 *   bottone manda; la parola dipende dallo stato (bloccata dice Riprova).
 * - **Sta nel telaio e non in una pagina** perche' il lavoro sopravvive alla pagina.
 * - **Il ritmo lo dichiara il contratto della spina**: ogni 1.5 s mentre gira, ogni 60 s da
 *   fermo, niente a scheda nascosta.
 * - **Quando il lavoro finisce, cio' che l'app mostra e' vecchio**: si rilegge.
 */

const MENTRE_GIRA_MS = 1500
const DA_FERMO_MS = 60000
const GESTO = ["scan-gesto"]

type Azione = "start" | "stop" | "resume"
type Stato = components["schemas"]["PipelineStatus"]

/** Lo stato della scansione come lo disegna la tavola (`scansione` del Telaio). */
export type StatoScansione = "ferma" | "in corso" | "interrotta" | "bloccata"

/** Perche' una cartella e' stata saltata. Chiusa: un motivo nuovo qui non compilerebbe. */
const SALTI: Record<components["schemas"]["FolderSkipped"]["reason"], Chiave> = {
  root_unreachable: "scan.skipped.unreachable",
  scan_running: "scan.skipped.running",
}

/** I rifiuti che si riparano nelle Cartelle: solo questi portano li' con *Dettagli*. */
const DI_CARTELLE: ReadonlySet<Chiave> = new Set([
  "scan.error.no_folders",
  "scan.error.no_readable_folders",
])

/** Un rifiuto del gesto, con la chiave della sua frase: serve a sapere dove porta *Dettagli*. */
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

/** Lo stato del lavoro di sottofondo: il telaio e la Dashboard leggono questo. */
export function useStato() {
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

/** Lo stato della tavola dai campi del backend: bloccata prima di tutto, poi il verbo. */
export function statoDi(dati: Stato | undefined): StatoScansione {
  if (dati?.worker.state === "error") return "bloccata"
  if (dati?.action === "stop") return "in corso"
  if (dati?.action === "resume") return "interrotta"
  return "ferma"
}

/** Come si dice lo stato accanto a un nome ("Impostazioni, scansione in corso"); a riposo niente. */
const PAROLE_ARIA: Record<StatoScansione, Chiave | null> = {
  ferma: null,
  "in corso": "frame.scan.running.aria",
  interrotta: "frame.scan.stopped.aria",
  bloccata: "frame.scan.blocked.aria",
}

/** Il nome di un bottone che porta il segno della scansione. */
export function nomeConScansione(nome: string, stato: StatoScansione): string {
  const parola = PAROLE_ARIA[stato]
  return parola ? t("frame.with", { nome, stato: t(parola) }) : nome
}

/** Il timbro di fine corsa cambia una volta per corsa: quando cambia, cio' che le pagine
 *  mostrano va riletto. Lo monta il telaio, che c'e' su ogni pagina. */
export function useFineDelLavoro() {
  const cache = useQueryClient()
  const finita = useStato().data?.worker.ended_at ?? null
  useEffect(() => {
    if (finita === null) return
    for (const chiave of ["review", "scan-runs", "nights", "year"]) {
      void cache.invalidateQueries({ queryKey: [chiave] })
    }
  }, [finita, cache])
}

/** Il segno della scansione: l'anello che gira mentre lavora, "!" ambra interrotta o bloccata.
 *  Le misure sono quelle della tavola, per l'ingranaggio (`tondo`) e per la scheda Altro. */
export function SegnoDellaScansione({
  stato,
  dove,
}: {
  stato: StatoScansione
  dove: "tondo" | "scheda"
}) {
  if (stato === "ferma") return null
  const gira = stato === "in corso"
  const tondo = dove === "tondo"
  const forma: CSSProperties = gira
    ? {
        position: "absolute",
        borderRadius: "50%",
        border: "2px solid var(--accento)",
        borderRightColor: "transparent",
        animation: "alSpin 1.1s linear infinite",
        ...(tondo
          ? { inset: "-3px", borderBottomColor: "transparent" }
          : { top: 6, left: "calc(50% + 5px)", width: 12, height: 12, boxSizing: "border-box" }),
      }
    : {
        position: "absolute",
        width: 16,
        height: 16,
        borderRadius: "50%",
        background: "var(--avviso)",
        color: "var(--avviso-testo)",
        fontSize: 11,
        fontWeight: 700,
        display: "grid",
        placeItems: "center",
        boxShadow: `0 0 0 2px ${tondo ? "var(--telaio)" : "var(--carta)"}`,
        ...(tondo ? { top: "-3px", right: "-3px" } : { top: 4, left: "calc(50% + 5px)" }),
      }
  return (
    <span aria-hidden="true" style={forma}>
      {gira ? null : "!"}
    </span>
  )
}

/** La riga sotto *Scansiona* a riposo: quando, quanti file nuovi, e se qualcuno non si e' letto. */
function rigaUltima(ultima: components["schemas"]["LastScanOut"]): string {
  const quando = { giorno: giorno(ultima.ended_at), ora: orario(ultima.ended_at) }
  const nuovi =
    ultima.new === 0 ? t("frame.scan.new.none") : t("frame.scan.new", { n: numero(ultima.new) })
  return ultima.not_read === 0
    ? t("frame.scan.last.ok", { ...quando, nuovi })
    : t("frame.scan.last.unread", {
        ...quando,
        nuovi,
        nonLetti: t("frame.scan.unread", { n: numero(ultima.not_read) }),
      })
}

/** *Scansiona* a riposo, voce del menu dell'ingranaggio col suo percorso (Menu v76). */
export function VoceScansiona({ icona }: { icona: ReactNode }) {
  const stato = useStato()
  const azione = useGesto()
  const ultima = stato.data?.last_scan ?? null
  return (
    <a
      className="al-c-menu__riga-5"
      href="#"
      role="menuitem"
      aria-disabled={azione.isPending || undefined}
      onClick={gesto(() => !azione.isPending && azione.mutate(stato.data?.action ?? "start"))}
    >
      {icona}
      <span className="al-c-menu__colonna-3">
        <span className="al-c-menu__testo-4">{t("scan.start")}</span>
        {ultima && <span className="al-c-menu__testo-2">{rigaUltima(ultima)}</span>}
      </span>
    </a>
  )
}

/** I numeri della scansione: file letti su quanti, e il tempo che resta quando c'e'. */
function letti(dati: Stato): { fatti: string; su: string } | null {
  const evento = dati.scan?.last_event
  return evento ? { fatti: numero(evento.current), su: numero(evento.total) } : null
}

/** Cio' che il riquadro dice in ogni stato acceso: titolo, fase, riga, la parola del bottone. */
function detto(dati: Stato, stato: Exclude<StatoScansione, "ferma">) {
  const corrente = dati.worker.stages.find((s) => s.name === dati.worker.stage)
  const conti = letti(dati)
  const finita = dati.worker.ended_at
  const quando = finita ? t("frame.scan.when", { giorno: giorno(finita), ora: orario(finita) }) : ""
  if (stato === "bloccata") {
    // Il worker va in errore anche per solve/identify/db: la cartella si incolpa solo se la lettura e' caduta.
    const perche = dati.scan?.state === "error" ? t("scan.lostFolder") : t("scan.blocked.why")
    const riga = [perche, conti ? t("frame.scan.blocked.read", conti) : null]
    return {
      titolo: t("frame.scan.blocked"),
      fase: quando,
      riga: riga.filter(Boolean).join(" "),
      bottone: t("frame.scan.retry"),
      pct: null,
    }
  }
  if (stato === "interrotta") {
    const riga = [
      conti ? t("frame.scan.stopped.read", conti) : null,
      t("frame.scan.stopped.resume"),
    ]
    return {
      titolo: t("frame.scan.stopped"),
      fase: quando,
      riga: riga.filter(Boolean).join(" "),
      bottone: t("scan.resume"),
      pct: corrente?.pct ?? null,
    }
  }
  const fase = corrente
    ? FASI[corrente.name]
      ? t(FASI[corrente.name] as Chiave)
      : corrente.name
    : t("scan.working")
  const resta = dati.scan?.remaining_s
  let riga = ""
  if (conti) {
    const fatti = t("frame.scan.read", conti)
    riga = resta ? t("frame.scan.left", { letti: fatti, tempo: oreEMinuti(resta) }) : fatti
  } else if (corrente?.current != null && corrente.total != null) {
    riga = t("scan.progress", { fatti: numero(corrente.current), su: numero(corrente.total) })
  }
  return {
    titolo: t("frame.scan.running"),
    fase,
    riga,
    bottone: t("scan.stop"),
    pct: corrente?.pct ?? null,
  }
}

/** Il riquadro della scansione accesa, in testa al menu dell'ingranaggio e al menu Altro del
 *  telefono: titolo, fase, barra, quanto ha letto, il gesto, e da bloccata *Dettagli*. */
export function RiquadroDellaScansione({ formato }: { formato: Formato }) {
  const dati = useStato().data
  const azione = useGesto()
  const stato = statoDi(dati)
  if (!dati || stato === "ferma") return null
  const d = detto(dati, stato)
  const alto = formato === "telefono" ? "44px" : "36px"
  const pieno = stato === "in corso"
  return (
    <div className="al-c-menu__colonna-2" role="group" aria-label={t("frame.scan.group")}>
      <span className="al-c-menu__riga-1">
        <b className="al-c-menu__testo-1">{d.titolo}</b>
        <span className="al-c-menu__testo-2">{d.fase}</span>
      </span>
      {/* not a progressbar: ARIA allows none inside a menu; the line below says the numbers */}
      {d.pct !== null && (
        <span className="al-c-menu__riga-2" aria-hidden="true">
          <span className="al-c-menu__pillola-1" style={{ width: `${d.pct}%` }} />
        </span>
      )}
      {d.riga && <span className="al-c-menu__testo-3">{d.riga}</span>}
      <a
        className="al-c-menu__riga-3"
        href="#"
        role="menuitem"
        aria-disabled={azione.isPending || undefined}
        onClick={gesto(() => !azione.isPending && azione.mutate(dati.action))}
        style={{
          minHeight: alto,
          background: pieno ? "var(--carta)" : "var(--accento)",
          color: pieno ? "var(--testo)" : "var(--scelta-testo)",
        }}
      >
        {d.bottone}
      </a>
      {stato === "bloccata" && (
        <Link
          className="al-c-menu__riga-4"
          to="/impostazioni/letture"
          role="menuitem"
          style={{ minHeight: alto }}
        >
          {t("scan.blocked.see")}
        </Link>
      )}
    </div>
  )
}

function conSaltate(dati: unknown): dati is { skipped: components["schemas"]["FolderSkipped"][] } {
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
  // "avvia tutte" e Riprendi che rilegge rispondono con le saltate; fermare con una lista vuota
  const dati = ultimo?.dati
  const saltate = conSaltate(dati) ? dati.skipped : []
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
          azioni={
            errore instanceof Rifiuto && DI_CARTELLE.has(errore.chiave)
              ? vedi("/impostazioni/cartelle")
              : undefined
          }
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
