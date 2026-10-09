import { useState } from "react"

import { Avviso } from "./Avviso"
import { SfogliaCartelle } from "./SfogliaCartelle"
import { ScriviPercorso, VistaDellaSonda, useCartelle } from "./cartelle"
import { numero, t } from "./i18n"
import { usePienoDelPasso } from "./pienoDelPasso"
import { useRadiceDati } from "./radiceDati"

/**
 * Il terzo passo: dove stanno i file. **Quante cartelle vuoi**, non una sola.
 *
 * La sostanza -- guardare dentro, registrare, elencare -- sta in `cartelle.tsx`, che la divide
 * con la sezione Cartelle delle Impostazioni. Qui resta cio' che e' del **passo**:
 *
 * - **Aggiungere una cartella non chiude il primo avvio.** Prima lo chiudeva, ed e' il motivo per
 *   cui se ne poteva indicare una sola: chi tiene le foto su due dischi doveva aggiungere la
 *   seconda da un posto che non esisteva. A chiudere e' il tasto Fine.
 * - **Dove l'app ha una radice dei dati** (il NAS in Docker) le cartelle si **scelgono**: li'
 *   l'utente non sa che percorso abbia la sua cartella *dentro* il container, e scriverlo a mano
 *   e' indovinare. Sul desktop non c'e' radice, e il percorso si scrive.
 */
export function WizardFolders({ onOffre }: { onOffre: (offre: boolean) => void }) {
  const [path, setPath] = useState("")
  const cartelle = useCartelle("wizard.folders.failed")
  const radice = useRadiceDati()
  // Quando l'esito offre di registrare, il comando pieno e' il suo: il guscio lo deve sapere,
  // perche' Avanti gli ceda il posto.
  usePienoDelPasso(onOffre, cartelle.vista?.reachable === true)

  const scrivi = (
    <ScriviPercorso
      id="wizard-path"
      onGuarda={() => void cartelle.guarda(path)}
      onScrivi={setPath}
      prefisso="wizard.folders"
      valore={path}
    />
  )

  const quante = cartelle.elenco.data?.items.length ?? 0
  return (
    <>
      <div className="as-passo__parte">
        {/* Due strade, e le decide **dove gira l'app**: sul computer il percorso si scrive, sul
            NAS non si puo' indovinare e si sfoglia. */}
        {radice === null ? (
          scrivi
        ) : (
          <SfogliaCartelle
            onGuarda={cartelle.guarda}
            radice={radice}
            scrivi={scrivi}
            usa={t("wizard.folders.useThis")}
          />
        )}

        {cartelle.vista && (
          <VistaDellaSonda
            inCorso={cartelle.inCorso}
            nonSpostata={cartelle.nonSpostata}
            onAggiungi={() => {
              setPath("")
              void cartelle.aggiungi()
            }}
            onSposta={(id) => {
              setPath("")
              void cartelle.spostaQui(id)
            }}
            prefisso="wizard.folders"
            vista={cartelle.vista}
          />
        )}

        {cartelle.rotto && (
          <Avviso esito="allarme">
            {t(
              cartelle.rotto === "guarda" ? "wizard.folders.lookFailed" : "wizard.folders.failed",
            )}
          </Avviso>
        )}
      </div>

      {quante > 0 && (
        <div className="as-passo__parte">
          {/* Quante sono sta **nel titoletto**, non contato a occhio sulle righe. */}
          <p className="as-soprattitolo as-soprattitolo--nudo" id="wizard-added">
            {t("wizard.folders.added")}
            {" \u00b7 "}
            {numero(quante)}
          </p>
          <ul className="as-cartelle" aria-labelledby="wizard-added">
            {cartelle.elenco.data?.items.map((c) => (
              <li key={c.id} className="as-cartelle__voce">
                <span className="as-cartelle__percorso">{c.root_path}</span>
                <span className="as-cartelle__frame">{t("review.frames", { n: numero(c.frames) })}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  )
}
