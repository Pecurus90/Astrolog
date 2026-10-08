import type { CSSProperties } from "react"

import type { components } from "./api/schema"
import { numero, ore, t } from "./i18n"

type Filtro = components["schemas"]["FilterUsed"]

/**
 * **Con che filtri hai ripreso, e quanto**: la fila delle pastiglie dell'Archivio e la barra delle
 * Notti, col nome che tu hai dato a ognuno e le sue ore, quando le pose le dicono.
 *
 * - **Il colore viene dalla banda, non dal nome.** Il nome lo sceglie chi ha scritto il file o
 *   l'utente (`Lum`, `H`, `Ha 3nm`) e a una macchina non dice niente; la banda canonica e' un
 *   dominio chiuso che il backend ha gia' deciso. Leggere il colore dal nome vorrebbe dire
 *   indovinare, e sbagliare sul filtro di chiunque non scriva come Marco.
 * - **L'ordine e' del backend**, uno in tutta l'app (`vocab/filters.DISPLAY_ORDER`): qui non si
 *   riordina niente.
 * - **E' un mattone** perche' gli stessi colori stanno nell'Archivio e nelle Notti: le sue classi
 *   si scrivono qui dentro e basta (`tools/controlli_veste.py`, `MATTONI`).
 * - **Una banda che non conosciamo non sparisce**: prende il tratteggio dell'ignoto, che e'
 *   un'informazione -- hai ripreso con qualcosa, e l'app non sa cosa.
 */

/** Dalla banda canonica alla variante che il foglio disegna (v30, `65-filtri`): **una per banda**,
 *  e le bande con piu' righe sono le strisce delle loro righe. Accorparne due darebbe a un filtro
 *  il colore di un altro, e due pezzi affiancati della barra si confonderebbero. Scritte per esteso
 *  perche' una classe composta a pezzi nessuna guardia la vede; che qui ci sia ogni banda del
 *  vocabolario **e che ogni classe esista nel foglio** lo prova `frontend/tests/filtri-usati.test.ts`. */
export const VARIANTE: Record<string, string> = {
  L: "as-filtro--l",
  R: "as-filtro--r",
  G: "as-filtro--g",
  B: "as-filtro--b",
  HA: "as-filtro--ha",
  HB: "as-filtro--hb",
  OIII: "as-filtro--oiii",
  SII: "as-filtro--sii",
  DUO_HAOIII: "as-filtro--ha-oiii",
  DUO_SIIOIII: "as-filtro--sii-oiii",
  TRI_NB: "as-filtro--tri",
  MULTI_NB: "as-filtro--quad",
  OSC: "as-filtro--colori",
  OSC_LP: "as-filtro--colori-lp",
  OSC_UVIR: "as-filtro--colori-uvir",
  NONE: "as-filtro--senza",
  UNKNOWN: "as-filtro--ignoto",
}

/** Cosa dice un filtro nella legenda: frame, e ore se le pose le dicono. */
function quanto(f: Filtro): string {
  const frame = numero(f.frames)
  return f.integration_s > 0
    ? t("filters.legend.timed", { n: frame, h: ore(f.integration_s) })
    : t("filters.legend.untimed", { n: frame })
}

/**
 * La barra dei filtri di una notte (v29): ogni pezzo pesa le sue ore, e la legenda sotto ne dice
 * nome, frame e ore. In una notte senza tempo pesano i frame (`perFrame`): e' la sola misura che
 * c'e', e il foglio lo prevede.
 */
export function BarraDeiFiltri({ filtri, perFrame }: { filtri: Filtro[]; perFrame: boolean }) {
  if (filtri.length === 0) return <p>{t("filters.none")}</p>
  const detto = filtri.map((f) => `${f.name} ${quanto(f)}`).join(", ")
  return (
    <div className="as-filtri">
      <p className="as-filtri__barra" role="img" aria-label={t("filters.bar", { filtri: detto })}>
        {filtri.map((f) => (
          <i
            key={f.name}
            className={VARIANTE[f.passband] ?? "as-filtro--ignoto"}
            style={{ "--peso": perFrame ? f.frames : f.integration_s } as CSSProperties}
          />
        ))}
      </p>
      <ul className="as-filtri__legenda">
        {filtri.map((f) => (
          <li key={f.name} className="as-filtri__voce">
            <i className={`as-filtri__pallino ${VARIANTE[f.passband] ?? "as-filtro--ignoto"}`} aria-hidden="true" />
            <b>{f.name}</b>
            <span>{quanto(f)}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
