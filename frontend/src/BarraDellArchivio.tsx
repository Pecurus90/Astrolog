import { type ReactNode, useEffect, useRef, useState } from "react"

import { Bottone } from "./Bottone"
import { CampoDiRicerca, Cerco } from "./CampoDiRicerca"
import { ApriLeTendine, Spunta, Tendina, Togli, type VoceDiTendina } from "./Tendina"
import type { components, operations } from "./api/schema"
import { type Chiave, notte, numero, t } from "./i18n"
import { costellazione, inOrdineDiNome } from "./costellazioni"

/** Cio' che le tendine offrono: lo manda la rotta, e sono solo i valori che l'archivio ha. */
export type ScelteDellaBarra = components["schemas"]["ArchiveChoices"]

/** L'ordine dell'elenco: i suoi valori sono quelli della rotta, non una copia. */
export type Ordine = NonNullable<NonNullable<operations["archive_page"]["parameters"]["query"]>["sort"]>

export type Criteri = {
  q: string
  catalog: string
  constellation: string
  filter: string
  /** `SOLO_MOSAICI` o vuoto: nell'indirizzo come gli altri, cosi' un elenco di soli mosaici si
   *  manda a qualcuno. */
  mosaic: string
  /** Un anno (`2025`), `PERIODO_DATE` per le date scelte a mano, o vuoto. */
  period: string
  /** Le date di `PERIODO_DATE`, `YYYY-MM-DD`: notti, non istanti. */
  since: string
  until: string
  /** Gli id di sito, ottica e camera, come li manda la rotta. */
  site: string
  optics: string
  camera: string
  sort: Ordine
}

export const SOLO_MOSAICI = "1"

export const PERIODO_DATE = "date"

export type Trovati = components["schemas"]["ArchiveFound"]

export const ORDINI: { chiave: Ordine; testo: Chiave }[] = [
  { chiave: "name", testo: "archive.sort.name" },
  { chiave: "hours", testo: "archive.sort.hours" },
  { chiave: "frames", testo: "archive.sort.frames" },
]

// I criteri che stringono, e che "Filtri" conta sul telefono. L'ordine e la ricerca no: l'ordine
// non toglie righe, e cio' che hai scritto si vede nel campo.
const FILTRI = ["catalog", "constellation", "filter", "mosaic", "period", "site", "optics", "camera"] as const

const TENDINE = "archivio-tendine"

/**
 * La barra dell'Archivio (disegno v31, `.as-restringi`): in alto la vista, il campo, l'ordine e
 * la conta; sotto le tendine, che offrono solo cio' che l'archivio ha. Sul telefono le tendine
 * stanno dietro "Filtri" e si aprono nel flusso.
 *
 * - **Ogni scelta va nell'indirizzo** (`onCriteri`): la barra non tiene niente di suo, tranne chi
 *   ha chiesto per ultimo e se le tendine sono aperte.
 * - **L'attesa sta su chi ha chiesto**: il campo o la tendina che ha cambiato porta il segno
 *   finche' la risposta non arriva; le righe di prima restano. Niente si spegne. Se non ha
 *   chiesto nessuno della barra, il segno lo portano il campo e tutte le tendine.
 * - **Una tendina senza scelte non compare**: con un sito solo non c'e' niente da scegliere.
 */
export function BarraDellArchivio({
  criteri,
  scelte,
  trovati,
  aspetta,
  onCriteri,
  onTogli,
  children,
}: {
  criteri: Criteri
  scelte: ScelteDellaBarra
  /** Quanti ne ha trovati, o `null` se la richiesta e' caduta: zero sarebbe una bugia. */
  trovati: Trovati | null
  aspetta: boolean
  onCriteri: (cambio: Partial<Criteri>) => void
  /** Toglie ogni filtro insieme. */
  onTogli: () => void
  /** L'interruttore di vista, che la pagina governa. */
  children?: ReactNode
}) {
  const [aperte, setAperte] = useState(false)
  // chi ha chiesto per ultimo: e' lui a portare il segno dell'attesa
  const [chiesto, setChiesto] = useState<{ chi: keyof Criteri; criteri: Criteri } | null>(null)
  const quanti = FILTRI.filter((c) => criteri[c]).length

  function chiedi(chi: keyof Criteri, cambio: Partial<Criteri>) {
    setChiesto({ chi, criteri: { ...criteri, ...cambio } })
    onCriteri(cambio)
  }
  // Il segno e' suo finche' l'indirizzo e' quello che ha chiesto lui. Se la richiesta viene da
  // fuori (il "togli i filtri" del vuoto, il tasto indietro, un collegamento) lo portano tutti:
  // sotto possono esserci zero righe, e senza segno l'attesa non si vedrebbe.
  const suo = chiesto !== null && (Object.keys(criteri) as (keyof Criteri)[]).every((c) => criteri[c] === chiesto.criteri[c])
  const attende = (chi: keyof Criteri) => aspetta && (!suo || chiesto.chi === chi)
  const siti = new Map(scelte.sites.map((s) => [String(s.id), s.name]))
  const ottiche = new Map(scelte.optics.map((s) => [String(s.id), s.name]))
  const camere = new Map(scelte.cameras.map((s) => [String(s.id), s.name]))
  const nomeDelPeriodo = (v: string) => (v === PERIODO_DATE ? t("archive.filter.period.dates") : v)

  return (
    <div
      className="as-restringi"
      role="search"
      aria-label={t("archive.bar")}
      aria-busy={aspetta}
      data-aperta={aperte ? "" : undefined}
    >
      <div className="as-restringi__riga">
        {children}
        <Cerca scritto={criteri.q} aspetta={attende("q")} onScritto={(q) => chiedi("q", { q })} />
        <ApriLeTendine
          aperte={aperte}
          governa={TENDINE}
          quanti={quanti > 0 ? <b>{numero(quanti)}</b> : null}
          onCambia={setAperte}
        >
          {t("archive.bar.filters")}{" "}
        </ApriLeTendine>
        <div className="as-restringi__fine">
          <Tendina
            etichetta={t("archive.sort")}
            valore={t(ORDINI.find((o) => o.chiave === criteri.sort)?.testo ?? "archive.sort.name")}
            voci={ORDINI.map((o) => ({ chiave: o.chiave, nome: t(o.testo) }))}
            scelta={criteri.sort}
            aspetta={attende("sort")}
            onScelta={(sort) => chiedi("sort", { sort: sort as Ordine })}
          />
          <Conta trovati={trovati} />
        </div>
      </div>
      <div className="as-restringi__tendine" id={TENDINE}>
        <Filtro
          etichetta="archive.filter.catalog"
          tutti="archive.filter.catalog.any"
          nessuno="archive.any.m"
          valore={criteri.catalog}
          voci={scelte.catalogs}
          aspetta={attende("catalog")}
          onScelto={(catalog) => chiedi("catalog", { catalog })}
        />
        <Filtro
          etichetta="archive.filter.constellation"
          tutti="archive.filter.constellation.any"
          nessuno="archive.any.f"
          valore={criteri.constellation}
          voci={inOrdineDiNome(scelte.constellations)}
          nome={costellazione}
          aspetta={attende("constellation")}
          onScelto={(constellation) => chiedi("constellation", { constellation })}
        />
        <Filtro
          etichetta="archive.filter.filter"
          tutti="archive.filter.filter.any"
          nessuno="archive.any.m"
          valore={criteri.filter}
          voci={scelte.filters}
          aspetta={attende("filter")}
          onScelto={(filter) => chiedi("filter", { filter })}
        />
        {scelte.mosaics && (
          <Spunta
            accesa={criteri.mosaic === SOLO_MOSAICI}
            aspetta={attende("mosaic")}
            onCambia={(solo) => chiedi("mosaic", { mosaic: solo ? SOLO_MOSAICI : "" })}
          >
            {t("archive.filter.mosaic.only")}
          </Spunta>
        )}
        {/* Cambiare periodo dimentica le date: resterebbero nell'indirizzo, e tornando a "scegli le
            date" stringerebbero senza che nessuno le abbia appena scelte. */}
        {criteri.period === PERIODO_DATE ? (
          <DalAl
            dal={criteri.since}
            al={criteri.until}
            aspetta={attende("since") || attende("until")}
            onDal={(since) => chiedi("since", { since })}
            onAl={(until) => chiedi("until", { until })}
            onTogli={() => chiedi("period", { period: "", since: "", until: "" })}
          />
        ) : (
          <Filtro
            etichetta="archive.filter.period"
            tutti="archive.filter.period.any"
            nessuno="archive.filter.period.short"
            valore={criteri.period}
            voci={scelte.years.length > 0 ? [...scelte.years, PERIODO_DATE] : []}
            nome={nomeDelPeriodo}
            aspetta={attende("period")}
            onScelto={(period) => chiedi("period", { period, since: "", until: "" })}
          />
        )}
        <Filtro
          etichetta="archive.filter.site"
          tutti="archive.filter.site.any"
          nessuno="archive.any.m"
          valore={criteri.site}
          voci={[...siti.keys()]}
          nome={(v) => siti.get(v) ?? v}
          aspetta={attende("site")}
          onScelto={(site) => chiedi("site", { site })}
        />
        <Filtro
          etichetta="archive.filter.optics"
          tutti="archive.filter.optics.any"
          nessuno="archive.any.f"
          valore={criteri.optics}
          voci={[...ottiche.keys()]}
          nome={(v) => ottiche.get(v) ?? v}
          aspetta={attende("optics")}
          onScelto={(optics) => chiedi("optics", { optics })}
        />
        <Filtro
          etichetta="archive.filter.camera"
          tutti="archive.filter.camera.any"
          nessuno="archive.any.f"
          valore={criteri.camera}
          voci={[...camere.keys()]}
          nome={(v) => camere.get(v) ?? v}
          aspetta={attende("camera")}
          onScelto={(camera) => chiedi("camera", { camera })}
        />
        {/* In coda alle tendine; la nota "si applicano subito" il foglio la mostra solo sul telefono. */}
        <div className="as-restringi__chiudi">
          <span className="as-archivio__nota">{t("archive.bar.applied")}</span>
          {quanti > 0 && (
            <Bottone verso="nudo" piccolo onClick={onTogli}>
              {t("archive.nothing.clear")}
            </Bottone>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * Quanti ne ha trovati: gli oggetti e i mosaici, coi numeri in evidenza. Se la richiesta e' caduta
 * dice "non so quanti": zero e' l'unica risposta che sappiamo falsa. **Si dice**, non si tace:
 * togliere la conta sposterebbe l'ordine sotto le dita di chi l'ha appena toccato.
 */
function Conta({ trovati }: { trovati: Trovati | null }) {
  if (trovati === null) {
    return (
      <p className="as-archivio__conta" aria-live="polite">
        {t("archive.count.unknown")}
      </p>
    )
  }
  const { objects: oggetti, mosaics: mosaici } = trovati
  const diOggetti = (
    <>
      <b>{numero(oggetti)}</b> {t("archive.count.objects", { n: oggetti })}
    </>
  )
  const diMosaici = (
    <>
      <b>{numero(mosaici)}</b> {t("archive.count.mosaics.word", { n: mosaici })}
    </>
  )
  return (
    <p className="as-archivio__conta" aria-live="polite">
      {mosaici === 0 ? (
        diOggetti
      ) : oggetti === 0 ? (
        diMosaici
      ) : (
        <>
          {diOggetti} {t("archive.count.join")} {diMosaici}
        </>
      )}
    </p>
  )
}

/**
 * Il campo di ricerca. **Aspetta che tu finisca di scrivere** prima di chiedere: una richiesta per
 * parola, non per tasto. Cio' che scrivi sta qui dentro; l'indirizzo lo riceve dopo 250 ms.
 *
 * - `consegna` in un ref: il padre cambia funzione a ogni disegno, e metterla fra le dipendenze
 *   farebbe ripartire il ritardo a ogni risposta.
 * - `consegnato`: il campo si riallinea all'indirizzo solo quando cambia **da fuori** (indietro,
 *   "togli i filtri"). Senza, un tasto battuto mentre la consegna torna indietro sparirebbe.
 */
function Cerca({
  scritto,
  aspetta,
  onScritto,
}: {
  scritto: string
  aspetta: boolean
  onScritto: (q: string) => void
}) {
  const [testo, setTesto] = useState(scritto)

  const consegna = useRef(onScritto)
  useEffect(() => {
    consegna.current = onScritto
  })

  const consegnato = useRef(scritto)
  useEffect(() => {
    if (scritto === consegnato.current) return
    consegnato.current = scritto
    setTesto(scritto)
  }, [scritto])

  useEffect(() => {
    if (testo === scritto) return
    const quando = setTimeout(() => {
      consegnato.current = testo
      consegna.current(testo)
    }, 250)
    return () => clearTimeout(quando)
  }, [testo, scritto])

  return (
    <CampoDiRicerca
      nellaBarra
      etichetta={t("archive.search")}
      placeholder={t("archive.search.placeholder")}
      value={testo}
      onChange={(e) => setTesto(e.target.value)}
      coda={(aspetta || testo !== scritto) && <Cerco />}
    />
  )
}

/** Una tendina che stringe: la prima voce la toglie ("tutti"), le altre sono cio' che l'archivio
 *  ha. Senza scelte non compare. `nome` traduce il valore in cio' che si legge. */
function Filtro({
  etichetta,
  tutti,
  nessuno,
  valore,
  voci,
  nome = (v) => v,
  aspetta,
  onScelto,
}: {
  etichetta: Chiave
  /** La voce che toglie il filtro, per intero: "Tutti i cataloghi". */
  tutti: Chiave
  /** La stessa cosa accanto all'etichetta, corta: "tutti". */
  nessuno: Chiave
  valore: string
  voci: string[]
  nome?: (voce: string) => string
  aspetta: boolean
  onScelto: (scelto: string) => void
}) {
  if (voci.length === 0) return null
  const elenco: VoceDiTendina[] = [{ chiave: "", nome: t(tutti) }, ...voci.map((v) => ({ chiave: v, nome: nome(v) }))]
  return (
    <Tendina
      etichetta={t(etichetta)}
      valore={valore ? nome(valore) : t(nessuno)}
      voci={elenco}
      scelta={valore}
      accesa={valore !== ""}
      aspetta={aspetta}
      togli={valore ? t("archive.filter.remove", { cosa: t(etichetta).toLowerCase(), valore: nome(valore) }) : undefined}
      onScelta={onScelto}
    />
  )
}

/**
 * Il periodo scelto a giorni (v32, `.as-dal-al`): "dal" e "al" in una pillola, al posto della
 * tendina del periodo, e la x che torna a "sempre".
 *
 * - **Se "al" viene prima di "dal" lo dice** sotto, col segno e la frase, e il campo porta
 *   `aria-invalid`: due date scambiate non trovano niente, e senza un motivo sembrerebbe un
 *   archivio vuoto.
 */
function DalAl({
  dal,
  al,
  aspetta,
  onDal,
  onAl,
  onTogli,
}: {
  dal: string
  al: string
  aspetta: boolean
  onDal: (data: string) => void
  onAl: (data: string) => void
  onTogli: () => void
}) {
  const scambiate = dal !== "" && al !== "" && al < dal
  return (
    <div
      className={dal || al ? "as-dal-al as-dal-al--scelta" : "as-dal-al"}
      role="group"
      aria-labelledby="archivio-periodo"
    >
      <div className="as-dal-al__pillola">
        <span className="as-dal-al__eti" id="archivio-periodo">
          {t("archive.filter.period")}
        </span>
        {/* Il foglio non ha una veste d'attesa per le date: il segno comune sta accanto al nome. */}
        {aspetta && <span className="as-attesa" aria-hidden="true" />}
        <Data etichetta="archive.filter.since" valore={dal} onData={onDal} />
        <Data etichetta="archive.filter.until" valore={al} sbagliata={scambiate} onData={onAl} />
        <Togli nome={t("archive.filter.period.remove")} onTogli={onTogli} />
      </div>
      {scambiate && (
        <p className="as-dal-al__errore" id="archivio-periodo-errore">
          <span className="as-dal-al__segno" aria-hidden="true">
            !
          </span>
          {t("archive.filter.dates.wrong", { giorno: notte(dal) })}
        </p>
      )}
    </div>
  )
}

/**
 * Una data del periodo. Il campo **non e' controllato**: un `value` controllato riscrive il campo
 * a ogni risposta, e mentre batti l'anno il browser passa da date a meta' (`0002-...`) che
 * tornerebbero indietro a cancellare cio' che stai scrivendo. Si consegna solo una data intera.
 */
function Data({
  etichetta,
  valore,
  sbagliata = false,
  onData,
}: {
  etichetta: Chiave
  valore: string
  sbagliata?: boolean
  onData: (data: string) => void
}) {
  const campo = useRef<HTMLInputElement>(null)
  useEffect(() => {
    if (campo.current && campo.current.value !== valore) campo.current.value = valore
  }, [valore])
  return (
    <label className="as-dal-al__campo">
      <span>{t(etichetta)}</span>
      <input
        ref={campo}
        type="date"
        defaultValue={valore}
        aria-invalid={sbagliata || undefined}
        aria-describedby={sbagliata ? "archivio-periodo-errore" : undefined}
        onChange={(e) => {
          if (!e.target.value.startsWith("0")) onData(e.target.value)
        }}
      />
    </label>
  )
}
