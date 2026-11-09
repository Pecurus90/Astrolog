/**
 * La **finestra dell'oggetto** (tavola v76, `componenti/FinestraRiepilogo.dc.html` e
 * `componenti/Riepilogo.dc.html`, tipo `oggetto`): il riepilogo di una riga dell'Archivio sopra
 * la pagina, coi pezzi della notte. Formatta e basta: tutto da `GET /api/v1/objects/{key}`, una
 * produzione alla volta quando sono piu' d'una.
 */
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { Link } from "react-router"

import { api } from "./api/client"
import type { components } from "./api/schema"
import { Avviso } from "./componenti/Avviso"
import { Carta } from "./componenti/Carta"
import { gesto } from "./componenti/gesto"
import { Luna } from "./componenti/Luna"
import { Pillola } from "./componenti/Pillola"
import { Scheletro } from "./componenti/Scheletro"
import type { Formato } from "./componenti/Tema"
import { costellazione } from "./costellazioni"
import {
  dataLunga,
  decimali,
  estremi,
  giornoMeseAnno,
  maiuscola,
  numero,
  oreEMinuti,
  t,
} from "./i18n"
import { MisureDeiFrame } from "./MisureDeiFrame"
import { MENTRE_LEGGE_MS } from "./Notti"
import { type EsitoDelGruppo, type Misure, medianeInTesta } from "./MisureDati"
import { cielo, luna, segnoDi } from "./NottiDati"
import {
  FiltriInTesta,
  FinestraRiepilogo,
  NumeriInTesta,
  inCatalogo,
  MISURE,
  RigaDiTesta,
  SCHELETRO,
  Setups,
} from "./RiepilogoComune"
import { tipoDi } from "./RigaDellArchivio"
import { distanza, estensione } from "./TuttoDellaNotte"

type Dettaglio = components["schemas"]["ObjectDetail"]
type Produzione = components["schemas"]["ArchiveProduction"]

class NonTrovato extends Error {}

async function dettaglio(key: string, production: string | null): Promise<Dettaglio> {
  const { data, error, response } = await api.GET("/api/v1/objects/{key}", {
    params: { path: { key }, query: production ? { production } : {} },
  })
  if (response.status === 404) throw new NonTrovato()
  if (error) throw new Error(t("window.failed"))
  return data
}

async function misure(key: string, production: string | null) {
  const { data, error } = await api.GET("/api/v1/objects/{key}/measures", {
    params: { path: { key }, query: production ? { production } : {} },
  })
  if (error) throw new Error(t("window.failed"))
  return data
}

/** La produzione come la chiede la rotta: `ottica:camera`, `none` per un pezzo che non si sa. */
function chiaveDi(p: Produzione): string {
  return `${p.optics_id ?? "none"}:${p.camera_id ?? "none"}`
}

export function TuttoDellOggetto({
  chiave,
  nome,
  formato,
  onChiudi,
  onPrima,
  onDopo,
}: {
  chiave: string
  nome: string
  formato: Formato
  onChiudi: () => void
  onPrima?: (() => void) | undefined
  onDopo?: (() => void) | undefined
}) {
  const [scelta, setScelta] = useState(0)
  const intera = useQuery({
    queryKey: ["objects", "detail", chiave, null],
    queryFn: () => dettaglio(chiave, null),
    retry: (n, e) => !(e instanceof NonTrovato) && n < 2,
  })
  // Un mosaico non ha ancora i pannelli dall'API: niente linguette (differenze-dalle-tavole.md).
  const produzioni =
    intera.data && !intera.data.row.panels && intera.data.row.productions.length > 1
      ? intera.data.row.productions
      : null
  const scelta1 = produzioni ? produzioni[Math.min(scelta, produzioni.length - 1)] : undefined
  const una = useQuery({
    queryKey: ["objects", "detail", chiave, scelta1 ? chiaveDi(scelta1) : null],
    queryFn: () => dettaglio(chiave, scelta1 ? chiaveDi(scelta1) : null),
    enabled: !!scelta1,
  })
  const dati = scelta1 ? una : intera
  const quale = scelta1 ? chiaveDi(scelta1) : null
  // Aspetta l'intera: con piu' produzioni le misure sono di una sola, mai di tutte insieme.
  const mis = useQuery({
    queryKey: ["objects", "measures", chiave, quale],
    queryFn: () => misure(chiave, quale),
    enabled: !!intera.data && (!produzioni || !!scelta1),
    refetchInterval: (q) => ((q.state.data?.pending ?? 0) > 0 ? MENTRE_LEGGE_MS : false),
  })
  const L = MISURE[formato]
  const tel = formato === "telefono"

  let corpo
  if (intera.isPending || (dati.isPending && !dati.data)) {
    corpo = (
      <Scheletro
        formato={formato}
        carte={SCHELETRO}
        griglia="minmax(0,1fr)"
        gap={L.gap}
        testo={t("window.loading")}
      />
    )
  } else if (intera.error instanceof NonTrovato) {
    corpo = (
      <Avviso
        tipo="pagina"
        formato={formato}
        segno="?"
        titolo={t("object.gone")}
        testo={t("object.gone.text")}
      />
    )
  } else if (dati.isError || !dati.data) {
    corpo = (
      <Avviso
        tipo="pagina"
        formato={formato}
        segno="!"
        titolo={t("window.failed")}
        testo={t("window.failed.text")}
        azione={t("window.retry")}
        onAzione={() => void dati.refetch()}
      />
    )
  } else {
    const d = dati.data
    corpo = (
      <div
        className="al-c-riepilogo__centro-1"
        style={{
          gridTemplateColumns: tel ? "minmax(0,1fr)" : "repeat(12,minmax(0,1fr))",
          gap: L.gap,
        }}
      >
        <Testa
          d={d}
          misure={mis.data}
          formato={formato}
          produzioni={produzioni}
          scelta={scelta1}
          onScegli={setScelta}
          onChiudi={onChiudi}
          onPrima={onPrima}
          onDopo={onDopo}
        />
        <Setups setups={d.rigs} formato={formato} />
        <InCielo f={d.facts} formato={formato} />
        <div className="al-c-riepilogo__blocco-4">
          {mis.data && (
            <MisureDeiFrame
              key={`${chiave}|${quale ?? ""}`}
              misure={mis.data}
              formato={formato}
              tipo="oggetto"
              esiti={esitiDelleNotti(d)}
            />
          )}
          {mis.isError && !mis.data && (
            <Avviso
              formato={formato}
              segno="!"
              titolo={t("window.failed")}
              azione={t("window.retry")}
              onAzione={() => void mis.refetch()}
            />
          )}
        </div>
        <div
          className="al-c-riepilogo__colonna-12"
          style={{ gridColumn: tel ? "auto" : "span 8", gap: L.gap }}
        >
          <LeNotti d={d} formato={formato} />
        </div>
      </div>
    )
  }

  return (
    <FinestraRiepilogo aria={t("object.window", { nome })} formato={formato} onChiudi={onChiudi}>
      {corpo}
    </FinestraRiepilogo>
  )
}

/** L'esito di ogni notte, lo stesso di *Le notti*, accanto alla sua riga in *Le notti a confronto*. */
function esitiDelleNotti(d: Dettaglio): Map<string, EsitoDelGruppo> {
  return new Map(
    d.nights.map(({ night: n }) => {
      const c = cielo(n)
      return [
        String(n.id),
        { esito: c.esito === -1 ? "mancante" : c.esito, testo: c.pillola, segno: segnoDi(c.esito) },
      ]
    }),
  )
}

function periodo(d: Dettaglio): string {
  if (!d.first_night || !d.last_night) return ""
  // Due siti la stessa notte sono due notti con la stessa data.
  const n = d.nights.length
  const notti =
    d.first_night !== d.last_night
      ? t("object.period", { ...estremi(d.first_night, d.last_night), n })
      : n > 1
        ? t("object.period.day", { data: giornoMeseAnno(d.first_night), n })
        : t("object.period.one", { data: giornoMeseAnno(d.first_night) })
  return d.sites.length > 1
    ? t("object.period.sites", { periodo: notti, n: d.sites.length })
    : notti
}

function Testa({
  d,
  misure: m,
  formato,
  produzioni,
  scelta,
  onScegli,
  onChiudi,
  onPrima,
  onDopo,
}: {
  d: Dettaglio
  misure: Misure | undefined
  formato: Formato
  produzioni: Produzione[] | null
  scelta: Produzione | undefined
  onScegli: (i: number) => void
  onChiudi: () => void
  onPrima?: (() => void) | undefined
  onDopo?: (() => void) | undefined
}) {
  const tel = formato === "telefono"
  const L = MISURE[formato]
  const r = d.row
  const conOre = r.integration_s > 0
  const frame = t("window.frames", { n: numero(r.frames) })
  const grande = conOre ? oreEMinuti(r.integration_s) : frame
  const sotto = !conOre
    ? t("window.untimed")
    : r.untimed > 0
      ? t("object.untimed", { frame, n: numero(r.untimed) })
      : frame
  const nome = d.facts.common_name ?? (inCatalogo(d.facts) ? "" : t("object.outside"))
  const filtri = r.filters.length ? (
    <FiltriInTesta filtri={r.filters} />
  ) : (
    <span className="al-c-riepilogo__testo-3">{t("archive.unknown.filters")}</span>
  )
  return (
    <Carta
      formato={formato}
      etichetta={t("window.summary")}
      colonne={7}
      ritardo={0}
      padding={L.pad}
      gap={16}
    >
      <RigaDiTesta
        siti={d.sites}
        formato={formato}
        prima="object.prev"
        dopo="object.next"
        onChiudi={onChiudi}
        onPrima={onPrima}
        onDopo={onDopo}
      />
      <div className="al-c-riepilogo__colonna-1">
        <span className="al-c-riepilogo__testo-1">{t("object.above")}</span>
        <span className="al-c-riepilogo__riga-5">
          <b className="al-c-riepilogo__testo-2" style={{ fontSize: L.tfs }}>
            {r.name ?? r.key}
          </b>
          {nome && (
            <span className="al-c-riepilogo__testo-3" style={{ fontSize: L.sfs }}>
              {nome}
            </span>
          )}
        </span>
        <span className="al-c-riepilogo__testo-4">{periodo(d)}</span>
      </div>
      {produzioni && (
        <div
          className="al-c-riepilogo__riga-6"
          role="tablist"
          aria-label={t("object.productions")}
          style={{ flexWrap: tel ? "nowrap" : "wrap", overflowX: tel ? "auto" : "visible" }}
        >
          <span className="al-c-riepilogo__blocco-2">{t("object.productions")}</span>
          {produzioni.map((p, i) => {
            const sel = p === scelta
            return (
              <a
                key={chiaveDi(p)}
                className="al-c-riepilogo__colonna-2"
                href="#"
                role="tab"
                aria-selected={sel ? "true" : "false"}
                onClick={gesto(() => onScegli(i))}
                style={{
                  minHeight: tel ? 52 : 48,
                  background: "transparent",
                  color: sel ? "var(--testo)" : "var(--tenue)",
                  boxShadow: sel ? "inset 0 -2px 0 var(--accento)" : "inset 0 -1px 0 var(--linea)",
                  borderRadius: 0,
                }}
              >
                <b className="al-c-riepilogo__testo-5">{p.optics ?? t("gear.rig.noOptics")}</b>
                <span className="al-c-riepilogo__testo-6" style={{ color: "var(--tenue)" }}>
                  {t("object.production.sub", {
                    camera: p.camera ?? t("gear.rig.noCamera"),
                    ore:
                      p.integration_s > 0
                        ? oreEMinuti(p.integration_s)
                        : t("window.frames", { n: numero(p.frames) }),
                  })}
                </span>
              </a>
            )
          })}
        </div>
      )}
      <NumeriInTesta
        formato={formato}
        grande={grande}
        sotto={sotto}
        conOre={conOre}
        kpi={medianeInTesta(m)}
        filtri={filtri}
      />
    </Carta>
  )
}

// Interi come la tavola; sotto i 10 primi un decimale, o una nebulosa planetaria direbbe zero.
function primi(x: number): string {
  return decimali(x, x < 10 ? 1 : 0)
}

function lune(m: NonNullable<Dettaglio["facts"]["moon"]>): string {
  if (m.compare === "more")
    return m.moons === 1
      ? t("object.moon.more.one")
      : t("object.moon.more", { n: numero(m.moons ?? 0) })
  return t(m.compare === "like" ? "object.moon.like" : "object.moon.less")
}

function InCielo({ f, formato }: { f: Dettaglio["facts"]; formato: Formato }) {
  const tipo = tipoDi(f)
  const tessere = !inCatalogo(f)
    ? [
        { l: t("window.fact.type"), v: t("object.type.none"), s: t("object.type.none.sub") },
        { l: t("window.fact.constellation"), v: t("object.constellation.none"), s: "" },
      ]
    : [
        { l: t("window.fact.type"), v: tipo ? maiuscola(t(tipo)) : "\u2014", s: "" },
        {
          l: t("window.fact.constellation"),
          v: f.constellation ? costellazione(f.constellation) : "\u2014",
          s: "",
        },
        {
          l: t("window.fact.distance"),
          v: distanza(f),
          s: f.distance_pc != null ? t("object.parsec", { n: numero(f.distance_pc) }) : "",
        },
        {
          l: t("window.fact.extent"),
          v: estensione(f),
          s:
            f.size_arcmin != null && f.moon
              ? t("object.size", { n: primi(f.size_arcmin), luna: lune(f.moon) })
              : "",
        },
      ]
  return (
    <Carta
      formato={formato}
      etichetta={t("object.sky")}
      colonne={12}
      ritardo={60}
      padding={MISURE[formato].pad}
      gap={14}
    >
      <span className="al-c-riepilogo__riga-10">
        <span className="al-c-riepilogo__testo-14">{t("object.sky")}</span>
        <span className="al-c-riepilogo__testo-8">{t("window.objects.sub")}</span>
      </span>
      <div className="al-c-riepilogo__griglia-2">
        {tessere.map((x) => (
          <span key={x.l} className="al-c-riepilogo__colonna-9">
            <span className="al-c-riepilogo__testo-12">{x.l}</span>
            <span
              className="al-c-riepilogo__testo-15"
              style={{ fontSize: formato === "telefono" ? "18px" : "24px" }}
            >
              {x.v}
            </span>
            <span className="al-c-riepilogo__testo-16">{x.s}</span>
          </span>
        ))}
      </div>
    </Carta>
  )
}

function LeNotti({ d, formato }: { d: Dettaglio; formato: Formato }) {
  const tel = formato === "telefono"
  const colonne = tel
    ? "minmax(0,1fr) auto auto auto"
    : "minmax(140px,1fr) 60px 72px 56px minmax(0,130px) 20px"
  const largo = tel ? "none" : "flex"
  return (
    <Carta
      formato={formato}
      etichetta={t("object.nights")}
      colonne={12}
      ritardo={300}
      padding={MISURE[formato].pad}
      gap={4}
    >
      <span className="al-c-riepilogo__riga-12">
        <span className="al-c-riepilogo__testo-14">{t("object.nights")}</span>
        <span className="al-c-riepilogo__testo-8">
          {t("object.nights.sub", { nome: d.row.name ?? d.row.key })}
        </span>
      </span>
      {d.nights.map(({ night: n, frames, integration_s }) => {
        const c = cielo(n)
        const l = luna(n)
        const data = dataLunga(n.night_date)
        return (
          <Link
            key={n.id}
            className="al-c-riepilogo__centro-2"
            to={`/notti?notte=${n.id}`}
            aria-label={t("object.night.open", { data })}
            style={{ gridTemplateColumns: colonne }}
          >
            <span className="al-c-riepilogo__colonna-13">
              <b className="al-c-riepilogo__testo-20">{data}</b>
              <span className="al-c-riepilogo__testo-8">{n.site}</span>
            </span>
            <span className="al-c-riepilogo__testo-21">
              {integration_s > 0 ? oreEMinuti(integration_s) : t("window.untimed")}
            </span>
            <span className="al-c-riepilogo__testo-22" style={{ display: largo }}>
              {t("window.frames", { n: numero(frames) })}
            </span>
            <span className="al-c-riepilogo__blocco-5" style={{ display: largo }}>
              {l && (
                <>
                  <Luna percento={l.pct} lato={l.lato} misura={20} />
                  {`${numero(l.pct)}%`}
                </>
              )}
            </span>
            <span className="al-c-riepilogo__colonna-14">
              <Pillola
                esito={c.esito === -1 ? "mancante" : c.esito}
                testo={c.pillola}
                segno={segnoDi(c.esito)}
                dimensione="minima"
              />
              <span className="al-c-riepilogo__testo-23" style={{ display: largo }}>
                {c.corto}
              </span>
            </span>
            <span className="al-c-riepilogo__blocco-6" aria-hidden="true">
              {"\u2197"}
            </span>
          </Link>
        )
      })}
    </Carta>
  )
}
