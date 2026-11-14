import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { gesto } from "./componenti/gesto"
import { rifiutoDetto } from "./ModuloDelGesto"
import { nomeDelSetup } from "./misureDelSetup"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"

type Pagina = components["schemas"]["GearList"]
type Rifiuto = components["schemas"]["DeleteRefused"]
type NelSetup = components["schemas"]["PieceInRig"]

/** "a, b e c" (tavola `nomi`). */
export function inFila(nomi: string[]): string {
  if (nomi.length < 2) return nomi.join("")
  return t("gear.list.and", { a: nomi.slice(0, -1).join(", "), b: nomi.at(-1) ?? "" })
}

/** Il perche' di Elimina spento, dal rifiuto che l'API ha gia' letto (`delete_refused`). */
export function percheNo(rifiuto: Rifiuto, pagina: Pagina): string {
  const setup = inFila(
    rifiuto.rigs.flatMap((id) => {
      const r = pagina.rigs.find((x) => x.id === id)
      return r ? [nomeDelSetup(r)] : []
    }),
  )
  if (rifiuto.code === "in_rig") return t("gear.delete.inRig", { setup })
  const n = numero(rifiuto.frames)
  return setup ? t("gear.delete.inUse", { n, setup }) : t("gear.delete.inUse.noRig", { n })
}

/**
 * **Elimina** in fondo al modulo di un pezzo (tavola v82, `elimina`; contratto: solo un pezzo senza
 * frame). Spento col perche' quando l'API dice che resta; la conferma nella stessa carta, con i
 * setup da cui esce. Un rifiuto arrivato al gesto (un pezzo non ancora contato) si scrive uguale.
 */
export function EliminaDelModulo({
  nome,
  pagina,
  rifiuto,
  inSetup,
  scansione,
  salvando,
  unisci,
  elimina,
  onFatto,
  onErrore,
}: {
  nome: string
  pagina: Pagina
  rifiuto: Rifiuto | null
  inSetup: NelSetup[]
  scansione: boolean
  /** The form is saving: nothing else starts. */
  salvando: boolean
  /** The merge drop-down's id, when there is one: "Unisci a" brings it into focus. */
  unisci: string | null
  elimina: () => Promise<{ error?: unknown }>
  onFatto: () => void
  /** A refusal at the gesture: the form shows it as its own error (board `delErr`). */
  onErrore: (testo: string | null) => void
}) {
  const coda = useQueryClient()
  const [chiede, setChiede] = useState(false)
  const via = useMutation({
    mutationFn: async () => {
      const { error } = await elimina()
      if (error) throw error
    },
    onSuccess: async () => {
      await Promise.all([
        coda.invalidateQueries({ queryKey: ["gear"] }),
        coda.invalidateQueries({ queryKey: ["review"] }),
      ])
      onFatto()
    },
    onError: (e) => {
      const detto = (e as { detail?: Rifiuto } | null)?.detail
      onErrore(
        detto?.code === "in_use" || detto?.code === "in_rig"
          ? percheNo(detto, pagina)
          : rifiutoDetto(e),
      )
      setChiede(false)
    },
  })
  const spento = rifiuto !== null || scansione || salvando
  const perche = rifiuto ? percheNo(rifiuto, pagina) : scansione ? t("gear.delete.scanning") : ""
  const esce = inFila(
    inSetup
      .filter((s) => s.chosen)
      .flatMap((s) => {
        const r = pagina.rigs.find((x) => x.id === s.rig_id)
        return r ? [nomeDelSetup(r)] : []
      }),
  )
  return (
    <div className="al-c-modulo__elimina">
      {!chiede && (
        <>
          <a
            href="#"
            role="button"
            aria-disabled={spento ? "true" : undefined}
            onClick={gesto(() => {
              if (spento) return
              onErrore(null)
              setChiede(true)
            })}
            className={
              spento
                ? "al-c-modulo__elimina-l al-c-modulo__elimina-l--spento"
                : "al-c-modulo__elimina-l"
            }
          >
            {t("gear.delete")}
          </a>
          {perche && (
            <div className="al-c-modulo__elimina-nota">
              <span className="al-c-modulo__blocco-7">{perche}</span>
              {rifiuto?.code === "in_use" && unisci && (
                <a
                  href={`#${unisci}`}
                  role="button"
                  onClick={gesto(() => document.getElementById(unisci)?.focus())}
                  className="al-bottone al-bottone--contorno"
                >
                  {t("gear.write.sameAs")}
                </a>
              )}
            </div>
          )}
        </>
      )}
      {chiede && (
        <div
          className="al-c-modulo__conferma"
          role="alertdialog"
          aria-label={t("gear.delete.ask", { nome })}
        >
          <span className="al-c-modulo__conferma-segno" aria-hidden="true">
            ✕{/* glifo-ok: segno della tavola */}
          </span>
          <span className="al-c-modulo__conferma-testo">
            <b>{t("gear.delete.ask", { nome })}</b>
            {esce && (
              <span className="al-c-modulo__conferma-sub">
                {t("gear.delete.leaves", { setup: esce })}
              </span>
            )}
          </span>
          <span className="al-c-modulo__conferma-azioni">
            <a
              href="#"
              role="button"
              aria-busy={via.isPending ? "true" : undefined}
              onClick={gesto(() => {
                if (!via.isPending) via.mutate()
              })}
              className="al-c-modulo__conferma-si"
            >
              {t(via.isPending ? "gear.delete.busy" : "gear.delete")}
            </a>
            <a
              href="#"
              role="button"
              onClick={gesto(() => {
                if (!via.isPending) setChiede(false)
              })}
              className="al-bottone al-bottone--contorno"
            >
              {t("ui.form.cancel")}
            </a>
          </span>
        </div>
      )}
    </div>
  )
}
