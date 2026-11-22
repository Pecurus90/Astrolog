import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"

import { api } from "./api/client"
import type { components } from "./api/schema"
import { Avviso } from "./componenti/Avviso"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { Scheletro } from "./componenti/Scheletro"
import { type Chiave, t } from "./i18n"
import { Sezione } from "./ImpostazioniScansioni"
import { usePreferenze } from "./preferenze"

type Esito =
  components["schemas"]["SkyKeyOut"]["status"] | components["schemas"]["MeteoblueKeyOut"]["status"]

// Where the keys are asked: addresses, not texts to translate (tavola `SezioneServizi`).
export const METEOBLUE = "https://www.meteoblue.com/it/weather-api"
const CIELO = "https://www.lightpollutionmap.info/"

const SEGNI: Record<Esito, string> = {
  ok: "✓", // glifo-ok: segno della tavola
  removed: "",
  refused: "✕", // glifo-ok: segno della tavola
  limited: "!", // glifo-ok: segno della tavola
  unreachable: "!", // glifo-ok: segno della tavola
  bad_answer: "!", // glifo-ok: segno della tavola
  spent_today: "!", // glifo-ok: segno della tavola
}

type Servizio = {
  nome: Chiave
  serve: Chiave
  senza: Chiave
  dove: string
  /** The settings key that carries the hint (`GET /settings`, never the key). */
  valore: "meteoblue_key" | "sky_service_key"
  manda: (chiave: string) => Promise<Esito>
  /** What else reads the key and must read it again. */
  dopo: string[][]
}

const SERVIZI: Servizio[] = [
  {
    nome: "settings.services.meteoblue",
    serve: "settings.services.meteoblue.what",
    senza: "settings.services.meteoblue.without",
    dove: METEOBLUE,
    valore: "meteoblue_key",
    manda: async (key) => {
      const { data, error } = await api.PUT("/api/v1/weather/meteoblue-key", { body: { key } })
      if (error) throw new Error(t("settings.services.sendFailed"))
      return data.status
    },
    dopo: [["weather"]],
  },
  {
    nome: "settings.services.sky",
    serve: "settings.services.sky.what",
    senza: "settings.services.sky.without",
    dove: CIELO,
    valore: "sky_service_key",
    manda: async (key) => {
      const { data, error } = await api.PUT("/api/v1/services/sky-key", { body: { key } })
      if (error) throw new Error(t("settings.services.sendFailed"))
      return data.status
    },
    dopo: [["sites"]],
  },
]

/**
 * **Servizi** (tavola Impostazioni v82, `SezioneServizi`): the services' keys in one place. A key
 * is tried before it is saved; only its end comes out. "Ultimo tentativo", AAVSO and TNS stay
 * out (lista fissa 14/11): the row is simulated, and no page reads those keys yet.
 */
export function Servizi() {
  const formato = useFormato()
  const preferenze = usePreferenze()
  return (
    <Sezione>
      <p className="al-imp-intro">{t("settings.services.intro")}</p>
      {preferenze.isPending && (
        <Scheletro
          formato={formato}
          testo={t("settings.services.loading")}
          griglia="minmax(0,1fr)"
          carte={[0, 1].map(() => ({
            h: "180px",
            blocchi: [{ h: "24px", w: "180px" }, { flex: "1" }],
          }))}
        />
      )}
      {preferenze.isError && (
        <Avviso
          tipo="blocco"
          formato={formato}
          segno="!"
          titolo={t("settings.services.failed")}
          azione={t("settings.retry")}
          onAzione={() => void preferenze.refetch()}
        />
      )}
      {preferenze.data &&
        SERVIZI.map((s) => (
          <CartaServizio
            key={s.valore}
            s={s}
            fine={(preferenze.data.values[s.valore] as string | null | undefined) ?? null}
          />
        ))}
    </Sezione>
  )
}

function CartaServizio({ s, fine }: { s: Servizio; fine: string | null }) {
  const cache = useQueryClient()
  const nome = t(s.nome)
  const [chiave, setChiave] = useState("")
  const [cambia, setCambia] = useState(false)
  const invia = useMutation({
    mutationFn: s.manda,
    onSuccess: async (esito) => {
      if (esito === "ok" || esito === "removed" || esito === "limited") {
        setChiave("")
        setCambia(false)
      }
      await cache.invalidateQueries({ queryKey: ["settings"] })
      for (const k of s.dopo) await cache.invalidateQueries({ queryKey: k })
    },
  })
  const campo = !fine || cambia
  const esito = invia.data
  return (
    <section className="al-imp-carta" aria-label={nome}>
      <div className="al-imp-testa">
        <span className="al-imp-titoli">
          <b className="al-imp-titolo">{nome}</b>
          <span className="al-imp-sotto">{t(s.serve)}</span>
        </span>
        <a
          href={s.dove}
          target="_blank"
          rel="noopener noreferrer"
          className="al-bottone al-bottone--testo al-bottone--piccolo"
        >
          {t("settings.services.where")}
        </a>
      </div>
      <div className="al-imp-riga">
        <span className="al-imp-etichetta">{t("settings.services.key")}</span>
        <span className="al-imp-valore">
          {fine && !cambia && (
            <>
              <span className="al-imp-chiave">{fine}</span>
              <a
                href="#"
                role="button"
                onClick={gesto(() => setCambia(true))}
                className="al-bottone al-bottone--contorno al-bottone--piccolo"
              >
                {t("settings.services.change")}
              </a>
              <a
                href="#"
                role="button"
                aria-disabled={invia.isPending ? "true" : undefined}
                onClick={gesto(() => !invia.isPending && invia.mutate(""))}
                className="al-bottone al-bottone--testo al-bottone--piccolo"
              >
                {t("settings.services.remove")}
              </a>
            </>
          )}
          {campo && (
            <>
              <input
                className="al-campo al-campo--piccolo al-c-sezione-servizi__blocco-2"
                aria-label={t("settings.services.aria", { servizio: nome })}
                placeholder={t("settings.services.paste")}
                autoComplete="off"
                spellCheck={false}
                value={chiave}
                onChange={(e) => setChiave(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && chiave.trim() && !invia.isPending) invia.mutate(chiave)
                }}
              />
              <a
                href="#"
                role="button"
                aria-disabled={invia.isPending || !chiave.trim() ? "true" : undefined}
                onClick={gesto(() => chiave.trim() && !invia.isPending && invia.mutate(chiave))}
                className="al-bottone al-bottone--pieno al-bottone--piccolo"
              >
                {t("settings.services.check")}
              </a>
              {cambia && (
                <a
                  href="#"
                  role="button"
                  onClick={gesto(() => {
                    setCambia(false)
                    setChiave("")
                  })}
                  className="al-bottone al-bottone--testo al-bottone--piccolo"
                >
                  {t("settings.services.cancel")}
                </a>
              )}
            </>
          )}
        </span>
      </div>
      {esito && (
        <p className="al-imp-nota" aria-live="polite">
          {[SEGNI[esito], t(`settings.services.${esito}`, { servizio: nome })]
            .filter(Boolean)
            .join(" ")}
        </p>
      )}
      {invia.error && (
        <p className="al-imp-nota" aria-live="polite">
          {`${SEGNI.refused} ${invia.error.message}`}
        </p>
      )}
      {!fine && <p className="al-imp-nota">{t(s.senza)}</p>}
    </section>
  )
}
