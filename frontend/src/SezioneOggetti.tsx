import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { useContext, useState } from "react"

import { Avviso } from "./componenti/Avviso"
import { gesto } from "./componenti/gesto"
import { FormatoConf, statoDi } from "./ConfermareGuscio"
import {
  Campi,
  Domanda,
  DomandaAperta,
  Parte,
  type Prova,
  Risposte,
  righeDelleNotti,
  rigaDeiFrame,
  voce,
} from "./Domanda"
import { Sezione } from "./Sezione"
import { provaDegliStrumenti } from "./Soggetti"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, cielo, numero, oraDelSito, t } from "./i18n"

type Scheda = components["schemas"]["ObjectCard"]
type Risposta = components["schemas"]["ObjectEdit"]

// Le due risposte che non sono una voce del campo. Una voce si riconosce dalla sua sigla.
const ALTRO_NOME = "nome"
const NON_OGGETTO = "nessuno"

/**
 * **Che oggetto e'**: una scheda per gruppo di frame (ADR 0014, S3; tavola v82, 210-213) -- un
 * oggetto su cui l'app ha un dubbio, o frame che non dicono cosa e' stato ripreso e di cui il
 * plate solving non dice niente.
 *
 * - **Una risposta sola fra tre**: una voce trovata nel campo, un nome scritto, "non e' un oggetto".
 * - **Un nome vuoto non e' una risposta**; ridare la risposta salvata non manda niente.
 * - **Gli oggetti identificati non sono domande**: chiusi in fondo, nell'ordine dell'API (piu' frame prima), 5 e poi 50 alla volta;
 *   si correggono a scheda sotto la riga, e la correzione parte con Applica (tavola 254-260).
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
        <RigaOggetti
          indice={indice}
          scheda={s}
          risposta={risposte[s.key]}
          onRisposta={onRisposta}
        />
      )}
      piede={
        aPosto > 0 && <Identificati quanti={aPosto} risposte={risposte} onRisposta={onRisposta} />
      }
    />
  )
}

// [T] Da confermare.dc.html `ricN` (254-260): 5 in vista, poi 50 alla volta
const PRIMI = 5
const ELENCO = "objects:"
const ALTRI = 50

/** Gli oggetti identificati: si aprono, si correggono, una scheda alla volta. */
function Identificati({
  quanti,
  risposte,
  onRisposta,
}: {
  quanti: number
  risposte: Record<string, Risposta>
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  const formato = useContext(FormatoConf)
  const { aperta, apri } = useContext(DomandaAperta)
  const [chiesti, setChiesti] = useState(false)
  const [quanteVisti, setQuanteVisti] = useState(PRIMI)
  const [corretto, setCorretto] = useState<string | null>(null)
  // Una cosa aperta alla volta: aprire una domanda chiude l'elenco.
  // "objects:" senza chiave: nessuna domanda aperta, ma la sezione e' quella su cui si lavora
  const aperti = chiesti && aperta === ELENCO
  // Sotto la chiave della pagina: l'Applica che la rilegge rilegge anche questi.
  const pagina = useQuery({
    queryKey: ["review", "settled", quanteVisti],
    enabled: aperti,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/review/objects/settled", {
        params: { query: { limit: quanteVisti, offset: 0 } },
      })
      if (error) throw new Error(t("review.settled.failed"))
      return data
    },
    placeholderData: keepPreviousData,
  })
  const dati = pagina.data
  const restano = dati ? dati.total - dati.items.length : 0
  return (
    <div className="al-conf__colonna-23">
      <a
        className="al-conf__riga-15"
        href="#"
        role="button"
        aria-expanded={aperti ? "true" : "false"}
        onClick={gesto(() => {
          setChiesti(!aperti)
          if (!aperti) apri(ELENCO)
        })}
      >
        <span className="al-conf__blocco-15">
          {t("review.settled.count", { n: numero(quanti) })}
        </span>
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d={aperti ? "M6 15l6-6 6 6" : "M6 9l6 6 6-6"} />
        </svg>
      </a>
      {aperti && pagina.error && (
        <Avviso tipo="riga" formato={formato} segno="!" titolo={pagina.error.message} />
      )}
      {aperti && dati && (
        <>
          <ul className="al-conf__colonna-9">
            {dati.items.map((s) => (
              <Identificato
                key={s.key}
                scheda={s}
                aperta={corretto === s.key}
                onApri={() => setCorretto(corretto === s.key ? null : s.key)}
                risposta={risposte[s.key]}
                onRisposta={onRisposta}
              />
            ))}
          </ul>
          {restano > 0 && (
            <a
              href="#"
              role="button"
              onClick={gesto(() => setQuanteVisti(quanteVisti + ALTRI))}
              className="al-bottone al-bottone--tenue al-bottone--rovescio al-bottone--blocco"
            >
              {t("review.settled.more", {
                n: numero(Math.min(ALTRI, restano)),
                di: numero(restano),
              })}
            </a>
          )}
        </>
      )}
    </div>
  )
}

/** Un oggetto identificato: la riga, e sotto la scheda che lo corregge. */
function Identificato({
  scheda,
  aperta,
  onApri,
  risposta,
  onRisposta,
}: {
  scheda: Scheda
  aperta: boolean
  onApri: () => void
  risposta: Risposta | undefined
  onRisposta: (chiave: string, r: Risposta | null) => void
}) {
  const nome = scheda.name ?? scheda.key
  // Il nome scritto e' della riga: un nome a meta' non sta in mano, e il campo non si svuota.
  const [scritto, setScritto] = useState(risposta?.name ?? "")
  const [altro, setAltro] = useState(Boolean(risposta?.name))
  const scelta = risposta?.not_an_object ? NON_OGGETTO : altro ? ALTRO_NOME : null
  const frames = t("review.frames", { n: numero(scheda.frames) })
  const gestoDetto = t(aperta ? "frame.close" : "review.fix")
  const manda = (quale: string | null, nuovo: string) => {
    setAltro(quale === ALTRO_NOME)
    setScritto(nuovo)
    if (quale === NON_OGGETTO)
      return onRisposta(scheda.key, { key: scheda.key, not_an_object: true })
    const pulito = nuovo.trim()
    // il nome di adesso riscritto non e' una correzione
    const nuovoNome = quale === ALTRO_NOME && pulito !== "" && pulito !== nome
    onRisposta(
      scheda.key,
      nuovoNome ? { key: scheda.key, name: pulito, not_an_object: false } : null,
    )
  }
  const titolo = t("review.settled.which", { nome })
  return (
    <>
      <li className="al-conf__riga-16">
        <span className="al-conf__colonna-24">
          <span className="al-conf__testo-18">{nome}</span>
          <span className="al-conf__testo-10">
            {[scheda.common_name, frames].filter(Boolean).join(" \u00b7 ")}
          </span>
        </span>
        <a
          href="#"
          role="button"
          onClick={gesto(onApri)}
          aria-label={`${gestoDetto}: ${nome}`}
          className="al-bottone al-bottone--tenue al-bottone--rovescio al-conf__blocco-16"
        >
          {gestoDetto}
        </a>
      </li>
      {aperta && (
        <li className="al-conf__corr">
          <span className="al-conf__testo-14">{titolo}</span>
          <Risposte
            etichetta={titolo}
            opzioni={[
              voce(
                scelta === null,
                t("review.settled.stays", { nome }),
                () => manda(null, scritto),
                t("review.settled.stays.why"),
              ),
              voce(scelta === ALTRO_NOME, t("review.objects.other"), () =>
                manda(ALTRO_NOME, scritto),
              ),
              voce(
                scelta === NON_OGGETTO,
                t("review.objects.none"),
                () => manda(NON_OGGETTO, scritto),
                t("review.objects.none.why"),
              ),
            ]}
          />
          {scelta === ALTRO_NOME && (
            <input
              value={scritto}
              onChange={(e) => manda(ALTRO_NOME, e.target.value)}
              aria-label={t("review.objects.name")}
              placeholder={t("review.settled.hint")}
              autoComplete="off"
              spellCheck={false}
              className="al-campo al-campo--rovescio al-conf__blocco-13"
            />
          )}
          <span className="al-conf__testo-10">
            {t("review.settled.scope", { n: scheda.frames, frame: frames })}
          </span>
        </li>
      )}
    </>
  )
}

/** Cosa dice una risposta salvata, nella forma di una scelta: una sigla, o una delle due. */
function salvataDi(scheda: Scheda): string | null {
  const data = scheda.answer
  if (!data) return null
  if (data.kind === "none") return NON_OGGETTO
  return data.kind === "catalog" && scheda.candidates.some((c) => c.slug === data.value)
    ? data.value
    : ALTRO_NOME
}

// Come l'app ha deciso, a parole (Marco, 12/11/2026): il metodo, e la fiducia.
const METODI: Partial<Record<NonNullable<Scheda["method"]>, Chiave>> = {
  coord_confirmed: "review.objects.method.sky",
  coord_review: "review.objects.method.sky",
  exact_name: "review.objects.method.name",
  historic_name: "review.objects.method.historic",
}
const FIDUCIE: Partial<Record<NonNullable<Scheda["confidence"]>, Chiave>> = {
  low: "review.objects.confidence.low",
  high: "review.objects.confidence.high",
  certain: "review.objects.confidence.high",
}

/** Le prove di una scheda: perche' l'app dubita di un nome, o cosa si sa dei frame senza nome. */
function proveDi(scheda: Scheda): Prova[] {
  const gruppo = scheda.group
  const campo: Prova[] =
    scheda.candidates.length === 0
      ? [
          {
            nome: t("review.proof.inField"),
            righe: [t(scheda.searched ? "review.objects.notFound" : "review.objects.notSearched")],
            tenue: true,
          },
        ]
      : []
  if (!gruppo) {
    const metodo = scheda.method ? METODI[scheda.method] : undefined
    const fiducia = scheda.confidence ? FIDUCIE[scheda.confidence] : undefined
    const dubbio = [metodo && t(metodo), fiducia && t(fiducia)].filter((x): x is string =>
      Boolean(x),
    )
    return [
      ...campo,
      ...(dubbio.length > 0 ? [{ nome: t("review.proof.doubt"), righe: dubbio }] : []),
      ...(scheda.nights.length > 0
        ? [{ nome: t("review.proof.night"), righe: righeDelleNotti(scheda.nights) }]
        : []),
      ...provaDegliStrumenti(scheda.rigs),
    ]
  }
  const strumenti = [gruppo.camera, gruppo.telescope].filter(Boolean).join(" \u00b7 ")
  const puntamento =
    gruppo.ra_deg !== null && gruppo.dec_deg !== null ? cielo(gruppo.ra_deg, gruppo.dec_deg) : null
  // L'ora e' gia' quella del posto: si legge dalla stringa, senza passare dal fuso di chi guarda.
  // l'intervallo col lineato delle tavole, come in Dashboard; un frame solo, un'ora sola
  const [da, a] = [gruppo.first_frame, gruppo.last_frame].map((x) => (x ? oraDelSito(x) : null))
  const arco = da && a ? (da === a ? da : `${da}\u2013${a}`) : null
  return [
    ...campo,
    gruppo.night
      ? { nome: t("review.proof.night"), righe: righeDelleNotti([gruppo.night]) }
      : { nome: t("review.proof.night"), righe: [t("review.unknown.f")], tenue: true },
    {
      nome: t("review.proof.gear"),
      righe: [strumenti || t("review.unknown.mp")],
      tenue: !strumenti,
    },
    {
      nome: t("review.proof.pointing"),
      righe: [puntamento ?? t("review.unknown.m")],
      tenue: puntamento === null,
    },
    { nome: t("review.proof.span"), righe: [arco ?? t("review.unknown.mp")], tenue: arco === null },
  ]
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
  // La scelta e il nome sono della riga: un nome a meta' non sta nell'accumulo.
  const [scelta, setScelta] = useState<string | null>(
    risposta ? (risposta.not_an_object ? NON_OGGETTO : (risposta.slug ?? ALTRO_NOME)) : salvata,
  )
  const [scritto, setScritto] = useState(risposta?.name ?? nomeSalvato)

  const manda = (quale: string, nome: string) => {
    setScelta(quale)
    setScritto(nome)
    const pulito = nome.trim()
    const uguale = quale === salvata && (quale !== ALTRO_NOME || pulito === nomeSalvato)
    if (uguale || (quale === ALTRO_NOME && pulito === "")) return onRisposta(scheda.key, null)
    if (quale === NON_OGGETTO)
      return onRisposta(scheda.key, { key: scheda.key, not_an_object: true })
    onRisposta(
      scheda.key,
      quale === ALTRO_NOME
        ? { key: scheda.key, name: pulito, not_an_object: false }
        : { key: scheda.key, slug: quale, not_an_object: false },
    )
  }

  const gruppo = scheda.group
  const titolo = scheda.name ?? t("review.objects.unnamed")
  // due gruppi senza nome della stessa notte: chi ascolta li distingue dalla notte e dalla camera
  const chi = gruppo
    ? [titolo, gruppo.night && righeDelleNotti([gruppo.night])[0], gruppo.camera]
        .filter(Boolean)
        .join(", ")
    : titolo
  const etichetta = (c: Scheda["candidates"][number]) =>
    c.common_name ? `${c.name} \u00b7 ${c.common_name}` : c.name
  const nomeDi = (r: Risposta) =>
    r.not_an_object
      ? t("review.objects.none")
      : (r.name ?? scheda.candidates.find((c) => c.slug === r.slug)?.name ?? "")
  const salvataDetta = scheda.answer
    ? scheda.answer.kind === "none"
      ? t("review.objects.none")
      : (scheda.answer.name ?? "")
    : null
  const detta = risposta ? nomeDi(risposta) : salvataDetta
  const alternative = scheda.candidates.length
    ? scheda.candidates.map((c) => c.name)
    : [t("review.objects.other"), t("review.objects.none")]
  const capo = t("review.objects.question", { nome: titolo })

  return (
    <Domanda
      id={`objects:${scheda.key}`}
      voce={chi}
      nome={titolo}
      frame={rigaDeiFrame(scheda.frames, scheda.integration_s, scheda.untimed)}
      stato={statoDi(scheda.answer !== null, risposta !== undefined)}
      era={salvataDetta ?? undefined}
      detta={detta !== null}
      breve={detta ?? alternative.join(" \u00b7 ")}
      prova={proveDi(scheda)}
    >
      <Parte capo={capo} prima>
        <Risposte
          etichetta={capo}
          opzioni={[
            ...scheda.candidates.map((c) =>
              voce(
                scelta === c.slug,
                etichetta(c),
                () => manda(c.slug, scritto),
                t(
                  c.in_frame === null
                    ? "review.objects.frame.unknown"
                    : c.in_frame
                      ? "review.objects.frame.in"
                      : "review.objects.frame.out",
                ),
              ),
            ),
            voce(scelta === ALTRO_NOME, t("review.objects.other"), () =>
              manda(ALTRO_NOME, scritto),
            ),
            voce(
              scelta === NON_OGGETTO,
              t("review.objects.none"),
              () => manda(NON_OGGETTO, scritto),
              t("review.objects.none.why"),
            ),
          ]}
        />
        {scelta === ALTRO_NOME && (
          <Campi
            campi={[
              {
                id: `oggetto-nome-${indice}`,
                etichetta: t("review.objects.name"),
                valore: scritto,
                onValore: (v) => manda(ALTRO_NOME, v),
              },
            ]}
          />
        )}
      </Parte>
    </Domanda>
  )
}
