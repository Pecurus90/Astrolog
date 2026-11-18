import { useQueryClient } from "@tanstack/react-query"
import { type ChangeEvent, useEffect, useState } from "react"

import { api } from "./api/client"
import type { Riga } from "./ArchivioDati"
import { Avviso } from "./componenti/Avviso"
import type { Formato } from "./componenti/Tema"
import { t } from "./i18n"

export type Anteprima = Riga["previews"][number]

// Icons of the board (Archivio.dc.html, `CAM` and `MAT`): camera to add, pencil to change.
const CAMERA = "M4 8h3l2-2h6l2 2h3v11H4zM12 11v5M9.5 13.5h5"
const MATITA = "M4 20h4L19 9l-4-4L4 16zM14 6l4 4"
const PATH = "/api/v1/archive/preview"

/** The query of the address the API gave: the page reads it, never builds it. */
function domanda(url: string): { key: string; production?: string } {
  const q = new URL(url, window.location.origin).searchParams
  const production = q.get("production")
  return { key: q.get("key") ?? "", ...(production ? { production } : {}) }
}

/** The photo read with the page's key and shown from memory: an `<img>` sends no header. */
function useFoto(a: Anteprima): string | null {
  const [src, setSrc] = useState<string | null>(null)
  useEffect(() => {
    if (a.at === null) {
      setSrc(null)
      return undefined
    }
    const via = new AbortController()
    let fatto: string | null = null
    let spento = false
    void api
      .GET(PATH, { params: { query: domanda(a.url) }, parseAs: "blob", signal: via.signal })
      .then(({ data }) => {
        // a reading that lands after the cleanup would leave a blob: nobody revokes
        if (spento || !(data instanceof Blob)) return
        fatto = URL.createObjectURL(data)
        setSrc(fatto)
      })
      .catch(() => undefined)
    return () => {
      spento = true
      via.abort()
      if (fatto) URL.revokeObjectURL(fatto)
    }
  }, [a.url, a.at])
  return src
}

const ERRORI: Record<string, string> = {
  not_an_image: "archive.preview.unreadable",
  too_large: "archive.preview.tooBig",
  too_many_pixels: "archive.preview.tooBig",
}

/** The photo parts of the card: one per production, one for a mosaic (board v56.13). */
export function FotoParti({ anteprime }: { anteprime: Anteprima[] }) {
  return (
    <>
      {anteprime.map((a) => (
        <FotoParte key={a.url} a={a} />
      ))}
    </>
  )
}

function FotoParte({ a }: { a: Anteprima }) {
  const src = useFoto(a)
  return (
    <span
      className="al-arch__foto-parte"
      style={src ? { backgroundImage: `url(${src})` } : undefined}
    />
  )
}

/** The round buttons over the photo, outside the card's link: add or change, with the reason of
 *  a refusal in a row notice under the card. */
export function FotoTasti({
  anteprime,
  nome,
  colonne,
  formato,
}: {
  anteprime: Anteprima[]
  nome: string
  colonne: number
  formato: Formato
}) {
  const client = useQueryClient()
  const [errore, setErrore] = useState<string | null>(null)
  const molte = anteprime.length > 1

  const metti = async (a: Anteprima, e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = "" // the same file can be chosen again
    if (!file) return
    setErrore(null)
    const { error } = await api.PUT(PATH, {
      params: { query: domanda(a.url) },
      body: file as unknown as string,
      bodySerializer: (b: unknown) => b as BodyInit,
      headers: { "Content-Type": file.type || "application/octet-stream" },
    })
    if (error) {
      const code = (error as { detail?: { code?: string } }).detail?.code ?? ""
      setErrore(t((ERRORI[code] ?? "archive.preview.unreachable") as "archive.preview.tooBig"))
      return
    }
    await client.invalidateQueries({ queryKey: ["archive"] })
  }

  return (
    <>
      <div
        className="al-arch__foto-tasti"
        style={{ gridTemplateColumns: `repeat(${colonne},minmax(0,1fr))` }}
      >
        {anteprime.map((a, i) => {
          const c = a.at !== null
          const n = i + 1
          const titolo = molte
            ? t(c ? "archive.preview.changeNth" : "archive.preview.addNth", { n })
            : t(c ? "archive.preview.change" : "archive.preview.add")
          const chi = molte ? t("archive.preview.nth", { n, nome }) : nome
          return (
            <span key={a.url} className="al-arch__foto-cella">
              <label title={titolo} className="al-arch__foto-tasto">
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="al-arch__foto-file"
                  aria-label={t(c ? "archive.preview.aria.change" : "archive.preview.aria.add", {
                    nome: chi,
                  })}
                  onChange={(e) => void metti(a, e)}
                />
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden="true"
                >
                  <path d={c ? MATITA : CAMERA} />
                </svg>
              </label>
            </span>
          )
        })}
      </div>
      {errore && (
        <Avviso
          tipo="riga"
          formato={formato}
          segno="!"
          titolo={errore}
          azione={t("ui.close")}
          onAzione={() => setErrore(null)}
        />
      )}
    </>
  )
}
