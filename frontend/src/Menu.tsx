import type { CSSProperties, ReactNode } from "react"
import { Link } from "react-router"

import { RiquadroDellaScansione, VoceScansiona, statoDi, useStato } from "./Scansiona"
import { Tratto } from "./TelaioComune"
import { t } from "./i18n"
import { ALTRO_TELEFONO, PAGINE, type Pagina, pagineDi } from "./pagine"

/**
 * I menu del telaio v76 (tavola `Menu`): *Altro* del desktop (le pagine meno usate, coi
 * sottotitoli), l'ingranaggio (la scansione e *Tutte le impostazioni*) e *Altro* del telefono (le
 * pagine fuori dalla bolla, con la scansione in testa quando c'e').
 *
 * Il fuoco, le frecce, Esc e il clic fuori li tiene il telaio: qui solo cio' che si vede.
 */

/** I tre menu della tavola (`tipo`). */
export type TipoMenu = "altro" | "impostazioni" | "altro telefono"

// [T] the board's icons (Menu.dc.html `IC`), by address
const ICONE: Record<string, string> = {
  "/piano-della-notte": "M4 7h7M14 7h6M4 12h11M18 12h2M4 17h3M10 17h10",
  "/planner": "M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.4l-5.3 3 1.2-6-4.5-4.1 6-.7z",
  "/selezione-dei-frame": "M4 5h16v14H4zM4 15l4-4 3 3 4-5 5 6M8 9h.01",
  "/attrezzatura": "M3 14l12-6 2 4-12 6zM15 8l3-1.5 2 4-3 1.5M9 16l-2 5M11 15l2 6",
  "/progetti": "M12 3v3M12 18v3M3 12h3M18 12h3M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z",
  "/statistiche": "M5 20v-9M12 20V5M19 20v-7M3 20h18",
  "/impostazioni": "M4 7h10M18 7h2M4 17h4M12 17h8M16 5v4M10 15v4",
}
const SCANSIONA = "M20 12a8 8 0 1 1-2.3-5.7M20 4v4h-4"

// [T] where each menu opens (Menu.dc.html `P`): under its button on the desktop, over the bubble on the phone
const POSTI: Record<TipoMenu, CSSProperties> = {
  "altro telefono": {
    position: "sticky",
    bottom: "84px",
    margin: "0 12px -8px",
    boxShadow: "0 -12px 40px rgba(0,0,0,.3)",
  },
  impostazioni: {
    position: "absolute",
    top: "calc(100% + 10px)",
    right: 0,
    width: "290px",
    boxShadow: "0 16px 40px rgba(0,0,0,.25)",
  },
  altro: {
    position: "absolute",
    top: "calc(100% + 12px)",
    left: "-8px",
    width: "260px",
    boxShadow: "0 16px 40px rgba(0,0,0,.25)",
  },
}

/** Una voce di pagina del desktop: icona, nome e sottotitolo. */
function VoceDesktop({ pagina }: { pagina: Pagina }) {
  return (
    <Link className="al-c-menu__riga-5" to={pagina.a} role="menuitem">
      <Tratto lato={20} classe="al-c-menu__grafico-1" d={ICONE[pagina.a] ?? ""} />
      <span className="al-c-menu__colonna-3">
        <span className="al-c-menu__testo-4">{t(pagina.chiave)}</span>
        {pagina.sotto && <span className="al-c-menu__testo-2">{t(pagina.sotto)}</span>}
      </span>
    </Link>
  )
}

/** Un menu del telaio, col suo posto e le sue voci. */
export function Menu({ tipo }: { tipo: TipoMenu }) {
  const stato = statoDi(useStato().data)
  const telefono = tipo === "altro telefono"
  let voci: ReactNode
  if (tipo === "impostazioni") {
    voci = (
      <>
        {stato === "ferma" && (
          <VoceScansiona icona={<Tratto lato={20} classe="al-c-menu__grafico-1" d={SCANSIONA} />} />
        )}
        <Link className="al-c-menu__riga-5" to="/impostazioni" role="menuitem">
          <Tratto lato={20} classe="al-c-menu__grafico-1" d={ICONE["/impostazioni"] ?? ""} />
          <span className="al-c-menu__colonna-3">
            <span className="al-c-menu__testo-4">{t("frame.settings.all")}</span>
            <span className="al-c-menu__testo-2">{t("frame.settings.all.sub")}</span>
          </span>
        </Link>
      </>
    )
  } else if (telefono) {
    voci = pagineDi(ALTRO_TELEFONO).map((p) => (
      <Link className="al-c-menu__riga-6" to={p.a} role="menuitem" key={p.a}>
        <Tratto lato={20} classe="al-c-menu__grafico-1" d={ICONE[p.a] ?? ""} />
        <span className="al-c-menu__testo-5">{t(p.chiave)}</span>
      </Link>
    ))
  } else {
    voci = PAGINE.filter((p) => p.posto === "altro").map((p) => (
      <VoceDesktop pagina={p} key={p.a} />
    ))
  }
  return (
    <div
      className="al-c-menu__colonna-1 app-telaio"
      data-menu="1"
      role="menu"
      aria-label={t(tipo === "impostazioni" ? "nav.settings" : "frame.more.menu")}
      style={POSTI[tipo]}
    >
      {tipo !== "altro" && <RiquadroDellaScansione formato={telefono ? "telefono" : "desktop"} />}
      {voci}
    </div>
  )
}
