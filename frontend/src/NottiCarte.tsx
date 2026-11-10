/**
 * Le carte delle Notti (tavola v76, `Notti.dc.html` 35-57, 71-95, 122-154): la notte
 * protagonista, l'elenco a confronto, tutto l'archivio. Formattano e basta.
 */
import { Link } from "react-router"

import { Avviso } from "./componenti/Avviso"
import { BarraFiltri } from "./componenti/BarraFiltri"
import { Carta } from "./componenti/Carta"
import { gesto } from "./componenti/gesto"
import { Luna } from "./componenti/Luna"
import { Pillola } from "./componenti/Pillola"
import { Ripresa } from "./componenti/Ripresa"
import type { Formato } from "./componenti/Tema"
import { type Chiave, maiuscola, meseEAnno, numero, ore, t } from "./i18n"
import {
  type Elenco,
  type Notte,
  cielo,
  filtri,
  fonteDelSito,
  giornoBreve,
  luna,
  numeri,
  oggetti,
  oggettiInFila,
  oreDi,
  ripresa,
  segnoDi,
  sommaDelMese,
  testaDelCielo,
  titoloDi,
} from "./NottiDati"

const PIN =
  "M12 21s7-6.3 7-11.5A7 7 0 0 0 5 9.5C5 14.7 12 21 12 21zM12 7.5a2 2 0 1 0 0 4 2 2 0 0 0 0-4z"

function Sito({ notte, telefono }: { notte: Notte; telefono: boolean }) {
  const misura = telefono ? 13 : 14
  const fonte = fonteDelSito(notte)
  return (
    // v78: name and source with the dots, both whole in the title
    <span
      className={telefono ? "al-notti__riga-27" : "al-notti__riga-5"}
      title={`${notte.site} \u00B7 ${fonte}`}
    >
      <svg
        width={misura}
        height={misura}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d={PIN} />
      </svg>
      <span className="al-notti__sito-nome">{notte.site}</span>
      <span className="al-notti__sito-fonte">{`\u00B7 ${fonte}`}</span>
    </span>
  )
}

// the full ticks take the outcome's colour (tavola: `t.pills[e][1]`)
const PIENE = ["var(--buono-testo)", "var(--incerto-testo)", "var(--non-adatto-testo)"]

function Tacche({
  tutte,
  piene,
  esito,
  telefono,
}: {
  tutte: number
  piene: number
  esito: number
  telefono: boolean
}) {
  return (
    <span className={telefono ? "al-notti__riga-31" : "al-notti__riga-9"} aria-hidden="true">
      {Array.from({ length: tutte }, (_, i) => (
        <span
          key={i}
          className="al-notti__pillola-1"
          style={{ background: i < piene ? PIENE[esito] : "var(--barretta-spenta)" }}
        />
      ))}
    </span>
  )
}

/** La notte protagonista: titolo, sito, ore, cielo, Luna, oggetti e filtri. */
export function Protagonista({
  notte,
  formato,
  sola,
  onPrima,
  onDopo,
  onApri,
}: {
  notte: Notte
  formato: Formato
  sola: boolean
  onPrima?: (() => void) | undefined
  onDopo?: (() => void) | undefined
  /** La freccia di Tutto della notte: la finestra col riepilogo. */
  onApri: () => void
}) {
  const tel = formato === "telefono"
  const apri = (
    <a
      className="al-notti__tondo-1"
      href="#"
      onClick={gesto(onApri)}
      aria-haspopup="dialog"
      aria-label={t("window.night")}
      title={t("window.night")}
    >
      {"\u2197"}
    </a>
  )
  const c = cielo(notte)
  const r = ripresa(notte)
  const l = luna(notte)
  const o = oggetti(notte)
  const num = numeri(notte)
  const segno = segnoDi(c.esito)
  const pillola = (
    <Pillola
      esito={c.esito === -1 ? "mancante" : c.esito}
      testo={c.pillola}
      segno={segno}
      fondo="carta"
      dimensione="piccola"
    />
  )
  const modifica = c.modificaSito && (
    <Link
      to="/impostazioni/sito"
      className={
        tel
          ? "al-bottone al-bottone--pieno al-bottone--blocco al-notti__testo-28"
          : "al-bottone al-bottone--pieno al-bottone--piccolo"
      }
    >
      {t("nights.sky.unknown.how")}
    </Link>
  )
  const tacche = c.tacche && (
    <>
      <Tacche tutte={c.tacche.tutte} piene={c.tacche.piene} esito={c.esito} telefono={tel} />
      <span className={tel ? "al-notti__testo-11" : "al-notti__testo-2"}>{t("nights.ticks")}</span>
    </>
  )
  const elencoOggetti = (
    <div className={tel ? "al-notti__colonna-17" : "al-notti__colonna-3"}>
      <span className={tel ? "al-notti__testo-11" : "al-notti__testo-2"}>
        {t("nights.objects")}
      </span>
      {o.primi.map((x) => (
        <span key={x.nome} className={tel ? "al-notti__griglia-8" : "al-notti__griglia-4"}>
          <b className={tel ? "al-notti__blocco-11" : "al-notti__blocco-3"}>{x.nome}</b>
          <span className="al-notti__riga-11">
            <span className="al-notti__pillola-2" data-an="barra" style={{ width: x.larghezza }} />
          </span>
          <span className={tel ? "al-notti__testo-29" : "al-notti__testo-7"}>{x.ore}</span>
        </span>
      ))}
      {o.altri && (
        <span className={tel ? "al-notti__testo-11" : "al-notti__testo-2"}>{o.altri}</span>
      )}
    </div>
  )
  const elencoFiltri = (
    <div className={tel ? "al-notti__colonna-18" : "al-notti__colonna-3"}>
      <span className={tel ? "al-notti__testo-11" : "al-notti__testo-2"}>
        {t("nights.filters")}
      </span>
      <BarraFiltri filtri={filtri(notte)} anima righe formato={formato} />
    </div>
  )

  if (tel) {
    return (
      <Carta
        formato="telefono"
        etichetta={t("nights.night")}
        tono="protagonista"
        ritardo={60}
        padding="20px 16px"
        gap={16}
      >
        <div className="al-notti__riga-26">
          <span className="al-notti__colonna-7">
            <b className="al-notti__testo-24">{titoloDi(notte)}</b>
            <Sito notte={notte} telefono />
          </span>
          {!sola && (
            <span className="al-notti__riga-28">
              <a
                className="al-notti__tondo-1"
                href="#"
                onClick={gesto(onPrima)}
                aria-label={t("nights.prev")}
                aria-disabled={onPrima ? undefined : "true"}
                style={{ opacity: onPrima ? 1 : 0.35 }}
              >
                {"\u2039"}
              </a>
              <a
                className="al-notti__tondo-1"
                href="#"
                onClick={gesto(onDopo)}
                aria-label={t("nights.next")}
                aria-disabled={onDopo ? undefined : "true"}
                style={{ opacity: onDopo ? 1 : 0.35 }}
              >
                {"\u203A"}
              </a>
            </span>
          )}
          {apri}
        </div>
        <div className="al-notti__riga-29">
          <span className="al-notti__testo-25" data-an="big">
            {num.grande}
          </span>
          <span className="al-notti__colonna-15">
            <span className="al-notti__testo-26">{num.parola}</span>
            <span className="al-notti__testo-11">{num.sotto}</span>
          </span>
        </div>
        <div className="al-notti__colonna-16">
          <span className="al-notti__riga-30">
            <span className="al-notti__testo-11">{t("nights.sky")}</span>
            {pillola}
          </span>
          <b className="al-notti__testo-23">{c.titolo}</b>
          <span className="al-notti__testo-27">{c.sotto}</span>
          {r && <Ripresa tipo={r.tipo} testo={r.testo} />}
          {tacche}
          {modifica}
          {l && (
            <span className="al-notti__riga-32">
              <Luna
                percento={l.pct}
                lato={l.lato}
                misura={34}
                titolo={l.titolo}
                testo={l.testo}
                formato="telefono"
              />
            </span>
          )}
        </div>
        {elencoOggetti}
        {elencoFiltri}
      </Carta>
    )
  }

  return (
    <Carta
      formato="desktop"
      etichetta={t("nights.night")}
      tono="protagonista"
      colonne={sola ? 12 : 8}
      ritardo={0}
      padding="28px"
      gap={22}
    >
      <div className="al-notti__riga-3">
        <span className="al-notti__riga-4">
          <b className="al-notti__testo-3">{titoloDi(notte)}</b>
          <Sito notte={notte} telefono={false} />
        </span>
        {apri}
      </div>
      <div className="al-notti__riga-6">
        <span className="al-notti__testo-4" data-an="big">
          {num.grande}
        </span>
        <span className="al-notti__colonna-1">
          <span className="al-notti__testo-5">{num.parola}</span>
          <span className="al-notti__testo-2">{num.sotto}</span>
        </span>
      </div>
      <div className="al-notti__riga-7">
        {pillola}
        <span className="al-notti__colonna-2">
          <b className="al-notti__testo-6">{c.titolo}</b>
          <span className="al-notti__testo-2">{c.sotto}</span>
          {r && (
            <span className="al-notti__riga-8">
              <Ripresa tipo={r.tipo} testo={r.testo} />
            </span>
          )}
        </span>
        {tacche && <span className="al-notti__barra-posa">{tacche}</span>}
        {modifica}
        {l && (
          <span className="al-notti__riga-10">
            <Luna
              percento={l.pct}
              lato={l.lato}
              misura={30}
              titolo={l.titolo}
              testo={l.testo}
              formato="desktop"
            />
          </span>
        )}
      </div>
      <div className="al-notti__griglia-3">
        {elencoOggetti}
        {elencoFiltri}
      </div>
    </Carta>
  )
}

/** Una riga di *A confronto*. */
function Riga({
  notte,
  scelta,
  onScegli,
}: {
  notte: Notte
  scelta: boolean
  onScegli: () => void
}) {
  const c = cielo(notte)
  const r = ripresa(notte)
  const l = luna(notte)
  const tempo = oreDi(notte.integration_s) ?? t("nights.untimed")
  const [dow = "", giorno = ""] = giornoBreve(notte).split(" ")
  return (
    <a
      className="al-notti__griglia-6"
      data-an="riga"
      role="button"
      href="#"
      onClick={gesto(onScegli)}
      aria-pressed={scelta ? "true" : "false"}
      aria-label={t("nights.row", {
        giorno: titoloDi(notte),
        sito: notte.site,
        ore: tempo,
        cielo: c.letto ? `${c.pillola}, ${c.letto}` : c.pillola,
      })}
      style={{
        background: scelta ? "var(--carta-2)" : "transparent",
        boxShadow: `inset 0 0 0 2px ${scelta ? "var(--accento)" : "transparent"}`,
      }}
    >
      <span className="al-notti__colonna-5">
        <span className="al-notti__testo-10">{giorno}</span>
        <span className="al-notti__testo-11">{dow}</span>
      </span>
      <span className="al-notti__colonna-6">
        <b className="al-notti__blocco-5">{notte.site}</b>
        <span className="al-notti__blocco-6">{oggettiInFila(notte)}</span>
      </span>
      <span className="al-notti__colonna-5">
        <span className="al-notti__testo-12">{tempo}</span>
        <span className="al-notti__testo-13">
          {t("nights.frames", { n: numero(notte.frames) })}
        </span>
      </span>
      <span className="al-notti__colonna-7">
        <BarraFiltri filtri={filtri(notte)} altezza={8} />
        <span className="al-notti__blocco-7">
          {notte.filters.map((f) => f.name).join(" \u00B7 ")}
        </span>
      </span>
      <span className="al-notti__colonna-8">
        <Pillola
          esito={c.esito === -1 ? "mancante" : c.esito}
          testo={c.pillola}
          segno={segnoDi(c.esito)}
          fondo={scelta ? "carta" : "carta2"}
          dimensione="minima"
        />
        <span className="al-notti__testo-13">{c.corto}</span>
        {r && <Ripresa tipo={r.tipo} testo={r.testo} />}
      </span>
      <span className="al-notti__riga-17">
        {l && <Luna percento={l.pct} lato={l.lato} misura={22} />}
        {l ? `${numero(l.pct)}%` : ""}
      </span>
    </a>
  )
}

const COLONNE: Chiave[] = [
  "nights.list.day",
  "nights.list.where",
  "nights.list.time",
  "nights.list.filters",
  "nights.list.sky",
  "nights.list.moon",
]

/** *A confronto*: le notti per mese, 20 alla volta. */
export function AConfronto({
  notti,
  mesi,
  colonne,
  sotto,
  conta,
  scelta,
  onScegli,
  altre,
}: {
  notti: Notte[]
  mesi: Elenco["months"]
  colonne: number
  sotto: string
  conta: string
  scelta: number | undefined
  onScegli: (id: number) => void
  altre: {
    testo: string
    spento: boolean
    occupato: boolean
    errore: boolean
    onAltre: () => void
  } | null
}) {
  const perMese = new Map<string, Notte[]>()
  for (const n of notti) {
    const m = n.night_date.slice(0, 7)
    perMese.set(m, [...(perMese.get(m) ?? []), n])
  }
  return (
    <Carta
      formato="desktop"
      etichetta={t("nights.list")}
      colonne={colonne}
      ritardo={180}
      padding="24px 20px 24px"
      gap={14}
    >
      <div className="al-notti__riga-15">
        <span className="al-notti__testo-1">{t("nights.list")}</span>
        <span className="al-notti__testo-2">{sotto}</span>
      </div>
      <div className="al-notti__griglia-5" aria-hidden="true">
        {COLONNE.map((k) => (
          <span key={k}>{k === "nights.list.sky" ? testaDelCielo(notti) : t(k)}</span>
        ))}
      </div>
      {[...perMese].map(([mese, righe]) => {
        const somma = mesi.find((m) => m.month === mese)
        return (
          <div key={mese} className="al-notti__colonna-5">
            <span className="al-notti__riga-16">
              <b className="al-notti__testo-9">{meseMaiuscolo(mese)}</b>
              <span>{somma ? sommaDelMese(somma.nights, somma.integration_s) : ""}</span>
            </span>
            {righe.map((n) => (
              <Riga key={n.id} notte={n} scelta={n.id === scelta} onScegli={() => onScegli(n.id)} />
            ))}
          </div>
        )
      })}
      {notti.length === 0 && (
        <span className="al-notti__colonna-9">
          <b className="al-notti__testo-14">{t("nights.list.empty")}</b>
          <span className="al-notti__testo-2">{t("nights.list.empty.why")}</span>
        </span>
      )}
      <div className="al-notti__riga-18">
        {altre && (
          <a
            href="#"
            onClick={gesto(altre.spento ? undefined : altre.onAltre)}
            aria-disabled={altre.spento ? "true" : "false"}
            aria-busy={altre.occupato ? "true" : "false"}
            className="al-bottone al-bottone--tenue al-notti__testo-15"
          >
            {altre.testo}
          </a>
        )}
        <span className="al-notti__testo-16">{conta}</span>
      </div>
      {altre?.errore && <Avviso tipo="riga" segno="!" titolo={t("nights.more.failed")} />}
    </Carta>
  )
}

function meseMaiuscolo(mese: string): string {
  return maiuscola(meseEAnno(mese))
}

export interface VoceFuori {
  chiave: "review" | "site" | "date"
  n: number
  a: string | null
}

const FUORI: Record<VoceFuori["chiave"], { l: Chiave; sub: Chiave }> = {
  review: { l: "nights.out.review", sub: "nights.out.review.why" },
  site: { l: "nights.out.site", sub: "nights.out.site.why" },
  date: { l: "nights.out.date", sub: "nights.out.date.why" },
}

/** *Tutto l'archivio*: i totali e le voci fuori da ogni notte. */
export function TuttoLArchivio({
  tot,
  fuori,
  formato,
}: {
  tot: NonNullable<Elenco["totals"]>
  fuori: VoceFuori[]
  formato: Formato
}) {
  const tel = formato === "telefono"
  const parti = [
    t("nights.archive.objects", { n: numero(tot.objects) }),
    t("nights.frames", { n: numero(tot.frames) }),
    // \u00AB486 ore\u00BB (tavola): il totale in ore, non in ore e minuti
    ...(tot.integration_s > 0 ? [t("nights.archive.hours", { n: ore(tot.integration_s) })] : []),
    ...(tot.untimed ? [t("nights.archive.untimed", { n: numero(tot.untimed) })] : []),
  ].join(" \u00B7 ")
  const voci = fuori.map((f) => {
    const testi = FUORI[f.chiave]
    const dentro = (
      <>
        <span className="al-notti__fuori-voce">
          <span className="al-notti__testo-18">{t(testi.l)}</span>
          <span className="al-notti__testo-2">{t(testi.sub)}</span>
        </span>
        <b className="al-notti__testo-19">{numero(f.n)}</b>
        {f.a && (
          <span className="al-notti__tondo-1" aria-hidden="true">
            {"\u2197"}
          </span>
        )}
      </>
    )
    return f.a ? (
      <Link
        key={f.chiave}
        className={tel ? "al-notti__riga-34" : "al-notti__riga-20"}
        to={f.a}
        aria-label={t("nights.out.label", {
          n: numero(f.n),
          voce: t(testi.l),
          perche: t(testi.sub),
        })}
        style={{ display: "flex", alignItems: "center", gap: 10 }}
      >
        {dentro}
      </Link>
    ) : (
      <span
        key={f.chiave}
        className={tel ? "al-notti__riga-34" : "al-notti__riga-20"}
        style={{ display: "flex", alignItems: "center", gap: 10 }}
      >
        {dentro}
      </span>
    )
  })
  if (tel) {
    return (
      <Carta
        formato="telefono"
        etichetta={t("nights.archive")}
        ritardo={180}
        padding="20px"
        gap={10}
      >
        <span className="al-notti__testo-11">{t("nights.archive.small")}</span>
        <span className="al-notti__riga-33">
          <span className="al-notti__testo-30">{numero(tot.nights)}</span>
          <span className="al-notti__testo-26">{t("nights.archive.nights")}</span>
        </span>
        <span className="al-notti__testo-18">{parti}</span>
        <span className="al-notti__testo-11">{t("nights.archive.copies")}</span>
        {voci.length > 0 && (
          <>
            <span className="al-notti__testo-31">{t("nights.out")}</span>
            {voci}
          </>
        )}
      </Carta>
    )
  }
  return (
    <Carta
      formato="desktop"
      etichetta={t("nights.archive")}
      colonne={12}
      ritardo={240}
      padding="22px 28px"
      gap={24}
      allinea="center"
      griglia="auto auto minmax(0,1fr)"
    >
      <span className="al-notti__colonna-10">
        <span className="al-notti__testo-2">{t("nights.archive.small")}</span>
        <span className="al-notti__riga-19">
          <span className="al-notti__testo-17">{numero(tot.nights)}</span>
          <span className="al-notti__testo-5">{t("nights.archive.nights")}</span>
        </span>
      </span>
      <span className="al-notti__blocco-8">{parti}</span>
      <span className="al-notti__blocco-9">{t("nights.archive.copies")}</span>
      {voci.length > 0 && (
        <div className="al-notti__colonna-11">
          <span className="al-notti__testo-2">{t("nights.out")}</span>
          <div className="al-notti__griglia-7">{voci}</div>
        </div>
      )}
    </Carta>
  )
}
