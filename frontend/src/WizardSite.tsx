import { useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { Avviso } from "./componenti/Avviso"
import { gesto } from "./componenti/gesto"
import type { Formato } from "./componenti/Tema"
import { CampoAvvio, Comando } from "./PrimoAvvioCornice"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, coordinate, t } from "./i18n"
import { CLASSI, type ClasseDiCielo, useCampiDelSito, useCercaPosto } from "./sito"

type Posto = components["schemas"]["PlaceOut"]

/** Two places are the same place by name and point: by name alone "Verona" would light both. */
const chiave = (p: Posto) => `${p.name}-${p.latitude}-${p.longitude}`

/**
 * The site step's state, held by the shell: the first site is the home one (without it no night
 * is born), and a failed write keeps the user on the step. Saved, the form stays as the board
 * keeps it: going back, Salva sito with nothing changed moves on, a change edits the same site.
 */
export function useSitoDelPasso(onSaved: () => void) {
  const campi = useCampiDelSito()
  const cache = useQueryClient()
  const [rotto, setRotto] = useState(false)
  const [salvando, setSalvando] = useState(false)
  const [salvato, setSalvato] = useState<{ id: number; firma: string } | null>(null)

  const salva = async () => {
    if (!campi.valido || salvando) return
    const corpo = campi.corpo()
    const firma = JSON.stringify(corpo)
    if (salvato?.firma === firma) {
      onSaved()
      return
    }
    setSalvando(true)
    // a request that never reaches the service rejects instead of returning `error`
    const scrivi = salvato
      ? api.PATCH("/api/v1/sites/{site_id}", {
          params: { path: { site_id: salvato.id } },
          body: corpo,
        })
      : api.POST("/api/v1/sites", { body: { ...corpo, is_default: true } })
    const id = await scrivi.then(
      ({ data, error }) => (error || !data ? null : data.id),
      () => null,
    )
    setSalvando(false)
    setRotto(id === null)
    if (id === null) return
    setSalvato({ id, firma })
    // the Tema step next: Automatico needs this site (`theme_site`)
    void cache.invalidateQueries({ queryKey: ["settings"] })
    onSaved()
  }
  // leaving the step drops a failed write: back on it, nothing was retried yet
  const dimentica = () => setRotto(false)
  return { campi, rotto, salvando, salva, dimentica }
}

type Sito = ReturnType<typeof useSitoDelPasso>

/** Search by name. Without network `GET /places` answers an empty list on purpose (sito.md), and
 *  a fault is not "no place": it says so, with the way to the coordinates inside. */
function CercaPerNome({ formato, onScegli }: { formato: Formato; onScegli: (p: Posto) => void }) {
  const [scelto, setScelto] = useState<string>()
  const { q, setQ, stato, trovati, cerca } = useCercaPosto(() => setScelto(undefined))
  return (
    <div className="al-avvio__colonna-12">
      <span className="al-avvio__testo-13">{t("wizard.site.searchGroup")}</span>
      <form
        onSubmit={(e) => {
          e.preventDefault()
          void cerca()
        }}
      >
        <CampoAvvio
          id="pa-q"
          etichetta={t("site.searchLabel")}
          valore={q}
          onScrivi={setQ}
          dopo={
            <Comando
              testo={t("site.search")}
              verso="tenue"
              spento={!q.trim()}
              occupato={stato === "cerco" ? t("wizard.site.searching") : undefined}
              onClick={() => void cerca()}
            />
          }
        />
      </form>
      {trovati && trovati.length > 0 && (
        <div className="al-avvio__colonna-4">
          <span className="al-avvio__testo-9">{t("site.found")}</span>
          <ul className="al-avvio__colonna-13">
            {trovati.map((p) => {
              const sel = scelto === chiave(p)
              return (
                <li
                  key={chiave(p)}
                  className="al-avvio__riga-8"
                  aria-current={sel ? "true" : undefined}
                  style={{ boxShadow: `inset 0 0 0 ${sel ? "2px" : "0"} var(--testo)` }}
                >
                  <span className="al-avvio__colonna-14">
                    <span className="al-avvio__testo-14">{p.name}</span>
                    <span className="al-avvio__testo-15">
                      {coordinate(p.latitude, p.longitude)}
                    </span>
                  </span>
                  {sel ? (
                    <span className="al-avvio__riga-9">
                      {`✓ ${t("site.chosen")}` /* glifo-ok: segno della tavola */}
                    </span>
                  ) : (
                    <a
                      href="#"
                      role="button"
                      aria-label={t("site.chooseOne", { nome: p.name })}
                      onClick={gesto(() => {
                        setScelto(chiave(p))
                        onScegli(p)
                      })}
                      className="al-bottone al-bottone--tenue al-bottone--rovescio al-avvio__blocco-4"
                    >
                      {t("site.choose")}
                    </a>
                  )}
                </li>
              )
            })}
          </ul>
        </div>
      )}
      {trovati && trovati.length === 0 && (
        <Avviso
          tipo="blocco"
          formato={formato}
          segno="?"
          titolo={t("wizard.site.none.title")}
          testo={t("wizard.site.none.text")}
        />
      )}
      {stato === "rotto" && (
        <Avviso
          tipo="riga"
          formato={formato}
          segno="!"
          titolo={t("site.searchFailedTitle")}
          testo={t("site.searchFailed")}
          azione={t("site.writeByHand")}
          onAzione={() => document.getElementById("pa-lat")?.focus()}
        />
      )}
    </div>
  )
}

/** Bortle from 1 to 9 (tavola `bortle`, `bL`): nine radios, the chosen one again clears it.
 *  One tab stop, the arrows move inside the scale and never wrap: a turn would jump from city
 *  centre to full dark with one key, and left on 1 would clear the choice in silence. */
function SceltaBortle({ sito, tel }: { sito: Sito; tel: boolean }) {
  const { cielo, setCielo } = sito.campi
  const freccia = (n: ClasseDiCielo, key: string, el: HTMLElement) => {
    const passo =
      key === "ArrowRight" || key === "ArrowDown"
        ? 1
        : key === "ArrowLeft" || key === "ArrowUp"
          ? -1
          : 0
    const dopo = CLASSI.find((c) => c === n + passo)
    if (!passo || dopo === undefined) return false
    setCielo(dopo)
    const vicino = passo > 0 ? el.nextElementSibling : el.previousElementSibling
    if (vicino instanceof HTMLElement) vicino.focus()
    return true
  }
  return (
    <div className="al-avvio__colonna-15">
      <span className="al-avvio__testo-13" id="pa-b">
        {t("sky.scale")}
      </span>
      <div
        className="al-avvio__centro-4"
        role="radiogroup"
        aria-labelledby="pa-b"
        style={{ gridTemplateColumns: tel ? "repeat(5,minmax(0,1fr))" : "repeat(9,minmax(0,1fr))" }}
      >
        {CLASSI.map((n) => {
          const sel = cielo === n
          return (
            <a
              key={n}
              className="al-avvio__centro-5"
              href="#"
              role="radio"
              aria-checked={sel ? "true" : "false"}
              aria-label={t("sky.chosen", { n, cielo: t(`sky.${n}` as Chiave) })}
              tabIndex={sel || (cielo === undefined && n === 1) ? 0 : -1}
              onClick={gesto(() => setCielo(sel ? undefined : n))}
              onKeyDown={(e) => {
                if (freccia(n, e.key, e.currentTarget)) e.preventDefault()
              }}
              style={
                sel
                  ? { background: "var(--accento)", color: "var(--scelta-testo)" }
                  : { background: "var(--carta-2)", color: "var(--testo)" }
              }
            >
              {n}
            </a>
          )
        })}
      </div>
      <div className="al-avvio__riga-10" aria-hidden="true">
        <span>{t("sky.low")}</span>
        <span>{t("sky.high")}</span>
      </div>
      <div className="al-avvio__colonna-17" aria-live="polite">
        <span className="al-avvio__testo-3" style={{ fontWeight: cielo ? 600 : 400 }}>
          {cielo
            ? t("sky.chosen", { n: cielo, cielo: t(`sky.${cielo}` as Chiave) })
            : t("sky.noneChosen")}
        </span>
        {cielo && <span className="al-avvio__testo-16">{t(`sky.${cielo}.what` as Chiave)}</span>}
      </div>
      <span className="al-avvio__testo-12">{t("sky.optional")}</span>
    </div>
  )
}

/**
 * The site step (tavola v82 `Primo avvio`, `V.sito`): search by name, coordinates written by hand
 * (also without network), Bortle, and Salva sito under the fields. A field's reason shows once
 * the field is left: an empty field is not wrong yet.
 */
export function WizardSite({ sito, formato }: { sito: Sito; formato: Formato }) {
  const { campi } = sito
  const [lasciati, setLasciati] = useState<Record<string, boolean>>({})
  const lascia = (k: string) => () => setLasciati((s) => (s[k] ? s : { ...s, [k]: true }))
  return (
    <div className="al-avvio__colonna-11">
      <CercaPerNome
        formato={formato}
        onScegli={(p) => {
          campi.prendiDa(p)
          setLasciati({})
        }}
      />
      <div className="al-avvio__colonna-15">
        <span className="al-avvio__colonna-16">
          <span className="al-avvio__testo-13">{t("wizard.site.manual")}</span>
          <span className="al-avvio__testo-12">{t("wizard.site.manualWhy")}</span>
        </span>
        <CampoAvvio
          id="pa-sn"
          etichetta={t("site.name")}
          valore={campi.nome}
          onScrivi={campi.setNome}
          onLascia={lascia("nome")}
          segnaposto={t("site.namePlaceholder")}
          errore={lasciati["nome"] && !campi.nome.trim() ? t("site.nameNeeded") : undefined}
        />
        <div
          className="al-avvio__centro-3"
          style={{ gridTemplateColumns: "repeat(2,minmax(0,1fr))" }}
        >
          <CampoAvvio
            id="pa-lat"
            etichetta={t("site.lat")}
            valore={campi.lat}
            onScrivi={campi.setLat}
            onLascia={lascia("lat")}
            segnaposto={t("site.latPlaceholder")}
            errore={lasciati["lat"] ? campi.fuoriScala(campi.lat, "lat") : undefined}
          />
          <CampoAvvio
            id="pa-lon"
            etichetta={t("site.lon")}
            valore={campi.lon}
            onScrivi={campi.setLon}
            onLascia={lascia("lon")}
            segnaposto={t("site.lonPlaceholder")}
            errore={lasciati["lon"] ? campi.fuoriScala(campi.lon, "lon") : undefined}
          />
        </div>
        <span className="al-avvio__testo-12">{t("wizard.site.coordsHelp")}</span>
      </div>
      <SceltaBortle sito={sito} tel={formato === "telefono"} />
      <div className="al-avvio__riga-11">
        <Comando
          testo={t("wizard.site.save")}
          verso="pieno"
          spento={!campi.valido}
          occupato={sito.salvando ? t("wizard.saving") : undefined}
          onClick={() => void sito.salva()}
        />
      </div>
    </div>
  )
}
