import { Fragment, type ReactNode, createContext, useContext } from "react"

import { gesto } from "./componenti/gesto"
import { type OpzioneScelta, PillolaScelta } from "./componenti/PillolaScelta"
import {
  FormatoConf,
  MISURE,
  PillolaDi,
  type StatoParte,
  type StatoRisposta,
} from "./ConfermareGuscio"
import { notte, nottiPerMese, numero, oreEMinuti, t } from "./i18n"

/**
 * Quale domanda e' aperta: **una sola in tutta la pagina**. Lo tiene la pagina e lo leggono le
 * domande e le sezioni, senza passarlo di mano in mano per cinque file.
 */
export const DomandaAperta = createContext<{ aperta: string | null; apri: (id: string) => void }>({
  aperta: null,
  apri: () => {},
})

/** Sul telefono si vede **un caso alla volta**: quale caso della sezione. `null` sulla pagina larga. */
export const UnCaso = createContext<number | null>(null)

/** Una riga delle prove: la parola, e il dato in una o piu' righe. `tenue` e' cio' che manca. */
export interface Prova {
  nome: string
  righe: readonly ReactNode[]
  tenue?: boolean
}

/** La riga dei frame sotto il nome (tavola `frameL`, 246): pannelli, frame, ore, senza durata. */
export function rigaDeiFrame(
  frames: number,
  secondi = 0,
  senzaDurata = 0,
  pannelli?: number,
): string {
  return [
    pannelli !== undefined && t("review.mosaics.panels", { n: numero(pannelli) }),
    t("review.frames", { n: numero(frames) }),
    secondi > 0 && oreEMinuti(secondi),
    senzaDurata > 0 && t("review.objects.untimed", { n: numero(senzaDurata) }),
  ]
    .filter(Boolean)
    .join(" \u00b7 ")
}

/** Le notti nelle prove: una si scrive intera, di piu' una riga per mese (`ago 2025: 12, 13`). */
export function righeDelleNotti(notti: readonly string[]): string[] {
  if (notti.length === 1 && notti[0] !== undefined) return [notte(notti[0])]
  return nottiPerMese(notti).map((m) => `${m.mese}: ${m.giorni}`)
}

/** La durata nelle prove: le ore, e quanti frame non la dicono; `null` se non c'e' niente da dire. */
export function provaDellaDurata(secondi: number, senzaDurata: number): Prova | null {
  if (secondi > 0) {
    const righe = [
      oreEMinuti(secondi),
      senzaDurata > 0 && t("review.objects.untimed", { n: numero(senzaDurata) }),
    ]
    return { nome: t("review.proof.time"), righe: [righe.filter(Boolean).join(" \u00b7 ")] }
  }
  return senzaDurata > 0
    ? { nome: t("review.proof.time"), righe: [t("review.untimed.all")], tenue: true }
    : null
}

/** Il sensore come si legge nelle prove: lati in px, poi il pixel; `null` se i file non lo dicono. */
export function sensore(
  larghi: number | null,
  alti: number | null,
  pixel: number | null,
): string | null {
  if (larghi === null || alti === null) return null
  return [
    `${numero(larghi)} \u00d7 ${numero(alti)} px`,
    pixel !== null && `${numero(pixel)} \u00b5m`,
  ]
    .filter(Boolean)
    .join(" \u00b7 ")
}

/** Una voce di una scelta a risposta: la parola, cosa comporta, se e' scelta, se si puo' scegliere. */
export const voce = (
  sel: boolean,
  l: string,
  on: () => void,
  sub?: string,
  no?: boolean,
): OpzioneScelta => ({
  l,
  sel,
  on,
  ...(sub ? { sub } : {}),
  ...(no ? { no } : {}),
})

const STATI: Record<
  StatoRisposta,
  "review.state.open" | "review.state.inHand" | "review.state.saved" | "review.state.changed"
> = {
  dare: "review.state.open",
  ora: "review.state.inHand",
  salvata: "review.state.saved",
  cambiata: "review.state.changed",
}

/**
 * Una domanda di *Da confermare* (tavola v82, 51-65): **chiusa** e' una riga (di cosa si parla,
 * la risposta in breve, lo stato, il gesto che la apre); **aperta** e' la scheda con le prove e le
 * parti.
 *
 * - **I controlli esistono solo da aperta**: cio' che la sezione tiene in mano vive nella sezione.
 * - **Il gesto dice di quale riga**: a vista tutti i bottoni si chiamano "Rispondi" o "Cambia".
 */
export function Domanda({
  id,
  voce: chi,
  nome,
  frame,
  prova = [],
  stato,
  era,
  breve,
  detta,
  children,
}: {
  /** Quale domanda e', in tutta la pagina: `sezione:chiave`. */
  id: string
  /** Il nome a parole, per chi ascolta e per il gesto. */
  voce: string
  nome: ReactNode
  /** La riga sotto il nome: `rigaDeiFrame`. */
  frame: string
  prova?: readonly Prova[]
  stato: StatoRisposta
  /** Cosa c'era prima, se la risposta salvata cambia. */
  era?: string | undefined
  /** La risposta in breve, o fra cosa si sceglie. */
  breve: string
  /** `breve` e' una risposta, non l'elenco delle scelte. */
  detta: boolean
  children: ReactNode
}) {
  const { aperta, apri } = useContext(DomandaAperta)
  const m = MISURE[useContext(FormatoConf)]
  const pillola = <PillolaDi stato={stato} />
  const eraDetta = stato === "cambiata" && era ? t("review.state.was", { era }) : ""

  if (aperta !== id) {
    const parola = t(stato === "dare" ? "review.answer" : "review.change")
    return (
      <div
        className="al-conf__centro-2"
        style={{ gridTemplateColumns: m.riga, padding: m.rigaDentro }}
      >
        <span className="al-conf__colonna-14">
          {/* lo spazio scritto stacca nome e frame per chi legge il testo: in colonna non si vede */}
          <span className="al-conf__testo-11">{nome}</span>{" "}
          <span className="al-conf__testo-10">{frame}</span>
        </span>
        <span
          className="al-conf__blocco-9"
          style={{ fontWeight: detta ? 600 : 400, color: detta ? "var(--testo)" : "var(--tenue)" }}
        >
          {breve}
        </span>
        <span className="al-conf__colonna-15">
          {pillola}
          {eraDetta && <span className="al-conf__blocco-10">{eraDetta}</span>}
        </span>
        <a
          href="#"
          role="button"
          onClick={gesto(() => apri(id))}
          aria-label={`${parola}: ${chi}`}
          className="al-bottone al-bottone--tenue al-bottone--rovescio al-conf__blocco-11"
        >
          {parola}
        </a>
      </div>
    )
  }
  return (
    <article
      className="al-conf__colonna-16"
      aria-label={`${chi}, ${t(STATI[stato])}`}
      style={{ padding: m.domandaDentro }}
    >
      <div className="al-conf__colonna-17">
        <div className="al-conf__riga-12">
          <h3 className="al-conf__blocco-12" style={{ fontSize: m.titoloDomanda }}>
            {nome}
          </h3>
          {pillola}
          {eraDetta && <span className="al-conf__testo-10">{eraDetta}</span>}
        </div>
        <span className="al-conf__testo-7">{frame}</span>
      </div>
      {prova.length > 0 && (
        <dl
          className="al-conf__centro-3"
          style={{ gridTemplateColumns: m.prove, gap: m.proveStacco }}
        >
          {prova.map((p) => (
            <Fragment key={p.nome}>
              <dt className="al-conf__testo-12">{p.nome}</dt>
              <dd
                className="al-conf__colonna-18"
                style={{ color: p.tenue ? "var(--tenue)" : "var(--testo)" }}
              >
                {p.righe.map((r, i) => (
                  <span key={i}>{r}</span>
                ))}
              </dd>
            </Fragment>
          ))}
        </dl>
      )}
      {children}
    </article>
  )
}

/** Una parte di una domanda (tavola 56-64): il capo, lo stato se la parte ne ha uno, il resto. */
export function Parte({
  capo,
  prima,
  stato,
  children,
}: {
  capo: string
  /** La prima parte non ha la linea sopra. */
  prima: boolean
  stato?: StatoParte | undefined
  children: ReactNode
}) {
  return (
    <div
      className="al-conf__colonna-19"
      style={{
        paddingTop: prima ? "0" : "16px",
        borderTop: prima ? "0" : "1px solid var(--linea)",
      }}
    >
      <span className="al-conf__riga-13">
        <span className="al-conf__testo-13">{capo}</span>
        {stato && <PillolaDi stato={stato} />}
      </span>
      {children}
    </div>
  )
}

/** Le scelte di una parte, a risposta: il gruppo porta il nome della domanda. */
export function Risposte({
  opzioni,
  etichetta,
  multipla = false,
}: {
  opzioni: OpzioneScelta[]
  etichetta: string
  multipla?: boolean
}) {
  return (
    <PillolaScelta
      forma="risposta"
      opzioni={opzioni}
      etichetta={etichetta}
      formato={useContext(FormatoConf)}
      multipla={multipla}
    />
  )
}

/** Un campo da scrivere di una parte. */
export interface CampoConf {
  id: string
  etichetta: string
  valore: string
  onValore: (v: string) => void
  suggerimento?: string
  aiuto?: string
  /** Un numero: la tastiera dei numeri sul telefono. */
  numerico?: boolean
}

/** I campi di una parte (tavola 60): etichetta sopra, aiuto sotto. */
export function Campi({ campi }: { campi: readonly CampoConf[] }) {
  const m = MISURE[useContext(FormatoConf)]
  return (
    <div className="al-conf__centro-4" style={{ gridTemplateColumns: m.campi }}>
      {campi.map((f) => (
        <div className="al-conf__colonna-17" key={f.id}>
          <label className="al-conf__testo-14" htmlFor={f.id}>
            {f.etichetta}
          </label>
          <input
            id={f.id}
            value={f.valore}
            onChange={(e) => f.onValore(e.target.value)}
            placeholder={f.suggerimento}
            autoComplete="off"
            spellCheck={false}
            inputMode={f.numerico ? "decimal" : undefined}
            className="al-campo al-campo--rovescio al-conf__blocco-13"
          />
          {f.aiuto && <span className="al-conf__testo-10">{f.aiuto}</span>}
        </div>
      ))}
    </div>
  )
}

/** Le scelte che una risposta apre sotto di se' (tavola 62), col loro titolo se ne hanno uno. */
export function Sotto({
  titolo,
  etichetta,
  opzioni,
  multipla = false,
}: {
  titolo?: string
  etichetta: string
  opzioni: OpzioneScelta[]
  multipla?: boolean
}) {
  return (
    <div className="al-conf__colonna-22">
      {titolo && <span className="al-conf__testo-14">{titolo}</span>}
      <Risposte opzioni={opzioni} etichetta={etichetta} multipla={multipla} />
    </div>
  )
}

/** Una nota sotto le scelte (tavola 63). */
export const Nota = ({ children }: { children: ReactNode }) => (
  <span className="al-conf__testo-17" aria-live="polite">
    {children}
  </span>
)
