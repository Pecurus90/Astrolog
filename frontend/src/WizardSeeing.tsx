import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"

import { Avviso, type SegnoAvviso } from "./componenti/Avviso"
import type { Formato } from "./componenti/Tema"
import { METEOBLUE } from "./ImpostazioniServizi"
import { CampoAvvio, Comando } from "./PrimoAvvioCornice"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, t } from "./i18n"
import { usePienoDelPasso } from "./pienoDelPasso"
import { usePreferenze } from "./preferenze"

type Esito = components["schemas"]["MeteoblueKeyOut"]["status"]

// tavola `EK`: the backend sends the code, here only the sentence and its sign
const ESITI: Record<Esito, { frase: Chiave; segno: SegnoAvviso }> = {
  ok: { frase: "meteoblue.saved", segno: "\u2713" },
  removed: { frase: "meteoblue.removed", segno: "?" },
  refused: { frase: "meteoblue.refused", segno: "!" },
  limited: { frase: "meteoblue.limited", segno: "!" },
  unreachable: { frase: "meteoblue.unreachable", segno: "!" },
  bad_answer: { frase: "meteoblue.badAnswer", segno: "!" },
}

/**
 * The seeing step (tavola v82 `Primo avvio`, `V.seeing`, `K`): the Meteoblue key is tried on the
 * account and kept only if it holds. It never comes back whole: its last four characters say
 * whether it is the one you put. Removing it is a gesture, and the seeing goes with it.
 */
export function WizardSeeing({
  formato,
  onOffre,
  onPrimaDiAvanti,
}: {
  formato: Formato
  onOffre: (offre: boolean) => void
  /** Avanti with a key written: verify and save first; `false` stays on the step. */
  onPrimaDiAvanti?: (prima: (() => Promise<boolean>) | null) => void
}) {
  const cache = useQueryClient()
  const impostazioni = usePreferenze()
  const [chiave, setChiave] = useState("")
  const salva = useMutation({
    mutationFn: async (quale: string) => {
      const { data, error } = await api.PUT("/api/v1/weather/meteoblue-key", {
        body: { key: quale },
      })
      if (error) throw new Error(t("meteoblue.failed"))
      return data.status
    },
    onSuccess: async (esito) => {
      if (esito === "ok" || esito === "removed" || esito === "limited") setChiave("")
      await cache.invalidateQueries({ queryKey: ["settings"] })
      await cache.invalidateQueries({ queryKey: ["weather"] })
    },
  })
  const salvata = impostazioni.data?.values["meteoblue_key"] ?? null
  const scritta = chiave.trim() !== ""
  // tavola `cmd`: the step's command stays full until a key is saved and the field is empty
  const proprio = !(salvata && !scritta)
  usePienoDelPasso(onOffre, proprio)
  const esito = salva.data ? ESITI[salva.data] : undefined
  const manda = () => {
    if (scritta && !salva.isPending) salva.mutate(chiave.trim())
  }
  const { mutateAsync } = salva
  useEffect(() => {
    if (!onPrimaDiAvanti) return
    const scritto = chiave.trim()
    onPrimaDiAvanti(
      scritto
        ? () =>
            mutateAsync(scritto).then(
              (e) => e === "ok" || e === "limited",
              () => false,
            )
        : null,
    )
    return () => onPrimaDiAvanti(null)
  }, [chiave, mutateAsync, onPrimaDiAvanti])

  return (
    <div className="al-avvio__colonna-21">
      <Avviso
        tipo="riga"
        formato={formato}
        segno={salvata ? "\u2713" : "?"}
        titolo={salvata ? t("meteoblue.current", { fine: String(salvata) }) : t("meteoblue.none")}
      />
      <a className="al-avvio__riga-15" href={METEOBLUE} target="_blank" rel="noopener">
        {t("wizard.services.where")}
      </a>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          manda()
        }}
      >
        <CampoAvvio
          id="pa-key"
          etichetta={t("meteoblue.label")}
          valore={chiave}
          onScrivi={setChiave}
          dopo={
            <Comando
              testo={t("meteoblue.save")}
              verso={proprio ? "pieno" : "tenue"}
              spento={!scritta}
              occupato={salva.isPending ? t("wizard.checking") : undefined}
              onClick={manda}
            />
          }
        />
      </form>
      {salvata && (
        <div className="al-avvio__riga-11">
          <Comando
            testo={t("meteoblue.remove")}
            verso="contorno"
            spento={salva.isPending}
            onClick={() => salva.mutate("")}
          />
        </div>
      )}
      {esito && (
        <Avviso tipo="riga" formato={formato} segno={esito.segno} titolo={t(esito.frase)} />
      )}
      {salva.error && (
        <Avviso tipo="riga" formato={formato} segno="!" titolo={salva.error.message} />
      )}
    </div>
  )
}
