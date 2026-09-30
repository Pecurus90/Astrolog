import { useState } from "react"
import { CampoConScelte } from "./CampoConScelte"

import { Dettaglio, Riga } from "./Riga"
import { Sezione } from "./Sezione"
import { TempoDellePose } from "./TempoDellePose"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"
import { testo } from "./scritto"

type Domanda = components["schemas"]["OpticslessRig"]
type Risposta = components["schemas"]["OpticslessEdit"]

/**
 * Le pose i cui file non nominano l'ottica -- l'ASIAIR ci scrive la montatura --: **una domanda per
 * camera e focale**, e la risposta vale anche per le pose che arriveranno.
 *
 * - **Un campo solo**: si sceglie fra le ottiche che hai (`optics_choices`) o se ne scrive il nome,
 *   e il pezzo nuovo nasce dal nome nel backend. Il campo parte vuoto: nessuna ottica e' proposta,
 *   perche' i file non ne dicono nessuna.
 * - **Una domanda risposta resta in pagina** con la sua risposta nel campo, e si cambia; ridarla
 *   uguale, o svuotare il campo, non manda niente.
 */
export function SezioneSenzaOttica({
  domande,
  ottiche,
  risposte,
  onRisposta,
}: {
  domande: Domanda[]
  ottiche: string[]
  risposte: Record<string, Risposta>
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  return (
    <Sezione titolo={t("review.opticsless")} domanda={t("review.opticsless.why")}
      voci={domande}
      chiave={(d) => d.key}
      riga={(d, i) => (
        <RigaSenzaOttica domanda={d} indice={i} ottiche={ottiche} risposta={risposte[d.key]}
          onRisposta={onRisposta} />
      )}
    />
  )
}

function RigaSenzaOttica({
  domanda,
  indice,
  ottiche,
  risposta,
  onRisposta,
}: {
  domanda: Domanda
  indice: number
  ottiche: string[]
  risposta: Risposta | undefined
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  // Il nome scritto e' della riga e non dell'accumulatore: ridando la risposta salvata la voce
  // nell'accumulatore si toglie, e un campo che leggesse da li' si svuoterebbe sotto le dita.
  const [nome, setNome] = useState(domanda.answer ?? "")
  // l'indice e non la chiave: la chiave porta il nome della camera, con spazi e barre
  const idCampo = `ottica-${indice}`
  const scrive = (scritto: string) => {
    setNome(scritto)
    const detto = testo(scritto.trim(), domanda.answer)
    onRisposta(domanda.key, detto ? { key: domanda.key, optics: detto } : null)
  }
  return (
    <Riga
      nome={domanda.camera}
      frames={domanda.frames}
      ripreso={domanda.subjects}
      stato={risposta ? "risposta" : undefined}
      dettagli={
        <>
          {domanda.focal_mm != null && (
            <Dettaglio>{t("review.opticsless.focal", { mm: numero(domanda.focal_mm) })}</Dettaglio>
          )}{" "}
          <TempoDellePose secondi={domanda.integration_s} senzaTempo={domanda.untimed} />
        </>
      }
    >
      <CampoConScelte
        id={idCampo}
        etichetta={t("review.opticsless.optics", { camera: domanda.camera })}
        valore={nome}
        scelte={ottiche}
        onScrivi={scrive}
      />
    </Riga>
  )
}
