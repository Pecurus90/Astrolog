import { useState } from "react"
import { useNavigate } from "react-router"

import { Carta } from "./componenti/Carta"
import { gesto } from "./componenti/gesto"
import { Pillola } from "./componenti/Pillola"
import type { Formato } from "./componenti/Tema"
import { api } from "./api/client"
import { useSiti } from "./api/siti"
import { anello, type Sito, useScriviSito } from "./ImpostazioniSiti"
import { type Chiave, meseEAnno, mesiIniziali, numero, t } from "./i18n"
import { usePreferenze } from "./preferenze"

/** The four ways are the four sources the API writes (sito.md): the chosen way is the source of
 *  the saved sky, until the user opens another. */
type Via = "frames" | "scale" | "measured" | "service"
const VIE: readonly Via[] = ["frames", "scale", "measured", "service"]

const classe = (b: number) => t("sites.sky.class", { n: b, cielo: t(`sky.${b}` as Chiave) })
// "SQM 21,6", "SQM 21,37": up to two decimals, the trailing zeros fall (tavola `AL.virg`)
const sqm = (v: number) => numero(Number(v.toFixed(2)))

/** "Ora": the saved sky and where it comes from (tavola `CV`). */
function ora(sito: Sito): { v: string; da: string } {
  if (sito.bortle === null || sito.sky_sqm === null) {
    return { v: t("sites.sky.none"), da: t("sites.sky.da.empty") }
  }
  const da = {
    frames: t("sites.sky.da.frames", { sqm: sqm(sito.sky_sqm), n: numero(sito.sky_nights ?? 0) }),
    scale: t("sites.sky.da.scale"),
    measured: t("sites.sky.da.measured", { sqm: sqm(sito.sky_sqm) }),
    service: t("sites.sky.da.service", { sqm: sqm(sito.sky_sqm) }),
  }[sito.sky_source ?? "scale"]
  return { v: classe(sito.bortle), da }
}

/**
 * **Il cielo del sito** (tavola 65-90): the proposal of the measures, the sky now, the four ways
 * and the twelve months. A way writes when its gesture says a sky: a class, an SQM, the map, the
 * measures; opening a way alone writes nothing.
 */
export function CieloDelSito({ formato, sito }: { formato: Formato; sito: Sito }) {
  const tel = formato === "telefono"
  const [via, setVia] = useState<Via | null>(sito.sky_source)
  const [esito, setEsito] = useState("")
  const [mappaTace, setMappaTace] = useState(false)
  const scrivi = useScriviSito(sito.is_default)
  const chiave = Boolean(usePreferenze().data?.values.sky_service_key)
  const percorso = { params: { path: { site_id: sito.id } } }
  const adesso = ora(sito)
  const apri = (k: Via) => {
    setVia(k)
    setEsito("")
    setMappaTace(false)
    if (k === "frames" && sito.measured.status === "enough" && sito.sky_source !== "frames") {
      void scrivi(() => api.POST("/api/v1/sites/{site_id}/sky/use", percorso))
    }
    if (k === "service" && chiave && sito.sky_source !== "service") {
      void scrivi(() => api.POST("/api/v1/sites/{site_id}/sky/service", percorso), [503]).then(
        (r) => setMappaTace(r.status === 503),
      )
    }
  }
  const vuota = gesto(() => {
    setVia(null)
    setEsito("")
    void scrivi(() =>
      api.PATCH("/api/v1/sites/{site_id}", { ...percorso, body: { sky_sqm: null } }),
    )
  })
  return (
    <Carta
      formato={formato}
      {...(tel ? {} : { colonne: 7 })}
      ritardo={60}
      padding={tel ? "20px" : "24px 28px"}
      gap={0}
      etichetta={t("sites.sky.card")}
    >
      <div className="al-imp__riga-9">
        <span className="al-imp__testo-3">{t("sites.sky.card")}</span>
        <span className="al-imp__testo-5">{t("sites.sky.sub")}</span>
      </div>
      <Proposta sito={sito} onEsito={setEsito} onUsato={() => setVia("frames")} />
      {esito && (
        <span className="al-imp__cielo-esito" aria-live="polite">
          {`✓ ${esito}` /* glifo-ok: segno della tavola */}
        </span>
      )}
      <div className="al-imp__cielo-riga">
        <span className="al-imp__testo-2">{t("sites.sky.now")}</span>
        <span className="al-imp__cielo-val">{adesso.v}</span>
        <span className="al-imp__testo-5">{adesso.da}</span>
      </div>
      <div className="al-imp__cielo-riga">
        <span className="al-imp__testo-2">{t("sites.sky.from")}</span>
        <span className="al-imp__riga-17" role="group" aria-label={t("sites.sky.from.group")}>
          {VIE.map((k) => (
            <a
              key={k}
              className="al-imp__riga-18"
              href="#"
              onClick={gesto(() => apri(k))}
              role="button"
              aria-pressed={via === k ? "true" : "false"}
              style={anello(via === k, 1.5)}
            >
              {t(`sites.sky.way.${k}` as Chiave)}
            </a>
          ))}
          {via !== null && (
            <a
              href="#"
              onClick={vuota}
              className="al-bottone al-bottone--testo al-bottone--piccolo"
            >
              {t("sites.sky.leaveEmpty")}
            </a>
          )}
        </span>
        <Via via={via} sito={sito} chiave={chiave} mappaTace={mappaTace} />
      </div>
      <Mesi sito={sito} />
    </Carta>
  )
}

/** What a way shows under the pills: the nine classes, the SQM field, the note, Apri Servizi. */
function Via({
  via,
  sito,
  chiave,
  mappaTace,
}: {
  via: Via | null
  sito: Sito
  chiave: boolean
  mappaTace: boolean
}) {
  const scrivi = useScriviSito(sito.is_default)
  const vai = useNavigate()
  const percorso = { params: { path: { site_id: sito.id } } }
  const bastano = sito.measured.status === "enough"
  const nota: Chiave = {
    frames: bastano ? "sites.sky.note.frames" : "sites.sky.note.frames.few",
    scale: "sites.sky.note.scale",
    measured: "sites.sky.note.measured",
    service: chiave ? "sites.sky.note.service" : "sites.sky.note.service.nokey",
    vuota: "sites.sky.note.empty",
  }[via ?? "vuota"] as Chiave
  return (
    <>
      {via === "scale" && (
        <span className="al-imp__riga-17" role="group" aria-label={t("sites.sky.classes")}>
          {Array.from({ length: 9 }, (_, i) => i + 1).map((b) => {
            const su = sito.sky_source === "scale" && sito.bortle === b
            return (
              <a
                key={b}
                className="al-imp__riga-18"
                href="#"
                role="button"
                aria-pressed={su ? "true" : "false"}
                style={anello(su, 1.5)}
                onClick={gesto(() => {
                  void scrivi(() =>
                    api.PATCH("/api/v1/sites/{site_id}", { ...percorso, body: { bortle: b } }),
                  )
                })}
              >
                {numero(b)}
              </a>
            )
          })}
        </span>
      )}
      {via === "measured" && <CampoSqm key={sito.id} sito={sito} />}
      {mappaTace && (
        <span className="al-imp__testo-20" aria-live="polite">
          {`✕ ${t("sites.sky.map.failed")}` /* glifo-ok: segno della tavola */}
        </span>
      )}
      {/* "resta senza cielo" is true only of a site without one: opening the way keeps the sky */}
      {!(via === "frames" && !bastano && sito.bortle !== null) && (
        <span className="al-imp__testo-11">{t(nota)}</span>
      )}
      {via === "service" && !chiave && (
        <a
          href="#"
          onClick={gesto(() => void vai("/impostazioni/servizi"))}
          className="al-bottone al-bottone--contorno al-bottone--piccolo al-imp__blocco-10"
        >
          {t("sites.sky.openServices")}
        </a>
      )}
    </>
  )
}

/** SQM a mano: written when the field is left or Invio is pressed, if the number is believable
 *  (the range is the API's). */
function CampoSqm({ sito }: { sito: Sito }) {
  const scrivi = useScriviSito(sito.is_default)
  const range = useSiti().data?.sqm_range
  const [v, setV] = useState(
    sito.sky_source === "measured" && sito.sky_sqm !== null ? sqm(sito.sky_sqm) : "",
  )
  const n = Number(v.replace(",", "."))
  const ok = v !== "" && Number.isFinite(n) && (!range || (n >= range.min && n <= range.max))
  const salva = () => {
    if (!ok || (sito.sky_source === "measured" && sito.sky_sqm === n)) return
    void scrivi(() =>
      api.PATCH("/api/v1/sites/{site_id}", {
        params: { path: { site_id: sito.id } },
        body: { sky_sqm: n },
      }),
    )
  }
  return (
    <>
      <span className="al-imp__riga-12">
        <input
          type="text"
          inputMode="decimal"
          value={v}
          onChange={(e) => setV(e.target.value.replace(/[^0-9.,]/g, "").slice(0, 5))}
          onBlur={salva}
          onKeyDown={(e) => e.key === "Enter" && salva()}
          placeholder={t("sites.sky.sqm.example")}
          aria-label={t("sites.sky.sqm")}
          aria-invalid={v && !ok ? "true" : "false"}
          className="al-campo al-campo--numero al-campo--piccolo al-imp__blocco-19"
        />
        <span className="al-imp__testo-2">{t("sites.sky.sqm.unit")}</span>
      </span>
      {v && !ok && range && (
        <span className="al-imp__testo-20" aria-live="polite">
          {
            `✕ ${t("sites.sky.sqm.range", { min: numero(range.min), max: numero(range.max) })}` /* glifo-ok: segno della tavola */
          }
        </span>
      )}
    </>
  )
}

/** The measures' proposal, with Usa and Lascia (sito.md, Marco 5/11/2026). */
function Proposta({
  sito,
  onEsito,
  onUsato,
}: {
  sito: Sito
  onEsito: (s: string) => void
  onUsato: () => void
}) {
  const scrivi = useScriviSito(sito.is_default)
  const m = sito.measured
  if (!m.propose || m.bortle === null || m.sqm === null) return null
  const percorso = { params: { path: { site_id: sito.id } } }
  const b = m.bortle
  const frase = `${t("sites.sky.prop", { sito: sito.name, classe: classe(b), sqm: sqm(m.sqm), n: numero(m.nights), m: numero(m.months) })} ${
    sito.bortle === null ? t("sites.sky.prop.none") : t("sites.sky.prop.has", { b: sito.bortle })
  }`
  const usa = gesto(async () => {
    const r = await scrivi(() => api.POST("/api/v1/sites/{site_id}/sky/use", percorso))
    if (!r.data) return
    onUsato()
    onEsito(t("sites.sky.done.use", { b }))
  })
  const lascia = gesto(async () => {
    const r = await scrivi(() => api.POST("/api/v1/sites/{site_id}/sky/dismiss", percorso))
    if (r.data)
      onEsito(
        sito.bortle === null
          ? t("sites.sky.done.keepEmpty")
          : t("sites.sky.done.keep", { b: sito.bortle }),
      )
  })
  return (
    <div className="al-imp__pannello">
      <span className="al-imp__sel-come">
        <Pillola forma="segno" esito="mancante" segno="?" fondo="carta" />
        <span>{frase}</span>
      </span>
      <span className="al-imp__sito-gesti">
        <a href="#" onClick={usa} className="al-bottone al-bottone--pieno al-bottone--piccolo">
          {t("sites.sky.use", { b })}
        </a>
        <a
          href="#"
          onClick={lascia}
          className="al-bottone al-bottone--contorno al-bottone--piccolo"
        >
          {sito.bortle === null
            ? t("sites.sky.leaveEmpty")
            : t("sites.sky.keep", { b: sito.bortle })}
        </a>
      </span>
    </div>
  )
}

/** The twelve months up to the last measured night (tavola `mesi`, `mesiT`). */
function Mesi({ sito }: { sito: Sito }) {
  const m = sito.measured
  const iniziali = mesiIniziali()
  const misurati = m.month_marks.filter((x) => x.measured).length
  const notti =
    m.nights === 1
      ? t("sites.months.nights.one")
      : t("sites.months.nights", { n: numero(m.nights) })
  const mesi =
    misurati === 1
      ? t("sites.months.months.one")
      : t("sites.months.months", { n: numero(misurati) })
  const testo =
    m.nights === 0
      ? t("sites.months.none")
      : m.status === "enough" && m.sqm !== null && m.bortle !== null
        ? t("sites.months.enough", {
            n: numero(m.nights),
            m: numero(misurati),
            sqm: sqm(m.sqm),
            classe: classe(m.bortle),
          })
        : t("sites.months.few", { notti, mesi })
  return (
    <div className="al-imp__cielo-riga">
      <span className="al-imp__testo-2">{t("sites.months")}</span>
      {m.month_marks.length > 0 && (
        <span
          className="al-imp__mesi"
          role="img"
          aria-label={t("sites.months.aria", { n: numero(misurati) })}
        >
          {m.month_marks.map((x) => {
            const nome = meseEAnno(`${x.year}-${String(x.month).padStart(2, "0")}`)
            return (
              <span
                key={`${x.year}-${x.month}`}
                className={x.measured ? "al-imp__mese al-imp__mese--fatto" : "al-imp__mese"}
                title={t(x.measured ? "sites.month.on" : "sites.month.off", { mese: nome })}
              >
                {iniziali[x.month - 1]}
              </span>
            )
          })}
        </span>
      )}
      <span className="al-imp__testo-9">{testo}</span>
      <span className="al-imp__testo-11">{t("sites.months.rule")}</span>
    </div>
  )
}
