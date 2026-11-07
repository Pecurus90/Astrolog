import type { CSSProperties, MouseEvent, ReactNode } from "react"

import { t } from "../i18n"
import { type Formato, useTema } from "./Tema"

export interface OpzioneScelta {
  /** The word of the option. */
  l: string
  /** Answers only: the line below. */
  sub?: string
  sel?: boolean
  on?: () => void
  /** Pills only: the count beside the word. */
  c?: string
  /** Switched off: shown, not answering. */
  no?: boolean
  /** Pills only: the dot's ground and border, as the caller's filter colour gives them. */
  tinta?: { fondo: string; bordo?: string }
  /** Pills only: the colour of the curve this option draws. */
  linea?: string
  /** Ticks only: the colour of the measure (`--voce-colore`). */
  colore?: string
  /** The name for who listens (the switch's aria-label), or a hint. */
  titolo?: string
  /** Tabs that lead to another page. */
  href?: string
}

export type FormaScelta =
  "pillole" | "segmentato" | "linguette" | "spunta" | "risposta" | "interruttore"

// Classes stay literal in these maps; className={`${...}`} below only lets the sheet guard read it.
const FORME: Record<Exclude<FormaScelta, "interruttore">, string> = {
  pillole: "al-scelta al-scelta--pillole",
  segmentato: "al-scelta al-scelta--segmentato",
  linguette: "al-scelta al-scelta--linguette",
  spunta: "al-scelta al-scelta--spunta",
  risposta: "al-scelta al-scelta--risposta",
}

const FONDI = {
  carta: "",
  carta2: " al-scelta--fondo-carta-2",
  vuoto: " al-scelta--fondo-vuoto",
  protagonista: " al-scelta--su-protagonista",
} as const

interface Voce {
  o: OpzioneScelta
  sel: "true" | "false"
  no: "true" | undefined
  clic: (e: MouseEvent) => void
}

const voce = (o: OpzioneScelta): Voce => {
  const sel = o.sel === true
  const no = o.no === true && !sel
  return {
    o,
    sel: sel ? "true" : "false",
    no: no ? "true" : undefined,
    clic: (e) => {
      if (!o.href) e.preventDefault()
      if (!no) o.on?.()
    },
  }
}

function Tinta({ o, linea = true }: { o: OpzioneScelta; linea?: boolean }) {
  return (
    <>
      {o.tinta && (
        <i
          className="al-scelta__tinta"
          style={{ background: o.tinta.fondo, border: o.tinta.bordo ?? "0" }}
        />
      )}
      {linea && o.linea && <i className="al-scelta__linea" style={{ borderTopColor: o.linea }} />}
    </>
  )
}

/**
 * The choices (v58 `PillolaScelta`): pills, segmented, tabs, ticks, answers, switch. The roles
 * follow the form: pills pressed, segmented tabs selected, `ruolo="radio"` a radiogroup.
 */
export function PillolaScelta({
  opzioni,
  forma = "pillole",
  misura = "normale",
  fondo = "carta",
  scorre = false,
  allinea,
  etichetta,
  ruolo,
  classe,
  formato = "desktop",
}: {
  opzioni: OpzioneScelta[]
  forma?: FormaScelta
  misura?: "normale" | "piccola"
  fondo?: keyof typeof FONDI
  scorre?: boolean
  allinea?: string
  /** The group's name; without it, the dictionary's word. */
  etichetta?: string
  ruolo?: "radio"
  /** A class of the place, from the page's own section of the sheet. */
  classe?: string
  formato?: Formato
}) {
  const { modo, accento } = useTema()
  const nome = etichetta || t("ui.choice")
  const voci = opzioni.map(voce)
  const piu = classe ? ` ${classe}` : ""
  const radio = ruolo === "radio"
  const posto: CSSProperties = { alignSelf: allinea }
  const gruppo =
    forma === "interruttore"
      ? ""
      : `${FORME[forma]}${FONDI[fondo]}${misura === "piccola" ? " al-scelta--piccola" : ""}${scorre ? " al-scelta--scorre" : ""}${piu}`

  let corpo: ReactNode
  if (forma === "interruttore") {
    corpo = voci.map(({ o, sel, no, clic }, i) => (
      <button
        key={i}
        type="button"
        role="switch"
        aria-checked={sel}
        aria-label={o.titolo}
        aria-disabled={no}
        onClick={clic}
        className={classe ? `al-interruttore ${classe}` : "al-interruttore"}
      >
        <span className="al-interruttore__binario" aria-hidden="true">
          <span className="al-interruttore__pomello" />
        </span>
        <span className="al-interruttore__nome">{o.l}</span>
      </button>
    ))
  } else if (forma === "spunta") {
    corpo = (
      <span role="group" aria-label={nome} className={`${gruppo}`}>
        {voci.map(({ o, sel, no, clic }, i) => (
          <a
            key={i}
            href="#"
            role="checkbox"
            aria-checked={sel}
            aria-disabled={no}
            title={o.titolo}
            onClick={clic}
            className="al-scelta__voce"
            style={{ "--voce-colore": o.colore } as CSSProperties}
          >
            <i className="al-scelta__pallino" />
            {o.l}
          </a>
        ))}
      </span>
    )
  } else if (forma === "risposta") {
    corpo = (
      <div role="radiogroup" aria-label={nome} className={`${gruppo}`}>
        {voci.map(({ o, sel, no, clic }, i) => (
          <a
            key={i}
            href="#"
            role="radio"
            aria-checked={sel}
            aria-disabled={no}
            onClick={clic}
            className={o.sub ? "al-scelta__voce al-scelta__voce--con-riga" : "al-scelta__voce"}
          >
            <span aria-hidden="true" className="al-scelta__tondo" />
            <span className="al-scelta__testi">
              <span>{o.l}</span>
              {o.sub && <span className="al-scelta__riga">{o.sub}</span>}
            </span>
          </a>
        ))}
      </div>
    )
  } else if (radio) {
    // segmented, tabs and pills alike: one choice, said as a radiogroup
    corpo = (
      <div role="radiogroup" aria-label={nome} className={`${gruppo}`} style={posto}>
        {voci.map(({ o, sel, no, clic }, i) => (
          <a
            key={i}
            href="#"
            role="radio"
            aria-checked={sel}
            aria-disabled={no}
            title={o.titolo}
            onClick={clic}
            className="al-scelta__voce"
          >
            {forma === "pillole" && <Tinta o={o} linea={false} />}
            {o.l}
            {forma === "pillole" && o.c && <span className="al-scelta__conto">{o.c}</span>}
          </a>
        ))}
      </div>
    )
  } else if (forma === "segmentato" || forma === "linguette") {
    corpo = (
      <span role="tablist" aria-label={nome} className={`${gruppo}`} style={posto}>
        {voci.map(({ o, sel, clic }, i) => (
          <a
            key={i}
            href={o.href ?? "#"}
            role="tab"
            aria-selected={sel}
            title={o.titolo}
            onClick={clic}
            className="al-scelta__voce"
          >
            {o.l}
          </a>
        ))}
      </span>
    )
  } else {
    corpo = (
      <span role="group" aria-label={nome} className={`${gruppo}`}>
        {voci.map(({ o, sel, no, clic }, i) => (
          <a
            key={i}
            href="#"
            onClick={clic}
            aria-pressed={sel}
            aria-disabled={no}
            className="al-scelta__voce"
          >
            <Tinta o={o} />
            {o.l}
            {o.c && <span className="al-scelta__conto">{o.c}</span>}
          </a>
        ))}
      </span>
    )
  }

  return (
    <div
      className="al-c-pillola-scelta__blocco-1"
      data-modo={modo}
      data-accento={accento}
      data-formato={formato}
    >
      {corpo}
    </div>
  )
}
