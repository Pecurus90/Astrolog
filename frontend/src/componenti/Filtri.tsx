import { numero, t } from "../i18n"
import { gesto } from "./gesto"
import { type OpzioneScelta, PillolaScelta } from "./PillolaScelta"
import { type Formato, useTema } from "./Tema"

/** A group of criteria: its name and its options, as PillolaScelta takes them. */
export interface GruppoFiltri {
  l: string
  opz: OpzioneScelta[]
}

/**
 * The criteria (v76 `Filtri`) in three parts: `bottone` opens them, `togli` clears them, `corpo`
 * holds search field and groups. Which options combine is the page's, not this.
 */
export function Filtri({
  parte = "corpo",
  gruppi = [],
  colonne = 1,
  campo,
  q = "",
  onCerca,
  attivi = 0,
  aperto = false,
  freccia = true,
  onApri,
  onTogli,
  mostra,
  onMostra,
  altezza,
  rientro = "0",
  formato = "desktop",
}: {
  parte?: "corpo" | "bottone" | "togli"
  gruppi?: GruppoFiltri[]
  /** Columns of the groups on desktop; the phone has one. */
  colonne?: number
  /** Placeholder of the search field; without it there is no field. */
  campo?: string
  q?: string
  onCerca?: (q: string) => void
  /** How many criteria are on, as the page counts them. */
  attivi?: number
  aperto?: boolean
  freccia?: boolean
  onApri?: () => void
  onTogli?: () => void
  /** Phone only: the words of the button that closes and shows the result. */
  mostra?: string
  onMostra?: () => void
  /** Desktop height of the button, a CSS length; 40px without it. */
  altezza?: string
  /** Padding of the body, a CSS value. */
  rientro?: string
  formato?: Formato
}) {
  const { modo, accento } = useTema()
  const telefono = formato === "telefono"
  const alto = telefono ? "44px" : altezza || "40px"
  const spazio = telefono ? "12px" : "14px"
  const etichetta = telefono ? "12px" : "13px"
  const acceso = attivi > 0

  let corpo = null
  if (parte === "bottone") {
    corpo = (
      <a
        className="al-c-filtri__riga-1"
        href="#"
        onClick={gesto(onApri)}
        aria-expanded={aperto ? "true" : "false"}
        style={{
          minHeight: alto,
          background: acceso ? "var(--scelta)" : "var(--carta-2)",
          color: acceso ? "var(--scelta-testo)" : "var(--testo)",
        }}
      >
        {t("ui.filters.criteria")}
        {acceso && (
          <span
            className="al-c-filtri__pillola-1"
            style={{ background: "var(--scelta-testo)", color: "var(--scelta)" }}
          >
            {numero(attivi)}
          </span>
        )}
        {freccia && (
          <span className="al-c-filtri__testo-1" aria-hidden="true">
            {aperto ? "\u25B4" : "\u25BE"}
          </span>
        )}
      </a>
    )
  } else if (parte === "togli") {
    corpo = acceso ? (
      <a
        className="al-c-filtri__riga-3"
        href="#"
        onClick={gesto(onTogli)}
        style={{ minHeight: alto }}
      >
        {t("ui.filters.clear")}
      </a>
    ) : null
  } else {
    corpo = (
      <div className="al-c-filtri__colonna-1" style={{ gap: spazio, padding: rientro }}>
        {campo && (
          <label className="al-c-filtri__colonna-2">
            <span className="al-c-filtri__testo-2" style={{ fontSize: etichetta }}>
              {t("ui.filters.object")}
            </span>
            <input
              value={q}
              onChange={(e) => onCerca?.(e.target.value)}
              placeholder={campo}
              className="al-campo al-campo--tondo al-campo--piccolo al-c-filtri__blocco-2"
            />
          </label>
        )}
        <div
          className="al-c-filtri__centro-1"
          style={{
            gridTemplateColumns: telefono ? "minmax(0,1fr)" : `repeat(${colonne},minmax(0,1fr))`,
            gap: `${spazio} 24px`,
          }}
        >
          {gruppi.map((g) => (
            <div
              key={g.l}
              className="al-c-filtri__colonna-3"
              role="group"
              aria-label={g.l}
              style={{ paddingTop: telefono ? "10px" : "12px" }}
            >
              <span className="al-c-filtri__testo-2" style={{ fontSize: etichetta }}>
                {g.l}
              </span>
              <PillolaScelta opzioni={g.opz} etichetta={g.l} formato={formato} />
            </div>
          ))}
        </div>
        {telefono && mostra && (
          <div className="al-c-filtri__riga-2">
            <a
              href="#"
              onClick={gesto(onMostra)}
              className="al-bottone al-bottone--pieno al-bottone--blocco al-c-filtri__blocco-3"
            >
              {mostra}
            </a>
            {acceso && (
              <a
                href="#"
                onClick={gesto(onTogli)}
                className="al-bottone al-bottone--testo al-bottone--blocco al-bottone--a-sinistra"
              >
                {t("ui.filters.clear")}
              </a>
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    // data-formato: the sheet's phone rules hang from it
    <div
      className="al-c-filtri__blocco-1"
      data-modo={modo}
      data-accento={accento}
      data-formato={formato}
    >
      {corpo}
    </div>
  )
}
