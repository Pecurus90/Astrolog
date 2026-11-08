import { type KeyboardEvent, type MouseEvent, type ReactNode, useEffect, useRef } from "react"

import { t } from "../i18n"
import { type Formato, useTema } from "./Tema"

export type Larghezza = "stretta" | "media" | "larga" | "schermo"

// The sheet dresses only narrow and full screen; medium and wide keep the panel's own measure.
const PANNELLI: Record<Larghezza, string> = {
  stretta: "al-finestra__pannello al-finestra__pannello--stretta",
  media: "al-finestra__pannello",
  larga: "al-finestra__pannello",
  schermo: "al-finestra__pannello al-finestra__pannello--schermo",
}

const DENTRO =
  "a[href],button:not([disabled]),input:not([disabled]),select,textarea,[tabindex]:not([tabindex='-1'])"

/** Tab turns among the window's controls and never slips behind the veil. */
export function trattieni(e: KeyboardEvent<HTMLDivElement>): void {
  if (e.key !== "Tab") return
  const voci = [...e.currentTarget.querySelectorAll<HTMLElement>(DENTRO)]
  const primo = voci[0]
  const ultimo = voci[voci.length - 1]
  if (!primo || !ultimo) {
    e.preventDefault()
    return
  }
  const qui = document.activeElement
  if (e.shiftKey && (qui === primo || qui === e.currentTarget)) {
    e.preventDefault()
    ultimo.focus()
  } else if (!e.shiftKey && qui === ultimo) {
    e.preventDefault()
    primo.focus()
  }
}

/**
 * A window above the page (v58 `Finestra`): title, x, body, actions in `al-finestra__gesti`. Esc,
 * the x or a click on the veil close it; the focus goes in on opening, turns inside, and goes
 * back where it was on closing. On the phone it is a sheet from the bottom, by the sheet alone.
 */
export function Finestra({
  titolo,
  segno,
  sottotitolo,
  larghezza = "media",
  fondo = "telaio",
  posizione = "fissa",
  testa = true,
  formato = "desktop",
  onChiudi,
  children,
}: {
  /** The window's name; without a head it is still the dialog's name for who listens. */
  titolo: string
  segno?: "!" | "?"
  sottotitolo?: string
  larghezza?: Larghezza
  fondo?: "telaio" | "carta"
  posizione?: "fissa" | "dentro"
  /** False: no title nor x, the page brings its own head. */
  testa?: boolean
  formato?: Formato
  onChiudi: () => void
  children: ReactNode
}) {
  const { modo, accento } = useTema()
  const pannello = useRef<HTMLDivElement>(null)
  // a new onChiudi each render must not pull the focus back to the panel
  const chiusura = useRef(onChiudi)
  useEffect(() => {
    chiusura.current = onChiudi
  }, [onChiudi])

  useEffect(() => {
    const prima = document.activeElement
    pannello.current?.focus({ preventScroll: true })
    const esc = (e: globalThis.KeyboardEvent) => {
      if (e.key === "Escape") chiusura.current()
    }
    document.addEventListener("keydown", esc)
    return () => {
      document.removeEventListener("keydown", esc)
      if (prima instanceof HTMLElement) prima.focus()
    }
  }, [])

  const chiudi = (e: MouseEvent) => {
    e.preventDefault()
    onChiudi()
  }
  const fuori = (e: MouseEvent) => {
    if (e.target === e.currentTarget) onChiudi()
  }
  const velo = `al-finestra${posizione === "dentro" ? " al-finestra--dentro" : ""}${larghezza === "schermo" ? " al-finestra--schermo" : ""}`

  return (
    <div
      className="al-c-finestra__blocco-1"
      data-modo={modo}
      data-accento={accento}
      data-formato={formato}
    >
      <div className={`${velo}`} onClick={fuori}>
        <div
          ref={pannello}
          role="dialog"
          aria-modal="true"
          aria-label={titolo}
          tabIndex={-1}
          onKeyDown={trattieni}
          className={`${PANNELLI[larghezza]}${fondo === "carta" ? " al-finestra__pannello--carta" : ""}`}
        >
          {testa && (
            <>
              <span aria-hidden="true" className="al-finestra__maniglia" />
              <div className="al-finestra__testa">
                {segno && (
                  <span aria-hidden="true" className="al-finestra__segno">
                    {segno}
                  </span>
                )}
                <span className="al-finestra__titoli">
                  <span className="al-finestra__titolo">{titolo}</span>
                  {sottotitolo && <span className="al-finestra__sottotitolo">{sottotitolo}</span>}
                </span>
                <a
                  href="#"
                  onClick={chiudi}
                  aria-label={t("ui.close")}
                  className="al-finestra__chiudi"
                >
                  {t("ui.close.sign")}
                </a>
              </div>
            </>
          )}
          {children}
        </div>
      </div>
    </div>
  )
}
