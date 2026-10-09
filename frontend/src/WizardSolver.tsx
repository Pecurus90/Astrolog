import { t } from "./i18n"
import { CampoDelPercorso, DoveSiPrende, IlCatalogo, useDoveStaASTAP } from "./riconoscitore"

/**
 * Il passo che compare **solo se** il riconoscitore non e' pronto: cosa ci perdi senza, dove si
 * prende, e il campo per dire dove sta se ce l'hai gia'.
 *
 * Il campo, la scrittura e il "dove si prende" stanno in `riconoscitore.tsx`, che li divide con
 * la sezione *Il riconoscitore*. Qui resta cio' che e' del **passo**:
 *
 * - **Quale dei due casi sia lo decide chi monta il passo, entrando**, e non una domanda viva: il
 *   passo si guarda mentre si scrive dentro, e una risposta che arriva dopo cambierebbe schermata
 *   sotto le mani -- portandosi via il campo e la conferma di cio' che si e' appena scritto. E'
 *   la stessa ragione per cui il **numero** dei passi si congela entrando.
 * - **Non e' un guasto, e' una cosa da fare**: nessun allarme. L'app senza solver cataloga, mette
 *   in ordine i nomi e conta le ore -- quello che non sa dire e' **cosa** hai ripreso.
 * - Si salta come ogni altro passo: chi vuole solo catalogare non deve installare niente.
 */
export function WizardSolver({
  senzaCatalogo,
  onOffre,
}: {
  senzaCatalogo: boolean
  onOffre: (offre: boolean) => void
}) {
  const dove = useDoveStaASTAP()

  // **ASTAP c'e', gli manca il catalogo**: qui il percorso non si chiede, perche' e' gia' giusto.
  // Chiederlo manderebbe a correggere una cosa che non e' sbagliata.
  if (senzaCatalogo) {
    return (
      <div className="as-passo__parte">
        <IlCatalogo quali={[]} />
      </div>
    )
  }

  return (
    <>
      {/* **Cosa cambia senza**, e non e' un guasto: una parte del passo, senza allarme. Manca un
          programma, e si puo' installare dopo. */}
      <div className="as-passo__parte">
        <p className="as-soprattitolo as-soprattitolo--nudo">{t("solver.withoutTitle")}</p>
        <p className="as-passo__nota">{t("solver.without")}</p>
      </div>

      <div className="as-passo__parte">
        <DoveSiPrende />
        {/* **Anche il catalogo, e detto qui**: chi installa ASTAP dopo aver chiuso il primo avvio
            non ripassa piu' di qua. Una riga, non un secondo avviso. */}
        <p className="as-passo__nota">{t("solver.alsoTheDatabase")}</p>
      </div>

      <div className="as-passo__parte">
        <p className="as-soprattitolo as-soprattitolo--nudo">{t("solver.haveItGroup")}</p>
        <CampoDelPercorso dove={dove} id="wizard-solver-path" onOffre={onOffre} />
      </div>
    </>
  )
}
