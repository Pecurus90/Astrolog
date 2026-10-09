import { useState } from "react"
import { CampoConScelte } from "./CampoConScelte"
import { Scelte } from "./Scelte"
import { Domanda } from "./Domanda"
import { Sezione } from "./Sezione"
import type { components } from "./api/schema"
import { TempoDellePose } from "./TempoDellePose"
import { type Chiave, cielo, numero, t } from "./i18n"
import { testo } from "./scritto"

type Mosaico = components["schemas"]["MosaicCandidate"]
type Risposta = components["schemas"]["MosaicEdit"]
type Parola = Risposta["answer"]

/**
 * Le regioni riprese a **pannelli affiancati**: l'app le propone come mosaico, **non le fonde**.
 *
 * - **Si risponde con la chiave del mosaico**, che non cambia quando cambia la camera.
 * - **Un no e' una risposta come un si'**, e resta: senza, l'unico modo di far tacere una proposta
 *   sbagliata sarebbe accettarla. Ridare la stessa non manda niente.
 * - **Il si' dice di cosa**: una domanda sola, col campo gia' compilato con la proposta del backend.
 * - **La riga dice la regione**: lo stesso soggetto ripreso in due parti sono due proposte, e senza
 *   il centro sarebbero due righe con lo stesso nome.
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
    <Sezione quale="mosaics" domanda={t("review.mosaics.why")}
      voci={mosaici}
      chiave={(m) => m.key}
      riga={(m) => <RigaMosaici mosaico={m} risposta={risposte[m.key]} onRisposta={onRisposta} />}
    />
  )
}

function RigaMosaici({
  mosaico,
  risposta,
  onRisposta,
}: {
  mosaico: Mosaico
  risposta: Risposta | undefined
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  const chiave = mosaico.key
  const dove = cielo(mosaico.ra_deg, mosaico.dec_deg)
  // La scelta e il nome sono della riga e non dell'accumulatore: ridando la risposta gia' salvata
  // la voce nell'accumulatore si toglie, e un campo che leggesse da li' si svuoterebbe sotto le dita.
  const [scelta, setScelta] = useState<Parola | null>(risposta?.answer ?? mosaico.answer ?? null)
  // Parte dal nome in mano, se c'e': la sezione si rimonta quando si chiude e si riapre.
  const [nome, setNome] = useState(risposta?.name ?? mosaico.answer_name ?? mosaico.proposed)
  const idCampo = `mosaico-nome-${chiave}`

  const manda = (parola: Parola, scritto: string) => {
    setScelta(parola)
    setNome(scritto)
    const punto = { key: mosaico.key }
    if (parola === "no") {
      onRisposta(chiave, mosaico.answer === "no" ? null : { ...punto, answer: "no" })
      return
    }
    // un si' senza nome non parte: il backend lo rifiuterebbe, e con lui tutto l'Applica
    const detto = testo(scritto, mosaico.answer === "yes" ? mosaico.answer_name : null)
    onRisposta(chiave, detto ? { ...punto, answer: "yes", name: detto.trim() } : null)
  }

  const detta = risposta?.answer ?? mosaico.answer
  const dettoDi = risposta?.name ?? mosaico.answer_name ?? ""
  const si = t(PAROLE.yes)
  const no = t(PAROLE.no)
  return (
    <Domanda
      id={`mosaics:${chiave}`}
      voce={`${mosaico.object}, ${dove}`}
      nome={<span className="as-nome-oggetto">{mosaico.object}</span>}
      frames={mosaico.frames}
      salvata={mosaico.answer !== null}
      inMano={risposta !== undefined}
      era={mosaico.answer ? t(PAROLE[mosaico.answer]) : undefined}
      // In breve si legge la risposta che c'e' -- in mano o salvata --, non la scelta a meta':
      // un si' col nome svuotato non e' una risposta.
      breve={detta ? <b>{detta === "yes" ? `${si}: ${dettoDi}` : no}</b> : `${si} \u00b7 ${no}`}
      accanto={t("review.mosaics.panels", { n: numero(mosaico.panels) })}
      prova={[
        ...(mosaico.integration_s > 0 || mosaico.untimed > 0
          ? [
              {
                nome: t("review.proof.time"),
                dato: <TempoDellePose secondi={mosaico.integration_s} senzaTempo={mosaico.untimed} stacco={" \u00b7 "} />,
              },
            ]
          : []),
        // La regione dice QUALE: lo stesso soggetto ripreso in due parti fa due domande.
        { nome: t("review.proof.where"), dato: dove },
      ]}
    >
      <Scelte
        domanda={t("review.mosaics.question", { soggetti: mosaico.object, dove })}
        nome={`mosaico-${chiave}`}
        opzioni={RISPOSTE.map(([valore, parola]) => ({ valore, etichetta: t(parola) }))}
        scelta={scelta}
        onScelta={(valore) => manda(valore, nome)}
      >
        {/* Col si' si dice anche DI COSA, e il campo arriva gia' compilato con la proposta. I
            soggetti dei pannelli sono i suggerimenti. L'etichetta dice quale mosaico. */}
        {scelta === "yes" && (
          <CampoConScelte
            id={idCampo}
            etichetta={t("review.mosaics.name", { dove })}
            valore={nome}
            scelte={mosaico.names}
            onScrivi={(scritto) => manda("yes", scritto)}
          />
        )}
      </Scelte>
    </Domanda>
  )
}

/** Il si' e il no, sul tipo generato (`MosaicAnswer` nel backend). */
const PAROLE: Record<Parola, Chiave> = {
  yes: "review.mosaics.yes",
  no: "review.mosaics.no",
}
const RISPOSTE = Object.entries(PAROLE) as [Parola, Chiave][]
