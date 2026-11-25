import { useQuery } from "@tanstack/react-query"
import { useState } from "react"

import { Avviso, type SegnoAvviso } from "./componenti/Avviso"
import { Carta } from "./componenti/Carta"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { Scheletro } from "./componenti/Scheletro"
import { Tema, type Formato } from "./componenti/Tema"
import { api } from "./api/client"
import { motivo } from "./api/motivo"
import type { components } from "./api/schema"
import {
  esitoDellaSovrapposizione,
  esitoDelloSpostamento,
  RIFIUTI_SPOSTA,
  sposta,
  useCartelle,
} from "./cartelle"
import { CartaScansione } from "./ImpostazioniScansione"
import { numero, t } from "./i18n"
import { useRadiceDati } from "./radiceDati"

type Cartella = components["schemas"]["FolderOut"]
type Esito = { segno: SegnoAvviso; titolo: string; testo?: string; azione?: string; onAzione?: () => void }

/**
 * **Cartelle e scansione** (tavola Impostazioni v82, 108-129 and 307-330): the folders with Sposta
 * and Togli in their row, Aggiungi una cartella with Verifica, and the Scansione card.
 *
 * - **Where the files are is not a choice**: the app knows it (`data_root`), so the board's
 *   "Su questo computer / Sul NAS" is out; on a NAS the folders are browsed.
 * - **Togli is a retirement**: the frames stay, as the confirmation says.
 */
export function Cartelle() {
  const formato = useFormato()
  const tel = formato === "telefono"
  const cartelle = useCartelle("settings.folders.failed")
  let corpo
  if (cartelle.elenco.isPending) {
    corpo = (
      <Scheletro
        formato={formato}
        testo={t("settings.folders.loading")}
        griglia={tel ? "minmax(0,1fr)" : "repeat(12,minmax(0,1fr))"}
        carte={[
          { ...(tel ? {} : { col: "span 8" }), h: "420px", blocchi: [{ h: "24px", w: "160px" }, { flex: "1" }] },
          { ...(tel ? {} : { col: "span 4" }), h: "220px", blocchi: [{ h: "20px", w: "120px" }, { flex: "1" }] },
        ]}
        gap={tel ? "12px" : "16px"}
      />
    )
  } else if (cartelle.elenco.isError) {
    corpo = (
      <Avviso
        tipo="pagina"
        formato={formato}
        segno="!"
        titolo={t("settings.folders.failed")}
        azione={t("settings.retry")}
        onAzione={() => void cartelle.elenco.refetch()}
      />
    )
  } else {
    corpo = (
      <>
        <CartaCartelle formato={formato} cartelle={cartelle} />
        <CartaScansione formato={formato} />
      </>
    )
  }
  return (
    <Tema>
      <div className={tel ? "al-imp__colonna-18" : "al-imp__griglia-2"}>{corpo}</div>
    </Tema>
  )
}

type Stato = ReturnType<typeof useCartelle>

function CartaCartelle({ formato, cartelle }: { formato: Formato; cartelle: Stato }) {
  const tel = formato === "telefono"
  const elenco = cartelle.elenco.data?.items ?? []
  // one row open at a time: its confirmation or its new path
  const [aperta, setAperta] = useState<{ id: number; cosa: "togli" | "sposta" } | null>(null)
  return (
    <Carta
      formato={formato}
      colonne={8}
      ritardo={0}
      padding={tel ? "20px" : "24px 28px"}
      gap={0}
      etichetta={t("settings.folders.title")}
    >
      <span className="al-imp__riga-9">
        <span className={tel ? "al-imp__testo-27" : "al-imp__testo-3"}>
          {t("settings.folders.title")}
        </span>
        <span className={tel ? "al-imp__testo-8" : "al-imp__testo-5"}>
          {t("settings.folders.count", { n: numero(elenco.length) })}
        </span>
      </span>
      {elenco.map((c) => (
        <Riga
          key={c.id}
          formato={formato}
          cartella={c}
          aperta={aperta?.id === c.id ? aperta.cosa : null}
          onApri={(cosa) =>
            setAperta(aperta?.id === c.id && aperta.cosa === cosa ? null : { id: c.id, cosa })
          }
          onFatto={() => {
            setAperta(null)
            cartelle.rileggi()
          }}
        />
      ))}
      {elenco.length === 0 && <span className="al-imp__blocco-8">{t("settings.folders.empty")}</span>}
      <Aggiungi formato={formato} cartelle={cartelle} />
    </Carta>
  )
}

function Riga({
  formato,
  cartella: c,
  aperta,
  onApri,
  onFatto,
}: {
  formato: Formato
  cartella: Cartella
  aperta: "togli" | "sposta" | null
  onApri: (cosa: "togli" | "sposta") => void
  onFatto: () => void
}) {
  const [nonTolta, setNonTolta] = useState(false)
  const frame = t("settings.folders.frames", { n: numero(c.frames) })
  const togli = async () => {
    const { error } = await api.DELETE("/api/v1/folders/{folder_id}", {
      params: { path: { folder_id: c.id } },
    })
    setNonTolta(Boolean(error))
    if (!error) onFatto()
  }
  return (
    <div>
      <div className="al-imp__riga-10">
        <span className={c.reachable ? "al-imp__tondo-2" : "al-imp__tondo-1"} aria-hidden="true">
          {c.reachable ? "✓" : "!" /* glifo-ok: segni della tavola */}
        </span>
        <span className="al-imp__colonna-6">
          <b className="al-imp__testo-14">{c.root_path}</b>
          <span className="al-imp__testo-8">
            {c.reachable
              ? frame
              : t("settings.folders.unreachable.line", {
                  frame: t("settings.folders.frames.kept", { n: numero(c.frames) }),
                })}
          </span>
        </span>
        <span className="al-imp__sito-gesti">
          <a
            href="#"
          role="button"
            onClick={gesto(() => onApri("sposta"))}
            aria-expanded={aperta === "sposta"}
            className="al-bottone al-bottone--testo al-bottone--piccolo"
          >
            {t("settings.folders.move")}
          </a>
          <a
            href="#"
          role="button"
            onClick={gesto(() => onApri("togli"))}
            aria-expanded={aperta === "togli"}
            className="al-bottone al-bottone--contorno al-bottone--piccolo al-imp__blocco-7"
          >
            {t("settings.folders.remove")}
          </a>
        </span>
      </div>
      {aperta === "togli" && (
        <div
          className="al-imp__pannello al-imp__cart-pannello"
          role="alertdialog"
          aria-label={t("settings.folders.remove")}
        >
          <span>{t("settings.folders.confirm", { percorso: c.root_path })}</span>
          <span className="al-imp__sito-gesti">
            <a
              href="#"
          role="button"
              onClick={gesto(() => void togli())}
              className="al-bottone al-bottone--pericolo al-bottone--piccolo"
            >
              {t("settings.folders.stop")}
            </a>
            <a
              href="#"
          role="button"
              onClick={gesto(() => onApri("togli"))}
              className="al-bottone al-bottone--testo al-bottone--piccolo"
            >
              {t("settings.folders.cancel")}
            </a>
          </span>
          {nonTolta && (
            <span className="al-imp__testo-20" aria-live="polite">
              {`✕ ${t("settings.folders.removeFailed")}` /* glifo-ok: segno della tavola */}
            </span>
          )}
        </div>
      )}
      {aperta === "sposta" && (
        <Sposta formato={formato} cartella={c} onFatto={onFatto} onAnnulla={() => onApri("sposta")} />
      )}
    </div>
  )
}

/** The new path of a folder whose files moved: Verifica asks the backend without writing, Usa
 *  questo percorso moves. */
function Sposta({
  formato,
  cartella: c,
  onFatto,
  onAnnulla,
}: {
  formato: Formato
  cartella: Cartella
  onFatto: () => void
  onAnnulla: () => void
}) {
  const [v, setV] = useState("")
  const [inCorso, setInCorso] = useState(false)
  const [esito, setEsito] = useState<Esito | null>(null)
  const usa = async (dove: string) => {
    setInCorso(true)
    const perche = await sposta(c.id, dove)
    setInCorso(false)
    if (perche) setEsito({ segno: "!", titolo: t(perche) })
    else onFatto()
  }
  const verifica = async () => {
    const dove = v.trim()
    if (!dove || inCorso) return
    setInCorso(true)
    const { data, error } = await api.POST("/api/v1/folders/{folder_id}/move/check", {
      params: { path: { folder_id: c.id } },
      body: { root_path: dove },
    })
    setInCorso(false)
    setEsito(
      data
        ? {
            segno: "\u2713",
            titolo: t("settings.folders.move.same", { percorso: data.root_path }),
            testo: t("settings.folders.move.keeps"),
            azione: t("folders.move.here"),
            onAzione: () => void usa(data.root_path),
          }
        : { segno: "!", titolo: t(motivo(error, RIFIUTI_SPOSTA, "folders.move.failed")) },
    )
  }
  return (
    <div className="al-imp__pannello al-imp__cart-pannello">
      <span style={{ overflowWrap: "anywhere" }}>
        {t("settings.folders.move.what", { percorso: c.root_path })}
      </span>
      <form
        className="al-imp__riga-4"
        onSubmit={(e) => {
          e.preventDefault()
          void verifica()
        }}
      >
        <input
          value={v}
          onChange={(e) => {
            setV(e.target.value)
            setEsito(null)
          }}
          aria-label={t("settings.folders.move.label")}
          placeholder={t("settings.folders.move.placeholder")}
          spellCheck={false}
          className="al-campo al-imp__blocco-9"
        />
        <a
          href="#"
          role="button"
          onClick={gesto(() => void verifica())}
          className="al-bottone al-bottone--pieno al-bottone--piccolo"
        >
          {t(inCorso ? "settings.folders.checking" : "settings.folders.look")}
        </a>
        <a
          href="#"
          role="button"
          onClick={gesto(onAnnulla)}
          className="al-bottone al-bottone--testo al-bottone--piccolo"
        >
          {t("settings.folders.cancel")}
        </a>
      </form>
      {esito && <Avviso tipo="blocco" formato={formato} {...esito} />}
    </div>
  )
}

/** Aggiungi una cartella: on a NAS browse the data root, else write the path; Verifica looks in
 *  without writing, the outcome carries the gesture that registers. */
function Aggiungi({ formato, cartelle }: { formato: Formato; cartelle: Stato }) {
  const tel = formato === "telefono"
  const radice = useRadiceDati()
  const [perc, setPerc] = useState("")
  const [guardando, setGuardando] = useState(false)
  const [guardato, setGuardato] = useState("")
  const pc = perc.trim()
  const guarda = async (dove: string) => {
    if (!dove || guardando) return
    setPerc(dove)
    setGuardando(true)
    await cartelle.guarda(dove)
    setGuardato(dove)
    setGuardando(false)
  }
  const fatto = (riuscito: boolean) => {
    if (riuscito) setPerc("")
  }
  const esito = guardato === pc ? esitoDellaSonda(cartelle, pc, fatto) : null
  const verifica = (
    <a
      className={tel ? "al-imp__riga-37" : "al-imp__riga-5"}
      href="#"
          role="button"
      onClick={gesto(() => void guarda(pc))}
      aria-disabled={pc ? "false" : "true"}
      style={{
        background: pc && !esito ? "var(--scelta)" : "var(--carta-2)",
        color: pc && !esito ? "var(--scelta-testo)" : "var(--tenue)",
      }}
    >
      {t(guardando ? "settings.folders.checking" : "settings.folders.look")}
    </a>
  )
  const campo = (
    <input
      value={perc}
      onChange={(e) => setPerc(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === "Enter") void guarda(pc)
      }}
      aria-label={t("settings.folders.label")}
      placeholder={radice ?? t("settings.folders.placeholder")}
      spellCheck={false}
      className={tel ? "al-campo" : "al-campo al-imp__blocco-9"}
    />
  )
  return (
    <div className={tel ? "al-imp__colonna-22" : "al-imp__colonna-7"}>
      <span className={tel ? "al-imp__testo-23" : "al-imp__testo-15"}>
        {t("settings.folders.add.title")}
      </span>
      {radice !== null && <Sfoglia radice={radice} onScegli={(d) => void guarda(d)} />}
      {tel ? (
        <>
          {campo}
          {verifica}
        </>
      ) : (
        <span className="al-imp__riga-4">
          {campo}
          {verifica}
        </span>
      )}
      <span className="al-imp__testo-8">
        {t(radice === null ? "settings.folders.help" : "settings.folders.help.nas")}
      </span>
      {esito && <Avviso tipo="blocco" formato={formato} {...esito} />}
    </div>
  )
}

/** What the probe saw, as the board's outcome: found, partial count, unreachable, or the files of a
 *  registered folder that moved here. A refused registration says why. */
function esitoDellaSonda(
  c: Stato,
  percorso: string,
  fatto: (riuscito: boolean) => void,
): Esito | null {
  if (c.rotto === "registrata") {
    return {
      segno: "!",
      titolo: t("folders.move.foundTitle"),
      testo: t("settings.folders.already", { percorso }),
    }
  }
  if (c.rotto) {
    return {
      segno: "!",
      titolo: t(c.rotto === "guarda" ? "settings.folders.lookFailed" : "settings.folders.addFailed"),
    }
  }
  const v = c.vista
  if (!v) return null
  if (!v.reachable) {
    return {
      segno: "!",
      titolo: t("settings.folders.unreachableTitle"),
      testo: t("settings.folders.unreachableHelp"),
    }
  }
  const sovrapposta = esitoDellaSovrapposizione(c, fatto)
  if (sovrapposta) return sovrapposta
  const spostamento = esitoDelloSpostamento(c, fatto)
  if (spostamento) return spostamento
  const parziale = v.complete === false
  const n = numero(v.fits_count ?? 0)
  return {
    segno: "\u2713",
    titolo: t(parziale ? "settings.folders.atLeastTitle" : "settings.folders.foundTitle"),
    testo: parziale
      ? t("settings.folders.atLeast", { n })
      : t("settings.folders.found.where", { file: t("settings.folders.found", { n }), percorso }),
    azione: t("settings.folders.add"),
    // one registration: a second click would come back 409 on a write that went through
    onAzione: () => {
      if (!c.inCorso) void c.aggiungi().then(fatto)
    },
  }
}

/** The NAS's folders under the data root: where you are, up, the subfolders, Seleziona. */
function Sfoglia({ radice, onScegli }: { radice: string; onScegli: (dove: string) => void }) {
  const [qui, setQui] = useState<string | undefined>(undefined)
  const sfoglia = useQuery({
    queryKey: ["browse", qui ?? radice],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/folders/browse", {
        params: { query: qui === undefined ? {} : { path: qui } },
      })
      if (error) throw new Error(t("settings.folders.lookFailed"))
      return data
    },
    retry: false,
  })
  // where you are is what was clicked, not the answer still on its way
  const dove = qui ?? radice
  const su = sfoglia.data?.path === dove ? sfoglia.data.parent : null
  const sotto = sfoglia.data?.path === dove ? sfoglia.data.folders : []
  return (
    <div className="al-imp__nas">
      <span className="al-imp__riga-11">
        <span className="al-imp__testo-5">
          {t("settings.folders.nas.here")} <b className="al-imp__testo-14">{dove}</b>
        </span>
        {su && (
          <a
            href="#"
          role="button"
            onClick={gesto(() => setQui(su))}
            className="al-bottone al-bottone--testo al-bottone--piccolo"
          >
            {t("settings.folders.nas.up")}
          </a>
        )}
      </span>
      {sotto.map((d) => (
        <a key={d.path} href="#" role="button" onClick={gesto(() => setQui(d.path))} className="al-imp__nas-voce">
          <span>{d.name}</span>
          <span aria-hidden="true">{"›" /* glifo-ok: freccia della tavola */}</span>
        </a>
      ))}
      {sfoglia.isSuccess && sotto.length === 0 && (
        <span className="al-imp__testo-5">{t("settings.folders.nas.none")}</span>
      )}
      {sfoglia.isError && <span className="al-imp__testo-20" aria-live="polite">{sfoglia.error.message}</span>}
      <a
        href="#"
          role="button"
        onClick={gesto(() => onScegli(dove))}
        className="al-bottone al-bottone--contorno al-bottone--piccolo al-imp__blocco-10"
      >
        {t("settings.folders.nas.select")}
      </a>
    </div>
  )
}
