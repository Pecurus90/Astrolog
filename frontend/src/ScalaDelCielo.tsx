import { useId, useRef } from "react"

import { numero, t } from "./i18n"

/**
 * **Che cielo hai**: le nove classi di Bortle, scelte guardando cosa ci si vede.
 *
 * Esiste come mattone perche' la stessa scala compare in **tre posti** -- il primo avvio dove si
 * sceglie, la scheda del luogo dove si corregge, la barra dove si legge e basta -- e il foglio lo
 * dice da se'. Adesso ci sono tutti e tre, e montano questo: le tre mappe di tinte qui sotto
 * sono i tre nomi che il foglio da' alla stessa rampa.
 *
 * Vincoli non ovvi:
 *
 * - **Il colore non dice mai da solo che classe e'** (WCAG 2.2, 1.4.1): la fascia colorata e'
 *   decorazione e non si sente, la cifra e' sempre scritta, e i due estremi stanno **a parole**
 *   sotto la scala. Chi non distingue il ciano dal rosa legge lo stesso da che parte si va.
 * - **Nove radio veri**: il foglio aggancia la veste a `:has(input:checked)`, e un gruppo di
 *   radio si attraversa con un tasto e si sceglie con le frecce.
 * - **Le frecce non girano**: dal centro citta' non si salta al buio pieno con un tasto. La scala
 *   ha due estremi veri, e un giro li nasconderebbe.
 * - **Senza scelta nessuna classe e' scelta.** Partire dalla 1 dichiarerebbe un cielo eccellente
 *   a chi non ha risposto -- e quel numero e' esattamente cio' che finisce nel database.
 * - **La classe non e' un dato che si salva**: l'app salva la luminosita' con la sua provenienza
 *   (`docs/domini/sito.md`), e la classe si deriva. Qui si sceglie, e basta.
 */

/** Le nove classi, nell'ordine in cui si leggono. Non e' un intervallo calcolato: e' la scala. */
export const CLASSI = [1, 2, 3, 4, 5, 6, 7, 8, 9] as const

// La tinta di ogni classe **ce l'ha il foglio**, una classe per fascia: la rampa e' sua, e
// scriverla qui vorrebbe dire due verita' sullo stesso colore. Scritte per esteso e non composte
// (`as-bortle-scegli__voce--${n}`) perche' un nome costruito a pezzi la guardia delle classi non lo sa
// leggere: il giorno che il design ne rinomina una, un nome per esteso e' rosso e uno costruito no.
const TINTE: Record<ClasseDiCielo, string> = {
  1: "as-bortle-scegli__voce--1",
  2: "as-bortle-scegli__voce--2",
  3: "as-bortle-scegli__voce--3",
  4: "as-bortle-scegli__voce--4",
  5: "as-bortle-scegli__voce--5",
  6: "as-bortle-scegli__voce--6",
  7: "as-bortle-scegli__voce--7",
  8: "as-bortle-scegli__voce--8",
  9: "as-bortle-scegli__voce--9",
}

// Le stesse nove tinte per la **terza forma**, quella del piede della barra: il foglio le mappa
// tutte e tre (`.as-bortle-scegli__voce--N, .as-bortle-letta__fascia--N, .as-bortle-scala__voce--N`) ma
// i nomi sono diversi, e per la guardia delle classi vanno scritti per esteso come sopra.
export const TINTE_IN_BARRA: Record<ClasseDiCielo, string> = {
  1: "as-bortle-scala__voce--1",
  2: "as-bortle-scala__voce--2",
  3: "as-bortle-scala__voce--3",
  4: "as-bortle-scala__voce--4",
  5: "as-bortle-scala__voce--5",
  6: "as-bortle-scala__voce--6",
  7: "as-bortle-scala__voce--7",
  8: "as-bortle-scala__voce--8",
  9: "as-bortle-scala__voce--9",
}

// E le stesse nove per la forma **compatta**, quella della scheda del luogo: una fascia sola
// accanto alla classe e alla misura. Scritte per esteso come le altre, per la guardia.
const TINTE_LETTE: Record<ClasseDiCielo, string> = {
  1: "as-bortle-letta__fascia--1",
  2: "as-bortle-letta__fascia--2",
  3: "as-bortle-letta__fascia--3",
  4: "as-bortle-letta__fascia--4",
  5: "as-bortle-letta__fascia--5",
  6: "as-bortle-letta__fascia--6",
  7: "as-bortle-letta__fascia--7",
  8: "as-bortle-letta__fascia--8",
  9: "as-bortle-letta__fascia--9",
}

export type ClasseDiCielo = (typeof CLASSI)[number]

/** Il cielo di un posto **letto e basta**, nella forma compatta: la fascia, la classe e la misura.
 *
 * Sta qui e non nella pagina che la mostra perche' e' la terza forma della stessa scala, e le sue
 * nove tinte sono due righe sopra: divisa in due file, la classe e il colore avrebbero due case.
 *
 * - **La misura c'e'**, ed e' la regola: la conversione classe/luminosita' e' una convenzione, e
 *   la sola classe la farebbe passare per legge. Il piede della barra e il primo avvio sono le
 *   **due eccezioni** che il foglio dichiara, non il contrario.
 * - **Un cielo mai dichiarato non e' uno zero**, e si legge lo stesso. */
export function CieloLetto({ bortle, sqm }: { bortle: number | null; sqm: number | null }) {
  if (bortle === null || sqm === null) {
    return (
      <span className="as-bortle-letta">
        <span
          aria-hidden="true"
          className="as-bortle-letta__fascia as-bortle-letta__fascia--ignota"
        />
        {t("site.sky")} <span className="as-dato as-dato--ignoto">{t("site.sky.none")}</span>
      </span>
    )
  }
  return (
    <span className="as-bortle-letta">
      <span
        aria-hidden="true"
        className={["as-bortle-letta__fascia", TINTE_LETTE[bortle as ClasseDiCielo]].join(" ")}
      />
      {t("site.sky")}{" "}
      <span className="as-bortle-letta__classe">{t("site.bortle", { n: bortle })}</span>{" "}
      <span className="as-bortle-letta__misura">({numero(sqm)})</span>
    </span>
  )
}

/** Il nome corto di una classe: `cielo di periferia`.
 *
 * La chiave si **compone**, e non serve nessun cast: TypeScript legge il template su un numero
 * che e' l'unione dei nove, ne fa l'unione delle nove chiavi, e se una sparisce dai dizionari
 * non compila piu'. Misurato togliendo `sky.5` da tutte e due le lingue: `TS2345`. Due mappe da
 * nove voci scritte per esteso sarebbero state diciotto righe che non difendono niente. */
export function nomeDelCielo(classe: ClasseDiCielo): string {
  return t(`sky.${classe}`)
}

/** Cosa ci si vede con quella classe: e' la riga su cui si sceglie davvero. */
export function cosaSiVede(classe: ClasseDiCielo): string {
  return t(`sky.${classe}.what`)
}

export function ScalaDelCielo({
  scelta,
  onScegli,
}: {
  /** La classe scelta, o niente finche' nessuno ha risposto. */
  scelta?: ClasseDiCielo | undefined
  onScegli: (classe: ClasseDiCielo) => void
}) {
  const voci = useRef<(HTMLInputElement | null)[]>([])
  const gruppo = useId()

  // La fermata del tabulatore: quella scelta, o la prima finche' non si e' scelto niente. Serve
  // un posto dove entrare, e la prima non e' "scelta" -- lo dice `checked`, non il fuoco.
  const fermata = scelta ?? CLASSI[0]

  const conLeFrecce = (e: React.KeyboardEvent, classe: ClasseDiCielo) => {
    const passo = e.key === "ArrowRight" || e.key === "ArrowDown" ? 1 : 0
    const indietro = e.key === "ArrowLeft" || e.key === "ArrowUp" ? -1 : 0
    if (passo === 0 && indietro === 0) return
    const dove = CLASSI.indexOf(classe) + passo + indietro
    // Sempre fermato: da solo, un gruppo di radio gira dall'ultima alla prima.
    e.preventDefault()
    // Fuori dalla scala non si va: la 9 e la 1 sono estremi veri, non un anello.
    if (dove < 0 || dove >= CLASSI.length) return
    onScegli(CLASSI[dove]!)
    voci.current[dove]?.focus()
  }

  return (
    <fieldset className="as-bortle-scegli" role="radiogroup">
      <legend className="as-solo-lettori">{t("sky.scale")}</legend>
      <div className="as-bortle-scegli__scala">
        {CLASSI.map((classe, i) => (
          <label key={classe} className={`as-bortle-scegli__voce ${TINTE[classe]}`}>
            <input
              ref={(nodo) => {
                voci.current[i] = nodo
              }}
              type="radio"
              name={gruppo}
              value={classe}
              checked={scelta === classe}
              // Il nome che si sente e la riga sotto la scala sono la stessa frase del dizionario.
              aria-label={t("sky.chosen", { n: classe, cielo: nomeDelCielo(classe) })}
              tabIndex={fermata === classe ? 0 : -1}
              onChange={() => onScegli(classe)}
              onKeyDown={(e) => conLeFrecce(e, classe)}
            />
            <span className="as-bortle-scegli__cifra">{classe}</span>
            {/* Sul telefono la scala e' una colonna, e il foglio mostra qui il nome e la frase. */}
            <span className="as-bortle-scegli__nome" aria-hidden="true">
              {nomeDelCielo(classe)}
              <span className="as-bortle-scegli__frase">{cosaSiVede(classe)}</span>
            </span>
          </label>
        ))}
      </div>
      {/* Da che parte si va, **scritto**: la rampa da sola lo direbbe col colore soltanto. */}
      <p className="as-bortle-scegli__estremi" aria-hidden="true">
        <span>{t("sky.low")}</span>
        <span>{t("sky.high")}</span>
      </p>
      {scelta === undefined ? (
        <p className="as-bortle-scegli__letta as-bortle-scegli__letta--niente" aria-live="polite">{t("sky.noneChosen")}</p>
      ) : (
        <p className="as-bortle-scegli__letta" aria-live="polite">
          <b>{t("sky.chosen", { n: numero(scelta), cielo: nomeDelCielo(scelta) })}</b>
          <span>{cosaSiVede(scelta)}</span>
        </p>
      )}
    </fieldset>
  )
}
