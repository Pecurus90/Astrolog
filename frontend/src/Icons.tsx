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

/** Lo sprite, una volta per pagina. Il segno del sito porta il suo tratto, come nella tavola. */
export function IconSprite() {
  return (
    <svg className="app-sprite" aria-hidden="true">
      {Object.entries(PATHS).map(([name, shape]) => (
        <symbol id={`i-${name}`} key={name} viewBox="0 0 20 20">
          {shape}
        </symbol>
      ))}
      <symbol
        id="i-m-sito"
        viewBox="0 0 20 20"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M10 17.5s5.5-5.2 5.5-9.3a5.5 5.5 0 0 0-11 0c0 4.1 5.5 9.3 5.5 9.3z" />
        <circle cx="10" cy="8.2" r="2" />
      </symbol>
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
