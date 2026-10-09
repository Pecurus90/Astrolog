import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Campo } from "./Campo"
import { Domanda } from "./Domanda"
import { Scelte } from "./Scelte"
import { Sezione } from "./Sezione"
import { api } from "./api/client"
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
 * - **Gli oggetti a posto non sono domande**: stanno chiusi in fondo, si aprono a pagine, e si
 *   correggono con la stessa scheda, col nome di adesso gia' scelto.
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
      piede={aPosto > 0 && <APosto daIndice={schede.length} quanti={aPosto} risposte={risposte} onRisposta={onRisposta} />}
    />
  )
}

const PER_PAGINA = 20

function APosto({
  quanti,
  daIndice,
  risposte,
  onRisposta,
}: {
  quanti: number
  /** Da dove contano gli id dei campi: dopo le schede di sopra, per non ripeterli. */
  daIndice: number
  risposte: Record<string, Risposta>
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  const [aperti, setAperti] = useState(false)
  const [da, setDa] = useState(0)
  // Sotto la chiave della pagina: l'Applica che la rilegge rilegge anche questi.
  const pagina = useQuery({
    queryKey: ["review", "settled", da],
    enabled: aperti,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/review/objects/settled", {
        params: { query: { limit: PER_PAGINA, offset: da } },
      })
      if (error) throw new Error(t("review.settled.failed"))
      return data
    },
    placeholderData: keepPreviousData,
  })
  const dati = pagina.data
  return (
    <>
      <div className={aperti ? "as-conferma-aposto as-conferma-aposto--aperto" : "as-conferma-aposto"}>
        <p>
          <b>{numero(quanti)}</b> {t("review.objects.settled", { n: quanti })}
        </p>
        {aperti ? (
          <Bottone piccolo verso="nudo" onClick={() => setAperti(false)}>
            {t("frame.close")}
          </Bottone>
        ) : (
          <Bottone piccolo onClick={() => setAperti(true)}>
            {t("review.settled.open")}
          </Bottone>
        )}
      </div>
      {aperti && pagina.error && <Avviso esito="allarme">{pagina.error.message}</Avviso>}
      {aperti && dati && (
        <>
          {dati.items.map((s, i) => (
            <RigaOggetti aPosto indice={daIndice + i} key={s.key} scheda={s} risposta={risposte[s.key]} onRisposta={onRisposta} />
          ))}
          <div className="as-conferma-pagine">
            <p className="as-conferma-pagine__dove">
              {t("review.settled.range", {
                da: numero(dati.offset + 1),
                a: numero(dati.offset + dati.items.length),
                n: numero(dati.total),
              })}
            </p>
            <Bottone disabled={da === 0} piccolo onClick={() => setDa(Math.max(0, da - PER_PAGINA))}>
              {t("review.settled.before")}
            </Bottone>
            <Bottone disabled={da + PER_PAGINA >= dati.total} piccolo onClick={() => setDa(da + PER_PAGINA)}>
              {t("review.settled.after")}
            </Bottone>
          </div>
        </>
      )}
    </>
  )
}

/**
 * Cosa dice una risposta salvata, nella stessa forma di una scelta: una sigla, o una delle due.
 * Una sigla che non e' fra le voci del campo e' stata scritta in "Altro nome": il catalogo
 * l'ha riconosciuta, ma la scelta da mostrare resta il nome.
 */
function salvataDi(scheda: Scheda, aPosto: boolean): string | null {
  // Un oggetto a posto non ha risposta: cio' che vale e' il nome che l'app gli ha dato. Senza
  // sigla (una cometa, un nome scritto) quel nome sta nel campo di "Altro nome".
  if (aPosto) return scheda.slug ?? (scheda.name ? ALTRO_NOME : null)
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
  aPosto = false,
}: {
  indice: number
  scheda: Scheda
  /** Un oggetto che l'app riconosce da sola: si corregge, non si risponde. */
  aPosto?: boolean
  risposta: Risposta | undefined
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  const salvata = salvataDi(scheda, aPosto)
  const nomeSalvato = salvata === ALTRO_NOME ? (scheda.answer?.name ?? (aPosto ? scheda.name : null) ?? "") : ""
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
  // Un oggetto a posto non ripete il suo nome: e' gia' il titolo della riga.
  const detta = risposta
    ? risposta.not_an_object
      ? t("review.objects.none")
      : (risposta.name ?? scheda.candidates.find((c) => c.slug === risposta.slug)?.name ?? "")
    : scheda.answer
      ? scheda.answer.kind === "none"
        ? t("review.objects.none")
        : (scheda.answer.name ?? "")
      : aPosto
        ? ""
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
      aPosto={aPosto}
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
          ...(aPosto && scheda.slug ? [{ valore: scheda.slug, etichetta: scheda.name ?? scheda.slug }] : []),
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
