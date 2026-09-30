import { useState } from "react"

import { TendinaDiScelta } from "./TendinaDiScelta"
import { Scelte } from "./Scelte"
import { Riga } from "./Riga"
import { type PerGruppo, Sezione } from "./Sezione"
import type { components } from "./api/schema"
import { type Chiave, t } from "./i18n"

type Gruppo = components["schemas"]["UnfilteredCamera"]
type Risposta = components["schemas"]["UnfilteredEdit"]
type Filtro = components["schemas"]["FilterCandidate"]
type Scelta = Risposta["answer"]

/**
 * Le pose che non dicono il filtro: **una domanda per camera**, perche' senza `BAYERPAT` una mono e
 * una camera a colori non si distinguono, e la risposta vale anche per le pose che verranno. Una
 * camera che i file dicono a colori non arriva qui: decide l'app.
 *
 * - **Tre risposte**: a colori, nessun filtro, o uno dei tuoi filtri, che si sceglie dalla tendina
 *   dei filtri con la banda nota -- la stessa per ogni camera, e la manda la pagina una volta sola.
 * - **La risposta gia' data resta selezionata**, e ridarla uguale non manda niente: riscrivere la
 *   stessa risposta rimetterebbe in coda pose che non cambiano. Scegliere "uno dei tuoi" non manda
 *   niente finche' il filtro non c'e'.
 */
export function SezioneSenzaFiltro({
  gruppi,
  filtri,
  risposte,
  onRisposta,
}: PerGruppo<Gruppo, Risposta> & { filtri: Filtro[] }) {
  return (
    <Sezione titolo={t("review.unfiltered")} domanda={t("review.unfiltered.why")}
      voci={gruppi}
      chiave={(g) => g.key}
      riga={(g, indice) => (
        <RigaSenzaFiltro
          gruppo={g}
          id={`senza-filtro-${indice}`}
          filtri={filtri}
          risposta={risposte[g.key]}
          onRisposta={onRisposta}
        />
      )}
    />
  )
}

function RigaSenzaFiltro({
  gruppo,
  id,
  filtri,
  risposta,
  onRisposta,
}: {
  gruppo: Gruppo
  id: string
  filtri: Filtro[]
  risposta: Risposta | undefined
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  const [voglioUnFiltro, setVoglioUnFiltro] = useState(false)
  const scelta = risposta?.answer ?? (voglioUnFiltro ? "filter" : gruppo.answer)
  const salvato = gruppo.filter_id ?? undefined
  const filtro = risposta?.filter_id ?? salvato
  function scegli(valore: Scelta) {
    setVoglioUnFiltro(valore === "filter")
    const uguale = valore === gruppo.answer || valore === "filter"
    onRisposta(gruppo.key, uguale ? null : { key: gruppo.key, answer: valore })
  }
  function scegliFiltro(scelto: number | undefined) {
    const uguale = scelto === undefined || (gruppo.answer === "filter" && scelto === salvato)
    onRisposta(gruppo.key, uguale ? null : { key: gruppo.key, answer: "filter", filter_id: scelto })
  }
  return (
    <Riga
      frames={gruppo.frames}
      ripreso={gruppo.subjects}
      nome={gruppo.key}
      stato={risposta ? "risposta" : undefined}
    >
      <Scelte
        domanda={t("review.unfiltered.question", { camera: gruppo.key })}
        nome={`${id}-scelta`}
        opzioni={SCELTE.map(([valore, parola]) => ({ valore, etichetta: t(parola) }))}
        scelta={scelta}
        onScelta={scegli}
      />
      {scelta === "filter" && (
        <TendinaDiScelta
          id={`${id}-filtro`}
          etichetta={t("review.unfiltered.which", { camera: gruppo.key })}
          altri={filtri}
          valore={filtro}
          onScelta={scegliFiltro}
        />
      )}
    </Riga>
  )
}

/** Le tre risposte, sul tipo generato: il giorno che il backend ne aggiunge una, qui non compila
 *  finche' qualcuno non le da' un nome. */
const PAROLE: Record<Scelta, Chiave> = {
  color: "review.unfiltered.color",
  no_filter: "review.unfiltered.noFilter",
  filter: "review.unfiltered.mine",
}
const SCELTE = Object.entries(PAROLE) as [Scelta, Chiave][]
