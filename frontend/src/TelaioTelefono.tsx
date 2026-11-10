import { type CSSProperties, type ReactNode, useEffect, useState } from "react"
import { Link, useLocation } from "react-router"

import { Menu } from "./Menu"
import { Ricerca } from "./Ricerca"
import { SegnoDellaScansione, nomeConScansione, statoDi, useStato } from "./Scansiona"
import { PannelloStanotte, usePastiglia } from "./Stanotte"
import { type Comandi, Conto, LENTE, Tratto, titoloDi } from "./TelaioComune"
import { useRevisione } from "./api/revisione"
import { gesto } from "./componenti/gesto"
import { Tema } from "./componenti/Tema"
import { numero, t } from "./i18n"
import { PAGINE, paginaDi } from "./pagine"

/**
 * Il telaio del telefono (Telaio v76, righe 42-68): la testa col titolo e il sito che apre
 * Stanotte, Da confermare e Cerca; il corpo; il menu Altro; la bolla di vetro in basso.
 *
 * - **La bolla chiusa e' la pagina**: toccata si allarga sulle cinque schede (Dashboard, Notti,
 *   Archivio, Meteo, Altro); una pagina fuori dalle cinque e' la sesta. Mentre si scorre si chiude.
 * - **Niente vetro accanto alla bolla** (Marco, v50: `CON=[]`), niente modo chiaro nel menu Altro
 *   (arriva col passo Tema).
 */

// [T] Telaio.dc.html `NV`: the tab icons, by address
const ICONE: Record<string, string> = {
  "/": "M4 4h7v9H4zM13 4h7v5h-7zM13 11h7v9h-7zM4 15h7v5H4z",
  "/notti": "M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z",
  "/archivio": "M4 5h16v4H4zM5 9v10h14V9M10 13h4",
  "/meteo": "M7 18h10a4 4 0 0 0 .5-7.97A6 6 0 0 0 6 11a3.5 3.5 0 0 0 1 7z",
  altro: "M5 12h.01M12 12h.01M19 12h.01",
  "/progetti": "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z",
  "/statistiche": "M5 20V11M12 20V5M19 20v-6",
  "/piano-della-notte": "M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5zM14 3h5M16.5 3v4",
  "/selezione-dei-frame": "M4 5h16l-6 8v6l-4-2v-4z",
  "/planner": "M12 3l2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5z",
  "/attrezzatura": "M4 15l11-6 2 4-11 6zM9 17l-2 4M11 16l2 5",
  "/da-confermare": "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM8 12l3 3 5-6",
  "/impostazioni":
    "M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1",
}

// [T] Telaio.dc.html: the bubble sits 28 px over the bottom, 64 px tall, glass over the page
const POSTO_BOLLA: CSSProperties = {
  position: "sticky",
  bottom: 0,
  zIndex: 5,
  marginTop: "auto",
  height: 0,
  pointerEvents: "none",
}
const VETRO = "blur(18px) saturate(1.6)"

/** La bolla di vetro: la pagina, e toccata le cinque schede (Telaio.dc.html:148-177). */
function Bolla({ comandi }: { comandi: Comandi }) {
  const dove = useLocation()
  const qui = paginaDi(dove.pathname)
  const stato = statoDi(useStato().data)
  const [aperta, setAperta] = useState(false)
  useEffect(() => setAperta(false), [dove.pathname])
  // scorrendo si chiude: resta la bolla, che non copre la pagina
  useEffect(() => {
    const chiudi = () => setAperta(false)
    window.addEventListener("scroll", chiudi, true)
    return () => window.removeEventListener("scroll", chiudi, true)
  }, [])

  const cinque = [...PAGINE.filter((p) => p.telefono).map((p) => p.a), "altro"]
  const fuori = qui !== undefined && !qui.telefono
  const corrente = qui?.a ?? "altro"
  const schede = fuori ? [corrente, ...cinque] : cinque
  const nome = (a: string) =>
    a === "altro" ? t("frame.more") : t(paginaDi(a)?.chiave ?? "nav.unknown")

  return (
    <div style={POSTO_BOLLA}>
      <nav
        aria-label={t("frame.tabs.label")}
        style={{
          position: "absolute",
          left: "12px",
          bottom: "28px",
          height: "64px",
          width: aperta ? "calc(100% - 24px)" : "64px",
          boxSizing: "border-box",
          padding: "5px",
          borderRadius: "32px",
          display: "flex",
          justifyContent: "center",
          overflow: "hidden",
          pointerEvents: "auto",
          background: "color-mix(in srgb, var(--carta) 90%, transparent)",
          backdropFilter: VETRO,
          WebkitBackdropFilter: VETRO,
          boxShadow: "inset 0 0 0 1px var(--linea), 0 12px 30px rgba(0,0,0,.28)",
          transition: "width .5s var(--curva-entrata)",
        }}
      >
        {schede.map((a) => {
          const su = a === corrente
          const via = (!aperta && !su) || (fuori && a === corrente && aperta)
          const altro = a === "altro"
          const stile: CSSProperties = {
            flex: "1 1 0",
            maxWidth: via ? "0px" : "90px",
            minWidth: 0,
            opacity: via ? 0 : 1,
            height: "54px",
            borderRadius: "27px",
            background:
              aperta && !via && (su || (fuori && altro)) ? "var(--carta-2)" : "transparent",
            color: su || (fuori && aperta && altro) ? "var(--accento)" : "var(--testo)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "3px",
            padding: via ? "0" : "0 4px",
            overflow: "hidden",
            textDecoration: "none",
            position: "relative",
            transition: "max-width .5s var(--curva-entrata), opacity .3s, background .3s",
          }
          const dentro = (
            <>
              <Tratto d={ICONE[a] ?? ""} lato={22} spessore={2.1} />
              <span
                style={{
                  fontSize: "10px",
                  lineHeight: 1,
                  whiteSpace: "nowrap",
                  maxHeight: aperta ? "12px" : "0px",
                  opacity: aperta ? 1 : 0,
                  transition: "opacity .2s, max-height .3s",
                }}
              >
                {nome(a)}
              </span>
              {altro && <SegnoDellaScansione stato={stato} dove="scheda" />}
            </>
          )
          const nascosta = via ? { "aria-hidden": true, tabIndex: -1 } : {}
          if (su && !via) {
            return (
              <a
                key={a}
                href="#"
                style={stile}
                onClick={gesto(() => {
                  setAperta(!aperta)
                  comandi.apri(null)
                })}
                aria-label={aperta ? nome(a) : t("frame.tabs.show", { pagina: nome(a) })}
                aria-current={a === qui?.a ? "page" : undefined}
                aria-expanded={aperta ? undefined : false}
              >
                {dentro}
              </a>
            )
          }
          if (altro) {
            return (
              <a
                key={a}
                href="#"
                style={stile}
                data-menu="1"
                onClick={comandi.tocca("altro")}
                ref={comandi.segna("altro")}
                aria-label={nomeConScansione(nome(a), stato)}
                aria-haspopup="menu"
                aria-expanded={comandi.aperto === "altro"}
                {...nascosta}
              >
                {dentro}
              </a>
            )
          }
          return (
            <Link key={a} to={a} style={stile} aria-label={nome(a)} {...nascosta}>
              {dentro}
            </Link>
          )
        })}
      </nav>
    </div>
  )
}

/** Il telefono: testa, Stanotte sotto la testa, corpo, menu Altro e bolla di vetro. */
export function TelaioTelefono({ comandi, children }: { comandi: Comandi; children: ReactNode }) {
  const dove = useLocation()
  const qui = paginaDi(dove.pathname)
  const quante = useRevisione().data?.to_confirm ?? 0
  const pastiglia = usePastiglia()
  const { aperto, tocca, segna } = comandi
  const titolo = titoloDi(dove.pathname, true)
  const dice = (
    <>
      <b
        style={{
          fontSize: 17,
          fontWeight: 600,
          lineHeight: 1.1,
          color: "var(--testo)",
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
          maxWidth: "100%",
        }}
      >
        {titolo}
      </b>
      <span style={{ fontSize: 12, lineHeight: 1.2, color: "var(--tenue)", whiteSpace: "nowrap" }}>
        {pastiglia.etichetta}
      </span>
    </>
  )
  const aria = t("frame.with", { nome: titolo, stato: pastiglia.aria })
  return (
    <div className="al-c-telaio__colonna-2" data-formato="telefono" style={{ minHeight: "100vh" }}>
      <Tema>
        <header className="al-c-telaio__riga-11 app-telaio">
          <span className="al-c-telaio__tondo-5" role="img" aria-label={t("app.title")}>
            <span className="al-c-telaio__tondo-6" />
          </span>
          {pastiglia.senzaSito ? (
            <Link className="al-c-telaio__riga-12" to="/impostazioni/sito" aria-label={aria}>
              {dice}
            </Link>
          ) : (
            <a
              className="al-c-telaio__riga-12"
              href="#"
              onClick={tocca("notte")}
              ref={segna("notte")}
              data-menu="1"
              aria-haspopup="dialog"
              aria-expanded={aperto === "notte"}
              aria-label={aria}
            >
              {dice}
            </a>
          )}
          <span className="al-c-telaio__blocco-6" />
          {qui?.a !== "/da-confermare" && (
            <Link
              className="al-c-telaio__riga-13"
              to="/da-confermare"
              aria-label={quante > 0 ? t("frame.count", { n: numero(quante) }) : t("nav.review")}
            >
              <Tratto d={ICONE["/da-confermare"] ?? ""} lato={18} classe="al-c-telaio__grafico-1" />
              {quante > 0 && <Conto n={quante} />}
            </Link>
          )}
          <a
            className="al-c-telaio__tondo-7"
            href="#"
            data-menu="1"
            onClick={tocca("cerca")}
            onMouseDown={(e) => aperto === "cerca" && e.preventDefault()}
            ref={segna("cerca")}
            aria-haspopup="dialog"
            aria-expanded={aperto === "cerca"}
            aria-label={t("search.open")}
          >
            <Tratto d={LENTE} lato={20} classe="al-c-telaio__grafico-1" />
          </a>
        </header>
      </Tema>
      {aperto === "cerca" && (
        <div data-menu="1">
          <Ricerca onChiudi={comandi.chiudiCerca} />
        </div>
      )}
      {aperto === "notte" && (
        <Tema>
          <PannelloStanotte telefono />
        </Tema>
      )}
      <main className="al-c-telaio__colonna-3 app-corpo" id="contenuto" tabIndex={-1}>
        <h1 className="as-solo-lettori">{titolo}</h1>
        {children}
      </main>
      {aperto === "altro" && (
        <Tema>
          <Menu tipo="altro telefono" />
        </Tema>
      )}
      <Tema>
        <Bolla comandi={comandi} />
      </Tema>
    </div>
  )
}
