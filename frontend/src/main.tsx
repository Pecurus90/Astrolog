import { QueryClientProvider } from "@tanstack/react-query"
import { StrictMode } from "react"
import { createRoot } from "react-dom/client"

import { App } from "./App"
import { nuoviDati } from "./dati"
// Il carattere del foglio, dentro l'app e mai scaricato (ADR 0018): i pesi che il foglio chiede,
// 300-700 per il testo, 400-700 per le cifre. Prima del foglio, che lo nomina.
import "@fontsource/atkinson-hyperlegible-next/300.css"
import "@fontsource/atkinson-hyperlegible-next/400.css"
import "@fontsource/atkinson-hyperlegible-next/500.css"
import "@fontsource/atkinson-hyperlegible-next/600.css"
import "@fontsource/atkinson-hyperlegible-next/700.css"
import "@fontsource/atkinson-hyperlegible-mono/400.css"
import "@fontsource/atkinson-hyperlegible-mono/500.css"
import "@fontsource/atkinson-hyperlegible-mono/600.css"
import "@fontsource/atkinson-hyperlegible-mono/700.css"
// v58 sheet first, old after: its :root wins for as- pages; al- pages sit under Tema's data-modo.
import "./stili/consegna/astrolog.css"
import "./stili/consegna/caratteri.css"
// Il foglio della consegna: dentro, prima i token e poi i mattoni che li leggono.
import "./stili/astrolog.css"
// e in coda il poco che e' nostro: la catena delle altezze fino al nodo radice.
import "./stili/app.css"

// La casa dei dati che arrivano dall'API: una sola, e le pagine ci chiedono dentro. Senza,
// ogni schermo si porterebbe il suo stato di caricamento e le sue copie -- e due parti della
// stessa pagina potrebbero mostrare due versioni dello stesso numero.
const dati = nuoviDati()

// A page opened after an update asks for a file the new build renamed: the page reloads, as
// Vite advises (vite.dev/guide/build, "Load Error Handling"). Once a minute, or it would loop.
window.addEventListener("vite:preloadError", () => {
  const ultima = Number(sessionStorage.getItem("astrolog-ricarica") ?? 0)
  if (Date.now() - ultima < 60_000) return
  sessionStorage.setItem("astrolog-ricarica", String(Date.now()))
  window.location.reload()
})

const radice = document.getElementById("root")
if (!radice) {
  // La pagina la serve il backend da `index.html`: se questo nodo manca, il file servito non e'
  // quello costruito. Meglio dirlo che disegnare nel vuoto.
  throw new Error("manca il nodo radice: la pagina servita non e' quella costruita")
}

createRoot(radice).render(
  <StrictMode>
    <QueryClientProvider client={dati}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
