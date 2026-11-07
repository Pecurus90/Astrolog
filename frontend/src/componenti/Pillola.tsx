import { type Chiave, t } from "../i18n"
import { useTema } from "./Tema"

/** The outcome as the app sends it: 0 good, 1 uncertain, 2 not suitable, or the delivery's word. */
export type Esito =
  | 0
  | 1
  | 2
  | "buona"
  | "buono"
  | "incerta"
  | "non adatta"
  | "no"
  | "mancante"
  | "ignoto"
  | "neutra"
  | "avviso"
  | "spenta"

type Tono = "buona" | "incerta" | "non-adatta" | "mancante" | "neutra" | "avviso" | "spenta"

const TONI: Record<Esito, Tono> = {
  0: "buona",
  1: "incerta",
  2: "non-adatta",
  buona: "buona",
  buono: "buona",
  incerta: "incerta",
  "non adatta": "non-adatta",
  no: "non-adatta",
  mancante: "mancante",
  ignoto: "mancante",
  neutra: "neutra",
  avviso: "avviso",
  spenta: "spenta",
}

// Signs from the delivery's tema.js (SEGNI); neutral, warning and off carry only the given text.
// The round of an uncertain outcome is the warning one; neutral and off have no round class.
const VESTI: Record<Tono, { segno: string; parola?: Chiave; pillola: string; tondo: string }> = {
  buona: {
    segno: "\u2713",
    parola: "ui.outcome.good",
    pillola: "al-pillola al-pillola--buona",
    tondo: "al-segno al-segno--buona",
  },
  incerta: {
    segno: "!",
    parola: "ui.outcome.uncertain",
    pillola: "al-pillola al-pillola--incerta",
    tondo: "al-segno al-segno--avviso",
  },
  "non-adatta": {
    segno: "\u2715",
    parola: "ui.outcome.unsuitable",
    pillola: "al-pillola al-pillola--non-adatta",
    tondo: "al-segno al-segno--non-adatta",
  },
  mancante: {
    segno: "?",
    parola: "ui.outcome.missing",
    pillola: "al-pillola al-pillola--mancante",
    tondo: "al-segno al-segno--mancante",
  },
  neutra: { segno: "", pillola: "al-pillola al-pillola--neutra", tondo: "al-segno" },
  avviso: {
    segno: "",
    pillola: "al-pillola al-pillola--avviso",
    tondo: "al-segno al-segno--avviso",
  },
  spenta: { segno: "", pillola: "al-pillola al-pillola--spenta", tondo: "al-segno" },
}

export type Dimensione = "media" | "piccola" | "minima" | "micro"

const DIMENSIONI: Record<Dimensione, string> = {
  media: "",
  piccola: " al-pillola--piccola",
  minima: " al-pillola--minima",
  micro: " al-pillola--micro",
}

/**
 * The outcome with colour, sign and word (v58 `Pillola`): it shows, never judges. `forma="segno"`
 * is the round alone, aria-hidden, beside a text that already says it.
 */
export function Pillola({
  esito = 0,
  testo,
  segno,
  forma = "pillola",
  dimensione = "media",
  fondo = "carta2",
  acapo = false,
  allinea,
  classe,
}: {
  esito?: Esito
  /** The word; without it, the outcome's word from the dictionary. */
  testo?: string
  /** The sign; without it, the outcome's sign. An empty string shows no sign. */
  segno?: string
  forma?: "pillola" | "segno"
  dimensione?: Dimensione
  fondo?: "carta2" | "carta"
  acapo?: boolean
  allinea?: string
  /** A class of the place, from the page's own section of the sheet. */
  classe?: string
}) {
  const { modo, accento } = useTema()
  const veste = VESTI[TONI[esito]]
  const piu = classe ? ` ${classe}` : ""
  const scritto = segno ?? veste.segno
  if (forma === "segno") {
    return (
      <div className="al-c-pillola__blocco-1" data-modo={modo} data-accento={accento}>
        <span
          aria-hidden="true"
          className={`${veste.tondo}${fondo === "carta2" ? " al-segno--carta-2" : ""}${piu}`}
          style={{ alignSelf: allinea }}
        >
          {scritto || "?"}
        </span>
      </div>
    )
  }
  const parola = testo ?? (veste.parola ? t(veste.parola) : "")
  return (
    <div className="al-c-pillola__blocco-1" data-modo={modo} data-accento={accento}>
      <span
        className={`${veste.pillola}${DIMENSIONI[dimensione]}${acapo ? " al-pillola--acapo" : ""}${fondo === "carta" ? " al-pillola--su-carta" : ""}${piu}`}
        style={{
          alignSelf: allinea,
          textAlign: acapo && allinea === "flex-end" ? "right" : undefined,
        }}
      >
        {scritto ? `${scritto} ${parola}` : parola}
      </span>
    </div>
  )
}
