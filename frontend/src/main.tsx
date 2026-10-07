import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { StrictMode } from "react"
import { createRoot } from "react-dom/client"

import { App } from "./App"
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
// Il foglio della consegna: dentro, prima i token e poi i mattoni che li leggono.
import "./stili/astrolog.css"
// e in coda il poco che e' nostro: la catena delle altezze fino al nodo radice.
import "./stili/app.css"

// La casa dei dati che arrivano dall'API: una sola, e le pagine ci chiedono dentro. Senza,
// ogni schermo si porterebbe il suo stato di caricamento e le sue copie -- e due parti della
// stessa pagina potrebbero mostrare due versioni dello stesso numero.
const dati = new QueryClient()

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
