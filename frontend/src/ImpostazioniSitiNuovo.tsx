import { useQuery } from "@tanstack/react-query"
import { useState } from "react"

import { Avviso } from "./componenti/Avviso"
import { Carta } from "./componenti/Carta"
import { gesto } from "./componenti/gesto"
import type { Formato } from "./componenti/Tema"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { useScriviSito, useSitoScelto } from "./ImpostazioniSiti"
import { fuso, Riga } from "./ImpostazioniSitiSito"
import { coordinataDa, coordinate, numero, t } from "./i18n"
import { useCercaPosto } from "./sito"

type Posto = components["schemas"]["PlaceOut"]
type Per = "nome" | "coord"

/** A point written by hand, read back: `NaN` when it is not a point on the Earth. */
function punto(lat: string, lon: string): { lat: number; lon: number } | null {
  const a = coordinataDa(lat, "lat")
  const o = coordinataDa(lon, "lon")
  return Number.isFinite(a) && Number.isFinite(o) && Math.abs(a) <= 90 && Math.abs(o) <= 180
    ? { lat: a, lon: o }
    : null
}

/** What the point would be as a site: zone, offset, terrain elevation (`GET /places/point`). */
function useAnteprima(p: { lat: number; lon: number } | null) {
  return useQuery({
    queryKey: ["place-point", p?.lat, p?.lon],
    enabled: p !== null,
    staleTime: Number.POSITIVE_INFINITY,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/places/point", {
        params: { query: { latitude: p?.lat ?? 0, longitude: p?.lon ?? 0 } },
      })
      if (error) throw new Error(t("settings.site.failed"))
      return data
    },
  })
}

/** **Nuovo sito** (tavola 91-105): by name or by coordinates, then the name, the zone and the
 *  elevation of the terrain model, which can be changed. The sky is chosen afterwards. */
export function NuovoSito({
  formato,
  onFatto,
  onAnnulla,
}: {
  formato: Formato
  onFatto: (id: number) => void
  onAnnulla: () => void
}) {
  const tel = formato === "telefono"
  const { elenco } = useSitoScelto()
  // the first site is born home (sites.py)
  const scrivi = useScriviSito(elenco.length === 0)
  const [per, setPer] = useState<Per>("nome")
  const [scelto, setScelto] = useState<Posto | null>(null)
  const [lat, setLat] = useState("")
  const [lon, setLon] = useState("")
  const [nome, setNome] = useState("")
  const [alt, setAlt] = useState<string | null>(null)
  const [preso, setPreso] = useState(false)
  const p =
    per === "nome"
      ? scelto
        ? { lat: scelto.latitude, lon: scelto.longitude }
        : null
      : punto(lat, lon)
  const anteprima = useAnteprima(p)
  const modello = anteprima.data?.elevation_m ?? null
  const modelloScritto = modello === null ? "" : String(Math.round(modello))
  const altV = alt ?? modelloScritto
  const nm = nome.trim()
  const doppio = preso || elenco.some((s) => s.name === nm)
  const pronto = p !== null && anteprima.isSuccess
  const ok = pronto && nm !== "" && !doppio
  const salva = gesto(async () => {
    if (!ok || !p) return
    const aMano = altV !== "" && altV !== modelloScritto
    const r = await scrivi(
      () =>
        api.POST("/api/v1/sites", {
          body: {
            name: nm,
            latitude: p.lat,
            longitude: p.lon,
            coords_source: per === "nome" ? "place" : "declared",
            is_default: false,
            ...(aMano ? { elevation_m: Number(altV) } : {}),
          },
        }),
      [409],
    )
    if (r.status === 409) setPreso(true)
    else if (r.data) onFatto(r.data.id)
  })
  const cambiaPer = (k: Per) => {
    setPer(k)
    setAlt(null)
  }
  return (
    <Carta
      formato={formato}
      {...(tel ? {} : { colonne: 8 })}
      ritardo={0}
      padding={tel ? "20px" : "24px 28px"}
      gap={12}
      etichetta={t("sites.new")}
    >
      <div className="al-imp__riga-6">
        <span className="al-imp__testo-3">{t("sites.new")}</span>
        <span className="al-imp__testo-5">{t("sites.new.sub")}</span>
      </div>
      <span
        role="radiogroup"
        aria-label={t("sites.new.how")}
        className={
          tel
            ? "al-scelta al-scelta--segmentato al-scelta--sottili al-scelta--riempie"
            : "al-scelta al-scelta--segmentato al-scelta--sottili"
        }
      >
        {(["nome", "coord"] as const).map((k) => (
          <a
            key={k}
            href="#"
            role="radio"
            aria-checked={per === k ? "true" : "false"}
            onClick={gesto(() => cambiaPer(k))}
            className="al-scelta__voce"
          >
            {t(k === "nome" ? "sites.new.byName" : "sites.new.byCoords")}
          </a>
        ))}
      </span>
      {per === "nome" ? (
        <PerNome
          formato={formato}
          scelto={scelto}
          onScegli={(x) => {
            setScelto(x)
            setNome(x.name)
            setAlt(null)
            setPreso(false)
          }}
        />
      ) : (
        <>
          <span className="al-imp__riga-4">
            <input
              value={lat}
              onChange={(e) => setLat(e.target.value)}
              aria-label={t("sites.new.lat")}
              placeholder={t("sites.new.lat.example")}
              className="al-campo al-imp__coord"
            />
            <input
              value={lon}
              onChange={(e) => setLon(e.target.value)}
              aria-label={t("sites.new.lon")}
              placeholder={t("sites.new.lon.example")}
              className="al-campo al-imp__coord"
            />
          </span>
          <span className="al-imp__testo-8">{t("sites.new.coords.help")}</span>
        </>
      )}
      {anteprima.isError && (
        <Avviso
          tipo="riga"
          formato={formato}
          segno="!"
          titolo={t("sites.new.preview.failed")}
          azione={t("settings.retry")}
          onAzione={() => void anteprima.refetch()}
        />
      )}
      {pronto && p && (
        <div className="al-imp__nuovo-dati">
          <div className="al-imp__griglia-3">
            <span className="al-imp__testo-2">{t("sites.new.name")}</span>
            <span className="al-imp__colonna-1">
              <input
                value={nome}
                onChange={(e) => {
                  setNome(e.target.value)
                  setPreso(false)
                }}
                aria-label={t("sites.name")}
                aria-invalid={doppio ? "true" : "false"}
                className="al-campo"
              />
              {doppio && (
                <span className="al-imp__testo-20" aria-live="polite">
                  {`✕ ${t("sites.name.taken")}` /* glifo-ok: segno della tavola */}
                </span>
              )}
            </span>
          </div>
          <Riga
            etichetta={t("sites.coords")}
            valore={coordinate(p.lat, p.lon)}
            sotto={t(per === "nome" ? "sites.coords.place" : "sites.coords.declared")}
          />
          <Riga
            etichetta={t("sites.zone")}
            valore={fuso(
              anteprima.data?.timezone ?? null,
              anteprima.data?.utc_offset_minutes ?? null,
            )}
            sotto={anteprima.data?.timezone ? t("sites.zone.from") : ""}
          />
          <div className="al-imp__griglia-3">
            <span className="al-imp__testo-2">{t("sites.elevation")}</span>
            <span className="al-imp__colonna-1">
              <span className="al-imp__riga-12">
                <input
                  type="text"
                  inputMode="numeric"
                  value={altV}
                  onChange={(e) => setAlt(e.target.value.replace(/[^0-9]/g, "").slice(0, 4))}
                  aria-label={t("sites.new.elevation")}
                  className="al-campo al-campo--numero al-campo--piccolo al-imp__blocco-19"
                />
                <span className="al-imp__testo-2">{t("sites.new.elevation.unit")}</span>
              </span>
              <span className="al-imp__testo-8">
                {modello === null
                  ? t("sites.elevation.none.why")
                  : altV !== modelloScritto
                    ? t("sites.new.elevation.hand", { n: numero(Math.round(modello)) })
                    : t("sites.new.elevation.model")}
              </span>
            </span>
          </div>
        </div>
      )}
      <div className="al-imp__sito-gesti al-imp__sito-fondo al-imp__sito-fondo--riga">
        <a
          href="#"
          onClick={salva}
          aria-disabled={ok ? "false" : "true"}
          className="al-bottone al-bottone--pieno al-imp__salva"
        >
          {t("sites.new.save")}
        </a>
        {elenco.length > 0 && (
          <a href="#" onClick={gesto(onAnnulla)} className="al-bottone al-bottone--testo">
            {t("ui.form.cancel")}
          </a>
        )}
      </div>
      <span className="al-imp__testo-11">{t("sites.new.after")}</span>
    </Carta>
  )
}

/** The search by name: the service's candidates, one chosen. Without network the list comes back
 *  empty (sito.md), and a fault is not "no place". */
function PerNome({
  formato,
  scelto,
  onScegli,
}: {
  formato: Formato
  scelto: Posto | null
  onScegli: (p: Posto) => void
}) {
  const { q, setQ, stato, trovati, setTrovati, cerca } = useCercaPosto()
  const stesso = (p: Posto) =>
    scelto !== null &&
    p.name === scelto.name &&
    p.latitude === scelto.latitude &&
    p.longitude === scelto.longitude
  return (
    <>
      <span className="al-imp__riga-4">
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value)
            setTrovati(null)
          }}
          onKeyDown={(e) => e.key === "Enter" && void cerca()}
          aria-label={t("sites.new.place")}
          placeholder={t("sites.new.place.example")}
          className="al-campo al-imp__blocco-9"
        />
        <a href="#" onClick={gesto(() => void cerca())} className="al-bottone al-bottone--pieno">
          {t(stato === "cerco" ? "sites.new.searching" : "sites.new.search")}
        </a>
      </span>
      {trovati && trovati.length > 0 && (
        <div className="al-imp__nas" role="group" aria-label={t("site.found")}>
          {trovati.map((p) => (
            <a
              key={`${p.name}-${p.latitude}-${p.longitude}`}
              href="#"
              onClick={gesto(() => onScegli(p))}
              role="button"
              aria-pressed={stesso(p) ? "true" : "false"}
              className="al-imp__nas-voce"
            >
              <span>{p.name}</span>
              <span className="al-imp__testo-4">
                {t(stesso(p) ? "sites.new.chosen" : "sites.new.choose")}
              </span>
            </a>
          ))}
        </div>
      )}
      {trovati && trovati.length === 0 && (
        <Avviso tipo="riga" formato={formato} segno="?" titolo={t("sites.new.none")} />
      )}
      {stato === "rotto" && (
        <Avviso
          tipo="riga"
          formato={formato}
          segno="!"
          titolo={t("site.searchFailedTitle")}
          testo={t("site.searchFailed")}
        />
      )}
    </>
  )
}
