import { useQuery } from "@tanstack/react-query"
import { useState } from "react"

import { api } from "./api/client"
import type { components } from "./api/schema"
import { Avviso } from "./componenti/Avviso"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { type Esito, Pillola } from "./componenti/Pillola"
import { Scheletro } from "./componenti/Scheletro"
import { Tema } from "./componenti/Tema"
import { durata, numero, orario, t } from "./i18n"
import { giornoDetto, useGesto, useStato } from "./Scansiona"

type Scansione = components["schemas"]["ScanOut"]

const A_PAGINA = 20 // [T] piu' di un mese di scansioni quotidiane
const PAGINA_ROTTA = 200 // [T] il massimo di `GET /scans` (`api/scan_history.py`)
const MENTRE_GIRA_MS = 1500 // [T] come lo stato della spina (`Scansiona.tsx`)

const PILLOLE: Record<Scansione["outcome"], { esito: Esito; segno: string }> = {
  completed: { esito: 0, segno: "✓" /* glifo-ok: segno della tavola */ },
  stopped: { esito: 1, segno: "!" /* glifo-ok: segno della tavola */ },
  blocked: { esito: 2, segno: "✕" /* glifo-ok: segno della tavola */ },
  running: { esito: "neutra", segno: "" },
}

/** The sections' frame (tavola `SezioneServizi`): the sheet's `al-imp-sezione`, desktop and phone. */
export function Sezione({ children }: { children: React.ReactNode }) {
  const formato = useFormato()
  return (
    <Tema>
      <div className="al-c-sezione-servizi__blocco-1" data-formato={formato}>
        <div className="al-imp-sezione">{children}</div>
      </div>
    </Tema>
  )
}

/**
 * **Scansioni** (tavola Impostazioni v82, `SezioneServizi`): the scans as the user made them
 * (`GET /scans`), newest first. While one runs the list follows it.
 */
export function Scansioni() {
  const formato = useFormato()
  const [quante, setQuante] = useState(A_PAGINA)
  const scansioni = useQuery({
    queryKey: ["scans", quante],
    queryFn: async () => {
      // pages of the route's maximum until `quante`: "Mostra altre" grows past it
      const items: Scansione[] = []
      for (;;) {
        const { data, error } = await api.GET("/api/v1/scans", {
          params: {
            query: { limit: Math.min(PAGINA_ROTTA, quante - items.length), offset: items.length },
          },
        })
        if (error) throw new Error(t("settings.scans.failed"))
        items.push(...data.items)
        if (data.items.length === 0 || items.length >= Math.min(quante, data.total)) {
          return { items, total: data.total }
        }
      }
    },
    refetchInterval: (q) =>
      q.state.data?.items[0]?.outcome === "running" ? MENTRE_GIRA_MS : false,
  })
  const voci = scansioni.data?.items ?? []
  return (
    <Sezione>
      <p className="al-imp-intro">{t("settings.scans.intro")}</p>
      {scansioni.isPending && (
        <Scheletro
          formato={formato}
          griglia="minmax(0,1fr)"
          carte={[0, 1].map(() => ({
            h: "220px",
            blocchi: [{ h: "24px", w: "180px" }, { flex: "1" }],
          }))}
        />
      )}
      {scansioni.isError && (
        <Avviso
          tipo="blocco"
          formato={formato}
          segno="!"
          titolo={t("settings.scans.failed")}
          azione={t("settings.retry")}
          onAzione={() => void scansioni.refetch()}
        />
      )}
      {scansioni.isSuccess && voci.length === 0 && (
        <Avviso
          tipo="blocco"
          formato={formato}
          segno="?"
          titolo={t("settings.scans.none")}
          testo={t("settings.scans.none.how")}
        />
      )}
      {voci.map((s) => (
        <CartaScansione key={s.id} s={s} />
      ))}
      {(scansioni.data?.total ?? 0) > voci.length && (
        <div className="al-imp-gesti al-imp-gesti--inizio">
          <a
            href="#"
            role="button"
            onClick={gesto(() => setQuante((n) => n + A_PAGINA))}
            className="al-bottone al-bottone--contorno al-bottone--piccolo"
          >
            {t("settings.scans.more")}
          </a>
        </div>
      )}
    </Sezione>
  )
}

function quando(s: Scansione): string {
  if (s.outcome === "running") return t("settings.scans.now")
  return t("settings.scans.when", {
    giorno: giornoDetto(s.started_at, s.started_day ?? undefined),
    ora: orario(s.started_at),
  })
}

function esitoDetto(s: Scansione): string {
  if (s.outcome === "running" && s.progress) {
    return t("settings.scans.running.pct", { pct: numero(s.progress.pct) })
  }
  return t(`settings.scans.${s.outcome}`)
}

function CartaScansione({ s }: { s: Scansione }) {
  const titolo = quando(s)
  const lungo = durata(s.duration_s)
  const pillola = PILLOLE[s.outcome]
  return (
    // with the outcome: two scans in the same minute are still two regions with their own name
    <section
      className="al-imp-carta"
      aria-label={`${titolo} · ${esitoDetto(s)}` /* glifo-ok: segno della tavola */}
    >
      <div className="al-imp-testa">
        <span className="al-imp-titoli">
          <b className="al-imp-titolo">{titolo}</b>
          {lungo && <span className="al-imp-sotto">{lungo}</span>}
        </span>
        <Pillola
          esito={pillola.esito}
          segno={pillola.segno}
          testo={esitoDetto(s)}
          dimensione="piccola"
          fondo="carta"
        />
      </div>
      {s.progress && (
        <span
          role="progressbar"
          aria-label={esitoDetto(s)}
          aria-valuenow={s.progress.pct}
          aria-valuemin={0}
          aria-valuemax={100}
          className="al-imp-barra"
        >
          <span style={{ width: `${s.progress.pct}%` }} />
        </span>
      )}
      <Riga etichetta={t("settings.scans.folders")} colonna>
        {s.folders.map((c) => (
          <span key={c} className="al-imp-percorso">
            {c}
          </span>
        ))}
      </Riga>
      <Riga etichetta={t("settings.scans.entered")}>
        <b>
          {s.progress
            ? t("settings.scans.entered.read", {
                letti: numero(s.progress.read),
                su: numero(s.progress.total),
              })
            : t("settings.scans.entered.n", { n: numero(s.new) })}
        </b>
      </Riga>
      {(s.left_out.length > 0 || s.dirs_left_out.length > 0) && (
        <Riga etichetta={t("settings.scans.leftOut")} colonna>
          {s.left_out.map((f) => (
            <span key={f.reason}>
              {t(`settings.scans.out.${f.reason}`, { n: numero(f.count) })}
            </span>
          ))}
          {s.dirs_left_out.map((d) => (
            <span key={`${d.why}-${d.path}`} className="al-imp-percorso">
              {t(`settings.scans.dir.${d.why}`, { percorso: d.path })}
            </span>
          ))}
        </Riga>
      )}
      {s.unread > 0 && <NonLeggibili s={s} />}
      {s.reason && (
        <Riga etichetta={t("settings.scans.reason")}>
          {t(`settings.scans.why.${s.reason}`, { cartella: s.reason_folder ?? "" })}
        </Riga>
      )}
      <Gesti s={s} />
    </section>
  )
}

function Riga({
  etichetta,
  colonna = false,
  children,
}: {
  etichetta: string
  colonna?: boolean
  children: React.ReactNode
}) {
  return (
    <div className="al-imp-riga">
      <span className="al-imp-etichetta">{etichetta}</span>
      <span className={colonna ? "al-imp-valore al-imp-valore--colonna" : "al-imp-valore"}>
        {children}
      </span>
    </div>
  )
}

/** The first five unread files come with the scan; "Mostra tutti" asks the rest. */
function NonLeggibili({ s }: { s: Scansione }) {
  const [tutti, setTutti] = useState(false)
  const elenco = useQuery({
    queryKey: ["scans", "unread", s.id],
    enabled: tutti,
    queryFn: async () => {
      // pages of the route's maximum until the total: they can be thousands
      const voci: Scansione["unread_files"] = []
      for (;;) {
        const { data, error } = await api.GET("/api/v1/scans/{scan_id}/unread", {
          params: { path: { scan_id: s.id }, query: { limit: 1000, offset: voci.length } },
        })
        if (error) throw new Error(t("settings.scans.unread.failed"))
        voci.push(...data.items)
        if (data.items.length === 0 || voci.length >= data.total) return voci
      }
    },
  })
  const file = tutti && elenco.data ? elenco.data : s.unread_files
  const altri = s.unread_kept && s.unread > s.unread_files.length && !elenco.data
  return (
    <Riga etichetta={t("settings.scans.unread", { n: numero(s.unread) })} colonna>
      {file.map((f, i) => (
        // the path is relative to its folder: two folders can repeat it
        <span key={i} className="al-imp-file">
          <span className="al-imp-percorso">{f.file}</span>
          <span className="al-imp-nota">{t(`settings.scans.file.${f.reason}`)}</span>
        </span>
      ))}
      {!s.unread_kept && <span className="al-imp-nota">{t("settings.scans.unread.gone")}</span>}
      {elenco.isError && <span className="al-imp-nota">{elenco.error.message}</span>}
      {altri && (
        <a
          href="#"
          role="button"
          aria-disabled={elenco.isFetching ? "true" : undefined}
          onClick={gesto(() => setTutti(true))}
          className="al-bottone al-bottone--testo al-bottone--piccolo al-bottone--a-filo"
        >
          {t("settings.scans.unread.all", { n: numero(s.unread) })}
        </a>
      )}
    </Riga>
  )
}

/** Interrompi while it runs, Riprova on the newest blocked one: the gear menu's gestures. */
function Gesti({ s }: { s: Scansione }) {
  const azione = useGesto()
  const stato = useStato().data
  if (s.outcome !== "running" && !s.can_retry) return null
  const ferma = s.outcome === "running"
  return (
    <div className="al-imp-gesti">
      {azione.error && <span className="al-imp-nota">{azione.error.message}</span>}
      <a
        href="#"
        role="button"
        aria-disabled={azione.isPending || (!ferma && !stato) ? "true" : undefined}
        onClick={gesto(() => {
          if (azione.isPending) return
          if (ferma) azione.mutate("stop")
          else if (stato) azione.mutate(stato.action)
        })}
        className={
          ferma
            ? "al-bottone al-bottone--contorno al-bottone--piccolo"
            : "al-bottone al-bottone--pieno al-bottone--piccolo"
        }
      >
        {t(ferma ? "settings.scans.stop" : "settings.scans.retry")}
      </a>
    </div>
  )
}
