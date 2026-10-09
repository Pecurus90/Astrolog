import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useRef } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { CartaSola } from "./CartaSola"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { giorno, numero, orario, t } from "./i18n"

type Stato = components["schemas"]["BackupStatus"]
type Conti = components["schemas"]["BackupCounts"]

/** Lo stato del file delle risposte, letto una volta per tutta l'app (ADR 0017). */
export function useBackup() {
  return useQuery({
    queryKey: ["backup"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/backup")
      if (error) throw new Error(t("backup.failed"))
      return data
    },
  })
}

function quando(c: Conti): string {
  return c.written_at ? t("backup.when", { giorno: giorno(c.written_at), ora: orario(c.written_at) }) : ""
}

function contenuto(c: Conti): string {
  return t("backup.counts", {
    risposte: c.answers,
    siti: c.sites,
    cartelle: c.folders,
    pezzi: c.instruments + c.filters,
  })
}

/**
 * Il database e' nuovo e accanto c'e' il file delle risposte: si chiede se rimetterle, prima del
 * primo avvio. Rimesse, si rileggono le cartelle: frame, corredi e notti li rifa' la lettura.
 */
export function RipristinoProposto({ stato }: { stato: Stato }) {
  const cache = useQueryClient()
  const rimetti = useMutation({
    mutationFn: async () => {
      const { error } = await api.POST("/api/v1/backup/restore")
      if (error) throw new Error(t("backup.restoreFailed"))
      await api.POST("/api/v1/scan")
    },
    onSuccess: () => cache.invalidateQueries(),
  })
  const ricomincia = useMutation({
    mutationFn: async () => {
      const { error } = await api.POST("/api/v1/backup/decline")
      if (error) throw new Error(t("backup.failed"))
    },
    onSuccess: () => cache.invalidateQueries({ queryKey: ["backup"] }),
  })
  const conti = stato.last

  return (
    <CartaSola
      titolo={t("backup.found.title")}
      // la data, se c'e', e' una frase sua: senza, la domanda non comincia con un punto
      sotto={[conti ? quando(conti) : "", t("backup.found.question")].filter(Boolean).join(". ")}
      conti={
        conti
          ? [
              { nome: t("backup.count.answers"), dato: numero(conti.answers) },
              { nome: t("backup.count.sites"), dato: numero(conti.sites) },
              { nome: t("backup.count.folders"), dato: numero(conti.folders) },
              { nome: t("backup.count.gear"), dato: numero(conti.instruments + conti.filters) },
            ]
          : []
      }
      azioni={
        <>
          <Bottone onClick={() => ricomincia.mutate()} disabled={rimetti.isPending}>
            {t("backup.found.decline")}
          </Bottone>
          <Bottone verso="primario" onClick={() => rimetti.mutate()} disabled={rimetti.isPending}>
            {t("backup.found.restore")}
          </Bottone>
        </>
      }
    >
      {rimetti.error && <Avviso esito="allarme">{rimetti.error.message}</Avviso>}
      {ricomincia.error && <Avviso esito="allarme">{ricomincia.error.message}</Avviso>}
    </CartaSola>
  )
}

/**
 * La sezione **Backup** delle Impostazioni: quando e' stato scritto il file, dove sta, e i due
 * gesti per un altro computer. L'Esporta non porta le chiavi dei servizi (ADR 0017).
 */
export function ImpostazioniBackup() {
  const cache = useQueryClient()
  const stato = useBackup()
  const scegli = useRef<HTMLInputElement>(null)
  const esporta = useMutation({
    mutationFn: async () => {
      const { data, error } = await api.GET("/api/v1/backup/export", { parseAs: "blob" })
      if (error || !data) throw new Error(t("backup.exportFailed"))
      const link = document.createElement("a")
      link.href = URL.createObjectURL(data)
      link.download = "risposte.json"
      link.click()
      URL.revokeObjectURL(link.href)
    },
  })
  const importa = useMutation({
    mutationFn: async (file: File) => {
      let contenuto: Record<string, unknown>
      try {
        contenuto = JSON.parse(await file.text()) as Record<string, unknown>
      } catch {
        throw new Error(t("backup.notABackup"))
      }
      const { error, response } = await api.POST("/api/v1/backup/import", { body: contenuto })
      if (response.status === 422) throw new Error(t("backup.notABackup"))
      if (error) throw new Error(t("backup.importFailed"))
      await api.POST("/api/v1/scan")
    },
    onSuccess: () => cache.invalidateQueries(),
  })
  const ultimo = stato.data?.last

  return (
    <section className="as-carta">
      <div className="as-carta__intestazione">
        <div>
          <h2 className="as-carta__titolo">{t("backup.title")}</h2>
          <p className="as-carta__domanda">{t("backup.what")}</p>
        </div>
      </div>
      <div className="as-carta__corpo as-carta__corpo--colonna">
        {stato.error && <Avviso esito="allarme">{stato.error.message}</Avviso>}
        {stato.data && (
          <p>
            {ultimo ? [quando(ultimo), contenuto(ultimo)].filter(Boolean).join(" \u00b7 ") : t("backup.none")}
            <br />
            <code>{stato.data.path}</code>
          </p>
        )}
        {stato.data?.unreadable && <Avviso esito="allarme">{t("backup.unreadable")}</Avviso>}
        <div>
          <Bottone onClick={() => esporta.mutate()} disabled={esporta.isPending}>
            {t("backup.export")}
          </Bottone>{" "}
          <Bottone onClick={() => scegli.current?.click()} disabled={importa.isPending}>
            {t("backup.import")}
          </Bottone>
          <input
            ref={scegli}
            type="file"
            accept="application/json,.json"
            hidden
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) importa.mutate(file)
              e.target.value = ""
            }}
          />
        </div>
        {importa.isSuccess && <Avviso esito="buono">{t("backup.imported")}</Avviso>}
        {esporta.error && <Avviso esito="allarme">{esporta.error.message}</Avviso>}
        {importa.error && <Avviso esito="allarme">{importa.error.message}</Avviso>}
      </div>
    </section>
  )
}
