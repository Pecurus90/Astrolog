import { memo } from "react"

import { Scelte } from "./Scelte"
import { Dettaglio, Riga } from "./Riga"
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
 * - **Due risposte e basta** -- foto del cielo, file di calibrazione -- e sono poche e fisse:
 *   quindi il gruppo di scelte comune (`Scelte`), come le altre sezioni che chiedono "quale di
 *   queste".
 * - **Non c'e' un "non lo so"**: non saperlo e' gia' lo stato di partenza, e una terza scelta non
 *   toglierebbe quei frame da nessuna parte.
 * - **Una cartella risposta resta in pagina** con la sua risposta, e si cambia: basta scegliere
 *   l'altra. Riscegliere quella gia' data toglie la risposta dall'accumulatore, perche'
 *   rimandarla rimetterebbe in coda quei frame per non cambiare niente.
 * - **Cio' che il cielo ha trovato non si mostra**, a differenza delle altre sezioni per gruppo:
 *   su quei frame il cielo non ha saputo dire, e un elenco vuoto sembrerebbe una risposta.
 * - **E' memorizzata**: ogni risposta, in qualunque sezione, riscrive l'accumulatore della pagina.
 */
export const SezioneSenzaTipo = memo(function SezioneSenzaTipo({
  gruppi,
  risposte,
  onRisposta,
}: PerGruppo<Gruppo, Risposta>) {
  return (
    <Sezione titolo={t("review.typeless")} domanda={t("review.typeless.why")}
      voci={gruppi}
      chiave={(g) => g.key}
      riga={(g) => (
        <RigaSenzaTipo gruppo={g} risposta={risposte[g.key]} onRisposta={onRisposta} />
      )}
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
  // Cio' che si vede scelto e' la risposta appena data, se c'e', altrimenti quella gia' salvata:
  // leggendo solo la salvata, chi sceglie non vedrebbe succedere niente finche' non applica.
  const scelta = risposta?.kind ?? gruppo.answer
  return (
    <Riga
      frames={gruppo.frames}
      nome={gruppo.key}
      stato={risposta ? "risposta" : undefined}
      dettagli={
        <>
          {gruppo.answer && <Dettaglio>{t(DETTO[gruppo.answer])}</Dettaglio>}
        </>
      }
    >
      <Scelte
        domanda={t("review.typeless.question", { cartella: gruppo.key })}
        nome={`senza-tipo-${gruppo.key}`}
        opzioni={SCELTE.map(([valore, parola]) => ({ valore, etichetta: t(parola) }))}
        scelta={scelta}
        onScelta={(kind) =>
          onRisposta(gruppo.key, kind === gruppo.answer ? null : { key: gruppo.key, kind })
        }
      />
    </Riga>
  )
}

/** Le due risposte, sul tipo generato: il giorno che il backend ne aggiunge una, qui non compila
 *  finche' qualcuno non le da' un nome. */
const PAROLE: Record<Scelta, Chiave> = {
  light: "review.typeless.light",
  calibration: "review.typeless.calibration",
}
const SCELTE = Object.entries(PAROLE) as [Scelta, Chiave][]

/** Come si legge la risposta gia' data, accanto alla cartella. Stessa regola: una parola per
 *  risposta, e una risposta nuova non compila finche' non ne ha una. */
const DETTO: Record<Scelta, Chiave> = {
  light: "review.typeless.answerLight",
  calibration: "review.typeless.answerCalibration",
}
