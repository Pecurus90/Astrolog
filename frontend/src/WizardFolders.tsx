import { useState } from "react"

import { Avviso } from "./Avviso"
import { Riga } from "./Riga"
import { SfogliaCartelle } from "./SfogliaCartelle"
import { ScriviPercorso, VistaDellaSonda, useCartelle } from "./cartelle"
import { numero, t } from "./i18n"
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
export function WizardFolders() {
  const [path, setPath] = useState("")
  const cartelle = useCartelle("wizard.folders.failed")
  const radice = useRadiceDati()

  const scrivi = (
    <ScriviPercorso
      id="wizard-path"
      onGuarda={() => void cartelle.guarda(path)}
      onScrivi={setPath}
      prefisso="wizard.folders"
      valore={path}
    />
  )

  return (
    <>
      {/* Due strade, e le decide **dove gira l'app**: sul computer il percorso si scrive, sul NAS
          non si puo' indovinare e si sfoglia. */}
      {radice === null ? (
        scrivi
      ) : (
        <SfogliaCartelle onGuarda={cartelle.guarda} radice={radice} scrivi={scrivi} />
      )}

      {cartelle.vista && (
        <VistaDellaSonda
          inCorso={cartelle.inCorso}
          onAggiungi={() => {
            setPath("")
            void cartelle.aggiungi()
          }}
          prefisso="wizard.folders"
          vista={cartelle.vista}
        />
      )}

      {(cartelle.elenco.data?.items.length ?? 0) > 0 && (
        <>
          {/* Il conteggio sta **accanto al titoletto**, non contato a occhio sulle righe. */}
          <p className="as-soprattitolo" id="wizard-added">
            {t("wizard.folders.added")}{" "}
            <span className="as-stato as-stato--conteggio">
              {numero(cartelle.elenco.data?.items.length ?? 0)}
            </span>
          </p>
          <div className="as-carta as-carta--alta">
            <div className="as-carta__corpo as-carta__corpo--stretto">
              <ul className="as-elenco" aria-labelledby="wizard-added">
                {cartelle.elenco.data?.items.map((c) => (
                  <li key={c.id}>
                    <Riga nome={c.root_path} frames={c.frames} />
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </>
      )}

      {cartelle.rotto && (
        <Avviso esito="allarme">
          {t(
            cartelle.rotto === "guarda" ? "wizard.folders.lookFailed" : "wizard.folders.failed",
          )}
        </Avviso>
      )}
    </>
  )
}
