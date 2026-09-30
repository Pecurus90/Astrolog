import { memo, useState } from "react"
import { Campo } from "./Campo"
import { Bottone } from "./Bottone"

import { Dettaglio, Riga } from "./Riga"
import { Sezione } from "./Sezione"
import type { components } from "./api/schema"
import { cielo, nomeDelGruppo, oraDelSito, t } from "./i18n"
import { testo } from "./scritto"

type Gruppo = components["schemas"]["UnnamedGroup"]
type Risposta = components["schemas"]["UnnamedEdit"]

/**
 * Le pose che l'header non nomina e di cui il cielo non dice niente: **una domanda per gruppo** --
 * notte, camera, telescopio e dove puntava la montatura --, che la riga dice al posto di un percorso.
 * La risposta vale anche per le pose che arriveranno con gli stessi valori.
 *
 * - **L'oggetto scritto oppure "non e' un oggetto"**, mai tutti e due (`UnnamedEdit`): qui non ci
 *   sono candidati del cielo da cliccare. Una sigla scritta la porta il backend sulla voce del
 *   catalogo, quindi il campo e' uno solo.
 * - **Un nome vuoto, o uguale alla risposta gia' data, non parte**: il primo tornerebbe un rifiuto
 *   che annulla tutto l'Applica, il secondo rimetterebbe in coda le pose per non cambiare niente.
 * - **Un gruppo risposto resta in pagina** con la sua risposta, e si cambia.
 * - **E' memorizzata**: ogni risposta, in qualunque sezione, riscrive l'accumulatore della pagina,
 *   e con migliaia di gruppi ridisegnarli tutti a ogni tasto rallenta la scrittura.
 */
export const SezioneSenzaNome = memo(function SezioneSenzaNome({
  gruppi,
  onRisposta,
}: {
  gruppi: Gruppo[]
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  return (
    <Sezione titolo={t("review.unnamed")} domanda={t("review.unnamed.why")}
      voci={gruppi}
      chiave={(g) => g.key}
      // l'id nasce dalla posizione: la chiave porta spazi e virgolette, e non e' un id valido
      riga={(g, indice) => (
        <RigaSenzaNome gruppo={g} id={`senza-nome-${indice}`} onRisposta={onRisposta} />
      )}
    />
  )
})

function RigaSenzaNome({
  gruppo,
  id,
  onRisposta,
}: {
  gruppo: Gruppo
  id: string
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  const data = gruppo.answer
  const [aperta, setAperta] = useState(data === null)
  // I due campi sono della riga e non dell'accumulatore: scrivendo la risposta gia' data la voce
  // nell'accumulatore si toglie, e un campo che leggesse da li' si svuoterebbe sotto le dita.
  const [nome, setNome] = useState(data?.kind === "none" ? "" : (data?.name ?? ""))
  const [nonOggetto, setNonOggetto] = useState(data?.kind === "none")

  const chi = nomeDelGruppo(gruppo.night, [
    gruppo.camera,
    gruppo.telescope,
    gruppo.ra_deg === null || gruppo.dec_deg === null
      ? null
      : t("review.unnamed.pointing", { dove: cielo(gruppo.ra_deg, gruppo.dec_deg) }),
  ])

  const manda = (scritto: string, nessuno: boolean) => {
    setNome(scritto)
    setNonOggetto(nessuno)
    if (nessuno) {
      onRisposta(gruppo.key, data?.kind === "none" ? null : { key: gruppo.key, not_an_object: true })
      return
    }
    const detto = testo(scritto, data?.kind === "none" ? null : data?.name)
    onRisposta(gruppo.key, detto ? { key: gruppo.key, name: detto, not_an_object: false } : null)
  }

  return (
    <Riga
      frames={gruppo.frames}
      nome={chi}
      // qui lo stato viene dalla risposta **gia' salvata**, non dall'accumulatore: questa riga
      // tiene i suoi campi da se' (`nome`, `nonOggetto`) e la pagina non le passa l'accumulatore
      stato={data ? "risposta" : undefined}
      dettagli={
        <>
          {/* Le ore della prima e dell'ultima posa, nell'ora del posto: due oggetti senza
              puntamento nella stessa notte sono una domanda sola, e le ore dicono se sono due. */}
          {gruppo.first_frame && gruppo.last_frame && (
            <Dettaglio>
              {gruppo.first_frame === gruppo.last_frame
                ? t("review.unnamed.at", { ora: oraDelSito(gruppo.first_frame) })
                : t("review.unnamed.hours", {
                    da: oraDelSito(gruppo.first_frame),
                    a: oraDelSito(gruppo.last_frame),
                  })}
            </Dettaglio>
          )}{" "}
          {data && (
            <Dettaglio>{data.kind === "none"
                ? t("review.unnamed.answerNone")
                : t("review.unnamed.answer", { nome: data.name ?? "" })}</Dettaglio>
          )}{" "}
        </>
      }
    >
      {/* Il bottone si ripete uguale su ogni gruppo: il nome accessibile dice quale, e comincia
          con la parola che si vede. */}
      {!aperta && (
        <Bottone piccolo nome={t("review.unnamed.changeFor", { gruppo: chi })} onClick={() => setAperta(true)}>
          {t("review.unnamed.change")}
        </Bottone>
      )}
      {/* Il gruppo dice di quale riga: i due campi si ripetono uguali su ogni riga, e un nome
          accessibile diverso dall'etichetta che si vede non lo ritrova chi lo pronuncia a voce. */}
      {aperta && (
        <fieldset>
          <legend>{t("review.unnamed.question", { gruppo: chi })}</legend>
          <Campo id={`${id}-oggetto`} etichetta={t("review.unnamed.object")}>
          <input
            className="as-campo__input"
            id={`${id}-oggetto`}
            value={nome}
            disabled={nonOggetto}
            onChange={(e) => manda(e.target.value, false)}
          />
          </Campo>{" "}
          <input
            id={`${id}-nessuno`}
            type="checkbox"
            checked={nonOggetto}
            onChange={(e) => manda(nome, e.target.checked)}
          />
          <label htmlFor={`${id}-nessuno`}>{t("review.unnamed.notAnObject")}</label>
        </fieldset>
      )}
    </Riga>
  )
}
