import { useState } from "react"

import { Campo } from "./Campo"
import { Domanda } from "./Domanda"
import { Scelte } from "./Scelte"
import { Sezione } from "./Sezione"
import type { components } from "./api/schema"
import { cielo, notte, numero, oraDelSito, ore, t } from "./i18n"

type Scheda = components["schemas"]["ObjectCard"]
type Risposta = components["schemas"]["ObjectEdit"]

// Le due risposte che non sono una voce del campo. Una voce si riconosce dalla sua sigla.
const ALTRO_NOME = "nome"
const NON_OGGETTO = "nessuno"

/**
 * **Che oggetto e'**: una scheda per gruppo di frame, sempre uguale (ADR 0014, S3) -- un oggetto
 * su cui l'app ha un dubbio, o frame che non dicono cosa e' stato ripreso e di cui il plate
 * solving non dice niente.
 *
 * - **Una risposta sola fra tre**: una voce trovata nel campo, un nome scritto, "non e' un
 *   oggetto". Il backend ne rifiuta due insieme, e qui non se ne possono dare due.
 * - **Un nome vuoto non e' una risposta**: Applica direbbe "fatto" senza aver cambiato niente.
 * - **Una scheda risposta resta in pagina**, e ridare la stessa risposta non manda niente.
 * - **Puntamento, camera e ore ci sono solo nei frame senza nome**: per un oggetto in dubbio
 *   l'API non li manda.
 */
export function SezioneOggetti({
  schede,
  aPosto,
  risposte,
  onRisposta,
}: {
  schede: Scheda[]
  /** Quanti oggetti l'app riconosce da sola: non sono domande. */
  aPosto: number
  risposte: Record<string, Risposta>
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  return (
    <Sezione
      quale="objects"
      domanda={t("review.objects.why")}
      voci={schede}
      chiave={(s) => s.key}
      riga={(s, indice) => (
        <RigaOggetti indice={indice} scheda={s} risposta={risposte[s.key]} onRisposta={onRisposta} />
      )}
      piede={
        aPosto > 0 && (
          <div className="as-conferma-aposto">
            <p>
              <b>{numero(aPosto)}</b> {t("review.objects.settled", { n: aPosto })}
            </p>
          </div>
        )
      }
    />
  )
}

/**
 * Cosa dice una risposta salvata, nella stessa forma di una scelta: una sigla, o una delle due.
 * Una sigla che non e' fra le voci del campo e' stata scritta in "Altro nome": il catalogo
 * l'ha riconosciuta, ma la scelta da mostrare resta il nome.
 */
function salvataDi(scheda: Scheda): string | null {
  const data = scheda.answer
  if (!data) return null
  if (data.kind === "none") return NON_OGGETTO
  return data.kind === "catalog" && scheda.candidates.some((c) => c.slug === data.value) ? data.value : ALTRO_NOME
}

function RigaOggetti({
  indice,
  scheda,
  risposta,
  onRisposta,
}: {
  indice: number
  scheda: Scheda
  risposta: Risposta | undefined
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  const salvata = salvataDi(scheda)
  const nomeSalvato = salvata === ALTRO_NOME ? (scheda.answer?.name ?? "") : ""
  // La scelta e il nome sono della riga: un nome a meta' non sta nell'accumulo, e senza tenerlo
  // qui il campo si svuoterebbe sotto le dita. Partono dalla risposta in mano, poi dalla salvata.
  const [scelta, setScelta] = useState<string | null>(
    risposta ? (risposta.not_an_object ? NON_OGGETTO : (risposta.slug ?? ALTRO_NOME)) : salvata,
  )
  const [scritto, setScritto] = useState(risposta?.name ?? nomeSalvato)

  const manda = (quale: string, nome: string) => {
    setScelta(quale)
    setScritto(nome)
    const pulito = nome.trim()
    // ridare la risposta gia' salvata non manda niente
    const uguale = quale === salvata && (quale !== ALTRO_NOME || pulito === nomeSalvato)
    if (uguale || (quale === ALTRO_NOME && pulito === "")) return onRisposta(scheda.key, null)
    if (quale === NON_OGGETTO) return onRisposta(scheda.key, { key: scheda.key, not_an_object: true })
    onRisposta(
      scheda.key,
      quale === ALTRO_NOME
        ? { key: scheda.key, name: pulito, not_an_object: false }
        : { key: scheda.key, slug: quale, not_an_object: false },
    )
  }

  const gruppo = scheda.group
  const titolo = scheda.name ?? (gruppo?.night ? notte(gruppo.night) : t("review.objects.unnamed"))
  const voce = (c: Scheda["candidates"][number]) => (c.common_name ? `${c.name} - ${c.common_name}` : c.name)
  const durata = [
    scheda.integration_s > 0 && t("review.objects.hours", { h: ore(scheda.integration_s) }),
    scheda.untimed > 0 && t("review.objects.untimed", { n: numero(scheda.untimed) }),
  ]
    .filter(Boolean)
    .join(" \u00b7 ")
  // Cio' che vale adesso: la risposta in mano, o quella salvata. Una scelta a meta' non e' una risposta.
  const detta = risposta
    ? risposta.not_an_object
      ? t("review.objects.none")
      : (risposta.name ?? scheda.candidates.find((c) => c.slug === risposta.slug)?.name ?? "")
    : scheda.answer
      ? scheda.answer.kind === "none"
        ? t("review.objects.none")
        : (scheda.answer.name ?? "")
      : null
  // La chiave di un gruppo porta spazi e virgolette: un id valido si fa col posto in elenco.
  const idNome = `oggetto-nome-${indice}`

  return (
    <Domanda
      id={`objects:${scheda.key}`}
      voce={titolo}
      nome={scheda.name ? <span className="as-nome-oggetto">{scheda.name}</span> : titolo}
      frames={scheda.frames}
      accanto={durata || undefined}
      salvata={scheda.answer !== null}
      inMano={risposta !== undefined}
      era={scheda.answer ? (scheda.answer.kind === "none" ? t("review.objects.none") : (scheda.answer.name ?? undefined)) : undefined}
      breve={
        detta !== null ? (
          <b>{detta}</b>
        ) : (
          [...scheda.candidates.map((c) => c.name), t("review.objects.other"), t("review.objects.none")].join(" \u00b7 ")
        )
      }
      prova={
        gruppo
          ? [
              // la notte fa gia' da titolo: si scrive qui solo quando manca
              ...(gruppo.night ? [] : [{ nome: t("review.proof.night"), dato: t("review.unknown.f") }]),
              {
                nome: t("review.proof.gear"),
                dato: [gruppo.camera, gruppo.telescope].filter(Boolean).join(" \u00b7 ") || t("review.unknown.mp"),
              },
              {
                nome: t("review.proof.pointing"),
                dato: gruppo.ra_deg !== null && gruppo.dec_deg !== null ? cielo(gruppo.ra_deg, gruppo.dec_deg) : t("review.unknown.m"),
              },
              {
                nome: t("review.proof.span"),
                // L'ora e' gia' quella del posto: si legge dalla stringa, senza passare dal fuso di chi guarda.
                dato:
                  gruppo.first_frame && gruppo.last_frame
                    ? `${oraDelSito(gruppo.first_frame)} - ${oraDelSito(gruppo.last_frame)}`
                    : t("review.unknown.mp"),
              },
              ...(scheda.candidates.length === 0 ? [{ nome: t("review.proof.inField"), dato: t("review.objects.noCandidates") }] : []),
            ]
          : []
      }
    >
      <Scelte
        domanda={t("review.objects.question", { nome: titolo })}
        nome={`oggetto-${scheda.key}`}
        opzioni={[
          ...scheda.candidates.map((c) => ({
            valore: c.slug,
            etichetta: voce(c),
            sub: t(c.in_frame === null ? "review.objects.frame.unknown" : c.in_frame ? "review.objects.frame.in" : "review.objects.frame.out"),
          })),
          { valore: ALTRO_NOME, etichetta: t("review.objects.other") },
          { valore: NON_OGGETTO, etichetta: t("review.objects.none"), sub: t("review.objects.none.why") },
        ]}
        scelta={scelta}
        onScelta={(quale) => manda(quale, scritto)}
      >
        {scelta === ALTRO_NOME && (
          <Campo id={idNome} etichetta={t("review.objects.name")}>
            <input
              className="as-campo-modulo__input"
              id={idNome}
              value={scritto}
              onChange={(e) => manda(ALTRO_NOME, e.target.value)}
            />
          </Campo>
        )}
      </Scelte>
    </Domanda>
  )
}
