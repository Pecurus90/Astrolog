import { Avviso } from "./componenti/Avviso"
import type { Formato } from "./componenti/Tema"
import { CampoAvvio, Comando } from "./PrimoAvvioCornice"
import { t } from "./i18n"
import { usePienoDelPasso } from "./pienoDelPasso"
import { DOVE_SI_SCARICA, useDoveStaASTAP, useSolver } from "./riconoscitore"

/**
 * The ASTAP step, shown **only** when the recognizer is not ready (tavola v82 `Primo avvio`,
 * `V.astapNo`, `V.astapCat`, `A`). Which of the two cases is decided on entry by whoever mounts
 * the step: a live answer would change the screen under the user's hands.
 *
 * - **Not a fault, a thing to do**: without ASTAP the app catalogues and counts the hours.
 * - **The app downloads and runs nothing by itself**: it gives the address.
 * - **ASTAP there, catalogue missing**: the path is not asked, it is already right.
 */
export function WizardSolver({
  formato,
  senzaCatalogo,
  onOffre,
}: {
  formato: Formato
  senzaCatalogo: boolean
  onOffre: (offre: boolean) => void
}) {
  const dove = useDoveStaASTAP()
  const trovato = dove.esito === "found"
  const solver = useSolver()
  // on a NAS only ASTROLOG_ASTAP picks it (#95): no path to ask
  const chiede = solver.data?.set_by_admin !== true
  const admin = !chiede
  // tavola `cmd`: Verifica percorso is the full command until ASTAP is found
  usePienoDelPasso(onOffre, !senzaCatalogo && !trovato && chiede)

  if (senzaCatalogo)
    return (
      <div className="al-avvio__colonna-12">
        <Avviso
          tipo="blocco"
          formato={formato}
          segno="!"
          titolo={t("solver.databaseTitle")}
          testo={t("solver.databaseWhy")}
        />
        <Catalogo />
      </div>
    )

  const esito =
    dove.esito === "found"
      ? { segno: "\u2713" as const, titolo: t("solver.foundTitle"), testo: t("solver.found") }
      : dove.esito === "foundNoDatabase"
        ? {
            segno: "!" as const,
            titolo: t("wizard.solver.foundNoDatabase"),
            testo: t("solver.foundNoDatabase"),
          }
        : dove.esito === "notThere"
          ? {
              segno: "!" as const,
              titolo: t("wizard.solver.notThere"),
              testo: t("wizard.solver.notThere.text"),
            }
          : undefined
  return (
    <>
      <div className="al-avvio__colonna-11">
        <div
          className="al-avvio__centro-6"
          style={{
            gridTemplateColumns:
              formato === "telefono" ? "minmax(0,1fr)" : "repeat(2,minmax(0,1fr))",
          }}
        >
          <div className="al-avvio__colonna-22">
            <span className="al-avvio__testo-13">{t("solver.withoutTitle")}</span>
            <span className="al-avvio__testo-20">{t("solver.without")}</span>
          </div>
          {admin ? (
            <div className="al-avvio__colonna-22">
              <span className="al-avvio__testo-13">{t("settings.solver.channel.admin")}</span>
              <span className="al-avvio__testo-20">{t("settings.solver.channel.admin.sub")}</span>
            </div>
          ) : (
            <div className="al-avvio__colonna-22">
              <span className="al-avvio__testo-13">{t("solver.whereGroup")}</span>
              <a
                className="al-avvio__riga-15"
                href={DOVE_SI_SCARICA}
                target="_blank"
                rel="noopener"
              >
                {`${t("solver.download")} ↗` /* glifo-ok: freccia della tavola */}
              </a>
              <span className="al-avvio__testo-12">{t("solver.noDownload")}</span>
            </div>
          )}
        </div>
        {chiede && (
          <div className="al-avvio__colonna-12">
            <span className="al-avvio__testo-13">{t("solver.haveItGroup")}</span>
            <form
              onSubmit={(e) => {
                e.preventDefault()
                dove.manda()
              }}
            >
              <CampoAvvio
                id="pa-astap"
                etichetta={t("solver.label")}
                valore={dove.path}
                onScrivi={(v) => {
                  dove.setPath(v)
                  // the outcome belongs to what was written before
                  dove.dimentica()
                }}
                // a path typed by hand is kept also when the field is left (riconoscitore.tsx)
                onLascia={dove.manda}
                segnaposto={t("solver.placeholder")}
                aiuto={t("solver.pathHelp")}
                dopo={
                  <Comando
                    testo={t("solver.use")}
                    verso={trovato ? "tenue" : "pieno"}
                    spento={!dove.path.trim()}
                    occupato={dove.salva.isPending ? t("wizard.checking") : undefined}
                    onClick={dove.manda}
                  />
                }
              />
            </form>
          </div>
        )}
      </div>
      {esito && <Avviso tipo="blocco" formato={formato} {...esito} />}
      {dove.salva.error && (
        <Avviso tipo="blocco" formato={formato} segno="!" titolo={dove.salva.error.message} />
      )}
    </>
  )
}

/** Where the star catalogue is taken, and which one (ADR 0036). */
function Catalogo() {
  return (
    <div className="al-avvio__colonna-22">
      <a className="al-avvio__riga-15" href={DOVE_SI_SCARICA} target="_blank" rel="noopener">
        {`${t("solver.databaseGet")} ↗` /* glifo-ok: freccia della tavola */}
      </a>
      <span className="al-avvio__testo-20">{t("wizard.solver.which")}</span>
    </div>
  )
}
