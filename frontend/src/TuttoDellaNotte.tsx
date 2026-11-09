/**
 * **Tutto della notte** (tavola v76, `componenti/FinestraRiepilogo.dc.html` e
 * `componenti/Riepilogo.dc.html`, tipo `notte`): il riepilogo di una notte in una finestra sopra
 * le Notti, larga 1180 sul desktop, pagina intera sul telefono. Si chiude con x, Esc o fuori;
 * le frecce vanno alla notte prima e dopo. Formatta e basta: la notte, i setup e il catalogo da
 * `GET /api/v1/nights/{id}`, le misure da `GET /api/v1/nights/{id}/measures`.
 */
import { useQuery } from "@tanstack/react-query"

import { useApriOggetto } from "./apriOggetto"
import { api } from "./api/client"
import { gesto } from "./componenti/gesto"
import type { components } from "./api/schema"
import { Avviso } from "./componenti/Avviso"
import { Carta } from "./componenti/Carta"
import { Pillola } from "./componenti/Pillola"
import { Scheletro } from "./componenti/Scheletro"
import type { Formato } from "./componenti/Tema"
import { dataLunga, numero, oraDelSito, oreEMinuti, t } from "./i18n"
import { MisureDeiFrame } from "./MisureDeiFrame"
import { medianeInTesta } from "./MisureDati"
import { MENTRE_LEGGE_MS } from "./Notti"
import { cielo, segnoDi } from "./NottiDati"
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
import { costellazione } from "./costellazioni"

type Dettaglio = components["schemas"]["NightDetail"]

class NonTrovata extends Error {}

async function dettaglio(id: number): Promise<Dettaglio> {
  const { data, error, response } = await api.GET("/api/v1/nights/{night_id}", {
    params: { path: { night_id: id } },
  })
  if (response.status === 404) throw new NonTrovata()
  if (error) throw new Error(t("window.failed"))
  return data
}

async function misure(id: number) {
  const { data, error } = await api.GET("/api/v1/nights/{night_id}/measures", {
    params: { path: { night_id: id } },
  })
  if (error) throw new Error(t("window.failed"))
  return data
}

export function TuttoDellaNotte({
  id,
  formato,
  onChiudi,
  onPrima,
  onDopo,
}: {
  id: number
  formato: Formato
  onChiudi: () => void
  onPrima?: (() => void) | undefined
  onDopo?: (() => void) | undefined
}) {
  const tel = formato === "telefono"
  const notte = useQuery({
    queryKey: ["nights", "detail", id],
    queryFn: () => dettaglio(id),
    retry: (n, e) => !(e instanceof NonTrovata) && n < 2,
  })
  const mis = useQuery({
    queryKey: ["nights", "measures", id],
    queryFn: () => misure(id),
    refetchInterval: (q) => ((q.state.data?.pending ?? 0) > 0 ? MENTRE_LEGGE_MS : false),
  })
  const L = MISURE[formato]

  let corpo
  if (notte.isPending) {
    corpo = (
      <Scheletro
        formato={formato}
        carte={SCHELETRO}
        griglia="minmax(0,1fr)"
        gap={L.gap}
        testo={t("window.loading")}
      />
    )
  } else if (notte.error instanceof NonTrovata) {
    corpo = (
      <Avviso
        tipo="pagina"
        formato={formato}
        segno="?"
        titolo={t("window.gone")}
        testo={t("window.gone.text")}
      />
    )
  } else if (notte.isError) {
    corpo = (
      <Avviso
        tipo="pagina"
        formato={formato}
        segno="!"
        titolo={t("window.failed")}
        testo={t("window.failed.text")}
        azione={t("window.retry")}
        onAzione={() => void notte.refetch()}
      />
    )
  } else {
    const d = notte.data
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
          onChiudi={onChiudi}
          onPrima={onPrima}
          onDopo={onDopo}
        />
        <Setups setups={d.rigs} formato={formato} />
        <Oggetti d={d} formato={formato} onChiudi={onChiudi} />
        <div className="al-c-riepilogo__blocco-4">
          {mis.data && <MisureDeiFrame key={id} misure={mis.data} formato={formato} />}
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
      </div>
    )
  }

  return (
    <FinestraRiepilogo aria={t("window.night")} formato={formato} onChiudi={onChiudi}>
      {corpo}
    </FinestraRiepilogo>
  )
}

function Testa({
  d,
  misure: m,
  formato,
  onChiudi,
  onPrima,
  onDopo,
}: {
  d: Dettaglio
  misure: components["schemas"]["NightMeasures"] | undefined
  formato: Formato
  onChiudi: () => void
  onPrima?: (() => void) | undefined
  onDopo?: (() => void) | undefined
}) {
  const n = d.night
  const L = MISURE[formato]
  const conOre = n.integration_s > 0
  const periodo =
    d.first_start && d.last_end
      ? t("window.span", { sito: n.site, da: oraDelSito(d.first_start), a: oraDelSito(d.last_end) })
      : t("window.span.untimed", { sito: n.site })
  const grande = conOre ? oreEMinuti(n.integration_s) : t("window.frames", { n: numero(n.frames) })
  const sotto = conOre
    ? `${t("window.frames", { n: numero(n.frames) })} \u00B7 ${t("window.objects", { n: n.objects.length })}`
    : t("window.untimed")
  const kpi = medianeInTesta(m)
  const c = cielo(n)
  const esito = (
    <Pillola
      esito={c.esito === -1 ? "mancante" : c.esito}
      testo={c.pillola}
      segno={segnoDi(c.esito)}
      dimensione="piccola"
      allinea="flex-start"
    />
  )
  const filtri = <FiltriInTesta filtri={n.filters} />
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
        siti={[n.site]}
        formato={formato}
        prima="nights.prev"
        dopo="nights.next"
        onChiudi={onChiudi}
        onPrima={onPrima}
        onDopo={onDopo}
      />
      <div className="al-c-riepilogo__colonna-1">
        <span className="al-c-riepilogo__testo-1">{t("window.above")}</span>
        <span className="al-c-riepilogo__riga-5">
          <b className="al-c-riepilogo__testo-2" style={{ fontSize: L.tfs }}>
            {dataLunga(n.night_date)}
          </b>
        </span>
        <span className="al-c-riepilogo__testo-4">{periodo}</span>
      </div>
      <NumeriInTesta
        formato={formato}
        grande={grande}
        sotto={sotto}
        conOre={conOre}
        kpi={kpi}
        esito={esito}
        filtri={filtri}
      />
    </Carta>
  )
}

export function distanza(f: components["schemas"]["ObjectFacts"]): string {
  if (!f.distance) return t("window.fact.distance.none")
  return t(f.distance.unit === "ly" ? "window.fact.ly" : "window.fact.mly", {
    n: numero(f.distance.value),
  })
}

export function estensione(f: components["schemas"]["ObjectFacts"]): string {
  return f.extent_ly != null
    ? t("window.fact.extent.value", { n: numero(f.extent_ly) })
    : t("window.fact.extent.none")
}

function Oggetti({
  d,
  formato,
  onChiudi,
}: {
  d: Dettaglio
  formato: Formato
  onChiudi: () => void
}) {
  const fatti = new Map(d.objects.map((f) => [f.key, f]))
  const apriOggetto = useApriOggetto()
  return (
    <Carta
      formato={formato}
      etichetta={t("window.objects.title")}
      colonne={12}
      ritardo={60}
      padding={MISURE[formato].pad}
      gap={14}
    >
      <span className="al-c-riepilogo__riga-10">
        <span className="al-c-riepilogo__testo-14">{t("window.objects.title")}</span>
        <span className="al-c-riepilogo__testo-8">{t("window.objects.sub")}</span>
      </span>
      <div className="al-c-riepilogo__griglia-3">
        {d.night.objects.map((o) => {
          const f = fatti.get(o.key)
          const dentro = !!f && inCatalogo(f)
          const tipo = f && tipoDi(f)
          const dati =
            dentro && f
              ? [
                  { l: t("window.fact.type"), v: tipo ? t(tipo) : "\u2014" },
                  {
                    l: t("window.fact.constellation"),
                    v: f.constellation ? costellazione(f.constellation) : "\u2014",
                  },
                  { l: t("window.fact.distance"), v: distanza(f) },
                  { l: t("window.fact.extent"), v: estensione(f) },
                ]
              : []
          const nome = !dentro ? t("window.objects.outside") : (f?.common_name ?? "")
          return (
            <span key={o.key} className="al-c-riepilogo__colonna-10">
              <span className="al-c-riepilogo__riga-11">
                <span className="al-c-riepilogo__colonna-11">
                  {apriOggetto ? (
                    // one window at a time: two would close together on the same Esc
                    <a
                      href="#"
                      aria-haspopup="dialog"
                      onClick={gesto(() => {
                        onChiudi()
                        apriOggetto(o.key, o.name ?? o.key)
                      })}
                    >
                      <b className="al-c-riepilogo__testo-17">{o.name ?? o.key}</b>
                    </a>
                  ) : (
                    <b className="al-c-riepilogo__testo-17">{o.name ?? o.key}</b>
                  )}
                  {nome && <span className="al-c-riepilogo__testo-12">{nome}</span>}
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: 8, flex: "none" }}>
                  <span className="al-c-riepilogo__testo-18">
                    {o.integration_s > 0
                      ? oreEMinuti(o.integration_s)
                      : t("window.frames", { n: numero(o.frames) })}
                  </span>
                </span>
              </span>
              {dati.length > 0 && (
                <span className="al-c-riepilogo__griglia-4">
                  {dati.map((x) => (
                    <span key={x.l} style={{ display: "contents" }}>
                      <span className="al-c-riepilogo__testo-3">{x.l}</span>
                      <span className="al-c-riepilogo__testo-19">{x.v}</span>
                    </span>
                  ))}
                </span>
              )}
            </span>
          )
        })}
      </div>
    </Carta>
  )
}
