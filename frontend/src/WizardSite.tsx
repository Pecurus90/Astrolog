import { useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { api } from "./api/client"
import { t } from "./i18n"
import { CampiDelSito, CercaIlPosto, SceltaDelCielo, useCampiDelSito } from "./sito"

/**
 * Il secondo passo: da dove osservi. E' quello che fa nascere le notti.
 *
 * I campi, la ricerca del posto e la scala del cielo stanno in `sito.tsx`, che li divide con la
 * sezione *Il sito* delle Impostazioni. Qui resta cio' che e' del **passo**:
 *
 * - **Il primo sito e' quello di casa**: e' l'unico che c'e', e senza uno di casa le notti non
 *   nascono.
 * - **Una scrittura fallita non fa avanzare**: si resta qui, dove il problema si puo' ancora
 *   risolvere.
 */
export function WizardSite({ onSaved }: { onSaved: () => void }) {
  const campi = useCampiDelSito()
  const [rotto, setRotto] = useState(false)
  const [salvando, setSalvando] = useState(false)

  const salva = async () => {
    if (!campi.valido || salvando) return
    setSalvando(true)
    const { error } = await api.POST("/api/v1/sites", {
      body: { ...campi.corpo(), is_default: true },
    })
    setSalvando(false)
    setRotto(Boolean(error))
    if (!error) onSaved()
  }

  return (
    <>
      <p className="as-soprattitolo">{t("wizard.site.searchGroup")}</p>
      <CercaIlPosto
        aMano={() => document.getElementById("wizard-name")?.focus()}
        id="wizard-place"
        onScegli={campi.prendiDa}
      />

      <p className="as-soprattitolo">{t("wizard.site.manual")}</p>
      <p className="as-carta__domanda">{t("wizard.site.manualWhy")}</p>
      <CampiDelSito campi={campi} id="wizard" />

      {/* **Che cielo hai**, dopo il punto sulla Terra e prima di salvare: e' l'ultima cosa che
          serve al sito, e si sceglie guardando cosa ci si vede invece di scrivere una magnitudine
          per arcosecondo quadrato. */}
      <SceltaDelCielo cielo={campi.cielo} onScegli={campi.setCielo} />

      <div className="as-pagina__azioni">
        <Bottone disabled={!campi.valido || salvando} verso="primario" onClick={() => void salva()}>
          {t("wizard.site.save")}
        </Bottone>
      </div>

      {rotto && (
        <Avviso esito="allarme" titolo={t("wizard.site.failedTitle")}>
          {t("wizard.site.failed")}
        </Avviso>
      )}
    </>
  )
}
