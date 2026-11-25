import { useQuery } from "@tanstack/react-query"
import { useEffect, useState } from "react"

import { Avviso } from "./componenti/Avviso"
import { gesto } from "./componenti/gesto"
import type { Formato } from "./componenti/Tema"
import { CampoAvvio, Comando, segno } from "./PrimoAvvioCornice"
import { api } from "./api/client"
import type { components } from "./api/schema"
import {
  type EsitoSonda as Esito,
  esitoDellaSovrapposizione,
  esitoDelloSpostamento,
  useCartelle,
} from "./cartelle"
import { numero, t } from "./i18n"
import { usePienoDelPasso } from "./pienoDelPasso"
import { useRadiceDati } from "./radiceDati"

type Probe = components["schemas"]["ProbeOut"]
type Cartelle = ReturnType<typeof useCartelle>

/** How many FITS the probe saw, or its floor when the count stopped at its time limit. */
function quanti(v: Probe): string {
  const n = numero(v.fits_count ?? 0)
  return v.complete === false
    ? t("wizard.folders.atLeast.short", { n })
    : t("wizard.folders.found", { n })
}

/** The probe's outcome (tavola `EC`): found, partial count, unreachable, inside or holding listed
 *  folders, the files of a registered folder that moved here; a refused registration says why.
 *  The command that registers sits in it. */
function esitoDellaSonda(
  c: Cartelle,
  onAggiunta: (v: Probe) => void,
  onSpostata: () => void,
): Esito | null {
  if (c.rotto === "registrata")
    return {
      segno: "!",
      titolo: t("folders.move.foundTitle"),
      testo: t("settings.folders.already", { percorso: c.vista?.root_path ?? "" }),
    }
  if (c.rotto)
    return {
      segno: "!",
      titolo: t(c.rotto === "guarda" ? "wizard.folders.lookFailed" : "wizard.folders.failed"),
    }
  const v = c.vista
  if (!v) return null
  if (!v.reachable)
    return {
      segno: "!",
      titolo: t("wizard.folders.unreachableTitle"),
      testo: t("wizard.folders.unreachableHelp"),
    }
  const sovrapposta = esitoDellaSovrapposizione(c, (ok) => ok && onAggiunta(v))
  if (sovrapposta) return sovrapposta
  const spostamento = esitoDelloSpostamento(c, (ok) => ok && onSpostata())
  if (spostamento) return spostamento
  const parziale = v.complete === false
  return {
    segno: "\u2713",
    titolo: t(parziale ? "wizard.folders.atLeastTitle" : "wizard.folders.foundTitle"),
    testo: parziale
      ? t("wizard.folders.atLeast", { n: numero(v.fits_count ?? 0) })
      : t("wizard.folders.found.where", { file: quanti(v), percorso: v.root_path }),
    azione: t("wizard.folders.add"),
    // one registration: a second click would come back 409 on a write that went through
    onAzione: () => {
      if (!c.inCorso) void c.aggiungi().then((ok) => ok && onAggiunta(v))
    },
  }
}

/** The NAS's folders under the data root (tavola `V.nas`): where you are, Seleziona cartella,
 *  up, back to the data root, the subfolders with Apri. Where you are is what was clicked, not
 *  the answer still on its way: falling back to it, Seleziona would register the folder before. */
function Sfoglia({
  radice,
  qui,
  setQui,
  pende,
  verifica,
  onSeleziona,
  onCaduto,
}: {
  radice: string
  /** Where you are; `undefined` is the data root. Held by the step: a list that fails below
   *  the root keeps the way back in its notice. */
  qui: string | undefined
  setQui: (dove: string | undefined) => void
  pende: boolean
  verifica: boolean
  onSeleziona: (dove: string) => void
  onCaduto: (caduto: boolean) => void
}) {
  const dove = qui ?? radice
  const sfoglia = useQuery({
    queryKey: ["browse", dove],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/folders/browse", {
        params: { query: qui === undefined ? {} : { path: qui } },
      })
      if (error) throw new Error(t("wizard.folders.browseFailedTitle"))
      return data
    },
    retry: false,
  })
  const caduto = sfoglia.isError
  useEffect(() => onCaduto(caduto), [caduto, onCaduto])
  if (caduto) return null
  const pronto = sfoglia.data?.path === dove
  const su = pronto ? sfoglia.data?.parent : null
  const sotto = pronto ? (sfoglia.data?.folders ?? []) : []
  return (
    <div className="al-avvio__colonna-18">
      <span className="al-avvio__testo-17">{t("wizard.folders.choose")}</span>
      <div className="al-avvio__colonna-19">
        <span className="al-avvio__testo-9">{t("wizard.folders.here")}</span>
        <span className="al-avvio__testo-18">{dove}</span>
      </div>
      <div className="al-avvio__riga-12">
        <Comando
          testo={t("wizard.folders.useThis")}
          verso={pende ? "rovescio" : "pieno"}
          spento={!pronto}
          occupato={verifica ? t("wizard.checking") : undefined}
          onClick={() => onSeleziona(dove)}
        />
        <Comando
          testo={t("wizard.folders.up")}
          verso="rovescio"
          spento={!su}
          onClick={() => su && setQui(su)}
        />
        <Comando
          testo={t("wizard.folders.backToRoot")}
          verso="rovescio"
          spento={dove === radice}
          onClick={() => setQui(undefined)}
        />
      </div>
      <ul className="al-avvio__colonna-20" aria-label={t("wizard.folders.subfolders")}>
        {sotto.map((d) => (
          <li key={d.path} className="al-avvio__riga-13">
            <span className="al-avvio__blocco-7">{d.name}</span>
            <a
              href="#"
              role="button"
              aria-label={t("wizard.folders.openOne", { nome: d.name })}
              onClick={gesto(() => setQui(d.path))}
              className="al-bottone al-bottone--tenue al-avvio__blocco-4"
            >
              {t("wizard.folders.open")}
            </a>
          </li>
        ))}
        {sfoglia.isSuccess && pronto && sotto.length === 0 && (
          <li className="al-avvio__blocco-8">{t("wizard.folders.empty")}</li>
        )}
      </ul>
    </div>
  )
}

/**
 * The folders step (tavola v82 `Primo avvio`, `V.pc`, `V.nas`, `C`). **As many folders as you
 * want**: adding one does not close the first run, Fine does. Where the app has a data root (the
 * NAS in Docker) folders are chosen, since the path inside the container cannot be guessed; on
 * the computer the path is written. Looked at before registering: the probe counts without writing.
 */
export function WizardFolders({
  formato,
  onOffre,
}: {
  formato: Formato
  /** The step's own command is the full one (tavola `cmd`): Avanti steps down. */
  onOffre: (offre: boolean) => void
}) {
  const [path, setPath] = useState("")
  const [verifica, setVerifica] = useState(false)
  const [nasCaduto, setNasCaduto] = useState(false)
  const [qui, setQui] = useState<string | undefined>(undefined)
  // what the probe counted, per registered path: the database counts frames only after the scan
  const [contati, setContati] = useState<Record<string, string>>({})
  const cartelle = useCartelle("wizard.folders.failed")
  const radice = useRadiceDati()
  const nas = radice !== null
  const conPercorso = !nas || nasCaduto

  const guarda = async (quale: string) => {
    if (!quale.trim() || verifica) return
    setVerifica(true)
    await cartelle.guarda(quale.trim()).catch(() => undefined)
    setVerifica(false)
  }
  const esito = esitoDellaSonda(cartelle, (v) => {
    setPath("")
    setContati((c) => ({ ...c, [v.root_path]: quanti(v) }))
  }, () => setPath(""))
  const pende = esito?.azione !== undefined
  const aggiunte = cartelle.elenco.data?.items ?? []
  // tavola `cmd`: Avanti is full only with folders added and nothing waiting to be added
  const fermo = aggiunte.length > 0 && !pende && (!conPercorso || !path.trim())
  usePienoDelPasso(onOffre, !fermo)

  return (
    <>
      {nas && nasCaduto && (
        <Avviso
          tipo="blocco"
          formato={formato}
          segno="?"
          titolo={t("wizard.folders.browseFailedTitle")}
          testo={t("wizard.folders.browseFailed")}
          {...(qui === undefined
            ? {}
            : { azione: t("wizard.folders.backToRoot"), onAzione: () => setQui(undefined) })}
        />
      )}
      {conPercorso && (
        <form
          onSubmit={(e) => {
            e.preventDefault()
            void guarda(path)
          }}
        >
          <CampoAvvio
            id="pa-perc"
            etichetta={t("wizard.folders.label")}
            valore={path}
            onScrivi={setPath}
            aiuto={nas ? t("wizard.folders.pathHelp") : ""}
            dopo={
              <Comando
                testo={t("wizard.folders.look")}
                verso={pende ? "tenue" : "pieno"}
                spento={!path.trim()}
                occupato={verifica ? t("wizard.checking") : undefined}
                onClick={() => void guarda(path)}
              />
            }
          />
        </form>
      )}
      {nas && radice !== null && (
        <Sfoglia
          radice={radice}
          qui={qui}
          setQui={setQui}
          pende={pende}
          verifica={verifica}
          onSeleziona={(d) => void guarda(d)}
          onCaduto={setNasCaduto}
        />
      )}
      {esito && <Avviso tipo="blocco" formato={formato} {...esito} />}
      {aggiunte.length > 0 && (
        <div className="al-avvio__colonna-15">
          <span className="al-avvio__testo-13">{t("wizard.folders.added")}</span>
          <ul className="al-avvio__colonna-13">
            {aggiunte.map((c) => {
              const s = segno("fatto", 0)
              const n =
                contati[c.root_path] ??
                (c.frames > 0 ? t("wizard.folders.found", { n: numero(c.frames) }) : "")
              return (
                <li key={c.id} className="al-avvio__riga-14">
                  <span className="al-avvio__tondo-4" aria-hidden="true" style={s.stile}>
                    {s.testo}
                  </span>
                  <span className="al-avvio__colonna-19">
                    <span className="al-avvio__testo-19">{c.root_path}</span>
                    {n && <span className="al-avvio__testo-9">{n}</span>}
                  </span>
                </li>
              )
            })}
          </ul>
        </div>
      )}
    </>
  )
}
