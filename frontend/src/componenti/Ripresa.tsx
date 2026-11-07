import { t } from "../i18n"

/** What the night allows with the Moon: broadband, only narrowband, or broadband then narrowband. */
export type TipoRipresa = "larga" | "stretta" | "mista"

/**
 * The night's shooting with the Moon (v76 `Ripresa`, the `segno` form): sign and words. The sign
 * takes the text colour, never the accent: shape and word say the kind.
 */
export function Ripresa({
  tipo = "mista",
  testo,
  fondo = "carta",
  colore,
  tenue,
}: {
  tipo?: TipoRipresa
  /** The words, written by the app (hours of broadband, then narrowband). */
  testo: string
  fondo?: "carta" | "protagonista"
  /** Colour of the sign; without it, the text colour of the ground. */
  colore?: string
  /** Colour of the words; without it, the muted colour of the ground. */
  tenue?: string
}) {
  const protagonista = fondo === "protagonista"
  const segno = colore || (protagonista ? "var(--prot-testo)" : "var(--testo)")
  const parole = tenue || (protagonista ? "var(--prot-tenue)" : "var(--tenue)")
  return (
    <span
      className="al-c-ripresa__riga-1"
      role="img"
      aria-label={t("ui.shooting.label", { testo })}
      style={{ gap: "6px", color: segno }}
    >
      <span className="al-c-ripresa__riga-2" aria-hidden="true" style={{ marginTop: "3px" }}>
        {tipo !== "stretta" && (
          <svg className="al-c-ripresa__grafico-1" width={16} height={8} viewBox="0 0 20 10">
            <rect x="1" y="1" width="18" height="8" rx="4" fill="currentColor" />
          </svg>
        )}
        {tipo !== "larga" && (
          <svg className="al-c-ripresa__grafico-1" width={16} height={8} viewBox="0 0 20 10">
            <rect
              x="1.6"
              y="1.6"
              width="16.8"
              height="6.8"
              rx="3.4"
              fill="none"
              stroke="currentColor"
              strokeOpacity=".6"
              strokeWidth="1.2"
            />
            <rect x="7.5" y="1" width="5" height="8" rx="2.5" fill="currentColor" />
          </svg>
        )}
      </span>
      <span
        className="al-c-ripresa__blocco-1"
        style={{ fontSize: "12px", fontWeight: 400, color: parole }}
      >
        {testo}
      </span>
    </span>
  )
}
