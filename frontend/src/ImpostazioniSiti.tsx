import { useQueryClient } from "@tanstack/react-query"
import type { CSSProperties } from "react"
import { useContext } from "react"
import { useSearchParams } from "react-router"

import { Avviso } from "./componenti/Avviso"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { Scheletro } from "./componenti/Scheletro"
import { Tema } from "./componenti/Tema"
import type { components } from "./api/schema"
import { useSiti } from "./api/siti"
import { CieloDelSito } from "./ImpostazioniSitiCielo"
import { NuovoSito } from "./ImpostazioniSitiNuovo"
import { IlSito } from "./ImpostazioniSitiSito"
import { SalvataggioFallito } from "./ImpostazioniGenerale"
import { t } from "./i18n"

export type Sito = components["schemas"]["SiteOut"]

/** The chosen site lives in the address (`?sito=<id>`, `?sito=nuovo`): the shell's pills and the
 *  section read the same one, and the search opens a site by link. */
export function useSitoScelto() {
  const [indirizzo, setIndirizzo] = useSearchParams()
  const siti = useSiti()
  const elenco = siti.data?.items ?? []
  const chiesto = indirizzo.get("sito")
  // no site yet: the only thing to do is add one
  const nuovo = chiesto === "nuovo" || (siti.isSuccess && elenco.length === 0)
  const scelto = nuovo
    ? undefined
    : (elenco.find((s) => String(s.id) === chiesto) ??
      elenco.find((s) => s.is_default) ??
      elenco[0])
  const scegli = (id: number | "nuovo" | null) => {
    const dopo = new URLSearchParams(indirizzo)
    if (id === null) dopo.delete("sito")
    else dopo.set("sito", String(id))
    setIndirizzo(dopo, { replace: true })
  }
  return { siti, elenco, scelto, nuovo, scegli }
}

/** The tavola's `pill`: the choice wears the accent ring, the others the line. */
export const anello = (su: boolean, spessore = 2): CSSProperties => ({
  fontWeight: su ? 600 : 500,
  background: "transparent",
  color: "var(--testo)",
  boxShadow: `inset 0 0 0 ${spessore}px ${su ? "var(--accento)" : "var(--linea)"}`,
})

/** A write of a site: the answer refreshes the list; a fault goes to the page's notice with its
 *  retry; expected refusals stay with the caller. `casa`: the write touches the home site, so
 *  tonight and the Moon calendar (which read home) are read again -- only then, because
 *  `GET /tonight` redoes the ephemerides and is the dearest route of the app. */
export function useScriviSito(casa: boolean) {
  const cache = useQueryClient()
  const fallito = useContext(SalvataggioFallito)
  return async function scrivi<T>(
    fa: () => Promise<{ data?: T; error?: unknown; response: Response }>,
    attese: readonly number[] = [],
  ): Promise<{ data: T | undefined; status: number }> {
    const { data, error, response } = await fa()
    if (error && !attese.includes(response.status)) {
      fallito(() => void scrivi(fa, attese))
      return { data: undefined, status: response.status }
    }
    if (!error) {
      fallito(null)
      await cache.invalidateQueries({ queryKey: ["sites"] })
      // a site written can answer Da confermare's place questions; its count is kept, not polled
      void cache.invalidateQueries({ queryKey: ["review"] })
      if (casa) {
        void cache.invalidateQueries({ queryKey: ["tonight"] })
        void cache.invalidateQueries({ queryKey: ["moon-calendar"] })
      }
    }
    return { data, status: response.status }
  }
}

/** The pills of the sites and "+ Aggiungi sito": in the shell's title row on the desktop, on top
 *  of the section on the phone (tavola 20, 246). */
export function PilloleSiti() {
  const tel = useFormato() === "telefono"
  const { elenco, scelto, nuovo, scegli } = useSitoScelto()
  return (
    <Tema>
      <span className="al-imp__siti" role="group" aria-label={t("sites.list")}>
        {elenco.map((s) => (
          <a
            key={s.id}
            href="#"
            className={tel ? "al-imp__riga-30" : "al-imp__pillola-1"}
            role="button"
            aria-pressed={!nuovo && s.id === scelto?.id ? "true" : "false"}
            onClick={gesto(() => scegli(s.id))}
            style={anello(!nuovo && s.id === scelto?.id)}
          >
            {s.name}
          </a>
        ))}
        <a
          href="#"
          className="al-bottone al-bottone--contorno al-imp__aggiungi"
          role="button"
          aria-pressed={nuovo ? "true" : "false"}
          onClick={gesto(() => scegli("nuovo"))}
        >
          {t("sites.add")}
        </a>
      </span>
    </Tema>
  )
}

/**
 * **Siti** (tavola Impostazioni v82, 43-105 and 245-305): the chosen site in two cards, Il sito
 * and Il cielo del sito, or the Nuovo sito card. The horizon card is out (lista fissa 14/11).
 */
export function Siti() {
  const formato = useFormato()
  const tel = formato === "telefono"
  const { siti, scelto, nuovo, scegli } = useSitoScelto()
  let corpo
  if (siti.isPending) {
    corpo = (
      <Scheletro
        formato={formato}
        testo={t("sites.loading")}
        griglia={tel ? "minmax(0,1fr)" : "repeat(12,minmax(0,1fr))"}
        carte={[
          {
            ...(tel ? {} : { col: "span 5" }),
            h: "480px",
            blocchi: [{ h: "30px", w: "200px" }, { flex: "1" }],
          },
          {
            ...(tel ? {} : { col: "span 7" }),
            h: "480px",
            blocchi: [{ h: "20px", w: "160px" }, { flex: "1" }],
          },
        ]}
        gap={tel ? "12px" : "16px"}
      />
    )
  } else if (siti.isError) {
    corpo = (
      <Avviso
        tipo="pagina"
        formato={formato}
        segno="!"
        titolo={t("settings.site.failed")}
        azione={t("settings.retry")}
        onAzione={() => void siti.refetch()}
      />
    )
  } else if (nuovo) {
    corpo = (
      <NuovoSito formato={formato} onFatto={(id) => scegli(id)} onAnnulla={() => scegli(null)} />
    )
  } else if (scelto) {
    corpo = (
      <>
        <IlSito key={`sito-${scelto.id}`} formato={formato} sito={scelto} />
        <CieloDelSito key={`cielo-${scelto.id}`} formato={formato} sito={scelto} />
      </>
    )
  }
  return (
    <Tema>
      {tel ? (
        <div className="al-imp__colonna-18">
          <PilloleSiti />
          {corpo}
        </div>
      ) : (
        <div className="al-imp__griglia-2">{corpo}</div>
      )}
    </Tema>
  )
}
