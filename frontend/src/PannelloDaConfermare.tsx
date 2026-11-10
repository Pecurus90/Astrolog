import type { CSSProperties } from "react"
import { Link } from "react-router"

import type { components } from "./api/schema"
import { numero, t } from "./i18n"
import { SEZIONI } from "./sezioniDaConfermare"

type SezioneAperta = components["schemas"]["ReviewSectionOut"]

// [T] DaConfermare.dc.html: under its pill, as wide as the board
const POSTO: CSSProperties = {
  position: "absolute",
  top: "calc(100% + 10px)",
  right: 0,
  width: "320px",
}

/**
 * Il pannello di *Da confermare* (tavola `DaConfermare` v76): quante domande aspettano, e le
 * sezioni che ne hanno, ognuna col suo *Rispondi* che apre la pagina su quella sezione.
 *
 * Il totale e i conti arrivano dal backend (`to_confirm`, `sections`): qui non si somma niente.
 */
export function PannelloDaConfermare({
  quante,
  sezioni,
}: {
  quante: number
  sezioni: readonly SezioneAperta[]
}) {
  return (
    <div
      className="al-c-da-confermare__colonna-1 app-telaio"
      role="dialog"
      aria-label={t("nav.review")}
      data-menu="1"
      style={POSTO}
    >
      <span className="al-c-da-confermare__riga-1">
        <span className="al-c-da-confermare__testo-1">{numero(quante)}</span>
        <span className="al-c-da-confermare__testo-2">{t("frame.todo.word")}</span>
      </span>
      <ul className="al-c-da-confermare__colonna-2" aria-label={t("frame.todo.sections")}>
        {sezioni.map((s) => {
          const nome = t(SEZIONI[s.key].titolo)
          return (
            <li className="al-c-da-confermare__riga-2" key={s.key}>
              <span className="al-c-da-confermare__colonna-3">
                <span className="al-c-da-confermare__testo-3">{nome}</span>
                <span className="al-c-da-confermare__testo-4">
                  {t("frame.todo.questions", { n: numero(s.count) })}
                </span>
              </span>
              <Link
                className="al-c-da-confermare__riga-3"
                to={`/da-confermare#${SEZIONI[s.key].ancora}`}
                aria-label={t("frame.todo.answer.aria", { sezione: nome })}
              >
                {t("frame.todo.answer")}
              </Link>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
