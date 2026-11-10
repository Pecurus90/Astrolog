import { Carta } from "./componenti/Carta"
import { BarraFiltri } from "./componenti/BarraFiltri"
import { gesto } from "./componenti/gesto"
import type { Formato } from "./componenti/Tema"
import { type Fuori, type Pezzi, type Riga, pezzi, pezziFuori } from "./ArchivioDati"
import { t } from "./i18n"
import { filtri } from "./NottiDati"

interface Mostrata {
  chiave: string
  p: Pezzi
  barra: ReturnType<typeof filtri>
  /** Quante anteprime: una per produzione, una sola per un mosaico (tavola v56.13). */
  parti: number
  onApri?: () => void
}

function mostrate(righe: Riga[], fuori: Fuori | null, onApri: (k: string) => void): Mostrata[] {
  const prima: Mostrata[] = fuori
    ? [{ chiave: "__fuori__", p: pezziFuori(fuori), barra: filtri(fuori), parti: 1 }]
    : []
  return prima.concat(
    righe.map((r) => ({
      chiave: r.key,
      p: pezzi(r),
      barra: filtri(r),
      parti: r.panels !== null ? 1 : Math.max(1, r.productions.length),
      onApri: () => onApri(r.key),
    })),
  )
}

/** La vista a carte (tavola, 52-65): anteprima 3:2 col nome finche' non c'e' una foto, il segno
 *  delle produzioni o del mosaico, ore, frame e la barra dei filtri. */
export function CarteArchivio({
  righe,
  fuori,
  formato,
  onApri,
}: {
  righe: Riga[]
  fuori: Fuori | null
  formato: Formato
  onApri: (chiave: string) => void
}) {
  return (
    <div className="al-arch__centro-1">
      {mostrate(righe, fuori, onApri).map((m, j) => {
        // fino a tre per riga, oltre su due righe (tavola, `pCols`)
        const colonne = m.parti <= 3 ? m.parti : Math.ceil(m.parti / 2)
        const corpo = (
          <>
            <span className="al-arch__riga-7">
              <span
                aria-hidden="true"
                className="al-arch__foto-griglia"
                style={{ gridTemplateColumns: `repeat(${colonne},minmax(0,1fr))` }}
              >
                {Array.from({ length: m.parti }, (_, i) => (
                  <span key={i} className="al-arch__foto-parte" />
                ))}
              </span>
              <span className="al-arch__blocco-7">{m.p.nome}</span>
              {m.p.tag && <span className="al-arch__strato-2">{m.p.tag}</span>}
            </span>
            <span className="al-arch__colonna-2 al-arch__carta-testo">
              <span className="al-arch__colonna-6">
                <b className="al-arch__blocco-8">{m.p.nome}</b>
                <span className="al-arch__blocco-9">{m.p.sub || m.p.comune}</span>
              </span>
              <span className="al-arch__riga-8">
                <span className="al-arch__testo-6">{m.p.ore}</span>
                <span className="al-arch__testo-7">{m.p.fr}</span>
              </span>
              {m.barra.length > 0 && <BarraFiltri filtri={m.barra} altezza={8} formato={formato} />}
              <span className="al-arch__blocco-9">{m.p.filT}</span>
            </span>
          </>
        )
        return (
          <Carta
            key={m.chiave}
            formato={formato}
            etichetta={m.p.nome}
            colonne="auto"
            ritardo={Math.min(8, j) * 60}
            padding={0}
            gap={0}
          >
            <div className="al-arch__carta-corpo">
              {m.onApri ? (
                <a
                  className="al-arch__colonna-5"
                  href="#"
                  onClick={gesto(m.onApri)}
                  aria-haspopup="dialog"
                  aria-label={m.p.aria}
                >
                  {corpo}
                </a>
              ) : (
                <div className="al-arch__colonna-5" role="group" aria-label={m.p.aria}>
                  {corpo}
                </div>
              )}
            </div>
          </Carta>
        )
      })}
    </div>
  )
}

/** La vista a elenco (tavola, 67-77): il nome apre la finestra e si stende su tutta la riga. */
export function ElencoArchivio({
  righe,
  fuori,
  formato,
  onApri,
}: {
  righe: Riga[]
  fuori: Fuori | null
  formato: Formato
  onApri: (chiave: string) => void
}) {
  const desk = formato !== "telefono"
  return (
    <Carta
      formato={formato}
      etichetta={t("archive.view.list")}
      colonne={12}
      ritardo={60}
      padding={desk ? "16px 16px 8px" : "8px 4px"}
      gap={2}
    >
      {desk && (
        <div className="al-arch__centro-2 al-arch__elenco-righe" aria-hidden="true">
          <span>{t("archive.list.object")}</span>
          <span>{t("archive.list.kind")}</span>
          <span>{t("archive.list.time")}</span>
          <span>{t("archive.list.filters")}</span>
          <span>{t("archive.list.productions")}</span>
          <span />
        </div>
      )}
      {mostrate(righe, fuori, onApri).map((m) => (
        <div key={m.chiave} className="al-arch__centro-3 al-arch__elenco-righe al-arch__riga">
          <span className="al-arch__colonna-6">
            {m.onApri ? (
              <a
                className="al-arch__riga-apri"
                href="#"
                onClick={gesto(m.onApri)}
                aria-haspopup="dialog"
                aria-label={m.p.aria}
              >
                <b className="al-arch__blocco-10">{m.p.nome}</b>
              </a>
            ) : (
              <b className="al-arch__blocco-10">{m.p.nome}</b>
            )}
            <span className="al-arch__blocco-9">{m.p.comune}</span>
          </span>
          <span className="al-arch__blocco-11 al-arch__solo-desk">{m.p.sub}</span>
          <span className="al-arch__colonna-1 al-arch__elenco-ore">
            <span className="al-arch__testo-8">{m.p.ore}</span>
            <span className="al-arch__testo-7">{m.p.fr}</span>
          </span>
          <span className="al-arch__blocco-12 al-arch__solo-desk">
            {m.barra.length > 0 && <BarraFiltri filtri={m.barra} altezza={8} formato={formato} />}
            <span className="al-arch__blocco-9">{m.p.filT}</span>
          </span>
          <span className="al-arch__testo-9 al-arch__solo-desk">{m.p.prod}</span>
          <span className="al-arch__blocco-13 al-arch__solo-desk" aria-hidden="true">
            {m.onApri ? String.fromCharCode(0x2197) : ""}
          </span>
        </div>
      ))}
    </Carta>
  )
}
