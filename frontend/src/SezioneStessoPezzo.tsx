import { memo } from "react"

import { statoDi } from "./ConfermareGuscio"
import { Domanda, Parte, Risposte, rigaDeiFrame, sensore, voce } from "./Domanda"
import { type PerGruppo, Sezione } from "./Sezione"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"

type Coppia = components["schemas"]["LookalikeOut"]
type Risposta = components["schemas"]["LookalikeEdit"]

/**
 * Due grafie che hanno tutta l'aria di essere lo stesso strumento: "sono lo stesso?". L'app non
 * puo' saperlo -- due camere dello stesso modello sono due pezzi -- quindi chiede.
 *
 * - **Si' unisce, no non la ripropone**; un'unione non si disfa, per questo niente e' preselezionato.
 * - **Quale grafia resta lo dice l'API** (`into_id`, quella con piu' frame): qui non si sceglie.
 * - **E' memorizzata**: ogni risposta, in qualunque sezione, riscrive l'accumulatore della pagina.
 */
export const SezioneStessoPezzo = memo(function SezioneStessoPezzo({
  gruppi,
  risposte,
  onRisposta,
}: PerGruppo<Coppia, Risposta>) {
  return (
    <Sezione
      quale="lookalikes"
      domanda={t("review.lookalikes.why")}
      voci={gruppi}
      chiave={(c) => c.id}
      riga={(c) => (
        <RigaStessoPezzo coppia={c} risposta={risposte[String(c.id)]} onRisposta={onRisposta} />
      )}
    />
  )
})

function RigaStessoPezzo({
  coppia,
  risposta,
  onRisposta,
}: {
  coppia: Coppia
  risposta: Risposta | undefined
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  const unisci = t("review.lookalikes.same", { nome: coppia.into_name })
  const distinti = t("review.lookalikes.distinct")
  const manda = (same: boolean) =>
    onRisposta(String(coppia.id), { id: coppia.id, into_id: coppia.into_id, same })
  const sens = sensore(coppia.width_px, coppia.height_px, coppia.pixel_um)
  const domanda = t("review.lookalikes.question", { nome: coppia.name, altra: coppia.into_name })
  return (
    <Domanda
      id={`lookalikes:${coppia.id}`}
      voce={coppia.name}
      nome={coppia.name}
      frame={rigaDeiFrame(coppia.frames)}
      stato={statoDi(false, risposta !== undefined)}
      detta={risposta !== undefined}
      breve={risposta ? (risposta.same ? unisci : distinti) : `${unisci} \u00b7 ${distinti}`}
      prova={[
        { nome: t("review.proof.like"), righe: [coppia.into_name] },
        ...(sens ? [{ nome: t("review.proof.sensor"), righe: [sens] }] : []),
        {
          nome: t("review.proof.others"),
          righe: [
            t("review.lookalikes.otherFrames", {
              frame: t("review.frames", { n: numero(coppia.into_frames) }),
              nome: coppia.into_name,
            }),
          ],
        },
      ]}
    >
      <Parte capo={domanda} prima>
        <Risposte
          etichetta={domanda}
          opzioni={[
            voce(
              risposta?.same === true,
              unisci,
              () => manda(true),
              t("review.lookalikes.same.sub", {
                nome: coppia.into_name,
                n: numero(coppia.into_frames),
                m: numero(coppia.frames),
              }),
            ),
            voce(risposta?.same === false, distinti, () => manda(false)),
          ]}
        />
      </Parte>
    </Domanda>
  )
}
