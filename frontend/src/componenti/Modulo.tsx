import type { ReactNode } from "react"

import { gesto } from "./gesto"
import { type Formato, useTema } from "./Tema"
import { t } from "../i18n"

/**
 * Il **Modulo** della consegna (v82 `componenti/Modulo`): titolo, i campi, l'errore, Salva e
 * Annulla col perche' accanto quando Salva e' spento. `dentro` e' quello aperto in una carta, con
 * l'anello nell'accento; senza, quello in testa alla pagina. Sul telefono la riga dei bottoni resta
 * attaccata al fondo mentre si scorre.
 *
 * Qui solo la parte che i moduli di oggi usano (un blocco di campi senza titolo); i tipi a icone e
 * l'Elimina arrivano col modulo di un pezzo (passo 33, Attrezzatura D).
 */
export function Modulo({
  titolo,
  formato,
  dentro = false,
  errore,
  salva,
  onAnnulla,
  perche,
  children,
}: {
  titolo: string
  formato: Formato
  dentro?: boolean
  /** The refusal, already in words. */
  errore?: string | null
  /** Null: the form only cancels (nothing to save, "aggiungine uno"). */
  salva: { onSalva: () => void; occupato: boolean; spento: boolean } | null
  onAnnulla: () => void
  /** Why Salva is off. */
  perche?: string
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
          <section
            className="al-c-modulo__colonna-4"
            style={{ gridColumn: "1 / -1", background: "transparent", padding: 0 }}
          >
            <div className="al-c-modulo__griglia-1">{children}</div>
          </section>
        </div>
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
      </section>
    </div>
  )
}

/** Un campo del Modulo: l'etichetta col suo controllo; `largo` prende la riga intera. */
export function CampoDelModulo({
  id,
  etichetta,
  largo = false,
  children,
}: {
  id: string
  etichetta: string
  largo?: boolean
  children: ReactNode
}) {
  return (
    <div className="al-c-modulo__colonna-5" style={{ gridColumn: largo ? "1 / -1" : "auto" }}>
      {etichetta && (
        <span className="al-c-modulo__riga-5">
          <label className="al-c-modulo__testo-1" htmlFor={id} id={`${id}-l`}>
            {etichetta}
          </label>
        </span>
      )}
      {children}
    </div>
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
