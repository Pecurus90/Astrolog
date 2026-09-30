import { memo } from "react"

import { Dettaglio, Riga } from "./Riga"
import { Scelte } from "./Scelte"
import { type PerGruppo, Sezione } from "./Sezione"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"

type Coppia = components["schemas"]["LookalikeOut"]
type Risposta = components["schemas"]["LookalikeEdit"]
type Scelta = "same" | "distinct"

/**
 * Due grafie che hanno tutta l'aria di essere la stessa camera: "sono lo stesso pezzo?". L'app non
 * puo' saperlo -- due camere dello stesso modello sono due pezzi -- quindi chiede.
 *
 * - **Si' unisce, no non la ripropone**: sono le due sole risposte, e tutte e due chiudono la
 *   domanda. Un'unione non si disfa, per questo niente e' preselezionato.
 * - **Quale grafia resta lo dice l'API** (`into_id`, quella con piu' pose): qui non si sceglie.
 * - **E' memorizzata**: ogni risposta, in qualunque sezione, riscrive l'accumulatore della pagina.
 */
export const SezioneStessoPezzo = memo(function SezioneStessoPezzo({
  gruppi,
  risposte,
  onRisposta,
}: PerGruppo<Coppia, Risposta>) {
  return (
    <Sezione titolo={t("review.lookalikes")} domanda={t("review.lookalikes.why")}
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
  const scelta: Scelta | undefined = risposta && (risposta.same ? "same" : "distinct")
  return (
    <Riga
      frames={coppia.frames}
      nome={coppia.name}
      stato={risposta ? "risposta" : undefined}
      dettagli={
        <Dettaglio>
          {t("review.lookalikes.looksLike", {
            nome: coppia.into_name,
            pose: numero(coppia.into_frames),
          })}
        </Dettaglio>
      }
    >
      <Scelte
        domanda={t("review.lookalikes.question", { nome: coppia.name, altra: coppia.into_name })}
        nome={`stesso-pezzo-${coppia.id}`}
        opzioni={[
          { valore: "same" as const, etichetta: t("review.lookalikes.same", { nome: coppia.into_name }) },
          { valore: "distinct" as const, etichetta: t("review.lookalikes.distinct") },
        ]}
        scelta={scelta}
        onScelta={(v) =>
          onRisposta(String(coppia.id), {
            id: coppia.id,
            into_id: coppia.into_id,
            same: v === "same",
          })
        }
      />
    </Riga>
  )
}
