import { type ReactNode, useEffect, useRef } from "react"

import type { Formato } from "./Tema"

const misura = (v: number | string | undefined): string | undefined =>
  v === undefined || v === ""
    ? undefined
    : typeof v === "number" || /^\d+(\.\d+)?$/.test(v)
      ? `${v}px`
      : v

/**
 * The bento card (v58 `Carta`): ground, corners, grid columns, and an entrance that starts when
 * the card reaches the screen, once. Without `ritardo` there is no entrance.
 */
export function Carta({
  formato = "desktop",
  tono = "carta",
  colonne,
  padding,
  gap,
  griglia,
  anello,
  ritardo,
  etichetta,
  allinea,
  giustifica,
  flex,
  children,
}: {
  formato?: Formato
  tono?: "carta" | "protagonista"
  /** Columns of the page grid on desktop: a number is a span; ignored on the phone. */
  colonne?: number | string
  padding?: number | string
  gap?: number | string
  /** Grid template of the card's inside; without it the inside is a column. */
  griglia?: string
  /** Colour of the 2px ring, from the data (a group's colour). */
  anello?: string
  /** Entrance delay in ms. */
  ritardo?: number
  etichetta?: string
  allinea?: string
  giustifica?: string
  flex?: string
  children: ReactNode
}) {
  const carta = useRef<HTMLElement>(null)
  const telefono = formato === "telefono"
  const quieta =
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true
  const entra = ritardo !== undefined && !quieta

  useEffect(() => {
    const el = carta.current
    if (!el || !entra) return
    const parti = () => {
      el.style.animationPlayState = "running"
    }
    // printing shows every card, seen or not
    window.addEventListener("beforeprint", parti)
    if (typeof IntersectionObserver === "undefined") {
      parti()
      return () => window.removeEventListener("beforeprint", parti)
    }
    const vista = new IntersectionObserver(
      (voci) => {
        if (voci.some((v) => v.isIntersecting)) {
          parti()
          vista.disconnect()
        }
      },
      { rootMargin: "0px 0px -40px 0px" },
    )
    vista.observe(el)
    return () => {
      vista.disconnect()
      window.removeEventListener("beforeprint", parti)
    }
  }, [entra])

  const protagonista = tono === "protagonista"
  const colonna =
    telefono || colonne === undefined || colonne === ""
      ? undefined
      : typeof colonne === "number" || /^\d+(\.\d+)?$/.test(colonne)
        ? `span ${colonne}`
        : colonne
  return (
    <section
      ref={carta}
      className="al-c-carta__blocco-1"
      aria-label={etichetta}
      style={{
        animation: entra
          ? `alIn var(--durata-entrata) var(--curva-entrata) ${ritardo}ms both paused`
          : undefined,
        gridColumn: colonna,
        background: protagonista ? "var(--prot-fondo)" : "var(--carta)",
        color: protagonista ? "var(--prot-testo)" : "var(--testo)",
        borderRadius: telefono ? "24px" : "28px",
        padding: misura(padding) ?? (telefono ? "20px" : "28px"),
        display: griglia ? "grid" : "flex",
        gridTemplateColumns: griglia,
        gap: misura(gap) ?? (telefono ? "14px" : "18px"),
        alignItems: allinea,
        justifyContent: giustifica,
        flex,
        boxShadow: `inset 0 0 0 2px ${anello || "transparent"}`,
      }}
    >
      {children}
    </section>
  )
}
