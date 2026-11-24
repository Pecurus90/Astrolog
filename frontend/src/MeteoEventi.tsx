import { type CSSProperties, useState } from "react"

import { gesto } from "./componenti/gesto"
import type { Formato } from "./componenti/Tema"
import { numero, t } from "./i18n"
import type { Sguardo } from "./Meteo"
import type { Notte } from "./MeteoDati"
import { oraDellEvento, type Punto, type RigaDellEvento, rigaDellEvento } from "./MeteoEventiDati"

const SEGNO: Partial<Record<Punto, string>> = {
  go: "\u2713",
  marginal: "!",
  nogo: "\u2715",
  ignoto: "?",
}

/** The dot's look by kind (board `dBg`, `dFg`, `dSh`): a verdict's strong ink with the card's
 *  sign, the unknown neutral, the Sun and the Moon their colour, the rest a grey ring. */
function stileDelPunto(r: RigaDellEvento, tel: boolean): CSSProperties {
  const d = r.esito ? "18px" : "10px"
  const base = { width: d, height: d, ...(tel || r.esito ? {} : { marginTop: "4px" }) }
  switch (r.punto) {
    case "go":
      return { ...base, background: "var(--buono-testo)", color: "var(--carta)" }
    case "marginal":
      return { ...base, background: "var(--incerto-testo)", color: "var(--carta)" }
    case "nogo":
      return { ...base, background: "var(--non-adatto-testo)", color: "var(--carta)" }
    case "ignoto":
      return {
        ...base,
        background: "var(--carta-2)",
        color: "var(--testo)",
        boxShadow: "inset 0 0 0 1.5px var(--linea)",
      }
    case "sole":
      return { ...base, background: "var(--sole)" }
    case "luna":
      return { ...base, background: "var(--luna-linea)" }
    default:
      return { ...base, background: "var(--carta)", boxShadow: "inset 0 0 0 1.5px var(--tenue)" }
  }
}

/** The night's story under the other factors (board v82 `pesa.ev`): every event on the desktop;
 *  on the phone the moments that matter, the whole night a tap away. A tap moves the chart. */
export function RaccontoDellaNotte({
  notte: n,
  formato,
  sguardo: g,
}: {
  notte: Notte
  formato: Formato
  sguardo: Sguardo
}) {
  const tel = formato === "telefono"
  const [tutta, setTutta] = useState(false)
  // the touched event, not its hour: three events at 22:00 light one row (board `hover === e.at`)
  const [toccato, setToccato] = useState<string | null>(null)
  const righe = n.events.map((e) => ({ r: rigaDellEvento(e), i: oraDellEvento(n, e.at) }))
  const contano = righe.filter((x) => x.r.contano)
  const mostrate = tel && !tutta ? contano : righe
  const tot = numero(righe.length)
  const etichetta =
    tel && !tutta
      ? t("meteo.events.lab.key", { n: numero(contano.length), tot })
      : t("meteo.events.lab", { n: tot })
  const elenco = mostrate.map(({ r, i }) => (
    <a
      key={r.chiave}
      className={tel ? "al-meteo__griglia-5" : "al-meteo__griglia-2"}
      role="listitem"
      aria-label={r.aria}
      style={{
        background: toccato === r.chiave && g.ora === i ? "var(--carta-2)" : "transparent",
      }}
      onClick={() => {
        setToccato(r.chiave)
        g.scegliOra(i)
      }}
    >
      <b className={tel ? "al-meteo__testo-30" : "al-meteo__blocco-10"}>{r.ora}</b>
      <span className={tel ? "al-meteo__riga-31" : "al-meteo__riga-13"}>
        <span className={tel ? "al-meteo__strato-4" : "al-meteo__strato-2"} />
        <span className="al-meteo__tondo-1" aria-hidden="true" style={stileDelPunto(r, tel)}>
          {SEGNO[r.punto] ?? ""}
        </span>
      </span>
      <span className="al-meteo__colonna-9">
        <span className="al-meteo__testo-13" style={{ fontWeight: r.esito ? 600 : 500 }}>
          {r.nome}
        </span>
        <span className="al-meteo__testo-14">{r.sotto}</span>
      </span>
    </a>
  ))
  if (!tel) {
    return (
      <>
        <span className="al-meteo__blocco-8">{etichetta}</span>
        <div className="al-meteo__blocco-9">
          <div className="al-meteo__strato-1" role="list">
            {elenco}
          </div>
        </div>
      </>
    )
  }
  return (
    <>
      <span className="al-meteo__blocco-15">{etichetta}</span>
      <div className="al-meteo__colonna-21" role="list">
        {elenco}
      </div>
      <a
        className="al-meteo__riga-32"
        href="#"
        role="button"
        aria-expanded={tutta}
        onClick={gesto(() => setTutta(!tutta))}
      >
        {tutta ? t("meteo.events.key") : t("meteo.events.all", { tot })}
        <span className="al-meteo__testo-31" aria-hidden="true">
          {tutta ? "\u25b4" : "\u25be"}
        </span>
      </a>
    </>
  )
}
