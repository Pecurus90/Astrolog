import { useMutation } from "@tanstack/react-query"
import { useId, useRef, useState } from "react"

import { Avviso } from "./Avviso"
import { Bottone } from "./Bottone"
import { Campo } from "./Campo"
import { ChiaveMeteoblue } from "./ChiaveMeteoblue"
import { BinarioDeiPassi } from "./BinarioDeiPassi"
import { WizardFolders } from "./WizardFolders"
import { WizardSite } from "./WizardSite"
import { WizardSolver } from "./WizardSolver"
import { api } from "./api/client"
import type { components } from "./api/schema"
import { type Chiave, t } from "./i18n"
import { useRadiceDati } from "./radiceDati"

// Cosa manca all'app, coi codici generati dall'API: scritto `string[]` a mano, un codice
// ritirato o rinominato dal backend continuerebbe a compilare e il passo non comparirebbe piu'.
type Manca = components["schemas"]["SettingsOut"]["missing"]

// `as const` e non `readonly Chiave[]`: cosi' `Passo` e' l'elenco dei cinque nomi veri, e la
// tabella qui sotto non puo' dimenticarne uno. Annotata `Chiave[]`, il tipo di un passo tornava
// a essere "una chiave qualunque" e un passo senza la sua riga non faceva rosso da nessuna parte.
const STEPS = [
  "wizard.step.name",
  "wizard.step.site",
  "wizard.step.folders",
  "wizard.step.services",
] as const

// Il passo in piu': c'e' solo se il riconoscitore non e' pronto. Non e' un quinto passo per
// tutti -- chi ce l'ha non deve nemmeno sapere che esiste -- ma senza, chi non ce l'ha scansiona,
// aspetta e non riconosce niente, senza che nessuno glielo dica (Marco, 9/9/2026).
//
// **Non pronto sono due cose**: il programma che non c'e', e il programma che c'e' senza il suo
// catalogo stellare. La seconda arriva allo stesso identico punto -- una scansione che non
// riconosce niente -- e chiederla solo per la prima lasciava fuori chi ha installato ASTAP e si
// e' fermato prima di scaricare anche quello.
const PASSO_SOLVER = "wizard.step.solver" as const
const RICONOSCITORE_NON_PRONTO = ["no_solver", "no_star_database"] as const

type Passo = (typeof STEPS)[number] | typeof PASSO_SOLVER

// Perche' l'app chiede quel passo: una riga per ognuno, accanto al suo nome. Sta qui e non nei
// quattro file dei passi perche' e' l'intestazione della carta a mostrarla, e l'intestazione la
// monta il guscio: scritta di la', ogni passo dovrebbe passarla su.
const PERCHE: Record<Passo, Chiave> = {
  "wizard.step.name": "wizard.name.why",
  "wizard.step.site": "wizard.site.why",
  "wizard.step.folders": "wizard.folders.intro",
  "wizard.step.services": "wizard.services.why",
  "wizard.step.solver": "wizard.solver.intro",
}

/**
 * Il primo avvio: quattro domande -- come ti chiami, da dove osservi, dove stanno i file, e la
 * chiave Meteoblue se ce l'hai -- piu' una quinta a chi manca il riconoscitore, e poi si toglie di mezzo. Le decisioni stanno nel contratto
 * (`docs/domini/sito.md`), che e' la loro casa; qui ci sono solo i vincoli di questo pezzo di
 * schermo.
 *
 * - **Quanti passi sono si decide entrando**, e non cambia piu': scrivere il percorso del solver
 *   fa sparire `no_solver`, e con l'elenco vivo il quinto passo si toglierebbe da sotto i piedi di
 *   chi ci sta dentro -- schermata vuota, e nessuna idea di cosa sia appena successo.
 * - **Si salta sempre, da ogni passo**, e saltare non chiede conferma: e' una scelta legittima,
 *   non un incidente.
 * - **Saltare e completare timbrano**, e il timbro porta **fuori**: scriverlo e restare fermi qui
 *   sarebbe la stessa prigione con una riga in piu' nel database.
 * - **Il binario non e' una barra di avanzamento**: dice quanti passi sono e come si chiamano --
 *   cose che si sanno prima di cominciare -- e quale si sta facendo. Una percentuale prometterebbe
 *   una misura del lavoro che resta, che nessuno ha.
 * - **La riga che dice perche' l'app chiede non e' sempre la stessa**: al passo delle cartelle
 *   dipende da dove gira l'app, perche' sul NAS si sfoglia e sul computer si scrive, e una sola
 *   delle due frasi e' vera per chi la legge.
 * - **Qui non c'e' un guasto, manca una configurazione**: nessun allarme per cio' che e' solo da
 *   fare. Ma una **scrittura fallita si dice**, perche' tacerla lascerebbe credere fatto qualcosa
 *   che non e' successo.
 */
export function Wizard({ onDone, manca }: { onDone: () => void; manca: Manca }) {
  const [passi] = useState<readonly Passo[]>(() =>
    RICONOSCITORE_NON_PRONTO.some((c) => manca.includes(c)) ? [...STEPS, PASSO_SOLVER] : STEPS,
  )
  // Dove l'app vede i dati decide **quale riga** spiega il terzo passo: sul NAS non si scrive un
  // percorso, si sfoglia, e la riga che dice "scrivi il percorso di una cartella" mandava a fare
  // una cosa che quella schermata non offre. La domanda e' quella che fa anche il passo delle
  // cartelle, e parte gia' da qui: cosi' quando ci si arriva la risposta c'e' di sicuro.
  const radice = useRadiceDati()
  // Chi ha ASTAP e non il suo catalogo arriva al **quinto passo per un altro motivo**, e la riga
  // che dice perche' l'app lo chiede deve dire il suo: "non trovo ASTAP" a chi ce l'ha manda a
  // cercare la cosa sbagliata. Si decide da cio' che mancava **entrando**, come il numero dei
  // passi: cambiando sotto i piedi, la ragione non corrisponderebbe piu' al passo che si vede.
  const [senzaCatalogo] = useState(() => manca.includes("no_star_database"))
  const perche = (passo: Passo): Chiave => {
    if (passo === "wizard.step.folders" && radice !== null) return "wizard.folders.introNas"
    if (passo === PASSO_SOLVER && senzaCatalogo) return "wizard.solver.introNoDatabase"
    return PERCHE[passo]
  }
  const [step, setStep] = useState(0)
  const [name, setName] = useState("")
  const [failed, setFailed] = useState(false)
  const saved = useRef<string | undefined>(undefined)
  const last = step === passi.length - 1
  const titolo = useId()

  const stamp = useMutation({
    mutationFn: async () => {
      const { error } = await api.POST("/api/v1/settings/wizard-done", {})
      if (error) throw new Error(t("settings.failed"))
      // **Finito il primo avvio, l'app si mette a leggere.** Chi ha appena installato non deve
      // sapere che esiste un pulsante: indica dove stanno le foto, chiude, e l'archivio si
      // riempie. Si chiede **solo se una cartella c'e'**: senza, il backend risponderebbe "non
      // c'e' niente da leggere" e il primo avvio si chiuderebbe con un errore in faccia.
      //
      // E **il timbro comanda**: se questa parte va storta si esce lo stesso. Il timbro e' gia'
      // scritto, quindi tenere l'utente dentro il primo avvio vorrebbe dire chiuderlo in una
      // stanza di cui ha gia' la chiave -- e la lettura si chiede col pulsante in barra.
      try {
        // `limit: 1` perche' qui serve solo **quante** sono: l'elenco intero e' 27 KB su
        // trecento cartelle, e nessuno lo guarda (misurato: 319 byte contro 27.156).
        const { data } = await api.GET("/api/v1/folders", { params: { query: { limit: 1 } } })
        if ((data?.total ?? 0) > 0) await api.POST("/api/v1/scan")
      } catch {
        // niente: l'archivio si leggera' col pulsante, e il primo avvio e' finito comunque
      }
    },
    onSuccess: onDone,
  })

  // Il nome si scrive lasciando il passo, non a ogni tasto -- e non si riscrive se non e'
  // cambiato: con Indietro e Avanti si ripasserebbe di qui a ogni giro.
  const next = async () => {
    if (step === 0 && name && name !== saved.current) {
      const { error } = await api.PATCH("/api/v1/settings", {
        body: { values: { user_name: name } },
      })
      setFailed(Boolean(error))
      if (error) return
      saved.current = name
    }
    setStep((s) => s + 1)
  }

  return (
    /* Fuori dal telaio: lo schermo e' `.as-entra`, coi passi di lato e la carta del passo. Sotto
       900 il foglio mette i passi in fila e i gesti in una barra in fondo. */
    <main className="as-entra">
      <div className="as-entra__colonna">
        <div className="as-entra__lato">
          <header className="as-entra__testata">
            <h1 className="as-entra__titolo">{t("wizard.title")}</h1>
            <p className="as-entra__sotto">{t("wizard.reassure")}</p>
          </header>
          <BinarioDeiPassi passi={passi} step={step} />
        </div>

        {/* La carta ripete il nome del passo che il lato mostra gia': chi arriva a meta' non
            guarda di lato, e sul telefono i nomi di lato non si vedono. */}
        <section className="as-carta as-passo" aria-labelledby={titolo}>
          <div className="as-passo__corpo">
            <div className="as-passo__capo">
              <h2 className="as-passo__titolo" id={titolo}>
                {t(passi[step]!)}
                {/* Attesa e non allarme: non avere ASTAP e' una cosa da fare, non un guasto. */}
                {passi[step] === PASSO_SOLVER && (
                  <span className="as-passo__pastiglia">
                    {t(senzaCatalogo ? "wizard.solver.state.noDatabase" : "wizard.solver.state")}
                  </span>
                )}
              </h2>
              {/* La ragione prima della domanda: chi sta per rispondere legge prima perche'. */}
              <p className="as-passo__perche">{t(perche(passi[step]!))}</p>
            </div>
            <div className="as-passo__parti">
              {step === 0 && (
                <Campo id="wizard-name" etichetta={t("wizard.name.label")}>
                  <input
                    className="as-campo-modulo__input"
                    id="wizard-name"
                    placeholder={t("wizard.name.placeholder")}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                  <p className="as-campo-modulo__aiuto">{t("wizard.name.hint")}</p>
                </Campo>
              )}
              {step === 1 && <WizardSite onSaved={() => setStep(2)} />}
              {/* Aggiungere una cartella non chiude il primo avvio: a chiudere e' Fatto. */}
              {step === 2 && <WizardFolders />}
              {passi[step] === "wizard.step.services" && <ChiaveMeteoblue id="wizard-meteoblue-key" />}
              {passi[step] === PASSO_SOLVER && <WizardSolver senzaCatalogo={senzaCatalogo} />}
              {/* Una scrittura fallita si dice nel passo che l'ha provocata, e ci si resta. */}
              {(failed || stamp.error) && (
                <Avviso esito="allarme" titolo={t("wizard.savedFailedTitle")}>
                  {t("settings.failed")}
                </Avviso>
              )}
            </div>
          </div>

          {/* Saltare sta per primo, lontano da cio' che manda avanti; al primo passo Indietro
              non c'e'. Il primario e' l'ultimo. */}
          <div className="as-gesti">
            <Bottone verso="nudo" onClick={() => stamp.mutate()} disabled={stamp.isPending}>
              {t("wizard.skip")}
            </Bottone>
            {step > 0 && <Bottone onClick={() => setStep((s) => s - 1)}>{t("wizard.back")}</Bottone>}
            {!last && (
              <Bottone verso="primario" onClick={() => void next()}>
                {t("wizard.next")}
              </Bottone>
            )}
            {last && (
              <Bottone verso="primario" onClick={() => stamp.mutate()} disabled={stamp.isPending}>
                {t("wizard.done")}
              </Bottone>
            )}
          </div>
        </section>
      </div>
    </main>
  )
}
