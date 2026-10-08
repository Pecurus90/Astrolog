import { type FocusEvent, type KeyboardEvent, type ReactNode, useEffect, useRef, useState } from "react"

/** Una voce della tendina: `chiave` e' cio' che si sceglie, `nome` cio' che si legge. */
export type VoceDiTendina = { chiave: string; nome: string }

/**
 * La tendina del foglio (v31, `54-tendina`): una pillola con l'etichetta e il valore, che apre
 * sotto l'elenco delle scelte.
 *
 * - **E' un bottone che apre un menu di scelte** (`menuitemradio`), come gli altri menu dell'app:
 *   la voce accesa porta `aria-checked`, che e' cio' che il foglio veste.
 * - **Si toglie con la x accanto** (v32: un bottone suo, fuori dalla pillola, una fermata di Tab
 *   in piu') o scegliendo la prima voce ("tutti").
 * - **Il fuoco segue cio' che si apre** e torna al bottone; Esc chiude, uscire col fuoco chiude.
 * - `aspetta`: questa tendina ha chiesto e la risposta non c'e'. Il segno prende il posto della
 *   freccia; non si spegne niente, perche' cambiare idea mentre si aspetta e' legittimo.
 */
export function Tendina({
  etichetta,
  valore,
  voci,
  scelta,
  accesa = false,
  aspetta = false,
  togli,
  onScelta,
}: {
  etichetta: string
  /** Cio' che la pillola dice accanto all'etichetta. */
  valore: string
  voci: VoceDiTendina[]
  /** La chiave della voce accesa. */
  scelta: string
  /** La tendina stringe qualcosa: prende il velo e il filo d'accento. */
  accesa?: boolean
  aspetta?: boolean
  /** Il nome della x che toglie la scelta ("Togli costellazione: Cygnus"). Senza, la x non c'e'. */
  togli?: string | undefined
  onScelta: (chiave: string) => void
}) {
  const [aperta, setAperta] = useState(false)
  const bottone = useRef<HTMLButtonElement>(null)
  const elenco = useRef<HTMLDivElement>(null)

  // Aprendo, il fuoco va alla voce accesa (o alla prima): le frecce partono da li'.
  useEffect(() => {
    if (!aperta) return
    const voci = elenco.current?.querySelectorAll<HTMLElement>("[role=menuitemradio]")
    const accesa = elenco.current?.querySelector<HTMLElement>("[aria-checked=true]")
    ;(accesa ?? voci?.[0])?.focus()
  }, [aperta])

  function chiudi() {
    setAperta(false)
    bottone.current?.focus()
  }
  function tasti(e: KeyboardEvent<HTMLDivElement>) {
    if (e.key === "Escape" && aperta) {
      // qui si ferma: il telaio non deve chiudere anche Stanotte con lo stesso tasto
      e.stopPropagation()
      chiudi()
    } else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault()
      if (!aperta) return setAperta(true)
      const tutte = [...(elenco.current?.querySelectorAll<HTMLElement>("[role=menuitemradio]") ?? [])]
      const qui = tutte.indexOf(document.activeElement as HTMLElement)
      const passo = e.key === "ArrowDown" ? 1 : -1
      tutte[(qui + passo + tutte.length) % tutte.length]?.focus()
    }
  }
  function esce(e: FocusEvent<HTMLDivElement>) {
    if (!e.currentTarget.contains(e.relatedTarget)) setAperta(false)
  }

  const pillola = (
    <button
      className={accesa ? "as-tendina as-tendina--scelta" : "as-tendina"}
      type="button"
      aria-haspopup="menu"
      aria-expanded={aperta}
      aria-busy={aspetta || undefined}
      ref={bottone}
      // Il fuoco non si sposta col mouse: dove un bottone cliccato non lo prende (Safari),
      // uscirebbe verso nessuno e il menu si chiuderebbe prima del clic.
      onMouseDown={(e) => e.preventDefault()}
      onClick={() => setAperta(!aperta)}
    >
      {etichetta} <b>{valore}</b>
      {aspetta ? <span className="as-attesa" aria-hidden="true" /> : <i className="as-tendina__freccia" aria-hidden="true" />}
    </button>
  )

  return (
    <div className="as-tendina-elenco" onKeyDown={tasti} onBlur={esce}>
      {/* L'involucro c'e' sempre, e prende la veste della coppia solo con la x: cosi' la pillola
          non cambia posto quando la x compare, React non la rimonta, e il fuoco le resta. */}
      <span className={accesa && togli ? "as-tendina-coppia" : undefined}>
        {pillola}
        {accesa && togli && (
          <Togli
            nome={togli}
            onTogli={() => {
              // la x sparisce col fuoco addosso: lo prende la sua tendina
              onScelta("")
              bottone.current?.focus()
            }}
          />
        )}
      </span>
      {aperta && (
        <div className="as-tendina-elenco__voci as-menu__voci" role="menu" aria-label={etichetta} ref={elenco}>
          {voci.map((voce) => (
            <button
              className="as-menu__voce"
              type="button"
              role="menuitemradio"
              aria-checked={voce.chiave === scelta}
              key={voce.chiave}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => {
                onScelta(voce.chiave)
                chiudi()
              }}
            >
              <span className="as-menu__nome">{voce.nome}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

/** La x che toglie una scelta: un bottone suo accanto alla pillola, col nome di cio' che toglie
 *  ("Togli costellazione: Cygnus"), perche' la x da sola non dice niente a chi ascolta. */
export function Togli({ nome, onTogli }: { nome: string; onTogli: () => void }) {
  return (
    <button className="as-tendina__togli" type="button" aria-label={nome} onClick={onTogli}>
      {"\u00d7"}
    </button>
  )
}

/** La tendina che e' un interruttore: "Solo i mosaici". Il quadretto si spunta, e chi ascolta
 *  sente se e' premuta. */
export function Spunta({
  accesa,
  aspetta = false,
  onCambia,
  children,
}: {
  accesa: boolean
  aspetta?: boolean
  onCambia: (accesa: boolean) => void
  children: ReactNode
}) {
  return (
    <button
      className="as-tendina"
      type="button"
      aria-pressed={accesa}
      aria-busy={aspetta || undefined}
      onClick={() => onCambia(!accesa)}
    >
      <span className="as-tendina__spunta" aria-hidden="true">
        {accesa ? "\u2713" : ""}
      </span>
      {children}
      {aspetta && <span className="as-attesa" aria-hidden="true" />}
    </button>
  )
}

/** Sul telefono le tendine stanno dietro questa: le apre e le chiude nel flusso, e dice quanti
 *  filtri sono scelti. Sul desktop il foglio la nasconde. */
export function ApriLeTendine({
  aperte,
  governa,
  quanti,
  onCambia,
  children,
}: {
  aperte: boolean
  /** L'id del gruppo delle tendine. */
  governa: string
  quanti: ReactNode
  onCambia: (aperte: boolean) => void
  children: ReactNode
}) {
  return (
    <button
      className="as-tendina as-restringi__apri"
      type="button"
      aria-expanded={aperte}
      aria-controls={governa}
      onClick={() => onCambia(!aperte)}
    >
      {children}
      {quanti}
      <i className="as-tendina__freccia" aria-hidden="true" />
    </button>
  )
}
