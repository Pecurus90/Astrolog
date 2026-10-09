import { useState } from "react"

import { Avviso } from "./Avviso"
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
 * - **Il comando che salva sta coi gesti del passo**, in fondo: lo stato vive in
 *   `useSitoDelPasso`, che il guscio tiene, perche' il primario sia uno solo.
 * - **Salvato, il modulo si svuota**: lo stato sopravvive al passo, e tornando indietro lo stesso
 *   sito si salverebbe due volte.
 */
export function useSitoDelPasso(onSaved: () => void) {
  const campi = useCampiDelSito()
  const [rotto, setRotto] = useState(false)
  const [salvando, setSalvando] = useState(false)

  const salva = async () => {
    if (!campi.valido || salvando) return
    setSalvando(true)
    // A request that never reaches the service rejects instead of returning `error`: it is the
    // same failure to the user, and `salvando` must not outlive it (this state survives the step).
    const fallita = await api
      .POST("/api/v1/sites", { body: { ...campi.corpo(), is_default: true } })
      .then(
        ({ error }) => Boolean(error),
        () => true,
      )
    setSalvando(false)
    setRotto(fallita)
    if (fallita) return
    campi.azzera()
    onSaved()
  }
  return { campi, rotto, salvando, salva }
}

export function WizardSite({ sito }: { sito: ReturnType<typeof useSitoDelPasso> }) {
  const { campi, rotto } = sito
  return (
    <>
      <div className="as-passo__parte">
        <p className="as-soprattitolo as-soprattitolo--nudo">{t("wizard.site.searchGroup")}</p>
        <CercaIlPosto
          aMano={() => document.getElementById("wizard-name")?.focus()}
          id="wizard-place"
          onScegli={campi.prendiDa}
        />
      </div>

      <div className="as-passo__parte">
        <p className="as-soprattitolo as-soprattitolo--nudo">{t("wizard.site.manual")}</p>
        <p className="as-passo__nota">{t("wizard.site.manualWhy")}</p>
        <CampiDelSito campi={campi} id="wizard" />
      </div>

      {/* Che cielo hai, dopo il punto sulla Terra: si sceglie guardando cosa ci si vede. */}
      <div className="as-passo__parte">
        <SceltaDelCielo cielo={campi.cielo} onScegli={campi.setCielo} />
        {rotto && (
          <Avviso esito="allarme" titolo={t("wizard.site.failedTitle")}>
            {t("wizard.site.failed")}
          </Avviso>
        )}
      </div>
    </>
  )
}
