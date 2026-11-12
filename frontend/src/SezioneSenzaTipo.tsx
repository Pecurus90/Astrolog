import { memo } from "react"

import { statoDi } from "./ConfermareGuscio"
import {
  Domanda,
  Parte,
  provaDellaDurata,
  Risposte,
  righeDelleNotti,
  rigaDeiFrame,
  voce,
} from "./Domanda"
import { type PerGruppo, Sezione } from "./Sezione"
import type { components } from "./api/schema"
import { type Chiave, t } from "./i18n"

type Gruppo = components["schemas"]["TypelessFolder"]
type Risposta = components["schemas"]["TypelessFolderEdit"]
type Scelta = Risposta["kind"]

/**
 * I file che non dicono **che file sono**: una domanda per cartella, quella che li contiene. La
 * risposta vale anche per i file che arriveranno li' dentro.
 *
 * - **Due risposte e basta**, Light e Calibrazione; non c'e' un "non lo so": non saperlo e' gia'
 *   lo stato di partenza.
 * - **Una cartella risposta resta in pagina** con la sua risposta, e si cambia scegliendo l'altra.
 *   Riscegliere quella salvata toglie la risposta in mano: rimandarla non cambierebbe niente.
 * - **E' memorizzata**: ogni risposta, in qualunque sezione, riscrive l'accumulatore della pagina.
 */
export const SezioneSenzaTipo = memo(function SezioneSenzaTipo({
  gruppi,
  risposte,
  onRisposta,
}: PerGruppo<Gruppo, Risposta>) {
  return (
    <Sezione
      quale="typeless"
      domanda={t("review.typeless.why")}
      voci={gruppi}
      chiave={(g) => g.key}
      riga={(g) => <RigaSenzaTipo gruppo={g} risposta={risposte[g.key]} onRisposta={onRisposta} />}
    />
  )
})

function RigaSenzaTipo({
  gruppo,
  risposta,
  onRisposta,
}: {
  gruppo: Gruppo
  risposta: Risposta | undefined
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  // Si vede scelta la risposta appena data, se c'e', altrimenti quella gia' salvata.
  const scelta = risposta?.kind ?? gruppo.answer
  const durata = provaDellaDurata(gruppo.integration_s, gruppo.untimed)
  const domanda = t("review.typeless.question", { cartella: gruppo.key })
  return (
    <Domanda
      id={`typeless:${gruppo.key}`}
      voce={gruppo.key}
      nome={gruppo.key}
      frame={rigaDeiFrame(gruppo.frames)}
      stato={statoDi(gruppo.answer !== null, risposta !== undefined)}
      era={gruppo.answer ? t(PAROLE[gruppo.answer]) : undefined}
      detta={scelta !== null}
      breve={scelta ? t(PAROLE[scelta]) : SCELTE.map(([, parola]) => t(parola)).join(" \u00b7 ")}
      prova={[
        ...(gruppo.nights.length > 0
          ? [{ nome: t("review.proof.night"), righe: righeDelleNotti(gruppo.nights) }]
          : []),
        ...(durata ? [durata] : []),
      ]}
    >
      <Parte capo={domanda} prima>
        <Risposte
          etichetta={domanda}
          opzioni={SCELTE.map(([kind, parola]) =>
            voce(scelta === kind, t(parola), () =>
              onRisposta(gruppo.key, kind === gruppo.answer ? null : { key: gruppo.key, kind }),
            ),
          )}
        />
      </Parte>
    </Domanda>
  )
}

/** Le due risposte, sul tipo generato: una nuova non compila finche' non ha un nome. */
const PAROLE: Record<Scelta, Chiave> = {
  light: "review.typeless.light",
  calibration: "review.typeless.calibration",
}
const SCELTE = Object.entries(PAROLE) as [Scelta, Chiave][]
