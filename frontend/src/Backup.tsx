import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useRef } from "react"

import { Comando, CorniceAvvio, MISURE } from "./PrimoAvvioCornice"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { Avviso } from "./componenti/Avviso"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { Scheletro } from "./componenti/Scheletro"
import { giorno, numero, orario, t } from "./i18n"
import { Sezione } from "./ImpostazioniScansioni"
import { giornoDetto } from "./Scansiona"

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
    // App gates on pending: a mount that reset the error to pending would loop (#90)
    retryOnMount: false,
  })
}

function quando(c: Conti): string {
  return c.written_at ? t("backup.when", { giorno: giorno(c.written_at), ora: orario(c.written_at) }) : ""
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
      // a backup without folders has nothing to read: the scan would only be refused
      if (stato.last?.folders) await api.POST("/api/v1/scan")
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
  const formato = useFormato()
  const conti = stato.last
  const errore = rimetti.error ?? ricomincia.error

  // tavola v82 `Primo avvio`, passo `backup`: before the steps, so no list of them
  return (
    <CorniceAvvio titolo={t("backup.found.title")} perche={conti ? `${quando(conti)}.` : undefined}>
      {conti && (
        <div className="al-avvio__centro-2" style={{ gridTemplateColumns: MISURE[formato].conti }}>
          {[
            { n: conti.answers, l: t("backup.count.answers") },
            { n: conti.sites, l: t("backup.count.sites") },
            { n: conti.folders, l: t("backup.count.folders") },
            { n: conti.instruments + conti.filters, l: t("backup.count.gear") },
          ].map((c) => (
            <div key={c.l} className="al-avvio__colonna-9">
              <span className="al-avvio__testo-8">{numero(c.n)}</span>
              <span className="al-avvio__testo-9">{c.l}</span>
            </div>
          ))}
        </div>
      )}
      <p className="al-avvio__testo-10">{t("backup.found.question")}</p>
      <div className="al-avvio__riga-5">
        <Comando
          testo={t("backup.found.restore")}
          verso="pieno"
          spento={ricomincia.isPending}
          occupato={rimetti.isPending ? t("backup.restoring") : undefined}
          onClick={() => rimetti.mutate()}
        />
        <Comando
          testo={t("backup.found.decline")}
          verso="tenue"
          spento={rimetti.isPending || ricomincia.isPending}
          onClick={() => ricomincia.mutate()}
        />
      </div>
      {errore && <Avviso tipo="blocco" formato={formato} segno="!" titolo={errore.message} />}
    </CorniceAvvio>
  )
}

/** A refusal of the file itself: said under the buttons, not a "Ripristino non riuscito". */
class Rifiuto extends Error {}

function kb(byte: number): string {
  return numero(Math.max(1, Math.round(byte / 1024)))
}

/**
 * La sezione **Backup** (tavola Impostazioni v82, `SezioneServizi`): il file delle risposte, quando
 * e' stato scritto, e i due gesti per un altro computer. L'Esporta non porta le chiavi dei servizi
 * (ADR 0017); il file accanto al database si' (Marco 16/11).
 */
export function ImpostazioniBackup() {
  const formato = useFormato()
  const cache = useQueryClient()
  const stato = useBackup()
  const scegli = useRef<HTMLInputElement>(null)
  const ultimoFile = useRef<File | null>(null)
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
        throw new Rifiuto(t("backup.notABackup"))
      }
      const { error, response } = await api.POST("/api/v1/backup/import", { body: contenuto })
      if (response.status === 422) {
        // a folder refused on this machine comes back with its path; the file itself is sound
        const percorso = (error as { detail?: { path?: unknown } } | undefined)?.detail?.path
        throw new Rifiuto(
          typeof percorso === "string" ? t("backup.folderRefused", { percorso }) : t("backup.notABackup"),
        )
      }
      if (error) throw new Error(t("backup.importFailed"))
      // the folders already here are read; only a file that brings folders has new ones to read
      if (Array.isArray(contenuto.folders) && contenuto.folders.length > 0)
        await api.POST("/api/v1/scan")
    },
    onSuccess: () => cache.invalidateQueries(),
  })
  const dati = stato.data
  const ultimo = dati?.last
  const mai = !ultimo && !dati?.unreadable
  const importaFile = (file: File) => {
    ultimoFile.current = file
    importa.mutate(file)
  }
  // the server did not answer an import: nothing changed, Riprova sends the same file again.
  // The offer of the file found (tavola "ripristino al primo avvio") is App's, before any page.
  const nonRiuscito = importa.isError && !(importa.error instanceof Rifiuto)
  const bottone = "al-bottone"

  return (
    <Sezione>
      <p className="al-imp-intro">{t("backup.intro")}</p>
      {stato.isPending && (
        <Scheletro
          formato={formato}
          testo={t("backup.loading")}
          griglia="minmax(0,1fr)"
          carte={[{ h: "200px", blocchi: [{ h: "20px", w: "220px" }, { flex: "1" }] }]}
        />
      )}
      {stato.isError && (
        <Avviso
          tipo="blocco"
          formato={formato}
          segno="!"
          titolo={t("backup.failed")}
          azione={t("settings.retry")}
          onAzione={() => void stato.refetch()}
        />
      )}
      {dati?.unreadable && (
        <Avviso
          tipo="blocco"
          formato={formato}
          segno="!"
          titolo={t("backup.unreadable.title")}
          testo={t("backup.unreadable.text", { file: dati.path })}
        />
      )}
      {nonRiuscito && (
        <Avviso
          tipo="blocco"
          formato={formato}
          segno="!"
          titolo={t("backup.notRestored.title")}
          testo={t("backup.notRestored.text")}
          azione={t("settings.retry")}
          onAzione={() => ultimoFile.current && importa.mutate(ultimoFile.current)}
        />
      )}
      {dati && (
        <section className="al-imp-carta" aria-label={t("settings.backup.sub")}>
          <div className="al-imp-riga">
            <span className="al-imp-etichetta">{t("backup.file")}</span>
            <span className="al-imp-valore">
              <span className="al-imp-percorso">{dati.path}</span>
            </span>
          </div>
          {/* a file that cannot be read has no date to say: the Avviso above says it */}
          {!dati.unreadable && (
            <div className="al-imp-riga">
              <span className="al-imp-etichetta">{t("backup.written")}</span>
              <span className="al-imp-valore">
                {ultimo?.written_at && dati.size_bytes !== null
                  ? t("backup.written.when", {
                      giorno: giornoDetto(ultimo.written_at, dati.written_day ?? undefined),
                      ora: orario(ultimo.written_at),
                      kb: kb(dati.size_bytes),
                    })
                  : t("backup.written.never")}
              </span>
            </div>
          )}
          <div className="al-imp-gesti al-imp-gesti--inizio">
            <a
              href="#"
              role="button"
              // Esporta reads the database: only a file never written leaves it off
              aria-disabled={mai || esporta.isPending ? "true" : undefined}
              onClick={gesto(() => !mai && !esporta.isPending && esporta.mutate())}
              className={`${bottone} al-bottone--pieno`}
            >
              {t("backup.export")}
            </a>
            <a
              href="#"
              role="button"
              aria-disabled={importa.isPending ? "true" : undefined}
              onClick={gesto(() => !importa.isPending && scegli.current?.click())}
              className={`${bottone} al-bottone--contorno`}
            >
              {t("backup.import")}
            </a>
            <input
              ref={scegli}
              type="file"
              accept="application/json,.json"
              hidden
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) importaFile(file)
                e.target.value = ""
              }}
            />
          </div>
          <p className="al-imp-nota">{t("backup.note")}</p>
          <span aria-live="polite">
            {importa.isSuccess && <p className="al-imp-nota">{t("backup.imported")}</p>}
            {esporta.error && <p className="al-imp-nota">{esporta.error.message}</p>}
            {importa.error instanceof Rifiuto && <p className="al-imp-nota">{importa.error.message}</p>}
          </span>
        </section>
      )}
    </Sezione>
  )
}
