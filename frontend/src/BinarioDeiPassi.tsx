import { type Chiave, numero, t } from "./i18n"

/**
 * **A che punto sei**: il binario del primo avvio, col mattone che il design ha fatto apposta.
 *
 * - **Lo stato di una tappa si vede in tre modi e nessuno e' il colore**: la spunta su quella
 *   fatta, il disco pieno su quella di adesso, il disco punteggiato su quelle che vengono -- e la
 *   parola in piu' per chi ascolta, che il segno non puo' dargli perche' e' `aria-hidden`.
 * - **`aria-current="step"`**, il valore giusto per un passo dentro un procedimento: e' anche il
 *   selettore a cui il foglio aggancia lo stato, quindi la veste arriva tutta.
 * - **Le tappe non sono bottoni**, e questo **non e' un `<nav>`** anche se il foglio lo suggerisce:
 *   in un primo avvio non si salta a un passo che non si e' raggiunto, e un landmark di
 *   navigazione con dentro cose che non portano da nessuna parte inganna chi lo cerca. Sarebbe
 *   anche il **secondo** dell'app, e le prove che lo cercano al singolare -- quelle senza nome,
 *   che si contano col grep -- cadrebbero tutte. Il nome sta sulla lista, che lo accetta.
 * - **Sul telefono i nomi li nasconde il foglio**, non questa pagina: restano per chi ascolta.
 */
export function BinarioDeiPassi({ passi, step }: { passi: readonly Chiave[]; step: number }) {
  return (
    <div className="as-passi">
      <p className="as-soprattitolo as-soprattitolo--nudo as-passi__quanti">
        {t("wizard.passo", { n: numero(step + 1), tot: numero(passi.length) })}
      </p>
      <ol className="as-passi__elenco" aria-label={t("wizard.steps")}>
        {passi.map((quale, i) => (
          <li
            key={quale}
            className={i < step ? "as-passi__tappa as-passi__tappa--fatto" : "as-passi__tappa"}
            aria-current={i === step ? "step" : undefined}
          >
            <span className="as-passi__segno" aria-hidden="true">
              {i < step ? "\u2713" : i + 1}
            </span>
            <span className="as-passi__nome">
              {t(quale)}
              {i <= step && (
                <span className="as-solo-lettori">
                  {" "}
                  {t(i < step ? "wizard.step.done" : "wizard.step.here")}
                </span>
              )}
            </span>
          </li>
        ))}
      </ol>
    </div>
  )
}
