import { useState } from "react"

import { Carta } from "./componenti/Carta"
import { gesto } from "./componenti/gesto"
import type { Formato } from "./componenti/Tema"
import { api } from "./api/client"
import { type Sito, useScriviSito, useSitoScelto } from "./ImpostazioniSiti"
import { coordinate, numero, t } from "./i18n"

/** "UTC+1", "UTC+5:30", "UTC-3": the offset the API gives, as the tavola writes it. */
export function scarto(minuti: number): string {
  const segno = minuti < 0 ? "−" : "+" // glifo-ok: il meno vero
  const a = Math.abs(minuti)
  const ore = Math.floor(a / 60)
  const resto = a % 60
  return `UTC${segno}${ore}${resto ? `:${String(resto).padStart(2, "0")}` : ""}`
}

/** The zone row, shared with Nuovo sito's preview. */
export function fuso(timezone: string | null, minuti: number | null): string {
  if (!timezone) return t("sites.zone.none")
  return minuti === null
    ? timezone
    : t("sites.zone.value", { fuso: timezone, scarto: scarto(minuti) })
}

export function Riga({
  etichetta,
  valore,
  sotto,
}: {
  etichetta: string
  valore: string
  sotto?: string
}) {
  return (
    <div className="al-imp__griglia-3">
      <span className="al-imp__testo-2">{etichetta}</span>
      <span className="al-imp__colonna-1">
        <b className="al-imp__testo-7">{valore}</b>
        {sotto ? <span className="al-imp__testo-8">{sotto}</span> : null}
      </span>
    </div>
  )
}

function righe(sito: Sito) {
  const altitudine =
    sito.elevation_m === null
      ? { valore: t("sites.elevation.none"), sotto: t("sites.elevation.none.why") }
      : {
          valore: t("sites.elevation.m", { n: numero(Math.round(sito.elevation_m)) }),
          sotto: t(
            sito.elevation_source === "service"
              ? "sites.elevation.service"
              : "sites.elevation.declared",
          ),
        }
  const notti =
    sito.nights === 0
      ? t("sites.nights.none")
      : sito.nights === 1
        ? t("sites.nights.one")
        : t("sites.nights.n", { n: numero(sito.nights) })
  return [
    {
      etichetta: t("sites.coords"),
      valore: coordinate(sito.latitude, sito.longitude),
      sotto: t(sito.coords_source === "place" ? "sites.coords.place" : "sites.coords.declared"),
    },
    { etichetta: t("sites.elevation"), ...altitudine },
    {
      etichetta: t("sites.zone"),
      valore: fuso(sito.timezone, sito.utc_offset_minutes),
      sotto: sito.timezone ? t("sites.zone.from") : "",
    },
    {
      etichetta: t("sites.nights"),
      valore: notti,
      sotto: sito.nights ? t("sites.nights.sub") : "",
    },
  ]
}

/** **Il sito** (tavola 45-64): the name with Rinomina, where each number comes from, the default,
 *  and Elimina, spent while the site holds nights or is the default. */
export function IlSito({ formato, sito }: { formato: Formato; sito: Sito }) {
  const tel = formato === "telefono"
  const scrivi = useScriviSito(true)
  const { scegli } = useSitoScelto()
  const [elimina, setElimina] = useState(false)
  const usaPredefinito = gesto(() => {
    void scrivi(() =>
      api.POST("/api/v1/sites/{site_id}/default", { params: { path: { site_id: sito.id } } }),
    )
  })
  const bloccato = sito.nights > 0 || sito.is_default
  const perche =
    sito.nights > 1
      ? t("sites.delete.hasNights", { n: numero(sito.nights) })
      : sito.nights === 1
        ? t("sites.delete.hasNights.one")
        : sito.is_default
          ? t("sites.delete.isDefault")
          : t("sites.delete.free")
  const eliminaDavvero = gesto(async () => {
    const fatto = await scrivi(() =>
      api.DELETE("/api/v1/sites/{site_id}", { params: { path: { site_id: sito.id } } }),
    )
    if (fatto.data) scegli(null)
  })
  return (
    <Carta
      formato={formato}
      {...(tel ? {} : { colonne: 5 })}
      ritardo={0}
      padding={tel ? "20px" : "24px 28px"}
      gap={0}
      etichetta={t("sites.card")}
    >
      <Nome sito={sito} />
      {righe(sito).map((r) => (
        <Riga key={r.etichetta} {...r} />
      ))}
      <div className="al-imp__griglia-3">
        <span className="al-imp__testo-2">{t("sites.default")}</span>
        <span className="al-imp__colonna-2">
          <b className="al-imp__testo-7">
            {t(sito.is_default ? "sites.default.yes" : "sites.default.no")}
          </b>
          {!sito.is_default && (
            <a
              href="#"
              onClick={usaPredefinito}
              className="al-bottone al-bottone--contorno al-bottone--piccolo"
            >
              {t("sites.default.use")}
            </a>
          )}
          <span className="al-imp__testo-8">{t("sites.default.what")}</span>
        </span>
      </div>
      <div className="al-imp__sito-fondo">
        {elimina ? (
          <div
            className="al-imp__pannello"
            role="alertdialog"
            aria-label={t("sites.delete.ask", { nome: sito.name })}
          >
            <span>{t("sites.delete.ask", { nome: sito.name })}</span>
            <span className="al-imp__sito-gesti">
              <a
                href="#"
                onClick={eliminaDavvero}
                className="al-bottone al-bottone--pericolo al-bottone--piccolo"
              >
                {t("sites.delete.yes")}
              </a>
              <a
                href="#"
                onClick={gesto(() => setElimina(false))}
                className="al-bottone al-bottone--testo al-bottone--piccolo"
              >
                {t("ui.form.cancel")}
              </a>
            </span>
          </div>
        ) : (
          <>
            <a
              href="#"
              onClick={gesto(() => !bloccato && setElimina(true))}
              aria-disabled={bloccato ? "true" : "false"}
              className="al-bottone al-bottone--pericolo al-bottone--piccolo al-imp__elimina"
            >
              {t("sites.delete")}
            </a>
            <span className="al-imp__testo-8">{perche}</span>
          </>
        )}
      </div>
    </Carta>
  )
}

/** The name, and Rinomina in place: the taken name is the API's 409, said under the field. */
function Nome({ sito }: { sito: Sito }) {
  const scrivi = useScriviSito(sito.is_default)
  const { elenco } = useSitoScelto()
  const [scritto, setScritto] = useState<string | null>(null)
  const [preso, setPreso] = useState(false)
  if (scritto === null) {
    return (
      <div className="al-imp__sito-testa">
        <span className="al-imp__sito-nome">{sito.name}</span>
        <a
          href="#"
          onClick={gesto(() => setScritto(sito.name))}
          className="al-bottone al-bottone--contorno al-bottone--piccolo"
        >
          {t("sites.rename")}
        </a>
      </div>
    )
  }
  const nome = scritto.trim()
  const doppio = preso || elenco.some((s) => s.id !== sito.id && s.name === nome)
  const errore = !nome ? t("sites.name.empty") : doppio ? t("sites.name.taken") : ""
  const salva = gesto(async () => {
    if (errore) return
    if (nome === sito.name) return setScritto(null)
    const fatto = await scrivi(
      () =>
        api.PATCH("/api/v1/sites/{site_id}", {
          params: { path: { site_id: sito.id } },
          body: { name: nome },
        }),
      [409],
    )
    if (fatto.status === 409) setPreso(true)
    else if (fatto.data) setScritto(null)
  })
  return (
    <div className="al-imp__sito-rin">
      <span className="al-imp__riga-4">
        <input
          value={scritto}
          onChange={(e) => {
            setScritto(e.target.value)
            setPreso(false)
          }}
          aria-label={t("sites.name")}
          aria-invalid={errore ? "true" : "false"}
          className="al-campo al-imp__blocco-4"
        />
        <a
          href="#"
          onClick={salva}
          aria-disabled={errore ? "true" : "false"}
          className="al-bottone al-bottone--pieno al-bottone--piccolo"
        >
          {t("ui.form.save")}
        </a>
        <a
          href="#"
          onClick={gesto(() => setScritto(null))}
          className="al-bottone al-bottone--testo al-bottone--piccolo"
        >
          {t("ui.form.cancel")}
        </a>
      </span>
      {errore && (
        <span className="al-imp__testo-20" aria-live="polite">
          {`✕ ${errore}` /* glifo-ok: segno della tavola */}
        </span>
      )}
    </div>
  )
}
