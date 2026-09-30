import { Filtri, Mosaico, nomeDi, tipoDi } from "./RigaDellArchivio"
import { TempoDellePose } from "./TempoDellePose"
import type { components } from "./api/schema"
import { numero, t } from "./i18n"
import { costellazione } from "./costellazioni"

type Riga = components["schemas"]["ArchiveObject"]

/**
 * L'Archivio **a colonne**: il caso "confronto". Chi ha piu' ore, chi ha piu' pose.
 *
 * - **Le celle che non sanno sono la terza forma del dato**, non la seconda. Il foglio ne
 *   dichiara tre -- piena, vuota (una misura vera che vale zero), ignota (non si sa) -- e vuole
 *   che la terza non si distingua col solo colore: ha un tratteggio **e una parola**. Un
 *   trattino muto era gia' stato escluso con Design (`handoff/design-archivio.md`).
 * - **`data-etichetta` non e' decorazione**: sotto i 720px il foglio ribalta la tabella in un
 *   elenco e quella parola diventa il nome della cella. Toglierla lascerebbe, sul telefono, una
 *   colonna di numeri senza sapere di cosa.
 * - **Sotto i numeri c'e' `as-num`**, che li incolonna a destra: due righe di seguito si
 *   confrontano a occhio solo se le cifre stanno una sopra l'altra.
 */
export function ElencoDellArchivio({ righe }: { righe: Riga[] }) {
  return (
    <div className="as-tabella-guscio">
      <table className="as-tabella">
        <caption className="as-solo-lettori">{t("archive.table.caption")}</caption>
        <thead>
          <tr>
            <th scope="col">{t("archive.column.object")}</th>
            <th scope="col">{t("archive.column.type")}</th>
            <th scope="col">{t("archive.column.constellation")}</th>
            <th scope="col" className="as-num">
              {t("archive.column.frames")}
            </th>
            <th scope="col" className="as-num">
              {t("archive.column.time")}
            </th>
            <th scope="col">{t("archive.column.filters")}</th>
            <th scope="col">{t("archive.column.labels")}</th>
          </tr>
        </thead>
        <tbody>
          {righe.map((riga) => (
            <UnaRiga key={riga.key} riga={riga} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

/** Cio' che il catalogo non dice: la **terza forma** del dato. Il segno porta il tratteggio,
 *  la parola dice cosa vuol dire -- il colore da solo non basta (WCAG 1.4.1). */
function Ignoto() {
  return (
    <span className="as-dato as-dato--ignoto">
      <span className="as-dato__segno" aria-hidden="true">
        {"\u2014"}
      </span>
      {t("archive.unknown")}
    </span>
  )
}

function UnaRiga({ riga }: { riga: Riga }) {
  const tipo = tipoDi(riga)
  return (
    <tr>
      <td>
        <span className="as-tabella__oggetto">{nomeDi(riga)}</span>
      </td>
      <td data-etichetta={t("archive.column.type")}>{tipo ? t(tipo) : <Ignoto />}</td>
      <td data-etichetta={t("archive.column.constellation")}>
        {riga.constellation ? costellazione(riga.constellation) : <Ignoto />}
      </td>
      <td className="as-num" data-etichetta={t("archive.column.frames")}>
        <span className="as-dato">{numero(riga.frames)}</span>
      </td>
      <td className="as-num" data-etichetta={t("archive.column.time")}>
        <span className="as-dato">
          <TempoDellePose secondi={riga.integration_s} senzaTempo={riga.untimed} />
        </span>
      </td>
      <td data-etichetta={t("archive.column.filters")}>
        {riga.filters.length === 0 ? <Ignoto /> : <Filtri riga={riga} />}
      </td>
      {/* Un oggetto senza etichette non e' un dato che non si sa: e' vuoto davvero, e si tace. */}
      <td data-etichetta={t("archive.column.labels")}>
        <Mosaico riga={riga} forma="muto" />
      </td>
    </tr>
  )
}
