/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react"
import { defineConfig } from "vitest/config"

// Il build finisce DENTRO il pacchetto Python, non in `dist/`: dopo un'installazione
// `frontend/` non esiste piu', e "il frontend si serve da se'" resterebbe vero solo dal
// sorgente. Il backend la cerca esattamente li' (`astrolog/api/page.py`, `WEB_DIR`).
const PAGINA_COSTRUITA = "../backend/astrolog/web"

/**
 * In sviluppo la pagina la serve Vite, non il backend -- quindi il `<meta>` con la chiave di
 * avvio non c'e', e senza quello ogni chiamata all'API prende 401. Qui si mette lo stesso meta
 * che il backend mette in produzione, prendendo la chiave da chi ha acceso tutto
 * (`tools/dev.py`). Solo in sviluppo (`apply: "serve"`): nel build la pagina la serve il
 * backend, ed e' lui a iniettarla a ogni richiesta.
 */
function chiaveNellaPagina() {
  return {
    name: "astrolog-chiave-in-sviluppo",
    apply: "serve" as const,
    transformIndexHtml(html: string) {
      const chiave = process.env["ASTROLOG_TOKEN"]
      if (!chiave) return html
      // `token_urlsafe` produce solo lettere, cifre, `-` e `_`: niente da sfuggire in un
      // attributo. Se un giorno la chiave cambiasse forma, qui va sfuggita come fa il backend.
      return html.replace("<head>", `<head><meta name="astrolog-token" content="${chiave}">`)
    },
  }
}

export default defineConfig({
  plugins: [react(), chiaveNellaPagina()],
  build: {
    outDir: PAGINA_COSTRUITA,
    // Ripulisce prima di ricostruire: senza, i file di un build vecchio -- che hanno l'impronta
    // nel nome -- si accumulerebbero nel pacchetto per sempre.
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    // Porta fissa e non "la prima libera": il backend ammette host noti, e un numero che
    // cambia a ogni avvio e' un errore che sembra un difetto dell'app.
    strictPort: true,
    // In sviluppo la pagina la serve Vite, le chiamate `/api` le gira al backend: una sola
    // origine per il browser, quindi nessun permesso fra origini diverse da configurare.
    proxy: { "/api": "http://127.0.0.1:8765" },
  },
  test: {
    // Tests live in `tests/`, not next to the component.
    // `tsx` compreso: senza, il primo test di un componente non verrebbe raccolto e vitest
    // direbbe verde su una suite che non ha eseguito.
    include: ["tests/**/*.test.{ts,tsx}"],
    environment: "node",
    // Il pavimento della copertura, **bloccante** come quello del backend: fino al 14/9/2026
    // meta' del prodotto era misurata e meta' no, e ogni difetto sfuggito quel giorno stava
    // nella meta' senza pavimento. Il numero e' lo stesso del backend -- una regola sola per
    // tutto il prodotto -- e oggi c'e' abbondante margine (statement 96%): un pavimento tirato
    // al millimetro si rompe al primo test lento e chi lo trova lo spegne.
    coverage: {
      provider: "v8",
      // `include` governa **l'insieme misurato**, non solo quello riportato: un file che nessun
      // test importa deve risultare scoperto, non assente -- altrimenti il pavimento premia chi
      // non scrive prove invece di fermarlo. Verificato contando i file nel riepilogo JSON.
      include: ["src/**"],
      // `schema.d.ts` e' **generato** dall'OpenAPI e `main.tsx` e' l'avvio della pagina (monta
      // React e basta): misurarli direbbe "quanto proviamo cio' che non scriviamo" e "quanto
      // proviamo l'avvio", che e' la stessa ragione per cui il backend esclude `__main__.py`.
      exclude: ["src/api/schema.d.ts", "src/main.tsx"],
      thresholds: { statements: 85, branches: 85, functions: 85, lines: 85 },
    },
  },
})
