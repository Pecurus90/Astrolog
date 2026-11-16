import { useCallback, useState } from "react"
import { Link, useLocation } from "react-router"

import { ImpostazioniBackup } from "./Backup"
import { Avviso } from "./componenti/Avviso"
import { useFormato } from "./componenti/formato"
import { NOMI_MODO } from "./componenti/SceltaTema"
import { Tema, vesteDa } from "./componenti/Tema"
import { useSiti } from "./api/siti"
import { Cartelle } from "./ImpostazioniCartelle"
import { Generale, SalvataggioFallito } from "./ImpostazioniGenerale"
import { Scansioni } from "./ImpostazioniScansioni"
import { Luna } from "./ImpostazioniLuna"
import { Meteo } from "./ImpostazioniMeteo"
import { Riconoscitore } from "./ImpostazioniRiconoscitore"
import { Servizi } from "./ImpostazioniServizi"
import { PilloleSiti, Siti } from "./ImpostazioniSiti"
import { numero, t } from "./i18n"
import { type Sezione, sezioniAperte } from "./pagine"
import { usePreferenze } from "./preferenze"

/**
 * **Impostazioni** (tavola v82): one section at a time, under tabs on the desktop and from an
 * index on the phone.
 *
 * - **Every section has its own address** (`/impostazioni/<key>`, the board's keys): back
 *   works and the link can be sent. A section without `elemento` does not exist.
 * - **The page's address** opens Generale on the desktop, the index on the phone.
 */
export const SEZIONI: readonly Sezione[] = [
  {
    a: "/impostazioni/generale",
    chiave: "settings.general",
    sotto: "settings.general.sub",
    elemento: (
      <Tema>
        <Generale />
      </Tema>
    ),
  },
  {
    a: "/impostazioni/siti",
    chiave: "settings.site",
    sotto: "settings.site.sub",
    elemento: <Siti />,
    testa: <PilloleSiti />,
  },
  {
    a: "/impostazioni/cartelle",
    chiave: "settings.folders",
    sotto: "settings.folders.sub",
    elemento: <Cartelle />,
  },
  {
    a: "/impostazioni/meteo",
    chiave: "settings.weather",
    sotto: "settings.weather.sub",
    elemento: <Meteo />,
  },
  {
    a: "/impostazioni/astap",
    chiave: "settings.solver",
    sotto: "settings.solver.sub",
    elemento: <Riconoscitore />,
  },
  {
    a: "/impostazioni/luna",
    chiave: "settings.moon",
    sotto: "settings.moon.sub",
    elemento: <Luna />,
  },
  {
    a: "/impostazioni/servizi",
    chiave: "settings.services",
    sotto: "settings.services.sub",
    elemento: <Servizi />,
  },
  {
    a: "/impostazioni/scansioni",
    chiave: "settings.readings",
    sotto: "settings.readings.sub",
    elemento: <Scansioni />,
  },
  {
    a: "/impostazioni/backup",
    chiave: "settings.backup",
    sotto: "settings.backup.sub",
    elemento: <ImpostazioniBackup />,
  },
]

export function Impostazioni() {
  const formato = useFormato()
  const tel = formato === "telefono"
  const dove = useLocation()
  const aperte = sezioniAperte(SEZIONI)
  const trovata = aperte.find((s) => s.a === dove.pathname)
  const qui = trovata ?? aperte[0]
  // a failed write: its retry, for the page's notice
  const [riprova, setRiprova] = useState<(() => void) | null>(null)
  // null: a write went through, and the notice of an older one is no longer true
  const fallito = useCallback((f: (() => void) | null) => setRiprova(() => f), [])
  if (!qui) return null
  const indice = tel && trovata === undefined

  const avviso = riprova && (
    <Avviso
      tipo="riga"
      formato={formato}
      segno="!"
      titolo={t("settings.saveFailed")}
      azione={t("settings.retry")}
      onAzione={() => {
        setRiprova(null)
        riprova()
      }}
    />
  )
  // the shell wears the sheet (Tema); a section brings its own, the old ones none
  return (
    <div className="app-cornice app-pagina" data-formato={formato}>
      <SalvataggioFallito.Provider value={fallito}>
        {tel ? (
          <div className="al-imp__colonna-15">
            <Tema>
              {avviso}
              {indice ? (
                <Indice sezioni={aperte} search={dove.search} />
              ) : (
                <>
                  <Link
                    className="al-imp__riga-27"
                    to={{ pathname: "/impostazioni", search: dove.search }}
                  >
                    {`← ${t("nav.settings")}` /* glifo-ok: freccia della tavola */}
                  </Link>
                  <span className="al-imp__colonna-17">
                    <span className="al-imp__testo-26">{t(qui.chiave)}</span>
                    {qui.sotto && <span className="al-imp__testo-5">{t(qui.sotto)}</span>}
                  </span>
                </>
              )}
            </Tema>
            {!indice && qui.elemento}
          </div>
        ) : (
          <div className="al-imp__griglia-1">
            <Tema>
              {avviso && <div style={{ gridColumn: "1 / -1" }}>{avviso}</div>}
              <div className="al-imp__riga-1">
                <span className="al-imp__riga-2">
                  <span className="al-imp__testo-1 al-solo-voce">{t("nav.settings")}</span>
                  {qui.sotto && <span className="al-imp__testo-2">{t(qui.sotto)}</span>}
                </span>
                {qui.testa}
              </div>
              <div
                role="tablist"
                aria-label={t("settings.sections")}
                className="al-scelta al-scelta--linguette al-scelta--sottili al-imp__blocco-3"
              >
                {aperte.map((s) => (
                  <Link
                    key={s.a}
                    to={{ pathname: s.a, search: dove.search }}
                    role="tab"
                    aria-selected={s.a === qui.a ? "true" : "false"}
                    className="al-scelta__voce"
                  >
                    {t(s.chiave)}
                  </Link>
                ))}
              </div>
            </Tema>
            {qui.elemento}
          </div>
        )}
      </SalvataggioFallito.Provider>
    </div>
  )
}

/** The phone's first screen: every section with its line, Generale and Siti with what they hold
 *  (tavola `RIAS`). */
function Indice({ sezioni, search }: { sezioni: readonly Sezione[]; search: string }) {
  const riassunti = useRiassunti()
  return (
    <div className="al-imp__colonna-16" role="list">
      {sezioni.map((s, i) => {
        const sotto = riassunti[s.a] ?? (s.sotto ? t(s.sotto) : "")
        return (
          <Link
            key={s.a}
            className="al-imp__riga-26"
            to={{ pathname: s.a, search }}
            role="listitem"
            style={{ borderTop: i ? "1px solid var(--linea)" : "0" }}
          >
            <span className="al-imp__colonna-6">
              <b className="al-imp__testo-25">{t(s.chiave)}</b>
              <span className="al-imp__blocco-24">{sotto}</span>
            </span>
            <span className="al-imp__blocco-25" aria-hidden="true">
              {"↗" /* glifo-ok: freccia della tavola */}
            </span>
          </Link>
        )
      })}
    </div>
  )
}

function useRiassunti(): Record<string, string> {
  const valori = usePreferenze().data?.values
  const siti = useSiti().data?.items
  const fuori: Record<string, string> = {}
  if (valori) {
    const modo = t(
      NOMI_MODO[vesteDa(valori.theme_mode, valori.theme_accent).modo],
    ).toLocaleLowerCase()
    const nome = String(valori.user_name ?? "").trim()
    fuori["/impostazioni/generale"] = nome
      ? t("settings.index.general", { nome, modo })
      : t("settings.index.general.noname", { modo })
  }
  if (siti && siti.length > 0) {
    const casa = siti.find((s) => s.is_default)
    const n = numero(siti.length)
    fuori["/impostazioni/siti"] = casa
      ? t("settings.index.sites", { n, sito: casa.name })
      : t("settings.index.sites.nohome", { n })
  }
  return fuori
}
