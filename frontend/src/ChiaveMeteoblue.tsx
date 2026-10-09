import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Campo } from "./Campo"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, t } from "./i18n"
import { usePreferenze } from "./preferenze"
import { CAMPO_E_BOTTONE } from "./inLinea"

// Dove si chiede la chiave: un indirizzo, non un testo da tradurre.
const DOVE_SI_CHIEDE = "https://www.meteoblue.com/en/weather-api"

// Com'e' andata, come si dice: il backend manda il codice, qui c'e' solo la frase.
type Esito = components["schemas"]["MeteoblueKeyOut"]["status"]
const ESITI: Record<Esito, { frase: Chiave; bene: boolean }> = {
  ok: { frase: "meteoblue.saved", bene: true },
  removed: { frase: "meteoblue.removed", bene: true },
  refused: { frase: "meteoblue.refused", bene: false },
  unreachable: { frase: "meteoblue.unreachable", bene: false },
  bad_answer: { frase: "meteoblue.badAnswer", bene: false },
}

/**
 * La chiave Meteoblue: la scrivi, l'app la prova sul tuo conto, e solo se vale la tiene.
 *
 * Sta in un modulo suo perche' la chiedono in due -- il primo avvio, come passo facoltativo, e la
 * sezione *Servizi* delle Impostazioni.
 *
 * - **La chiave non torna mai indietro intera**: l'app ne mostra le ultime quattro cifre, che
 *   bastano a dire se e' quella che hai messo tu.
 * - **Una chiave che il conto rifiuta non si salva**, e il perche' si legge qui, dove l'hai scritta.
 * - **Toglierla e' un gesto**, e il seeing sparisce: viene solo da Meteoblue.
 */
export function ChiaveMeteoblue({ id }: { id: string }) {
  const cache = useQueryClient()
  const impostazioni = usePreferenze()
  const [chiave, setChiave] = useState("")
  const salva = useMutation({
    mutationFn: async (quale: string) => {
      const { data, error } = await api.PUT("/api/v1/weather/meteoblue-key", { body: { key: quale } })
      if (error) throw new Error(t("meteoblue.failed"))
      return data.status
    },
    onSuccess: async (esito) => {
      if (esito === "ok" || esito === "removed") setChiave("")
      await cache.invalidateQueries({ queryKey: ["settings"] })
      await cache.invalidateQueries({ queryKey: ["weather"] })
    },
  })
  const salvata = impostazioni.data?.values["meteoblue_key"] ?? null
  const esito = salva.data ? ESITI[salva.data] : undefined

  return (
    <>
      <p>
        {salvata ? t("meteoblue.current", { fine: salvata }) : t("meteoblue.none")}{" "}
        <a href={DOVE_SI_CHIEDE}>{t("meteoblue.where")}</a>
      </p>
      <div style={CAMPO_E_BOTTONE}>
        <Campo id={id} etichetta={t("meteoblue.label")} aspetta={salva.isPending}>
          <input
            className="as-campo-modulo__input"
            id={id}
            autoComplete="off"
            spellCheck={false}
            value={chiave}
            onChange={(e) => setChiave(e.target.value)}
          />
        </Campo>
        <Bottone
          verso="primario"
          onClick={() => salva.mutate(chiave)}
          disabled={salva.isPending || chiave.trim() === ""}
        >
          {t("meteoblue.save")}
        </Bottone>
      </div>
      {salvata && (
        <Bottone verso="nudo" onClick={() => salva.mutate("")} disabled={salva.isPending}>
          {t("meteoblue.remove")}
        </Bottone>
      )}
      {esito && <Avviso esito={esito.bene ? "buono" : "attesa"}>{t(esito.frase)}</Avviso>}
      {salva.error && <Avviso esito="allarme">{salva.error.message}</Avviso>}
    </>
  )
}
