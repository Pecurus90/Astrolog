import { type CSSProperties, type ReactNode, useCallback, useEffect, useRef, useState } from "react"
import { Link, useLocation } from "react-router"

import { FinestraDellOggetto } from "./FinestraDellOggetto"
import { IconSprite } from "./Icons"
import { Menu } from "./Menu"
import { PannelloDaConfermare } from "./PannelloDaConfermare"
import { Ricerca } from "./Ricerca"
import {
  AvvisiDellaScansione,
  SegnoDellaScansione,
  nomeConScansione,
  statoDi,
  useFineDelLavoro,
  useStato,
} from "./Scansiona"
import { ApriStanotte, PannelloStanotte, usePastiglia } from "./Stanotte"
import { type Aperto, type Comandi, Conto, LENTE, Tratto, titoloDi } from "./TelaioComune"
import { TelaioTelefono } from "./TelaioTelefono"
import { useRevisione } from "./api/revisione"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { Tema } from "./componenti/Tema"
import { numero, t } from "./i18n"
import { PAGINE, paginaDi } from "./pagine"

/**
 * Il telaio v76 (tavola `Telaio`; contratto in `docs/domini/navigazione.md`): sul desktop la
 * testa con le pillole, Altro, Stanotte, Da confermare, Cerca e l'ingranaggio; sul telefono la
 * testa, il corpo e la bolla di vetro (`TelaioTelefono`).
 *
 * - **Qui non si calcola niente**: il conto e le sezioni da confermare arrivano da `GET /review`,
 *   la scansione da `GET /pipeline/status`, Stanotte da `GET /tonight`.
 * - **Un menu aperto alla volta** (`aperto`), come nella tavola: Esc lo chiude e riporta il
 *   fuoco a chi l'ha aperto, il clic fuori lo chiude, le frecce girano fra le voci, Ctrl K apre Cerca.
 * - **Solo la testa porta i token del foglio nuovo** (`Tema`): il corpo tiene le pagine col foglio
 *   vecchio, che sotto `data-modo` prenderebbero il suo `--inchiostro` e il suo `--linea`.
 */

// [T] Telaio.dc.html: Ctrl K (Cmd K on a Mac) is the key the Cerca button declares
const SUL_MAC = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform)

/** Lo stato dei menu del telaio e i tasti della tavola (`componentDidMount`): Esc, frecce, Ctrl K,
 *  clic fuori, e il fuoco sulla prima voce di un menu appena aperto. */
function useComandi(): Comandi {
  const dove = useLocation()
  const [aperto, setAperto] = useState<Aperto | null>(null)
  const apritori = useRef<Partial<Record<Aperto, HTMLElement | null>>>({})
  // cambiare pagina chiude: la voce scelta e' gia' la risposta
  useEffect(() => setAperto(null), [dove.pathname])

  const torna = useCallback((quale: Aperto) => apritori.current[quale]?.focus(), [])
  useEffect(() => {
    function giu(e: globalThis.MouseEvent) {
      if (e.target instanceof Element && e.target.closest("[data-menu]")) return
      setAperto(null)
    }
    function tasto(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault()
        setAperto("cerca")
        return
      }
      // la ricerca tiene i suoi tasti: Esc la chiude da se', le frecce scelgono fra i trovati
      if (aperto === null || aperto === "cerca") return
      if (e.key === "Escape") {
        setAperto(null)
        torna(aperto)
      } else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        const voci = [
          ...document.querySelectorAll<HTMLElement>(
            ".al-c-menu__colonna-1[role=menu] [role=menuitem]",
          ),
        ]
        if (voci.length === 0) return
        const qui = voci.indexOf(document.activeElement as HTMLElement)
        const dopo =
          e.key === "ArrowDown" ? (qui + 1) % voci.length : (qui - 1 + voci.length) % voci.length
        voci[dopo]?.focus()
        e.preventDefault()
      }
    }
    document.addEventListener("mousedown", giu)
    document.addEventListener("keydown", tasto)
    return () => {
      document.removeEventListener("mousedown", giu)
      document.removeEventListener("keydown", tasto)
    }
  }, [aperto, torna])
  // un menu appena aperto porta il fuoco alla sua prima voce
  useEffect(() => {
    if (aperto !== "altro" && aperto !== "imp") return
    document
      .querySelector<HTMLElement>(".al-c-menu__colonna-1[role=menu] [role=menuitem]")
      ?.focus({ preventScroll: true })
  }, [aperto])

  return {
    aperto,
    tocca: (quale) =>
      gesto(() => {
        const chiude = aperto === quale
        setAperto(chiude ? null : quale)
        if (chiude) torna(quale)
      }),
    segna: (quale) => (e) => {
      apritori.current[quale] = e
    },
    chiudiCerca: (riportaIlFuoco) => {
      setAperto(null)
      if (riportaIlFuoco) torna("cerca")
    },
    apri: setAperto,
  }
}

export function Layout({ children }: { children: ReactNode }) {
  const formato = useFormato()
  const comandi = useComandi()
  useFineDelLavoro()
  const corpo = (
    <>
      <AvvisiDellaScansione />
      <ApriStanotte value={() => comandi.apri("notte")}>{children}</ApriStanotte>
    </>
  )
  return (
    <>
      <IconSprite />
      {/* object window outside the frame: its Esc closes it alone */}
      <FinestraDellOggetto>
        <a className="as-telaio__salta" href="#contenuto">
          {t("frame.skip")}
        </a>
        {formato === "telefono" ? (
          <TelaioTelefono comandi={comandi}>{corpo}</TelaioTelefono>
        ) : (
          <TelaioDesktop comandi={comandi}>{corpo}</TelaioDesktop>
        )}
      </FinestraDellOggetto>
    </>
  )
}

const GRANAGGIO =
  "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"
// open search floats under the head: in the row it would widen it past the frame
const SOTTO_LA_TESTA: CSSProperties = {
  position: "absolute",
  top: "calc(100% + 10px)",
  right: 0,
  width: "var(--cerca-aperta)",
}
/** La testa del desktop e il corpo, nella colonna del telaio (Telaio.dc.html:14-41). */
function TelaioDesktop({ comandi, children }: { comandi: Comandi; children: ReactNode }) {
  const dove = useLocation()
  const qui = paginaDi(dove.pathname)
  const revisione = useRevisione().data
  const quante = revisione?.to_confirm ?? 0
  const pastiglia = usePastiglia()
  const scansione = statoDi(useStato().data)
  const { aperto, tocca, segna } = comandi
  const nomeImp = nomeConScansione(t("nav.settings"), scansione)
  const altro = aperto === "altro"
  return (
    <div
      className="al-c-telaio__blocco-2"
      style={{ minHeight: "100vh", background: "var(--pagina)", padding: "40px" }}
    >
      <div className="al-c-telaio__colonna-1" style={{ boxSizing: "border-box" }}>
        <Tema>
          <header className="al-c-telaio__riga-1 app-telaio" style={{ flex: "none" }}>
            <div className="al-c-telaio__riga-2">
              <span className="al-c-telaio__tondo-1" aria-hidden="true">
                <span className="al-c-telaio__tondo-2" />
              </span>
              AstroLog
            </div>
            <nav className="al-c-telaio__riga-3" aria-label={t("frame.nav.label")}>
              {PAGINE.filter((p) => p.posto === "pillole").map((p) => {
                const su = p.a === qui?.a
                return (
                  <Link
                    key={p.a}
                    className="al-c-telaio__pillola-1"
                    to={p.a}
                    aria-current={su ? "page" : undefined}
                    style={{
                      background: su ? "var(--nav-su)" : "transparent",
                      color: su ? "var(--nav-su-testo)" : "var(--tenue)",
                      padding: su ? "9px 18px" : "9px 11px",
                      fontWeight: su ? 500 : 400,
                    }}
                  >
                    {t(p.chiave)}
                  </Link>
                )
              })}
              <span className="al-c-telaio__riga-4" data-menu="1">
                <a
                  className="al-c-telaio__riga-5"
                  href="#"
                  onClick={tocca("altro")}
                  ref={segna("altro")}
                  aria-haspopup="menu"
                  aria-expanded={altro}
                  style={{
                    color: altro ? "var(--testo)" : "var(--tenue)",
                    background: altro ? "var(--carta-2)" : "transparent",
                  }}
                >
                  {t("frame.more")}
                  <Tratto d={altro ? "M6 15l6-6 6 6" : "M6 9l6 6 6-6"} lato={12} spessore={2.2} />
                </a>
                {altro && <Menu tipo="altro" />}
              </span>
            </nav>
            <div className="al-c-telaio__riga-6" style={{ position: "relative" }}>
              <span className="al-c-telaio__notte-ancora" data-menu="1">
                {pastiglia.senzaSito ? (
                  <Link
                    className="al-c-telaio__riga-7 al-c-telaio__stanotte"
                    to="/impostazioni/sito"
                    aria-label={pastiglia.aria}
                  >
                    {pastiglia.etichetta}
                  </Link>
                ) : (
                  <a
                    className="al-c-telaio__riga-7 al-c-telaio__stanotte"
                    href="#"
                    onClick={tocca("notte")}
                    ref={segna("notte")}
                    aria-haspopup="dialog"
                    aria-expanded={aperto === "notte"}
                    aria-label={pastiglia.aria}
                  >
                    <span className="al-c-telaio__stanotte-t">{t("frame.tonight")}</span>
                    {pastiglia.etichetta}
                  </a>
                )}
                {aperto === "notte" && <PannelloStanotte telefono={false} />}
              </span>
              {qui?.a !== "/da-confermare" && (
                <span className="al-c-telaio__blocco-3" data-menu="1">
                  <a
                    className="al-c-telaio__riga-8"
                    href="#"
                    onClick={tocca("todo")}
                    ref={segna("todo")}
                    aria-haspopup="dialog"
                    aria-expanded={aperto === "todo"}
                    aria-label={quante > 0 ? t("frame.count", { n: numero(quante) }) : undefined}
                  >
                    {t("nav.review")}
                    {quante > 0 && <Conto n={quante} />}
                  </a>
                  {aperto === "todo" && (
                    <PannelloDaConfermare quante={quante} sezioni={revisione?.sections ?? []} />
                  )}
                </span>
              )}
              <a
                className="al-c-telaio__riga-9"
                href="#"
                data-menu="1"
                onClick={tocca("cerca")}
                // open: the field keeps the focus, or its blur would close it before the click toggles
                onMouseDown={(e) => aperto === "cerca" && e.preventDefault()}
                ref={segna("cerca")}
                aria-haspopup="dialog"
                aria-expanded={aperto === "cerca"}
                title={t("frame.search.title", {
                  cerca: t("search.open"),
                  tasto: t(SUL_MAC ? "search.key.shortcut.mac" : "search.key.shortcut"),
                })}
                aria-label={t("frame.search.aria")}
              >
                <Tratto d={LENTE} lato={18} />
                {t("search.open")}
              </a>
              {aperto === "cerca" && (
                <div data-menu="1" style={SOTTO_LA_TESTA}>
                  <Ricerca onChiudi={comandi.chiudiCerca} />
                </div>
              )}
              <span className="al-c-telaio__riga-10" data-menu="1">
                <a
                  className="al-c-telaio__tondo-4"
                  href="#"
                  onClick={tocca("imp")}
                  ref={segna("imp")}
                  aria-haspopup="menu"
                  aria-expanded={aperto === "imp"}
                  title={nomeImp}
                  aria-label={nomeImp}
                  style={{ background: aperto === "imp" ? "var(--carta-2)" : "var(--carta)" }}
                >
                  <Tratto d={GRANAGGIO} lato={20} />
                  <SegnoDellaScansione stato={scansione} dove="tondo" />
                </a>
                {aperto === "imp" && <Menu tipo="impostazioni" />}
              </span>
            </div>
          </header>
        </Tema>
        <main className="app-corpo" id="contenuto" tabIndex={-1}>
          <h1 className="as-solo-lettori">{titoloDi(dove.pathname, false)}</h1>
          {children}
        </main>
      </div>
    </div>
  )
}
