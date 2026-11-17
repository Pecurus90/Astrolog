import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useCallback, useRef, useState } from "react"

import { Avviso } from "./componenti/Avviso"
import { useFormato } from "./componenti/formato"
import { SceltaTema } from "./componenti/SceltaTema"
import { vesteDa } from "./componenti/Tema"
import { SalvataggioFallito, useScriviImpostazioni } from "./ImpostazioniGenerale"
import { Comando, CorniceAvvio, type Passo as Voce, type Tappa } from "./PrimoAvvioCornice"
import { ChiusuraAvvio, type Chiuso } from "./WizardChiusura"
import { WizardFolders } from "./WizardFolders"
import { WizardSeeing } from "./WizardSeeing"
import { WizardSite, useSitoDelPasso } from "./WizardSite"
import { WizardSolver } from "./WizardSolver"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, t } from "./i18n"
import { usePreferenze } from "./preferenze"
import { useRadiceDati } from "./radiceDati"

// What the app lacks, with the API's generated codes.
type Manca = components["schemas"]["SettingsOut"]["missing"]
type Cartelle = components["schemas"]["FolderList"]

// tavola v82 order: the theme after the site, ASTAP last and only when missing
const PASSI = ["nome", "sito", "tema", "cartelle", "seeing"] as const
type Passo = (typeof PASSI)[number] | "astap"

const NOMI: Record<Passo, Chiave> = {
  nome: "wizard.step.name",
  sito: "wizard.step.site",
  tema: "wizard.step.theme",
  cartelle: "wizard.step.folders",
  seeing: "wizard.step.services",
  astap: "wizard.step.solver",
}

const PERCHE: Record<Passo, Chiave> = {
  nome: "wizard.name.why",
  sito: "wizard.site.why",
  tema: "wizard.theme.why",
  cartelle: "wizard.folders.intro",
  seeing: "wizard.services.why",
  astap: "wizard.solver.intro",
}

// the recognizer is not ready: no program, or the program without its star catalogue
const RICONOSCITORE_NON_PRONTO = ["no_solver", "no_star_database"] as const

/** The home site as the database has it, for the closing. `undefined`: the read failed. */
async function sitoDiCasa() {
  const { data } = await api.GET("/api/v1/sites").catch(() => ({ data: undefined }))
  if (!data) return undefined
  const sito = data.items.find((s) => s.is_default) ?? data.items[0]
  return sito ? { nome: sito.name, bortle: sito.bortle } : null
}

/**
 * The first run (tavola v82 `Primo avvio`): name, site, theme, folders, seeing, and ASTAP to whom
 * lacks it; then it gets out of the way. Decisions in `docs/domini/sito.md`.
 *
 * - **The steps are fixed on entry**: writing the solver path drops `no_solver`, and a live list
 *   would pull the last step from under whoever is on it.
 * - **Skip from every step**, without asking; skipping and finishing write the same stamp.
 * - **A step stands done or skipped** by what the API holds when one moves on, never by colour.
 * - **A failed write is said**, and one stays on the step.
 */
export function Wizard({
  onDone,
  onChiusura,
  manca,
}: {
  onDone: () => void
  /** "Fine" was pressed: from here only `onDone` leaves, stamp written or not. */
  onChiusura: () => void
  manca: Manca
}) {
  const formato = useFormato()
  const cache = useQueryClient()
  const preferenze = usePreferenze()
  const valori = preferenze.data?.values
  const [passi] = useState<readonly Passo[]>(() =>
    RICONOSCITORE_NON_PRONTO.some((c) => manca.includes(c)) ? [...PASSI, "astap"] : PASSI,
  )
  // NAS or computer, ASTAP or its catalogue: which reason is true is decided on entry too
  const radice = useRadiceDati()
  const [senzaCatalogo] = useState(() => manca.includes("no_star_database"))
  const perche = (p: Passo): Chiave => {
    if (p === "cartelle" && radice !== null) return "wizard.folders.introNas"
    if (p === "astap" && senzaCatalogo) return "wizard.solver.introNoDatabase"
    return PERCHE[p]
  }
  const [step, setStep] = useState(0)
  const [segnati, setSegnati] = useState<Partial<Record<Passo, Tappa>>>({})
  const [name, setName] = useState("")
  const [nonScritto, setNonScritto] = useState(false)
  const saved = useRef<string | undefined>(undefined)
  const qui = passi[step]!
  const last = step === passi.length - 1
  const sito = useSitoDelPasso(() => {
    setSegnati((s) => ({ ...s, sito: "fatto" }))
    setStep((n) => n + 1)
  })
  // a step with a full command of its own (add, verify and save): Avanti steps down to tenue
  const [pienoDelPasso, setPienoDelPasso] = useState(false)
  const fallito = useCallback((f: (() => void) | null) => setNonScritto(f !== null), [])
  const scrivi = useScriviImpostazioni()

  const [chiuso, setChiuso] = useState<Chiuso>()
  const stamp = useMutation({
    // `mostra`: Fine goes through the closing, Salta enters at once
    mutationFn: async (mostra: boolean) => {
      // before the stamp: once written, a reread of the settings would unmount the page
      if (mostra) onChiusura()
      const { data: scritte, error } = await api.POST("/api/v1/settings/wizard-done", {})
      if (error) throw new Error(t("settings.failed"))
      const nome = scritte.values["user_name"]
      const dati = {
        mostra,
        nome: typeof nome === "string" ? nome : null,
        veste: vesteDa(scritte.values["theme_mode"], scritte.values["theme_accent"]),
        chiave: Boolean(scritte.values["meteoblue_key"]),
        sito: mostra ? await sitoDiCasa() : undefined,
      }
      // With a folder, the app starts reading at once; the stamp rules, so a failure here
      // still leaves the first run, and the read is asked from Scansiona.
      let cartelle: number | null = null
      try {
        // `limit: 1`: only how many (319 bytes against 27 156 on three hundred folders)
        const { data } = await api.GET("/api/v1/folders", { params: { query: { limit: 1 } } })
        cartelle = data?.total ?? null
        if (!cartelle) return { ...dati, cartelle, letta: false }
        const { error: nonLetta } = await api.POST("/api/v1/scan")
        return { ...dati, cartelle, letta: !nonLetta }
      } catch {
        return { ...dati, cartelle, letta: false }
      }
    },
    onSuccess: (esito) => {
      if (esito.mostra) setChiuso(esito)
      else onDone()
    },
  })

  // what the API holds when one moves on: given, or skipped
  const esito = (p: Passo): Tappa => {
    const missing = preferenze.data?.missing ?? manca
    const dato: Record<Passo, boolean> = {
      nome: Boolean(saved.current || valori?.["user_name"]),
      sito: segnati.sito === "fatto",
      tema: true,
      cartelle: (cache.getQueryData<Cartelle>(["folders"])?.items.length ?? 0) > 0,
      seeing: Boolean(valori?.["meteoblue_key"]),
      astap: !RICONOSCITORE_NON_PRONTO.some((c) => missing.includes(c)),
    }
    return dato[p] ? "fatto" : "saltato"
  }

  const avanti = async () => {
    // the name is written leaving the step, and not rewritten if unchanged
    const scritto = name.trim()
    if (qui === "nome" && scritto && scritto !== saved.current) {
      const { error } = await api
        .PATCH("/api/v1/settings", { body: { values: { user_name: scritto } } })
        .catch(() => ({ error: true }))
      setNonScritto(Boolean(error))
      if (error) return
      saved.current = scritto
      void cache.invalidateQueries({ queryKey: ["settings"] })
    }
    setNonScritto(false)
    sito.dimentica()
    setSegnati((s) => ({ ...s, [qui]: esito(qui) }))
    if (last) stamp.mutate(true)
    else setStep((n) => n + 1)
  }

  if (chiuso) {
    // name and site as the closing read them from the database, so list and rows agree
    const chiusa = (p: Passo): Tappa => {
      if (p === "nome") return chiuso.nome ? "fatto" : "saltato"
      if (p === "sito" && chiuso.sito !== undefined) return chiuso.sito ? "fatto" : "saltato"
      return segnati[p] ?? "saltato"
    }
    return (
      <ChiusuraAvvio
        chiuso={chiuso}
        passi={passi.map((p) => ({ nome: t(NOMI[p]), tappa: chiusa(p) }))}
        onApri={onDone}
      />
    )
  }

  const voci: Voce[] = passi.map((p, j) => ({
    nome: t(NOMI[p]),
    tappa: j === step ? "ora" : (segnati[p] ?? "dopo"),
  }))
  const proprio = qui === "sito" || pienoDelPasso
  const gesti = (
    <>
      <a
        className="al-avvio__riga-17"
        href="#"
        role="button"
        aria-disabled={stamp.isPending ? "true" : undefined}
        onClick={(e) => {
          e.preventDefault()
          if (!stamp.isPending) stamp.mutate(false)
        }}
      >
        {t("wizard.skip")}
      </a>
      <span className="al-avvio__blocco-9" />
      {step > 0 && (
        <Comando
          testo={t("wizard.back")}
          verso="tenue"
          onClick={() => {
            setNonScritto(false)
            sito.dimentica()
            setStep((n) => n - 1)
          }}
        />
      )}
      <Comando
        testo={t(last ? "wizard.done" : "wizard.next")}
        verso={proprio ? "tenue" : "pieno"}
        spento={stamp.isPending}
        onClick={() => void avanti()}
      />
    </>
  )
  const astapTrovato = esito("astap") === "fatto"
  // the pill follows what the API holds now: a check can find ASTAP without its catalogue
  const ora = preferenze.data?.missing ?? manca
  const soloCatalogo = ora.includes("no_star_database") && !ora.includes("no_solver")
  const pastiglia =
    qui !== "astap"
      ? undefined
      : astapTrovato
        ? { testo: `✓ ${t("wizard.solver.state.found")}`, buono: true } // glifo-ok: segno della tavola
        : {
            testo: `! ${t(soloCatalogo ? "wizard.solver.state.noDatabase" : "wizard.solver.state")}`,
            buono: false,
          }

  return (
    <SalvataggioFallito.Provider value={fallito}>
      <CorniceAvvio
        passi={voci}
        titolo={t(NOMI[qui])}
        pastiglia={pastiglia}
        perche={t(perche(qui))}
        gesti={gesti}
      >
        {qui === "nome" && (
          <div className="al-avvio__blocco-5">
            <div className="al-avvio__colonna-10">
              <label className="al-avvio__testo-11" htmlFor="pa-nome">
                {t("wizard.name.label")}
              </label>
              <div className="al-avvio__riga-6">
                <input
                  id="pa-nome"
                  className="al-campo al-avvio__blocco-6"
                  placeholder={t("wizard.name.placeholder")}
                  autoComplete="off"
                  spellCheck={false}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <span className="al-avvio__testo-12">{t("wizard.name.hint")}</span>
            </div>
          </div>
        )}
        {qui === "sito" && <WizardSite sito={sito} formato={formato} />}
        {qui === "tema" && valori && (
          <SceltaTema
            {...vesteDa(valori["theme_mode"], valori["theme_accent"])}
            formato={formato}
            onModo={(m) => scrivi.mutate({ theme_mode: m })}
            onAccento={(a) => scrivi.mutate({ theme_accent: a })}
          />
        )}
        {qui === "cartelle" && <WizardFolders formato={formato} onOffre={setPienoDelPasso} />}
        {qui === "seeing" && <WizardSeeing formato={formato} onOffre={setPienoDelPasso} />}
        {qui === "astap" && (
          <WizardSolver formato={formato} senzaCatalogo={senzaCatalogo} onOffre={setPienoDelPasso} />
        )}
        {(nonScritto || stamp.error || (qui === "sito" && sito.rotto)) && (
          <Avviso
            tipo="blocco"
            formato={formato}
            segno="!"
            titolo={t(
              qui === "sito" && sito.rotto ? "wizard.site.failedTitle" : "wizard.savedFailedTitle",
            )}
            testo={t("wizard.saveFailed.text")}
          />
        )}
      </CorniceAvvio>
    </SalvataggioFallito.Provider>
  )
}
