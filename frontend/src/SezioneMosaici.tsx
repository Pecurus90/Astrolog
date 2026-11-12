import { useState } from "react"

import { statoDi } from "./ConfermareGuscio"
import { Campi, Domanda, Parte, Risposte, righeDelleNotti, rigaDeiFrame, voce } from "./Domanda"
import { Sezione } from "./Sezione"
import type { components } from "./api/schema"
import { type Chiave, cielo, t } from "./i18n"
import { testo } from "./scritto"

type Mosaico = components["schemas"]["MosaicCandidate"]
type Risposta = components["schemas"]["MosaicEdit"]
type Parola = Risposta["answer"]

/**
 * Le regioni riprese a **pannelli affiancati**: l'app le propone come mosaico, **non le fonde**.
 *
 * - **Si risponde con la chiave del mosaico**, che non cambia quando cambia la camera.
 * - **Un no e' una risposta come un si'**, e resta. Ridare la risposta salvata non manda niente.
 * - **Il si' dice di cosa**: il campo arriva compilato col nome proposto dal backend.
 * - **La domanda dice la regione**: lo stesso soggetto in due parti sono due proposte.
 */
export function SezioneMosaici({
  mosaici,
  risposte,
  onRisposta,
}: {
  mosaici: Mosaico[]
  risposte: Record<string, Risposta>
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  return (
    <Sezione
      quale="mosaics"
      domanda={t("review.mosaics.why")}
      voci={mosaici}
      chiave={(m) => m.key}
      riga={(m, indice) => (
        <RigaMosaici
          indice={indice}
          mosaico={m}
          risposta={risposte[m.key]}
          onRisposta={onRisposta}
        />
      )}
    />
  )
}

function RigaMosaici({
  indice,
  mosaico,
  risposta,
  onRisposta,
}: {
  indice: number
  mosaico: Mosaico
  risposta: Risposta | undefined
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  const dove = cielo(mosaico.ra_deg, mosaico.dec_deg)
  // Scelta e nome sono della riga: ridando la risposta salvata la voce in mano si toglie, e un
  // campo che leggesse da li' si svuoterebbe sotto le dita.
  const [scelta, setScelta] = useState<Parola | null>(risposta?.answer ?? mosaico.answer ?? null)
  const [nome, setNome] = useState(risposta?.name ?? mosaico.answer_name ?? mosaico.proposed)

  const manda = (parola: Parola, scritto: string) => {
    setScelta(parola)
    setNome(scritto)
    const punto = { key: mosaico.key }
    if (parola === "no") {
      onRisposta(mosaico.key, mosaico.answer === "no" ? null : { ...punto, answer: "no" })
      return
    }
    // un si' senza nome non parte: il backend lo rifiuterebbe, e con lui tutto l'Applica
    const detto = testo(scritto, mosaico.answer === "yes" ? mosaico.answer_name : null)
    onRisposta(mosaico.key, detto ? { ...punto, answer: "yes", name: detto.trim() } : null)
  }

  const detto = (parola: Parola | null, di: string | null) =>
    parola === "yes"
      ? di
        ? t("review.mosaics.yesNamed", { nome: di })
        : null
      : parola === "no"
        ? t(PAROLE.no)
        : null
  // In breve la risposta che c'e', in mano o salvata: un si' col nome svuotato non e' una risposta.
  const breve = risposta
    ? detto(risposta.answer, risposta.name ?? null)
    : detto(mosaico.answer, mosaico.answer_name)
  const domanda = t("review.mosaics.question", { soggetti: mosaico.object, dove })
  return (
    <Domanda
      id={`mosaics:${mosaico.key}`}
      voce={`${mosaico.object}, ${dove}`}
      nome={mosaico.object}
      frame={rigaDeiFrame(mosaico.frames, mosaico.integration_s, mosaico.untimed, mosaico.panels)}
      stato={statoDi(mosaico.answer !== null, risposta !== undefined)}
      era={detto(mosaico.answer, mosaico.answer_name) ?? undefined}
      detta={breve !== null}
      breve={breve ?? RISPOSTE.map(([, parola]) => t(parola)).join(" \u00b7 ")}
      prova={[
        ...(mosaico.names.length > 0
          ? [{ nome: t("review.proof.inField"), righe: [mosaico.names.join(", ")] }]
          : []),
        ...(mosaico.nights.length > 0
          ? [{ nome: t("review.proof.night"), righe: righeDelleNotti(mosaico.nights) }]
          : []),
      ]}
    >
      <Parte capo={domanda} prima>
        <Risposte
          etichetta={domanda}
          opzioni={RISPOSTE.map(([parola, chiave]) =>
            voce(scelta === parola, t(chiave), () => manda(parola, nome)),
          )}
        />
        {scelta === "yes" && (
          <Campi
            campi={[
              {
                id: `mosaico-nome-${indice}`,
                etichetta: t("review.mosaics.name", { dove }),
                valore: nome,
                onValore: (scritto) => manda("yes", scritto),
                aiuto: t("review.mosaics.proposed", { nome: mosaico.proposed }),
              },
            ]}
          />
        )}
      </Parte>
    </Domanda>
  )
}

/** Il si' e il no, sul tipo generato (`MosaicAnswer` nel backend). */
const PAROLE: Record<Parola, Chiave> = {
  yes: "review.mosaics.yes",
  no: "review.mosaics.no",
}
const RISPOSTE = Object.entries(PAROLE) as [Parola, Chiave][]
