import { TempoDellePose } from "./TempoDellePose"
import type { components } from "./api/schema"

type Filtro = components["schemas"]["FilterUsed"]

/**
 * **Con che filtri hai ripreso, e quanto**: la fila delle pastiglie, col nome che tu hai dato a
 * ognuno e le sue ore, quando le pose le dicono.
 *
 * - **Il colore viene dalla banda, non dal nome.** Il nome lo sceglie chi ha scritto il file o
 *   l'utente (`Lum`, `H`, `Ha 3nm`) e a una macchina non dice niente; la banda canonica e' un
 *   dominio chiuso che il backend ha gia' deciso. Leggere il colore dal nome vorrebbe dire
 *   indovinare, e sbagliare sul filtro di chiunque non scriva come Marco.
 * - **La variante sta sulla voce, non su un involucro dentro.** E' il foglio a imporlo: i quattro
 *   slot di colore si risolvono **sullo stesso elemento** che porta la classe, e su un contenitore
 *   i figli erediterebbero il grigio gia' sostituito. Dentro ci va la sola pastiglia.
 * - **E' un mattone** perche' la stessa fila sta nell'Archivio e stara' nelle Notti: le sue classi
 *   si scrivono qui dentro e basta (`tools/controlli_veste.py`, `MATTONI`).
 * - **Una banda che non conosciamo non sparisce**: prende la forma "ignoto", che e' un'informazione
 *   -- hai ripreso con qualcosa, e l'app non sa cosa.
 */

/** Dalla banda canonica alla variante che il foglio disegna, **una per una**: il foglio ne ha una
 *  per banda, coi suoi colori, e accorparne due (le `OSC*`, le `DUO_*`) vuol dire dare a un filtro
 *  il colore di un altro. Scritte per esteso perche' una classe composta a pezzi nessuna guardia
 *  la vede; che qui ci sia ogni banda del vocabolario **e che ogni classe esista nel foglio** lo
 *  prova `frontend/tests/filtri-usati.test.ts`. */
export const VARIANTE: Record<string, string> = {
  L: "as-filtro--l",
  R: "as-filtro--r",
  G: "as-filtro--g",
  B: "as-filtro--b",
  HA: "as-filtro--ha",
  HB: "as-filtro--hb",
  OIII: "as-filtro--oiii",
  SII: "as-filtro--sii",
  DUO_HAOIII: "as-filtro--duo-haoiii",
  DUO_SIIOIII: "as-filtro--duo-siioiii",
  TRI_NB: "as-filtro--tri-nb",
  MULTI_NB: "as-filtro--multi-nb",
  OSC: "as-filtro--osc",
  OSC_LP: "as-filtro--osc-lp",
  OSC_UVIR: "as-filtro--osc-uvir",
  NONE: "as-filtro--nessuno",
  UNKNOWN: "as-filtro--ignoto",
}

export function FiltriUsati({ filtri, etichetta }: { filtri: Filtro[]; etichetta: string }) {
  if (filtri.length === 0) return null
  return (
    <ul className="as-ore-filtro" aria-label={etichetta}>
      {filtri.map((f) => (
        <li
          key={f.name}
          className={`as-ore-filtro__voce ${VARIANTE[f.passband] ?? "as-filtro--ignoto"}`}
        >
          {/* La pastiglia e' il **colore**, e il colore da solo non dice mai niente (WCAG 1.4.1):
              accanto c'e' sempre il nome, che e' la forma. */}
          <span className="as-filtro__pastiglia" aria-hidden="true" />
          <span className="as-ore-filtro__nome">{f.name}</span>
          {f.integration_s > 0 && (
            <span className="as-ore-filtro__ore">
              <TempoDellePose secondi={f.integration_s} senzaTempo={0} />
            </span>
          )}
        </li>
      ))}
    </ul>
  )
}
