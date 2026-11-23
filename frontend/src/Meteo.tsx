import { useMutation } from "@tanstack/react-query"
import { useEffect, useRef, useState } from "react"
import { useNavigate } from "react-router"

import { api } from "./api/client"
import { useAggiorna, usePrevisione, useRileggi } from "./api/previsione"
import { Avviso } from "./componenti/Avviso"
import { Carta } from "./componenti/Carta"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { Pagina } from "./componenti/Pagina"
import { type CartaScheletro, Scheletro } from "./componenti/Scheletro"
import { Striscia } from "./componenti/Striscia"
import type { Formato } from "./componenti/Tema"
import { type Chiave, t } from "./i18n"
import type { Accesa } from "./MeteoCielo"
import {
  arrivo,
  avvisoDellaPagina,
  type Meteo as Previsione,
  rigaDelServizio,
  tessera,
} from "./MeteoDati"
import { ComeVa, LeMisure } from "./MeteoMisure"
import { LaNotte, type Obiettivo } from "./MeteoNotte"

/**
 * The **Weather** on board v82: the next nights of the home site, one at a time. On top the
 * strip of seven nights with the model and Aggiorna; then the night with its Ore di posa and the
 * sky, what weighs beside the verdict, the measures always in their place, the other measures.
 * Nothing is computed here: verdict, judgements, Ore di posa, order and scales arrive written for
 * each model, and changing model reads another row.
 *
 * - **Out until their step**: the night's story (13.1), the sampling of the setups (14), the
 *   Sun's weather (46.11).
 */

// the skeleton's cards at the real ones' sizes (board v82, `SK`)
const SCHELETRO_DESK: CartaScheletro[] = [
  {
    col: "span 12",
    h: "262px",
    blocchi: [
      { riga: [{ h: "34px", w: "320px" }, t("ui.loading")], tra: true },
      {
        griglia: "repeat(7,minmax(0,1fr))",
        gap: "10px",
        flex: "1",
        figli: [1, 2, 3, 4, 5, 6, 7].map(() => ({ r: "22px" })),
      },
    ],
  },
  {
    col: "span 8",
    h: "640px",
    blocchi: [
      { h: "16px", w: "240px" },
      { h: "64px", w: "280px" },
      { flex: "1" },
      { h: "36px", w: "70%" },
    ],
  },
  {
    col: "span 4",
    h: "640px",
    gap: "14px",
    blocchi: [{ h: "28px", w: "60%" }, { h: "70px" }, { h: "70px" }, { flex: "1" }],
  },
  {
    col: "span 12",
    h: "560px",
    gap: "12px",
    griglia: "repeat(4,minmax(0,1fr))",
    blocchi: [1, 2, 3, 4, 5, 6, 7, 8].map(() => ({ r: "22px" })),
  },
]
const SCHELETRO_TEL: CartaScheletro[] = [
  { h: "230px", blocchi: [{ h: "30px", w: "70%" }, t("ui.loading"), { flex: "1" }] },
  { h: "440px", blocchi: [{ h: "48px", w: "55%" }, { flex: "1" }] },
  {
    h: "300px",
    gap: "10px",
    griglia: "1fr 1fr",
    blocchi: [1, 2, 3, 4].map(() => ({ r: "18px" })),
  },
]

/** What the page keeps while it is open: the chosen night and how its parts are looked at. */
export type Sguardo = {
  /** The thread of the chart, as an index of the drawn hours. */
  ora: number | null
  scegliOra: (i: number | null) => void
  accese: Accesa[]
  accendi: (a: Accesa) => void
  /** Cards fixed to an hour by their bars. */
  fisse: Partial<Record<string, number>>
  fissa: (code: string, i: number | null) => void
  /** The phone card open below its pair. */
  aperta: string | null
  apri: (code: string | null) => void
}

export function Meteo() {
  const formato = useFormato()
  const tel = formato === "telefono"
  const vai = useNavigate()
  const meteo = usePrevisione()
  const rileggi = useRileggi()
  const aggiorna = useAggiorna()
  const modello = useMutation({
    mutationFn: async (scelto: string) => {
      const { error } = await api.PATCH("/api/v1/settings", {
        body: { values: { weather_model: scelto } },
      })
      if (error) throw new Error(scelto)
    },
    onSuccess: rileggi,
  })
  const [scelta, setScelta] = useState(0)
  const [ora, setOra] = useState<number | null>(null)
  const [accese, setAccese] = useState<Accesa[]>([])
  const [fisse, setFisse] = useState<Partial<Record<string, number>>>({})
  const [aperta, setAperta] = useState<string | null>(null)
  const [obiettivo, setObiettivo] = useState<Obiettivo>("deep")
  const detto = meteo.data

  const sguardo: Sguardo = {
    ora,
    scegliOra: setOra,
    accese,
    // humidity adds; a measure on the right replaces the one there (board `toggleM`)
    accendi: (a) =>
      setAccese((ora) =>
        ora.includes(a)
          ? ora.filter((x) => x !== a)
          : a === "humidity"
            ? [...ora, a]
            : [...ora.filter((x) => x === "humidity"), a],
      ),
    fisse,
    fissa: (code, i) =>
      setFisse((ora) => {
        const dopo = { ...ora }
        if (i === null) delete dopo[code]
        else dopo[code] = i
        return dopo
      }),
    aperta,
    apri: setAperta,
  }
  const scegliNotte = (i: number) => {
    setScelta(i)
    setOra(null)
    setFisse({})
    setAperta(null)
  }

  let corpo
  if (meteo.isPending) {
    corpo = (
      <Scheletro
        formato={formato}
        carte={tel ? SCHELETRO_TEL : SCHELETRO_DESK}
        testo={t("ui.loading")}
      />
    )
  } else if (!detto) {
    corpo = (
      <Avviso
        tipo="pagina"
        formato={formato}
        segno="!"
        titolo={t("meteo.failed")}
        azione={t("meteo.retry")}
        onAzione={() => void meteo.refetch()}
      />
    )
  } else {
    const av = avvisoDellaPagina(detto)
    const notte = av ? undefined : (detto.nights[scelta] ?? detto.nights[0])
    const prima = notte === detto.nights[0]
    const sole = obiettivo === "sole"
    // the Sun never sets: no strip, no Come va, the night card on the whole row
    const senzaNotte = notte !== undefined && notte.window === null
    const testa = (
      <LeNotti
        detto={detto}
        formato={formato}
        scelta={notte}
        scegli={scegliNotte}
        striscia={!av && !senzaNotte && !sole}
        aggiorna={() => aggiorna.mutate()}
        occupato={aggiorna.isPending}
        modello={modello.variables ?? null}
        fallito={modello.isError}
        scegliModello={(m) => {
          setAperta(null)
          modello.mutate(m)
        }}
      />
    )
    const avviso = av && (
      <Avviso
        tipo="pagina"
        formato={formato}
        segno={av.segno}
        titolo={av.titolo}
        {...(av.testo ? { testo: av.testo } : {})}
        {...(av.azione
          ? {
              azione: av.azione.l,
              onAzione: () => {
                if (av.azione?.aggiorna) aggiorna.mutate()
                else if (av.azione?.a) void vai(av.azione.a)
              },
            }
          : {})}
      />
    )
    const pezzi = notte && (
      <>
        <LaNotte
          detto={detto}
          notte={notte}
          prima={prima}
          formato={formato}
          sguardo={sguardo}
          obiettivo={obiettivo}
          scegliObiettivo={(o) => {
            setObiettivo(o)
            setOra(null)
            setAperta(null)
          }}
          intera={senzaNotte}
        />
        {!sole && !senzaNotte && (
          <ComeVa
            key={notte.night}
            detto={detto}
            notte={notte}
            prima={prima}
            formato={formato}
            sguardo={sguardo}
          />
        )}
        {!sole && !senzaNotte && !notte.trend && (
          <LeMisure
            detto={detto}
            notte={notte}
            formato={formato}
            sguardo={sguardo}
            aggiorna={() => aggiorna.mutate()}
          />
        )}
      </>
    )
    corpo = (
      <>
        <div className={tel ? "al-meteo__colonna-14" : "al-meteo__griglia-1"}>
          {testa}
          {avviso}
          {pezzi}
        </div>
        {detto.fetched_at !== null && <Piede detto={detto} formato={formato} />}
      </>
    )
  }
  return <Pagina formato={formato}>{corpo}</Pagina>
}

/** The head card: title, when the forecast arrived, the model, Aggiorna, the service's row and
 *  the strip of the seven nights (board v82, `Le notti`). */
function LeNotti({
  detto,
  formato,
  scelta,
  scegli,
  striscia,
  aggiorna,
  occupato,
  modello,
  fallito,
  scegliModello,
}: {
  detto: Previsione
  formato: Formato
  scelta: Previsione["nights"][number] | undefined
  scegli: (i: number) => void
  striscia: boolean
  aggiorna: () => void
  occupato: boolean
  modello: string | null
  fallito: boolean
  scegliModello: (m: string) => void
}) {
  const tel = formato === "telefono"
  const [lungo, setLungo] = useState(false)
  const quando = arrivo(detto)
  const servizio = rigaDelServizio(detto)
  // a model that would not change stays the one there: the row says which
  const stato = fallito
    ? {
        t: t("meteo.model.failed", { m: t(`weather.model.${detto.model}` as Chiave) }),
        a: t("meteo.retry"),
        on: () => modello && scegliModello(modello),
      }
    : servizio
      ? { t: servizio, a: t("weather.refresh"), on: aggiorna }
      : null
  const conModello = detto.site !== null
  // Aggiorna lives in the row when the service is silent, nowhere without a site or a zone
  const conAggiorna =
    conModello &&
    detto.missing === null &&
    !servizio &&
    !(detto.last_request && detto.last_request.status !== "ok")
  const tessere = detto.nights.map((n, i) => tessera(n, i === 0, n === scelta, () => scegli(i)))
  const comandi = (
    <span
      className="al-meteo__riga-18"
      style={tel ? undefined : { display: "flex", gap: 8, alignItems: "center" }}
    >
      {conModello && <MenuDelModello detto={detto} scegli={scegliModello} />}
      {conAggiorna && (
        <a
          className="al-meteo__centro-1"
          href="#"
          role="button"
          aria-label={t("meteo.refresh.label")}
          title={t("weather.refresh")}
          aria-disabled={occupato || undefined}
          onClick={gesto(() => !occupato && aggiorna())}
        >
          <span className="al-meteo__tondo-2" aria-hidden="true">
            {"\u21bb"}
          </span>
        </a>
      )}
    </span>
  )
  const riga = stato && (
    <Avviso
      tipo="riga"
      formato={formato}
      segno="!"
      titolo={stato.t}
      azione={stato.a}
      onAzione={stato.on}
      {...(tel ? { rientro: 20 } : {})}
    />
  )
  const fila = striscia && detto.nights.length > 0 && (
    <Striscia formato={formato} notti={tessere} etichetta={t("meteo.strip")} intestazione={!tel} />
  )
  if (tel) {
    return (
      <Carta formato="telefono" etichetta={t("meteo.title")} ritardo={0} padding="20px 0" gap="14">
        <div className="al-meteo__colonna-15">
          <div className="al-meteo__riga-17">
            <span className="al-meteo__blocco-11">{t("meteo.title")}</span>
            {comandi}
          </div>
          {quando.lungo && (
            <a
              className="al-meteo__riga-23"
              href="#"
              role="button"
              aria-expanded={lungo}
              aria-label={quando.lungo}
              onClick={gesto(() => setLungo(!lungo))}
            >
              <span className="al-meteo__blocco-12">{lungo ? quando.lungo : quando.corto}</span>
              <svg
                className="al-meteo__grafico-1"
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d={lungo ? "M6 15l6-6 6 6" : "M6 9l6 6 6-6"} />
              </svg>
            </a>
          )}
        </div>
        {riga}
        {fila}
      </Carta>
    )
  }
  return (
    <Carta etichetta={t("meteo.title")} colonne={12} ritardo={0} padding="24px 28px 28px" gap="18">
      <div className="al-meteo__riga-1">
        <div className="al-meteo__colonna-1">
          <span className="al-meteo__testo-1">{t("meteo.title")}</span>
          {quando.lungo && <span className="al-meteo__testo-2">{quando.lungo}</span>}
        </div>
        <div className="al-meteo__riga-2">{comandi}</div>
      </div>
      {riga}
      {fila}
    </Carta>
  )
}

/** The model, chosen from a list where each entry says what it is (board v82 `models`). */
function MenuDelModello({ detto, scegli }: { detto: Previsione; scegli: (m: string) => void }) {
  const [aperto, setAperto] = useState(false)
  const qui = useRef<HTMLSpanElement>(null)
  useEffect(() => {
    if (!aperto) return
    const fuori = (ev: MouseEvent) => {
      if (!qui.current?.contains(ev.target as Node)) setAperto(false)
    }
    const esc = (ev: KeyboardEvent) => {
      if (ev.key === "Escape") setAperto(false)
    }
    document.addEventListener("mousedown", fuori)
    document.addEventListener("keydown", esc)
    return () => {
      document.removeEventListener("mousedown", fuori)
      document.removeEventListener("keydown", esc)
    }
  }, [aperto])
  const nome = t(`weather.model.${detto.model}` as Chiave)
  return (
    <span className="al-meteo__riga-19" ref={qui}>
      <a
        className="al-meteo__riga-20"
        href="#"
        role="button"
        aria-haspopup="menu"
        aria-expanded={aperto}
        aria-label={t("meteo.model.label", { m: nome })}
        onClick={gesto(() => setAperto(!aperto))}
      >
        <span className="al-meteo__riga-21">
          {nome}
          <span className="al-meteo__testo-12" aria-hidden="true">
            {"\u25be"}
          </span>
        </span>
      </a>
      {aperto && (
        <div className="al-meteo__strato-3" role="menu">
          {detto.models.map((m) => {
            const sel = m === detto.model
            return (
              <a
                key={m}
                className="al-meteo__riga-22"
                href="#"
                role="menuitemradio"
                aria-checked={sel}
                style={{ background: sel ? "var(--carta-2)" : "transparent" }}
                onClick={gesto(() => {
                  setAperto(false)
                  if (!sel) scegli(m)
                })}
              >
                <span className="al-meteo__colonna-5">
                  <span className="al-meteo__testo-23">{t(`weather.model.${m}` as Chiave)}</span>
                  <span className="al-meteo__testo-14">
                    {t(`weather.model.${m}.what` as Chiave)}
                  </span>
                </span>
                <span aria-hidden="true">{sel ? "\u2713" : ""}</span>
              </a>
            )
          })}
        </div>
      )}
    </span>
  )
}

/** The sources, with the words the services ask for (board v82 footer). */
function Piede({ detto, formato }: { detto: Previsione; formato: Formato }) {
  const cams = detto.sources.find((f) => f.source === "cams")
  const seeing = detto.sources.some((f) => f.source === "meteoblue")
  const copernicus = cams && t("weather.attribution.cams", { anno: cams.fetched_at.slice(0, 4) })
  if (formato === "telefono") {
    const righe = [
      `${t("weather.sources.forecast")} ${t("weather.attribution")}`,
      ...(seeing ? [t("weather.attribution.meteoblue")] : []),
      t("meteo.sources.siteTime"),
    ]
    return (
      <footer className="al-meteo__colonna-29">
        <span>{righe.join(" \u00b7 ")}</span>
        {copernicus && <span>{copernicus}</span>}
      </footer>
    )
  }
  return (
    <footer className="al-meteo__riga-16">
      <span>
        {t("weather.sources.forecast")}{" "}
        <a href="https://open-meteo.com/">{t("weather.attribution")}</a>
      </span>
      {seeing && (
        <span>
          <a href="https://www.meteoblue.com/">{t("weather.attribution.meteoblue")}</a>
        </span>
      )}
      <span>{t("meteo.sources.siteTime")}</span>
      {copernicus && <span className="al-meteo__testo-22">{copernicus}</span>}
    </footer>
  )
}
