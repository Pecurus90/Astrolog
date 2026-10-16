/**
 * Le icone del telaio, dalla tavola del disegno (`pagine/telaio.html`, v26): uno sprite solo in
 * pagina, e ogni icona lo legge con `<use>`. Tratto e colore li da' il foglio
 * (`.as-telaio__icona`), non l'icona.
 */

const PATHS = {
  casa: <path d="M3 9 10 3l7 6v8h-5v-5H8v5H3z" />,
  luna: <path d="M13.5 3.5A7 7 0 1 0 16.5 13a5.5 5.5 0 0 1-3-9.5z" />,
  griglia: <path d="M3 3h6v6H3zM11 3h6v6h-6zM3 11h6v6H3zM11 11h6v6h-6z" />,
  bersaglio: (
    <>
      <circle cx="10" cy="10" r="7" />
      <circle cx="10" cy="10" r="3.5" />
      <circle cx="10" cy="10" r=".6" />
    </>
  ),
  barre: <path d="M3 17h14M5 15v-4M9 15V5M13 15V8M17 15v-2" />,
  tubo: <path d="m3.5 11.5 10-6 2.5 4-10 6zM9 13l-2 4.5M9.5 13l3 4.5" />,
  calendario: (
    <>
      <rect x="3" y="4" width="14" height="13" rx="2" />
      <path d="M3 8h14M7 2.5v3M13 2.5v3" />
    </>
  ),
  stella: (
    <path d="m10 2.5 2.2 4.8 5.3.6-3.9 3.6 1.1 5.2L10 14.2l-4.7 2.5 1.1-5.2-3.9-3.6 5.3-.6z" />
  ),
  nuvola: <path d="M6 15.5h8.5a3.5 3.5 0 0 0 .3-7A5 5 0 0 0 5.2 9.5 3 3 0 0 0 6 15.5z" />,
  domanda: (
    <>
      <circle cx="10" cy="10" r="7.5" />
      <path d="M7.8 7.8a2.3 2.3 0 1 1 3.2 2.1c-.7.3-1 .8-1 1.5v.3M10 14.2v.3" />
    </>
  ),
  cursori: (
    <>
      <path d="M3 6h9M15.5 6h1.5M3 14h2M8.5 14H17" />
      <circle cx="13.7" cy="6" r="1.7" />
      <circle cx="6.7" cy="14" r="1.7" />
    </>
  ),
  mosaico: (
    <>
      <rect x="3" y="3" width="6" height="6" rx="1" />
      <rect x="11" y="3" width="6" height="6" rx="1" />
      <rect x="3" y="11" width="6" height="6" rx="1" />
      <rect x="11" y="11" width="6" height="6" rx="1" />
    </>
  ),
  cerca: (
    <>
      <circle cx="9" cy="9" r="5.5" />
      <path d="m13 13 4 4" />
    </>
  ),
} as const

export type IconName = keyof typeof PATHS

/** I segni delle misure (`i-m-*`, tavole del Meteo): portano il loro tratto, come il segno del sito. */
const MISURE = {
  sito: (
    <>
      <path d="M10 17.5s5.5-5.2 5.5-9.3a5.5 5.5 0 0 0-11 0c0 4.1 5.5 9.3 5.5 9.3z" />
      <circle cx="10" cy="8.2" r="2" />
    </>
  ),
  goccia: <path d="M10 3s5 5.4 5 9a5 5 0 0 1-10 0c0-3.6 5-9 5-9z" />,
  sereno: (
    <>
      <path d="M12 3.5a6.5 6.5 0 1 0 4.5 10.5A5.5 5.5 0 0 1 12 3.5z" />
      <path d="M16 2.5v3M14.5 4h3" />
    </>
  ),
  pioggia: (
    <>
      <path d="M6 12.5h8.2a3 3 0 0 0 .3-6A4.6 4.6 0 0 0 5.6 7.6 2.5 2.5 0 0 0 6 12.5z" />
      <path d="M7.5 15l-1 2.2M11 15l-1 2.2M14.5 15l-1 2.2" />
    </>
  ),
  velato: (
    <>
      <path d="M12.8 3a4.6 4.6 0 0 0 4.4 6.4" />
      <path d="M5.5 16.5h8.3a2.8 2.8 0 0 0 .2-5.6 4.3 4.3 0 0 0-8.3.6 2.5 2.5 0 0 0-.2 5z" />
    </>
  ),
  vento: <path d="M3 8h9.5a2.5 2.5 0 1 0-2.5-2.5M3 12h12a2.5 2.5 0 1 1-2.5 2.5M3 16h5" />,
  seeing: (
    <>
      <path d="m10 3 1.5 3.8L15.5 8l-4 1.5L10 13.5 8.5 9.5l-4-1.5 4-1.2z" />
      <path d="M3 16.5c1.5-1 3-1 4.5 0s3 1 4.5 0 3-1 4.5 0" />
    </>
  ),
  getto: (
    <>
      <path d="M2.5 7c3-2.5 6-2.5 9 0s5 2.5 6 1.5M2.5 12c3-2.5 6-2.5 9 0s5 2.5 6 1.5" />
      <path d="m15 5.5 2.5 3-3 1" />
    </>
  ),
  occhio: (
    <>
      <path d="M2.5 10s2.8-5 7.5-5 7.5 5 7.5 5-2.8 5-7.5 5-7.5-5-7.5-5z" />
      <circle cx="10" cy="10" r="2.3" />
    </>
  ),
  termometro: (
    <>
      <path d="M8.5 4.5a1.5 1.5 0 0 1 3 0v7.3a3.5 3.5 0 1 1-3 0z" />
      <path d="M10 9v5" />
    </>
  ),
} as const

/** Il nome di un segno nello sprite, da dare a `<use href="#i-...">`. */
export type SegnoDellaMisura = "nuvola" | `m-${Exclude<keyof typeof MISURE, "sito">}`

/** Lo sprite, una volta per pagina. */
export function IconSprite() {
  return (
    <svg className="app-sprite" aria-hidden="true">
      {Object.entries(PATHS).map(([name, shape]) => (
        <symbol id={`i-${name}`} key={name} viewBox="0 0 20 20">
          {shape}
        </symbol>
      ))}
      {Object.entries(MISURE).map(([name, shape]) => (
        <symbol id={`i-m-${name}`} key={name} viewBox="0 0 20 20" fill="none" stroke="currentColor"
          strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          {shape}
        </symbol>
      ))}
    </svg>
  )
}

export function Icon({ name, className = "" }: { name: IconName | "m-sito"; className?: string }) {
  return (
    <svg className={`as-telaio__icona ${className}`.trim()} viewBox="0 0 20 20" aria-hidden="true">
      <use href={`#i-${name}`} />
    </svg>
  )
}
