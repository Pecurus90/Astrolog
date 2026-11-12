import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "react-router"
import { Link } from "react-router"

import { AnnoDellaDashboard } from "./Anno"
import { api } from "./api/client"
import { useRevisione } from "./api/revisione"
import { Avviso } from "./componenti/Avviso"
import { Carta } from "./componenti/Carta"
import { useFormato } from "./componenti/formato"
import { Pagina } from "./componenti/Pagina"
import { type CartaScheletro, Scheletro } from "./componenti/Scheletro"
import type { Formato } from "./componenti/Tema"
import { DashboardLuna } from "./DashboardLuna"
import { MeteoDellaNotte, ProssimeNotti } from "./DashboardMeteo"
import { DashboardNotte } from "./DashboardNotte"
import { mesiBrevi, mesiIniziali, numero, oreEMinuti, t } from "./i18n"
import { usePrevisione } from "./Meteo"
import { MENTRE_LEGGE_MS } from "./Notti"
import { useStato } from "./Scansiona"
import { useStanotte } from "./Stanotte"

/**
 * The **Dashboard** on board v79: tonight's big card (Night and Solar System), the Moon with its
 * calendar, the night's weather in six cards, the next three nights, what is left to answer, and
 * the year with its filters.
 * Nothing is computed here: the numbers arrive written by `/tonight`, `/weather` and the archive.
 *
 * - **Out until their step**: projects and the finished-projects question (44, 44.1), the Sun
 *   and Kp (46.10-46.12).
 */

// the skeleton's cards at the real ones' sizes (board v79, `SK`)
const SCHELETRO_DESK: CartaScheletro[] = [
  {
    col: "span 7",
    h: "606px",
    blocchi: [
      { riga: [{ h: "36px", w: "300px" }, t("ui.loading")], tra: true },
      { h: "16px", w: "180px" },
      { h: "64px", w: "260px" },
      { h: "16px", w: "62%" },
      { flex: "1", w: "100%" },
      { h: "28px", w: "48%" },
    ],
  },
  {
    col: "span 5",
    h: "606px",
    blocchi: [
      { h: "36px", w: "150px" },
      {
        riga: [
          { h: "76px", w: "76px", r: "50%", flex: "none" },
          {
            figli: [
              { h: "14px", w: "40%" },
              { h: "22px", w: "65%" },
              { h: "14px", w: "55%" },
            ],
            gap: "8px",
            flex: "1",
          },
        ],
        gap: "18px",
      },
      { h: "24px", w: "100%" },
      { flex: "1", w: "100%" },
    ],
  },
  {
    col: "span 12",
    h: "348px",
    blocchi: [
      { h: "24px", w: "220px" },
      {
        griglia: "repeat(6,minmax(0,1fr))",
        gap: "12px",
        flex: "1",
        figli: [1, 2, 3, 4, 5, 6].map(() => ({ h: "100%" })),
      },
    ],
  },
  {
    col: "span 12",
    h: "308px",
    blocchi: [
      { h: "24px", w: "200px" },
      { flex: "1", w: "100%" },
    ],
  },
]
const SCHELETRO_TEL: CartaScheletro[] = [
  {
    h: "470px",
    blocchi: [
      { h: "36px", w: "80%" },
      t("ui.loading"),
      { h: "48px", w: "55%" },
      { flex: "1", w: "100%" },
    ],
  },
  {
    h: "260px",
    blocchi: [
      { h: "36px", w: "45%" },
      { flex: "1", w: "100%" },
    ],
  },
  {
    h: "230px",
    blocchi: [
      { h: "22px", w: "50%" },
      { flex: "1", w: "100%" },
    ],
  },
]

/** The archive in one line: the latest night and the totals. While the spine reads, it rereads. */
function useArchivio(leggendo: boolean) {
  return useQuery({
    queryKey: ["nights", "ultima"],
    refetchInterval: (q) => (leggendo || q.state.data?.still_reading ? MENTRE_LEGGE_MS : false),
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/nights", { params: { query: { limit: 1 } } })
      if (error) throw new Error(t("nights.failed"))
      return data
    },
  })
}

/** The archive folders chosen: the same query as the Settings. */
function useCartelle() {
  return useQuery({
    queryKey: ["folders"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/v1/folders")
      if (error) throw new Error(t("settings.folders.failed"))
      return data
    },
  })
}

type Passo = {
  titolo: string
  testo: string
  azione?: { l: string; a: string }
  barra?: { pct: number; righe: string[] }
}

/** A step of Per cominciare: the first one full, the second in outline (board v55.4). */
function PassoDelVia({ passo: p, n, formato }: { passo: Passo; n: number; formato: Formato }) {
  const tel = formato === "telefono"
  const primo = n === 1
  const tondo = {
    background: primo ? "var(--accento)" : "transparent",
    color: primo ? "var(--giorno-su-testo)" : "var(--tenue)",
    boxShadow: primo ? "none" : "inset 0 0 0 1.5px var(--linea)",
  }
  const fondo = { background: primo ? "var(--carta-2)" : "transparent" }
  const azione = p.azione && (
    <Link
      className={`al-bottone ${primo ? "al-bottone--pieno" : "al-bottone--contorno"}${tel ? " al-bottone--blocco" : ""}`}
      to={p.azione.a}
    >
      {p.azione.l}
    </Link>
  )
  const barra = p.barra && (
    <>
      <span
        className="al-dash__riga-23"
        role="progressbar"
        aria-label={t("dashboard.scan.bar")}
        aria-valuenow={p.barra.pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <span className="al-dash__pillola-5" style={{ width: `${p.barra.pct}%` }} />
      </span>
      <span className={tel ? "al-dash__colonna-18" : "al-dash__riga-24"}>
        {p.barra.righe.map((r) => (
          <span key={r} className={tel ? "al-dash__testo-40" : "al-dash__pillola-6"}>
            {r}
          </span>
        ))}
      </span>
    </>
  )
  if (tel) {
    return (
      <div className="al-dash__colonna-28" style={{ ...fondo, padding: primo ? "16px" : "0 16px" }}>
        <span className="al-dash__riga-41">
          <span className="al-dash__tondo-14" style={tondo}>
            {numero(n)}
          </span>
          <b className="al-dash__testo-38" style={{ fontWeight: primo ? 600 : 500 }}>
            {p.titolo}
          </b>
        </span>
        <span className="al-dash__testo-39">{p.testo}</span>
        {barra}
        {azione}
      </div>
    )
  }
  return (
    <div
      className="al-dash__griglia-8"
      style={{ ...fondo, padding: primo ? "18px 20px" : "2px 20px 6px" }}
    >
      <span className="al-dash__tondo-9" style={tondo}>
        {numero(n)}
      </span>
      <span className="al-dash__colonna-2">
        <b style={{ fontSize: primo ? "17px" : "16px", fontWeight: primo ? 600 : 500 }}>
          {p.titolo}
        </b>
        <span className="al-dash__testo-21">{p.testo}</span>
        {barra && <span className="al-dash__colonna-14">{barra}</span>}
      </span>
      {azione}
    </div>
  )
}

function PerCominciare({ passi, formato }: { passi: Passo[]; formato: Formato }) {
  const titolo = t("dashboard.start.title")
  if (formato === "telefono") {
    return (
      <Carta formato="telefono" etichetta={titolo} ritardo={240} padding="20px" gap="14">
        <span className="al-dash__testo-29">{titolo}</span>
        {passi.map((p, i) => (
          <PassoDelVia key={p.titolo} passo={p} n={i + 1} formato={formato} />
        ))}
      </Carta>
    )
  }
  return (
    <Carta padding="24px 28px" gap="16">
      <span className="al-dash__testo-1">{titolo}</span>
      {passi.map((p, i) => (
        <PassoDelVia key={p.titolo} passo={p} n={i + 1} formato={formato} />
      ))}
    </Carta>
  )
}

/** The year before the first scan: twelve empty months (board `monthsEmpty`). */
function AnnoVuoto({ anno }: { anno: string }) {
  const mesi = mesiBrevi()
  const iniziali = mesiIniziali()
  const tratteggio =
    "repeating-linear-gradient(135deg, var(--barretta-spenta) 0 3px, transparent 3px 8px)"
  return (
    <Carta padding="24px 28px" gap="14" flex="1">
      <div className="al-dash__riga-25">
        <span className="al-dash__testo-1">{t("dashboard.year.empty.title", { anno })}</span>
        <span className="al-dash__testo-2">{t("dashboard.year.empty.sub")}</span>
      </div>
      <div className="al-dash__griglia-9" aria-hidden="true">
        {mesi.map((m) => (
          <span key={m} className="al-dash__pillola-8" style={{ background: tratteggio }} />
        ))}
      </div>
      <div className="al-dash__griglia-10" aria-hidden="true">
        {mesi.map((m, i) => (
          <span key={m}>
            <span className="al-dash__mese-lungo">{m}</span>
            <span className="al-dash__mese-corto">{iniziali[i]}</span>
          </span>
        ))}
      </div>
      <span className="al-dash__testo-2">{t("dashboard.year.empty.text")}</span>
    </Carta>
  )
}

type Riga = {
  segno: "!" | "?"
  titolo: string
  testo: string
  azione: string
  a: string
  vai: boolean
}

/** What is left half answered: the cases to confirm and the frames outside every night. */
function DaRiprendere({
  righe,
  errore,
  formato,
}: {
  righe: Riga[]
  errore: string | null
  formato: Formato
}) {
  const tel = formato === "telefono"
  const titolo = t("dashboard.redo.title")
  const riga = (r: Riga) => (
    <div key={r.titolo} className={tel ? "al-dash__griglia-16" : "al-dash__griglia-2"}>
      <span
        className="al-dash__tondo-1"
        aria-hidden="true"
        style={
          r.segno === "!"
            ? { background: "var(--avviso)", color: "var(--avviso-testo)" }
            : {
                background: "var(--carta)",
                color: "var(--testo)",
                boxShadow: "inset 0 0 0 1.5px var(--linea)",
              }
        }
      >
        {r.segno}
      </span>
      <span className="al-dash__colonna-1">
        <b className="al-dash__testo-3">{r.titolo}</b>
        {r.testo && <span className="al-dash__testo-4">{r.testo}</span>}
      </span>
      {r.vai ? (
        <Link className="al-dash__tondo-3" to={r.a} aria-label={r.azione} title={r.azione}>
          {"\u2197"}
        </Link>
      ) : (
        <Link
          className={
            tel
              ? "al-bottone al-bottone--pieno al-bottone--blocco al-dash__riga-29"
              : "al-bottone al-bottone--pieno al-bottone--piccolo"
          }
          to={r.a}
        >
          {r.azione}
        </Link>
      )}
    </div>
  )
  if (tel) {
    return (
      <Carta formato="telefono" etichetta={titolo} ritardo={0} padding="20px" gap="10">
        <span className="al-dash__testo-29">{titolo}</span>
        {errore && <Avviso tipo="riga" formato={formato} segno="!" titolo={errore} />}
        {righe.map(riga)}
      </Carta>
    )
  }
  return (
    <Carta colonne={12} ritardo={0} padding="20px 24px" gap="10">
      <div className="al-dash__riga-1">
        <span className="al-dash__testo-1">{titolo}</span>
        <span className="al-dash__testo-2">{t("dashboard.redo.sub")}</span>
      </div>
      {errore && <Avviso tipo="riga" formato={formato} segno="!" titolo={errore} />}
      {righe.map(riga)}
    </Carta>
  )
}

export function Dashboard() {
  const formato = useFormato()
  const tel = formato === "telefono"
  const vai = useNavigate()
  const stanotte = useStanotte()
  const meteo = usePrevisione()
  const pipeline = useStato().data
  const scan = pipeline?.scan
  // the first read ends when `group` gave every frame its night, not with the scan stage
  const primaInCorso = scan?.first === true && pipeline?.worker.state === "running"
  const cartelle = useCartelle().data
  const archivio = useArchivio(primaInCorso).data
  const primaLettura =
    (scan?.first === true && scan.state === "running") ||
    (scan?.first === true && (archivio ? archivio.still_reading > 0 : primaInCorso))
  const revisione = useRevisione()
  const s = stanotte.data
  const m = meteo.data

  let corpo
  if (stanotte.isPending || (meteo.isPending && !meteo.isError)) {
    corpo = (
      <Scheletro
        formato={formato}
        carte={tel ? SCHELETRO_TEL : SCHELETRO_DESK}
        testo={t("ui.loading")}
      />
    )
  } else if (!s) {
    corpo = (
      <Avviso
        tipo="pagina"
        formato={formato}
        segno="!"
        titolo={t("tonight.failed")}
        azione={t("dashboard.retry")}
        onAzione={() => void stanotte.refetch()}
      />
    )
  } else {
    const sito = s.site !== null
    const vuoto = cartelle?.total === 0 && archivio?.totals?.frames === 0
    // the archive does not hang on the site: without a site its answers still wait
    const senzaArchivio = vuoto || primaLettura
    const anno = (s.night ?? new Date().toISOString()).slice(0, 4)
    const cartella: Passo = {
      titolo: t("dashboard.start.folder.title"),
      testo: t("dashboard.start.folder.text"),
      azione: { l: t("dashboard.start.folder.how"), a: "/impostazioni/cartelle" },
    }
    const passi: Passo[] = !sito
      ? [
          {
            titolo: t("dashboard.start.site.title"),
            testo: t("dashboard.start.site.text"),
            azione: { l: t("dashboard.start.site.how"), a: "/impostazioni/sito" },
          },
          ...(vuoto ? [cartella] : []),
        ]
      : !senzaArchivio
        ? []
        : primaLettura
          ? [
              {
                titolo: t("dashboard.start.scan.title"),
                testo: t("dashboard.start.scan.text"),
                barra: {
                  pct: scan?.last_event?.total
                    ? Math.round((scan.last_event.current / scan.last_event.total) * 100)
                    : 0,
                  righe: [
                    scan?.last_event
                      ? scan.remaining_s
                        ? t("dashboard.start.scan.files.eta", {
                            fatti: numero(scan.last_event.current),
                            su: numero(scan.last_event.total),
                            quanto: oreEMinuti(scan.remaining_s),
                          })
                        : t("dashboard.start.scan.files", {
                            fatti: numero(scan.last_event.current),
                            su: numero(scan.last_event.total),
                          })
                      : t("dashboard.start.scan.starting"),
                    t("dashboard.start.scan.later"),
                  ],
                },
              },
              {
                titolo: t("dashboard.start.project.title"),
                testo: t("dashboard.start.project.sofar", {
                  n: numero(archivio?.totals?.objects ?? 0),
                }),
                azione: { l: t("dashboard.start.project.how"), a: "/progetti" },
              },
            ]
          : [
              cartella,
              {
                titolo: t("dashboard.start.project.title"),
                testo: t("dashboard.start.project.text"),
              },
            ]
    const righe: Riga[] = []
    const daConfermare = revisione.data?.to_confirm ?? 0
    if (!senzaArchivio && daConfermare > 0) {
      righe.push({
        segno: "!",
        titolo: t("dashboard.redo.toConfirm", { n: numero(daConfermare) }),
        testo: "",
        azione: t("dashboard.redo.answer"),
        a: "/da-confermare",
        vai: false,
      })
    }
    if (!senzaArchivio && archivio && archivio.waiting_frames > 0) {
      righe.push({
        segno: "?",
        titolo: t(
          archivio.waiting_frames === 1 ? "dashboard.work.outside.one" : "dashboard.work.outside",
          { n: numero(archivio.waiting_frames) },
        ),
        testo: t("dashboard.redo.outside.text"),
        azione: t("dashboard.redo.outside.how"),
        a: "/notti",
        vai: true,
      })
    }
    const fuso = sito && s.night === null
    const avviso = fuso && (
      <Avviso
        tipo="pagina"
        formato={formato}
        segno="!"
        titolo={t("dashboard.noZone.title")}
        testo={t("dashboard.noZone.text", { sito: s.site?.name ?? "" })}
        azione={t("dashboard.noZone.how")}
        onAzione={() => void vai("/impostazioni/sito")}
      />
    )
    const notte = sito && <DashboardNotte stanotte={s} notte={m?.nights[0]} formato={formato} />
    const luna = sito && <DashboardLuna stanotte={s} meteo={m} formato={formato} />
    const tempo = sito && m && <MeteoDellaNotte meteo={m} formato={formato} />
    const prossime = sito && m && (
      <ProssimeNotti meteo={m} colonne={senzaArchivio ? 4 : 12} formato={formato} />
    )
    const inizio = passi.length > 0 && <PerCominciare passi={passi} formato={formato} />
    // a zero on an archive that did not answer would be a reassuring lie: it is said
    const errore = senzaArchivio ? null : (revisione.error?.message ?? null)
    const riprendi = (righe.length > 0 || errore) && (
      <DaRiprendere righe={righe} errore={errore} formato={formato} />
    )
    if (tel) {
      corpo = (
        <div className="al-dash__colonna-17">
          {avviso}
          {riprendi}
          {notte}
          {luna}
          {tempo}
          {inizio}
          {prossime}
          {!senzaArchivio && <AnnoDellaDashboard formato={formato} anno={anno} />}
        </div>
      )
    } else {
      corpo = (
        <div className="al-dash__griglia-1">
          {avviso}
          {riprendi}
          {notte}
          {luna}
          {tempo}
          {(inizio || senzaArchivio) && (
            <div
              className="al-dash__colonna-13"
              data-anim="1"
              style={{ gridColumn: sito ? "span 8" : "span 12", animationPlayState: "running" }}
            >
              {inizio}
              {senzaArchivio && <AnnoVuoto anno={anno} />}
            </div>
          )}
          {prossime}
          {!senzaArchivio && <AnnoDellaDashboard formato={formato} anno={anno} />}
        </div>
      )
    }
  }
  return <Pagina formato={formato}>{corpo}</Pagina>
}
