import { type KeyboardEvent, type ReactNode, useState } from "react"
import { Link } from "react-router"

import {
  CardMeteo,
  type CellaMeteo,
  type ParoleDellAvviso,
  type StatoMeteo,
} from "./componenti/CardMeteo"
import { Carta } from "./componenti/Carta"
import { gesto } from "./componenti/gesto"
import { type Esito, Pillola } from "./componenti/Pillola"
import type { Formato } from "./componenti/Tema"
import { ESITO } from "./DashboardDati"
import { type Chiave, numero, oraDelSito, t } from "./i18n"
import type { Sguardo } from "./Meteo"
import {
  ALTRE,
  buioDellaNotte,
  CARTE,
  type Codice,
  conUnita,
  disegnate,
  FORME,
  giornoDellaNotte,
  giudizioDi,
  livelloDellOra,
  type Meteo,
  type Misura,
  nelBuio,
  type Notte,
  parola,
  picco,
  quandoDellaMisura,
  quota,
  sotto,
  tondo,
} from "./MeteoDati"
import { nomeDellaMisura } from "./MeteoNotte"

/** A card that cannot show its measure, and the words it says instead. */
type Stato = { stato: StatoMeteo; parole?: ParoleDellAvviso }

/** Why a card has no number: no key, a refused key, the seeing not asked yet, under the clouds,
 *  or the service did not send it (board v82 `avc`). */
export function statoDellaCarta(
  m: Misura | undefined,
  code: Codice,
  n: Notte,
  detto: Meteo,
): Stato {
  if (m && m.known_hours > 0) return { stato: "normale" }
  if (code === "seeing") {
    const jet = m?.estimated_from === "jet"
    const stima: ParoleDellAvviso = {
      titolo: t("meteo.seeing.jet.title"),
      pillola: t("meteo.seeing.jet.pill"),
    }
    if (!detto.seeing.key) {
      return jet
        ? { stato: "chiave", parole: { ...stima, testo: t("meteo.seeing.jet.text") } }
        : { stato: "chiave" }
    }
    if (detto.seeing.meteoblue === "refused") return { stato: "chiave non valida" }
    if (detto.seeing.meteoblue === null) return { stato: "in arrivo" }
    // credits run out with no seeing from before: the key is good, it is asked again later
    if (detto.seeing.meteoblue === "limited") {
      return {
        stato: "non disponibile",
        parole: {
          titolo: t("weather.seeing.why.limited"),
          testo: "",
          pillola: t("meteo.seeing.later"),
        },
      }
    }
    if (jet) return { stato: "non disponibile", parole: { ...stima, testo: "" } }
  }
  const nuvole = n.measures.find((x) => x.code === "cloud")?.level === "nogo"
  if (nuvole && (code === "seeing" || code === "aerosol")) return { stato: "non si misura" }
  return { stato: "non disponibile", parole: { testo: t("meteo.card.missing.text") } }
}

const PLOTTABILI: readonly Codice[] = [
  "condensation",
  "rain",
  "wind",
  "seeing",
  "jet",
  "aerosol",
  "visibility",
]

/** "Luna al 55% dalle 23:00 \u00b7 banda larga fino alle 23:00": the hours it is up, what is left. */
function quandoLaLuna(m: Misura): string {
  if (!m.known_since || !m.known_until || (m.level !== "nogo" && m.level !== "marginal")) return ""
  const valori = {
    pct: numero(m.value ?? 0),
    da: oraDelSito(m.known_since),
    a: oraDelSito(m.known_until),
  }
  if (m.known_from_start && m.known_to_end) return t("weather.weighs.moon.all", valori)
  const forma = m.known_to_end ? "rises" : m.known_from_start ? "sets" : "middle"
  return t(`weather.weighs.moon.${forma}.${m.level}`, valori)
}

type Fattore = {
  code: Codice
  n: string
  esito: Esito
  parola: string
  testo: string
  mette: boolean
}

/** What weighs beside the verdict, worst first as the backend sorts them (board v82 `pesa`). */
function fattori(n: Notte, detto: Meteo): Fattore[] {
  const giudicati = n.measures.flatMap((m): Fattore[] => {
    if (m.code === "cloud" || m.level === null) return []
    if (m.code === "moon") {
      if (m.known_hours === 0) return []
      return [
        {
          code: m.code,
          n: nomeDellaMisura(m.code),
          esito: Math.min(1, ESITO[m.level]) as 0 | 1,
          parola: parola(m.code, m.level),
          testo: quandoLaLuna(m),
          mette: false,
        },
      ]
    }
    if (m.estimated_from === "jet") return []
    const come =
      m.code === "rain"
        ? "total"
        : m.code === "visibility" || m.code === "condensation"
          ? "lowest"
          : "mean"
    const valore =
      m.value === null || m.code === "gust"
        ? ""
        : ` \u00b7 ${t(`meteo.value.${come}`, { v: conUnita(m.code, m.value) })}`
    return [
      {
        code: m.code,
        n: nomeDellaMisura(m.code),
        esito: ESITO[m.level],
        parola: parola(m.code, m.level),
        testo: `${quandoDellaMisura(m, n)}${valore}`,
        mette: PLOTTABILI.includes(m.code),
      },
    ]
  })
  // cards without their number come last, with the reason (board: rank -1)
  const mancano = CARTE.filter((c) => c !== "cloud").flatMap((c): Fattore[] => {
    const m = n.measures.find((x) => x.code === c)
    const s = statoDellaCarta(m, c, n, detto)
    if (s.stato === "normale") return []
    const k = s.stato.replaceAll(" ", "-")
    return [
      {
        code: c,
        n: nomeDellaMisura(c),
        esito: s.stato === "chiave non valida" ? 2 : "mancante",
        parola: s.parole?.pillola ?? t(`ui.weather.${k}.pill` as Chiave),
        testo: s.parole?.titolo ?? t(`ui.weather.${k}.title` as Chiave),
        mette: false,
      },
    ]
  })
  return [...giudicati, ...mancano]
}

/** The card beside the night (board v82 `Come va`): the other factors, two in view, the facts. */
export function ComeVa({
  detto,
  notte: n,
  prima,
  formato,
  sguardo: g,
}: {
  detto: Meteo
  notte: Notte
  prima: boolean
  formato: Formato
  sguardo: Sguardo
}) {
  const tel = formato === "telefono"
  const [altri, setAltri] = useState(false)
  const tutti = n.trend ? [] : fattori(n, detto)
  const luna = n.trend ? n.measures.find((m) => m.code === "moon") : undefined
  const righe: Fattore[] = n.trend
    ? luna && luna.level
      ? [
          {
            code: "moon",
            n: nomeDellaMisura("moon"),
            esito: Math.min(1, ESITO[luna.level]) as 0 | 1,
            parola: parola("moon", luna.level),
            testo: quandoLaLuna(luna),
            mette: false,
          },
        ]
      : []
    : tutti
  const vista = righe.slice(0, 2)
  const resto = righe.slice(2)
  const buio = buioDellaNotte(n)
  const fatti = n.trend
    ? []
    : [
        ...(buio && n.window
          ? [
              {
                k: t(`meteo.facts.window.${n.window}`),
                v: buio,
                s:
                  n.window === "dark"
                    ? t("meteo.hours", { n: numero(Math.round(n.dark_hours)) })
                    : t(`meteo.facts.window.${n.window}.note`),
              },
            ]
          : []),
        ...(n.transparency != null
          ? [
              {
                k: t("meteo.facts.transparency"),
                v: t("meteo.facts.transparency.value", { v: numero(Math.round(n.transparency)) }),
                s: t("meteo.facts.transparency.note"),
              },
            ]
          : []),
      ]
  const riga = (f: Fattore, aperta: boolean) => {
    const dentro = (
      <>
        <span className="al-meteo__riga-12">
          <b className={tel ? "al-meteo__testo-29" : "al-meteo__testo-7"}>{f.n}</b>
          <Pillola esito={f.esito} testo={f.parola} dimensione={tel ? "minima" : "piccola"} />
        </span>
        <span className={tel ? "al-meteo__testo-14" : "al-meteo__testo-2"}>{f.testo}</span>
      </>
    )
    return f.mette ? (
      <a
        key={f.code}
        className={
          tel
            ? aperta
              ? "al-meteo__colonna-19"
              : "al-meteo__colonna-20"
            : aperta
              ? "al-meteo__colonna-7"
              : "al-meteo__colonna-8"
        }
        href="#"
        role="button"
        title={t("meteo.card.plot")}
        style={{ cursor: "pointer" }}
        onClick={gesto(() => {
          if (!g.accese.includes(f.code)) g.accendi(f.code)
        })}
      >
        {dentro}
      </a>
    ) : (
      <span
        key={f.code}
        className={
          tel
            ? aperta
              ? "al-meteo__colonna-19"
              : "al-meteo__colonna-20"
            : aperta
              ? "al-meteo__colonna-7"
              : "al-meteo__colonna-8"
        }
      >
        {dentro}
      </span>
    )
  }
  const titolo = (
    <div className={tel ? "al-meteo__riga-30" : "al-meteo__riga-11"}>
      <span className={tel ? "al-meteo__testo-28" : "al-meteo__testo-11"}>
        {t("meteo.weighs.title")}
      </span>
      <span className={tel ? "al-meteo__testo-14" : "al-meteo__testo-2"}>
        {giornoDellaNotte(n, prima)}
      </span>
    </div>
  )
  const etichetta = n.trend
    ? ""
    : t(righe.length === 1 ? "meteo.weighs.lab.one" : "meteo.weighs.lab", {
        n: numero(righe.length),
      })
  const vuoto = n.trend
    ? t("meteo.weighs.trend")
    : righe.length === 0
      ? t("weather.weighs.none")
      : ""
  const bottone = resto.length > 0 && (
    <a
      href="#"
      role="button"
      aria-expanded={altri}
      onClick={gesto(() => setAltri(!altri))}
      className={
        tel
          ? "al-bottone al-bottone--tenue al-bottone--blocco al-bottone--a-sinistra al-meteo__blocco-7"
          : "al-bottone al-bottone--tenue al-bottone--piccolo al-bottone--blocco al-bottone--a-sinistra al-meteo__blocco-7"
      }
    >
      {t(resto.length === 1 ? "weather.weighs.more.one" : "weather.weighs.more", {
        n: numero(resto.length),
      })}
      <span className="al-meteo__testo-12" aria-hidden="true">
        {altri ? "\u25b4" : "\u25be"}
      </span>
    </a>
  )
  const elenco = (
    <>
      {vista.map((f) => riga(f, true))}
      {vuoto && <span className={tel ? "al-meteo__blocco-14" : "al-meteo__blocco-6"}>{vuoto}</span>}
    </>
  )
  const fattiEl = (
    <div className={tel ? "al-meteo__griglia-6" : "al-meteo__griglia-3"}>
      {fatti.map((f) => (
        <span key={f.k} className={tel ? "al-meteo__colonna-22" : "al-meteo__colonna-10"}>
          <span className={tel ? "al-meteo__testo-32" : "al-meteo__testo-14"}>{f.k}</span>
          <b className={tel ? "al-meteo__testo-33" : "al-meteo__testo-15"}>{f.v}</b>
          <span className={tel ? "al-meteo__testo-32" : "al-meteo__testo-14"}>{f.s}</span>
        </span>
      ))}
    </div>
  )
  if (tel) {
    return (
      <Carta
        formato="telefono"
        etichetta={t("meteo.weighs.card")}
        ritardo={120}
        padding="20px"
        gap="10"
      >
        {titolo}
        {etichetta && <span className="al-meteo__testo-14">{etichetta}</span>}
        {elenco}
        {altri && resto.map((f) => riga(f, false))}
        {bottone}
        {fattiEl}
      </Carta>
    )
  }
  return (
    <Carta
      etichetta={t("meteo.weighs.card")}
      colonne={4}
      ritardo={120}
      padding="28px 24px"
      gap="14"
    >
      {titolo}
      <div className="al-meteo__colonna-5">
        {etichetta && <span className="al-meteo__blocco-5">{etichetta}</span>}
        {elenco}
      </div>
      {altri && resto.length > 0 && (
        <div className="al-meteo__colonna-5">{resto.map((f) => riga(f, false))}</div>
      )}
      {bottone}
      {fattiEl}
    </Carta>
  )
}

type Carta9 = {
  code: Codice
  nome: string
  stato: Stato
  valore: string
  unita: string
  celle: CellaMeteo[]
  nota: string
  picco: string
  esito: Esito
  giudizio: string
  /** The word alone, for the phone's small tile. */
  breve: string
  sulGrafico: boolean
  mette: boolean
  fissa: boolean
  aggiornamento: string
}

/** A card's numbers at the night, or at the hour the thread or its own bars point to. */
function cartaDi(code: Codice, n: Notte, detto: Meteo, g: Sguardo): Carta9 | null {
  const m = n.measures.find((x) => x.code === code)
  const forma = FORME[code]
  if (!forma || (!m && code !== "seeing")) return null
  const stato = statoDellaCarta(m, code, n, detto)
  const ore = disegnate(n)
  const fissata = g.fisse[code]
  const hC = fissata ?? g.ora
  const qui = hC == null ? undefined : ore[hC]
  const v = qui ? qui[forma.campo] : null
  const lv = qui ? livelloDellOra(qui, code) : null
  const sel = g.accese.includes(code)
  const scala = detto.scales.find((s) => s.code === code)
  const notte = m ? giudizioDi(m, scala) : { esito: "mancante" as Esito, parola: "" }
  const celle = ore.map((o, i): CellaMeteo => {
    const x = o[forma.campo]
    const l = livelloDellOra(o, code)
    return {
      h: x === null ? 100 : 25 + Math.max(0, Math.min(1, quota(m, x))) * 75,
      manca: x === null,
      esito: x === null || !nelBuio(o, n) || !l ? null : ESITO[l],
      op: hC == null || hC === i ? 1 : 0.35,
      title: `${oraDelSito(o.at)} \u00b7 ${x === null ? t("weather.card.unknown") : conUnita(code, x)}${l ? ` \u00b7 ${parola(code, l)}` : ""}`,
      on: () => g.scegliOra(i),
      click: () => g.fissa(code, i),
    }
  })
  const aOra = qui !== undefined && v !== null
  const meteoblue = detto.seeing.meteoblue
  return {
    code,
    nome: nomeDellaMisura(code),
    stato,
    valore: aOra ? numero(tondo(code, v)) : m?.value == null ? "?" : numero(tondo(code, m.value)),
    unita: forma.unita ? t(forma.unita) : "",
    celle,
    nota: aOra
      ? `${t("meteo.card.at", { ora: oraDelSito(qui.at) })}${fissata != null ? ` \u00b7 ${t("meteo.card.only")}` : ""}`
      : m
        ? sotto(m, n)
        : "",
    picco: aOra || !m ? "" : picco(m, n, scala),
    esito: aOra ? (lv ? ESITO[lv] : "neutra") : notte.esito,
    breve: aOra && lv ? parola(code, lv) : notte.parola,
    giudizio: aOra
      ? t("meteo.card.wordAt", {
          parola: lv ? parola(code, lv) : notte.parola,
          ora: oraDelSito(qui.at),
        })
      : m && m.level
        ? `${notte.parola} ${quandoDellaMisura(m, n)}`
        : notte.parola,
    sulGrafico: sel,
    mette: PLOTTABILI.includes(code) && stato.stato === "normale",
    fissa: fissata != null,
    aggiornamento:
      code === "seeing" &&
      detto.seeing.source !== null &&
      (meteoblue === "unreachable" || meteoblue === "bad_answer" || meteoblue === "limited")
        ? t(`weather.seeing.why.${meteoblue}`)
        : "",
  }
}

/** The measures of the night, always in their place, then the other measures (board v82). */
export function LeMisure({
  detto,
  notte: n,
  formato,
  sguardo: g,
  aggiorna,
}: {
  detto: Meteo
  notte: Notte
  formato: Formato
  sguardo: Sguardo
  aggiorna: () => void
}) {
  const tel = formato === "telefono"
  const carte = CARTE.flatMap((c) => {
    const k = cartaDi(c, n, detto, g)
    return k ? [k] : []
  })
  const ore = disegnate(n)
  const qui = g.ora == null ? undefined : ore[g.ora]
  const sottotitolo = qui
    ? tel
      ? t("meteo.card.at", { ora: oraDelSito(qui.at) })
      : t("meteo.cards.at", { ora: oraDelSito(qui.at) })
    : t(tel ? "meteo.cards.sub.tel" : "meteo.cards.sub")
  const tasto = (code: Codice) => (ev: KeyboardEvent<HTMLDivElement>) => {
    let h = g.fisse[code] ?? g.ora ?? 0
    if (ev.key === "ArrowRight") h += 1
    else if (ev.key === "ArrowLeft") h -= 1
    else if (ev.key === "Escape") {
      g.fissa(code, null)
      return
    } else return
    ev.preventDefault()
    g.fissa(code, Math.max(0, Math.min(ore.length - 1, h)))
  }
  const altre = ALTRE.flatMap((c) => {
    const m = n.measures.find((x) => x.code === c)
    return m
      ? [
          {
            code: c,
            k: nomeDellaMisura(c),
            v: m.value === null ? "?" : numero(m.value),
            u: FORME[c]?.unita ? t(FORME[c].unita) : "",
            n: sotto(m, n),
          },
        ]
      : []
  })
  const etichetta = (k: Carta9) =>
    k.code === "cloud" || k.code === "cloud_low"
      ? t("meteo.card.tag.pct")
      : k.sulGrafico
        ? t("meteo.card.tag")
        : undefined
  const titolo = (
    <div className={tel ? "al-meteo__colonna-23" : "al-meteo__riga-14"}>
      <span className={tel ? "al-meteo__testo-28" : "al-meteo__testo-11"}>
        {t("meteo.cards.title")}
      </span>
      <span className={tel ? "al-meteo__testo-14" : "al-meteo__testo-2"}>{sottotitolo}</span>
    </div>
  )
  if (tel) {
    const pezzi: ReactNode[] = []
    carte.forEach((k, i) => {
      pezzi.push(
        <CardMeteo
          key={k.code}
          formato="telefono"
          compatta
          stato={k.stato.stato}
          dette={k.stato.parole}
          nome={k.nome}
          valore={k.valore}
          unita={k.unita}
          celle={k.celle}
          esito={k.esito}
          giudizio={k.breve}
          anello={k.sulGrafico ? "var(--barretta)" : undefined}
          aperto={g.aperta === k.code}
          onClick={() => {
            g.fissa(k.code, null)
            g.apri(g.aperta === k.code ? null : k.code)
          }}
        />,
      )
      const aperta = carte.findIndex((x) => x.code === g.aperta)
      if (
        (i % 2 === 1 || i === carte.length - 1) &&
        aperta >= 0 &&
        Math.floor(aperta / 2) === Math.floor(i / 2)
      ) {
        const a = carte[aperta]
        if (a)
          pezzi.push(
            <Dettaglio key={`d${a.code}`} carta={a} notte={n} sguardo={g} aggiorna={aggiorna} />,
          )
      }
    })
    return (
      <Carta
        formato="telefono"
        etichetta={t("meteo.cards.card")}
        ritardo={180}
        padding="20px 16px"
        gap="12"
      >
        {titolo}
        <div className="al-meteo__griglia-7">{pezzi}</div>
        <div className="al-meteo__colonna-26">
          {altre.map((e) => (
            <span key={e.code} className="al-meteo__riga-37">
              <span className="al-meteo__colonna-5">
                <span className="al-meteo__testo-13">{e.k}</span>
                <span className="al-meteo__testo-32">{e.n}</span>
              </span>
              <span className="al-meteo__testo-37">
                <span className="al-meteo__testo-38">{e.v}</span>{" "}
                <span className="al-meteo__testo-14">{e.u}</span>
              </span>
            </span>
          ))}
        </div>
      </Carta>
    )
  }
  return (
    <>
      <Carta
        etichetta={t("meteo.cards.card")}
        colonne={12}
        ritardo={180}
        padding="24px 28px 28px"
        gap="18"
      >
        {titolo}
        <div className="al-meteo__griglia-4">
          {carte.map((k) => (
            <CardMeteo
              key={k.code}
              stato={k.stato.stato}
              dette={k.stato.parole}
              nome={k.nome}
              valore={k.valore}
              unita={k.unita}
              celle={k.celle}
              nota={k.nota}
              picco={k.picco}
              esito={k.esito}
              giudizio={k.giudizio}
              anello={k.sulGrafico ? "var(--barretta)" : undefined}
              etichetta={etichetta(k)}
              aggiornamento={k.aggiornamento}
              onAggiorna={aggiorna}
              {...(k.mette ? { onClick: () => g.accendi(k.code) } : {})}
              {...(k.fissa ? { onTorna: () => g.fissa(k.code, null) } : {})}
              onTasto={tasto(k.code)}
              onLeave={() => g.scegliOra(null)}
            />
          ))}
        </div>
      </Carta>
      <Carta
        etichetta={t("meteo.other.title")}
        colonne={12}
        ritardo={240}
        padding="24px 28px"
        gap="12"
        griglia="220px repeat(3,minmax(0,1fr))"
        allinea="center"
      >
        <span className="al-meteo__colonna-11">
          <span className="al-meteo__testo-11">{t("meteo.other.title")}</span>
          <span className="al-meteo__testo-2">{t("meteo.other.sub")}</span>
        </span>
        {altre.map((e) => (
          <span key={e.code} className="al-meteo__colonna-12">
            <span className="al-meteo__testo-16">{e.k}</span>
            <span className="al-meteo__riga-15">
              <span className="al-meteo__testo-17">{e.v}</span>
              <span className="al-meteo__testo-18">{e.u}</span>
            </span>
            <span className="al-meteo__testo-14">{e.n}</span>
          </span>
        ))}
      </Carta>
    </>
  )
}

/** The phone's open card, below its pair: bars to tap for an hour, the pill, and the chart. */
function Dettaglio({
  carta: k,
  notte: n,
  sguardo: g,
  aggiorna,
}: {
  carta: Carta9
  notte: Notte
  sguardo: Sguardo
  aggiorna: () => void
}) {
  const ore = disegnate(n)
  const tacche = [0, 0.25, 0.5, 0.75, 1].map((f) => {
    const i = Math.round(f * (ore.length - 1))
    return { i, l: ore[i] ? oraDelSito(ore[i].at).slice(0, 2) : "" }
  })
  const ok = k.stato.stato === "normale"
  const sk = k.stato.stato.replaceAll(" ", "-")
  return (
    <div className="al-meteo__colonna-24">
      <span className="al-meteo__riga-33">
        <b className="al-meteo__testo-7">{k.nome}</b>
        <a
          className="al-meteo__tondo-3"
          href="#"
          role="button"
          aria-label={t("meteo.card.close")}
          onClick={gesto(() => g.apri(null))}
        >
          {"\u00d7"}
        </a>
      </span>
      {ok ? (
        <div className="al-meteo__colonna-17">
          <span className="al-meteo__testo-34">
            {[k.nota, k.picco].filter(Boolean).join(" \u00b7 ")}
          </span>
          <div
            className="al-meteo__riga-34"
            role="group"
            aria-label={t("ui.weather.bars", { nome: k.nome })}
          >
            {k.celle.map((c, i) => (
              <span
                key={ore[i]?.at ?? i}
                className="al-meteo__riga-35"
                title={c.title}
                onClick={() => g.fissa(k.code, i)}
              >
                <span
                  className="al-meteo__pillola-5"
                  style={{
                    height: `${c.h}%`,
                    background: c.manca
                      ? "repeating-linear-gradient(135deg, var(--barretta-spenta) 0 3px, transparent 3px 8px)"
                      : c.esito === null
                        ? "var(--barretta-spenta)"
                        : ["var(--buono-testo)", "var(--incerto-testo)", "var(--non-adatto-testo)"][
                            c.esito
                          ],
                    opacity: c.op,
                  }}
                />
              </span>
            ))}
          </div>
          <div className="al-meteo__blocco-16">
            {tacche.map((x) => (
              <span
                key={x.i}
                style={{
                  position: "absolute",
                  left: `${(x.i / Math.max(1, ore.length - 1)) * 100}%`,
                  transform: "translateX(-50%)",
                }}
              >
                {x.l}
              </span>
            ))}
          </div>
          <Pillola
            esito={k.esito}
            testo={k.giudizio}
            fondo="carta"
            dimensione="piccola"
            allinea="flex-start"
          />
          {k.aggiornamento && (
            <span className="al-meteo__testo-35">
              ! {k.aggiornamento}{" "}
              <a href="#" className="al-bottone al-bottone--testo" onClick={gesto(aggiorna)}>
                {t("weather.refresh")}
              </a>
            </span>
          )}
          {k.mette && (
            <a
              href="#"
              role="button"
              className="al-bottone al-bottone--pieno al-bottone--blocco"
              onClick={gesto(() => g.accendi(k.code))}
            >
              {t(k.sulGrafico ? "meteo.card.unplot" : "meteo.card.plot")}
            </a>
          )}
        </div>
      ) : (
        <div className="al-meteo__colonna-17">
          <span className="al-meteo__riga-36">
            <span
              className="al-meteo__tondo-4"
              aria-hidden="true"
              style={{
                background:
                  k.stato.stato === "chiave non valida" ? "var(--avviso)" : "var(--carta-2)",
                color:
                  k.stato.stato === "chiave non valida" ? "var(--avviso-testo)" : "var(--testo)",
              }}
            >
              {k.stato.stato === "chiave non valida" ? "!" : "?"}
            </span>
            <span className="al-meteo__colonna-25">
              <b className="al-meteo__testo-36">
                {k.stato.parole?.titolo ?? t(`ui.weather.${sk}.title` as Chiave)}
              </b>
              {k.stato.parole?.testo !== "" && (
                <span className="al-meteo__testo-14">
                  {k.stato.parole?.testo ??
                    (sk === "non-si-misura" || sk === "in-arrivo"
                      ? t(`ui.weather.${sk}.text` as Chiave)
                      : "")}
                </span>
              )}
            </span>
          </span>
          {(k.stato.stato === "chiave" || k.stato.stato === "chiave non valida") && (
            <Link
              to="/impostazioni/servizi"
              className="al-bottone al-bottone--testo al-bottone--blocco"
            >
              {t("ui.weather.settings")}
            </Link>
          )}
        </div>
      )}
    </div>
  )
}
