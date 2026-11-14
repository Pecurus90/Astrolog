import type { CSSProperties, ReactNode } from "react"

import { gesto } from "./gesto"
import { type Formato, useTema } from "./Tema"
import { t } from "../i18n"

/** A warning line under the blocks (`m.righe`): the frames that go back, a merge for good. */
export interface RigaDelModulo {
  segno: string
  testo: string
  avviso: boolean
}

/**
 * Il **Modulo** della consegna (v82 `componenti/Modulo`): titolo, i campi, l'errore, Salva e
 * Annulla col perche' accanto quando Salva e' spento. `dentro` e' quello aperto in una carta, con
 * l'anello nell'accento; senza, quello in testa alla pagina. Sul telefono la riga dei bottoni resta
 * attaccata al fondo mentre si scorre.
 *
 * `blocchi`: i figli sono gia' `BloccoDelModulo` (nome e modello, dati tecnici); senza, un blocco
 * solo senza titolo. `elimina` sta in fondo, sotto i bottoni.
 */
export function Modulo({
  titolo,
  formato,
  dentro = false,
  disco,
  blocchi = false,
  righe = [],
  errore,
  salva,
  onAnnulla,
  perche,
  elimina,
  children,
}: {
  titolo: string
  formato: Formato
  dentro?: boolean
  /** A filter's colour beside the title. */
  disco?: CSSProperties
  blocchi?: boolean
  righe?: RigaDelModulo[]
  /** The refusal, already in words. */
  errore?: string | null
  /** Null: the form only cancels (nothing to save, "aggiungine uno"). */
  salva: { onSalva: () => void; occupato: boolean; spento: boolean } | null
  onAnnulla: () => void
  /** Why Salva is off. */
  perche?: string
  elimina?: ReactNode
  children: ReactNode
}) {
  const { modo, accento } = useTema()
  const tel = formato === "telefono"
  // [T] Attrezzatura.dc.html `modulo` return (295-300): the two contexts and the phone's footer
  const fondo = dentro ? "var(--carta-2)" : "var(--carta)"
  const spento = salva !== null && (salva.spento || salva.occupato)
  return (
    <div className="al-c-modulo__blocco-1" data-modo={modo} data-accento={accento}>
      <section
        className="al-c-modulo__colonna-1"
        role="group"
        aria-label={titolo}
        style={{
          background: fondo,
          borderRadius: dentro ? "20px" : tel ? "24px" : "28px",
          padding: dentro ? (tel ? "16px" : "22px") : tel ? "20px" : "28px",
          boxShadow: dentro ? "inset 0 0 0 2px var(--accento)" : "none",
          colorScheme: modo === "scuro" ? "dark" : "light",
        }}
      >
        <div className="al-c-modulo__riga-1">
          {disco && (
            <span
              className="al-c-modulo__centro-1"
              aria-hidden="true"
              style={{ background: dentro ? "var(--carta)" : "var(--carta-2)" }}
            >
              <span className="al-c-modulo__tondo-1" style={disco} />
            </span>
          )}
          <h2
            className="al-c-modulo__blocco-2"
            style={{ fontSize: dentro ? "17px" : tel ? "24px" : "30px" }}
          >
            {titolo}
          </h2>
        </div>
        <div
          className="al-c-modulo__centro-3"
          style={{ gridTemplateColumns: tel ? "minmax(0,1fr)" : "repeat(2,minmax(0,1fr))" }}
        >
          {blocchi ? (
            children
          ) : (
            <section
              className="al-c-modulo__colonna-4"
              style={{ gridColumn: "1 / -1", background: "transparent", padding: 0 }}
            >
              <div className="al-c-modulo__griglia-1">{children}</div>
            </section>
          )}
        </div>
        {righe.map((r) => (
          <div key={r.testo} className="al-c-modulo__riga-7">
            <span
              className="al-c-modulo__tondo-2"
              aria-hidden="true"
              style={
                r.avviso
                  ? { background: "var(--avviso)", color: "var(--avviso-testo)", border: "0" }
                  : {
                      background: "transparent",
                      color: "var(--testo)",
                      border: "1.5px solid var(--accento)",
                    }
              }
            >
              {r.segno}
            </span>
            <span className="al-c-modulo__blocco-6">{r.testo}</span>
          </div>
        ))}
        {errore && (
          <div className="al-c-modulo__riga-8" role="alert">
            <span className="al-c-modulo__tondo-3" aria-hidden="true">
              !
            </span>
            <span className="al-c-modulo__blocco-6">{errore}</span>
          </div>
        )}
        <div
          className="al-c-modulo__riga-9"
          style={{
            position: tel ? "sticky" : "static",
            background: tel ? `color-mix(in srgb, ${fondo} 92%, transparent)` : "transparent",
            padding: tel ? "10px" : "0",
            margin: tel ? "0 -6px" : "0",
            boxShadow: tel ? "0 8px 24px rgba(0,0,0,.18)" : "none",
          }}
        >
          {salva && (
            <a
              href="#"
              role="button"
              aria-disabled={spento ? "true" : undefined}
              aria-busy={salva.occupato ? "true" : undefined}
              onClick={gesto(() => {
                if (!spento) salva.onSalva()
              })}
              className="al-bottone al-bottone--pieno"
              style={{
                opacity: spento && !salva.occupato ? 0.45 : 1,
                cursor: salva.occupato ? "progress" : spento ? "not-allowed" : "pointer",
              }}
            >
              {salva.occupato && <span className="al-c-modulo__tondo-4" aria-hidden="true" />}
              {t(salva.occupato ? "ui.form.saving" : "ui.form.save")}
            </a>
          )}
          <a
            href="#"
            role="button"
            onClick={gesto(onAnnulla)}
            className="al-bottone al-bottone--contorno"
          >
            {t("ui.form.cancel")}
          </a>
          {perche && (
            <span className="al-c-modulo__blocco-7" aria-live="polite">
              {perche}
            </span>
          )}
        </div>
        {elimina}
      </section>
    </div>
  )
}

/**
 * Un blocco del Modulo col titolo e il riassunto ("3 di 4 scritti"). Sul telefono si piega: aperto
 * il primo, gli altri si aprono toccando il titolo; sul desktop restano aperti (tavola `blocco`).
 */
export function BloccoDelModulo({
  titolo,
  riassunto,
  formato,
  aperto,
  onApri,
  children,
}: {
  titolo: string
  riassunto: string
  formato: Formato
  /** On the phone one block at a time (board `passo`): the form says which. */
  aperto: boolean
  onApri: (si: boolean) => void
  children: ReactNode
}) {
  const fisso = formato !== "telefono"
  const visto = fisso || aperto
  const sotto = "var(--carta)"
  return (
    <section
      className="al-c-modulo__colonna-4"
      style={{
        gridColumn: "auto",
        background: sotto,
        padding: fisso ? "16px 20px 20px" : "4px 16px 16px",
      }}
    >
      <h3 className="al-c-modulo__testo-4">
        <button
          className="al-c-modulo__riga-3"
          type="button"
          aria-expanded={visto ? "true" : "false"}
          onClick={() => onApri(!aperto)}
          disabled={fisso}
          style={{ minHeight: fisso ? "40px" : "44px", cursor: fisso ? "default" : "pointer" }}
        >
          <span className="al-c-modulo__riga-4">
            <span className="al-c-modulo__testo-5">{titolo}</span>
            <span className="al-c-modulo__testo-6">{riassunto}</span>
          </span>
          {!fisso && (
            <svg
              aria-hidden="true"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d={visto ? "M6 15l6-6 6 6" : "M6 9l6 6 6-6"} />
            </svg>
          )}
        </button>
      </h3>
      {visto && <div className="al-c-modulo__griglia-1">{children}</div>}
    </section>
  )
}

/** Un campo del Modulo: l'etichetta col suo controllo; `largo` prende la riga intera. `origine`:
 *  "dai file", "inserito" o "calcolato" accanto all'etichetta. */
export function CampoDelModulo({
  id,
  etichetta,
  largo = false,
  origine,
  children,
}: {
  id: string
  etichetta: string
  largo?: boolean
  origine?: string | undefined
  children: ReactNode
}) {
  return (
    <div className="al-c-modulo__colonna-5" style={{ gridColumn: largo ? "1 / -1" : "auto" }}>
      {etichetta && (
        <span className="al-c-modulo__riga-5">
          <label className="al-c-modulo__testo-1" htmlFor={id} id={`${id}-l`}>
            {etichetta}
          </label>
          {origine && <span className="al-c-modulo__pillola-1">{origine}</span>}
        </span>
      )}
      {children}
    </div>
  )
}

/** Un valore che il Modulo non chiede: lo calcola il backend; senza i dati, cosa manca. */
export function CalcolatoDelModulo({
  id,
  etichetta,
  valore,
  manca,
}: {
  id: string
  etichetta: string
  valore: string | null
  manca: string
}) {
  return (
    <CampoDelModulo id={id} etichetta={etichetta} origine={t("gear.form.computed")}>
      <output
        className="al-c-modulo__riga-6"
        id={id}
        style={
          valore
            ? { fontSize: "16px", color: "var(--testo)", textDecoration: "underline dotted" }
            : { fontSize: "14px", color: "var(--tenue)", textDecoration: "none" }
        }
      >
        {valore ?? manca}
      </output>
    </CampoDelModulo>
  )
}

/** Il campo di testo del Modulo. */
export function TestoDelModulo({
  id,
  valore,
  onValore,
}: {
  id: string
  valore: string
  onValore: (v: string) => void
}) {
  return (
    <input
      id={id}
      value={valore}
      onChange={(e) => onValore(e.target.value)}
      autoComplete="off"
      spellCheck={false}
      className="al-campo al-campo--vuoto al-campo--piena"
    />
  )
}

/** La tendina del Modulo, con la freccia della consegna. */
export function TendinaDelModulo({
  id,
  valore,
  voci,
  onValore,
}: {
  id: string
  valore: string
  voci: { valore: string; l: string }[]
  onValore: (v: string) => void
}) {
  return (
    <div className="al-c-modulo__blocco-4">
      <select
        id={id}
        value={valore}
        onChange={(e) => onValore(e.target.value)}
        className="al-tendina al-tendina--vuoto al-tendina--freccia al-campo--piena"
      >
        {voci.map((v) => (
          <option key={v.valore} value={v.valore}>
            {v.l}
          </option>
        ))}
      </select>
      <svg
        aria-hidden="true"
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="al-tendina__freccia"
      >
        <path d="M6 9l6 6 6-6" />
      </svg>
    </div>
  )
}
