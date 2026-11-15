import { useMutation, useQueryClient } from "@tanstack/react-query"
import { createContext, useContext, useState } from "react"

import { Carta } from "./componenti/Carta"
import { useFormato } from "./componenti/formato"
import { gesto } from "./componenti/gesto"
import { SceltaTema } from "./componenti/SceltaTema"
import { type Formato, vesteDa } from "./componenti/Tema"
import { api } from "./api/client"
import { t } from "./i18n"
import { LINGUE, NOMI_LINGUE } from "./i18n/lingue"
import { usePreferenze } from "./preferenze"

/** "Impostazione non salvata": a failed write hands its retry to the page's notice (tavola
 *  `salvaErr`). */
export const SalvataggioFallito = createContext<(riprova: (() => void) | null) => void>(() => {})

/** One write of the settings, shared by every card of Generale: the answer replaces the cache, a
 *  failure goes to the page's notice with its retry. */
export function useScriviImpostazioni(dopo?: () => void) {
  const dati = useQueryClient()
  const fallito = useContext(SalvataggioFallito)
  const scrivi = useMutation({
    mutationFn: async (values: Record<string, string | null>) => {
      const { data, error } = await api.PATCH("/api/v1/settings", { body: { values } })
      if (error) throw new Error(t("settings.saveFailed"))
      return data
    },
    onSuccess: (data) => {
      dati.setQueryData(["settings"], data)
      fallito(null)
      dopo?.()
    },
    onError: (_e, values) => fallito(() => scrivi.mutate(values)),
  })
  return scrivi
}

/**
 * **Generale** (tavola Impostazioni v82): the user's name, the language, the theme. The name
 * lives here too, because the first start does not reopen (Marco 21/10/2026, Issue #19).
 */
export function Generale() {
  const formato = useFormato()
  const tel = formato === "telefono"
  const valori = usePreferenze().data?.values
  if (!valori) return null
  const salvato = String(valori.user_name ?? "")
  return (
    <div className={tel ? "al-imp__colonna-18" : "al-imp__griglia-2"}>
      {tel ? (
        <>
          <Nome formato={formato} salvato={salvato} />
          <Lingua formato={formato} lingua={String(valori.language)} />
          <Tema formato={formato} modo={valori.theme_mode} accento={valori.theme_accent} />
        </>
      ) : (
        <>
          <div className="al-imp__pila">
            <Nome formato={formato} salvato={salvato} />
            <Lingua formato={formato} lingua={String(valori.language)} />
          </div>
          <Tema formato={formato} modo={valori.theme_mode} accento={valori.theme_accent} />
        </>
      )}
    </div>
  )
}

function Nome({ formato, salvato }: { formato: Formato; salvato: string }) {
  const tel = formato === "telefono"
  const [scritto, setScritto] = useState<string | null>(null)
  const [fatto, setFatto] = useState(false)
  const scrivi = useScriviImpostazioni(() => setFatto(true))
  const v = scritto ?? salvato
  const nm = v.trim()
  const cambiato = !!nm && nm !== salvato && !fatto
  const salva = gesto(() => {
    if (nm) scrivi.mutate({ user_name: nm })
  })
  const scrive = (testo: string) => {
    setScritto(testo)
    setFatto(false)
  }
  return (
    <Carta
      formato={formato}
      ritardo={0}
      padding={tel ? "20px" : "24px 28px"}
      gap={tel ? 12 : 14}
      etichetta={t("settings.general.name")}
    >
      <span className={tel ? "al-imp__testo-27" : "al-imp__testo-3"}>
        {t("settings.general.name")}
      </span>
      {tel ? (
        <span className="al-imp__riga-28">
          <input
            value={v}
            onChange={(e) => scrive(e.target.value)}
            aria-label={t("settings.general.name")}
            placeholder={t("settings.general.name.placeholder")}
            className="al-campo al-imp__blocco-26"
          />
          {cambiato && (
            <a className="al-imp__strato-1" href="#" onClick={salva}>
              <span className="al-imp__riga-29">{t("ui.form.save")}</span>
            </a>
          )}
        </span>
      ) : (
        <span className="al-imp__riga-4">
          <input
            value={v}
            onChange={(e) => scrive(e.target.value)}
            aria-label={t("settings.general.name")}
            placeholder={t("settings.general.name.placeholder")}
            className="al-campo al-imp__blocco-4"
          />
          <a
            className="al-imp__riga-5"
            href="#"
            onClick={salva}
            aria-disabled={nm ? "false" : "true"}
            style={{
              background: nm ? "var(--scelta)" : "var(--carta-2)",
              color: nm ? "var(--scelta-testo)" : "var(--tenue)",
            }}
          >
            {t("ui.form.save")}
          </a>
        </span>
      )}
      {fatto && <span className="al-imp__testo-4">{t("settings.general.saved")}</span>}
      <span className={tel ? "al-imp__testo-8" : "al-imp__testo-5"}>{t("wizard.name.why")}</span>
    </Carta>
  )
}

function Lingua({ formato, lingua }: { formato: Formato; lingua: string }) {
  const tel = formato === "telefono"
  const scrivi = useScriviImpostazioni()
  return (
    <Carta
      formato={formato}
      ritardo={30}
      padding={tel ? "20px" : "24px 28px"}
      gap={tel ? 12 : 14}
      etichetta={t("settings.general.language")}
    >
      <span className={tel ? "al-imp__testo-27" : "al-imp__testo-3"}>
        {t("settings.general.language")}
      </span>
      <span
        role="radiogroup"
        aria-label={t("settings.general.language")}
        className={`al-scelta al-scelta--segmentato al-scelta--sottili${tel ? " al-scelta--riempie" : ""}`}
      >
        {LINGUE.map((l) => (
          <a
            key={l}
            href="#"
            role="radio"
            aria-checked={l === lingua ? "true" : "false"}
            onClick={gesto(() => {
              if (l !== lingua) scrivi.mutate({ language: l })
            })}
            className="al-scelta__voce"
          >
            {NOMI_LINGUE[l]}
          </a>
        ))}
      </span>
      <span className={tel ? "al-imp__testo-8" : "al-imp__testo-5"}>
        {t("settings.general.language.why")}
      </span>
    </Carta>
  )
}

function Tema({ formato, modo, accento }: { formato: Formato; modo: unknown; accento: unknown }) {
  const tel = formato === "telefono"
  const scrivi = useScriviImpostazioni()
  const veste = vesteDa(modo, accento)
  return (
    <Carta
      formato={formato}
      colonne={8}
      ritardo={60}
      padding={tel ? "20px" : "24px 28px"}
      gap={tel ? 12 : 14}
      etichetta={t("theme.label")}
    >
      {tel ? (
        <span className="al-imp__testo-27">{t("theme.label")}</span>
      ) : (
        <span className="al-imp__riga-6">
          <span className="al-imp__testo-3">{t("theme.label")}</span>
          <span className="al-imp__testo-5">{t("settings.general.theme.sub")}</span>
        </span>
      )}
      <SceltaTema
        modo={veste.modo}
        accento={veste.accento}
        formato={formato}
        onModo={(m) => scrivi.mutate({ theme_mode: m })}
        onAccento={(a) => scrivi.mutate({ theme_accent: a })}
      />
    </Carta>
  )
}
